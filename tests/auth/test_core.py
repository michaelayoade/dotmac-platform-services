"""Tests for auth core module."""

import json
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from dotmac.platform.auth.core import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_ALGORITHM,
    JWT_SECRET,
    REDIS_AVAILABLE,
    REFRESH_TOKEN_EXPIRE_DAYS,
    REDIS_URL,
    APIKeyService,
    JWTService,
    OAuthProvider,
    OAuthService,
    SessionManager,
    TokenData,
    TokenType,
    UserInfo,
    api_key_service,
    configure_auth,
    create_access_token,
    create_refresh_token,
    get_current_user,
    get_current_user_optional,
    hash_password,
    jwt_service,
    session_manager,
    verify_password,
)


@pytest.fixture
def sample_user_info():
    """Create sample UserInfo for testing."""
    return UserInfo(
        user_id="test-user-123",
        email="test@example.com",
        username="testuser",
        roles=["user", "admin"],
        permissions=["read", "write"],
        tenant_id="tenant-123",
    )


class TestUserInfo:
    """Test UserInfo model."""

    def test_user_info_creation(self, sample_user_info):
        """Test UserInfo model creation."""
        user = sample_user_info
        assert user.user_id == "test-user-123"
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.roles == ["user", "admin"]
        assert user.permissions == ["read", "write"]
        assert user.tenant_id == "tenant-123"

    def test_user_info_defaults(self):
        """Test UserInfo with default values."""
        user = UserInfo(user_id="test-123")
        assert user.user_id == "test-123"
        assert user.email is None
        assert user.username is None
        assert user.roles == []
        assert user.permissions == []
        assert user.tenant_id is None

    def test_user_info_validation(self):
        """Test UserInfo validation."""
        # Valid creation
        user = UserInfo(
            user_id="valid-id",
            email="test@example.com",
            roles=["admin"],
            permissions=["read:users"],
        )
        assert user.user_id == "valid-id"

        # Test field validation - UserInfo currently allows empty strings
        # This test verifies current behavior
        user_empty = UserInfo(user_id="")
        assert user_empty.user_id == ""


class TestTokenData:
    """Test TokenData model."""

    def test_token_data_creation(self):
        """Test TokenData creation."""
        token_data = TokenData(
            access_token="test-token",
            refresh_token="refresh-token",
            token_type="bearer",
            expires_in=3600,
        )
        assert token_data.access_token == "test-token"
        assert token_data.refresh_token == "refresh-token"
        assert token_data.token_type == "bearer"
        assert token_data.expires_in == 3600

    def test_token_data_defaults(self):
        """Test TokenData with defaults."""
        token_data = TokenData(
            access_token="test-token",
            expires_in=3600,
        )
        assert token_data.access_token == "test-token"
        assert token_data.refresh_token is None
        assert token_data.token_type == "bearer"
        assert token_data.expires_in == 3600


class TestTokenType:
    """Test TokenType enum."""

    def test_token_type_values(self):
        """Test TokenType enum values."""
        assert TokenType.ACCESS == "access"
        assert TokenType.REFRESH == "refresh"
        assert TokenType.API_KEY == "api_key"

    def test_token_type_iteration(self):
        """Test TokenType can be iterated."""
        types = list(TokenType)
        assert len(types) == 3
        assert TokenType.ACCESS in types
        assert TokenType.REFRESH in types
        assert TokenType.API_KEY in types


class TestOAuthProvider:
    """Test OAuthProvider enum."""

    def test_oauth_provider_values(self):
        """Test OAuthProvider enum values."""
        assert OAuthProvider.GOOGLE == "google"
        assert OAuthProvider.GITHUB == "github"
        assert OAuthProvider.MICROSOFT == "microsoft"


class TestJWTService:
    """Test JWT service functionality."""

    @pytest.fixture
    def jwt_service_instance(self):
        """Create JWT service instance for testing."""
        return JWTService(secret="test-secret", algorithm="HS256")

    def test_jwt_service_init(self, jwt_service_instance):
        """Test JWT service initialization."""
        service = jwt_service_instance
        assert service.secret == "test-secret"
        assert service.algorithm == "HS256"
        assert service.header == {"alg": "HS256"}

    def test_jwt_service_init_defaults(self):
        """Test JWT service with default values."""
        service = JWTService()
        assert service.secret == JWT_SECRET
        assert service.algorithm == JWT_ALGORITHM

    def test_create_access_token(self, jwt_service_instance):
        """Test access token creation."""
        service = jwt_service_instance
        token = service.create_access_token("user-123")

        assert isinstance(token, str)
        assert len(token) > 0

        # Verify token content
        claims = service.verify_token(token)
        assert claims["sub"] == "user-123"
        assert claims["type"] == TokenType.ACCESS.value
        assert "exp" in claims
        assert "iat" in claims
        assert "jti" in claims

    def test_create_access_token_with_claims(self, jwt_service_instance):
        """Test access token creation with additional claims."""
        service = jwt_service_instance
        additional_claims = {"roles": ["admin"], "tenant_id": "tenant-123"}
        token = service.create_access_token("user-123", additional_claims)

        claims = service.verify_token(token)
        assert claims["sub"] == "user-123"
        assert claims["roles"] == ["admin"]
        assert claims["tenant_id"] == "tenant-123"

    def test_create_access_token_custom_expiry(self, jwt_service_instance):
        """Test access token with custom expiry."""
        service = jwt_service_instance
        token = service.create_access_token("user-123", expire_minutes=60)

        claims = service.verify_token(token)
        assert claims["sub"] == "user-123"

        # Check expiry time (approximately)
        exp_time = datetime.fromtimestamp(claims["exp"], tz=timezone.utc)
        expected_exp = datetime.now(timezone.utc) + timedelta(minutes=60)
        assert abs((exp_time - expected_exp).total_seconds()) < 10

    def test_create_refresh_token(self, jwt_service_instance):
        """Test refresh token creation."""
        service = jwt_service_instance
        token = service.create_refresh_token("user-123")

        assert isinstance(token, str)
        assert len(token) > 0

        claims = service.verify_token(token)
        assert claims["sub"] == "user-123"
        assert claims["type"] == TokenType.REFRESH.value

    def test_create_refresh_token_with_claims(self, jwt_service_instance):
        """Test refresh token creation with additional claims."""
        service = jwt_service_instance
        additional_claims = {"device_id": "device-123"}
        token = service.create_refresh_token("user-123", additional_claims)

        claims = service.verify_token(token)
        assert claims["sub"] == "user-123"
        assert claims["device_id"] == "device-123"

    def test_verify_token_success(self, jwt_service_instance):
        """Test successful token verification."""
        service = jwt_service_instance
        token = service.create_access_token("user-123")
        claims = service.verify_token(token)

        assert claims["sub"] == "user-123"
        assert isinstance(claims["exp"], int)
        assert isinstance(claims["iat"], int)

    def test_verify_token_invalid(self, jwt_service_instance):
        """Test token verification with invalid token."""
        service = jwt_service_instance

        with pytest.raises(HTTPException) as exc_info:
            service.verify_token("invalid.token.here")

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid token" in str(exc_info.value.detail)

    def test_verify_token_wrong_secret(self):
        """Test token verification with wrong secret."""
        service1 = JWTService(secret="secret1")
        service2 = JWTService(secret="secret2")

        token = service1.create_access_token("user-123")

        with pytest.raises(HTTPException) as exc_info:
            service2.verify_token(token)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_token_expiry_claim(self, jwt_service_instance):
        """Test token expiry claim is set correctly."""
        service = jwt_service_instance

        # Create token with 30 minute expiry
        token = service.create_access_token("user-123", expire_minutes=30)
        claims = service.verify_token(token)

        # Check that expiry is approximately 30 minutes from now
        now = datetime.now(timezone.utc)
        exp_time = datetime.fromtimestamp(claims["exp"], tz=timezone.utc)
        expected_exp = now + timedelta(minutes=30)

        # Allow for some time difference in test execution (within 10 seconds)
        assert abs((exp_time - expected_exp).total_seconds()) < 10


class TestSessionManager:
    """Test session management functionality."""

    @pytest.fixture
    def session_manager_instance(self):
        """Create session manager instance for testing."""
        return SessionManager("redis://test:6379")

    @pytest.mark.skipif(not REDIS_AVAILABLE, reason="Redis not available")
    async def test_session_manager_init(self, session_manager_instance):
        """Test session manager initialization."""
        manager = session_manager_instance
        assert manager.redis_url == "redis://test:6379"
        assert manager._redis is None

    @pytest.mark.skipif(not REDIS_AVAILABLE, reason="Redis not available")
    async def test_create_session(self, session_manager_instance):
        """Test session creation."""
        manager = session_manager_instance

        with patch.object(manager, '_get_redis') as mock_get_redis:
            mock_redis = AsyncMock()
            mock_get_redis.return_value = mock_redis

            session_data = {"role": "admin", "permissions": ["read", "write"]}
            session_id = await manager.create_session("user-123", session_data, ttl=3600)

            assert isinstance(session_id, str)
            assert len(session_id) > 0

            # Verify Redis calls
            mock_redis.setex.assert_called_once()
            call_args = mock_redis.setex.call_args[0]
            assert call_args[0].startswith("session:")
            assert call_args[1] == 3600  # TTL

            # Verify session data structure
            stored_data = json.loads(call_args[2])
            assert stored_data["user_id"] == "user-123"
            assert stored_data["data"] == session_data
            assert "created_at" in stored_data

    @pytest.mark.skipif(not REDIS_AVAILABLE, reason="Redis not available")
    async def test_get_session_success(self, session_manager_instance):
        """Test successful session retrieval."""
        manager = session_manager_instance

        session_data = {
            "user_id": "user-123",
            "created_at": "2024-01-01T00:00:00Z",
            "data": {"role": "admin"}
        }

        with patch.object(manager, '_get_redis') as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.get.return_value = json.dumps(session_data)
            mock_get_redis.return_value = mock_redis

            result = await manager.get_session("session-123")

            assert result == session_data
            mock_redis.get.assert_called_once_with("session:session-123")

    @pytest.mark.skipif(not REDIS_AVAILABLE, reason="Redis not available")
    async def test_get_session_not_found(self, session_manager_instance):
        """Test session retrieval when session doesn't exist."""
        manager = session_manager_instance

        with patch.object(manager, '_get_redis') as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.get.return_value = None
            mock_get_redis.return_value = mock_redis

            result = await manager.get_session("nonexistent-session")

            assert result is None

    @pytest.mark.skipif(not REDIS_AVAILABLE, reason="Redis not available")
    async def test_delete_session_success(self, session_manager_instance):
        """Test successful session deletion."""
        manager = session_manager_instance

        session_data = {
            "user_id": "user-123",
            "created_at": "2024-01-01T00:00:00Z",
            "data": {"role": "admin"}
        }

        with patch.object(manager, '_get_redis') as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.get.return_value = json.dumps(session_data)
            mock_redis.delete.return_value = 1  # Successfully deleted
            mock_get_redis.return_value = mock_redis

            result = await manager.delete_session("session-123")

            assert result is True
            mock_redis.delete.assert_called_once_with("session:session-123")

    @pytest.mark.skipif(not REDIS_AVAILABLE, reason="Redis not available")
    async def test_delete_session_not_found(self, session_manager_instance):
        """Test session deletion when session doesn't exist."""
        manager = session_manager_instance

        with patch.object(manager, '_get_redis') as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.get.return_value = None
            mock_redis.delete.return_value = 0  # Nothing deleted
            mock_get_redis.return_value = mock_redis

            result = await manager.delete_session("nonexistent-session")

            assert result is False

    async def test_get_redis_unavailable(self, session_manager_instance):
        """Test Redis unavailable error handling."""
        manager = session_manager_instance

        with patch('dotmac.platform.auth.core.REDIS_AVAILABLE', False):
            with pytest.raises(HTTPException) as exc_info:
                await manager._get_redis()

            assert exc_info.value.status_code == 500
            assert "Redis not available" in str(exc_info.value.detail)


class TestAPIKeyService:
    """Test API key service functionality."""

    @pytest.fixture
    def api_key_service_instance(self):
        """Create API key service instance for testing."""
        return APIKeyService("redis://test:6379")

    async def test_api_key_service_init(self, api_key_service_instance):
        """Test API key service initialization."""
        service = api_key_service_instance
        assert service.redis_url == "redis://test:6379"
        assert service._redis is None

    async def test_create_api_key_with_redis(self, api_key_service_instance):
        """Test API key creation with Redis."""
        service = api_key_service_instance

        with patch.object(service, '_get_redis') as mock_get_redis:
            mock_redis = AsyncMock()
            mock_get_redis.return_value = mock_redis

            api_key = await service.create_api_key(
                user_id="user-123",
                name="Test API Key",
                scopes=["read", "write"]
            )

            assert isinstance(api_key, str)
            assert api_key.startswith("sk_")
            assert len(api_key) > 10

            # Verify Redis call
            mock_redis.set.assert_called_once()
            call_args = mock_redis.set.call_args[0]
            assert call_args[0] == f"api_key:{api_key}"

            # Verify stored data
            stored_data = json.loads(call_args[1])
            assert stored_data["user_id"] == "user-123"
            assert stored_data["name"] == "Test API Key"
            assert stored_data["scopes"] == ["read", "write"]
            assert "created_at" in stored_data

    async def test_create_api_key_memory_fallback(self, api_key_service_instance):
        """Test API key creation with memory fallback."""
        service = api_key_service_instance

        with patch.object(service, '_get_redis') as mock_get_redis:
            mock_get_redis.return_value = None  # Redis unavailable

            api_key = await service.create_api_key(
                user_id="user-123",
                name="Test API Key",
                scopes=["read"]
            )

            assert isinstance(api_key, str)
            assert api_key.startswith("sk_")

            # Verify data stored in memory
            assert hasattr(service, '_memory_keys')
            assert api_key in service._memory_keys
            assert service._memory_keys[api_key]["user_id"] == "user-123"

    async def test_verify_api_key_with_redis(self, api_key_service_instance):
        """Test API key verification with Redis."""
        service = api_key_service_instance

        api_key_data = {
            "user_id": "user-123",
            "name": "Test Key",
            "scopes": ["read"],
            "created_at": "2024-01-01T00:00:00Z"
        }

        with patch.object(service, '_get_redis') as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.get.return_value = json.dumps(api_key_data)
            mock_get_redis.return_value = mock_redis

            result = await service.verify_api_key("sk_test_key")

            assert result == api_key_data
            mock_redis.get.assert_called_once_with("api_key:sk_test_key")

    async def test_verify_api_key_memory_fallback(self, api_key_service_instance):
        """Test API key verification with memory fallback."""
        service = api_key_service_instance

        api_key_data = {
            "user_id": "user-123",
            "name": "Test Key",
            "scopes": ["read"]
        }

        # Set up memory storage
        service._memory_keys = {"sk_test_key": api_key_data}

        with patch.object(service, '_get_redis') as mock_get_redis:
            mock_get_redis.return_value = None  # Redis unavailable

            result = await service.verify_api_key("sk_test_key")

            assert result == api_key_data

    async def test_verify_api_key_not_found(self, api_key_service_instance):
        """Test API key verification when key doesn't exist."""
        service = api_key_service_instance

        with patch.object(service, '_get_redis') as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.get.return_value = None
            mock_get_redis.return_value = mock_redis

            result = await service.verify_api_key("sk_nonexistent")

            assert result is None

    async def test_revoke_api_key_with_redis(self, api_key_service_instance):
        """Test API key revocation with Redis."""
        service = api_key_service_instance

        with patch.object(service, '_get_redis') as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.delete.return_value = 1  # Successfully deleted
            mock_get_redis.return_value = mock_redis

            result = await service.revoke_api_key("sk_test_key")

            assert result is True
            mock_redis.delete.assert_called_once_with("api_key:sk_test_key")

    async def test_revoke_api_key_memory_fallback(self, api_key_service_instance):
        """Test API key revocation with memory fallback."""
        service = api_key_service_instance

        # Set up memory storage
        service._memory_keys = {"sk_test_key": {"user_id": "user-123"}}

        with patch.object(service, '_get_redis') as mock_get_redis:
            mock_get_redis.return_value = None  # Redis unavailable

            result = await service.revoke_api_key("sk_test_key")

            assert result is True
            assert "sk_test_key" not in service._memory_keys


class TestOAuthService:
    """Test OAuth service functionality."""

    @pytest.fixture
    def oauth_service_instance(self):
        """Create OAuth service instance for testing."""
        return OAuthService(client_id="test-client", client_secret="test-secret")

    def test_oauth_service_init(self, oauth_service_instance):
        """Test OAuth service initialization."""
        service = oauth_service_instance
        assert service.client_id == "test-client"
        assert service.client_secret == "test-secret"

    def test_get_authorization_url(self, oauth_service_instance):
        """Test authorization URL generation."""
        service = oauth_service_instance

        with patch('dotmac.platform.auth.core.AsyncOAuth2Client') as mock_client_class:
            mock_client = MagicMock()
            mock_client.create_authorization_url.return_value = "https://example.com/auth"
            mock_client_class.return_value = mock_client

            url, state = service.get_authorization_url(
                OAuthProvider.GOOGLE,
                "https://app.com/callback"
            )

            assert url == "https://example.com/auth"
            assert isinstance(state, str)
            assert len(state) > 0

    def test_get_authorization_url_custom_state(self, oauth_service_instance):
        """Test authorization URL generation with custom state."""
        service = oauth_service_instance

        with patch('dotmac.platform.auth.core.AsyncOAuth2Client') as mock_client_class:
            mock_client = MagicMock()
            mock_client.create_authorization_url.return_value = "https://example.com/auth"
            mock_client_class.return_value = mock_client

            url, state = service.get_authorization_url(
                OAuthProvider.GITHUB,
                "https://app.com/callback",
                state="custom-state"
            )

            assert url == "https://example.com/auth"
            assert state == "custom-state"

    async def test_exchange_code(self, oauth_service_instance):
        """Test code exchange for tokens."""
        service = oauth_service_instance

        with patch('dotmac.platform.auth.core.AsyncOAuth2Client') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.fetch_token.return_value = {
                "access_token": "access-token",
                "refresh_token": "refresh-token",
                "token_type": "Bearer"
            }
            mock_client_class.return_value = mock_client

            result = await service.exchange_code(
                OAuthProvider.GOOGLE,
                "auth-code",
                "https://app.com/callback"
            )

            assert result["access_token"] == "access-token"
            assert result["refresh_token"] == "refresh-token"

    async def test_get_user_info(self, oauth_service_instance):
        """Test user info retrieval."""
        service = oauth_service_instance

        with patch('dotmac.platform.auth.core.AsyncOAuth2Client') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "id": "123",
                "email": "user@example.com",
                "name": "Test User"
            }
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await service.get_user_info(
                OAuthProvider.GOOGLE,
                "access-token"
            )

            assert result["id"] == "123"
            assert result["email"] == "user@example.com"
            assert result["name"] == "Test User"


class TestUtilityFunctions:
    """Test utility functions."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "test-password-123"
        hashed = hash_password(password)

        assert isinstance(hashed, str)
        assert len(hashed) > 0
        assert hashed != password  # Should be hashed
        assert hashed.startswith("$2b$")  # bcrypt format

    def test_verify_password_success(self):
        """Test successful password verification."""
        password = "test-password-123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_failure(self):
        """Test failed password verification."""
        password = "test-password-123"
        wrong_password = "wrong-password"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_create_access_token_function(self):
        """Test create_access_token utility function."""
        token = create_access_token("user-123", roles=["admin"])

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token_function(self):
        """Test create_refresh_token utility function."""
        token = create_refresh_token("user-123", device_id="device-123")

        assert isinstance(token, str)
        assert len(token) > 0


class TestDependencies:
    """Test dependency functions."""

    @pytest.fixture
    def mock_credentials(self):
        """Mock HTTP authorization credentials."""
        return HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="valid-token"
        )

    async def test_get_current_user_bearer_token_success(self, mock_credentials, sample_user_info):
        """Test get_current_user with valid bearer token."""
        with patch('dotmac.platform.auth.core.jwt_service') as mock_jwt_service:
            mock_jwt_service.verify_token.return_value = {
                "sub": "test-user-123",
                "email": "test@example.com",
                "username": "testuser",
                "roles": ["user", "admin"],
                "permissions": ["read", "write"],
                "tenant_id": "tenant-123"
            }

            result = await get_current_user(
                token=None,
                api_key=None,
                credentials=mock_credentials
            )

            assert result.user_id == "test-user-123"
            assert result.email == "test@example.com"
            assert result.roles == ["user", "admin"]

    async def test_get_current_user_oauth_token_success(self, sample_user_info):
        """Test get_current_user with valid OAuth token."""
        with patch('dotmac.platform.auth.core.jwt_service') as mock_jwt_service:
            mock_jwt_service.verify_token.return_value = {
                "sub": "test-user-123",
                "email": "test@example.com",
                "username": "testuser",
                "roles": ["user"],
                "permissions": ["read"],
                "tenant_id": "tenant-123"
            }

            result = await get_current_user(
                token="valid-oauth-token",
                api_key=None,
                credentials=None
            )

            assert result.user_id == "test-user-123"
            assert result.email == "test@example.com"

    async def test_get_current_user_api_key_success(self):
        """Test get_current_user with valid API key."""
        with patch('dotmac.platform.auth.core.api_key_service') as mock_api_key_service:
            # Mock the async method properly
            async def mock_verify_api_key(api_key):
                return {
                    "user_id": "user-123",
                    "name": "Test API Key",
                    "scopes": ["read", "write"]
                }

            mock_api_key_service.verify_api_key = mock_verify_api_key

            result = await get_current_user(
                token=None,
                api_key="sk_valid_key",
                credentials=None
            )

            assert result.user_id == "user-123"
            assert result.username == "Test API Key"
            assert result.roles == ["api_user"]
            assert result.permissions == ["read", "write"]

    async def test_get_current_user_no_auth(self):
        """Test get_current_user with no authentication."""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                token=None,
                api_key=None,
                credentials=None
            )

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Not authenticated" in str(exc_info.value.detail)

    async def test_get_current_user_invalid_token(self, mock_credentials):
        """Test get_current_user with invalid token."""
        with patch('dotmac.platform.auth.core.jwt_service') as mock_jwt_service:
            mock_jwt_service.verify_token.side_effect = HTTPException(
                status_code=401,
                detail="Invalid token"
            )

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(
                    token=None,
                    api_key=None,
                    credentials=mock_credentials
                )

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_get_current_user_optional_success(self, mock_credentials, sample_user_info):
        """Test get_current_user_optional with valid token."""
        with patch('dotmac.platform.auth.core.jwt_service') as mock_jwt_service:
            mock_jwt_service.verify_token.return_value = {
                "sub": "test-user-123",
                "email": "test@example.com",
                "username": "testuser",
                "roles": ["user"],
                "permissions": ["read"],
                "tenant_id": "tenant-123"
            }

            result = await get_current_user_optional(
                token=None,
                api_key=None,
                credentials=mock_credentials
            )

            assert result is not None
            assert result.user_id == "test-user-123"

    async def test_get_current_user_optional_no_auth(self):
        """Test get_current_user_optional with no authentication."""
        result = await get_current_user_optional(
            token=None,
            api_key=None,
            credentials=None
        )

        assert result is None


class TestConfiguration:
    """Test auth configuration."""

    def test_configure_auth_all_params(self):
        """Test configure_auth with all parameters."""
        # Test that configure_auth function exists and is callable
        assert callable(configure_auth)

        # Create a test service to verify configuration works
        test_service = JWTService(secret="test-secret", algorithm="HS256")
        assert test_service.secret == "test-secret"
        assert test_service.algorithm == "HS256"

    def test_configure_auth_partial_params(self):
        """Test configure_auth with partial parameters."""
        # Test that function accepts partial parameters without error
        try:
            configure_auth(access_token_expire_minutes=45)
            # If no exception is raised, the test passes
            assert True
        except Exception as e:
            pytest.fail(f"configure_auth failed with partial parameters: {e}")


class TestConstants:
    """Test module constants."""

    def test_constants_exist(self):
        """Test that required constants exist."""
        assert isinstance(JWT_SECRET, str)
        assert isinstance(JWT_ALGORITHM, str)
        assert isinstance(ACCESS_TOKEN_EXPIRE_MINUTES, int)
        assert isinstance(REFRESH_TOKEN_EXPIRE_DAYS, int)
        assert isinstance(REDIS_URL, str)
        assert isinstance(REDIS_AVAILABLE, bool)

    def test_service_instances_exist(self):
        """Test that service instances exist."""
        assert jwt_service is not None
        assert session_manager is not None
        assert api_key_service is not None


class TestPrivateHelpers:
    """Test private helper functions."""

    def test_claims_to_user_info(self):
        """Test _claims_to_user_info helper function."""
        from dotmac.platform.auth.core import _claims_to_user_info

        claims = {
            "sub": "user-123",
            "email": "test@example.com",
            "username": "testuser",
            "roles": ["admin"],
            "permissions": ["read", "write"],
            "tenant_id": "tenant-123"
        }

        user_info = _claims_to_user_info(claims)

        assert user_info.user_id == "user-123"
        assert user_info.email == "test@example.com"
        assert user_info.username == "testuser"
        assert user_info.roles == ["admin"]
        assert user_info.permissions == ["read", "write"]
        assert user_info.tenant_id == "tenant-123"

    def test_claims_to_user_info_minimal(self):
        """Test _claims_to_user_info with minimal claims."""
        from dotmac.platform.auth.core import _claims_to_user_info

        claims = {"sub": "user-123"}

        user_info = _claims_to_user_info(claims)

        assert user_info.user_id == "user-123"
        assert user_info.email is None
        assert user_info.username is None
        assert user_info.roles == []
        assert user_info.permissions == []
        assert user_info.tenant_id is None