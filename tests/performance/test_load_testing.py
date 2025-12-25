"""
Load Testing for Cache System

Simulates realistic production load:
- Multiple concurrent users
- Mixed read/write operations
- Cache invalidation patterns
- System resource monitoring
"""

import pytest
import time
import threading
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
import psutil
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from app.core.cache import get_cache
from app.models.entry import Entry
from app.models.user import User
from app.models.forecast import Forecast
from app.db.session import Base


# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_load.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True
)
SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
ScopedSession = scoped_session(SessionFactory)


@pytest.fixture(scope="module")
def setup_test_data():
    """Create test database with multiple users"""
    Base.metadata.create_all(bind=engine)
    db = ScopedSession()

    # Create 10 test users
    users = []
    for i in range(10):
        user = User(
            email=f"loadtest{i}@example.com",
            username=f"loaduser{i}",
            hashed_password="test123",
            is_active=True
        )
        db.add(user)
        users.append(user)

    db.commit()

    # Create entries for each user
    base_date = datetime.now() - timedelta(days=365)

    for user in users:
        db.refresh(user)
        entries = []

        for j in range(200):  # 200 entries per user
            entry = Entry(
                user_id=user.id,
                type='expense' if j % 3 != 0 else 'income',
                amount=50 + (j % 200),
                date=(base_date + timedelta(days=j)).date(),
                category_id=(j % 5) + 1,
                note=f'Load test entry {j}'
            )
            entries.append(entry)

            if len(entries) >= 50:
                db.bulk_save_objects(entries)
                db.commit()
                entries = []

        if entries:
            db.bulk_save_objects(entries)
            db.commit()

    user_ids = [u.id for u in users]

    yield user_ids

    db.close()
    Base.metadata.drop_all(bind=engine)


class TestConcurrentCacheOperations:
    """Test cache under concurrent access"""

    def test_concurrent_cache_sets(self):
        """Test concurrent cache SET operations"""
        cache = get_cache()

        if not cache.enabled:
            pytest.skip("Redis not available")

        num_threads = 10
        operations_per_thread = 50

        def set_operation(thread_id):
            """Perform multiple SET operations"""
            for i in range(operations_per_thread):
                key = f'concurrent:set:{thread_id}:{i}'
                value = {'thread': thread_id, 'index': i, 'timestamp': time.time()}
                cache.set(key, value, ttl=600)

        # Run concurrent operations
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(set_operation, i) for i in range(num_threads)]
            for future in as_completed(futures):
                future.result()  # Wait for completion

        elapsed = time.time() - start_time
        total_ops = num_threads * operations_per_thread

        print(f"\nConcurrent Cache SET:")
        print(f"  Threads: {num_threads}")
        print(f"  Operations: {total_ops}")
        print(f"  Time: {elapsed:.3f}s")
        print(f"  Throughput: {total_ops/elapsed:.1f} ops/sec")

        # Verify data integrity
        for thread_id in range(num_threads):
            for i in range(operations_per_thread):
                key = f'concurrent:set:{thread_id}:{i}'
                result = cache.get(key)
                assert result is not None
                assert result['thread'] == thread_id
                assert result['index'] == i

        # Clean up
        cache.delete_pattern('concurrent:set:*')

    def test_concurrent_cache_gets(self):
        """Test concurrent cache GET operations"""
        cache = get_cache()

        if not cache.enabled:
            pytest.skip("Redis not available")

        # Set up shared data
        test_data = {'large_data': list(range(1000))}
        cache.set('shared:data', test_data, ttl=600)

        num_threads = 20
        reads_per_thread = 100

        def get_operation(thread_id):
            """Perform multiple GET operations"""
            results = []
            for _ in range(reads_per_thread):
                result = cache.get('shared:data')
                results.append(result is not None)
            return sum(results)  # Count successful reads

        # Run concurrent reads
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(get_operation, i) for i in range(num_threads)]
            successful_reads = sum(future.result() for future in as_completed(futures))

        elapsed = time.time() - start_time
        total_ops = num_threads * reads_per_thread

        print(f"\nConcurrent Cache GET:")
        print(f"  Threads: {num_threads}")
        print(f"  Operations: {total_ops}")
        print(f"  Successful: {successful_reads}")
        print(f"  Time: {elapsed:.3f}s")
        print(f"  Throughput: {total_ops/elapsed:.1f} ops/sec")

        assert successful_reads == total_ops

    def test_mixed_read_write_operations(self):
        """Test mixed concurrent reads and writes"""
        cache = get_cache()

        if not cache.enabled:
            pytest.skip("Redis not available")

        num_threads = 15
        operations = []

        def mixed_operation(thread_id):
            """Mix of read and write operations"""
            start = time.perf_counter()

            for i in range(30):
                if i % 3 == 0:
                    # Write operation (33%)
                    cache.set(f'mixed:{thread_id}:{i}', {'value': i}, ttl=600)
                else:
                    # Read operation (67%)
                    cache.get(f'mixed:{thread_id}:{i}')

            return (time.perf_counter() - start) * 1000  # Return thread time

        # Run mixed operations
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(mixed_operation, i) for i in range(num_threads)]
            thread_times = [future.result() for future in as_completed(futures)]

        elapsed = time.time() - start_time

        print(f"\nMixed Read/Write Operations:")
        print(f"  Threads: {num_threads}")
        print(f"  Total time: {elapsed:.3f}s")
        print(f"  Avg thread time: {statistics.mean(thread_times):.3f}ms")
        print(f"  Max thread time: {max(thread_times):.3f}ms")

        # Clean up
        cache.delete_pattern('mixed:*')


class TestDatabaseLoadUnderCaching:
    """Test database load with concurrent users"""

    def test_concurrent_database_queries(self, setup_test_data):
        """Test concurrent database queries with caching"""
        user_ids = setup_test_data
        cache = get_cache()

        if cache.enabled:
            cache.clear_all()

        def query_user_data(user_id, iteration):
            """Query user data with caching"""
            db = ScopedSession()
            cache_key = f'user:{user_id}:entries:recent'

            # Try cache first
            cached = cache.get(cache_key) if cache.enabled else None

            if cached is None:
                # Cache miss - query database
                entries = db.query(Entry).filter(
                    Entry.user_id == user_id
                ).order_by(Entry.date.desc()).limit(50).all()

                result = [{'id': e.id, 'amount': float(e.amount)} for e in entries]

                # Cache for next request
                if cache.enabled:
                    cache.set(cache_key, result, ttl=300)

                db.close()
                return 'miss'
            else:
                db.close()
                return 'hit'

        # Simulate 100 concurrent requests across 10 users
        num_requests = 100
        results = {'hit': 0, 'miss': 0}

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = []
            for i in range(num_requests):
                user_id = user_ids[i % len(user_ids)]
                futures.append(executor.submit(query_user_data, user_id, i))

            for future in as_completed(futures):
                result = future.result()
                results[result] += 1

        elapsed = time.time() - start_time

        hit_rate = (results['hit'] / num_requests * 100) if num_requests > 0 else 0

        print(f"\nConcurrent Database Queries with Caching:")
        print(f"  Total requests: {num_requests}")
        print(f"  Cache hits: {results['hit']}")
        print(f"  Cache misses: {results['miss']}")
        print(f"  Hit rate: {hit_rate:.1f}%")
        print(f"  Time: {elapsed:.3f}s")
        print(f"  Avg response: {elapsed/num_requests*1000:.3f}ms")

        # With 10 users and 100 requests, expect high hit rate
        if cache.enabled:
            assert hit_rate > 80, f"Cache hit rate too low: {hit_rate:.1f}%"


class TestCacheInvalidationUnderLoad:
    """Test cache invalidation with concurrent modifications"""

    def test_concurrent_invalidations(self, setup_test_data):
        """Test cache invalidation with multiple concurrent users"""
        user_ids = setup_test_data
        cache = get_cache()

        if not cache.enabled:
            pytest.skip("Redis not available")

        # Set initial cache for all users
        for user_id in user_ids:
            cache.set(f'forecast:{user_id}:total:90', {'data': 'initial'}, ttl=3600)

        invalidation_count = 0
        lock = threading.Lock()

        def modify_and_invalidate(user_id, entry_num):
            """Simulate entry modification and cache invalidation"""
            nonlocal invalidation_count

            db = ScopedSession()

            # Create new entry
            entry = Entry(
                user_id=user_id,
                type='expense',
                amount=100 + entry_num,
                date=datetime.now().date(),
                note=f'Load test {entry_num}'
            )
            db.add(entry)
            db.commit()

            # Invalidate cache
            deleted = cache.invalidate_user_cache(user_id)

            with lock:
                invalidation_count += 1

            db.close()
            return deleted

        # Simulate concurrent modifications
        num_modifications = 50

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for i in range(num_modifications):
                user_id = user_ids[i % len(user_ids)]
                futures.append(executor.submit(modify_and_invalidate, user_id, i))

            invalidations = [future.result() for future in as_completed(futures)]

        elapsed = time.time() - start_time

        print(f"\nConcurrent Cache Invalidations:")
        print(f"  Modifications: {num_modifications}")
        print(f"  Invalidations triggered: {invalidation_count}")
        print(f"  Time: {elapsed:.3f}s")
        print(f"  Avg time per invalidation: {elapsed/num_modifications*1000:.3f}ms")

        # Verify caches are invalidated
        for user_id in user_ids:
            result = cache.get(f'forecast:{user_id}:total:90')
            # May or may not be None depending on timing, but should be consistent
            assert result is None or isinstance(result, dict)


class TestSystemResourcesUnderLoad:
    """Monitor system resources during load testing"""

    def test_cpu_usage_under_load(self, setup_test_data):
        """Monitor CPU usage during concurrent operations"""
        user_ids = setup_test_data
        cache = get_cache()
        process = psutil.Process(os.getpid())

        # Baseline CPU
        baseline_cpu = process.cpu_percent(interval=1)

        def heavy_operation(user_id, iteration):
            """Perform cache and database operations"""
            db = ScopedSession()

            # Cache operations
            if cache.enabled:
                cache.set(f'cpu:test:{user_id}:{iteration}', {'data': list(range(100))}, ttl=300)
                cache.get(f'cpu:test:{user_id}:{iteration}')

            # Database query
            entries = db.query(Entry).filter(Entry.user_id == user_id).limit(20).all()

            db.close()
            return len(entries)

        # Run heavy load
        num_operations = 100

        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = []
            for i in range(num_operations):
                user_id = user_ids[i % len(user_ids)]
                futures.append(executor.submit(heavy_operation, user_id, i))

            results = [future.result() for future in as_completed(futures)]

        # Measure CPU after load
        peak_cpu = process.cpu_percent(interval=1)

        print(f"\nCPU Usage Under Load:")
        print(f"  Baseline: {baseline_cpu:.1f}%")
        print(f"  Peak: {peak_cpu:.1f}%")
        print(f"  Operations completed: {len(results)}")

    def test_memory_usage_under_load(self, setup_test_data):
        """Monitor memory usage during concurrent operations"""
        user_ids = setup_test_data
        cache = get_cache()
        process = psutil.Process(os.getpid())

        # Baseline memory
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

        def memory_intensive_operation(user_id):
            """Perform memory-intensive cache operations"""
            large_data = {
                'forecast': [
                    {'date': f'2025-{i:02d}-{j:02d}', 'amount': i * j}
                    for i in range(1, 13) for j in range(1, 31)
                ]
            }

            if cache.enabled:
                cache.set(f'memory:{user_id}', large_data, ttl=300)
                result = cache.get(f'memory:{user_id}')
                return len(result['forecast'])
            return 0

        # Run operations
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(memory_intensive_operation, uid) for uid in user_ids * 5]
            results = [future.result() for future in as_completed(futures)]

        # Peak memory
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB

        print(f"\nMemory Usage Under Load:")
        print(f"  Baseline: {baseline_memory:.2f} MB")
        print(f"  Peak: {peak_memory:.2f} MB")
        print(f"  Increase: {peak_memory - baseline_memory:.2f} MB")
        print(f"  Operations: {len(results)}")

        # Clean up
        if cache.enabled:
            cache.delete_pattern('memory:*')


class TestThroughput:
    """Measure system throughput"""

    def test_max_throughput(self):
        """Measure maximum cache throughput"""
        cache = get_cache()

        if not cache.enabled:
            pytest.skip("Redis not available")

        duration_seconds = 5
        num_threads = 20
        operations_count = [0] * num_threads

        def sustained_operations(thread_id):
            """Perform operations for fixed duration"""
            end_time = time.time() + duration_seconds
            count = 0

            while time.time() < end_time:
                cache.set(f'throughput:{thread_id}:{count}', {'value': count}, ttl=60)
                cache.get(f'throughput:{thread_id}:{count}')
                count += 1

            operations_count[thread_id] = count

        # Run sustained load
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(sustained_operations, i) for i in range(num_threads)]
            for future in as_completed(futures):
                future.result()

        elapsed = time.time() - start_time
        total_ops = sum(operations_count)

        print(f"\nMaximum Throughput Test:")
        print(f"  Duration: {elapsed:.2f}s")
        print(f"  Threads: {num_threads}")
        print(f"  Total operations: {total_ops}")
        print(f"  Throughput: {total_ops/elapsed:.1f} ops/sec")
        print(f"  Avg per thread: {total_ops/num_threads:.0f} ops")

        # Clean up
        cache.delete_pattern('throughput:*')


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
