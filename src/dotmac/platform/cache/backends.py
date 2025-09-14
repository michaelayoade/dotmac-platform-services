"""Cache backend implementations."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import time
from typing import Any

from .config import CacheConfig
from .exceptions import CacheConnectionError, CacheError
from .interfaces import CacheBackend

logger = logging.getLogger(__name__)

# Try to import Redis for optional Redis cache support
try:
    import redis.asyncio as redis

    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False
    redis = None


class CacheEntry:
    """Internal cache entry with metadata."""

    def __init__(self, value: Any, created_at: float, ttl: int | None = None):
        self.value = value
        self.created_at = created_at
        self.ttl = ttl
        self.last_accessed: float | None = None

    def is_expired(self) -> bool:
        """Check if entry is expired."""
        if self.ttl is None:
            return False
        return time.time() > self.created_at + self.ttl


class InMemoryCache(CacheBackend):
    """
    In-memory cache backend with TTL support.
    Thread-safe with automatic cleanup of expired entries.
    """

    def __init__(self, config: CacheConfig) -> None:
        self.config = config
        self.cache: dict[str, CacheEntry] = {}
        self._access_times: dict[str, float] = {}
        self._lock = asyncio.Lock()
        self._connected = False
        self._cleanup_task: asyncio.Task | None = None

    async def connect(self) -> bool:
        """Connect to the cache backend."""
        if self._connected:
            return True

        self._connected = True
        # Start background cleanup task
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_expired())
        return True

    async def disconnect(self) -> bool:
        """Disconnect from the cache backend."""
        if not self._connected:
            return True

        # Stop cleanup task
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._cleanup_task

        self._connected = False
        return True

    def is_connected(self) -> bool:
        """Check if backend is connected."""
        return self._connected

    async def _cleanup_expired(self) -> None:
        """Background task to clean up expired entries."""
        while self._connected:
            try:
                await asyncio.sleep(60)  # Clean up every minute
                await self._remove_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"Cache cleanup error: {e}")

    async def _remove_expired(self) -> None:
        """Remove expired entries from cache."""
        async with self._lock:
            expired_keys = []
            for key, entry in self.cache.items():
                if entry.is_expired():
                    expired_keys.append(key)

            for key in expired_keys:
                del self.cache[key]
                self._access_times.pop(key, None)

            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

    async def _evict_lru_if_needed(self) -> None:
        """Evict least recently used entries if cache is full."""
        while len(self.cache) >= self.config.max_size:
            # Find least recently used key
            lru_key = min(self._access_times.keys(), key=lambda k: self._access_times[k])
            del self.cache[lru_key]
            del self._access_times[lru_key]
            logger.debug(f"Evicted LRU cache entry: {lru_key}")

    async def get(self, key: str) -> Any | None:
        """Get value from cache."""
        if not self._connected:
            raise CacheConnectionError("Cache not connected")

        async with self._lock:
            entry = self.cache.get(key)

            if entry is None:
                return None

            # Check if expired
            if entry.is_expired():
                del self.cache[key]
                self._access_times.pop(key, None)
                return None

            # Update access time
            current_time = time.time()
            entry.last_accessed = current_time
            self._access_times[key] = current_time

            return entry.value

    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Set value in cache with optional TTL."""
        if not self._connected:
            raise CacheConnectionError("Cache not connected")

        async with self._lock:
            try:
                # Evict if needed
                await self._evict_lru_if_needed()

                current_time = time.time()
                ttl = ttl or self.config.default_ttl

                # Create entry
                entry = CacheEntry(value, current_time, ttl)
                self.cache[key] = entry
                self._access_times[key] = current_time

                return True

            except Exception as e:
                logger.error(f"Failed to cache value for key {key}: {e}")
                return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self._connected:
            raise CacheConnectionError("Cache not connected")

        async with self._lock:
            if key in self.cache:
                del self.cache[key]
                self._access_times.pop(key, None)
                return True
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self._connected:
            raise CacheConnectionError("Cache not connected")

        async with self._lock:
            entry = self.cache.get(key)
            if entry is None:
                return False

            if entry.is_expired():
                del self.cache[key]
                self._access_times.pop(key, None)
                return False

            return True

    async def clear(self) -> bool:
        """Clear all keys from cache."""
        if not self._connected:
            raise CacheConnectionError("Cache not connected")

        async with self._lock:
            self.cache.clear()
            self._access_times.clear()
            return True

    async def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        async with self._lock:
            return {
                "backend": "memory",
                "connected": self._connected,
                "size": len(self.cache),
                "max_size": self.config.max_size,
                "default_ttl": self.config.default_ttl,
            }


class RedisCache(CacheBackend):
    """
    Redis-based cache backend with TTL support.
    Suitable for distributed deployments.
    """

    def __init__(self, config: CacheConfig) -> None:
        if not HAS_REDIS:
            raise ImportError("Redis not available. Install with: pip install redis")

        self.config = config
        self._redis: redis.Redis | None = None
        self._connected = False

    async def connect(self) -> bool:
        """Connect to the cache backend."""
        if self._connected:
            return True

        try:
            self._redis = redis.from_url(
                self.config.redis_connection_url,
                decode_responses=False,  # We'll handle encoding/decoding
                max_connections=self.config.max_connections,
                socket_connect_timeout=self.config.connection_timeout,
            )

            # Test connection
            await self._redis.ping()
            self._connected = True
            logger.info("Connected to Redis cache")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise CacheConnectionError(f"Redis connection failed: {e}")

    async def disconnect(self) -> bool:
        """Disconnect from the cache backend."""
        if not self._connected:
            return True

        if self._redis:
            await self._redis.close()
            self._redis = None

        self._connected = False
        logger.info("Disconnected from Redis cache")
        return True

    def is_connected(self) -> bool:
        """Check if backend is connected."""
        return self._connected

    def _make_key(self, key: str) -> str:
        """Create prefixed Redis key."""
        return f"{self.config.key_prefix}{key}"

    def _serialize(self, value: Any) -> bytes:
        """Serialize value for storage using JSON."""
        return json.dumps(value).encode("utf-8")

    def _deserialize(self, data: bytes) -> Any:
        """Deserialize value from storage using JSON."""
        return json.loads(data.decode("utf-8"))

    async def get(self, key: str) -> Any | None:
        """Get value from cache."""
        if not self._connected or not self._redis:
            raise CacheConnectionError("Cache not connected")

        try:
            redis_key = self._make_key(key)
            data = await self._redis.get(redis_key)

            if data is None:
                return None

            return self._deserialize(data)

        except Exception as e:
            logger.warning(f"Failed to get cached value for key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Set value in cache with optional TTL."""
        if not self._connected or not self._redis:
            raise CacheConnectionError("Cache not connected")

        try:
            redis_key = self._make_key(key)
            data = self._serialize(value)
            ttl = ttl or self.config.default_ttl

            await self._redis.setex(redis_key, ttl, data)
            return True

        except Exception as e:
            logger.error(f"Failed to cache value for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self._connected or not self._redis:
            raise CacheConnectionError("Cache not connected")

        try:
            redis_key = self._make_key(key)
            result = await self._redis.delete(redis_key)
            return result > 0

        except Exception as e:
            logger.warning(f"Failed to delete cached key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self._connected or not self._redis:
            raise CacheConnectionError("Cache not connected")

        try:
            redis_key = self._make_key(key)
            result = await self._redis.exists(redis_key)
            return result > 0

        except Exception as e:
            logger.warning(f"Failed to check key existence for {key}: {e}")
            return False

    async def clear(self) -> bool:
        """Clear all keys from cache."""
        if not self._connected or not self._redis:
            raise CacheConnectionError("Cache not connected")

        try:
            pattern = f"{self.config.key_prefix}*"
            keys = []

            # Use SCAN to get keys in batches
            async for key in self._redis.scan_iter(pattern):
                keys.append(key)

            if keys:
                await self._redis.delete(*keys)

            logger.info(f"Cleared {len(keys)} cache entries")
            return True

        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False

    async def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        if not self._connected or not self._redis:
            return {
                "backend": "redis",
                "connected": False,
            }

        try:
            info = await self._redis.info("memory")
            pattern = f"{self.config.key_prefix}*"

            # Count keys with our prefix
            key_count = 0
            async for _ in self._redis.scan_iter(pattern):
                key_count += 1

            return {
                "backend": "redis",
                "connected": True,
                "key_count": key_count,
                "memory_used": info.get("used_memory_human", "unknown"),
                "redis_version": info.get("redis_version", "unknown"),
            }

        except Exception as e:
            logger.warning(f"Failed to get Redis stats: {e}")
            return {
                "backend": "redis",
                "connected": self._connected,
                "error": str(e),
            }


class NullCache(CacheBackend):
    """
    Null cache backend that doesn't cache anything.
    Useful for disabling caching in certain environments.
    """

    def __init__(self, config: CacheConfig) -> None:
        self.config = config
        self._connected = False

    async def connect(self) -> bool:
        """Connect to the cache backend."""
        self._connected = True
        return True

    async def disconnect(self) -> bool:
        """Disconnect from the cache backend."""
        self._connected = False
        return True

    def is_connected(self) -> bool:
        """Check if backend is connected."""
        return self._connected

    async def get(self, key: str) -> Any | None:
        """Always return None (no cache)."""
        return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Always return True (no-op)."""
        return True

    async def delete(self, key: str) -> bool:
        """Always return True (no-op)."""
        return True

    async def exists(self, key: str) -> bool:
        """Always return False (no cache)."""
        return False

    async def clear(self) -> bool:
        """Always return True (no-op)."""
        return True

    async def get_stats(self) -> dict[str, Any]:
        """Return empty stats."""
        return {
            "backend": "null",
            "connected": self._connected,
            "caching_disabled": True,
        }