"""Cache backend implementations."""

from __future__ import annotations

import asyncio
import contextlib
import json

import time
from typing import Any

from .config import CacheConfig
from .exceptions import CacheConnectionError, CacheError
from .interfaces import CacheBackend
from dotmac.platform.observability.unified_logging import get_logger

logger = get_logger(__name__)

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

    def __init__(self, config: CacheConfig | None = None) -> None:
        # Allow default construction for tests
        self.config = config or CacheConfig()
        self.cache: dict[str, CacheEntry] = {}
        self._access_times: dict[str, float] = {}
        self._lock = asyncio.Lock()
        self._connected = False
        self._cleanup_task: asyncio.Task | None = None
        # Simple counters for stats
        self._hits = 0
        self._misses = 0
        self._sets = 0

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
                self._misses += 1
                return None

            # Check if expired
            if entry.is_expired():
                del self.cache[key]
                self._access_times.pop(key, None)
                self._misses += 1
                return None

            # Update access time
            current_time = time.time()
            entry.last_accessed = current_time
            self._access_times[key] = current_time

            self._hits += 1
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

                self._sets += 1
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

    async def get_many(self, keys: list[str]) -> dict[str, Any | None]:
        """Get multiple keys at once."""
        results: dict[str, Any | None] = {}
        for k in keys:
            results[k] = await self.get(k)
        return results

    async def set_many(self, items: dict[str, Any], ttl: int | None = None) -> bool:
        """Set multiple keys at once."""
        for k, v in items.items():
            if not await self.set(k, v, ttl):
                return False
        return True

    async def close(self) -> None:
        await self.disconnect()

    class _StatsResult(dict):
        def __init__(self, data: dict[str, Any]):
            super().__init__(data)

        def __await__(self):
            async def _coro():
                return dict(self)

            return _coro().__await__()

    def get_stats(self):  # supports both direct use and awaiting
        """Get cache statistics; works with or without await."""
        data = {
            "backend": "memory",
            "connected": self._connected,
            "size": len(self.cache),
            "max_size": self.config.max_size,
            "default_ttl": self.config.default_ttl,
            "hits": self._hits,
            "misses": self._misses,
            "sets": self._sets,
        }
        return InMemoryCache._StatsResult(data)

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
            # Graceful behavior when not connected
            return None

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
            return False

        try:
            redis_key = self._make_key(key)
            data = self._serialize(value)
            ttl = ttl or self.config.default_ttl

            # Use standard set with expiry to match expectations
            await self._redis.set(redis_key, data, ex=ttl)
            return True

        except Exception as e:
            logger.error(f"Failed to cache value for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self._connected or not self._redis:
            return False

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
            return False

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
            return False

        try:
            # Tests expect flushdb for clear
            await self._redis.flushdb()
            return True

        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False

    def get_stats(self) -> dict[str, Any]:
        """Minimal synchronous stats."""
        return {"backend": "redis", "connected": self._connected}

    async def get_many(self, keys: list[str]) -> dict[str, Any | None]:
        if not self._connected or not self._redis:
            return {k: None for k in keys}
        try:
            values = await self._redis.mget(keys)
            out: dict[str, Any | None] = {}
            for k, v in zip(keys, values):
                out[k] = self._deserialize(v) if v is not None else None
            return out
        except Exception as e:
            logger.warning(f"Failed mget: {e}")
            return {k: None for k in keys}

    async def set_many(self, items: dict[str, Any], ttl: int | None = None) -> bool:
        if not self._connected or not self._redis:
            return False
        try:
            pipe = self._redis.pipeline()
            ttl_val = ttl or self.config.default_ttl
            for k, v in items.items():
                pipe.set(self._make_key(k), self._serialize(v), ex=ttl_val)
            await pipe.execute()
            return True
        except Exception as e:
            logger.error(f"Failed to set_many: {e}")
            return False

    async def close(self) -> None:
        if self._redis:
            await self._redis.close()
        self._connected = False

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
        """Indicate nothing deleted."""
        return False

    async def exists(self, key: str) -> bool:
        """Always return False (no cache)."""
        return False

    async def clear(self) -> bool:
        """Always return True (no-op)."""
        return True

    def get_stats(self) -> dict[str, Any]:
        return {
            "backend": "null",
            "connected": self._connected,
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "size": 0,
        }

    async def close(self) -> None:
        await self.disconnect()
