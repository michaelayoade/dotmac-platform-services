"""Test router functions by executing them directly."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

# Import all router components
from dotmac.platform.auth.router import (
    login, register, refresh_token, logout, verify_token,
    request_password_reset, confirm_password_reset, get_current_user,
    LoginRequest, RegisterRequest, RefreshTokenRequest,
    PasswordResetRequest, PasswordResetConfirm
)


class TestRouterFunctions:
    """Test router functions directly."""

    @pytest.fixture
    def mock_user(self):
        """Mock user for testing."""
        user = MagicMock()
        user.id = uuid4()
        user.username = "testuser"
        user.email = "test@example.com"
        user.password_hash = "$2b$12$LQv3c1yqBWVHLkqgqeHuYOqlJmP3LxWJYCbHyF8TtLFGhvKRLcChe"
        user.full_name = "Test User"
        user.roles = ["user"]
        user.is_active = True
        user.tenant_id = "tenant123"
        return user

    @pytest.fixture
    def mock_session(self):
        """Mock database session."""
        session = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        return session

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.verify_password')
    @patch('dotmac.platform.auth.router.jwt_service')
    @patch('dotmac.platform.auth.router.session_manager')
    async def test_login_function_success(
        self, mock_session_manager, mock_jwt_service, mock_verify_password,
        mock_user_service_class, mock_user, mock_session
    ):
        """Test login function directly."""
        # Setup mocks
        mock_user_service = MagicMock()
        mock_user_service.get_user_by_username = AsyncMock(return_value=mock_user)
        mock_user_service_class.return_value = mock_user_service

        mock_verify_password.return_value = True
        mock_jwt_service.create_access_token.return_value = "access_token"
        mock_jwt_service.create_refresh_token.return_value = "refresh_token"
        mock_session_manager.create_session = AsyncMock()

        # Test login
        request = LoginRequest(username="testuser", password="password123")
        result = await login(request, mock_session)

        assert result.access_token == "access_token"
        assert result.refresh_token == "refresh_token"
        assert result.token_type == "bearer"

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.verify_password')
    async def test_login_function_invalid_credentials(
        self, mock_verify_password, mock_user_service_class, mock_user, mock_session
    ):
        """Test login with invalid credentials."""
        mock_user_service = MagicMock()
        mock_user_service.get_user_by_username = AsyncMock(return_value=mock_user)
        mock_user_service_class.return_value = mock_user_service

        mock_verify_password.return_value = False

        request = LoginRequest(username="testuser", password="wrongpassword")

        with pytest.raises(HTTPException) as exc_info:
            await login(request, mock_session)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.verify_password')
    async def test_login_function_inactive_user(
        self, mock_verify_password, mock_user_service_class, mock_session
    ):
        """Test login with inactive user."""
        inactive_user = MagicMock()
        inactive_user.is_active = False
        inactive_user.password_hash = "$2b$12$LQv3c1yqBWVHLkqgqeHuYOqlJmP3LxWJYCbHyF8TtLFGhvKRLcChe"

        mock_user_service = MagicMock()
        mock_user_service.get_user_by_username = AsyncMock(return_value=inactive_user)
        mock_user_service_class.return_value = mock_user_service

        mock_verify_password.return_value = True

        request = LoginRequest(username="inactive", password="password123")

        with pytest.raises(HTTPException) as exc_info:
            await login(request, mock_session)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.jwt_service')
    @patch('dotmac.platform.auth.router.session_manager')
    @patch('dotmac.platform.auth.router.get_auth_email_service')
    async def test_register_function_success(
        self, mock_email_service, mock_session_manager, mock_jwt_service,
        mock_user_service_class, mock_session
    ):
        """Test register function directly."""
        new_user = MagicMock()
        new_user.id = uuid4()
        new_user.username = "newuser"
        new_user.email = "new@example.com"
        new_user.full_name = "New User"
        new_user.roles = ["user"]
        new_user.tenant_id = None

        mock_user_service = MagicMock()
        mock_user_service.get_user_by_username = AsyncMock(return_value=None)
        mock_user_service.get_user_by_email = AsyncMock(return_value=None)
        mock_user_service.create_user = AsyncMock(return_value=new_user)
        mock_user_service_class.return_value = mock_user_service

        mock_jwt_service.create_access_token.return_value = "access_token"
        mock_jwt_service.create_refresh_token.return_value = "refresh_token"
        mock_session_manager.create_session = AsyncMock()

        mock_facade = MagicMock()
        mock_facade.send_welcome_email = AsyncMock()
        mock_email_service.return_value = mock_facade

        request = RegisterRequest(
            username="newuser",
            email="new@example.com",
            password="SecurePass123!",
            full_name="New User"
        )

        result = await register(request, mock_session)

        assert result.access_token == "access_token"
        assert result.refresh_token == "refresh_token"

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.UserService')
    async def test_register_function_username_exists(
        self, mock_user_service_class, mock_user, mock_session
    ):
        """Test register with existing username."""
        mock_user_service = MagicMock()
        mock_user_service.get_user_by_username = AsyncMock(return_value=mock_user)
        mock_user_service_class.return_value = mock_user_service

        request = RegisterRequest(
            username="testuser",
            email="another@example.com",
            password="SecurePass123!"
        )

        with pytest.raises(HTTPException) as exc_info:
            await register(request, mock_session)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.jwt_service')
    async def test_refresh_token_function_success(
        self, mock_jwt_service, mock_user_service_class, mock_user, mock_session
    ):
        """Test refresh token function directly."""
        mock_user_service = MagicMock()
        mock_user_service.get_user_by_id = AsyncMock(return_value=mock_user)
        mock_user_service_class.return_value = mock_user_service

        mock_jwt_service.verify_token.return_value = {
            "sub": str(mock_user.id),
            "type": "refresh"
        }
        mock_jwt_service.revoke_token = AsyncMock()
        mock_jwt_service.create_access_token.return_value = "new_access_token"
        mock_jwt_service.create_refresh_token.return_value = "new_refresh_token"

        request = RefreshTokenRequest(refresh_token="old_refresh_token")
        result = await refresh_token(request, mock_session)

        assert result.access_token == "new_access_token"
        assert result.refresh_token == "new_refresh_token"

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.jwt_service')
    async def test_refresh_token_function_invalid_type(
        self, mock_jwt_service, mock_session
    ):
        """Test refresh token with wrong token type."""
        mock_jwt_service.verify_token.return_value = {
            "sub": "user_id",
            "type": "access"  # Wrong type
        }

        request = RefreshTokenRequest(refresh_token="access_token")

        with pytest.raises(HTTPException) as exc_info:
            await refresh_token(request, mock_session)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.jwt_service')
    @patch('dotmac.platform.auth.router.session_manager')
    async def test_logout_function_success(self, mock_session_manager, mock_jwt_service):
        """Test logout function directly."""
        mock_jwt_service.verify_token.return_value = {"sub": "user123"}
        mock_jwt_service.revoke_token = AsyncMock()
        mock_session_manager.delete_user_sessions = AsyncMock(return_value=3)

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid_token")
        result = await logout(credentials)

        assert result["message"] == "Logged out successfully"
        assert result["sessions_deleted"] == 3

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.jwt_service')
    async def test_verify_token_function_success(self, mock_jwt_service):
        """Test verify token function directly."""
        mock_jwt_service.verify_token.return_value = {
            "sub": "user123",
            "username": "testuser",
            "roles": ["user", "admin"]
        }

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid_token")
        result = await verify_token(credentials)

        assert result["valid"] is True
        assert result["user_id"] == "user123"
        assert result["username"] == "testuser"

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.jwt_service')
    async def test_verify_token_function_invalid(self, mock_jwt_service):
        """Test verify token with invalid token."""
        mock_jwt_service.verify_token.side_effect = Exception("Token expired")

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="expired_token")

        with pytest.raises(HTTPException) as exc_info:
            await verify_token(credentials)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.get_auth_email_service')
    async def test_request_password_reset_function(
        self, mock_email_service, mock_user_service_class, mock_user, mock_session
    ):
        """Test password reset request function."""
        mock_user_service = MagicMock()
        mock_user_service.get_user_by_email = AsyncMock(return_value=mock_user)
        mock_user_service_class.return_value = mock_user_service

        mock_email = MagicMock()
        mock_email.send_password_reset_email = MagicMock(return_value=("sent", "token123"))
        mock_email_service.return_value = mock_email

        request = PasswordResetRequest(email="test@example.com")
        result = await request_password_reset(request, mock_session)

        assert "password reset link has been sent" in result["message"]

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.get_auth_email_service')
    @patch('dotmac.platform.auth.router.hash_password')
    async def test_confirm_password_reset_function(
        self, mock_hash_password, mock_email_service,
        mock_user_service_class, mock_user, mock_session
    ):
        """Test confirm password reset function."""
        mock_user_service = MagicMock()
        mock_user_service.get_user_by_email = AsyncMock(return_value=mock_user)
        mock_user_service_class.return_value = mock_user_service

        mock_email = MagicMock()
        mock_email.verify_reset_token = MagicMock(return_value="test@example.com")
        mock_email.send_password_reset_success_email = MagicMock()
        mock_email_service.return_value = mock_email

        mock_hash_password.return_value = "new_hashed_password"

        request = PasswordResetConfirm(token="valid_token", new_password="NewSecurePass123!")
        result = await confirm_password_reset(request, mock_session)

        assert "Password has been reset successfully" in result["message"]

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.jwt_service')
    async def test_get_current_user_function_success(
        self, mock_jwt_service, mock_user_service_class, mock_user, mock_session
    ):
        """Test get current user function directly."""
        mock_user_service = MagicMock()
        mock_user_service.get_user_by_id = AsyncMock(return_value=mock_user)
        mock_user_service_class.return_value = mock_user_service

        mock_jwt_service.verify_token.return_value = {"sub": str(mock_user.id)}

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid_token")
        result = await get_current_user(credentials, mock_session)

        assert result["id"] == str(mock_user.id)
        assert result["username"] == "testuser"
        assert result["email"] == "test@example.com"

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.jwt_service')
    async def test_get_current_user_function_not_found(
        self, mock_jwt_service, mock_user_service_class, mock_session
    ):
        """Test get current user when user not found."""
        mock_user_service = MagicMock()
        mock_user_service.get_user_by_id = AsyncMock(return_value=None)
        mock_user_service_class.return_value = mock_user_service

        mock_jwt_service.verify_token.return_value = {"sub": "deleted_user"}

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid_token")

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, mock_session)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_error_conditions(self, mock_session):
        """Test various error conditions."""
        # Test login with user not found
        with patch('dotmac.platform.auth.router.UserService') as mock_service:
            mock_user_service = MagicMock()
            mock_user_service.get_user_by_username = AsyncMock(return_value=None)
            mock_user_service.get_user_by_email = AsyncMock(return_value=None)
            mock_service.return_value = mock_user_service

            request = LoginRequest(username="nonexistent", password="password123")

            with pytest.raises(HTTPException) as exc_info:
                await login(request, mock_session)

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

        # Test refresh with missing subject
        with patch('dotmac.platform.auth.router.jwt_service') as mock_jwt:
            mock_jwt.verify_token.return_value = {"type": "refresh"}  # Missing "sub"

            request = RefreshTokenRequest(refresh_token="invalid_token")

            with pytest.raises(HTTPException) as exc_info:
                await refresh_token(request, mock_session)

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

        # Test password reset with invalid token
        with patch('dotmac.platform.auth.router.get_auth_email_service') as mock_email_service:
            mock_email = MagicMock()
            mock_email.verify_reset_token = MagicMock(return_value=None)
            mock_email_service.return_value = mock_email

            request = PasswordResetConfirm(token="invalid_token", new_password="NewPass123!")

            with pytest.raises(HTTPException) as exc_info:
                await confirm_password_reset(request, mock_session)

            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST