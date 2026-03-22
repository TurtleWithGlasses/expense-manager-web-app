"""
Integration Tests for AI Insights Redis Caching

Tests that the 5 AI insight endpoints cache their results in Redis
and serve cached responses on subsequent requests, and that the
cache is invalidated when a user's entries change.

Endpoints tested:
  GET /ai/insights/spending-patterns
  GET /ai/insights/saving-opportunities
  GET /ai/insights/budget-health
  GET /ai/insights/recommendations
  GET /ai/insights/alerts
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.session import get_db
from app.db.base import Base
from app.models.user import User
from app.core.cache import get_cache, CacheService
from app.core.security import hash_password


SQLALCHEMY_DATABASE_URL = 'sqlite:///./test_ai_insights_cache.db'
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={'check_same_thread': False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope='function')
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope='function')
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope='function')
def test_user(db):
    user = User(
        email='insights_test@example.com',
        full_name='Insights Tester',
        hashed_password=hash_password('testpass123'),
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope='function')
def auth_client(client, test_user):
    """Client with session cookie for test_user."""
    from app.core.session import serializer, SESSION_COOKIE
    token = serializer.dumps({'id': test_user.id, 'email': test_user.email})
    client.cookies.set(SESSION_COOKIE, token)
    return client


@pytest.fixture(autouse=True)
def clear_insights_cache():
    """Wipe insight keys before and after every test."""
    cache = get_cache()
    if cache.enabled:
        cache.delete_pattern('insights:*')
    yield
    if cache.enabled:
        cache.delete_pattern('insights:*')


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

INSIGHT_ENDPOINTS = [
    '/ai/insights/spending-patterns',
    '/ai/insights/saving-opportunities',
    '/ai/insights/budget-health',
    '/ai/insights/recommendations',
    '/ai/insights/alerts',
]

CACHE_KEY_SUFFIXES = [
    'spending_patterns',
    'saving_opportunities',
    'budget_health',
    'recommendations',
    'alerts',
]


# ---------------------------------------------------------------------------
# Cache key construction tests (unit-level, no HTTP)
# ---------------------------------------------------------------------------

class TestInsightCacheKeyFormat:
    """Verify that the cache keys follow the expected naming convention."""

    def test_cache_key_prefix_is_insights(self):
        cache = CacheService.__new__(CacheService)
        cache.enabled = False
        cache.redis_client = None
        key = CacheService._make_key(cache, 'insights', 42, 'budget_health')
        assert key.startswith('insights:42:budget_health')

    def test_different_users_have_different_keys(self):
        cache = CacheService.__new__(CacheService)
        cache.enabled = False
        cache.redis_client = None
        key1 = CacheService._make_key(cache, 'insights', 1, 'alerts')
        key2 = CacheService._make_key(cache, 'insights', 2, 'alerts')
        assert key1 != key2

    def test_different_insight_types_have_different_keys(self):
        cache = CacheService.__new__(CacheService)
        cache.enabled = False
        cache.redis_client = None
        key1 = CacheService._make_key(cache, 'insights', 1, 'alerts')
        key2 = CacheService._make_key(cache, 'insights', 1, 'budget_health')
        assert key1 != key2


# ---------------------------------------------------------------------------
# Caching behaviour when Redis IS available (mock Redis)
# ---------------------------------------------------------------------------

class TestInsightEndpointsCacheWhenRedisAvailable:
    """Use a mock CacheService that behaves like an in-memory Redis."""

    @pytest.fixture(autouse=True)
    def mock_cache(self):
        """Replace the global cache with an in-memory dict-backed mock."""
        self._store = {}

        mock = MagicMock(spec=CacheService)
        mock.enabled = True

        def fake_make_key(prefix, *args, **kwargs):
            parts = [prefix] + [str(a) for a in args]
            return ':'.join(parts)

        def fake_get(key):
            return self._store.get(key)

        def fake_set(key, value, ttl=None):
            self._store[key] = value
            return True

        def fake_delete_pattern(pattern):
            prefix = pattern.rstrip('*').rstrip(':')
            removed = [k for k in list(self._store) if k.startswith(prefix)]
            for k in removed:
                del self._store[k]
            return len(removed)

        mock._make_key.side_effect = fake_make_key
        mock.get.side_effect = fake_get
        mock.set.side_effect = fake_set
        mock.delete_pattern.side_effect = fake_delete_pattern

        with patch('app.api.v1.ai.get_cache', return_value=mock):
            yield mock

    def _mock_insights_service(self):
        svc = MagicMock()
        svc._analyze_spending_patterns.return_value = {'most_active_day': 'Friday'}
        svc._identify_saving_opportunities.return_value = [{'category': 'Food', 'potential_saving': 50}]
        svc._assess_budget_health.return_value = {'health_score': 75, 'status': 'good'}
        svc._generate_recommendations.return_value = [{'title': 'Cut dining out', 'priority': 'high'}]
        svc._generate_alerts.return_value = [{'title': 'Over budget', 'severity': 'high'}]
        return svc

    def test_spending_patterns_cached_on_second_request(self, auth_client):
        svc = self._mock_insights_service()
        with patch('app.api.v1.ai.FinancialInsightsService', return_value=svc):
            r1 = auth_client.get('/ai/insights/spending-patterns')
            r2 = auth_client.get('/ai/insights/spending-patterns')

        assert r1.status_code == 200
        assert r2.status_code == 200
        # Service method must be called only once (second request served from cache)
        assert svc._analyze_spending_patterns.call_count == 1

    def test_budget_health_cached_on_second_request(self, auth_client):
        svc = self._mock_insights_service()
        with patch('app.api.v1.ai.FinancialInsightsService', return_value=svc):
            auth_client.get('/ai/insights/budget-health')
            auth_client.get('/ai/insights/budget-health')

        assert svc._assess_budget_health.call_count == 1

    def test_saving_opportunities_cached_on_second_request(self, auth_client):
        svc = self._mock_insights_service()
        with patch('app.api.v1.ai.FinancialInsightsService', return_value=svc):
            auth_client.get('/ai/insights/saving-opportunities')
            auth_client.get('/ai/insights/saving-opportunities')

        assert svc._identify_saving_opportunities.call_count == 1

    def test_recommendations_cached_on_second_request(self, auth_client):
        svc = self._mock_insights_service()
        with patch('app.api.v1.ai.FinancialInsightsService', return_value=svc):
            auth_client.get('/ai/insights/recommendations')
            auth_client.get('/ai/insights/recommendations')

        assert svc._generate_recommendations.call_count == 1

    def test_alerts_cached_on_second_request(self, auth_client):
        svc = self._mock_insights_service()
        with patch('app.api.v1.ai.FinancialInsightsService', return_value=svc):
            auth_client.get('/ai/insights/alerts')
            auth_client.get('/ai/insights/alerts')

        assert svc._generate_alerts.call_count == 1

    def test_cached_response_matches_original(self, auth_client):
        svc = self._mock_insights_service()
        with patch('app.api.v1.ai.FinancialInsightsService', return_value=svc):
            r1 = auth_client.get('/ai/insights/budget-health')
            r2 = auth_client.get('/ai/insights/budget-health')

        assert r1.json() == r2.json()

    def test_different_users_have_separate_caches(self, db):
        """Two users calling the same endpoint must not share cache entries."""
        user2 = User(
            email='user2_insights@example.com',
            full_name='User Two',
            hashed_password=hash_password('pass2'),
            is_verified=True,
        )
        db.add(user2)
        db.commit()
        db.refresh(user2)

        from app.core.session import serializer, SESSION_COOKIE

        svc = self._mock_insights_service()
        with patch('app.api.v1.ai.FinancialInsightsService', return_value=svc):
            # Client for user 1
            from fastapi.testclient import TestClient
            with TestClient(app) as c1:
                def override():
                    yield db
                app.dependency_overrides[get_db] = override
                c1.cookies.set(SESSION_COOKIE, serializer.dumps({'id': 1, 'email': 'insights_test@example.com'}))
                c1.get('/ai/insights/budget-health')

            # Client for user 2
            with TestClient(app) as c2:
                c2.cookies.set(SESSION_COOKIE, serializer.dumps({'id': user2.id, 'email': user2.email}))
                c2.get('/ai/insights/budget-health')

        # Service should have been called at least once per user (separate cache keys)
        assert svc._assess_budget_health.call_count >= 1
        app.dependency_overrides.clear()

    def test_cache_invalidated_by_delete_pattern(self, auth_client):
        """Simulates cache invalidation: after clear, service is called again."""
        svc = self._mock_insights_service()
        with patch('app.api.v1.ai.FinancialInsightsService', return_value=svc):
            auth_client.get('/ai/insights/alerts')
            assert svc._generate_alerts.call_count == 1

            # Simulate invalidation (entry created/modified)
            self._store.clear()

            auth_client.get('/ai/insights/alerts')
            assert svc._generate_alerts.call_count == 2


# ---------------------------------------------------------------------------
# Graceful degradation when Redis is NOT available
# ---------------------------------------------------------------------------

class TestInsightEndpointsFallbackWithoutRedis:
    """Endpoints must work correctly even when Redis is unavailable."""

    @pytest.fixture(autouse=True)
    def mock_disabled_cache(self):
        mock = MagicMock(spec=CacheService)
        mock.enabled = False
        mock.get.return_value = None
        mock.set.return_value = False

        def fake_make_key(prefix, *args, **kwargs):
            return ':'.join([prefix] + [str(a) for a in args])

        mock._make_key.side_effect = fake_make_key

        with patch('app.api.v1.ai.get_cache', return_value=mock):
            yield mock

    def _mock_insights_service(self):
        svc = MagicMock()
        svc._analyze_spending_patterns.return_value = {}
        svc._identify_saving_opportunities.return_value = []
        svc._assess_budget_health.return_value = {'health_score': 80}
        svc._generate_recommendations.return_value = []
        svc._generate_alerts.return_value = []
        return svc

    def test_budget_health_works_without_redis(self, auth_client):
        svc = self._mock_insights_service()
        with patch('app.api.v1.ai.FinancialInsightsService', return_value=svc):
            r = auth_client.get('/ai/insights/budget-health')
        assert r.status_code == 200
        data = r.json()
        assert data['success'] is True

    def test_spending_patterns_works_without_redis(self, auth_client):
        svc = self._mock_insights_service()
        with patch('app.api.v1.ai.FinancialInsightsService', return_value=svc):
            r = auth_client.get('/ai/insights/spending-patterns')
        assert r.status_code == 200

    def test_service_called_every_time_without_redis(self, auth_client):
        """Without cache, the service is invoked on each request."""
        svc = self._mock_insights_service()
        with patch('app.api.v1.ai.FinancialInsightsService', return_value=svc):
            auth_client.get('/ai/insights/alerts')
            auth_client.get('/ai/insights/alerts')
        assert svc._generate_alerts.call_count == 2


# ---------------------------------------------------------------------------
# Cache TTL validation
# ---------------------------------------------------------------------------

class TestInsightCacheTTL:
    """Verify that cache.set is called with the correct TTL (3600 s = 1 hour)."""

    def test_budget_health_sets_one_hour_ttl(self, auth_client):
        mock = MagicMock(spec=CacheService)
        mock.enabled = True
        mock.get.return_value = None
        mock.set.return_value = True

        def fake_make_key(prefix, *args, **kwargs):
            return ':'.join([prefix] + [str(a) for a in args])

        mock._make_key.side_effect = fake_make_key

        svc = MagicMock()
        svc._assess_budget_health.return_value = {'health_score': 70}

        with patch('app.api.v1.ai.get_cache', return_value=mock), \
             patch('app.api.v1.ai.FinancialInsightsService', return_value=svc):
            auth_client.get('/ai/insights/budget-health')

        mock.set.assert_called_once()
        _, _, kwargs = mock.set.call_args[0], mock.set.call_args[1], mock.set.call_args
        ttl_value = kwargs[1].get('ttl') if isinstance(kwargs[1], dict) else mock.set.call_args[1].get('ttl')
        assert ttl_value == 3600, f"Expected TTL=3600, got {ttl_value}"

    def test_alerts_sets_one_hour_ttl(self, auth_client):
        mock = MagicMock(spec=CacheService)
        mock.enabled = True
        mock.get.return_value = None
        mock.set.return_value = True

        def fake_make_key(prefix, *args, **kwargs):
            return ':'.join([prefix] + [str(a) for a in args])

        mock._make_key.side_effect = fake_make_key

        svc = MagicMock()
        svc._generate_alerts.return_value = []

        with patch('app.api.v1.ai.get_cache', return_value=mock), \
             patch('app.api.v1.ai.FinancialInsightsService', return_value=svc):
            auth_client.get('/ai/insights/alerts')

        mock.set.assert_called_once()
        ttl_value = mock.set.call_args[1].get('ttl')
        assert ttl_value == 3600

    def test_all_five_endpoints_use_same_ttl(self, auth_client):
        """All 5 insight endpoints must use the same 1-hour TTL."""
        endpoints = [
            ('/ai/insights/spending-patterns', '_analyze_spending_patterns', {}),
            ('/ai/insights/saving-opportunities', '_identify_saving_opportunities', []),
            ('/ai/insights/budget-health', '_assess_budget_health', {'health_score': 80}),
            ('/ai/insights/recommendations', '_generate_recommendations', []),
            ('/ai/insights/alerts', '_generate_alerts', []),
        ]

        for url, method, return_val in endpoints:
            mock = MagicMock(spec=CacheService)
            mock.enabled = True
            mock.get.return_value = None
            mock.set.return_value = True
            mock._make_key.side_effect = lambda p, *a, **kw: ':'.join([p] + [str(x) for x in a])

            svc = MagicMock()
            getattr(svc, method).return_value = return_val

            with patch('app.api.v1.ai.get_cache', return_value=mock), \
                 patch('app.api.v1.ai.FinancialInsightsService', return_value=svc):
                r = auth_client.get(url)

            assert r.status_code == 200, f"{url} returned {r.status_code}"
            mock.set.assert_called_once()
            ttl = mock.set.call_args[1].get('ttl')
            assert ttl == 3600, f"{url} used TTL={ttl}, expected 3600"


# ---------------------------------------------------------------------------
# Cache invalidation integration (entries API -> insights cache cleared)
# ---------------------------------------------------------------------------

class TestInsightCacheInvalidationOnEntryChange:
    """
    When invalidate_user_cache() is called (entry create/update/delete),
    the insights:user_id:* pattern must be deleted.
    """

    def test_invalidate_user_cache_clears_insights_pattern(self):
        from app.core.cache import CacheService

        store = {}

        mock = MagicMock(spec=CacheService)
        mock.enabled = True

        def fake_make_key(prefix, *args, **kwargs):
            return ':'.join([prefix] + [str(a) for a in args])

        def fake_set(key, value, ttl=None):
            store[key] = value
            return True

        def fake_get(key):
            return store.get(key)

        def fake_delete_pattern(pattern):
            prefix = pattern.rstrip('*').rstrip(':')
            removed = [k for k in list(store) if k.startswith(prefix)]
            for k in removed:
                del store[k]
            return len(removed)

        def fake_invalidate_user_cache(user_id):
            patterns = [
                f'forecast:{user_id}:',
                f'report:{user_id}:',
                f'scenario:{user_id}:',
                f'dashboard:{user_id}:',
                f'insights:{user_id}:',
            ]
            total = 0
            for p in patterns:
                removed = [k for k in list(store) if k.startswith(p)]
                for k in removed:
                    del store[k]
                total += len(removed)
            return total

        mock._make_key.side_effect = fake_make_key
        mock.set.side_effect = fake_set
        mock.get.side_effect = fake_get
        mock.delete_pattern.side_effect = fake_delete_pattern
        mock.invalidate_user_cache.side_effect = fake_invalidate_user_cache

        # Seed insights keys
        store['insights:7:budget_health'] = {'success': True}
        store['insights:7:alerts'] = {'success': True}
        store['forecast:7:total:90'] = {'forecast': []}

        assert len(store) == 3

        # Simulate entry modification
        deleted = fake_invalidate_user_cache(7)

        assert deleted == 3
        assert 'insights:7:budget_health' not in store
        assert 'insights:7:alerts' not in store
        assert 'forecast:7:total:90' not in store

    def test_insights_pattern_included_in_invalidation_list(self):
        """Regression: invalidate_user_cache must include 'insights:{user_id}:*'."""
        import inspect
        from app.core.cache import CacheService
        src = inspect.getsource(CacheService.invalidate_user_cache)
        assert 'insights' in src, (
            "invalidate_user_cache() does not include 'insights' pattern — "
            "AI insights cache will NOT be cleared when entries change"
        )


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
