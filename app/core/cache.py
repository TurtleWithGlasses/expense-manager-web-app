"""
Redis-based Caching Service

Provides fast caching for expensive operations like:
- Prophet forecasts
- Reports
- Dashboard data
- Scenario analysis results
"""

import json
import logging
from typing import Optional, Dict, Any, List
from datetime import timedelta
from functools import wraps
import hashlib

logger = logging.getLogger(__name__)

# Try to import Redis, but make it optional
try:
    import redis
    from redis import Redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not installed. Caching disabled. Install with: pip install redis")


class CacheService:
    """
    Redis-based caching service with automatic JSON serialization

    Falls back to no-op if Redis is unavailable.
    """

    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0, password: Optional[str] = None):
        """
        Initialize cache service

        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Optional Redis password
        """
        self.enabled = REDIS_AVAILABLE
        self.redis_client: Optional[Redis] = None

        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.Redis(
                    host=host,
                    port=port,
                    db=db,
                    password=password,
                    decode_responses=True,  # Auto-decode responses to strings
                    socket_connect_timeout=2,
                    socket_timeout=2
                )
                # Test connection
                self.redis_client.ping()
                logger.info(f"✅ Redis cache connected: {host}:{port}")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}. Caching disabled.")
                self.enabled = False
                self.redis_client = None
        else:
            logger.warning("Redis not available. Caching disabled.")

    def _make_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Generate cache key from prefix and arguments

        Args:
            prefix: Key prefix (e.g., 'forecast', 'report')
            *args: Positional arguments to include in key
            **kwargs: Keyword arguments to include in key

        Returns:
            Cache key string
        """
        # Create a stable string representation
        key_parts = [prefix]
        key_parts.extend(str(arg) for arg in args)
        key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))

        key_string = ":".join(key_parts)

        # Hash if too long (Redis key limit is 512MB, but keep reasonable)
        if len(key_string) > 200:
            key_hash = hashlib.md5(key_string.encode()).hexdigest()
            return f"{prefix}:hash:{key_hash}"

        return key_string

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value (deserialized from JSON) or None
        """
        if not self.enabled or not self.redis_client:
            return None

        try:
            value = self.redis_client.get(key)
            if value is None:
                return None

            # Deserialize JSON
            return json.loads(value)

        except json.JSONDecodeError:
            logger.error(f"Failed to deserialize cached value for key: {key}")
            # Delete corrupted cache entry
            self.delete(key)
            return None

        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (None = no expiration)

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.redis_client:
            return False

        try:
            # Serialize to JSON
            serialized = json.dumps(value, default=str)

            if ttl:
                self.redis_client.setex(key, ttl, serialized)
            else:
                self.redis_client.set(key, serialized)

            return True

        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize value for key {key}: {e}")
            return False

        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete key from cache

        Args:
            key: Cache key

        Returns:
            True if deleted, False otherwise
        """
        if not self.enabled or not self.redis_client:
            return False

        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern

        Args:
            pattern: Pattern to match (e.g., 'forecast:*', 'report:123:*')

        Returns:
            Number of keys deleted
        """
        if not self.enabled or not self.redis_client:
            return 0

        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache delete_pattern error for pattern {pattern}: {e}")
            return 0

    def invalidate_user_cache(self, user_id: int) -> int:
        """
        Invalidate all cached data for a specific user

        Args:
            user_id: User ID

        Returns:
            Number of keys deleted
        """
        patterns = [
            f"forecast:{user_id}:*",
            f"report:{user_id}:*",
            f"scenario:{user_id}:*",
            f"dashboard:{user_id}:*",
            f"insights:{user_id}:*"
        ]

        total_deleted = 0
        for pattern in patterns:
            total_deleted += self.delete_pattern(pattern)

        if total_deleted > 0:
            logger.info(f"Invalidated {total_deleted} cache entries for user {user_id}")

        return total_deleted

    def clear_all(self) -> bool:
        """
        Clear ALL cache entries (use with caution!)

        Returns:
            True if successful
        """
        if not self.enabled or not self.redis_client:
            return False

        try:
            self.redis_client.flushdb()
            logger.warning("🗑️  All cache entries cleared!")
            return True
        except Exception as e:
            logger.error(f"Cache clear_all error: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dictionary with cache stats
        """
        if not self.enabled or not self.redis_client:
            return {
                'enabled': False,
                'message': 'Redis not available'
            }

        try:
            info = self.redis_client.info()
            return {
                'enabled': True,
                'total_keys': self.redis_client.dbsize(),
                'memory_used': info.get('used_memory_human', 'unknown'),
                'hits': info.get('keyspace_hits', 0),
                'misses': info.get('keyspace_misses', 0),
                'hit_rate': self._calculate_hit_rate(
                    info.get('keyspace_hits', 0),
                    info.get('keyspace_misses', 0)
                )
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {'enabled': True, 'error': str(e)}

    def _calculate_hit_rate(self, hits: int, misses: int) -> str:
        """Calculate cache hit rate percentage"""
        total = hits + misses
        if total == 0:
            return "0%"
        return f"{(hits / total * 100):.1f}%"


# Helper decorator for caching function results
def cached(prefix: str, ttl: int = 3600):
    """
    Decorator to cache function results

    Usage:
        @cached(prefix='forecast', ttl=86400)  # 24 hours
        def expensive_forecast(user_id: int, days: int):
            # ... expensive operation
            return result

    Args:
        prefix: Cache key prefix
        ttl: Time to live in seconds
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get cache instance
            cache = _get_global_cache()
            if not cache.enabled:
                # Cache not available, execute function directly
                return func(*args, **kwargs)

            # Generate cache key
            cache_key = cache._make_key(prefix, *args, **kwargs)

            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache HIT: {cache_key}")
                return cached_result

            # Cache miss - execute function
            logger.debug(f"Cache MISS: {cache_key}")
            result = func(*args, **kwargs)

            # Store in cache
            cache.set(cache_key, result, ttl=ttl)

            return result

        return wrapper
    return decorator


# Global cache instance
_global_cache: Optional[CacheService] = None


def get_cache() -> CacheService:
    """Get global cache service instance"""
    global _global_cache
    if _global_cache is None:
        _global_cache = CacheService()
    return _global_cache


def _get_global_cache() -> CacheService:
    """Internal: Get global cache for decorator"""
    return get_cache()


# Convenience functions

def cache_forecast(user_id: int, forecast_type: str, days: int, data: Dict, ttl: int = 86400) -> bool:
    """
    Cache a forecast result

    Args:
        user_id: User ID
        forecast_type: Type of forecast ('total', 'category', etc.)
        days: Forecast period
        data: Forecast data
        ttl: Cache duration (default: 24 hours)

    Returns:
        True if cached successfully
    """
    cache = get_cache()
    key = cache._make_key('forecast', user_id, forecast_type, days)
    return cache.set(key, data, ttl=ttl)


def get_cached_forecast(user_id: int, forecast_type: str, days: int) -> Optional[Dict]:
    """Get cached forecast if available"""
    cache = get_cache()
    key = cache._make_key('forecast', user_id, forecast_type, days)
    return cache.get(key)


def invalidate_forecast_cache(user_id: int) -> int:
    """Invalidate all forecast caches for user"""
    cache = get_cache()
    return cache.delete_pattern(f"forecast:{user_id}:*")
