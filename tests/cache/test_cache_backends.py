"""Tests for cache backends using pytest only."""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from dotmac.platform.cache.backends import InMemoryCache, NullCache, RedisCache
from dotmac.platform.cache.config import CacheConfig


class TestInMemoryBackend:
    """Test in-memory cache backend."""

    @pytest.fixture
    async def backend(self):
        """Create in-memory backend."""
        config = CacheConfig(max_size=3)
        backend = InMemoryCache(config)
        await backend.connect()
        yield backend
        if hasattr(backend, 'close'):
            await backend.close()

    @pytest.mark.asyncio
    async def test_get_set(self, backend):
        """Test get and set operations."""
        # Set value
        await backend.set("key1", "value1")

        # Get value
        value = await backend.get("key1")
        assert value == "value1"

        # Get non-existent key
        value = await backend.get("nonexistent")
        assert value is None

    @pytest.mark.asyncio
    async def test_ttl(self, backend):
        """Test TTL functionality."""
        # Set with TTL
        await backend.set("key1", "value1", ttl=1)

        # Value should exist immediately
        value = await backend.get("key1")
        assert value == "value1"

        # Wait for expiration
        await asyncio.sleep(1.1)

        # Value should be expired
        value = await backend.get("key1")
        assert value is None

    @pytest.mark.asyncio
    async def test_delete(self, backend):
        """Test delete operation."""
        # Set value
        await backend.set("key1", "value1")

        # Delete it
        result = await backend.delete("key1")
        assert result is True

        # Should be gone
        value = await backend.get("key1")
        assert value is None

        # Delete non-existent key
        result = await backend.delete("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_exists(self, backend):
        """Test exists operation."""
        # Set value
        await backend.set("key1", "value1")

        # Should exist
        exists = await backend.exists("key1")
        assert exists is True

        # Non-existent key
        exists = await backend.exists("nonexistent")
        assert exists is False

    @pytest.mark.asyncio
    async def test_clear(self, backend):
        """Test clear operation."""
        # Set multiple values
        await backend.set("key1", "value1")
        await backend.set("key2", "value2")

        # Clear all
        await backend.clear()

        # Should be empty
        assert await backend.exists("key1") is False
        assert await backend.exists("key2") is False

    @pytest.mark.asyncio
    async def test_lru_eviction(self, backend):
        """Test LRU eviction policy."""
        # Fill cache to max size
        await backend.set("key1", "value1")
        await backend.set("key2", "value2")
        await backend.set("key3", "value3")

        # Access key1 to make it recently used
        await backend.get("key1")

        # Add new key, should evict key2 (least recently used)
        await backend.set("key4", "value4")

        # key1 and key3 should exist, key2 should be evicted
        assert await backend.exists("key1") is True
        assert await backend.exists("key2") is False
        assert await backend.exists("key3") is True
        assert await backend.exists("key4") is True

    @pytest.mark.asyncio
    async def test_get_many(self, backend):
        """Test get_many operation."""
        # Set multiple values
        await backend.set("key1", "value1")
        await backend.set("key2", "value2")

        # Get many
        values = await backend.get_many(["key1", "key2", "key3"])

        assert values == {
            "key1": "value1",
            "key2": "value2",
            "key3": None,
        }

    @pytest.mark.asyncio
    async def test_set_many(self, backend):
        """Test set_many operation."""
        # Set many values
        await backend.set_many({
            "key1": "value1",
            "key2": "value2",
        })

        # Verify they exist
        assert await backend.get("key1") == "value1"
        assert await backend.get("key2") == "value2"

    @pytest.mark.asyncio
    async def test_stats(self, backend):
        """Test statistics tracking."""
        # Perform operations
        await backend.set("key1", "value1")
        await backend.get("key1")  # Hit
        await backend.get("key2")  # Miss

        stats = backend.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["sets"] == 1
        assert stats["size"] == 1


class TestNullBackend:
    """Test null cache backend."""

    @pytest.fixture
    async def backend(self):
        """Create null backend."""
        config = CacheConfig(backend="null")
        backend = NullCache(config)
        await backend.connect()
        yield backend
        if hasattr(backend, 'close'):
            await backend.close()

    @pytest.mark.asyncio
    async def test_null_operations(self, backend):
        """Test that null backend doesn't store anything."""
        # Set should succeed but not store
        await backend.set("key1", "value1")

        # Get should return None
        value = await backend.get("key1")
        assert value is None

        # Exists should return False
        exists = await backend.exists("key1")
        assert exists is False

        # Delete should return False
        result = await backend.delete("key1")
        assert result is False

    @pytest.mark.asyncio
    async def test_null_clear(self, backend):
        """Test null backend clear."""
        # Should not raise
        await backend.clear()

    @pytest.mark.asyncio
    async def test_null_stats(self, backend):
        """Test null backend stats."""
        stats = backend.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["sets"] == 0
        assert stats["size"] == 0


class TestRedisBackend:
    """Test Redis cache backend."""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        mock = AsyncMock()
        mock.get = AsyncMock(return_value=None)
        mock.set = AsyncMock(return_value=True)
        mock.delete = AsyncMock(return_value=1)
        mock.exists = AsyncMock(return_value=0)
        mock.flushdb = AsyncMock()
        mock.mget = AsyncMock(return_value=[None])
        mock.close = AsyncMock()
        mock.ping = AsyncMock(return_value=True)
        return mock

    @pytest.fixture
    async def backend(self, mock_redis):
        """Create Redis backend with mock."""
        with patch("redis.asyncio.Redis.from_url", return_value=mock_redis):
            config = CacheConfig(backend="redis", redis_url="redis://localhost:6379/0")
            backend = RedisCache(config)
            backend.client = mock_redis
            await backend.connect()
            yield backend
            if hasattr(backend, 'close'):
                await backend.close()

    @pytest.mark.asyncio
    async def test_get_set(self, backend, mock_redis):
        """Test get and set operations."""
        # Setup mock
        mock_redis.get.return_value = b'{"value": "value1"}'

        # Set value
        await backend.set("key1", {"value": "value1"}, ttl=60)
        mock_redis.set.assert_called_once()

        # Get value
        value = await backend.get("key1")
        assert value == {"value": "value1"}
        mock_redis.get.assert_called_with("key1")

    @pytest.mark.asyncio
    async def test_delete(self, backend, mock_redis):
        """Test delete operation."""
        mock_redis.delete.return_value = 1

        result = await backend.delete("key1")
        assert result is True
        mock_redis.delete.assert_called_with("key1")

    @pytest.mark.asyncio
    async def test_exists(self, backend, mock_redis):
        """Test exists operation."""
        mock_redis.exists.return_value = 1

        exists = await backend.exists("key1")
        assert exists is True
        mock_redis.exists.assert_called_with("key1")

    @pytest.mark.asyncio
    async def test_clear(self, backend, mock_redis):
        """Test clear operation."""
        await backend.clear()
        mock_redis.flushdb.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_many(self, backend, mock_redis):
        """Test get_many operation."""
        mock_redis.mget.return_value = [
            b'{"value": "value1"}',
            None,
            b'{"value": "value3"}',
        ]

        values = await backend.get_many(["key1", "key2", "key3"])

        assert values == {
            "key1": {"value": "value1"},
            "key2": None,
            "key3": {"value": "value3"},
        }
        mock_redis.mget.assert_called_with(["key1", "key2", "key3"])

    @pytest.mark.asyncio
    async def test_set_many(self, backend, mock_redis):
        """Test set_many operation."""
        await backend.set_many({
            "key1": "value1",
            "key2": {"data": "value2"},
        }, ttl=60)

        # Should call pipeline
        assert mock_redis.pipeline.called

    @pytest.mark.asyncio
    async def test_connection_error(self, mock_redis):
        """Test handling connection errors."""
        mock_redis.ping.side_effect = Exception("Connection failed")

        with patch("redis.asyncio.Redis.from_url", return_value=mock_redis):
            config = CacheConfig(backend="redis", redis_url="redis://localhost:6379/0")
            backend = RedisCache(config)
            backend.client = mock_redis

            # Operations should handle errors gracefully
            value = await backend.get("key1")
            assert value is None

            result = await backend.set("key1", "value1")
            assert result is False

    @pytest.mark.asyncio
    async def test_close(self, backend, mock_redis):
        """Test closing connection."""
        await backend.close()
        mock_redis.close.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])