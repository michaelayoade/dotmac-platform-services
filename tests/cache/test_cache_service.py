"""Tests for cache service."""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from dotmac.platform.cache import (
    CacheConfig,
    CacheService,
    InMemoryCache,
    NullCache,
    RedisCache,
    cached,
    create_cache_service,
)
from dotmac.platform.cache.exceptions import CacheConnectionError


class TestCacheService:
    """Test CacheService functionality."""

    @pytest.fixture
    def cache_config(self):
        """Create test cache configuration."""
        return CacheConfig(
            backend="memory",
            default_ttl=300,
            max_size=100,
        )

    @pytest.fixture
    async def cache_service(self, cache_config):
        """Create and initialize cache service."""
        service = CacheService(config=cache_config)
        await service.initialize()
        yield service
        await service.shutdown()

    def test_cache_service_creation(self, cache_config):
        """Test cache service creation."""
        service = CacheService(config=cache_config)
        assert service is not None
        assert service.config == cache_config
        assert isinstance(service.backend, InMemoryCache)

    @pytest.mark.asyncio
    async def test_cache_service_initialization(self, cache_config):
        """Test cache service initialization."""
        service = CacheService(config=cache_config)
        await service.initialize()
        assert service.backend.is_connected()
        await service.shutdown()
        assert not service.backend.is_connected()

    @pytest.mark.asyncio
    async def test_cache_service_basic_operations(self, cache_service):
        """Test basic cache operations."""
        # Set value
        result = await cache_service.set("test_key", "test_value", ttl=60)
        assert result is True

        # Get value
        value = await cache_service.get("test_key")
        assert value == "test_value"

        # Check existence
        exists = await cache_service.exists("test_key")
        assert exists is True

        # Delete value
        deleted = await cache_service.delete("test_key")
        assert deleted is True

        # Check after deletion
        value = await cache_service.get("test_key")
        assert value is None

    @pytest.mark.asyncio
    async def test_cache_service_key_not_found(self, cache_service):
        """Test getting non-existent key."""
        value = await cache_service.get("non_existent_key")
        assert value is None

        exists = await cache_service.exists("non_existent_key")
        assert exists is False

        deleted = await cache_service.delete("non_existent_key")
        assert deleted is False

    @pytest.mark.asyncio
    async def test_cache_service_tenant_isolation(self, cache_config):
        """Test tenant-aware caching."""
        service = CacheService(config=cache_config, tenant_aware=True)
        await service.initialize()

        # Set values for different tenants
        await service.set("shared_key", "tenant1_value", tenant_id="tenant1")
        await service.set("shared_key", "tenant2_value", tenant_id="tenant2")

        # Get values by tenant
        value1 = await service.get("shared_key", tenant_id="tenant1")
        value2 = await service.get("shared_key", tenant_id="tenant2")

        assert value1 == "tenant1_value"
        assert value2 == "tenant2_value"

        # Ensure no cross-tenant access
        value_no_tenant = await service.get("shared_key")
        assert value_no_tenant is None

        await service.shutdown()

    @pytest.mark.asyncio
    async def test_cache_service_with_ttl(self, cache_service):
        """Test TTL functionality."""
        # Set with very short TTL
        await cache_service.set("ttl_key", "ttl_value", ttl=1)

        # Immediate get should work
        value = await cache_service.get("ttl_key")
        assert value == "ttl_value"

        # Wait for expiration
        await asyncio.sleep(1.1)

        # Should be expired
        value = await cache_service.get("ttl_key")
        assert value is None

    @pytest.mark.asyncio
    async def test_cache_service_clear(self, cache_service):
        """Test clearing cache."""
        # Set multiple values
        await cache_service.set("key1", "value1")
        await cache_service.set("key2", "value2")
        await cache_service.set("key3", "value3")

        # Clear cache
        result = await cache_service.clear()
        assert result is True

        # All keys should be gone
        assert await cache_service.get("key1") is None
        assert await cache_service.get("key2") is None
        assert await cache_service.get("key3") is None

    @pytest.mark.asyncio
    async def test_cache_service_stats(self, cache_service):
        """Test getting cache statistics."""
        # Set some values
        await cache_service.set("key1", "value1")
        await cache_service.set("key2", "value2")

        stats = await cache_service.get_stats()
        assert stats["backend"] == "memory"
        assert stats["connected"] is True
        assert stats["size"] == 2

    def test_cache_service_generate_key(self, cache_config):
        """Test cache key generation."""
        service = CacheService(config=cache_config)

        # Same arguments should generate same key
        key1 = service.generate_key("arg1", "arg2", kwarg1="value1")
        key2 = service.generate_key("arg1", "arg2", kwarg1="value1")
        assert key1 == key2

        # Different arguments should generate different keys
        key3 = service.generate_key("arg1", "arg3", kwarg1="value1")
        assert key1 != key3

        key4 = service.generate_key("arg1", "arg2", kwarg1="value2")
        assert key1 != key4


class TestCachedDecorator:
    """Test cached decorator functionality."""

    @pytest.fixture
    async def cache_service(self):
        """Create cache service for decorator tests."""
        service = create_cache_service(backend="memory")
        await service.initialize()
        yield service
        await service.shutdown()

    @pytest.mark.asyncio
    async def test_cached_decorator_basic(self, cache_service):
        """Test basic cached decorator functionality."""
        call_count = 0

        @cached(ttl=60, key_prefix="test")
        async def expensive_function(value: str) -> str:
            nonlocal call_count
            call_count += 1
            return f"processed_{value}"

        # First call should execute function
        result1 = await expensive_function("input", _cache_service=cache_service)
        assert result1 == "processed_input"
        assert call_count == 1

        # Second call should use cache
        result2 = await expensive_function("input", _cache_service=cache_service)
        assert result2 == "processed_input"
        assert call_count == 1  # Not incremented

    @pytest.mark.asyncio
    async def test_cached_decorator_different_args(self, cache_service):
        """Test cached decorator with different arguments."""
        call_count = 0

        @cached(ttl=60)
        async def function_with_args(a: int, b: int) -> int:
            nonlocal call_count
            call_count += 1
            return a + b

        # Different arguments should not share cache
        result1 = await function_with_args(1, 2, _cache_service=cache_service)
        assert result1 == 3
        assert call_count == 1

        result2 = await function_with_args(2, 3, _cache_service=cache_service)
        assert result2 == 5
        assert call_count == 2

        # Same arguments should use cache
        result3 = await function_with_args(1, 2, _cache_service=cache_service)
        assert result3 == 3
        assert call_count == 2  # Not incremented

    @pytest.mark.asyncio
    async def test_cached_decorator_tenant_aware(self, cache_service):
        """Test tenant-aware cached decorator."""
        cache_service.tenant_aware = True

        @cached(tenant_aware=True)
        async def tenant_function(value: str) -> str:
            return f"tenant_{value}"

        # Different tenants should have separate caches
        result1 = await tenant_function(
            "data",
            _cache_service=cache_service,
            _tenant_id="tenant1",
        )
        assert result1 == "tenant_data"

        # This should also be cached separately
        result2 = await tenant_function(
            "data",
            _cache_service=cache_service,
            _tenant_id="tenant2",
        )
        assert result2 == "tenant_data"

    @pytest.mark.asyncio
    async def test_cached_decorator_custom_key(self, cache_service):
        """Test cached decorator with custom key function."""
        def custom_key_func(user_id: str, *args, **kwargs) -> str:
            return f"user_{user_id}"

        @cached(key_func=custom_key_func)
        async def get_user_data(user_id: str, include_profile: bool = False) -> dict:
            return {"user_id": user_id, "profile": include_profile}

        # Should use custom key
        result1 = await get_user_data("123", True, _cache_service=cache_service)
        result2 = await get_user_data("123", False, _cache_service=cache_service)

        # Both should return the same cached value despite different include_profile
        assert result1 == result2

    def test_cached_decorator_sync_function_raises_error(self):
        """Test that cached decorator raises error for sync functions."""
        with pytest.raises(ValueError, match="can only be used with async functions"):

            @cached()
            def sync_function():
                return "value"

    @pytest.mark.asyncio
    async def test_cached_decorator_no_cache_service(self):
        """Test cached decorator without cache service."""
        call_count = 0

        @cached()
        async def function_without_cache() -> str:
            nonlocal call_count
            call_count += 1
            return "value"

        # Should just call function without caching
        result1 = await function_without_cache()
        result2 = await function_without_cache()

        assert result1 == "value"
        assert result2 == "value"
        assert call_count == 2  # Called twice


class TestCacheBackends:
    """Test different cache backends."""

    @pytest.mark.asyncio
    async def test_memory_backend(self):
        """Test memory cache backend."""
        config = CacheConfig(backend="memory", max_size=10, default_ttl=60)
        backend = InMemoryCache(config)

        await backend.connect()
        assert backend.is_connected()

        # Test basic operations
        await backend.set("key1", "value1", 60)
        value = await backend.get("key1")
        assert value == "value1"

        await backend.disconnect()
        assert not backend.is_connected()

    @pytest.mark.asyncio
    async def test_memory_backend_lru_eviction(self):
        """Test LRU eviction in memory backend."""
        config = CacheConfig(backend="memory", max_size=3)
        backend = InMemoryCache(config)
        await backend.connect()

        # Fill cache
        await backend.set("key1", "value1")
        await backend.set("key2", "value2")
        await backend.set("key3", "value3")

        # Access key1 to make it recently used
        await backend.get("key1")

        # Add new key, should evict key2 (least recently used)
        await backend.set("key4", "value4")

        # key2 should be evicted
        assert await backend.get("key2") is None
        assert await backend.get("key1") == "value1"
        assert await backend.get("key3") == "value3"
        assert await backend.get("key4") == "value4"

        await backend.disconnect()

    @pytest.mark.asyncio
    async def test_null_backend(self):
        """Test null cache backend."""
        config = CacheConfig(backend="null")
        backend = NullCache(config)

        await backend.connect()
        assert backend.is_connected()

        # Set should succeed but not store
        result = await backend.set("key", "value")
        assert result is True

        # Get should always return None
        value = await backend.get("key")
        assert value is None

        # Exists should always return False
        exists = await backend.exists("key")
        assert exists is False

        await backend.disconnect()

    @pytest.mark.asyncio
    @patch("dotmac.platform.cache.backends.HAS_REDIS", False)
    async def test_redis_backend_without_redis(self):
        """Test Redis backend when Redis is not installed."""
        config = CacheConfig(backend="redis")

        with pytest.raises(ImportError, match="Redis not available"):
            RedisCache(config)

    @pytest.mark.asyncio
    @patch("dotmac.platform.cache.backends.redis")
    @patch("dotmac.platform.cache.backends.HAS_REDIS", True)
    async def test_redis_backend_connection_failure(self, mock_redis):
        """Test Redis backend connection failure."""
        config = CacheConfig(backend="redis")
        backend = RedisCache(config)

        # Mock connection failure
        mock_client = AsyncMock()
        mock_client.ping.side_effect = Exception("Connection failed")
        mock_redis.from_url.return_value = mock_client

        with pytest.raises(CacheConnectionError, match="Redis connection failed"):
            await backend.connect()


class TestCacheFactory:
    """Test cache service factory."""

    def test_create_cache_service_default(self):
        """Test creating cache service with defaults."""
        service = create_cache_service()
        assert service is not None
        assert service.config.backend == "memory"
        assert not service.tenant_aware

    def test_create_cache_service_with_backend(self):
        """Test creating cache service with specific backend."""
        service = create_cache_service(backend="null")
        assert service.config.backend == "null"
        assert isinstance(service.backend, NullCache)

    def test_create_cache_service_tenant_aware(self):
        """Test creating tenant-aware cache service."""
        service = create_cache_service(tenant_aware=True)
        assert service.tenant_aware is True

    def test_create_cache_service_with_config(self):
        """Test creating cache service with custom config."""
        config = CacheConfig(
            backend="memory",
            default_ttl=600,
            max_size=500,
        )
        service = create_cache_service(config=config)
        assert service.config == config
        assert service.config.default_ttl == 600
        assert service.config.max_size == 500