"""
General-purpose caching service for DotMac Platform Services.

Provides a unified caching interface with multiple backend support:
- In-memory cache for development/testing
- Redis cache for production
- Null cache for disabling caching

Features:
- TTL support with automatic expiration
- LRU eviction for memory backend
- Async/await interface
- Type-safe with Pydantic models
- Tenant isolation support
"""

from .backends import InMemoryCache, NullCache, RedisCache
from .config import CacheConfig
from .exceptions import CacheConnectionError, CacheError, CacheKeyError
from .interfaces import CacheBackend
from .service import CacheService, cached, create_cache_service

__all__ = [
    # Service
    "CacheService",
    "create_cache_service",
    "cached",
    # Backends
    "CacheBackend",
    "InMemoryCache",
    "RedisCache",
    "NullCache",
    # Config
    "CacheConfig",
    # Exceptions
    "CacheError",
    "CacheConnectionError",
    "CacheKeyError",
]