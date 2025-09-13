"""
Caching layer for secrets with TTL support
Supports in-memory and optional Redis caching
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import time
from typing import Any

from pydantic import BaseModel, Field
from .interfaces import SecretCache
from .types import SecretMetadata, SecretValue

logger = logging.getLogger(__name__)

# Try to import Redis for optional Redis cache support
try:
    import redis.asyncio as redis

    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False
    redis = None


class InMemoryCache:
    """
    In-memory TTL cache for secrets
    Thread-safe with automatic cleanup of expired entries
    """

    def __init__(self, default_ttl: int = 300, max_size: int = 1000) -> None:
        self.default_ttl = default_ttl
        self.max_size = max_size
        self._cache: dict[str, dict[str, Any]] = {}
        self._access_times: dict[str, float] = {}
        self._lock = asyncio.Lock()

        # Start background cleanup task
        self._cleanup_task: asyncio.Task | None = None
        self._start_cleanup_task()

    def _start_cleanup_task(self) -> None:
        """Start background cleanup task for expired entries"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_expired())

    async def _cleanup_expired(self) -> None:
        """Background task to clean up expired entries"""
        while True:
            try:
                await asyncio.sleep(60)  # Clean up every minute
                await self._remove_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"Cache cleanup error: {e}")

    async def _remove_expired(self) -> None:
        """Remove expired entries from cache"""
        async with self._lock:
            current_time = time.time()
            expired_keys = []

            for key, entry in self._cache.items():
                if current_time > entry["expires_at"]:
                    expired_keys.append(key)

            for key in expired_keys:
                del self._cache[key]
                self._access_times.pop(key, None)

            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

    async def _evict_lru_if_needed(self) -> None:
        """Evict least recently used entries if cache is full"""
        if len(self._cache) >= self.max_size:
            # Find least recently used key
            lru_key = min(self._access_times.keys(), key=lambda k: self._access_times[k])
            del self._cache[lru_key]
            del self._access_times[lru_key]
            logger.debug(f"Evicted LRU cache entry: {lru_key}")

    async def get(self, key: str) -> SecretValue | None:
        """Get cached secret value"""
        async with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                return None

            # Check if expired
            current_time = time.time()
            if current_time > entry["expires_at"]:
                del self._cache[key]
                self._access_times.pop(key, None)
                return None

            # Update access time
            self._access_times[key] = current_time

            # Deserialize SecretValue
            try:
                metadata = SecretMetadata(**entry["metadata"])
                return SecretValue(value=entry["value"], metadata=metadata)
            except Exception as e:
                logger.warning(f"Failed to deserialize cached secret {key}: {e}")
                del self._cache[key]
                self._access_times.pop(key, None)
                return None

    async def set(self, key: str, value: SecretValue, ttl: int) -> bool:
        """Set cached secret value with TTL"""
        async with self._lock:
            try:
                # Evict if needed
                await self._evict_lru_if_needed()

                current_time = time.time()
                expires_at = current_time + ttl

                # Serialize SecretValue
                entry = {
                    "value": value.value,
                    "metadata": value.metadata.model_dump(),
                    "cached_at": current_time,
                    "expires_at": expires_at,
                }

                self._cache[key] = entry
                self._access_times[key] = current_time

                return True

            except Exception as e:
                logger.error(f"Failed to cache secret {key}: {e}")
                return False

    async def delete(self, key: str) -> bool:
        """Delete cached secret"""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._access_times.pop(key, None)
                return True
            return False

    async def clear(self) -> bool:
        """Clear all cached secrets"""
        async with self._lock:
            self._cache.clear()
            self._access_times.clear()
            return True

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache (and is not expired)"""
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return False

            current_time = time.time()
            if current_time > entry["expires_at"]:
                del self._cache[key]
                self._access_times.pop(key, None)
                return False

            return True

    async def get_stats(self) -> dict[str, Any]:
        """Get cache statistics"""
        async with self._lock:
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "default_ttl": self.default_ttl,
            }

    async def close(self) -> None:
        """Close cache and cleanup resources"""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._cleanup_task

        await self.clear()


class RedisCache:
    """
    Redis-based cache for secrets with TTL support
    Suitable for distributed deployments
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        key_prefix: str = "secrets:",
        default_ttl: int = 300,
        **redis_kwargs: Any,
    ) -> None:
        if not HAS_REDIS:
            raise ImportError("Redis not available. Install with: pip install redis")

        self.redis_url = redis_url
        self.key_prefix = key_prefix
        self.default_ttl = default_ttl
        self.redis_kwargs = redis_kwargs

        self._redis: redis.Redis | None = None

    async def _get_redis(self) -> redis.Redis:
        """Get or create Redis connection"""
        if self._redis is None:
            self._redis = redis.from_url(self.redis_url, decode_responses=True, **self.redis_kwargs)
        return self._redis

    def _make_key(self, key: str) -> str:
        """Create prefixed Redis key"""
        return f"{self.key_prefix}{key}"

    async def get(self, key: str) -> SecretValue | None:
        """Get cached secret value from Redis"""
        try:
            redis_client = await self._get_redis()
            redis_key = self._make_key(key)

            data = await redis_client.get(redis_key)
            if data is None:
                return None

            # Deserialize JSON data
            entry = json.loads(data)
            metadata = SecretMetadata(**entry["metadata"])

            return SecretValue(value=entry["value"], metadata=metadata)

        except Exception as e:
            logger.warning(f"Failed to get cached secret from Redis {key}: {e}")
            return None

    async def set(self, key: str, value: SecretValue, ttl: int) -> bool:
        """Set cached secret value in Redis with TTL"""
        try:
            redis_client = await self._get_redis()
            redis_key = self._make_key(key)

            # Serialize SecretValue
            entry = {
                "value": value.value,
                "metadata": value.metadata.model_dump(),
                "cached_at": time.time(),
            }

            data = json.dumps(entry)

            # Set with TTL
            await redis_client.setex(redis_key, ttl, data)
            return True

        except Exception as e:
            logger.error(f"Failed to cache secret in Redis {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete cached secret from Redis"""
        try:
            redis_client = await self._get_redis()
            redis_key = self._make_key(key)

            result = await redis_client.delete(redis_key)
            return result > 0

        except Exception as e:
            logger.warning(f"Failed to delete cached secret from Redis {key}: {e}")
            return False

    async def clear(self) -> bool:
        """Clear all cached secrets from Redis"""
        try:
            redis_client = await self._get_redis()
            pattern = f"{self.key_prefix}*"

            # Get all keys matching pattern
            keys = await redis_client.keys(pattern)

            if keys:
                await redis_client.delete(*keys)

            return True

        except Exception as e:
            logger.error(f"Failed to clear Redis cache: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis cache"""
        try:
            redis_client = await self._get_redis()
            redis_key = self._make_key(key)

            result = await redis_client.exists(redis_key)
            return result > 0

        except Exception as e:
            logger.warning(f"Failed to check key existence in Redis {key}: {e}")
            return False

    async def get_stats(self) -> dict[str, Any]:
        """Get Redis cache statistics"""
        try:
            redis_client = await self._get_redis()
            info = await redis_client.info("memory")

            # Count keys with our prefix
            pattern = f"{self.key_prefix}*"
            key_count = len(await redis_client.keys(pattern))

            return {
                "key_count": key_count,
                "memory_used": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "redis_version": info.get("redis_version", "unknown"),
            }

        except Exception as e:
            logger.warning(f"Failed to get Redis stats: {e}")
            return {}

    async def close(self) -> None:
        """Close Redis connection"""
        if self._redis:
            await self._redis.close()
            self._redis = None


class NullCache:
    """
    Null cache implementation that doesn't cache anything
    Useful for disabling caching in certain environments
    """

    async def get(self, key: str) -> SecretValue | None:
        """Always return None (no cache)"""
        return None

    async def set(self, key: str, value: SecretValue, ttl: int) -> bool:
        """Always return True (no-op)"""
        return True

    async def delete(self, key: str) -> bool:
        """Always return True (no-op)"""
        return True

    async def clear(self) -> bool:
        """Always return True (no-op)"""
        return True

    async def exists(self, key: str) -> bool:
        """Always return False (no cache)"""
        return False

    async def get_stats(self) -> dict[str, Any]:
        """Return empty stats"""
        return {"type": "null", "caching_disabled": True}

    async def close(self) -> None:
        """No-op close"""


def create_cache(
    cache_type: str = "memory", **config: Any
) -> InMemoryCache | RedisCache | NullCache:
    """
    Factory function to create cache instances

    Args:
        cache_type: Type of cache ("memory", "redis", "null")
        **config: Configuration parameters for the cache

    Returns:
        Cache instance

    Raises:
        ValueError: If cache type is not supported
    """
    if cache_type == "memory":
        return InMemoryCache(**config)
    if cache_type == "redis":
        return RedisCache(**config)
    if cache_type == "null":
        return NullCache()
    raise ValueError(f"Unsupported cache type: {cache_type}")


# Register cache classes with SecretCache protocol
SecretCache.register(InMemoryCache)
SecretCache.register(RedisCache)
SecretCache.register(NullCache)


class CacheConfig(BaseModel):
    """Simple cache configuration used in tests."""

    ttl_seconds: int = Field(default=300, gt=0)
    max_size: int = Field(default=1000, gt=0)
    eviction_policy: str = Field(default="lru")
