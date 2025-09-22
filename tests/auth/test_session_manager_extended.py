"""
Comprehensive tests for SessionManager with full coverage.
Tests session creation, retrieval, expiration, invalidation, and Redis integration.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta, UTC
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from dotmac.platform.auth.session_manager import (
    MemorySessionBackend,
    RedisSessionBackend,
    SessionConfig,
    SessionData,
    SessionManager,
    SessionStatus,
)
# Mock fixtures imported directly from mock_redis module when needed


@pytest.mark.asyncio
class TestSessionData:
    """Comprehensive tests for SessionData model."""

    def test_session_data_creation(self):
        """Test SessionData creation and attributes."""
        now = datetime.now(UTC)
        session = SessionData(
            session_id="test-123",
            user_id="user-456",
            tenant_id="tenant-789",
            created_at=now,
            last_accessed=now,
            expires_at=now + timedelta(hours=1),
            status=SessionStatus.ACTIVE,
            metadata={"ip": "192.168.1.1", "user_agent": "TestAgent"},
        )

        assert session.session_id == "test-123"
        assert session.user_id == "user-456"
        assert session.tenant_id == "tenant-789"
        assert session.metadata["ip"] == "192.168.1.1"
        assert session.status == SessionStatus.ACTIVE

    def test_session_data_to_dict(self):
        """Test conversion to dictionary for storage."""
        now = datetime.now(UTC)
        expires = now + timedelta(hours=1)
        session = SessionData(
            session_id="test-123",
            user_id="user-456",
            tenant_id=None,
            created_at=now,
            last_accessed=now,
            expires_at=expires,
            status=SessionStatus.ACTIVE,
            metadata={},
        )

        data = session.to_dict()
        assert data["session_id"] == "test-123"
        assert data["user_id"] == "user-456"
        assert data["tenant_id"] is None
        assert data["created_at"] == now.isoformat()
        assert data["expires_at"] == expires.isoformat()
        assert data["status"] == "active"

    def test_session_data_from_dict(self):
        """Test creation from dictionary."""
        now_str = datetime.now(UTC).isoformat()
        expires_str = (datetime.now(UTC) + timedelta(hours=1)).isoformat()

        data = {
            "session_id": "test-123",
            "user_id": "user-456",
            "tenant_id": "tenant-789",
            "created_at": now_str,
            "last_accessed": now_str,
            "expires_at": expires_str,
            "status": SessionStatus.ACTIVE,
            "metadata": {"key": "value"},
        }

        session = SessionData.from_dict(data)
        assert session.session_id == "test-123"
        assert session.user_id == "user-456"
        assert isinstance(session.created_at, datetime)
        assert session.metadata["key"] == "value"

    def test_session_is_expired(self):
        """Test session expiration checking."""
        now = datetime.now(UTC)

        # Expired session
        expired_session = SessionData(
            session_id="exp-1",
            user_id="user-1",
            tenant_id=None,
            created_at=now - timedelta(hours=2),
            last_accessed=now - timedelta(hours=1),
            expires_at=now - timedelta(seconds=1),
            status=SessionStatus.ACTIVE,
            metadata={},
        )
        assert expired_session.is_expired() is True
        assert expired_session.is_active() is False

        # Active session
        active_session = SessionData(
            session_id="act-1",
            user_id="user-1",
            tenant_id=None,
            created_at=now,
            last_accessed=now,
            expires_at=now + timedelta(hours=1),
            status=SessionStatus.ACTIVE,
            metadata={},
        )
        assert active_session.is_expired() is False
        assert active_session.is_active() is True

    def test_session_is_active_with_different_status(self):
        """Test is_active with different session statuses."""
        now = datetime.now(UTC)
        future = now + timedelta(hours=1)

        # Invalidated session (not expired but status is INVALIDATED)
        invalidated = SessionData(
            session_id="inv-1",
            user_id="user-1",
            tenant_id=None,
            created_at=now,
            last_accessed=now,
            expires_at=future,
            status=SessionStatus.INVALIDATED,
            metadata={},
        )
        assert invalidated.is_active() is False

        # Suspicious session
        suspicious = SessionData(
            session_id="sus-1",
            user_id="user-1",
            tenant_id=None,
            created_at=now,
            last_accessed=now,
            expires_at=future,
            status=SessionStatus.SUSPICIOUS,
            metadata={},
        )
        assert suspicious.is_active() is False


@pytest.mark.asyncio
class TestSessionConfig:
    """Tests for SessionConfig validation."""

    def test_session_config_defaults(self):
        """Test default configuration values."""
        config = settings.Session.model_copy()
        assert config.secret_key == "change-me"
        assert config.session_lifetime_seconds == 3600
        assert config.refresh_threshold_seconds == 300
        assert config.max_sessions_per_user == 10
        assert config.enable_refresh is True
        assert config.secure_cookie is False
        assert config.same_site == "lax"

    def test_session_config_custom_values(self):
        """Test custom configuration values."""
        config = settings.Session.model_copy(update={
            secret_key="super-secret",
            session_lifetime_seconds=7200,
            refresh_threshold_seconds=600,
            max_sessions_per_user=5,
            enable_refresh=False,
            secure_cookie=True,
            same_site="strict",
        })
        assert config.secret_key == "super-secret"
        assert config.session_lifetime_seconds == 7200
        assert config.max_sessions_per_user == 5
        assert config.secure_cookie is True

    def test_session_config_validation(self):
        """Test configuration validation."""
        # Invalid session lifetime
        with pytest.raises(ValueError, match="session_lifetime_seconds must be > 0"):
            settings.Session.model_copy(update={session_lifetime_seconds=0})

        with pytest.raises(ValueError, match="session_lifetime_seconds must be > 0"):
            settings.Session.model_copy(update={session_lifetime_seconds=-100})

        # Invalid refresh threshold
        with pytest.raises(ValueError, match="refresh_threshold_seconds must be > 0"):
            settings.Session.model_copy(update={refresh_threshold_seconds=0})

        # Invalid max sessions
        with pytest.raises(ValueError, match="max_sessions_per_user must be > 0"):
            settings.Session.model_copy(update={max_sessions_per_user=0})

        # Refresh threshold >= lifetime
        with pytest.raises(ValueError, match="refresh_threshold_seconds must be < session_lifetime_seconds"):
            settings.Session.model_copy(update={session_lifetime_seconds=300, refresh_threshold_seconds=300})

        with pytest.raises(ValueError, match="refresh_threshold_seconds must be < session_lifetime_seconds"):
            settings.Session.model_copy(update={session_lifetime_seconds=300, refresh_threshold_seconds=400})


@pytest.mark.asyncio
class TestMemorySessionBackend:
    """Tests for in-memory session backend."""

    async def test_store_and_get_session(self):
        """Test storing and retrieving sessions."""
        backend = MemorySessionBackend()
        now = datetime.now(UTC)

        session = SessionData(
            session_id="mem-1",
            user_id="user-1",
            tenant_id="tenant-1",
            created_at=now,
            last_accessed=now,
            expires_at=now + timedelta(hours=1),
            status=SessionStatus.ACTIVE,
            metadata={"test": "value"},
        )

        # Store session
        result = await backend.store_session(session)
        assert result is True

        # Get session
        retrieved = await backend.get_session("mem-1")
        assert retrieved is not None
        assert retrieved.session_id == "mem-1"
        assert retrieved.metadata["test"] == "value"

    async def test_get_expired_session(self):
        """Test that expired sessions are automatically deleted."""
        backend = MemorySessionBackend()
        now = datetime.now(UTC)

        expired_session = SessionData(
            session_id="exp-1",
            user_id="user-1",
            tenant_id=None,
            created_at=now - timedelta(hours=2),
            last_accessed=now - timedelta(hours=1),
            expires_at=now - timedelta(seconds=1),
            status=SessionStatus.ACTIVE,
            metadata={},
        )

        await backend.store_session(expired_session)
        retrieved = await backend.get_session("exp-1")
        assert retrieved is None  # Should be deleted
        assert "exp-1" not in backend.sessions

    async def test_delete_session(self):
        """Test session deletion."""
        backend = MemorySessionBackend()
        now = datetime.now(UTC)

        session = SessionData(
            session_id="del-1",
            user_id="user-del",
            tenant_id=None,
            created_at=now,
            last_accessed=now,
            expires_at=now + timedelta(hours=1),
            status=SessionStatus.ACTIVE,
            metadata={},
        )

        await backend.store_session(session)
        assert "del-1" in backend.sessions

        # Delete session
        result = await backend.delete_session("del-1")
        assert result is True
        assert "del-1" not in backend.sessions
        assert "del-1" not in backend.user_sessions.get("user-del", set())

        # Delete non-existent session
        result = await backend.delete_session("non-existent")
        assert result is False

    async def test_get_user_sessions(self):
        """Test retrieving all sessions for a user."""
        backend = MemorySessionBackend()
        now = datetime.now(UTC)

        # Store multiple sessions for same user
        for i in range(3):
            session = SessionData(
                session_id=f"user1-sess-{i}",
                user_id="user-1",
                tenant_id=None,
                created_at=now,
                last_accessed=now,
                expires_at=now + timedelta(hours=1),
                status=SessionStatus.ACTIVE,
                metadata={},
            )
            await backend.store_session(session)

        # Store session for different user
        other_session = SessionData(
            session_id="user2-sess",
            user_id="user-2",
            tenant_id=None,
            created_at=now,
            last_accessed=now,
            expires_at=now + timedelta(hours=1),
            status=SessionStatus.ACTIVE,
            metadata={},
        )
        await backend.store_session(other_session)

        # Get user-1 sessions
        user1_sessions = await backend.get_user_sessions("user-1")
        assert len(user1_sessions) == 3
        assert all(s.startswith("user1-sess-") for s in user1_sessions)

        # Get user-2 sessions
        user2_sessions = await backend.get_user_sessions("user-2")
        assert len(user2_sessions) == 1
        assert "user2-sess" in user2_sessions

    async def test_cleanup_expired_sessions(self):
        """Test cleanup of expired sessions."""
        backend = MemorySessionBackend()
        now = datetime.now(UTC)

        # Mix of expired and active sessions
        sessions_data = [
            ("exp-1", now - timedelta(seconds=1), True),  # expired
            ("exp-2", now - timedelta(hours=1), True),     # expired
            ("active-1", now + timedelta(hours=1), False),  # active
            ("active-2", now + timedelta(minutes=30), False),  # active
        ]

        for sid, expires, should_expire in sessions_data:
            session = SessionData(
                session_id=sid,
                user_id=f"user-{sid}",
                tenant_id=None,
                created_at=now - timedelta(hours=2),
                last_accessed=now - timedelta(minutes=5),
                expires_at=expires,
                status=SessionStatus.ACTIVE,
                metadata={},
            )
            await backend.store_session(session)

        # Run cleanup
        cleaned = await backend.cleanup_expired_sessions()
        assert cleaned == 2  # Should clean 2 expired sessions

        # Verify expired sessions are gone
        assert await backend.get_session("exp-1") is None
        assert await backend.get_session("exp-2") is None

        # Verify active sessions remain
        assert await backend.get_session("active-1") is not None
        assert await backend.get_session("active-2") is not None


@pytest.mark.asyncio
class TestRedisSessionBackend:
    """Tests for Redis session backend."""

    async def test_redis_initialization(self):
        """Test Redis backend initialization."""
        # With URL
        backend = RedisSessionBackend(redis_url="redis://localhost:6379/0")
        assert backend.redis_url == "redis://localhost:6379/0"
        assert backend.key_prefix == "session:"

        # With host/port/db
        backend2 = RedisSessionBackend(host="127.0.0.1", port=6380, db=1)
        assert backend2.redis_url == "redis://127.0.0.1:6380/1"

        # Custom prefix
        backend3 = RedisSessionBackend(key_prefix="mysession:")
        assert backend3.key_prefix == "mysession:"

    async def test_redis_lazy_connection(self):
        """Test lazy Redis connection initialization."""
        backend = RedisSessionBackend()
        assert backend._redis is None

        with patch("redis.asyncio.Redis.from_url") as mock_from_url:
            mock_client = MagicMock()
            mock_from_url.return_value = mock_client

            # Access redis property triggers connection
            client = backend.redis
            assert client is mock_client
            mock_from_url.assert_called_once_with("redis://localhost:6379/0", decode_responses=True)

    async def test_redis_store_and_get_session(self):
        """Test storing and retrieving sessions from Redis."""
        backend = RedisSessionBackend()
        from tests.fixtures.mock_redis import MockRedis
        mock_client = MockRedis()

        with patch.object(backend, "_redis", mock_client):
            now = datetime.now(UTC)
            expires = now + timedelta(hours=1)

            session = SessionData(
                session_id="redis-1",
                user_id="user-redis",
                tenant_id="tenant-redis",
                created_at=now,
                last_accessed=now,
                expires_at=expires,
                status=SessionStatus.ACTIVE,
                metadata={"source": "redis-test"},
            )

            # Store session
            result = await backend.store_session(session)
            assert result is True

            # Verify pipeline operations
            assert mock_client.pipeline.called

            # Simulate get operation
            mock_client.get.return_value = json.dumps(session.to_dict())
            retrieved = await backend.get_session("redis-1")
            assert retrieved is not None
            assert retrieved.session_id == "redis-1"
            assert retrieved.metadata["source"] == "redis-test"

    async def test_redis_get_expired_session(self):
        """Test that expired sessions are deleted from Redis."""
        backend = RedisSessionBackend()
        from tests.fixtures.mock_redis import MockRedis
        mock_client = MockRedis()

        with patch.object(backend, "_redis", mock_client):
            now = datetime.now(UTC)
            expired_session = SessionData(
                session_id="exp-redis",
                user_id="user-1",
                tenant_id=None,
                created_at=now - timedelta(hours=2),
                last_accessed=now - timedelta(hours=1),
                expires_at=now - timedelta(seconds=1),
                status=SessionStatus.ACTIVE,
                metadata={},
            )

            # Mock get returns expired session
            mock_client.get.return_value = json.dumps(expired_session.to_dict())

            retrieved = await backend.get_session("exp-redis")
            assert retrieved is None  # Should return None for expired

            # Verify deletion was attempted
            mock_client.pipeline.assert_called()

    async def test_redis_delete_session(self):
        """Test session deletion from Redis."""
        backend = RedisSessionBackend()
        from tests.fixtures.mock_redis import MockRedis, MockRedisPipeline
        mock_client = MockRedis()

        with patch.object(backend, "_redis", mock_client):
            now = datetime.now(UTC)
            session = SessionData(
                session_id="del-redis",
                user_id="user-del",
                tenant_id=None,
                created_at=now,
                last_accessed=now,
                expires_at=now + timedelta(hours=1),
                status=SessionStatus.ACTIVE,
                metadata={},
            )

            # Mock get returns the session
            mock_client.get.return_value = json.dumps(session.to_dict())

            # Mock pipeline execute
            mock_pipe = MockRedisPipeline()
            mock_pipe.execute.return_value = [1, 1]  # Deleted successfully
            mock_client.pipeline.return_value = mock_pipe

            result = await backend.delete_session("del-redis")
            assert result is True

            # Verify pipeline operations
            mock_pipe.delete.assert_called_with("session:del-redis")
            mock_pipe.srem.assert_called_with("session:user:user-del", "del-redis")

    async def test_redis_get_user_sessions(self):
        """Test retrieving user sessions from Redis."""
        backend = RedisSessionBackend()
        from tests.fixtures.mock_redis import MockRedis
        mock_client = MockRedis()

        with patch.object(backend, "_redis", mock_client):
            # Mock smembers returns session IDs
            mock_client.smembers.return_value = {"sess-1", "sess-2", "sess-3"}

            sessions = await backend.get_user_sessions("user-1")
            assert len(sessions) == 3
            assert "sess-1" in sessions
            assert "sess-2" in sessions

            mock_client.smembers.assert_called_with("session:user:user-1")

    async def test_redis_error_handling(self):
        """Test error handling in Redis operations."""
        backend = RedisSessionBackend()
        mock_client = mock_redis()

        with patch.object(backend, "_redis", mock_client):
            # Simulate Redis error
            mock_client.get.side_effect = Exception("Redis connection error")

            result = await backend.get_session("error-sess")
            assert result is None  # Should handle error gracefully

            # Test store error
            mock_client.pipeline.side_effect = Exception("Redis write error")
            session = SessionData(
                session_id="err-1",
                user_id="user-1",
                tenant_id=None,
                created_at=datetime.now(UTC),
                last_accessed=datetime.now(UTC),
                expires_at=datetime.now(UTC) + timedelta(hours=1),
                status=SessionStatus.ACTIVE,
                metadata={},
            )

            result = await backend.store_session(session)
            assert result is False  # Should return False on error


@pytest.mark.asyncio
class TestSessionManager:
    """Comprehensive tests for SessionManager."""

    @pytest.fixture
    def memory_backend(self):
        """Create a memory backend for testing."""
        return MemorySessionBackend()

    @pytest.fixture
    def session_manager(self, memory_backend):
        """Create a session manager with memory backend."""
        return SessionManager(
            backend=memory_backend,
            default_ttl=3600,
            max_sessions_per_user=3,
            cleanup_interval=300,
        )

    async def test_create_session_basic(self, session_manager):
        """Test basic session creation."""
        session = await session_manager.create_session(
            user_id="test-user",
            tenant_id="test-tenant",
            metadata={"ip": "192.168.1.1"},
        )

        assert session.session_id is not None
        assert session.user_id == "test-user"
        assert session.tenant_id == "test-tenant"
        assert session.metadata["ip"] == "192.168.1.1"
        assert session.status == SessionStatus.ACTIVE
        assert session.is_active() is True

    async def test_create_session_with_custom_ttl(self, session_manager):
        """Test session creation with custom TTL."""
        custom_ttl = 7200  # 2 hours

        session = await session_manager.create_session(
            user_id="test-user",
            ttl=custom_ttl,
        )

        expected_expiry = session.created_at + timedelta(seconds=custom_ttl)
        time_diff = abs((session.expires_at - expected_expiry).total_seconds())
        assert time_diff < 1  # Allow 1 second tolerance

    async def test_session_limit_enforcement(self, session_manager):
        """Test max sessions per user enforcement."""
        # Create max sessions
        created_sessions = []
        for i in range(3):  # max_sessions_per_user = 3
            session = await session_manager.create_session(
                user_id="limited-user",
                metadata={"index": i},
            )
            created_sessions.append(session)

        # Verify all 3 sessions exist
        user_sessions = await session_manager.get_user_sessions("limited-user")
        assert len(user_sessions) == 3

        # Create one more session (should remove oldest)
        new_session = await session_manager.create_session(
            user_id="limited-user",
            metadata={"index": 3},
        )

        # Verify still only 3 sessions
        user_sessions = await session_manager.get_user_sessions("limited-user")
        assert len(user_sessions) == 3

        # Verify newest session is included
        session_ids = {s.session_id for s in user_sessions}
        assert new_session.session_id in session_ids

        # Verify oldest session was removed
        assert created_sessions[0].session_id not in session_ids

    async def test_get_session_updates_last_accessed(self, session_manager):
        """Test that getting a session updates last accessed time."""
        session = await session_manager.create_session(user_id="test-user")
        original_accessed = session.last_accessed

        # Wait a bit and get session
        await asyncio.sleep(0.1)
        retrieved = await session_manager.get_session(session.session_id)

        assert retrieved is not None
        assert retrieved.last_accessed > original_accessed

    async def test_get_invalid_session(self, session_manager):
        """Test getting non-existent session."""
        result = await session_manager.get_session("non-existent-id")
        assert result is None

    async def test_invalidate_session(self, session_manager):
        """Test session invalidation."""
        session = await session_manager.create_session(user_id="test-user")
        assert session.status == SessionStatus.ACTIVE

        # Invalidate session
        result = await session_manager.invalidate_session(session.session_id)
        assert result is True

        # Get invalidated session
        retrieved = await session_manager.backend.get_session(session.session_id)
        assert retrieved is not None
        assert retrieved.status == SessionStatus.INVALIDATED
        assert retrieved.is_active() is False

    async def test_delete_session(self, session_manager):
        """Test complete session deletion."""
        session = await session_manager.create_session(user_id="test-user")

        # Delete session
        result = await session_manager.delete_session(session.session_id)
        assert result is True

        # Verify session is gone
        retrieved = await session_manager.get_session(session.session_id)
        assert retrieved is None

    async def test_invalidate_user_sessions(self, session_manager):
        """Test invalidating all sessions for a user."""
        # Create multiple sessions
        sessions = []
        for i in range(3):
            session = await session_manager.create_session(
                user_id="multi-user",
                metadata={"index": i},
            )
            sessions.append(session)

        # Invalidate all sessions except the second one
        count = await session_manager.invalidate_user_sessions(
            "multi-user",
            exclude_session=sessions[1].session_id,
        )
        assert count == 2  # Should invalidate 2 sessions

        # Verify excluded session is still active
        excluded = await session_manager.get_session(sessions[1].session_id)
        assert excluded is not None
        assert excluded.status == SessionStatus.ACTIVE

        # Verify other sessions are invalidated
        for i in [0, 2]:
            sess = await session_manager.backend.get_session(sessions[i].session_id)
            assert sess is not None
            assert sess.status == SessionStatus.INVALIDATED

    async def test_extend_session(self, session_manager):
        """Test extending session expiration."""
        session = await session_manager.create_session(user_id="test-user")
        original_expiry = session.expires_at

        # Extend by 1 hour
        result = await session_manager.extend_session(session.session_id, 3600)
        assert result is True

        # Verify expiration was extended
        extended = await session_manager.get_session(session.session_id)
        assert extended is not None
        time_diff = (extended.expires_at - original_expiry).total_seconds()
        assert abs(time_diff - 3600) < 1  # Allow 1 second tolerance

    async def test_extend_invalid_session(self, session_manager):
        """Test extending non-existent or inactive session."""
        # Non-existent session
        result = await session_manager.extend_session("non-existent", 3600)
        assert result is False

        # Invalidated session
        session = await session_manager.create_session(user_id="test-user")
        await session_manager.invalidate_session(session.session_id)
        result = await session_manager.extend_session(session.session_id, 3600)
        assert result is False

    async def test_get_user_sessions(self, session_manager):
        """Test retrieving all active sessions for a user."""
        # Create mix of active and inactive sessions
        active1 = await session_manager.create_session(user_id="test-user")
        active2 = await session_manager.create_session(user_id="test-user")
        inactive = await session_manager.create_session(user_id="test-user")

        # Invalidate one session
        await session_manager.invalidate_session(inactive.session_id)

        # Get user sessions
        sessions = await session_manager.get_user_sessions("test-user")
        assert len(sessions) == 2  # Only active sessions

        session_ids = {s.session_id for s in sessions}
        assert active1.session_id in session_ids
        assert active2.session_id in session_ids
        assert inactive.session_id not in session_ids

    async def test_session_manager_with_config(self):
        """Test SessionManager with SessionConfig."""
        config = settings.Session.model_copy(update={
            session_lifetime_seconds=7200,
            max_sessions_per_user=5,
        })

        manager = SessionManager(
            backend=MemorySessionBackend(),
            config=config,
        )

        # Verify config was applied
        assert manager.default_ttl == 7200
        assert manager.max_sessions_per_user == 5

    async def test_concurrent_session_creation(self, session_manager):
        """Test concurrent session creation respects limits."""
        user_id = "concurrent-user"

        # Create sessions concurrently
        async def create_session(index):
            return await session_manager.create_session(
                user_id=user_id,
                metadata={"index": index},
            )

        # Create 5 sessions concurrently (limit is 3)
        tasks = [create_session(i) for i in range(5)]
        await asyncio.gather(*tasks)

        # Verify only 3 sessions exist
        sessions = await session_manager.get_user_sessions(user_id)
        assert len(sessions) == 3

    async def test_periodic_cleanup(self, session_manager):
        """Test periodic cleanup triggers."""
        # Mock the cleanup method
        with patch.object(session_manager.backend, "cleanup_expired_sessions") as mock_cleanup:
            mock_cleanup.return_value = 2

            # Set last cleanup to past
            session_manager._last_cleanup = time.time() - 400  # Past cleanup interval

            # Getting a session should trigger cleanup
            await session_manager.get_session("any-id")

            # Verify cleanup was called
            mock_cleanup.assert_called_once()

    async def test_session_manager_error_handling(self):
        """Test error handling in session manager."""
        backend = MemorySessionBackend()
        manager = SessionManager(backend=backend)

        # Mock store failure
        with patch.object(backend, "store_session", return_value=False):
            with pytest.raises(RuntimeError, match="Failed to store session"):
                await manager.create_session(user_id="test-user")


@pytest.mark.asyncio
class TestIntegrationScenarios:
    """Integration test scenarios for session management."""

    async def test_full_session_lifecycle(self):
        """Test complete session lifecycle."""
        manager = SessionManager(
            backend=MemorySessionBackend(),
            default_ttl=3600,
            max_sessions_per_user=5,
        )

        # 1. Create session
        session = await manager.create_session(
            user_id="lifecycle-user",
            tenant_id="tenant-1",
            metadata={"device": "mobile"},
        )
        assert session.is_active()

        # 2. Retrieve and update
        retrieved = await manager.get_session(session.session_id)
        assert retrieved is not None
        assert retrieved.last_accessed > session.last_accessed

        # 3. Extend session
        await manager.extend_session(session.session_id, 1800)

        # 4. Get user sessions
        user_sessions = await manager.get_user_sessions("lifecycle-user")
        assert len(user_sessions) == 1

        # 5. Invalidate session
        await manager.invalidate_session(session.session_id)

        # 6. Verify invalidated
        invalidated = await manager.backend.get_session(session.session_id)
        assert invalidated.status == SessionStatus.INVALIDATED

        # 7. Delete session
        await manager.delete_session(session.session_id)

        # 8. Verify deleted
        deleted = await manager.get_session(session.session_id)
        assert deleted is None

    async def test_multi_user_session_management(self):
        """Test managing sessions for multiple users."""
        manager = SessionManager(
            backend=MemorySessionBackend(),
            max_sessions_per_user=2,
        )

        users = ["alice", "bob", "charlie"]
        all_sessions = {}

        # Create sessions for each user
        for user in users:
            sessions = []
            for i in range(3):  # Create 3, but limit is 2
                session = await manager.create_session(
                    user_id=user,
                    metadata={"session_num": i},
                )
                sessions.append(session)
                await asyncio.sleep(0.01)  # Small delay to ensure different timestamps

            all_sessions[user] = sessions

        # Verify each user has only 2 sessions (due to limit)
        for user in users:
            user_sessions = await manager.get_user_sessions(user)
            assert len(user_sessions) == 2

            # Verify newest sessions are kept
            session_ids = {s.session_id for s in user_sessions}
            assert all_sessions[user][1].session_id in session_ids
            assert all_sessions[user][2].session_id in session_ids
            assert all_sessions[user][0].session_id not in session_ids  # Oldest removed

        # Invalidate all bob's sessions
        count = await manager.invalidate_user_sessions("bob")
        assert count == 2

        # Verify bob has no active sessions
        bob_sessions = await manager.get_user_sessions("bob")
        assert len(bob_sessions) == 0

        # Verify other users unaffected
        alice_sessions = await manager.get_user_sessions("alice")
        assert len(alice_sessions) == 2

    async def test_redis_backend_integration(self):
        """Test integration with Redis backend."""
        backend = RedisSessionBackend(key_prefix="test:")
        mock_client = mock_redis_with_data({})

        with patch.object(backend, "_redis", mock_client):
            manager = SessionManager(backend=backend)

            # Create session
            session = await manager.create_session(
                user_id="redis-user",
                metadata={"test": "redis-integration"},
            )

            # Mock successful pipeline execution
            mock_client.pipeline().execute.return_value = [True, True, True]

            # Verify session can be retrieved
            mock_client.get.return_value = json.dumps(session.to_dict())
            retrieved = await manager.get_session(session.session_id)
            assert retrieved is not None
            assert retrieved.metadata["test"] == "redis-integration"