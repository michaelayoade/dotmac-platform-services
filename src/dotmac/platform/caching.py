"""
Simple caching setup using redis-py and cachetools directly.

"""

import pickle
from functools import wraps
from typing import Any, Optional

import redis
from cachetools import LRUCache, TTLCache, cached

from dotmac.platform.settings import settings

# Redis client for distributed caching
redis_client: Optional[redis.Redis] = None

if settings.redis.host:
    redis_client = redis.Redis.from_url(
        settings.redis.cache_url,
        decode_responses=False,  # We'll handle encoding/decoding
        max_connections=settings.redis.max_connections,
    )

# In-memory caches for local caching
# These are thread-safe by default in cachetools
memory_cache = TTLCache(maxsize=1000, ttl=300)  # 5 min TTL
lru_cache = LRUCache(maxsize=500)


def get_redis() -> Optional[redis.Redis]:
    """Get Redis client if available."""
    return redis_client


def cache_get(key: str, default: Any = None) -> Any:
    """
    Get value from cache (Redis if available, memory otherwise).

    Args:
        key: Cache key
        default: Default value if not found

    Returns:
        Cached value or default
    """
    if redis_client:
        try:
            value = redis_client.get(key)
            if value and isinstance(value, (bytes, bytearray, memoryview)):
                return pickle.loads(value)
        except Exception:
            pass  # Fall back to memory cache

    return memory_cache.get(key, default)


def cache_set(key: str, value: Any, ttl: int = 300) -> bool:
    """
    Set value in cache (Redis if available, memory otherwise).

    Args:
        key: Cache key
        value: Value to cache
        ttl: Time to live in seconds

    Returns:
        True if successful
    """
    if redis_client:
        try:
            redis_client.setex(key, ttl, pickle.dumps(value))
            return True
        except Exception:
            pass  # Fall back to memory cache

    memory_cache[key] = value
    return True


def cache_delete(key: str) -> bool:
    """
    Delete value from cache.

    Args:
        key: Cache key

    Returns:
        True if key existed and was deleted
    """
    deleted = False

    if redis_client:
        try:
            deleted = bool(redis_client.delete(key))
        except Exception:
            pass

    if key in memory_cache:
        del memory_cache[key]
        deleted = True

    return deleted


def cache_clear() -> None:
    """Clear all caches."""
    if redis_client:
        try:
            redis_client.flushdb()
        except Exception:
            pass

    memory_cache.clear()
    lru_cache.clear()


def redis_cache(ttl: int = 300):
    """
    Decorator for caching function results in Redis.

    Args:
        ttl: Time to live in seconds

    Example:
        @redis_cache(ttl=600)
        def expensive_function(arg):
            return compute_something(arg)
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create stable cache key from function name and arguments
            import hashlib

            key_data = f"{func.__module__}.{func.__name__}:{args}:{sorted(kwargs.items())}"
            key = f"cache:{hashlib.md5(key_data.encode()).hexdigest()}"

            # Try to get from cache
            result = cache_get(key)
            if result is not None:
                return result

            # Compute and cache
            result = func(*args, **kwargs)
            cache_set(key, result, ttl)
            return result

        return wrapper

    return decorator


# Direct exports of cachetools decorators for in-memory caching
# Users can use these directly without any wrapper
__all__ = [
    # Redis functions
    "redis_client",
    "get_redis",
    "cache_get",
    "cache_set",
    "cache_delete",
    "cache_clear",
    "redis_cache",
    # In-memory caches
    "memory_cache",
    "lru_cache",
    # Direct cachetools exports
    "cached",
    "TTLCache",
    "LRUCache",
]

# Example usage:
#
# # Redis caching
# @redis_cache(ttl=600)
# def get_user(user_id):
#     return db.query(User).get(user_id)
#
# # In-memory caching with cachetools
# @cached(cache=TTLCache(maxsize=100, ttl=300))
# def calculate_something(x, y):
#     return expensive_calculation(x, y)
