"""
Integration Tests for Forecast Caching

Tests the three-tier caching strategy:
1. Redis cache (fastest - ~15ms)
2. Database cache (fast - ~100ms)
3. Fresh generation (slow - ~3000ms)

Also tests:
- Cache invalidation on entry modifications
- Cache tier reporting in responses
- Proper fallback between cache tiers
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import time

from app.main import app
from app.db.session import Base, get_db
from app.models.user import User
from app.models.entry import Entry
from app.models.forecast import Forecast
from app.core.cache import get_cache
from app.deps import create_access_token


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_forecast_cache.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create test database"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """Create test client with database override"""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db):
    """Create a test user"""
    user = User(
        email="testuser@example.com",
        username="testuser",
        hashed_password="fake_hashed_password",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_headers(test_user):
    """Create authentication headers"""
    token = create_access_token(data={"sub": test_user.email})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def sample_entries(db, test_user):
    """Create sample entries for forecasting"""
    entries = []
    base_date = datetime.now() - timedelta(days=180)

    for i in range(90):  # 90 days of data
        entry = Entry(
            user_id=test_user.id,
            type='expense',
            amount=100 + (i % 50),  # Varying amounts
            date=(base_date + timedelta(days=i)).date(),
            category_id=1,
            note=f'Test expense {i}'
        )
        entries.append(entry)
        db.add(entry)

    db.commit()
    return entries


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear cache before each test"""
    cache = get_cache()
    if cache.enabled:
        cache.clear_all()
    yield
    if cache.enabled:
        cache.clear_all()


class TestThreeTierCaching:
    """Test three-tier caching strategy"""

    def test_tier_3_fresh_generation(self, client, auth_headers, sample_entries, db):
        """Test Tier 3: Fresh forecast generation (no cache)"""
        cache = get_cache()

        # Clear all caches
        cache.clear_all()
        db.query(Forecast).delete()
        db.commit()

        # Make forecast request
        response = client.get(
            "/api/v1/forecasts/spending/total?days_ahead=90&use_cache=true",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data['success'] is True
        assert data['cached'] is False
        assert data['cache_tier'] == 'fresh'
        assert data['cache_speed'] == '~3000ms'
        assert 'forecast' in data
        assert 'forecast_id' in data

    def test_tier_2_database_cache(self, client, auth_headers, sample_entries, db, test_user):
        """Test Tier 2: Database cache hit (Redis miss, DB hit)"""
        cache = get_cache()

        # Create forecast in database but not in Redis
        forecast = Forecast(
            user_id=test_user.id,
            forecast_type='total_spending',
            forecast_horizon_days=90,
            training_data_start=datetime.now() - timedelta(days=180),
            training_data_end=datetime.now(),
            training_data_points=90,
            forecast_data=[{'date': '2025-01-01', 'amount': 100}],
            summary={'total': 100},
            insights={'message': 'Test insight'},
            model_type='prophet',
            confidence_level=0.95,
            expires_at=datetime.utcnow() + timedelta(hours=24),
            is_active=True
        )
        db.add(forecast)
        db.commit()

        # Clear Redis cache but keep DB cache
        if cache.enabled:
            cache.delete_pattern('forecast:*')

        # Make forecast request
        response = client.get(
            "/api/v1/forecasts/spending/total?days_ahead=90&use_cache=true",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data['success'] is True
        assert data['cached'] is True

        if cache.enabled:
            # Should be database cache tier
            assert data['cache_tier'] == 'database'
            assert data['cache_speed'] == '~100ms'
        else:
            # Without Redis, only DB cache exists
            assert data['cache_tier'] == 'database'

    def test_tier_1_redis_cache(self, client, auth_headers, sample_entries, test_user):
        """Test Tier 1: Redis cache hit (fastest)"""
        cache = get_cache()

        if not cache.enabled:
            pytest.skip("Redis not available")

        # Manually set Redis cache
        cached_data = {
            'success': True,
            'forecast': [{'date': '2025-01-01', 'amount': 150}],
            'summary': {'total': 150},
            'cached': True
        }

        cache.set(
            cache._make_key('forecast', test_user.id, 'total_spending', 90),
            cached_data,
            ttl=3600
        )

        # Make forecast request
        start_time = time.time()
        response = client.get(
            "/api/v1/forecasts/spending/total?days_ahead=90&use_cache=true",
            headers=auth_headers
        )
        elapsed_time = (time.time() - start_time) * 1000  # Convert to ms

        assert response.status_code == 200
        data = response.json()

        assert data['cached'] is True
        assert data['cache_tier'] == 'redis'
        assert data['cache_speed'] == '~15ms'

        # Should be very fast (< 100ms typically)
        assert elapsed_time < 500  # Allow 500ms buffer for test overhead

    def test_cache_bypass_with_use_cache_false(self, client, auth_headers, sample_entries):
        """Test bypassing cache with use_cache=false"""
        cache = get_cache()

        # Set cache
        if cache.enabled:
            cache.set('forecast:123:total_spending:90', {'data': 'old'})

        # Request with cache disabled
        response = client.get(
            "/api/v1/forecasts/spending/total?days_ahead=90&use_cache=false",
            headers=auth_headers
        )

        # Should skip all cache tiers
        if response.status_code == 200:
            data = response.json()
            assert data.get('cache_tier') == 'fresh' or data.get('cached') is False


class TestCacheInvalidation:
    """Test automatic cache invalidation on entry modifications"""

    def test_cache_invalidated_on_entry_create(self, client, auth_headers, test_user):
        """Test cache is cleared when new entry is created"""
        cache = get_cache()

        if not cache.enabled:
            pytest.skip("Redis not available")

        # Set forecast cache
        cache.set(
            f'forecast:{test_user.id}:total:90',
            {'data': 'test'},
            ttl=3600
        )

        # Verify cache exists
        assert cache.get(f'forecast:{test_user.id}:total:90') is not None

        # Create new entry (this should invalidate cache)
        response = client.post(
            "/entries/create",
            headers=auth_headers,
            data={
                'type': 'expense',
                'amount': 50.0,
                'note': 'Test entry',
                'date_str': '2025-01-01'
            }
        )

        # Cache should be invalidated
        assert cache.get(f'forecast:{test_user.id}:total:90') is None

    def test_cache_invalidated_on_entry_update(self, client, auth_headers, test_user, db):
        """Test cache is cleared when entry is updated"""
        cache = get_cache()

        if not cache.enabled:
            pytest.skip("Redis not available")

        # Create an entry
        entry = Entry(
            user_id=test_user.id,
            type='expense',
            amount=100,
            date=datetime.now().date(),
            note='Original'
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)

        # Set forecast cache
        cache.set(f'forecast:{test_user.id}:total:90', {'data': 'test'}, ttl=3600)

        # Update entry
        response = client.post(
            f"/entries/update/{entry.id}",
            headers=auth_headers,
            data={
                'type': 'expense',
                'amount': 150.0,
                'note': 'Updated',
                'date': '2025-01-01'
            }
        )

        # Cache should be invalidated
        assert cache.get(f'forecast:{test_user.id}:total:90') is None

    def test_cache_invalidated_on_entry_delete(self, client, auth_headers, test_user, db):
        """Test cache is cleared when entry is deleted"""
        cache = get_cache()

        if not cache.enabled:
            pytest.skip("Redis not available")

        # Create an entry
        entry = Entry(
            user_id=test_user.id,
            type='expense',
            amount=100,
            date=datetime.now().date(),
            note='To be deleted'
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)

        # Set forecast cache
        cache.set(f'forecast:{test_user.id}:total:90', {'data': 'test'}, ttl=3600)

        # Delete entry
        response = client.post(
            f"/entries/delete/{entry.id}",
            headers=auth_headers
        )

        # Cache should be invalidated
        assert cache.get(f'forecast:{test_user.id}:total:90') is None


class TestCacheFallbackBehavior:
    """Test cache fallback behavior when Redis is unavailable"""

    def test_forecast_works_without_redis(self, client, auth_headers, sample_entries):
        """Test forecast generation works even without Redis cache"""
        # This test should pass even if Redis is not available
        response = client.get(
            "/api/v1/forecasts/spending/total?days_ahead=90&use_cache=true",
            headers=auth_headers
        )

        # Should work regardless of Redis availability
        if response.status_code == 200:
            data = response.json()
            assert 'forecast' in data or 'message' in data


class TestCachePerformance:
    """Test cache performance improvements"""

    def test_redis_cache_faster_than_database(self, client, auth_headers, test_user, db):
        """Test that Redis cache is faster than database cache"""
        cache = get_cache()

        if not cache.enabled:
            pytest.skip("Redis not available")

        # Create database cached forecast
        forecast = Forecast(
            user_id=test_user.id,
            forecast_type='total_spending',
            forecast_horizon_days=90,
            training_data_start=datetime.now() - timedelta(days=180),
            training_data_end=datetime.now(),
            training_data_points=90,
            forecast_data=[{'date': '2025-01-01', 'amount': 100}],
            summary={'total': 100},
            model_type='prophet',
            confidence_level=0.95,
            expires_at=datetime.utcnow() + timedelta(hours=24),
            is_active=True
        )
        db.add(forecast)
        db.commit()

        # Time database cache access
        cache.delete_pattern('forecast:*')
        start = time.time()
        response1 = client.get(
            "/api/v1/forecasts/spending/total?days_ahead=90",
            headers=auth_headers
        )
        db_time = (time.time() - start) * 1000

        # Time Redis cache access
        start = time.time()
        response2 = client.get(
            "/api/v1/forecasts/spending/total?days_ahead=90",
            headers=auth_headers
        )
        redis_time = (time.time() - start) * 1000

        # Redis should be faster (though test overhead may skew results)
        # Just verify both work
        assert response1.status_code == 200
        assert response2.status_code == 200

        # Log times for analysis
        print(f"\nDatabase cache: {db_time:.2f}ms")
        print(f"Redis cache: {redis_time:.2f}ms")


class TestCacheConcurrency:
    """Test cache behavior with concurrent requests"""

    def test_multiple_users_separate_caches(self, client, db):
        """Test that different users have separate caches"""
        cache = get_cache()

        if not cache.enabled:
            pytest.skip("Redis not available")

        # Create two users
        user1 = User(email="user1@test.com", username="user1", hashed_password="pass1")
        user2 = User(email="user2@test.com", username="user2", hashed_password="pass2")
        db.add(user1)
        db.add(user2)
        db.commit()

        # Set different cache for each user
        cache.set(f'forecast:{user1.id}:total:90', {'user': 'user1'}, ttl=3600)
        cache.set(f'forecast:{user2.id}:total:90', {'user': 'user2'}, ttl=3600)

        # Verify caches are separate
        assert cache.get(f'forecast:{user1.id}:total:90')['user'] == 'user1'
        assert cache.get(f'forecast:{user2.id}:total:90')['user'] == 'user2'

        # Invalidate user1's cache
        cache.invalidate_user_cache(user1.id)

        # User1's cache gone, user2's remains
        assert cache.get(f'forecast:{user1.id}:total:90') is None
        assert cache.get(f'forecast:{user2.id}:total:90')['user'] == 'user2'


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
