"""
Additional tests for Auth Core module to achieve >90% coverage.

Focuses on edge cases and error paths.
"""

import json
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from authlib.jose import jwt
from fastapi import HTTPException

from dotmac.platform.auth.core import (
    JWTService,
    SessionManager,
    APIKeyService,
    TokenType,
    get_current_user,
    _verify_token_with_fallback,
)


class TestJWTServiceAdditional:
    """Additional JWT service tests for uncovered lines."""

    def test_create_access_token_without_additional_claims(self):
        """Test access token creation without additional claims."""
        service = JWTService(secret="test-secret")
        token = service.create_access_token(subject="user123")

        claims = jwt.decode(token, "test-secret")
        assert claims["sub"] == "user123"
        assert claims["type"] == TokenType.ACCESS.value
        # Should not have additional claims
        assert "role" not in claims

    def test_create_refresh_token_without_additional_claims(self):
        """Test refresh token creation without additional claims."""
        service = JWTService(secret="test-secret")
        token = service.create_refresh_token(subject="user456")

        claims = jwt.decode(token, "test-secret")
        assert claims["sub"] == "user456"
        assert claims["type"] == TokenType.REFRESH.value

    @pytest.mark.asyncio
    async def test_revoke_token_without_jti(self):
        """Test revoking a token without JTI."""
        service = JWTService(secret="test-secret")

        # Create a token without JTI (mock it)
        data = {"sub": "user123", "type": TokenType.ACCESS.value}
        expire = datetime.now(UTC) + timedelta(hours=1)
        to_encode = {"sub": "user123", "exp": expire, "iat": datetime.now(UTC)}
        # Note: No 'jti' field

        token = jwt.encode(service.header, to_encode, service.secret)
        token_str = token.decode("utf-8") if isinstance(token, bytes) else token

        mock_redis = AsyncMock()
        with patch.object(service, '_get_redis', return_value=mock_redis):
            result = await service.revoke_token(token_str)
            assert result is False  # Should return False for token without JTI

    @pytest.mark.asyncio
    async def test_revoke_token_without_exp(self):
        """Test revoking a token without expiry."""
        service = JWTService(secret="test-secret")

        # Create a token without exp
        data = {"sub": "user123", "jti": "test-jti", "iat": datetime.now(UTC)}
        token = jwt.encode(service.header, data, service.secret)
        token_str = token.decode("utf-8") if isinstance(token, bytes) else token

        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock(return_value=True)

        with patch.object(service, '_get_redis', return_value=mock_redis):
            result = await service.revoke_token(token_str)
            assert result is True
            # Should call set without TTL
            mock_redis.set.assert_called_with("blacklist:test-jti", "1")

    @pytest.mark.asyncio
    async def test_revoke_token_exception(self):
        """Test token revocation with exception."""
        service = JWTService(secret="test-secret")
        token = service.create_access_token("user123")

        with patch.object(service, '_get_redis', side_effect=Exception("Redis error")):
            result = await service.revoke_token(token)
            assert result is False

    @pytest.mark.asyncio
    async def test_is_token_revoked_exception(self):
        """Test checking token revocation with exception."""
        service = JWTService(secret="test-secret")

        mock_redis = AsyncMock()
        mock_redis.exists = AsyncMock(side_effect=Exception("Redis error"))

        with patch.object(service, '_get_redis', return_value=mock_redis):
            result = await service.is_token_revoked("test-jti")
            assert result is False

    def test_is_token_revoked_sync_no_redis(self):
        """Test sync token revocation check when Redis is not available."""
        service = JWTService(secret="test-secret")

        with patch('dotmac.platform.caching.get_redis', return_value=None):
            result = service.is_token_revoked_sync("test-jti")
            assert result is False

    @pytest.mark.asyncio
    async def test_get_redis_already_initialized(self):
        """Test getting Redis when already initialized."""
        service = JWTService(secret="test-secret")
        mock_redis = AsyncMock()
        service._redis = mock_redis

        result = await service._get_redis()
        assert result is mock_redis


class TestSessionManagerAdditional:
    """Additional session manager tests."""

    @pytest.mark.asyncio
    async def test_get_session_exception(self):
        """Test getting session with exception."""
        manager = SessionManager()

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(side_effect=Exception("Redis error"))

        with patch.object(manager, '_get_redis', return_value=mock_redis):
            result = await manager.get_session("session123")
            assert result is None

    @pytest.mark.asyncio
    async def test_delete_session_exception(self):
        """Test deleting session with exception."""
        manager = SessionManager()

        with patch.object(manager, '_get_redis', side_effect=Exception("Redis error")):
            result = await manager.delete_session("session123")
            assert result is False

    @pytest.mark.asyncio
    async def test_delete_session_no_user_id(self):
        """Test deleting session when session has no user_id."""
        manager = SessionManager()
        session_data = {"data": {}}  # No user_id field

        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock(return_value=1)

        with patch.object(manager, '_get_redis', return_value=mock_redis):
            with patch.object(manager, 'get_session', return_value=session_data):
                result = await manager.delete_session("session123")
                assert result is True
                # Should still delete the session
                mock_redis.delete.assert_called_with("session:session123")

    @pytest.mark.asyncio
    async def test_delete_user_sessions_exception(self):
        """Test deleting user sessions with exception."""
        manager = SessionManager()

        with patch.object(manager, '_get_redis', side_effect=Exception("Redis error")):
            count = await manager.delete_user_sessions("user123")
            assert count == 0

    @pytest.mark.asyncio
    async def test_get_redis_already_initialized(self):
        """Test getting Redis when already initialized."""
        manager = SessionManager()
        mock_redis = AsyncMock()
        manager._redis = mock_redis

        result = await manager._get_redis()
        assert result is mock_redis


class TestAPIKeyServiceAdditional:
    """Additional API key service tests."""

    @pytest.mark.asyncio
    async def test_verify_api_key_exception(self):
        """Test API key verification with exception."""
        service = APIKeyService()

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(side_effect=Exception("Redis error"))

        with patch.object(service, '_get_redis', return_value=mock_redis):
            result = await service.verify_api_key("sk_test")
            assert result is None

    @pytest.mark.asyncio
    async def test_verify_api_key_no_memory_keys(self):
        """Test API key verification with no memory keys attribute."""
        service = APIKeyService()
        # Remove the _memory_keys attribute to test the getattr fallback
        if hasattr(service, '_memory_keys'):
            delattr(service, '_memory_keys')

        with patch.object(service, '_get_redis', return_value=None):
            result = await service.verify_api_key("sk_test")
            assert result is None

    @pytest.mark.asyncio
    async def test_revoke_api_key_exception(self):
        """Test API key revocation with exception."""
        service = APIKeyService()

        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock(side_effect=Exception("Redis error"))

        with patch.object(service, '_get_redis', return_value=mock_redis):
            result = await service.revoke_api_key("sk_test")
            assert result is False

    @pytest.mark.asyncio
    async def test_revoke_api_key_no_memory_keys(self):
        """Test API key revocation with no memory keys."""
        service = APIKeyService()
        # Remove the _memory_keys attribute
        if hasattr(service, '_memory_keys'):
            delattr(service, '_memory_keys')

        with patch.object(service, '_get_redis', return_value=None):
            result = await service.revoke_api_key("sk_test")
            assert result is False

    @pytest.mark.asyncio
    async def test_get_redis_no_redis_available(self):
        """Test getting Redis when not available and initializing memory storage."""
        service = APIKeyService()
        # Remove existing _memory_keys to test initialization
        if hasattr(service, '_memory_keys'):
            delattr(service, '_memory_keys')

        with patch('dotmac.platform.auth.core.REDIS_AVAILABLE', False):
            result = await service._get_redis()
            assert result is None
            assert hasattr(service, '_memory_keys')
            assert service._memory_keys == {}

    @pytest.mark.asyncio
    async def test_get_redis_already_initialized(self):
        """Test getting Redis when already initialized."""
        service = APIKeyService()
        mock_redis = AsyncMock()
        service._redis = mock_redis

        with patch('dotmac.platform.auth.core.REDIS_AVAILABLE', True):
            result = await service._get_redis()
            assert result is mock_redis


class TestAuthDependenciesAdditional:
    """Additional auth dependency tests."""

    @pytest.mark.asyncio
    async def test_get_current_user_bearer_token_invalid(self):
        """Test getting current user with invalid Bearer token."""
        from fastapi.security import HTTPAuthorizationCredentials

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid-token"
        )

        with patch('dotmac.platform.auth.core._verify_token_with_fallback', side_effect=HTTPException(status_code=401)):
            # Should try OAuth2 token next
            with patch('dotmac.platform.auth.core.api_key_service.verify_api_key', return_value=None):
                with pytest.raises(HTTPException) as exc_info:
                    await get_current_user(
                        token=None,
                        api_key=None,
                        credentials=credentials
                    )
                assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_oauth_token_invalid(self):
        """Test getting current user with invalid OAuth token."""
        with patch('dotmac.platform.auth.core._verify_token_with_fallback', side_effect=HTTPException(status_code=401)):
            # Should try API key next
            with patch('dotmac.platform.auth.core.api_key_service.verify_api_key', return_value=None):
                with pytest.raises(HTTPException) as exc_info:
                    await get_current_user(
                        token="invalid-oauth",
                        api_key=None,
                        credentials=None
                    )
                assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_verify_token_with_fallback_awaitable_dict(self):
        """Test _verify_token_with_fallback when verify_token_async returns awaitable dict."""
        mock_service = MagicMock()
        mock_claims = {"sub": "user123", "type": "access"}

        # Create an async function that returns dict
        async def async_verify(token):
            return mock_claims

        mock_service.verify_token_async = async_verify

        with patch('dotmac.platform.auth.core.jwt_service', mock_service):
            result = await _verify_token_with_fallback("test-token")
            assert result == mock_claims

    @pytest.mark.asyncio
    async def test_verify_token_with_fallback_type_error(self):
        """Test _verify_token_with_fallback with TypeError (e.g., from MagicMock)."""
        mock_service = MagicMock()
        mock_claims = {"sub": "user456"}

        # Make verify_token_async raise TypeError when awaited
        mock_service.verify_token_async = MagicMock(side_effect=TypeError("Cannot await"))
        mock_service.verify_token = MagicMock(return_value=mock_claims)

        with patch('dotmac.platform.auth.core.jwt_service', mock_service):
            result = await _verify_token_with_fallback("test-token")
            assert result == mock_claims
            # Should fall back to sync verify_token
            mock_service.verify_token.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_token_with_fallback_non_awaitable(self):
        """Test _verify_token_with_fallback when result is not awaitable."""
        mock_service = MagicMock()
        mock_claims = {"sub": "user789"}

        # verify_token_async returns dict directly (not awaitable)
        mock_service.verify_token_async = MagicMock(return_value=mock_claims)

        with patch('dotmac.platform.auth.core.jwt_service', mock_service):
            with patch('inspect.isawaitable', return_value=False):
                result = await _verify_token_with_fallback("test-token")
                assert result == mock_claims