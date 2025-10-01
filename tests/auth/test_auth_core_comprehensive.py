"""
Comprehensive tests for Auth Core module to improve coverage.

Tests token generation, session management, OAuth, API keys, and all helper methods.
"""

import json
import secrets
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from authlib.jose import JoseError, jwt
from fastapi import HTTPException

from dotmac.platform.auth.core import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_ALGORITHM,
    JWT_SECRET,
    OAUTH_CONFIGS,
    REDIS_URL,
    REFRESH_TOKEN_EXPIRE_DAYS,
    APIKeyService,
    JWTService,
    OAuthProvider,
    OAuthService,
    SessionManager,
    TokenData,
    TokenType,
    UserInfo,
    configure_auth,
    create_access_token,
    create_refresh_token,
    get_current_user,
    get_current_user_optional,
    hash_password,
    verify_password,
)


@pytest.fixture
def jwt_service():
    """Create JWT service instance."""
    return JWTService(secret="test-secret", algorithm="HS256")


@pytest.fixture
def session_manager():
    """Create session manager instance."""
    return SessionManager(redis_url="redis://localhost:6379")


@pytest.fixture
def api_key_service():
    """Create API key service instance."""
    return APIKeyService(redis_url="redis://localhost:6379")


@pytest.fixture
def oauth_service():
    """Create OAuth service instance."""
    return OAuthService(client_id="test-client", client_secret="test-secret")


class TestJWTService:
    """Test JWT service functionality."""

    def test_jwt_service_initialization(self):
        """Test JWT service initialization with defaults and custom values."""
        # Default initialization
        service = JWTService()
        assert service.secret == JWT_SECRET
        assert service.algorithm == JWT_ALGORITHM
        assert service.redis_url == REDIS_URL

        # Custom initialization
        service = JWTService(secret="custom", algorithm="RS256", redis_url="redis://custom:6379")
        assert service.secret == "custom"
        assert service.algorithm == "RS256"
        assert service.redis_url == "redis://custom:6379"
        assert service._redis is None

    def test_create_access_token(self, jwt_service):
        """Test access token creation."""
        token = jwt_service.create_access_token(
            subject="user123",
            additional_claims={"role": "admin", "tenant_id": "tenant456"},
            expire_minutes=30,
        )

        # Verify token
        claims = jwt.decode(token, jwt_service.secret)
        assert claims["sub"] == "user123"
        assert claims["type"] == TokenType.ACCESS.value
        assert claims["role"] == "admin"
        assert claims["tenant_id"] == "tenant456"
        assert "exp" in claims
        assert "iat" in claims
        assert "jti" in claims

    def test_create_refresh_token(self, jwt_service):
        """Test refresh token creation."""
        token = jwt_service.create_refresh_token(
            subject="user123", additional_claims={"session_id": "sess123"}
        )

        # Verify token
        claims = jwt.decode(token, jwt_service.secret)
        assert claims["sub"] == "user123"
        assert claims["type"] == TokenType.REFRESH.value
        assert claims["session_id"] == "sess123"
        assert "exp" in claims
        assert "iat" in claims
        assert "jti" in claims

    def test_verify_token_valid(self, jwt_service):
        """Test token verification with valid token."""
        token = jwt_service.create_access_token("user123")
        claims = jwt_service.verify_token(token)

        assert claims["sub"] == "user123"
        assert claims["type"] == TokenType.ACCESS.value

    def test_verify_token_invalid(self, jwt_service):
        """Test token verification with invalid token."""
        with pytest.raises(HTTPException) as exc_info:
            jwt_service.verify_token("invalid-token")

        assert exc_info.value.status_code == 401
        assert "Invalid token" in exc_info.value.detail

    def test_verify_token_expired(self, jwt_service):
        """Test token verification with expired token."""
        # Create expired token
        data = {"sub": "user123", "type": TokenType.ACCESS.value}
        expire = datetime.now(UTC) - timedelta(hours=1)
        to_encode = data.copy()
        to_encode.update({"exp": expire, "iat": datetime.now(UTC), "jti": "test-jti"})

        token = jwt.encode(jwt_service.header, to_encode, jwt_service.secret)
        token_str = token.decode("utf-8") if isinstance(token, bytes) else token

        with pytest.raises(HTTPException) as exc_info:
            jwt_service.verify_token(token_str)

        assert exc_info.value.status_code == 401

    @patch("dotmac.platform.auth.core.redis")
    def test_verify_token_revoked(self, mock_redis, jwt_service):
        """Test token verification with revoked token."""
        # Mock Redis to indicate token is revoked
        with patch.object(jwt_service, 'is_token_revoked_sync', return_value=True):
            token = jwt_service.create_access_token("user123")

            with pytest.raises(HTTPException) as exc_info:
                jwt_service.verify_token(token)

            assert exc_info.value.status_code == 401
            assert "Token has been revoked" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_revoke_token(self, jwt_service):
        """Test token revocation."""
        token = jwt_service.create_access_token("user123")

        # Mock Redis
        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock(return_value=True)

        with patch.object(jwt_service, '_get_redis', return_value=mock_redis):
            result = await jwt_service.revoke_token(token)
            assert result is True
            mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_revoke_token_no_redis(self, jwt_service):
        """Test token revocation when Redis is not available."""
        token = jwt_service.create_access_token("user123")

        with patch.object(jwt_service, '_get_redis', return_value=None):
            result = await jwt_service.revoke_token(token)
            assert result is False

    @pytest.mark.asyncio
    async def test_is_token_revoked(self, jwt_service):
        """Test checking if token is revoked."""
        mock_redis = AsyncMock()
        mock_redis.exists = AsyncMock(return_value=1)

        with patch.object(jwt_service, '_get_redis', return_value=mock_redis):
            result = await jwt_service.is_token_revoked("test-jti")
            assert result is True
            mock_redis.exists.assert_called_with("blacklist:test-jti")

    @pytest.mark.asyncio
    async def test_verify_token_async(self, jwt_service):
        """Test async token verification."""
        token = jwt_service.create_access_token("user123")

        with patch.object(jwt_service, 'is_token_revoked', return_value=False):
            claims = await jwt_service.verify_token_async(token)
            assert claims["sub"] == "user123"


class TestSessionManager:
    """Test session management functionality."""

    @pytest.mark.asyncio
    async def test_create_session(self, session_manager):
        """Test session creation."""
        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock(return_value=True)
        mock_redis.sadd = AsyncMock(return_value=1)
        mock_redis.expire = AsyncMock(return_value=True)

        with patch.object(session_manager, '_get_redis', return_value=mock_redis):
            session_id = await session_manager.create_session(
                user_id="user123",
                data={"ip": "127.0.0.1", "user_agent": "Mozilla"},
                ttl=3600
            )

            assert session_id is not None
            assert len(session_id) > 0
            mock_redis.setex.assert_called_once()
            mock_redis.sadd.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_session(self, session_manager):
        """Test getting session data."""
        session_data = {
            "user_id": "user123",
            "created_at": datetime.now(UTC).isoformat(),
            "data": {"ip": "127.0.0.1"}
        }

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=json.dumps(session_data))

        with patch.object(session_manager, '_get_redis', return_value=mock_redis):
            result = await session_manager.get_session("session123")
            assert result == session_data
            mock_redis.get.assert_called_with("session:session123")

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, session_manager):
        """Test getting non-existent session."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)

        with patch.object(session_manager, '_get_redis', return_value=mock_redis):
            result = await session_manager.get_session("nonexistent")
            assert result is None

    @pytest.mark.asyncio
    async def test_delete_session(self, session_manager):
        """Test session deletion."""
        session_data = {"user_id": "user123", "data": {}}

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=json.dumps(session_data))
        mock_redis.srem = AsyncMock(return_value=1)
        mock_redis.delete = AsyncMock(return_value=1)

        with patch.object(session_manager, '_get_redis', return_value=mock_redis):
            with patch.object(session_manager, 'get_session', return_value=session_data):
                result = await session_manager.delete_session("session123")
                assert result is True
                mock_redis.delete.assert_called_with("session:session123")

    @pytest.mark.asyncio
    async def test_delete_user_sessions(self, session_manager):
        """Test deleting all sessions for a user."""
        mock_redis = AsyncMock()
        mock_redis.smembers = AsyncMock(return_value={"sess1", "sess2", "sess3"})
        mock_redis.delete = AsyncMock(side_effect=[1, 1, 1, 1])  # 3 sessions + 1 set

        with patch.object(session_manager, '_get_redis', return_value=mock_redis):
            count = await session_manager.delete_user_sessions("user123")
            assert count == 3
            assert mock_redis.delete.call_count == 4  # 3 sessions + user_sessions set

    @pytest.mark.asyncio
    async def test_session_manager_no_redis(self, session_manager):
        """Test session manager when Redis is not available."""
        with patch('dotmac.platform.auth.core.REDIS_AVAILABLE', False):
            with pytest.raises(HTTPException) as exc_info:
                await session_manager._get_redis()

            assert exc_info.value.status_code == 500
            assert "Redis not available" in exc_info.value.detail


class TestAPIKeyService:
    """Test API key service functionality."""

    @pytest.mark.asyncio
    async def test_create_api_key(self, api_key_service):
        """Test API key creation."""
        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock(return_value=True)

        with patch.object(api_key_service, '_get_redis', return_value=mock_redis):
            api_key = await api_key_service.create_api_key(
                user_id="user123",
                name="test-key",
                scopes=["read", "write"]
            )

            assert api_key.startswith("sk_")
            assert len(api_key) > 10
            mock_redis.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_api_key_memory_fallback(self, api_key_service):
        """Test API key creation with memory fallback."""
        with patch.object(api_key_service, '_get_redis', return_value=None):
            api_key = await api_key_service.create_api_key(
                user_id="user123",
                name="test-key",
                scopes=["read"]
            )

            assert api_key.startswith("sk_")
            assert api_key in api_key_service._memory_keys
            assert api_key_service._memory_keys[api_key]["user_id"] == "user123"

    @pytest.mark.asyncio
    async def test_verify_api_key(self, api_key_service):
        """Test API key verification."""
        key_data = {
            "user_id": "user123",
            "name": "test-key",
            "scopes": ["read"],
            "created_at": datetime.now(UTC).isoformat()
        }

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=json.dumps(key_data))

        with patch.object(api_key_service, '_get_redis', return_value=mock_redis):
            result = await api_key_service.verify_api_key("sk_testkey")
            assert result == key_data
            mock_redis.get.assert_called_with("api_key:sk_testkey")

    @pytest.mark.asyncio
    async def test_verify_api_key_memory_fallback(self, api_key_service):
        """Test API key verification with memory fallback."""
        key_data = {"user_id": "user123", "name": "test-key"}
        api_key_service._memory_keys = {"sk_testkey": key_data}

        with patch.object(api_key_service, '_get_redis', return_value=None):
            result = await api_key_service.verify_api_key("sk_testkey")
            assert result == key_data

    @pytest.mark.asyncio
    async def test_revoke_api_key(self, api_key_service):
        """Test API key revocation."""
        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock(return_value=1)

        with patch.object(api_key_service, '_get_redis', return_value=mock_redis):
            result = await api_key_service.revoke_api_key("sk_testkey")
            assert result is True
            mock_redis.delete.assert_called_with("api_key:sk_testkey")

    @pytest.mark.asyncio
    async def test_revoke_api_key_memory_fallback(self, api_key_service):
        """Test API key revocation with memory fallback."""
        api_key_service._memory_keys = {"sk_testkey": {"user_id": "user123"}}

        with patch.object(api_key_service, '_get_redis', return_value=None):
            result = await api_key_service.revoke_api_key("sk_testkey")
            assert result is True
            assert "sk_testkey" not in api_key_service._memory_keys


class TestOAuthService:
    """Test OAuth service functionality."""

    def test_get_authorization_url(self, oauth_service):
        """Test OAuth authorization URL generation."""
        url, state = oauth_service.get_authorization_url(
            provider=OAuthProvider.GOOGLE,
            redirect_uri="http://localhost:3000/callback",
            state="custom-state"
        )

        # url is returned as tuple (url, state)
        actual_url = url[0] if isinstance(url, tuple) else url
        assert OAUTH_CONFIGS[OAuthProvider.GOOGLE]["authorize_url"] in actual_url
        assert "client_id=test-client" in actual_url
        assert "redirect_uri=" in actual_url
        assert state == "custom-state"

    def test_get_authorization_url_auto_state(self, oauth_service):
        """Test OAuth authorization URL with auto-generated state."""
        url, state = oauth_service.get_authorization_url(
            provider=OAuthProvider.GITHUB,
            redirect_uri="http://localhost:3000/callback"
        )

        # url is returned as tuple (url, state)
        actual_url = url[0] if isinstance(url, tuple) else url
        assert OAUTH_CONFIGS[OAuthProvider.GITHUB]["authorize_url"] in actual_url
        assert len(state) > 0

    @pytest.mark.asyncio
    async def test_exchange_code(self, oauth_service):
        """Test OAuth code exchange."""
        mock_token = {"access_token": "test-token", "token_type": "Bearer"}

        with patch('dotmac.platform.auth.core.AsyncOAuth2Client') as mock_client:
            instance = mock_client.return_value
            instance.fetch_token = AsyncMock(return_value=mock_token)

            result = await oauth_service.exchange_code(
                provider=OAuthProvider.GOOGLE,
                code="auth-code",
                redirect_uri="http://localhost:3000/callback"
            )

            assert result == mock_token

    @pytest.mark.asyncio
    async def test_get_user_info(self, oauth_service):
        """Test getting user info from OAuth provider."""
        mock_user_info = {"id": "12345", "email": "user@example.com"}

        with patch('dotmac.platform.auth.core.AsyncOAuth2Client') as mock_client:
            instance = mock_client.return_value
            mock_response = MagicMock()
            mock_response.json.return_value = mock_user_info
            instance.get = AsyncMock(return_value=mock_response)

            result = await oauth_service.get_user_info(
                provider=OAuthProvider.GOOGLE,
                access_token="test-token"
            )

            assert result == mock_user_info


class TestAuthDependencies:
    """Test authentication dependencies."""

    @pytest.mark.asyncio
    async def test_get_current_user_with_bearer_token(self):
        """Test getting current user with Bearer token."""
        from fastapi.security import HTTPAuthorizationCredentials

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="valid-token"
        )

        mock_claims = {
            "sub": "user123",
            "email": "user@example.com",
            "roles": ["admin"],
            "permissions": ["read", "write"]
        }

        with patch('dotmac.platform.auth.core._verify_token_with_fallback', return_value=mock_claims):
            user = await get_current_user(
                token=None,
                api_key=None,
                credentials=credentials
            )

            assert isinstance(user, UserInfo)
            assert user.user_id == "user123"
            assert user.email == "user@example.com"
            assert user.roles == ["admin"]
            assert user.permissions == ["read", "write"]

    @pytest.mark.asyncio
    async def test_get_current_user_with_oauth_token(self):
        """Test getting current user with OAuth token."""
        mock_claims = {
            "sub": "user456",
            "username": "johndoe",
            "tenant_id": "tenant789"
        }

        with patch('dotmac.platform.auth.core._verify_token_with_fallback', return_value=mock_claims):
            user = await get_current_user(
                token="oauth-token",
                api_key=None,
                credentials=None
            )

            assert user.user_id == "user456"
            assert user.username == "johndoe"
            assert user.tenant_id == "tenant789"

    @pytest.mark.asyncio
    async def test_get_current_user_with_api_key(self):
        """Test getting current user with API key."""
        key_data = {
            "user_id": "api_user123",
            "name": "test-api-key",
            "scopes": ["api:read", "api:write"]
        }

        with patch('dotmac.platform.auth.core.api_key_service.verify_api_key', return_value=key_data):
            user = await get_current_user(
                token=None,
                api_key="sk_testkey",
                credentials=None
            )

            assert user.user_id == "api_user123"
            assert user.username == "test-api-key"
            assert user.roles == ["api_user"]
            assert user.permissions == ["api:read", "api:write"]

    @pytest.mark.asyncio
    async def test_get_current_user_not_authenticated(self):
        """Test getting current user when not authenticated."""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                token=None,
                api_key=None,
                credentials=None
            )

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Not authenticated"

    @pytest.mark.asyncio
    async def test_get_current_user_optional_authenticated(self):
        """Test optional authentication when user is authenticated."""
        from fastapi.security import HTTPAuthorizationCredentials

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="valid-token"
        )

        mock_claims = {"sub": "user123"}

        with patch('dotmac.platform.auth.core._verify_token_with_fallback', return_value=mock_claims):
            user = await get_current_user_optional(
                token=None,
                api_key=None,
                credentials=credentials
            )

            assert user is not None
            assert user.user_id == "user123"

    @pytest.mark.asyncio
    async def test_get_current_user_optional_not_authenticated(self):
        """Test optional authentication when user is not authenticated."""
        user = await get_current_user_optional(
            token=None,
            api_key=None,
            credentials=None
        )

        assert user is None


class TestUtilityFunctions:
    """Test utility functions."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "SecurePassword123!"
        hashed = hash_password(password)

        assert hashed != password
        assert len(hashed) > 20
        assert hashed.startswith("$2b$")  # bcrypt prefix

    def test_verify_password(self):
        """Test password verification."""
        password = "TestPassword456!"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True
        assert verify_password("WrongPassword", hashed) is False

    def test_create_access_token_utility(self):
        """Test access token creation utility function."""
        token = create_access_token(
            user_id="user789",
            role="moderator",
            tenant_id="tenant123"
        )

        # Verify token
        claims = jwt.decode(token, JWT_SECRET)
        assert claims["sub"] == "user789"
        assert claims["role"] == "moderator"
        assert claims["tenant_id"] == "tenant123"

    def test_create_refresh_token_utility(self):
        """Test refresh token creation utility function."""
        token = create_refresh_token(
            user_id="user999",
            session_id="sess456"
        )

        # Verify token
        claims = jwt.decode(token, JWT_SECRET)
        assert claims["sub"] == "user999"
        assert claims["session_id"] == "sess456"
        assert claims["type"] == TokenType.REFRESH.value


class TestConfiguration:
    """Test auth configuration functionality."""

    def test_configure_auth(self):
        """Test auth service configuration."""
        # Store original values
        original_secret = JWT_SECRET
        original_algorithm = JWT_ALGORITHM

        try:
            # Configure with new values
            configure_auth(
                jwt_secret="new-secret",
                jwt_algorithm="RS256",
                access_token_expire_minutes=60,
                refresh_token_expire_days=14,
                redis_url="redis://new-redis:6379"
            )

            # Verify services were recreated with new config
            from dotmac.platform.auth.core import jwt_service
            assert jwt_service.secret == "new-secret"
            assert jwt_service.algorithm == "RS256"

        finally:
            # Restore original configuration
            configure_auth(
                jwt_secret=original_secret,
                jwt_algorithm=original_algorithm
            )

    def test_token_data_model(self):
        """Test TokenData model."""
        data = TokenData(
            access_token="test-access",
            refresh_token="test-refresh",
            token_type="bearer",
            expires_in=3600
        )

        assert data.access_token == "test-access"
        assert data.refresh_token == "test-refresh"
        assert data.token_type == "bearer"
        assert data.expires_in == 3600

    def test_user_info_model(self):
        """Test UserInfo model."""
        user = UserInfo(
            user_id="user123",
            email="user@example.com",
            username="johndoe",
            roles=["admin", "user"],
            permissions=["read", "write", "delete"],
            tenant_id="tenant456"
        )

        assert user.user_id == "user123"
        assert user.email == "user@example.com"
        assert user.username == "johndoe"
        assert user.roles == ["admin", "user"]
        assert user.permissions == ["read", "write", "delete"]
        assert user.tenant_id == "tenant456"

    def test_user_info_defaults(self):
        """Test UserInfo model with defaults."""
        user = UserInfo(user_id="user123")

        assert user.user_id == "user123"
        assert user.email is None
        assert user.username is None
        assert user.roles == []
        assert user.permissions == []
        assert user.tenant_id is None


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_jwt_service_redis_connection_error(self, jwt_service):
        """Test JWT service with Redis connection error."""
        with patch('dotmac.platform.auth.core.REDIS_AVAILABLE', False):
            redis_client = await jwt_service._get_redis()
            # Should return None when Redis is not available
            assert redis_client is None

    def test_jwt_token_with_bytes_response(self, jwt_service):
        """Test JWT token creation when encode returns bytes."""
        with patch.object(jwt, 'encode', return_value=b'token-bytes'):
            token = jwt_service.create_access_token("user123")
            assert token == "token-bytes"
            assert isinstance(token, str)

    @pytest.mark.asyncio
    async def test_session_manager_error_handling(self, session_manager):
        """Test session manager error handling."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(side_effect=Exception("Redis error"))

        with patch.object(session_manager, '_get_redis', return_value=mock_redis):
            result = await session_manager.get_session("session123")
            assert result is None  # Should handle error gracefully

    @pytest.mark.asyncio
    async def test_api_key_service_error_handling(self, api_key_service):
        """Test API key service error handling."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(side_effect=Exception("Redis error"))

        with patch.object(api_key_service, '_get_redis', return_value=mock_redis):
            result = await api_key_service.verify_api_key("sk_testkey")
            assert result is None  # Should handle error gracefully

    def test_is_token_revoked_sync_error(self, jwt_service):
        """Test sync token revocation check with error."""
        with patch('dotmac.platform.caching.get_redis', side_effect=Exception("Redis error")):
            result = jwt_service.is_token_revoked_sync("test-jti")
            assert result is False  # Should return False on error

    @pytest.mark.asyncio
    async def test_verify_token_with_fallback_async(self):
        """Test _verify_token_with_fallback with async path."""
        from dotmac.platform.auth.core import _verify_token_with_fallback

        mock_service = MagicMock()
        mock_claims = {"sub": "user123"}
        mock_service.verify_token_async = AsyncMock(return_value=mock_claims)
        mock_service.verify_token = MagicMock(return_value=mock_claims)

        with patch('dotmac.platform.auth.core.jwt_service', mock_service):
            result = await _verify_token_with_fallback("test-token")
            assert result == mock_claims

    @pytest.mark.asyncio
    async def test_verify_token_with_fallback_sync(self):
        """Test _verify_token_with_fallback with sync fallback."""
        from dotmac.platform.auth.core import _verify_token_with_fallback

        mock_service = MagicMock()
        mock_claims = {"sub": "user456"}
        # No verify_token_async attribute
        mock_service.verify_token = MagicMock(return_value=mock_claims)

        with patch('dotmac.platform.auth.core.jwt_service', mock_service):
            result = await _verify_token_with_fallback("test-token")
            assert result == mock_claims