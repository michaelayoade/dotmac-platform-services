"""Tests for distributed locks module."""
import asyncio
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock

from dotmac.platform.distributed_locks import (
    get_redis_client,
    distributed_lock,
    try_lock,
    release_lock,
    DistributedLock,
)


class TestDistributedLocks:
    """Test distributed locks functionality."""

    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client."""
        client = AsyncMock()
        client.set = AsyncMock()
        client.eval = AsyncMock()
        client.get = AsyncMock()
        return client

    @patch("dotmac.platform.distributed_locks.redis.from_url")
    @patch("dotmac.platform.distributed_locks.settings")
    async def test_get_redis_client_creates_new(self, mock_settings, mock_from_url):
        """Test Redis client creation."""
        # Clear any existing client
        import dotmac.platform.distributed_locks
        dotmac.platform.distributed_locks._redis_client = None

        mock_settings.redis.redis_url = "redis://localhost:6379"
        mock_client = AsyncMock()
        mock_from_url.return_value = mock_client

        result = await get_redis_client()

        mock_from_url.assert_called_once_with("redis://localhost:6379")
        assert result == mock_client

    async def test_get_redis_client_returns_existing(self):
        """Test Redis client returns existing instance."""
        # Set up existing client
        import dotmac.platform.distributed_locks
        mock_existing_client = AsyncMock()
        dotmac.platform.distributed_locks._redis_client = mock_existing_client

        with patch("dotmac.platform.distributed_locks.redis.from_url") as mock_from_url:
            result = await get_redis_client()

            # Should not create new client
            mock_from_url.assert_not_called()
            assert result == mock_existing_client

        # Clean up
        dotmac.platform.distributed_locks._redis_client = None

    @patch("dotmac.platform.distributed_locks.get_redis_client")
    async def test_distributed_lock_success(self, mock_get_client, mock_redis_client):
        """Test successful lock acquisition and release."""
        mock_get_client.return_value = mock_redis_client
        mock_redis_client.set.return_value = True  # Lock acquired
        mock_redis_client.eval.return_value = 1  # Lock released

        async with distributed_lock("test_key", timeout=30):
            # Code in critical section
            pass

        # Verify lock acquisition
        assert mock_redis_client.set.call_count >= 1
        set_call = mock_redis_client.set.call_args
        assert set_call[0][0] == "lock:test_key"  # key
        assert set_call[1]["nx"] is True
        assert set_call[1]["ex"] == 30

        # Verify lock release
        mock_redis_client.eval.assert_called_once()

    @patch("dotmac.platform.distributed_locks.get_redis_client")
    async def test_distributed_lock_timeout(self, mock_get_client, mock_redis_client):
        """Test lock timeout when cannot acquire."""
        mock_get_client.return_value = mock_redis_client
        mock_redis_client.set.return_value = False  # Lock not acquired

        with pytest.raises(TimeoutError, match="Could not acquire lock test_key within 1s"):
            async with distributed_lock("test_key", timeout=1, retry_delay=0.1):
                pass

    @patch("dotmac.platform.distributed_locks.get_redis_client")
    @patch("asyncio.sleep")
    async def test_distributed_lock_retry_success(self, mock_sleep, mock_get_client, mock_redis_client):
        """Test lock acquisition after retry."""
        mock_get_client.return_value = mock_redis_client
        # First call fails, second succeeds
        mock_redis_client.set.side_effect = [False, True]
        mock_redis_client.eval.return_value = 1

        async with distributed_lock("test_key", timeout=2, retry_delay=0.1):
            pass

        # Verify retry was attempted
        assert mock_redis_client.set.call_count == 2
        mock_sleep.assert_called_with(0.1)

    @patch("dotmac.platform.distributed_locks.get_redis_client")
    async def test_try_lock_success(self, mock_get_client, mock_redis_client):
        """Test try_lock successful acquisition."""
        mock_get_client.return_value = mock_redis_client
        mock_redis_client.set.return_value = True

        result = await try_lock("test_key", timeout=30)

        assert result is not None
        assert isinstance(result, str)
        mock_redis_client.set.assert_called_once()

    @patch("dotmac.platform.distributed_locks.get_redis_client")
    async def test_try_lock_failure(self, mock_get_client, mock_redis_client):
        """Test try_lock failure."""
        mock_get_client.return_value = mock_redis_client
        mock_redis_client.set.return_value = False

        result = await try_lock("test_key", timeout=30)

        assert result is None

    @patch("dotmac.platform.distributed_locks.get_redis_client")
    async def test_release_lock_success(self, mock_get_client, mock_redis_client):
        """Test release_lock successful release."""
        mock_get_client.return_value = mock_redis_client
        mock_redis_client.eval.return_value = 1

        result = await release_lock("test_key", "test_value")

        assert result is True
        mock_redis_client.eval.assert_called_once()

    @patch("dotmac.platform.distributed_locks.get_redis_client")
    async def test_release_lock_failure(self, mock_get_client, mock_redis_client):
        """Test release_lock when we don't own the lock."""
        mock_get_client.return_value = mock_redis_client
        mock_redis_client.eval.return_value = 0

        result = await release_lock("test_key", "wrong_value")

        assert result is False

    @patch("dotmac.platform.distributed_locks.get_redis_client")
    async def test_release_lock_with_coroutine_result(self, mock_get_client, mock_redis_client):
        """Test release_lock when eval returns coroutine."""
        mock_get_client.return_value = mock_redis_client

        # Create a coroutine that returns 1
        async def mock_coroutine():
            return 1

        mock_redis_client.eval.return_value = mock_coroutine()

        result = await release_lock("test_key", "test_value")

        assert result is True


class TestDistributedLockClass:
    """Test DistributedLock class."""

    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client."""
        client = AsyncMock()
        client.set = AsyncMock()
        client.eval = AsyncMock()
        return client

    @patch("dotmac.platform.distributed_locks.get_redis_client")
    async def test_distributed_lock_acquire_success(self, mock_get_client, mock_redis_client):
        """Test DistributedLock acquire success."""
        mock_get_client.return_value = mock_redis_client
        mock_redis_client.set.return_value = True

        lock = DistributedLock("test_key", timeout=30)
        result = await lock.acquire()

        assert result is True
        assert lock.lock_value is not None

    @patch("dotmac.platform.distributed_locks.get_redis_client")
    async def test_distributed_lock_acquire_failure(self, mock_get_client, mock_redis_client):
        """Test DistributedLock acquire failure."""
        mock_get_client.return_value = mock_redis_client
        mock_redis_client.set.return_value = False

        lock = DistributedLock("test_key", timeout=1)
        result = await lock.acquire(retry_delay=0.1)

        assert result is False
        assert lock.lock_value is None

    @patch("dotmac.platform.distributed_locks.get_redis_client")
    async def test_distributed_lock_acquire_already_holding(self, mock_get_client, mock_redis_client):
        """Test DistributedLock acquire when already holding lock."""
        lock = DistributedLock("test_key")
        lock.lock_value = "existing_value"

        result = await lock.acquire()

        assert result is False

    @patch("dotmac.platform.distributed_locks.release_lock")
    async def test_distributed_lock_release_success(self, mock_release_lock):
        """Test DistributedLock release success."""
        mock_release_lock.return_value = True

        lock = DistributedLock("test_key")
        lock.lock_value = "test_value"

        result = await lock.release()

        assert result is True
        assert lock.lock_value is None
        mock_release_lock.assert_called_once_with("test_key", "test_value")

    async def test_distributed_lock_release_no_value(self):
        """Test DistributedLock release when no lock value."""
        lock = DistributedLock("test_key")

        result = await lock.release()

        assert result is False

    @patch("dotmac.platform.distributed_locks.get_redis_client")
    async def test_distributed_lock_context_manager_success(self, mock_get_client, mock_redis_client):
        """Test DistributedLock as async context manager."""
        mock_get_client.return_value = mock_redis_client
        mock_redis_client.set.return_value = True

        with patch.object(DistributedLock, "release", new_callable=AsyncMock) as mock_release:
            mock_release.return_value = True

            async with DistributedLock("test_key") as lock:
                assert isinstance(lock, DistributedLock)

            mock_release.assert_called_once()

    @patch("dotmac.platform.distributed_locks.get_redis_client")
    async def test_distributed_lock_context_manager_timeout(self, mock_get_client, mock_redis_client):
        """Test DistributedLock context manager timeout."""
        mock_get_client.return_value = mock_redis_client
        mock_redis_client.set.return_value = False

        with pytest.raises(TimeoutError, match="Could not acquire lock test_key"):
            async with DistributedLock("test_key", timeout=1):
                pass

    def test_distributed_lock_class_init(self):
        """Test DistributedLock initialization."""
        lock = DistributedLock("test_key", timeout=60)

        assert lock.key == "test_key"
        assert lock.timeout == 60
        assert lock.lock_value is None