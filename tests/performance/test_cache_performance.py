"""
Performance Benchmarks for Cache System

Measures:
- Cache operation speeds (get, set, delete)
- Database query performance with/without indexes
- Forecast generation time with different cache tiers
- Cache hit/miss ratios
- Memory usage and efficiency
"""

import pytest
import time
import statistics
from datetime import datetime, timedelta
import psutil
import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.cache import get_cache, CacheService
from app.models.entry import Entry
from app.models.user import User
from app.models.forecast import Forecast
from app.db.session import Base


# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_performance.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module")
def db_session():
    """Create test database with sample data"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Create test user
    user = User(
        email="perf_test@example.com",
        username="perftest",
        hashed_password="test123",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create large dataset (1000 entries for realistic performance testing)
    base_date = datetime.now() - timedelta(days=365)
    entries = []

    for i in range(1000):
        entry = Entry(
            user_id=user.id,
            type='expense' if i % 3 != 0 else 'income',
            amount=50 + (i % 500),
            date=(base_date + timedelta(days=i % 365)).date(),
            category_id=(i % 10) + 1,
            note=f'Performance test entry {i}'
        )
        entries.append(entry)

        # Bulk insert every 100 entries
        if len(entries) >= 100:
            db.bulk_save_objects(entries)
            db.commit()
            entries = []

    # Insert remaining
    if entries:
        db.bulk_save_objects(entries)
        db.commit()

    yield db, user

    db.close()
    Base.metadata.drop_all(bind=engine)


class TestCacheOperationPerformance:
    """Benchmark basic cache operations"""

    def test_cache_set_performance(self):
        """Benchmark cache SET operation speed"""
        cache = get_cache()

        if not cache.enabled:
            pytest.skip("Redis not available")

        # Test data
        test_data = {
            'forecast': [{'date': f'2025-{i:02d}-01', 'amount': i * 100} for i in range(1, 13)],
            'summary': {'total': 78000, 'average': 6500}
        }

        # Warm-up
        for i in range(10):
            cache.set(f'warmup:key:{i}', test_data, ttl=60)

        # Benchmark
        iterations = 100
        times = []

        for i in range(iterations):
            start = time.perf_counter()
            cache.set(f'perf:test:{i}', test_data, ttl=3600)
            elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
            times.append(elapsed)

        # Statistics
        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        p95_time = statistics.quantiles(times, n=20)[18]  # 95th percentile

        print(f"\nCache SET Performance ({iterations} iterations):")
        print(f"  Average: {avg_time:.3f}ms")
        print(f"  Median: {median_time:.3f}ms")
        print(f"  P95: {p95_time:.3f}ms")

        # Assert reasonable performance (< 5ms average)
        assert avg_time < 5.0, f"Cache SET too slow: {avg_time:.3f}ms"

    def test_cache_get_performance(self):
        """Benchmark cache GET operation speed"""
        cache = get_cache()

        if not cache.enabled:
            pytest.skip("Redis not available")

        # Set up test data
        test_data = {'large_dataset': list(range(1000))}
        cache.set('perf:get:test', test_data, ttl=3600)

        # Warm-up
        for _ in range(10):
            cache.get('perf:get:test')

        # Benchmark
        iterations = 100
        times = []

        for _ in range(iterations):
            start = time.perf_counter()
            result = cache.get('perf:get:test')
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        p95_time = statistics.quantiles(times, n=20)[18]

        print(f"\nCache GET Performance ({iterations} iterations):")
        print(f"  Average: {avg_time:.3f}ms")
        print(f"  Median: {median_time:.3f}ms")
        print(f"  P95: {p95_time:.3f}ms")

        # Assert reasonable performance (< 2ms average)
        assert avg_time < 2.0, f"Cache GET too slow: {avg_time:.3f}ms"

    def test_cache_delete_pattern_performance(self):
        """Benchmark pattern-based deletion"""
        cache = get_cache()

        if not cache.enabled:
            pytest.skip("Redis not available")

        # Set up multiple keys
        for i in range(100):
            cache.set(f'user:123:data:{i}', {'value': i}, ttl=3600)

        # Benchmark deletion
        start = time.perf_counter()
        deleted = cache.delete_pattern('user:123:data:*')
        elapsed = (time.perf_counter() - start) * 1000

        print(f"\nPattern Delete Performance:")
        print(f"  Deleted {deleted} keys in {elapsed:.3f}ms")
        print(f"  Average per key: {elapsed/deleted:.3f}ms")

        # Should delete all 100 keys reasonably fast
        assert deleted == 100
        assert elapsed < 100, f"Pattern delete too slow: {elapsed:.3f}ms"


class TestDatabaseQueryPerformance:
    """Benchmark database queries with and without indexes"""

    def test_indexed_query_performance(self, db_session):
        """Benchmark queries using composite indexes"""
        db, user = db_session

        # Query using composite index: user_id + date + type
        iterations = 50
        times = []

        start_date = datetime.now() - timedelta(days=90)
        end_date = datetime.now()

        for _ in range(iterations):
            start = time.perf_counter()

            # This query should use idx_entries_user_date_type
            entries = db.query(Entry).filter(
                Entry.user_id == user.id,
                Entry.date >= start_date.date(),
                Entry.date <= end_date.date(),
                Entry.type == 'expense'
            ).all()

            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        avg_time = statistics.mean(times)
        median_time = statistics.median(times)

        print(f"\nIndexed Query Performance ({iterations} iterations):")
        print(f"  Average: {avg_time:.3f}ms")
        print(f"  Median: {median_time:.3f}ms")
        print(f"  Results: {len(entries)} entries")

        # Indexed query should be fast (< 50ms on average)
        assert avg_time < 50, f"Indexed query too slow: {avg_time:.3f}ms"

    def test_sorted_query_performance(self, db_session):
        """Benchmark sorted queries using date DESC index"""
        db, user = db_session

        iterations = 50
        times = []

        for _ in range(iterations):
            start = time.perf_counter()

            # This query should use idx_entries_user_type_date_desc
            entries = db.query(Entry).filter(
                Entry.user_id == user.id,
                Entry.type == 'expense'
            ).order_by(Entry.date.desc()).limit(50).all()

            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        avg_time = statistics.mean(times)

        print(f"\nSorted Query Performance ({iterations} iterations):")
        print(f"  Average: {avg_time:.3f}ms")
        print(f"  Results: {len(entries)} entries")

        # Sorted query with index should be very fast
        assert avg_time < 30, f"Sorted query too slow: {avg_time:.3f}ms"

    def test_category_query_performance(self, db_session):
        """Benchmark category-specific queries"""
        db, user = db_session

        iterations = 50
        times = []

        start_date = datetime.now() - timedelta(days=180)

        for _ in range(iterations):
            start = time.perf_counter()

            # This query should use idx_entries_user_category_date
            entries = db.query(Entry).filter(
                Entry.user_id == user.id,
                Entry.category_id == 5,
                Entry.date >= start_date.date()
            ).all()

            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        avg_time = statistics.mean(times)

        print(f"\nCategory Query Performance ({iterations} iterations):")
        print(f"  Average: {avg_time:.3f}ms")
        print(f"  Results: {len(entries)} entries")

        assert avg_time < 40, f"Category query too slow: {avg_time:.3f}ms"


class TestForecastCachePerformance:
    """Benchmark forecast with different cache tiers"""

    def test_database_cache_retrieval(self, db_session):
        """Benchmark database cache retrieval time"""
        db, user = db_session

        # Create cached forecast in database
        forecast = Forecast(
            user_id=user.id,
            forecast_type='total_spending',
            forecast_horizon_days=90,
            training_data_start=datetime.now() - timedelta(days=180),
            training_data_end=datetime.now(),
            training_data_points=180,
            forecast_data=[{'date': f'2025-{i:02d}-01', 'amount': i * 100} for i in range(1, 4)],
            summary={'total': 600},
            insights={'message': 'Test'},
            model_type='prophet',
            confidence_level=0.95,
            expires_at=datetime.utcnow() + timedelta(hours=24),
            is_active=True
        )
        db.add(forecast)
        db.commit()

        # Benchmark retrieval
        iterations = 50
        times = []

        for _ in range(iterations):
            start = time.perf_counter()

            # Query cached forecast (should use idx_forecasts_user_type_created)
            cached = db.query(Forecast).filter(
                Forecast.user_id == user.id,
                Forecast.forecast_type == 'total_spending',
                Forecast.forecast_horizon_days == 90,
                Forecast.is_active == True,
                Forecast.created_at >= datetime.utcnow() - timedelta(hours=24)
            ).order_by(Forecast.created_at.desc()).first()

            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        avg_time = statistics.mean(times)

        print(f"\nDatabase Cache Retrieval ({iterations} iterations):")
        print(f"  Average: {avg_time:.3f}ms")

        # Should be reasonably fast (target: ~100ms)
        assert avg_time < 150, f"DB cache retrieval too slow: {avg_time:.3f}ms"

    def test_redis_cache_retrieval(self):
        """Benchmark Redis cache retrieval time"""
        cache = get_cache()

        if not cache.enabled:
            pytest.skip("Redis not available")

        # Set up cached forecast
        forecast_data = {
            'forecast': [{'date': f'2025-{i:02d}-01', 'amount': i * 100} for i in range(1, 13)],
            'summary': {'total': 78000},
            'insights': {'message': 'Cached forecast'}
        }
        cache.set(
            cache._make_key('forecast', 123, 'total_spending', 90),
            forecast_data,
            ttl=3600
        )

        # Benchmark retrieval
        iterations = 100
        times = []

        for _ in range(iterations):
            start = time.perf_counter()

            result = cache.get(cache._make_key('forecast', 123, 'total_spending', 90))

            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        avg_time = statistics.mean(times)
        median_time = statistics.median(times)

        print(f"\nRedis Cache Retrieval ({iterations} iterations):")
        print(f"  Average: {avg_time:.3f}ms")
        print(f"  Median: {median_time:.3f}ms")

        # Redis should be very fast (target: ~15ms)
        assert avg_time < 20, f"Redis cache too slow: {avg_time:.3f}ms"


class TestMemoryUsage:
    """Test memory usage and efficiency"""

    def test_cache_memory_usage(self):
        """Monitor memory usage of cache operations"""
        cache = get_cache()

        if not cache.enabled:
            pytest.skip("Redis not available")

        # Get initial stats
        initial_stats = cache.get_stats()
        initial_memory = initial_stats.get('memory_used', '0')

        print(f"\nInitial Redis Memory: {initial_memory}")

        # Add 1000 cached items
        for i in range(1000):
            data = {
                'id': i,
                'forecast': [{'date': f'2025-{j:02d}-01', 'amount': j * 10} for j in range(1, 13)],
                'metadata': {'created': datetime.now().isoformat()}
            }
            cache.set(f'memory:test:{i}', data, ttl=3600)

        # Get final stats
        final_stats = cache.get_stats()
        final_memory = final_stats.get('memory_used', '0')

        print(f"Final Redis Memory: {final_memory}")
        print(f"Total Keys: {final_stats.get('total_keys', 0)}")

        # Clean up
        cache.delete_pattern('memory:test:*')

    def test_process_memory_usage(self, db_session):
        """Monitor process memory during operations"""
        process = psutil.Process(os.getpid())

        # Get initial memory
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        db, user = db_session

        # Perform memory-intensive operations
        for _ in range(10):
            entries = db.query(Entry).filter(Entry.user_id == user.id).all()

        # Get final memory
        final_memory = process.memory_info().rss / 1024 / 1024  # MB

        print(f"\nProcess Memory Usage:")
        print(f"  Initial: {initial_memory:.2f} MB")
        print(f"  Final: {final_memory:.2f} MB")
        print(f"  Increase: {final_memory - initial_memory:.2f} MB")


class TestCacheHitRates:
    """Measure cache hit/miss ratios"""

    def test_cache_hit_ratio_simulation(self):
        """Simulate realistic usage to measure hit rates"""
        cache = get_cache()

        if not cache.enabled:
            pytest.skip("Redis not available")

        # Clear cache for clean test
        cache.clear_all()

        hits = 0
        misses = 0

        # Simulate 100 requests with realistic patterns
        # 80% of requests are for the same 5 forecasts (high hit rate expected)
        popular_forecasts = [(123, 90), (123, 30), (456, 90), (789, 60), (999, 90)]

        for i in range(100):
            if i % 5 == 0:
                # 20% requests for random forecasts (will miss)
                user_id = 1000 + i
                days = 90
            else:
                # 80% requests for popular forecasts (will hit after first request)
                user_id, days = popular_forecasts[i % len(popular_forecasts)]

            key = cache._make_key('forecast', user_id, 'total', days)
            result = cache.get(key)

            if result is None:
                # Miss - set the value
                misses += 1
                cache.set(key, {'user': user_id, 'days': days}, ttl=3600)
            else:
                # Hit
                hits += 1

        total = hits + misses
        hit_rate = (hits / total * 100) if total > 0 else 0

        print(f"\nCache Hit Rate Simulation:")
        print(f"  Total Requests: {total}")
        print(f"  Hits: {hits}")
        print(f"  Misses: {misses}")
        print(f"  Hit Rate: {hit_rate:.1f}%")

        # With 80% popular requests, expect >60% hit rate
        assert hit_rate > 60, f"Hit rate too low: {hit_rate:.1f}%"


class TestComparisonBenchmark:
    """Compare performance: no cache vs DB cache vs Redis cache"""

    def test_three_tier_comparison(self, db_session):
        """Compare all three cache tiers"""
        db, user = db_session
        cache = get_cache()

        results = {}

        # 1. Database query (no cache)
        print("\n=== Three-Tier Performance Comparison ===\n")

        iterations = 20
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            entries = db.query(Entry).filter(
                Entry.user_id == user.id,
                Entry.type == 'expense'
            ).order_by(Entry.date.desc()).limit(50).all()
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        results['fresh_query'] = statistics.mean(times)
        print(f"Fresh DB Query (no cache): {results['fresh_query']:.3f}ms")

        # 2. Database cache lookup
        forecast = Forecast(
            user_id=user.id,
            forecast_type='total_spending',
            forecast_horizon_days=90,
            training_data_start=datetime.now() - timedelta(days=180),
            training_data_end=datetime.now(),
            training_data_points=180,
            forecast_data=[{'test': 'data'}],
            summary={},
            model_type='prophet',
            confidence_level=0.95,
            expires_at=datetime.utcnow() + timedelta(hours=24),
            is_active=True
        )
        db.add(forecast)
        db.commit()

        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            cached = db.query(Forecast).filter(
                Forecast.user_id == user.id,
                Forecast.forecast_type == 'total_spending'
            ).first()
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        results['db_cache'] = statistics.mean(times)
        print(f"Database Cache: {results['db_cache']:.3f}ms")

        # 3. Redis cache lookup
        if cache.enabled:
            cache.set('perf:compare:test', {'test': 'data'}, ttl=3600)

            times = []
            for _ in range(iterations):
                start = time.perf_counter()
                result = cache.get('perf:compare:test')
                elapsed = (time.perf_counter() - start) * 1000
                times.append(elapsed)

            results['redis_cache'] = statistics.mean(times)
            print(f"Redis Cache: {results['redis_cache']:.3f}ms")

            # Print speedup
            print(f"\nSpeedup:")
            print(f"  Redis vs DB Cache: {results['db_cache'] / results['redis_cache']:.1f}x faster")
            print(f"  Redis vs Fresh: {results['fresh_query'] / results['redis_cache']:.1f}x faster")
            print(f"  DB Cache vs Fresh: {results['fresh_query'] / results['db_cache']:.1f}x faster")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])  # -s to show print statements
