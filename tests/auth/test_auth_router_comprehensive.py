"""
Comprehensive tests for Auth Router to achieve >90% coverage.

Tests all authentication endpoints including login, register, logout,
token refresh, password reset, and user info endpoints.
"""

import json
from datetime import datetime, timedelta, UTC
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.auth.router import (
    LoginRequest,
    RegisterRequest,
    RefreshTokenRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    TokenResponse,
    auth_router,
)
from dotmac.platform.user_management.models import User


@pytest.fixture
def mock_user():
    """Create a mock user for testing."""
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.username = "testuser"
    user.email = "test@example.com"
    user.password_hash = "$2b$12$LQv3c1yqBWVHLkqgqeHuYOqlJmP3LxWJYCbHyF8TtLFGhvKRLcChe"  # "password123"
    user.full_name = "Test User"
    user.roles = ["user"]
    user.is_active = True
    user.tenant_id = "tenant123"
    return user


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def mock_user_service():
    """Create a mock user service."""
    service = MagicMock()
    return service


@pytest.fixture
def mock_jwt_service():
    """Create a mock JWT service."""
    service = MagicMock()
    service.create_access_token.return_value = "access_token_123"
    service.create_refresh_token.return_value = "refresh_token_456"
    service.verify_token.return_value = {
        "sub": str(uuid4()),
        "username": "testuser",
        "email": "test@example.com",
        "roles": ["user"],
        "type": "access"
    }
    service.revoke_token = AsyncMock()
    return service


@pytest.fixture
def mock_session_manager():
    """Create a mock session manager."""
    manager = MagicMock()
    manager.create_session = AsyncMock(return_value="session_789")
    manager.delete_user_sessions = AsyncMock(return_value=2)
    return manager


@pytest.fixture
def mock_email_service():
    """Create a mock email service facade."""
    service = MagicMock()
    service.send_welcome_email = AsyncMock()
    service.send_password_reset_email = AsyncMock(return_value=("Email sent", "reset_token_123"))
    service.verify_reset_token = MagicMock(return_value="test@example.com")
    service.send_password_reset_success_email = AsyncMock()
    return service


class TestLoginEndpoint:
    """Test the /login endpoint."""

    @pytest.mark.asyncio
    async def test_login_success_with_username(
        self, mock_session, mock_user, mock_user_service, mock_jwt_service, mock_session_manager
    ):
        """Test successful login with username."""
        from dotmac.platform.auth.router import login

        # Setup mocks
        mock_user_service.get_user_by_username = AsyncMock(return_value=mock_user)
        mock_user_service.get_user_by_email = AsyncMock(return_value=None)

        with patch('dotmac.platform.auth.router.UserService', return_value=mock_user_service):
            with patch('dotmac.platform.auth.router.verify_password', return_value=True):
                with patch('dotmac.platform.auth.router.jwt_service', mock_jwt_service):
                    with patch('dotmac.platform.auth.router.session_manager', mock_session_manager):
                        request = LoginRequest(username="testuser", password="password123")
                        result = await login(request, mock_session)

                        assert isinstance(result, TokenResponse)
                        assert result.access_token == "access_token_123"
                        assert result.refresh_token == "refresh_token_456"
                        assert result.token_type == "bearer"
                        mock_session_manager.create_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_login_success_with_email(
        self, mock_session, mock_user, mock_user_service, mock_jwt_service, mock_session_manager
    ):
        """Test successful login with email."""
        from dotmac.platform.auth.router import login

        # Setup mocks - user not found by username, but found by email
        mock_user_service.get_user_by_username = AsyncMock(return_value=None)
        mock_user_service.get_user_by_email = AsyncMock(return_value=mock_user)

        with patch('dotmac.platform.auth.router.UserService', return_value=mock_user_service):
            with patch('dotmac.platform.auth.router.verify_password', return_value=True):
                with patch('dotmac.platform.auth.router.jwt_service', mock_jwt_service):
                    with patch('dotmac.platform.auth.router.session_manager', mock_session_manager):
                        request = LoginRequest(username="test@example.com", password="password123")
                        result = await login(request, mock_session)

                        assert isinstance(result, TokenResponse)
                        assert result.access_token == "access_token_123"

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(
        self, mock_session, mock_user, mock_user_service
    ):
        """Test login with invalid credentials."""
        from dotmac.platform.auth.router import login

        mock_user_service.get_user_by_username = AsyncMock(return_value=mock_user)
        mock_user_service.get_user_by_email = AsyncMock(return_value=None)

        with patch('dotmac.platform.auth.router.UserService', return_value=mock_user_service):
            with patch('dotmac.platform.auth.router.verify_password', return_value=False):
                request = LoginRequest(username="testuser", password="wrongpassword")

                with pytest.raises(HTTPException) as exc_info:
                    await login(request, mock_session)

                assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
                assert "Invalid username or password" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_login_user_not_found(
        self, mock_session, mock_user_service
    ):
        """Test login when user is not found."""
        from dotmac.platform.auth.router import login

        mock_user_service.get_user_by_username = AsyncMock(return_value=None)
        mock_user_service.get_user_by_email = AsyncMock(return_value=None)

        with patch('dotmac.platform.auth.router.UserService', return_value=mock_user_service):
            request = LoginRequest(username="nonexistent", password="password123")

            with pytest.raises(HTTPException) as exc_info:
                await login(request, mock_session)

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_login_inactive_user(
        self, mock_session, mock_user, mock_user_service
    ):
        """Test login with inactive user."""
        from dotmac.platform.auth.router import login

        mock_user.is_active = False
        mock_user_service.get_user_by_username = AsyncMock(return_value=mock_user)

        with patch('dotmac.platform.auth.router.UserService', return_value=mock_user_service):
            with patch('dotmac.platform.auth.router.verify_password', return_value=True):
                request = LoginRequest(username="testuser", password="password123")

                with pytest.raises(HTTPException) as exc_info:
                    await login(request, mock_session)

                assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
                assert "Account is disabled" in exc_info.value.detail


class TestRegisterEndpoint:
    """Test the /register endpoint."""

    @pytest.mark.asyncio
    async def test_register_success(
        self, mock_session, mock_user, mock_user_service, mock_jwt_service,
        mock_session_manager
    ):
        """Test successful user registration."""
        from dotmac.platform.auth.router import register

        mock_user_service.get_user_by_username = AsyncMock(return_value=None)
        mock_user_service.get_user_by_email = AsyncMock(return_value=None)
        mock_user_service.create_user = AsyncMock(return_value=mock_user)

        # Properly mock the facade
        mock_email_facade = MagicMock()
        mock_email_facade.send_welcome_email = AsyncMock()

        with patch('dotmac.platform.auth.router.UserService', return_value=mock_user_service):
            with patch('dotmac.platform.auth.router.jwt_service', mock_jwt_service):
                with patch('dotmac.platform.auth.router.session_manager', mock_session_manager):
                    with patch('dotmac.platform.auth.router.get_auth_email_service', return_value=mock_email_facade):
                        request = RegisterRequest(
                            username="newuser",
                            email="new@example.com",
                            password="password123",
                            full_name="New User"
                        )
                        # Mock request and response objects with proper attributes
                        mock_request = MagicMock()
                        mock_request.client.host = "127.0.0.1"
                        mock_request.headers.get.return_value = "test-user-agent"
                        mock_response = MagicMock()
                        result = await register(request, mock_request, mock_response, mock_session)

                        assert isinstance(result, TokenResponse)
                        assert result.access_token == "access_token_123"
                        mock_user_service.create_user.assert_called_once()
                        mock_email_facade.send_welcome_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_username_exists(
        self, mock_session, mock_user, mock_user_service
    ):
        """Test registration with existing username."""
        from dotmac.platform.auth.router import register

        mock_user_service.get_user_by_username = AsyncMock(return_value=mock_user)
        mock_user_service.get_user_by_email = AsyncMock(return_value=None)

        with patch('dotmac.platform.auth.router.UserService', return_value=mock_user_service):
            request = RegisterRequest(
                username="testuser",
                email="new@example.com",
                password="password123"
            )

            with pytest.raises(HTTPException) as exc_info:
                await register(request, mock_session)

            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            # Our security fix uses generic error message to prevent enumeration
            assert "Registration failed" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_register_email_exists(
        self, mock_session, mock_user, mock_user_service
    ):
        """Test registration with existing email."""
        from dotmac.platform.auth.router import register

        mock_user_service.get_user_by_username = AsyncMock(return_value=None)
        mock_user_service.get_user_by_email = AsyncMock(return_value=mock_user)

        with patch('dotmac.platform.auth.router.UserService', return_value=mock_user_service):
            request = RegisterRequest(
                username="newuser",
                email="test@example.com",
                password="password123"
            )

            with pytest.raises(HTTPException) as exc_info:
                await register(request, mock_session)

            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            # Our security fix uses generic error message to prevent enumeration
            assert "Registration failed" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_register_create_user_fails(
        self, mock_session, mock_user_service
    ):
        """Test registration when user creation fails."""
        from dotmac.platform.auth.router import register

        mock_user_service.get_user_by_username = AsyncMock(return_value=None)
        mock_user_service.get_user_by_email = AsyncMock(return_value=None)
        mock_user_service.create_user = AsyncMock(side_effect=Exception("Database error"))

        with patch('dotmac.platform.auth.router.UserService', return_value=mock_user_service):
            request = RegisterRequest(
                username="newuser",
                email="new@example.com",
                password="password123"
            )

            with pytest.raises(HTTPException) as exc_info:
                await register(request, mock_session)

            assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to create user" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_register_email_fails(
        self, mock_session, mock_user, mock_user_service, mock_jwt_service, mock_session_manager
    ):
        """Test registration when welcome email fails."""
        from dotmac.platform.auth.router import register

        mock_user_service.get_user_by_username = AsyncMock(return_value=None)
        mock_user_service.get_user_by_email = AsyncMock(return_value=None)
        mock_user_service.create_user = AsyncMock(return_value=mock_user)

        # Properly mock the facade
        mock_email_facade = MagicMock()
        mock_email_facade.send_welcome_email = AsyncMock(side_effect=Exception("Email error"))

        with patch('dotmac.platform.auth.router.UserService', return_value=mock_user_service):
            with patch('dotmac.platform.auth.router.jwt_service', mock_jwt_service):
                with patch('dotmac.platform.auth.router.session_manager', mock_session_manager):
                    with patch('dotmac.platform.auth.router.get_auth_email_service', return_value=mock_email_facade):
                        request = RegisterRequest(
                            username="newuser",
                            email="new@example.com",
                            password="password123"
                        )
                        # Should not raise exception even if email fails
                        # Mock request and response objects with proper attributes
                        mock_request = MagicMock()
                        mock_request.client.host = "127.0.0.1"
                        mock_request.headers.get.return_value = "test-user-agent"
                        mock_response = MagicMock()
                        result = await register(request, mock_request, mock_response, mock_session)
                        assert isinstance(result, TokenResponse)


class TestRefreshTokenEndpoint:
    """Test the /refresh endpoint."""

    @pytest.mark.asyncio
    async def test_refresh_token_success(
        self, mock_session, mock_user, mock_user_service, mock_jwt_service
    ):
        """Test successful token refresh."""
        from dotmac.platform.auth.router import refresh_token

        mock_jwt_service.verify_token.return_value = {
            "sub": str(mock_user.id),
            "type": "refresh"
        }
        mock_user_service.get_user_by_id = AsyncMock(return_value=mock_user)

        with patch('dotmac.platform.auth.router.UserService', return_value=mock_user_service):
            with patch('dotmac.platform.auth.router.jwt_service', mock_jwt_service):
                request = RefreshTokenRequest(refresh_token="refresh_token_456")
                result = await refresh_token(request, mock_session)

                assert isinstance(result, TokenResponse)
                assert result.access_token == "access_token_123"
                mock_jwt_service.revoke_token.assert_called_once_with("refresh_token_456")

    @pytest.mark.asyncio
    async def test_refresh_token_invalid_type(
        self, mock_session, mock_jwt_service
    ):
        """Test refresh with non-refresh token."""
        from dotmac.platform.auth.router import refresh_token

        mock_jwt_service.verify_token.return_value = {
            "sub": "user123",
            "type": "access"  # Wrong token type
        }

        with patch('dotmac.platform.auth.router.jwt_service', mock_jwt_service):
            request = RefreshTokenRequest(refresh_token="access_token_123")

            with pytest.raises(HTTPException) as exc_info:
                await refresh_token(request, mock_session)

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Invalid token type" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_refresh_token_no_subject(
        self, mock_session, mock_jwt_service
    ):
        """Test refresh with token missing subject."""
        from dotmac.platform.auth.router import refresh_token

        mock_jwt_service.verify_token.return_value = {
            "type": "refresh"
            # Missing 'sub' field
        }

        with patch('dotmac.platform.auth.router.jwt_service', mock_jwt_service):
            request = RefreshTokenRequest(refresh_token="refresh_token_456")

            with pytest.raises(HTTPException) as exc_info:
                await refresh_token(request, mock_session)

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Invalid refresh token" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_refresh_token_user_not_found(
        self, mock_session, mock_user_service, mock_jwt_service
    ):
        """Test refresh when user not found."""
        from dotmac.platform.auth.router import refresh_token

        mock_jwt_service.verify_token.return_value = {
            "sub": "user123",
            "type": "refresh"
        }
        mock_user_service.get_user_by_id = AsyncMock(return_value=None)

        with patch('dotmac.platform.auth.router.UserService', return_value=mock_user_service):
            with patch('dotmac.platform.auth.router.jwt_service', mock_jwt_service):
                request = RefreshTokenRequest(refresh_token="refresh_token_456")

                with pytest.raises(HTTPException) as exc_info:
                    await refresh_token(request, mock_session)

                assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
                assert "User not found or disabled" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_refresh_token_revoke_fails(
        self, mock_session, mock_user, mock_user_service, mock_jwt_service
    ):
        """Test refresh when token revocation fails."""
        from dotmac.platform.auth.router import refresh_token

        mock_jwt_service.verify_token.return_value = {
            "sub": str(mock_user.id),
            "type": "refresh"
        }
        mock_jwt_service.revoke_token = AsyncMock(side_effect=Exception("Redis error"))
        mock_user_service.get_user_by_id = AsyncMock(return_value=mock_user)

        with patch('dotmac.platform.auth.router.UserService', return_value=mock_user_service):
            with patch('dotmac.platform.auth.router.jwt_service', mock_jwt_service):
                request = RefreshTokenRequest(refresh_token="refresh_token_456")
                # Should still succeed even if revocation fails
                result = await refresh_token(request, mock_session)
                assert isinstance(result, TokenResponse)

    @pytest.mark.asyncio
    async def test_refresh_token_invalid_token(
        self, mock_session, mock_jwt_service
    ):
        """Test refresh with invalid token."""
        from dotmac.platform.auth.router import refresh_token

        mock_jwt_service.verify_token.side_effect = Exception("Invalid token")

        with patch('dotmac.platform.auth.router.jwt_service', mock_jwt_service):
            request = RefreshTokenRequest(refresh_token="invalid_token")

            with pytest.raises(HTTPException) as exc_info:
                await refresh_token(request, mock_session)

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Invalid or expired refresh token" in exc_info.value.detail


class TestLogoutEndpoint:
    """Test the /logout endpoint."""

    @pytest.mark.asyncio
    async def test_logout_success(
        self, mock_jwt_service, mock_session_manager
    ):
        """Test successful logout."""
        from dotmac.platform.auth.router import logout
        from fastapi.security import HTTPAuthorizationCredentials

        mock_jwt_service.verify_token.return_value = {
            "sub": "user123"
        }

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="access_token_123"
        )

        with patch('dotmac.platform.auth.router.jwt_service', mock_jwt_service):
            with patch('dotmac.platform.auth.router.session_manager', mock_session_manager):
                result = await logout(credentials)

                assert result["message"] == "Logged out successfully"
                assert result["sessions_deleted"] == 2
                mock_jwt_service.revoke_token.assert_called_once()
                mock_session_manager.delete_user_sessions.assert_called_once()

    @pytest.mark.asyncio
    async def test_logout_no_user_id(
        self, mock_jwt_service
    ):
        """Test logout when token has no user ID."""
        from dotmac.platform.auth.router import logout
        from fastapi.security import HTTPAuthorizationCredentials

        mock_jwt_service.verify_token.return_value = {}  # No 'sub' field

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="access_token_123"
        )

        with patch('dotmac.platform.auth.router.jwt_service', mock_jwt_service):
            result = await logout(credentials)
            assert result["message"] == "Logout completed"

    @pytest.mark.asyncio
    async def test_logout_exception(
        self, mock_jwt_service
    ):
        """Test logout with exception."""
        from dotmac.platform.auth.router import logout
        from fastapi.security import HTTPAuthorizationCredentials

        mock_jwt_service.verify_token.side_effect = Exception("Token error")
        mock_jwt_service.revoke_token = AsyncMock()

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid_token"
        )

        with patch('dotmac.platform.auth.router.jwt_service', mock_jwt_service):
            result = await logout(credentials)
            assert result["message"] == "Logout completed"
            # Should still try to revoke token
            mock_jwt_service.revoke_token.assert_called_once()


class TestVerifyEndpoint:
    """Test the /verify endpoint."""

    @pytest.mark.asyncio
    async def test_verify_token_success(
        self, mock_jwt_service
    ):
        """Test successful token verification."""
        from dotmac.platform.auth.router import verify_token
        from fastapi.security import HTTPAuthorizationCredentials

        mock_jwt_service.verify_token.return_value = {
            "sub": "user123",
            "username": "testuser",
            "roles": ["user", "admin"]
        }

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="access_token_123"
        )

        with patch('dotmac.platform.auth.router.jwt_service', mock_jwt_service):
            result = await verify_token(credentials)

            assert result["valid"] is True
            assert result["user_id"] == "user123"
            assert result["username"] == "testuser"
            assert result["roles"] == ["user", "admin"]

    @pytest.mark.asyncio
    async def test_verify_token_invalid(
        self, mock_jwt_service
    ):
        """Test verification with invalid token."""
        from dotmac.platform.auth.router import verify_token
        from fastapi.security import HTTPAuthorizationCredentials

        mock_jwt_service.verify_token.side_effect = Exception("Invalid token")

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid_token"
        )

        with patch('dotmac.platform.auth.router.jwt_service', mock_jwt_service):
            with pytest.raises(HTTPException) as exc_info:
                await verify_token(credentials)

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Invalid or expired token" in exc_info.value.detail


class TestPasswordResetEndpoints:
    """Test password reset endpoints."""

    @pytest.mark.asyncio
    async def test_request_password_reset_success(
        self, mock_session, mock_user, mock_user_service, mock_email_service
    ):
        """Test successful password reset request."""
        from dotmac.platform.auth.router import request_password_reset

        mock_user_service.get_user_by_email = AsyncMock(return_value=mock_user)

        with patch('dotmac.platform.auth.router.UserService', return_value=mock_user_service):
            with patch('dotmac.platform.auth.router.get_auth_email_service', return_value=mock_email_service):
                request = PasswordResetRequest(email="test@example.com")
                result = await request_password_reset(request, mock_session)

                assert "password reset link has been sent" in result["message"]
                mock_email_service.send_password_reset_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_request_password_reset_user_not_found(
        self, mock_session, mock_user_service
    ):
        """Test password reset request for non-existent user."""
        from dotmac.platform.auth.router import request_password_reset

        mock_user_service.get_user_by_email = AsyncMock(return_value=None)

        with patch('dotmac.platform.auth.router.UserService', return_value=mock_user_service):
            request = PasswordResetRequest(email="nonexistent@example.com")
            result = await request_password_reset(request, mock_session)

            # Should still return success to prevent email enumeration
            assert "password reset link has been sent" in result["message"]

    @pytest.mark.asyncio
    async def test_request_password_reset_email_fails(
        self, mock_session, mock_user, mock_user_service
    ):
        """Test password reset when email sending fails."""
        from dotmac.platform.auth.router import request_password_reset

        mock_user_service.get_user_by_email = AsyncMock(return_value=mock_user)
        mock_email_service = MagicMock()
        mock_email_service.send_password_reset_email.side_effect = Exception("Email error")

        with patch('dotmac.platform.auth.router.UserService', return_value=mock_user_service):
            with patch('dotmac.platform.auth.router.get_auth_email_service', return_value=mock_email_service):
                request = PasswordResetRequest(email="test@example.com")
                result = await request_password_reset(request, mock_session)

                # Should still return success
                assert "password reset link has been sent" in result["message"]

    @pytest.mark.asyncio
    async def test_confirm_password_reset_success(
        self, mock_session, mock_user, mock_user_service, mock_email_service
    ):
        """Test successful password reset confirmation."""
        from dotmac.platform.auth.router import confirm_password_reset

        mock_user_service.get_user_by_email = AsyncMock(return_value=mock_user)

        with patch('dotmac.platform.auth.router.UserService', return_value=mock_user_service):
            with patch('dotmac.platform.auth.router.get_auth_email_service', return_value=mock_email_service):
                with patch('dotmac.platform.auth.router.hash_password', return_value="new_hash"):
                    request = PasswordResetConfirm(
                        token="reset_token_123",
                        new_password="newpassword123"
                    )
                    result = await confirm_password_reset(request, mock_session)

                    assert "Password has been reset successfully" in result["message"]
                    mock_session.commit.assert_called_once()
                    mock_email_service.send_password_reset_success_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_confirm_password_reset_invalid_token(
        self, mock_session, mock_email_service
    ):
        """Test password reset confirmation with invalid token."""
        from dotmac.platform.auth.router import confirm_password_reset

        mock_email_service.verify_reset_token.return_value = None

        with patch('dotmac.platform.auth.router.get_auth_email_service', return_value=mock_email_service):
            request = PasswordResetConfirm(
                token="invalid_token",
                new_password="newpassword123"
            )

            with pytest.raises(HTTPException) as exc_info:
                await confirm_password_reset(request, mock_session)

            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert "Invalid or expired reset token" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_confirm_password_reset_user_not_found(
        self, mock_session, mock_user_service, mock_email_service
    ):
        """Test password reset confirmation when user not found."""
        from dotmac.platform.auth.router import confirm_password_reset

        mock_user_service.get_user_by_email = AsyncMock(return_value=None)

        with patch('dotmac.platform.auth.router.UserService', return_value=mock_user_service):
            with patch('dotmac.platform.auth.router.get_auth_email_service', return_value=mock_email_service):
                request = PasswordResetConfirm(
                    token="reset_token_123",
                    new_password="newpassword123"
                )

                with pytest.raises(HTTPException) as exc_info:
                    await confirm_password_reset(request, mock_session)

                assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
                assert "User not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_confirm_password_reset_commit_fails(
        self, mock_session, mock_user, mock_user_service, mock_email_service
    ):
        """Test password reset when database commit fails."""
        from dotmac.platform.auth.router import confirm_password_reset

        mock_user_service.get_user_by_email = AsyncMock(return_value=mock_user)
        mock_session.commit = AsyncMock(side_effect=Exception("Database error"))

        with patch('dotmac.platform.auth.router.UserService', return_value=mock_user_service):
            with patch('dotmac.platform.auth.router.get_auth_email_service', return_value=mock_email_service):
                with patch('dotmac.platform.auth.router.hash_password', return_value="new_hash"):
                    request = PasswordResetConfirm(
                        token="reset_token_123",
                        new_password="newpassword123"
                    )

                    with pytest.raises(HTTPException) as exc_info:
                        await confirm_password_reset(request, mock_session)

                    assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                    assert "Failed to reset password" in exc_info.value.detail
                    mock_session.rollback.assert_called_once()


class TestGetCurrentUserEndpoint:
    """Test the /me endpoint."""

    @pytest.mark.asyncio
    async def test_get_current_user_success(
        self, mock_session, mock_user, mock_user_service, mock_jwt_service
    ):
        """Test successful get current user."""
        from dotmac.platform.auth.router import get_current_user
        from fastapi.security import HTTPAuthorizationCredentials

        mock_jwt_service.verify_token.return_value = {
            "sub": str(mock_user.id)
        }
        mock_user_service.get_user_by_id = AsyncMock(return_value=mock_user)

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="access_token_123"
        )

        with patch('dotmac.platform.auth.router.UserService', return_value=mock_user_service):
            with patch('dotmac.platform.auth.router.jwt_service', mock_jwt_service):
                result = await get_current_user(credentials, mock_session)

                assert result["id"] == str(mock_user.id)
                assert result["username"] == "testuser"
                assert result["email"] == "test@example.com"
                assert result["roles"] == ["user"]
                assert result["is_active"] is True

    @pytest.mark.asyncio
    async def test_get_current_user_no_subject(
        self, mock_session, mock_jwt_service
    ):
        """Test get current user with token missing subject."""
        from dotmac.platform.auth.router import get_current_user
        from fastapi.security import HTTPAuthorizationCredentials

        mock_jwt_service.verify_token.return_value = {}  # No 'sub' field

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="access_token_123"
        )

        with patch('dotmac.platform.auth.router.jwt_service', mock_jwt_service):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials, mock_session)

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Invalid token" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_not_found(
        self, mock_session, mock_user_service, mock_jwt_service
    ):
        """Test get current user when user not found."""
        from dotmac.platform.auth.router import get_current_user
        from fastapi.security import HTTPAuthorizationCredentials

        mock_jwt_service.verify_token.return_value = {
            "sub": "user123"
        }
        mock_user_service.get_user_by_id = AsyncMock(return_value=None)

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="access_token_123"
        )

        with patch('dotmac.platform.auth.router.UserService', return_value=mock_user_service):
            with patch('dotmac.platform.auth.router.jwt_service', mock_jwt_service):
                with pytest.raises(HTTPException) as exc_info:
                    await get_current_user(credentials, mock_session)

                assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
                assert "User not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(
        self, mock_session, mock_jwt_service
    ):
        """Test get current user with invalid token."""
        from dotmac.platform.auth.router import get_current_user
        from fastapi.security import HTTPAuthorizationCredentials

        mock_jwt_service.verify_token.side_effect = Exception("Invalid token")

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid_token"
        )

        with patch('dotmac.platform.auth.router.jwt_service', mock_jwt_service):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials, mock_session)

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Invalid or expired token" in exc_info.value.detail


class TestDependencyWrappers:
    """Test dependency wrapper functions."""

    @pytest.mark.asyncio
    async def test_get_auth_session(self):
        """Test get_auth_session wrapper."""
        from dotmac.platform.auth.router import get_auth_session

        mock_session = AsyncMock()

        async def mock_get_session():
            yield mock_session

        with patch('dotmac.platform.auth.router.get_session_dependency', mock_get_session):
            async for session in get_auth_session():
                assert session == mock_session
                break