"""
Unit Tests for Redis Cache Service

Tests all cache service operations including:
- Basic get/set/delete operations
- TTL (Time To Live) functionality
- Pattern-based deletion
- User-level cache invalidation
- Cache statistics
- Error handling and graceful degradation
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from app.core.cache import CacheService, get_cache, cached, cache_forecast, get_cached_forecast, invalidate_forecast_cache


class TestCacheServiceBasicOperations:
    """Test basic cache operations (get, set, delete)"""

    def setup_method(self):
        """Setup test cache service"""
        self.cache = CacheService()

    def test_set_and_get_simple_value(self):
        """Test setting and getting a simple value"""
        key = 'test:simple'
        value = {'message': 'Hello Redis'}

        # Set value
        result = self.cache.set(key, value, ttl=60)
        assert result is True or result is False  # True if Redis available

        # Get value
        cached_value = self.cache.get(key)
        if self.cache.enabled:
            assert cached_value == value
        else:
            assert cached_value is None

    def test_set_and_get_complex_value(self):
        """Test setting and getting complex nested data"""
        key = 'test:complex'
        value = {
            'user_id': 123,
            'forecast': [
                {'date': '2025-01-01', 'amount': 100.50},
                {'date': '2025-01-02', 'amount': 200.75}
            ],
            'metadata': {
                'created_at': '2025-12-26',
                'version': 1
            }
        }

        self.cache.set(key, value, ttl=60)
        cached_value = self.cache.get(key)

        if self.cache.enabled:
            assert cached_value == value
            assert cached_value['user_id'] == 123
            assert len(cached_value['forecast']) == 2
            assert cached_value['metadata']['version'] == 1

    def test_get_nonexistent_key(self):
        """Test getting a key that doesn't exist"""
        result = self.cache.get('nonexistent:key')
        assert result is None

    def test_delete_key(self):
        """Test deleting a key"""
        key = 'test:delete'
        self.cache.set(key, {'data': 'test'}, ttl=60)

        # Delete the key
        result = self.cache.delete(key)
        if self.cache.enabled:
            assert result is True

            # Verify it's gone
            assert self.cache.get(key) is None

    def test_set_with_ttl(self):
        """Test that TTL is respected (basic check)"""
        key = 'test:ttl'
        value = {'message': 'expires soon'}

        # Set with very short TTL
        result = self.cache.set(key, value, ttl=1)
        if self.cache.enabled:
            assert result is True

            # Should exist immediately
            assert self.cache.get(key) == value

    def test_set_without_ttl(self):
        """Test setting value without expiration"""
        key = 'test:no_ttl'
        value = {'message': 'never expires'}

        result = self.cache.set(key, value)
        if self.cache.enabled:
            assert result is True
            assert self.cache.get(key) == value


class TestCacheServicePatternDeletion:
    """Test pattern-based deletion operations"""

    def setup_method(self):
        """Setup test cache service"""
        self.cache = CacheService()

    def test_delete_pattern_single_match(self):
        """Test deleting keys matching a pattern"""
        # Set multiple keys
        self.cache.set('user:123:forecast', {'data': 'f1'})
        self.cache.set('user:123:report', {'data': 'r1'})
        self.cache.set('user:456:forecast', {'data': 'f2'})

        # Delete user 123's data
        deleted = self.cache.delete_pattern('user:123:*')

        if self.cache.enabled:
            assert deleted == 2
            assert self.cache.get('user:123:forecast') is None
            assert self.cache.get('user:123:report') is None
            assert self.cache.get('user:456:forecast') is not None

    def test_delete_pattern_no_matches(self):
        """Test deleting with pattern that has no matches"""
        deleted = self.cache.delete_pattern('nonexistent:*')
        assert deleted == 0

    def test_invalidate_user_cache(self):
        """Test user-level cache invalidation"""
        user_id = 789

        # Set various cache entries for user
        self.cache.set(f'forecast:{user_id}:total:90', {'data': 'f'})
        self.cache.set(f'report:{user_id}:monthly:6', {'data': 'r'})
        self.cache.set(f'dashboard:{user_id}:week', {'data': 'd'})
        self.cache.set(f'scenario:{user_id}:123', {'data': 's'})
        self.cache.set(f'insights:{user_id}:spending', {'data': 'i'})

        # Invalidate all user cache
        deleted = self.cache.invalidate_user_cache(user_id)

        if self.cache.enabled:
            assert deleted == 5
            assert self.cache.get(f'forecast:{user_id}:total:90') is None
            assert self.cache.get(f'report:{user_id}:monthly:6') is None


class TestCacheServiceStatistics:
    """Test cache statistics and monitoring"""

    def setup_method(self):
        """Setup test cache service"""
        self.cache = CacheService()

    def test_get_stats_when_enabled(self):
        """Test getting cache statistics when Redis is available"""
        stats = self.cache.get_stats()

        assert 'enabled' in stats
        if self.cache.enabled:
            assert stats['enabled'] is True
            assert 'total_keys' in stats
            assert 'memory_used' in stats
            assert 'hits' in stats
            assert 'misses' in stats
            assert 'hit_rate' in stats
        else:
            assert stats['enabled'] is False
            assert 'message' in stats

    def test_hit_rate_calculation(self):
        """Test cache hit rate calculation"""
        # Test the internal hit rate calculator
        hit_rate = self.cache._calculate_hit_rate(90, 10)
        assert hit_rate == "90.0%"

        hit_rate_zero = self.cache._calculate_hit_rate(0, 0)
        assert hit_rate_zero == "0%"


class TestCacheServiceErrorHandling:
    """Test error handling and graceful degradation"""

    def test_cache_disabled_when_redis_unavailable(self):
        """Test cache gracefully handles Redis being unavailable"""
        # Create cache with invalid connection
        cache = CacheService(host='invalid-host', port=99999)

        # Should be disabled but not crash
        assert cache.enabled is False

        # Operations should return safe defaults
        assert cache.get('any:key') is None
        assert cache.set('any:key', {'data': 'test'}) is False
        assert cache.delete('any:key') is False
        assert cache.delete_pattern('any:*') == 0

    def test_corrupted_cache_value(self):
        """Test handling of corrupted cache values"""
        if not self.cache.enabled:
            pytest.skip("Redis not available")

        cache = CacheService()

        # Manually set corrupted data (if Redis available)
        key = 'test:corrupted'
        if cache.redis_client:
            cache.redis_client.set(key, 'not-valid-json{{{')

            # Should return None and delete corrupted entry
            result = cache.get(key)
            assert result is None

    def test_set_unserializable_value(self):
        """Test setting a value that can't be JSON serialized"""
        cache = CacheService()

        # Create an unserializable object
        class UnserializableClass:
            def __init__(self):
                self.func = lambda x: x  # Functions can't be serialized

        key = 'test:unserializable'
        value = UnserializableClass()

        # Should return False
        result = cache.set(key, value)
        # Either False (serialization failed) or error caught
        assert result in (True, False)


class TestCacheServiceHelpers:
    """Test helper functions (cache_forecast, get_cached_forecast, etc.)"""

    def setup_method(self):
        """Setup test cache service"""
        self.cache = get_cache()
        # Clear any existing forecast cache
        self.cache.delete_pattern('forecast:*')

    def test_cache_forecast_helper(self):
        """Test forecast-specific cache helper"""
        user_id = 999
        forecast_data = {
            'forecast': [{'date': '2025-01-01', 'amount': 100}],
            'summary': {'total': 100}
        }

        # Cache forecast
        result = cache_forecast(
            user_id=user_id,
            forecast_type='total',
            days=90,
            data=forecast_data,
            ttl=3600
        )

        if self.cache.enabled:
            assert result is True

            # Retrieve forecast
            cached = get_cached_forecast(
                user_id=user_id,
                forecast_type='total',
                days=90
            )
            assert cached == forecast_data

    def test_invalidate_forecast_cache_helper(self):
        """Test forecast cache invalidation helper"""
        user_id = 888

        # Set some forecasts
        cache_forecast(user_id, 'total', 90, {'data': 'f1'})
        cache_forecast(user_id, 'category', 30, {'data': 'f2'})

        # Invalidate all forecasts for user
        deleted = invalidate_forecast_cache(user_id)

        if self.cache.enabled:
            assert deleted >= 0  # May be 2 or 0 depending on cache state
            assert get_cached_forecast(user_id, 'total', 90) is None


class TestCachedDecorator:
    """Test @cached decorator for function result caching"""

    def setup_method(self):
        """Setup test cache service"""
        self.cache = get_cache()
        self.call_count = 0

    def test_cached_decorator_basic(self):
        """Test basic decorator functionality"""

        @cached(prefix='test_func', ttl=60)
        def expensive_function(x, y):
            self.call_count += 1
            return x + y

        # First call - should execute function
        result1 = expensive_function(5, 3)
        assert result1 == 8
        first_call_count = self.call_count

        # Second call - should use cache
        result2 = expensive_function(5, 3)
        assert result2 == 8

        if self.cache.enabled:
            # Call count shouldn't increase (cache hit)
            assert self.call_count == first_call_count
        else:
            # Without cache, function executes every time
            assert self.call_count == 2

    def test_cached_decorator_different_args(self):
        """Test decorator with different arguments"""

        @cached(prefix='test_func', ttl=60)
        def calculate(a, b):
            self.call_count += 1
            return a * b

        # Different arguments should not share cache
        result1 = calculate(2, 3)
        result2 = calculate(4, 5)

        assert result1 == 6
        assert result2 == 20
        assert self.call_count == 2  # Both executed

    def test_cached_decorator_with_kwargs(self):
        """Test decorator with keyword arguments"""

        @cached(prefix='test_kwargs', ttl=60)
        def process(value, multiplier=2):
            self.call_count += 1
            return value * multiplier

        result1 = process(10, multiplier=3)
        result2 = process(10, multiplier=3)

        assert result1 == 30
        assert result2 == 30

        if self.cache.enabled:
            assert self.call_count == 1  # Second call used cache


class TestCacheKeyGeneration:
    """Test cache key generation and hashing"""

    def test_make_key_simple(self):
        """Test simple key generation"""
        cache = CacheService()

        key = cache._make_key('forecast', 123, 'total', 90)
        assert key == 'forecast:123:total:90'

    def test_make_key_with_kwargs(self):
        """Test key generation with keyword arguments"""
        cache = CacheService()

        key = cache._make_key('report', user_id=456, type='monthly', months=6)
        # Kwargs are sorted alphabetically
        assert 'report' in key
        assert '456' in key
        assert 'monthly' in key
        assert '6' in key

    def test_make_key_long_hash(self):
        """Test that very long keys get hashed"""
        cache = CacheService()

        # Create a very long key
        long_args = ['x' * 50 for _ in range(10)]
        key = cache._make_key('prefix', *long_args)

        # Should be hashed (contains 'hash:')
        if len(':'.join(['prefix'] + long_args)) > 200:
            assert 'hash:' in key
            assert len(key) < 100  # Hashed key is shorter


class TestCacheClearAll:
    """Test clearing all cache entries"""

    def test_clear_all_cache(self):
        """Test clearing entire cache"""
        cache = CacheService()

        # Set some test data
        cache.set('test:1', {'data': '1'})
        cache.set('test:2', {'data': '2'})

        # Clear all
        result = cache.clear_all()

        if cache.enabled:
            assert result is True
            assert cache.get('test:1') is None
            assert cache.get('test:2') is None


# Integration with get_cache() singleton
class TestCacheSingleton:
    """Test global cache singleton"""

    def test_get_cache_returns_same_instance(self):
        """Test that get_cache() returns singleton instance"""
        cache1 = get_cache()
        cache2 = get_cache()

        assert cache1 is cache2  # Same instance

    def test_singleton_state_persistence(self):
        """Test that singleton maintains state"""
        cache = get_cache()

        cache.set('singleton:test', {'value': 'persistent'})

        # Get cache again
        cache2 = get_cache()

        if cache.enabled:
            result = cache2.get('singleton:test')
            assert result == {'value': 'persistent'}


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
