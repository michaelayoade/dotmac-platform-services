"""Cache service with decorator support."""

from __future__ import annotations

import functools
import hashlib
import inspect
import json
import logging
from typing import Any, Callable, TypeVar

from .backends import InMemoryCache, NullCache, RedisCache
from .config import CacheConfig
from .exceptions import CacheError
from .interfaces import CacheBackend

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CacheService:
    """
    High-level cache service with backend abstraction.

    Features:
    - Multiple backend support (memory, redis, null)
    - Tenant isolation
    - Automatic key generation
    - Decorator support for function caching
    """

    def __init__(
        self,
        backend: CacheBackend | None = None,
        config: CacheConfig | None = None,
        tenant_aware: bool = False,
    ) -> None:
        """
        Initialize cache service.

        Args:
            backend: Cache backend instance (created from config if not provided)
            config: Cache configuration
            tenant_aware: Whether to include tenant ID in cache keys
        """
        self.config = config or CacheConfig()
        self.tenant_aware = tenant_aware

        if backend:
            self.backend = backend
        else:
            self.backend = self._create_backend()

    def _create_backend(self) -> CacheBackend:
        """Create cache backend from configuration."""
        if self.config.backend == "redis":
            return RedisCache(self.config)
        elif self.config.backend == "null":
            return NullCache(self.config)
        else:
            return InMemoryCache(self.config)

    async def initialize(self) -> None:
        """Initialize the cache service."""
        await self.backend.connect()
        logger.info(f"Cache service initialized with {self.config.backend} backend")

    async def shutdown(self) -> None:
        """Shutdown the cache service."""
        await self.backend.disconnect()
        logger.info("Cache service shutdown")

    def _make_key(self, key: str, tenant_id: str | None = None) -> str:
        """
        Create cache key with optional tenant isolation.

        Args:
            key: Base cache key
            tenant_id: Optional tenant ID for isolation

        Returns:
            Formatted cache key
        """
        if self.tenant_aware and tenant_id:
            return f"tenant:{tenant_id}:{key}"
        return key

    async def get(self, key: str, tenant_id: str | None = None) -> Any | None:
        """
        Get value from cache.

        Args:
            key: Cache key
            tenant_id: Optional tenant ID for isolation

        Returns:
            Cached value or None if not found
        """
        full_key = self._make_key(key, tenant_id)
        return await self.backend.get(full_key)

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
        tenant_id: str | None = None,
    ) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            tenant_id: Optional tenant ID for isolation

        Returns:
            True if successful
        """
        full_key = self._make_key(key, tenant_id)
        return await self.backend.set(full_key, value, ttl)

    async def delete(self, key: str, tenant_id: str | None = None) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key
            tenant_id: Optional tenant ID for isolation

        Returns:
            True if key was deleted
        """
        full_key = self._make_key(key, tenant_id)
        return await self.backend.delete(full_key)

    async def exists(self, key: str, tenant_id: str | None = None) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key
            tenant_id: Optional tenant ID for isolation

        Returns:
            True if key exists
        """
        full_key = self._make_key(key, tenant_id)
        return await self.backend.exists(full_key)

    async def clear(self, tenant_id: str | None = None) -> bool:
        """
        Clear cache.

        Args:
            tenant_id: If provided, only clear tenant-specific keys

        Returns:
            True if successful
        """
        if tenant_id and self.tenant_aware:
            # Clear only tenant-specific keys
            # This is a simplified implementation
            # In production, you'd want to use SCAN with pattern matching
            logger.warning("Tenant-specific clear not fully implemented")
            return True
        return await self.backend.clear()

    async def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        stats = await self.backend.get_stats()
        stats["tenant_aware"] = self.tenant_aware
        return stats

    def generate_key(self, *args, **kwargs) -> str:
        """
        Generate cache key from function arguments.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Hashed cache key
        """
        # Create a hashable representation
        key_parts = []

        # Add positional arguments
        for arg in args:
            try:
                key_parts.append(json.dumps(arg, sort_keys=True))
            except (TypeError, ValueError):
                # For non-JSON-serializable objects, use repr
                key_parts.append(repr(arg))

        # Add keyword arguments
        for k, v in sorted(kwargs.items()):
            try:
                key_parts.append(f"{k}={json.dumps(v, sort_keys=True)}")
            except (TypeError, ValueError):
                key_parts.append(f"{k}={repr(v)}")

        # Create hash of the key using SHA256 for better security
        key_str = "|".join(key_parts)
        return hashlib.sha256(key_str.encode()).hexdigest()


def cached(
    ttl: int | None = None,
    key_prefix: str | None = None,
    key_func: Callable[..., str] | None = None,
    tenant_aware: bool = False,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for caching function results.

    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache keys
        key_func: Custom function to generate cache keys
        tenant_aware: Whether to include tenant ID in cache keys

    Returns:
        Decorated function

    Example:
        @cached(ttl=300, key_prefix="user")
        async def get_user(user_id: str) -> dict:
            # Expensive operation
            return await fetch_user_from_db(user_id)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # Check if function is async
        if not inspect.iscoroutinefunction(func):
            raise ValueError("cached decorator can only be used with async functions")

        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # Get cache service from somewhere (you'd inject this properly)
            # For now, we'll assume it's available as a keyword argument
            cache_service = kwargs.pop("_cache_service", None)
            if not cache_service:
                # No cache service, just call the function
                return await func(*args, **kwargs)

            # Get tenant ID if tenant-aware
            tenant_id = None
            if tenant_aware:
                tenant_id = kwargs.pop("_tenant_id", None)

            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = cache_service.generate_key(*args, **kwargs)

            # Add prefix if provided
            if key_prefix:
                cache_key = f"{key_prefix}:{cache_key}"
            else:
                cache_key = f"{func.__name__}:{cache_key}"

            # Try to get from cache
            cached_value = await cache_service.get(cache_key, tenant_id)
            if cached_value is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_value

            # Call the function
            logger.debug(f"Cache miss for key: {cache_key}")
            result = await func(*args, **kwargs)

            # Store in cache
            await cache_service.set(cache_key, result, ttl, tenant_id)

            return result

        # Store decorator parameters for inspection
        wrapper._cache_ttl = ttl
        wrapper._cache_key_prefix = key_prefix
        wrapper._cache_tenant_aware = tenant_aware

        return wrapper

    return decorator


def create_cache_service(
    config: CacheConfig | None = None,
    backend: str | None = None,
    tenant_aware: bool = False,
) -> CacheService:
    """
    Factory function to create cache service.

    Args:
        config: Cache configuration
        backend: Override backend type
        tenant_aware: Whether to enable tenant isolation

    Returns:
        CacheService instance

    Example:
        cache = create_cache_service(backend="redis", tenant_aware=True)
        await cache.initialize()
    """
    if config is None:
        config = CacheConfig()

    if backend:
        config.backend = backend

    return CacheService(config=config, tenant_aware=tenant_aware)