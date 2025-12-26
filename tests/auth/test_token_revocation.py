"""Tests for JWT token revocation and session management fixes."""

import json
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials

from dotmac.platform.auth.core import JWTService, SessionManager, get_current_user

pytestmark = pytest.mark.integration


class TestJWTRevocation:
    """Test JWT token revocation functionality."""

    @pytest.fixture
    def jwt_service(self):
        """Create JWT service with mocked Redis."""
        return JWTService(secret="test-secret", redis_url="redis://localhost:6379")

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        redis_mock = AsyncMock()
        return redis_mock

    @pytest.mark.asyncio
    async def test_revoke_token_success(self, jwt_service, mock_redis):
        """Test successful token revocation."""
        # Create a token
        token = jwt_service.create_access_token("user123")

        with patch.object(jwt_service, "_get_redis", return_value=mock_redis):
            # Mock Redis operations
            mock_redis.setex = AsyncMock(return_value=True)
            mock_redis.set = AsyncMock(return_value=True)

            result = await jwt_service.revoke_token(token)

            assert result is True
            # Verify Redis was called to blacklist the token
            mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_revoke_token_no_redis(self, jwt_service):
        """Test token revocation when Redis is not available."""
        with patch.object(jwt_service, "_get_redis", return_value=None):
            result = await jwt_service.revoke_token("some-token")
            assert result is False

    @pytest.mark.asyncio
    async def test_revoke_token_invalid_token(self, jwt_service, mock_redis):
        """Test revoking invalid token."""
        with patch.object(jwt_service, "_get_redis", return_value=mock_redis):
            result = await jwt_service.revoke_token("invalid-token")
            assert result is False

    @pytest.mark.asyncio
    async def test_is_token_revoked(self, jwt_service, mock_redis):
        """Test checking if token is revoked."""
        with patch.object(jwt_service, "_get_redis", return_value=mock_redis):
            mock_redis.exists = AsyncMock(return_value=True)

            is_revoked = await jwt_service.is_token_revoked("test-jti")

            assert is_revoked is True
            mock_redis.exists.assert_called_once_with("blacklist:test-jti")

    @pytest.mark.asyncio
    async def test_verify_token_async_with_revoked_token(self, jwt_service, mock_redis):
        """Test token verification fails for revoked token."""
        # Create a token
        token = jwt_service.create_access_token("user123")

        with patch.object(jwt_service, "_get_redis", return_value=mock_redis):
            # Mock token as revoked
            with patch.object(jwt_service, "is_token_revoked", return_value=True):
                with pytest.raises(Exception):  # Should raise HTTPException  # noqa: B017
                    await jwt_service.verify_token_async(token)

    @pytest.mark.asyncio
    async def test_verify_token_async_success(self, jwt_service, mock_redis):
        """Test successful async token verification."""
        token = jwt_service.create_access_token("user123")

        with patch.object(jwt_service, "_get_redis", return_value=mock_redis):
            with patch.object(jwt_service, "is_token_revoked", return_value=False):
                claims = await jwt_service.verify_token_async(token)

                assert claims["sub"] == "user123"
                assert claims["type"] == "access"

    def test_is_token_revoked_sync(self, jwt_service):
        """Test synchronous token revocation check."""
        with patch("dotmac.platform.core.caching.get_redis") as mock_get_redis:
            mock_redis = MagicMock()
            mock_get_redis.return_value = mock_redis
            mock_redis.exists.return_value = True

            is_revoked = jwt_service.is_token_revoked_sync("test-jti")

            assert is_revoked is True
            mock_redis.exists.assert_called_once_with("blacklist:test-jti")

    def test_is_token_revoked_sync_no_redis(self, jwt_service):
        """Test sync revocation check when Redis is not available."""
        with patch("dotmac.platform.core.caching.get_redis") as mock_get_redis:
            mock_get_redis.return_value = None

            is_revoked = jwt_service.is_token_revoked_sync("test-jti")

            assert is_revoked is False

    def test_is_token_revoked_sync_error(self, jwt_service):
        """Test sync revocation check with Redis error."""
        with patch("dotmac.platform.core.caching.get_redis") as mock_get_redis:
            mock_redis = MagicMock()
            mock_get_redis.return_value = mock_redis
            mock_redis.exists.side_effect = Exception("Redis connection error")

            is_revoked = jwt_service.is_token_revoked_sync("test-jti")

            assert is_revoked is False

    def test_verify_token_sync_with_revoked_token(self, jwt_service):
        """Test sync token verification fails for revoked token."""
        # Create a token
        token = jwt_service.create_access_token("user123")

        with patch.object(jwt_service, "is_token_revoked_sync", return_value=True):
            with pytest.raises(Exception):  # Should raise HTTPException  # noqa: B017
                jwt_service.verify_token(token)

    def test_verify_token_sync_success(self, jwt_service):
        """Test successful sync token verification with blacklist check."""
        token = jwt_service.create_access_token("user123")

        with patch.object(jwt_service, "is_token_revoked_sync", return_value=False):
            claims = jwt_service.verify_token(token)

            assert claims["sub"] == "user123"
            assert claims["type"] == "access"


class TestAuthenticationDependencyFix:
    """Test that get_current_user properly uses async token verification."""

    @pytest.fixture
    def jwt_service_mock(self):
        """Mock JWT service."""
        mock_service = MagicMock()
        mock_service.verify_token_async = AsyncMock()
        return mock_service

    @pytest.fixture
    def api_key_service_mock(self):
        """Mock API key service."""
        mock_service = AsyncMock()
        return mock_service

    @pytest.mark.asyncio
    async def test_get_current_user_bearer_token_revoked(
        self, jwt_service_mock, api_key_service_mock
    ):
        """Test get_current_user rejects revoked bearer token."""
        # Mock revoked token (async verification fails)
        jwt_service_mock.verify_token_async.side_effect = HTTPException(
            status_code=401, detail="Token has been revoked"
        )

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="revoked-token")
        mock_request = Mock(spec=Request)
        mock_request.cookies = {}

        with patch("dotmac.platform.auth.core.jwt_service", jwt_service_mock):
            with patch("dotmac.platform.auth.core.api_key_service", api_key_service_mock):
                with pytest.raises(HTTPException) as exc_info:
                    await get_current_user(
                        request=mock_request, token=None, api_key=None, credentials=credentials
                    )

                assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_oauth_token_revoked(
        self, jwt_service_mock, api_key_service_mock
    ):
        """Test get_current_user rejects revoked OAuth token."""
        # Mock revoked token
        jwt_service_mock.verify_token_async.side_effect = HTTPException(
            status_code=401, detail="Token has been revoked"
        )

        mock_request = Mock(spec=Request)
        mock_request.cookies = {}

        with patch("dotmac.platform.auth.core.jwt_service", jwt_service_mock):
            with patch("dotmac.platform.auth.core.api_key_service", api_key_service_mock):
                with pytest.raises(HTTPException) as exc_info:
                    await get_current_user(
                        request=mock_request,
                        token="revoked-oauth-token",
                        api_key=None,
                        credentials=None,
                    )

                assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_valid_token_success(
        self, jwt_service_mock, api_key_service_mock
    ):
        """Test get_current_user works with valid token."""
        # Mock valid token
        jwt_service_mock.verify_token_async.return_value = {
            "sub": "user123",
            "type": "access",
            "exp": (datetime.now(UTC) + timedelta(hours=1)).timestamp(),
            "iat": datetime.now(UTC).timestamp(),
        }

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid-token")
        mock_request = Mock(spec=Request)
        mock_request.cookies = {}

        with patch("dotmac.platform.auth.core.jwt_service", jwt_service_mock):
            with patch("dotmac.platform.auth.core.api_key_service", api_key_service_mock):
                user_info = await get_current_user(
                    request=mock_request, token=None, api_key=None, credentials=credentials
                )

                assert user_info.user_id == "user123"
                # Verify async version called with token and token type
                from dotmac.platform.auth.core import TokenType

                jwt_service_mock.verify_token_async.assert_called_once_with(
                    "valid-token", TokenType.ACCESS
                )

    @pytest.mark.asyncio
    async def test_get_current_user_uses_async_verification(
        self, jwt_service_mock, api_key_service_mock
    ):
        """Test that get_current_user calls the async version that checks blacklist."""
        jwt_service_mock.verify_token_async.return_value = {
            "sub": "test_user",
            "type": "access",
            "exp": (datetime.now(UTC) + timedelta(hours=1)).timestamp(),
            "iat": datetime.now(UTC).timestamp(),
        }

        mock_request = Mock(spec=Request)
        mock_request.cookies = {}

        with patch("dotmac.platform.auth.core.jwt_service", jwt_service_mock):
            with patch("dotmac.platform.auth.core.api_key_service", api_key_service_mock):
                await get_current_user(
                    request=mock_request, token="test-token", api_key=None, credentials=None
                )

                # Verify async version was called (which includes blacklist check)
                from dotmac.platform.auth.core import TokenType

                jwt_service_mock.verify_token_async.assert_called_once_with(
                    "test-token", TokenType.ACCESS
                )
                # Verify sync version was NOT called
                assert (
                    not hasattr(jwt_service_mock, "verify_token")
                    or not jwt_service_mock.verify_token.called
                )


class TestSessionManagerEnhancements:
    """Test enhanced session management functionality."""

    @pytest.fixture
    def session_manager(self):
        """Create session manager."""
        return SessionManager(redis_url="redis://localhost:6379")

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        redis_mock = AsyncMock()
        return redis_mock

    @pytest.mark.asyncio
    async def test_create_session_with_user_tracking(self, session_manager, mock_redis):
        """Test session creation with user session tracking."""
        with patch.object(session_manager, "_get_redis", return_value=mock_redis):
            mock_redis.setex = AsyncMock()
            mock_redis.sadd = AsyncMock()
            mock_redis.expire = AsyncMock()

            session_id = await session_manager.create_session(
                user_id="user123", data={"test": "data"}, ttl=3600
            )

            assert session_id is not None
            # Verify session was stored
            mock_redis.setex.assert_called_once()
            # Verify user session tracking
            mock_redis.sadd.assert_called_once()
            mock_redis.expire.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_user_sessions(self, session_manager, mock_redis):
        """Test deleting all sessions for a user."""
        with patch.object(session_manager, "_get_redis", return_value=mock_redis):
            # Mock existing sessions
            mock_redis.smembers = AsyncMock(return_value=["session1", "session2", "session3"])
            mock_redis.delete = AsyncMock(return_value=1)

            deleted_count = await session_manager.delete_user_sessions("user123")

            assert deleted_count == 3
            # Verify all sessions were deleted
            assert mock_redis.delete.call_count == 4  # 3 sessions + 1 user sessions set

    @pytest.mark.asyncio
    async def test_delete_session_with_user_cleanup(self, session_manager, mock_redis):
        """Test session deletion with user session set cleanup."""
        session_data = {
            "user_id": "user123",
            "created_at": datetime.now(UTC).isoformat(),
            "data": {"test": "data"},
        }

        with patch.object(session_manager, "_get_redis", return_value=mock_redis):
            mock_redis.get = AsyncMock(return_value=json.dumps(session_data))
            mock_redis.srem = AsyncMock()
            mock_redis.delete = AsyncMock(return_value=1)

            result = await session_manager.delete_session("session123")

            assert result is True
            # Verify session was removed from user sessions set
            mock_redis.srem.assert_called_once_with("user_sessions:user123", "session123")


class TestAuthRouterFixes:
    """Test auth router fixes for logout and refresh token."""

    @pytest.fixture
    def test_client(self):
        """Create test client for the auth router."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from dotmac.platform.auth.router import auth_router

        app = FastAPI()
        app.include_router(auth_router)

        return TestClient(app)

    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        session = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.close = AsyncMock()
        return session

    @pytest.fixture
    def mock_jwt_service(self):
        """Create mock JWT service."""
        service = MagicMock()
        service.verify_token.return_value = {"sub": "user123", "jti": "test-jti", "type": "refresh"}
        service.revoke_token = AsyncMock(return_value=True)
        service.create_access_token.return_value = "new-access-token"
        service.create_refresh_token.return_value = "new-refresh-token"
        return service

    @pytest.fixture
    def mock_session_manager(self):
        """Create mock session manager."""
        manager = AsyncMock()
        manager.delete_user_sessions = AsyncMock(return_value=2)
        return manager

    def test_logout_with_proper_cleanup(self, mock_jwt_service, mock_session_manager, test_client):
        """Test logout properly cleans up tokens and sessions."""

        # Patch module-level objects
        with patch("dotmac.platform.auth.router.jwt_service", mock_jwt_service):
            with patch("dotmac.platform.auth.router.session_manager", mock_session_manager):
                response = test_client.post(
                    "/auth/logout", headers={"Authorization": "Bearer test-token"}
                )

                assert response.status_code == 200
                result = response.json()
                assert result["message"] == "Logged out successfully"
                assert result["sessions_deleted"] == 2

                # Verify token was revoked
                mock_jwt_service.revoke_token.assert_called_once_with("test-token")
                # Verify sessions were deleted
                mock_session_manager.delete_user_sessions.assert_called_once_with("user123")

    def test_refresh_token_revokes_old_token(self, mock_jwt_service, mock_session, test_client):
        """Test refresh token flow revokes old refresh token."""
        from fastapi import FastAPI

        from dotmac.platform.db import get_session_dependency

        app: FastAPI = test_client.app

        # Mock user
        mock_user = MagicMock()
        mock_user.id = "user123"
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.roles = ["user"]
        mock_user.tenant_id = "tenant123"
        mock_user.is_active = True

        # Create mock dependencies
        async def mock_get_session():
            yield mock_session

        mock_user_service = AsyncMock()
        mock_user_service.get_user_by_id = AsyncMock(return_value=mock_user)

        # Create mock UserService class that returns our mock instance
        class MockUserServiceClass:
            def __init__(self, session):
                pass

            def __new__(cls, session):
                return mock_user_service

        # Set up dependency overrides
        app.dependency_overrides[get_session_dependency] = mock_get_session

        # Patch module-level objects and UserService class
        with patch("dotmac.platform.auth.router.jwt_service", mock_jwt_service):
            with patch("dotmac.platform.auth.router.UserService", MockUserServiceClass):
                try:
                    response = test_client.post(
                        "/auth/refresh", json={"refresh_token": "old-refresh-token"}
                    )

                    assert response.status_code == 200
                    result = response.json()
                    assert result["access_token"] == "new-access-token"
                    assert result["refresh_token"] == "new-refresh-token"

                    # Verify old refresh token was revoked
                    mock_jwt_service.revoke_token.assert_called_once_with("old-refresh-token")
                finally:
                    app.dependency_overrides.clear()


class TestIntegrationTokenRevocation:
    """Integration tests for token revocation flow."""

    @pytest.mark.asyncio
    async def test_full_token_lifecycle(self):
        """Test complete token lifecycle: create, use, revoke, verify."""
        # This would be an integration test with actual Redis
        # For now, we'll test the components work together correctly
        jwt_service = JWTService(secret="test-secret")

        # Create token
        token = jwt_service.create_access_token("user123")

        # Verify token works
        claims = jwt_service.verify_token(token)
        assert claims["sub"] == "user123"

        # Mock Redis for revocation test
        with patch.object(jwt_service, "_get_redis") as mock_get_redis:
            mock_redis = AsyncMock()
            mock_get_redis.return_value = mock_redis
            mock_redis.setex = AsyncMock()

            # Revoke token
            revoked = await jwt_service.revoke_token(token)
            assert revoked is True

            # Verify revocation was stored
            mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_and_token_coordination(self):
        """Test that session management and token revocation work together."""
        session_manager = SessionManager()
        jwt_service = JWTService(secret="test-secret")

        with patch.object(session_manager, "_get_redis") as mock_session_redis:
            with patch.object(jwt_service, "_get_redis") as mock_jwt_redis:
                # Setup mocks
                mock_session_client = AsyncMock()
                mock_jwt_client = AsyncMock()
                mock_session_redis.return_value = mock_session_client
                mock_jwt_redis.return_value = mock_jwt_client

                # Mock session operations
                mock_session_client.setex = AsyncMock()
                mock_session_client.sadd = AsyncMock()
                mock_session_client.expire = AsyncMock()
                mock_session_client.smembers = AsyncMock(return_value=["session1", "session2"])
                mock_session_client.delete = AsyncMock(return_value=1)

                # Mock token operations
                mock_jwt_client.setex = AsyncMock()

                # Create session
                session_id = await session_manager.create_session("user123", {"test": "data"})
                assert session_id is not None

                # Create and revoke token
                token = jwt_service.create_access_token("user123")
                revoked = await jwt_service.revoke_token(token)
                assert revoked is True

                # Delete user sessions
                deleted = await session_manager.delete_user_sessions("user123")
                assert deleted == 2

                # Verify all operations were called
                mock_session_client.setex.assert_called()
                mock_jwt_client.setex.assert_called()
                assert mock_session_client.delete.call_count == 3  # 2 sessions + 1 set


class TestSessionEnforcement:
    """Test that tokens are rejected when their session is deleted."""

    @pytest.fixture
    def jwt_service(self):
        """Create JWT service for testing."""
        return JWTService(secret="test-secret", redis_url="redis://localhost:6379")

    @pytest.fixture
    def session_manager(self):
        """Create session manager for testing."""
        return SessionManager(redis_url="redis://localhost:6379", fallback_enabled=True)

    @pytest.mark.asyncio
    async def test_token_rejected_when_session_deleted(self, jwt_service, session_manager):
        """Test that access tokens fail if their session is missing."""
        from dotmac.platform.auth.core import _ensure_session_active

        # Create a token with session_id claim
        session_id = "test-session-123"
        token = jwt_service.create_access_token(
            "user123",
            additional_claims={"session_id": session_id},
        )
        claims = jwt_service.verify_token(token)

        # Mock session manager to return None (session deleted)
        with patch("dotmac.platform.auth.core.session_manager") as mock_sm:
            mock_sm.get_session = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                await _ensure_session_active(claims)

            assert exc_info.value.status_code == 401
            assert "Session has been revoked" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_token_rejected_when_session_user_mismatch(self, jwt_service):
        """Test that tokens fail if session user_id doesn't match token subject."""
        from dotmac.platform.auth.core import _ensure_session_active

        session_id = "test-session-456"
        claims = {
            "sub": "user123",
            "session_id": session_id,
        }

        # Mock session with different user_id
        with patch("dotmac.platform.auth.core.session_manager") as mock_sm:
            mock_sm.get_session = AsyncMock(
                return_value={"user_id": "different_user", "session_id": session_id}
            )

            with pytest.raises(HTTPException) as exc_info:
                await _ensure_session_active(claims)

            assert exc_info.value.status_code == 401
            assert "Session has been revoked" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_token_accepted_when_session_valid(self, jwt_service):
        """Test that tokens work when session exists and matches."""
        from dotmac.platform.auth.core import _ensure_session_active

        session_id = "test-session-789"
        user_id = "user123"
        claims = {
            "sub": user_id,
            "session_id": session_id,
        }

        # Mock valid session
        with patch("dotmac.platform.auth.core.session_manager") as mock_sm:
            mock_sm.get_session = AsyncMock(
                return_value={"user_id": user_id, "session_id": session_id}
            )

            # Should not raise
            await _ensure_session_active(claims)

    @pytest.mark.asyncio
    async def test_token_without_session_id_passes(self, jwt_service):
        """Test that tokens without session_id claim are not rejected."""
        from dotmac.platform.auth.core import _ensure_session_active

        claims = {"sub": "user123"}  # No session_id

        # Should not raise and should not call session_manager
        with patch("dotmac.platform.auth.core.session_manager") as mock_sm:
            await _ensure_session_active(claims)
            mock_sm.get_session.assert_not_called()


class TestUserWideRevocation:
    """Test user-wide token revocation using the revocation marker."""

    @pytest.fixture
    def jwt_service(self):
        """Create JWT service for testing."""
        return JWTService(secret="test-secret", redis_url="redis://localhost:6379")

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_revoke_user_tokens_sets_marker(self, jwt_service, mock_redis):
        """Test that revoke_user_tokens sets the user_revoked marker in Redis."""
        user_id = "user123"

        with patch.object(jwt_service, "_get_redis", return_value=mock_redis):
            mock_redis.setex = AsyncMock(return_value=True)

            result = await jwt_service.revoke_user_tokens(user_id)

            assert result == 1
            # Verify Redis setex was called with correct key
            mock_redis.setex.assert_called_once()
            call_args = mock_redis.setex.call_args
            assert call_args[0][0] == f"user_revoked:{user_id}"
            # TTL should be refresh token expiry (7 days in seconds)
            assert call_args[0][1] == 7 * 24 * 60 * 60

    @pytest.mark.asyncio
    async def test_old_token_rejected_after_user_revocation(self, jwt_service, mock_redis):
        """Test that tokens issued before revocation are rejected."""
        import time

        user_id = "user123"

        # Create token with iat in the past
        old_iat = int(time.time()) - 100  # 100 seconds ago
        token = jwt_service.create_access_token(user_id, additional_claims={"iat": old_iat})

        # Mock revocation that happened after the token was issued
        revoked_at = int(time.time()) - 50  # 50 seconds ago (after token creation)

        with patch.object(jwt_service, "_get_redis", return_value=mock_redis):
            with patch.object(jwt_service, "is_token_revoked", return_value=False):
                mock_redis.get = AsyncMock(return_value=str(revoked_at))

                with pytest.raises(HTTPException) as exc_info:
                    await jwt_service.verify_token_async(token)

                assert exc_info.value.status_code == 401
                assert "revoked" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_new_token_works_after_user_revocation(self, jwt_service, mock_redis):
        """Test that tokens issued after revocation are still valid."""
        import time

        user_id = "user123"

        # Revocation happened 100 seconds ago
        revoked_at = int(time.time()) - 100

        # Create a new token (iat will be now, after revocation)
        token = jwt_service.create_access_token(user_id)

        with patch.object(jwt_service, "_get_redis", return_value=mock_redis):
            with patch.object(jwt_service, "is_token_revoked", return_value=False):
                mock_redis.get = AsyncMock(return_value=str(revoked_at))

                # Should not raise - token was issued after revocation
                claims = await jwt_service.verify_token_async(token)
                assert claims["sub"] == user_id

    @pytest.mark.asyncio
    async def test_no_revocation_marker_allows_token(self, jwt_service, mock_redis):
        """Test that tokens work when no user revocation marker exists."""
        user_id = "user123"
        token = jwt_service.create_access_token(user_id)

        with patch.object(jwt_service, "_get_redis", return_value=mock_redis):
            with patch.object(jwt_service, "is_token_revoked", return_value=False):
                # No revocation marker
                mock_redis.get = AsyncMock(return_value=None)

                claims = await jwt_service.verify_token_async(token)
                assert claims["sub"] == user_id

    def test_is_token_revoked_by_user_with_old_iat(self, jwt_service):
        """Test _is_token_revoked_by_user returns True for old tokens."""
        import time

        revoked_at = int(time.time())
        claims = {"iat": revoked_at - 100}  # Token issued 100s before revocation

        result = jwt_service._is_token_revoked_by_user(claims, revoked_at)
        assert result is True

    def test_is_token_revoked_by_user_with_new_iat(self, jwt_service):
        """Test _is_token_revoked_by_user returns False for new tokens."""
        import time

        revoked_at = int(time.time()) - 100  # Revoked 100s ago
        claims = {"iat": int(time.time())}  # Token issued now

        result = jwt_service._is_token_revoked_by_user(claims, revoked_at)
        assert result is False

    def test_is_token_revoked_by_user_with_equal_iat(self, jwt_service):
        """Test _is_token_revoked_by_user returns True when iat equals revoked_at."""
        import time

        revoked_at = int(time.time())
        claims = {"iat": revoked_at}  # Same timestamp

        # Edge case: token issued at exact revocation time should be revoked
        result = jwt_service._is_token_revoked_by_user(claims, revoked_at)
        assert result is True

    def test_is_token_revoked_by_user_with_missing_iat(self, jwt_service):
        """Test _is_token_revoked_by_user returns True when iat is missing."""
        import time

        revoked_at = int(time.time())
        claims = {}  # No iat claim

        # Missing iat should be treated as revoked (fail-safe)
        result = jwt_service._is_token_revoked_by_user(claims, revoked_at)
        assert result is True

    def test_normalize_timestamp_with_int(self, jwt_service):
        """Test _normalize_timestamp handles int values."""
        assert jwt_service._normalize_timestamp(12345) == 12345

    def test_normalize_timestamp_with_float(self, jwt_service):
        """Test _normalize_timestamp handles float values."""
        assert jwt_service._normalize_timestamp(12345.6) == 12345

    def test_normalize_timestamp_with_string(self, jwt_service):
        """Test _normalize_timestamp handles string digit values."""
        assert jwt_service._normalize_timestamp("12345") == 12345
        assert jwt_service._normalize_timestamp(" 12345 ") == 12345

    def test_normalize_timestamp_with_datetime(self, jwt_service):
        """Test _normalize_timestamp handles datetime values."""
        dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        result = jwt_service._normalize_timestamp(dt)
        assert result == int(dt.timestamp())

    def test_normalize_timestamp_with_invalid(self, jwt_service):
        """Test _normalize_timestamp returns None for invalid values."""
        assert jwt_service._normalize_timestamp("not-a-number") is None
        assert jwt_service._normalize_timestamp(None) is None
        assert jwt_service._normalize_timestamp({}) is None


class TestLogoutWithoutAccessToken:
    """Test logout works when access token is missing or invalid."""

    @pytest.fixture
    def test_client(self):
        """Create test client for the auth router."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from dotmac.platform.auth.router import auth_router

        app = FastAPI()
        app.include_router(auth_router)
        return TestClient(app)

    @pytest.fixture
    def mock_jwt_service(self):
        """Create mock JWT service."""
        service = MagicMock()
        service.revoke_token = AsyncMock(return_value=True)
        service.revoke_user_tokens = AsyncMock(return_value=1)
        return service

    @pytest.fixture
    def mock_session_manager(self):
        """Create mock session manager."""
        manager = AsyncMock()
        manager.delete_user_sessions = AsyncMock(return_value=2)
        return manager

    def test_logout_revokes_refresh_token_without_access_token(
        self, test_client, mock_jwt_service, mock_session_manager
    ):
        """Test logout revokes refresh token even when no access token provided."""
        with patch("dotmac.platform.auth.router.jwt_service", mock_jwt_service):
            with patch("dotmac.platform.auth.router.session_manager", mock_session_manager):
                # Set refresh token cookie but no access token
                test_client.cookies.set("refresh_token", "test-refresh-token")

                response = test_client.post("/auth/logout")

                assert response.status_code == 200
                # Verify refresh token was revoked
                mock_jwt_service.revoke_token.assert_called_once_with("test-refresh-token")

    def test_logout_with_invalid_access_token_still_revokes_refresh(
        self, test_client, mock_jwt_service, mock_session_manager
    ):
        """Test logout handles invalid access token and still revokes refresh token."""
        # Make verify_token raise an exception (invalid token)
        mock_jwt_service.verify_token.side_effect = Exception("Invalid token")

        with patch("dotmac.platform.auth.router.jwt_service", mock_jwt_service):
            with patch("dotmac.platform.auth.router.session_manager", mock_session_manager):
                test_client.cookies.set("access_token", "invalid-access-token")
                test_client.cookies.set("refresh_token", "valid-refresh-token")

                response = test_client.post("/auth/logout")

                assert response.status_code == 200
                assert response.json()["message"] == "Logout completed"

    def test_logout_clears_cookies_even_without_tokens(self, test_client):
        """Test logout clears cookies even when no tokens present."""
        response = test_client.post("/auth/logout")

        assert response.status_code == 200
        assert response.json()["message"] == "Logout completed"
        # Cookies should be cleared (set-cookie headers with max-age=0)


class TestRefreshTokenRevocationOnLogout:
    """Test that refresh tokens are unusable after logout."""

    @pytest.fixture
    def jwt_service(self):
        """Create real JWT service for integration testing."""
        return JWTService(secret="test-secret", redis_url="redis://localhost:6379")

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis for token operations."""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_refresh_token_rejected_after_user_revocation(self, jwt_service, mock_redis):
        """Test refresh token fails after revoke_user_tokens is called."""
        from dotmac.platform.auth.core import TokenType

        user_id = "user123"

        # Create refresh token
        refresh_token = jwt_service.create_refresh_token(user_id)

        # Simulate user logout which calls revoke_user_tokens
        with patch.object(jwt_service, "_get_redis", return_value=mock_redis):
            mock_redis.setex = AsyncMock(return_value=True)
            await jwt_service.revoke_user_tokens(user_id)

        # Now try to use the refresh token
        import time

        revoked_at = int(time.time())

        with patch.object(jwt_service, "_get_redis", return_value=mock_redis):
            with patch.object(jwt_service, "is_token_revoked", return_value=False):
                mock_redis.get = AsyncMock(return_value=str(revoked_at))

                with pytest.raises(HTTPException) as exc_info:
                    await jwt_service.verify_token_async(refresh_token, TokenType.REFRESH)

                assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_full_logout_flow_invalidates_all_tokens(self, jwt_service, mock_redis):
        """Test complete logout flow: access token, refresh token, and sessions all invalidated."""
        user_id = "user123"
        session_id = "session-abc"

        # Create both tokens with session binding
        access_token = jwt_service.create_access_token(
            user_id, additional_claims={"session_id": session_id}
        )
        refresh_token = jwt_service.create_refresh_token(
            user_id, additional_claims={"session_id": session_id}
        )

        # Simulate logout
        with patch.object(jwt_service, "_get_redis", return_value=mock_redis):
            mock_redis.setex = AsyncMock(return_value=True)

            # Revoke individual tokens
            await jwt_service.revoke_token(access_token)
            await jwt_service.revoke_token(refresh_token)

            # Revoke all user tokens (belt and suspenders)
            await jwt_service.revoke_user_tokens(user_id)

        # Verify both tokens would be rejected
        with patch.object(jwt_service, "_get_redis", return_value=mock_redis):
            # Mock JTI blacklist check - tokens are individually revoked
            mock_redis.exists = AsyncMock(return_value=True)

            with pytest.raises(HTTPException):
                await jwt_service.verify_token_async(access_token)

            with pytest.raises(HTTPException):
                await jwt_service.verify_token_async(refresh_token)
