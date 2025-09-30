"""Comprehensive tests for auth router to achieve >90% coverage."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import uuid

from dotmac.platform.auth.router import (
    LoginRequest,
    RegisterRequest,
    RefreshTokenRequest,
    TokenResponse,
    auth_router,
)
from dotmac.platform.user_management.models import User


@pytest.fixture
def mock_session():
    """Create mock async session."""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def mock_user():
    """Create mock user object."""
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.username = "testuser"
    user.email = "test@example.com"
    user.password_hash = "hashed_password"
    user.is_active = True
    user.roles = ["user"]
    user.tenant_id = "test-tenant"
    user.full_name = "Test User"
    return user


@pytest.fixture
def test_client():
    """Create test client for the auth router."""
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(auth_router, prefix="/auth")

    return TestClient(app)


class TestLoginEndpoint:
    """Test login endpoint."""

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.get_session_dependency')
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.verify_password')
    @patch('dotmac.platform.auth.router.jwt_service')
    @patch('dotmac.platform.auth.router.session_manager')
    async def test_login_success_with_username(
        self,
        mock_session_manager,
        mock_jwt_service,
        mock_verify_password,
        mock_user_service_class,
        mock_get_session,
        mock_session,
        mock_user,
        test_client,
    ):
        """Test successful login with username."""
        # Setup mocks
        async def mock_session_generator():
            yield mock_session
        mock_get_session.return_value = mock_session_generator()
        mock_user_service = AsyncMock()
        mock_user_service.get_user_by_username.return_value = mock_user
        mock_user_service_class.return_value = mock_user_service
        mock_verify_password.return_value = True
        mock_jwt_service.create_access_token.return_value = "access_token"
        mock_jwt_service.create_refresh_token.return_value = "refresh_token"
        mock_session_manager.create_session = AsyncMock()

        # Make request
        response = test_client.post(
            "/auth/login",
            json={"username": "testuser", "password": "password123"}
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "access_token"
        assert data["refresh_token"] == "refresh_token"
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

        # Verify mocks called
        mock_user_service.get_user_by_username.assert_called_once_with("testuser")
        mock_verify_password.assert_called_once_with("password123", "hashed_password")
        mock_jwt_service.create_access_token.assert_called_once()
        mock_jwt_service.create_refresh_token.assert_called_once()
        mock_session_manager.create_session.assert_called_once()

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.get_session_dependency')
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.verify_password')
    async def test_login_success_with_email(
        self,
        mock_verify_password,
        mock_user_service_class,
        mock_get_session,
        mock_session,
        mock_user,
        test_client,
    ):
        """Test successful login with email."""
        # Setup mocks
        async def mock_session_generator():
            yield mock_session
        mock_get_session.return_value = mock_session_generator()
        mock_user_service = AsyncMock()
        mock_user_service.get_user_by_username.return_value = None
        mock_user_service.get_user_by_email.return_value = mock_user
        mock_user_service_class.return_value = mock_user_service
        mock_verify_password.return_value = True

        with patch('dotmac.platform.auth.router.jwt_service') as mock_jwt:
            with patch('dotmac.platform.auth.router.session_manager') as mock_session_mgr:
                mock_jwt.create_access_token.return_value = "access_token"
                mock_jwt.create_refresh_token.return_value = "refresh_token"
                mock_session_mgr.create_session = AsyncMock()
                response = test_client.post(
                    "/auth/login",
                    json={"username": "test@example.com", "password": "password123"}
                )

        assert response.status_code == 200
        mock_user_service.get_user_by_email.assert_called_once_with("test@example.com")

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.get_session_dependency')
    @patch('dotmac.platform.auth.router.UserService')
    async def test_login_invalid_credentials(
        self,
        mock_user_service_class,
        mock_get_session,
        mock_session,
        test_client,
    ):
        """Test login with invalid credentials."""
        # Setup mocks
        async def mock_session_generator():
            yield mock_session
        mock_get_session.return_value = mock_session_generator()
        mock_user_service = AsyncMock()
        mock_user_service.get_user_by_username.return_value = None
        mock_user_service.get_user_by_email.return_value = None
        mock_user_service_class.return_value = mock_user_service

        response = test_client.post(
            "/auth/login",
            json={"username": "nonexistent", "password": "wrongpass"}
        )

        assert response.status_code == 401
        assert "Invalid username or password" in response.json()["detail"]

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.get_session_dependency')
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.verify_password')
    async def test_login_wrong_password(
        self,
        mock_verify_password,
        mock_user_service_class,
        mock_get_session,
        mock_session,
        mock_user,
        test_client,
    ):
        """Test login with wrong password."""
        # Setup mocks
        async def mock_session_generator():
            yield mock_session
        mock_get_session.return_value = mock_session_generator()
        mock_user_service = AsyncMock()
        mock_user_service.get_user_by_username.return_value = mock_user
        mock_user_service_class.return_value = mock_user_service
        mock_verify_password.return_value = False

        response = test_client.post(
            "/auth/login",
            json={"username": "testuser", "password": "wrongpass"}
        )

        assert response.status_code == 401
        assert "Invalid username or password" in response.json()["detail"]

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.get_session_dependency')
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.verify_password')
    async def test_login_inactive_user(
        self,
        mock_verify_password,
        mock_user_service_class,
        mock_get_session,
        mock_session,
        mock_user,
        test_client,
    ):
        """Test login with inactive user account."""
        # Setup mocks
        async def mock_session_generator():
            yield mock_session
        mock_get_session.return_value = mock_session_generator()
        mock_user.is_active = False
        mock_user_service = AsyncMock()
        mock_user_service.get_user_by_username.return_value = mock_user
        mock_user_service_class.return_value = mock_user_service
        mock_verify_password.return_value = True

        response = test_client.post(
            "/auth/login",
            json={"username": "testuser", "password": "password123"}
        )

        assert response.status_code == 403
        assert "Account is disabled" in response.json()["detail"]


class TestRegisterEndpoint:
    """Test register endpoint."""

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.get_session_dependency')
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.jwt_service')
    @patch('dotmac.platform.auth.router.session_manager')
    async def test_register_success(
        self,
        mock_session_manager,
        mock_jwt_service,
        mock_user_service_class,
        mock_get_session,
        mock_session,
        mock_user,
        test_client,
    ):
        """Test successful user registration."""
        # Setup mocks
        async def mock_session_generator():
            yield mock_session
        mock_get_session.return_value = mock_session_generator()
        mock_user_service = AsyncMock()
        mock_user_service.get_user_by_username.return_value = None
        mock_user_service.get_user_by_email.return_value = None
        mock_user_service.create_user.return_value = mock_user
        mock_user_service_class.return_value = mock_user_service
        mock_jwt_service.create_access_token.return_value = "access_token"
        mock_jwt_service.create_refresh_token.return_value = "refresh_token"
        mock_session_manager.create_session = AsyncMock()

        # Make request
        response = test_client.post(
            "/auth/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "password123",
                "full_name": "New User"
            }
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "access_token"
        assert data["refresh_token"] == "refresh_token"
        assert data["token_type"] == "bearer"

        # Verify user created with correct params (default role is 'guest')
        mock_user_service.create_user.assert_called_once_with(
            username="newuser",
            email="new@example.com",
            password="password123",
            full_name="New User",
            roles=["guest"],
            is_active=True
        )

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.get_session_dependency')
    @patch('dotmac.platform.auth.router.UserService')
    async def test_register_username_exists(
        self,
        mock_user_service_class,
        mock_get_session,
        mock_session,
        mock_user,
        test_client,
    ):
        """Test registration with existing username."""
        # Setup mocks
        async def mock_session_generator():
            yield mock_session
        mock_get_session.return_value = mock_session_generator()
        mock_user_service = AsyncMock()
        mock_user_service.get_user_by_username.return_value = mock_user
        mock_user_service_class.return_value = mock_user_service

        response = test_client.post(
            "/auth/register",
            json={
                "username": "existinguser",
                "email": "new@example.com",
                "password": "password123"
            }
        )

        assert response.status_code == 400
        assert "Registration failed. Please check your input and try again." == response.json()["detail"]

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.get_session_dependency')
    @patch('dotmac.platform.auth.router.UserService')
    async def test_register_email_exists(
        self,
        mock_user_service_class,
        mock_get_session,
        mock_session,
        mock_user,
        test_client,
    ):
        """Test registration with existing email."""
        # Setup mocks
        async def mock_session_generator():
            yield mock_session
        mock_get_session.return_value = mock_session_generator()
        mock_user_service = AsyncMock()
        mock_user_service.get_user_by_username.return_value = None
        mock_user_service.get_user_by_email.return_value = mock_user
        mock_user_service_class.return_value = mock_user_service

        response = test_client.post(
            "/auth/register",
            json={
                "username": "newuser",
                "email": "existing@example.com",
                "password": "password123"
            }
        )

        assert response.status_code == 400
        assert "Registration failed. Please check your input and try again." == response.json()["detail"]

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.get_session_dependency')
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.logger')
    async def test_register_create_user_failure(
        self,
        mock_logger,
        mock_user_service_class,
        mock_get_session,
        mock_session,
        test_client,
    ):
        """Test registration when user creation fails."""
        # Setup mocks
        async def mock_session_generator():
            yield mock_session
        mock_get_session.return_value = mock_session_generator()
        mock_user_service = AsyncMock()
        mock_user_service.get_user_by_username.return_value = None
        mock_user_service.get_user_by_email.return_value = None
        mock_user_service.create_user.side_effect = Exception("Database error")
        mock_user_service_class.return_value = mock_user_service

        response = test_client.post(
            "/auth/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "password123"
            }
        )

        assert response.status_code == 500
        assert "Failed to create user" in response.json()["detail"]
        mock_logger.error.assert_called_once()


class TestRefreshTokenEndpoint:
    """Test refresh token endpoint."""

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.get_session_dependency')
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.jwt_service')
    async def test_refresh_token_success(
        self,
        mock_jwt_service,
        mock_user_service_class,
        mock_get_session,
        mock_session,
        mock_user,
        test_client,
    ):
        """Test successful token refresh."""
        # Setup mocks
        async def mock_session_generator():
            yield mock_session
        mock_get_session.return_value = mock_session_generator()
        mock_user_service = AsyncMock()
        mock_user_service.get_user_by_id.return_value = mock_user
        mock_user_service_class.return_value = mock_user_service

        mock_jwt_service.verify_token.return_value = {
            "sub": str(mock_user.id),
            "type": "refresh"
        }
        mock_jwt_service.create_access_token.return_value = "new_access_token"
        mock_jwt_service.create_refresh_token.return_value = "new_refresh_token"

        # Make request
        response = test_client.post(
            "/auth/refresh",
            json={"refresh_token": "old_refresh_token"}
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "new_access_token"
        assert data["refresh_token"] == "new_refresh_token"
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.get_session_dependency')
    @patch('dotmac.platform.auth.router.jwt_service')
    async def test_refresh_token_invalid_type(
        self,
        mock_jwt_service,
        mock_get_session,
        mock_session,
        test_client,
    ):
        """Test refresh with wrong token type."""
        # Setup mocks
        async def mock_session_generator():
            yield mock_session
        mock_get_session.return_value = mock_session_generator()
        mock_jwt_service.verify_token.return_value = {
            "sub": "user_id",
            "type": "access"  # Wrong type
        }

        response = test_client.post(
            "/auth/refresh",
            json={"refresh_token": "access_token_instead"}
        )

        assert response.status_code == 401
        assert "Invalid token type" in response.json()["detail"]

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.get_session_dependency')
    @patch('dotmac.platform.auth.router.jwt_service')
    async def test_refresh_token_no_subject(
        self,
        mock_jwt_service,
        mock_get_session,
        mock_session,
        test_client,
    ):
        """Test refresh with token missing subject."""
        # Setup mocks
        async def mock_session_generator():
            yield mock_session
        mock_get_session.return_value = mock_session_generator()
        mock_jwt_service.verify_token.return_value = {
            "type": "refresh"
            # Missing "sub" field
        }

        response = test_client.post(
            "/auth/refresh",
            json={"refresh_token": "invalid_token"}
        )

        assert response.status_code == 401
        assert "Invalid refresh token" in response.json()["detail"]

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.get_session_dependency')
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.jwt_service')
    async def test_refresh_token_user_not_found(
        self,
        mock_jwt_service,
        mock_user_service_class,
        mock_get_session,
        mock_session,
        test_client,
    ):
        """Test refresh when user not found."""
        # Setup mocks
        async def mock_session_generator():
            yield mock_session
        mock_get_session.return_value = mock_session_generator()
        mock_user_service = AsyncMock()
        mock_user_service.get_user_by_id.return_value = None
        mock_user_service_class.return_value = mock_user_service

        mock_jwt_service.verify_token.return_value = {
            "sub": "nonexistent_user",
            "type": "refresh"
        }

        response = test_client.post(
            "/auth/refresh",
            json={"refresh_token": "valid_token"}
        )

        assert response.status_code == 401
        assert "User not found or disabled" in response.json()["detail"]

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.get_session_dependency')
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.jwt_service')
    async def test_refresh_token_inactive_user(
        self,
        mock_jwt_service,
        mock_user_service_class,
        mock_get_session,
        mock_session,
        mock_user,
        test_client,
    ):
        """Test refresh with inactive user."""
        # Setup mocks
        async def mock_session_generator():
            yield mock_session
        mock_get_session.return_value = mock_session_generator()
        mock_user.is_active = False
        mock_user_service = AsyncMock()
        mock_user_service.get_user_by_id.return_value = mock_user
        mock_user_service_class.return_value = mock_user_service

        mock_jwt_service.verify_token.return_value = {
            "sub": str(mock_user.id),
            "type": "refresh"
        }

        response = test_client.post(
            "/auth/refresh",
            json={"refresh_token": "valid_token"}
        )

        assert response.status_code == 401
        assert "User not found or disabled" in response.json()["detail"]

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.get_session_dependency')
    @patch('dotmac.platform.auth.router.jwt_service')
    @patch('dotmac.platform.auth.router.logger')
    async def test_refresh_token_invalid_token(
        self,
        mock_logger,
        mock_jwt_service,
        mock_get_session,
        mock_session,
        test_client,
    ):
        """Test refresh with invalid token."""
        # Setup mocks
        async def mock_session_generator():
            yield mock_session
        mock_get_session.return_value = mock_session_generator()
        mock_jwt_service.verify_token.side_effect = Exception("Invalid token")

        response = test_client.post(
            "/auth/refresh",
            json={"refresh_token": "invalid_token"}
        )

        assert response.status_code == 401
        assert "Invalid or expired refresh token" in response.json()["detail"]
        mock_logger.error.assert_called_once()


class TestLogoutEndpoint:
    """Test logout endpoint."""

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.jwt_service')
    @patch('dotmac.platform.auth.router.session_manager')
    async def test_logout_success(
        self,
        mock_session_manager,
        mock_jwt_service,
        test_client,
    ):
        """Test successful logout."""
        # Setup mocks
        mock_jwt_service.verify_token.return_value = {
            "sub": "user_id"
        }
        mock_jwt_service.revoke_token = AsyncMock(return_value=True)
        mock_session_manager.delete_user_sessions = AsyncMock(return_value=2)

        response = test_client.post(
            "/auth/logout",
            headers={"Authorization": "Bearer valid_token"}
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Logged out successfully"

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.jwt_service')
    @patch('dotmac.platform.auth.router.logger')
    async def test_logout_with_invalid_token(
        self,
        mock_logger,
        mock_jwt_service,
        test_client,
    ):
        """Test logout with invalid token."""
        # Setup mocks
        mock_jwt_service.verify_token.side_effect = Exception("Invalid token")

        response = test_client.post(
            "/auth/logout",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Logout completed"
        mock_logger.error.assert_called_once()


class TestVerifyEndpoint:
    """Test verify endpoint."""

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.jwt_service')
    async def test_verify_success(
        self,
        mock_jwt_service,
        test_client,
    ):
        """Test successful token verification."""
        # Setup mocks
        mock_jwt_service.verify_token.return_value = {
            "sub": "user_id",
            "username": "testuser",
            "roles": ["user", "admin"]
        }

        response = test_client.get(
            "/auth/verify",
            headers={"Authorization": "Bearer valid_token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["user_id"] == "user_id"
        assert data["username"] == "testuser"
        assert data["roles"] == ["user", "admin"]

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.jwt_service')
    async def test_verify_invalid_token(
        self,
        mock_jwt_service,
        test_client,
    ):
        """Test verification with invalid token."""
        # Setup mocks
        mock_jwt_service.verify_token.side_effect = Exception("Invalid token")

        response = test_client.get(
            "/auth/verify",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401
        assert "Invalid or expired token" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_verify_no_token(
        self,
        test_client,
    ):
        """Test verification without token."""
        response = test_client.get("/auth/verify")
        assert response.status_code == 403
        assert "Not authenticated" in response.json()["detail"]


class TestPasswordResetEndpoints:
    """Test password reset endpoints."""

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.get_session_dependency')
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.get_auth_email_service')
    async def test_password_reset_request_success(
        self,
        mock_email_service,
        mock_user_service_class,
        mock_get_session,
        mock_session,
        mock_user,
        test_client,
    ):
        """Test successful password reset request."""
        # Setup mocks
        async def mock_session_generator():
            yield mock_session
        mock_get_session.return_value = mock_session_generator()
        mock_user_service = AsyncMock()
        mock_user_service.get_user_by_email.return_value = mock_user
        mock_user_service_class.return_value = mock_user_service

        mock_email_svc = MagicMock()
        mock_email_svc.send_password_reset_email.return_value = ("success", "reset_token")
        mock_email_service.return_value = mock_email_svc

        response = test_client.post(
            "/auth/password-reset",
            json={"email": "test@example.com"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "reset link has been sent" in data["message"]
        mock_email_svc.send_password_reset_email.assert_called_once()

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.get_session_dependency')
    @patch('dotmac.platform.auth.router.UserService')
    async def test_password_reset_request_user_not_found(
        self,
        mock_user_service_class,
        mock_get_session,
        mock_session,
        test_client,
    ):
        """Test password reset request for non-existent user."""
        # Setup mocks
        async def mock_session_generator():
            yield mock_session
        mock_get_session.return_value = mock_session_generator()
        mock_user_service = AsyncMock()
        mock_user_service.get_user_by_email.return_value = None
        mock_user_service_class.return_value = mock_user_service

        response = test_client.post(
            "/auth/password-reset",
            json={"email": "nonexistent@example.com"}
        )

        # Should still return success to prevent email enumeration
        assert response.status_code == 200
        data = response.json()
        assert "reset link has been sent" in data["message"]

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.get_session_dependency')
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.get_auth_email_service')
    @patch('dotmac.platform.auth.router.logger')
    async def test_password_reset_request_email_failure(
        self,
        mock_logger,
        mock_email_service,
        mock_user_service_class,
        mock_get_session,
        mock_session,
        mock_user,
        test_client,
    ):
        """Test password reset when email sending fails."""
        # Setup mocks
        async def mock_session_generator():
            yield mock_session
        mock_get_session.return_value = mock_session_generator()
        mock_user_service = AsyncMock()
        mock_user_service.get_user_by_email.return_value = mock_user
        mock_user_service_class.return_value = mock_user_service

        mock_email_svc = MagicMock()
        mock_email_svc.send_password_reset_email.side_effect = Exception("Email error")
        mock_email_service.return_value = mock_email_svc

        response = test_client.post(
            "/auth/password-reset",
            json={"email": "test@example.com"}
        )

        # Should still return success even if email fails
        assert response.status_code == 200
        mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.get_session_dependency')
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.get_auth_email_service')
    @patch('dotmac.platform.auth.router.hash_password')
    async def test_password_reset_confirm_success(
        self,
        mock_hash_password,
        mock_email_service,
        mock_user_service_class,
        mock_get_session,
        mock_session,
        mock_user,
        test_client,
    ):
        """Test successful password reset confirmation."""
        # Setup mocks
        async def mock_session_generator():
            yield mock_session
        mock_get_session.return_value = mock_session_generator()
        mock_user_service = AsyncMock()
        mock_user_service.get_user_by_email.return_value = mock_user
        mock_user_service_class.return_value = mock_user_service

        mock_email_svc = MagicMock()
        mock_email_svc.verify_reset_token.return_value = "test@example.com"
        mock_email_svc.send_password_reset_success_email = MagicMock()
        mock_email_service.return_value = mock_email_svc

        mock_hash_password.return_value = "new_hashed_password"
        mock_session.commit = AsyncMock()

        response = test_client.post(
            "/auth/password-reset/confirm",
            json={
                "token": "valid_token",
                "new_password": "newpassword123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "reset successfully" in data["message"]
        mock_email_svc.verify_reset_token.assert_called_once_with("valid_token")
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.get_session_dependency')
    @patch('dotmac.platform.auth.router.get_auth_email_service')
    async def test_password_reset_confirm_invalid_token(
        self,
        mock_email_service,
        mock_get_session,
        mock_session,
        test_client,
    ):
        """Test password reset confirmation with invalid token."""
        # Setup mocks
        async def mock_session_generator():
            yield mock_session
        mock_get_session.return_value = mock_session_generator()

        mock_email_svc = MagicMock()
        mock_email_svc.verify_reset_token.return_value = None
        mock_email_service.return_value = mock_email_svc

        response = test_client.post(
            "/auth/password-reset/confirm",
            json={
                "token": "invalid_token",
                "new_password": "newpassword123"
            }
        )

        assert response.status_code == 400
        assert "Invalid or expired reset token" in response.json()["detail"]

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.get_session_dependency')
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.get_auth_email_service')
    async def test_password_reset_confirm_user_not_found(
        self,
        mock_email_service,
        mock_user_service_class,
        mock_get_session,
        mock_session,
        test_client,
    ):
        """Test password reset confirmation when user not found."""
        # Setup mocks
        async def mock_session_generator():
            yield mock_session
        mock_get_session.return_value = mock_session_generator()
        mock_user_service = AsyncMock()
        mock_user_service.get_user_by_email.return_value = None
        mock_user_service_class.return_value = mock_user_service

        mock_email_svc = MagicMock()
        mock_email_svc.verify_reset_token.return_value = "test@example.com"
        mock_email_service.return_value = mock_email_svc

        response = test_client.post(
            "/auth/password-reset/confirm",
            json={
                "token": "valid_token",
                "new_password": "newpassword123"
            }
        )

        assert response.status_code == 400
        assert "User not found" in response.json()["detail"]


class TestGetCurrentUserEndpoint:
    """Test /me endpoint."""

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.get_session_dependency')
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.jwt_service')
    async def test_get_current_user_success(
        self,
        mock_jwt_service,
        mock_user_service_class,
        mock_get_session,
        mock_session,
        mock_user,
        test_client,
    ):
        """Test successful current user retrieval."""
        # Setup mocks
        async def mock_session_generator():
            yield mock_session
        mock_get_session.return_value = mock_session_generator()
        mock_user_service = AsyncMock()
        mock_user_service.get_user_by_id.return_value = mock_user
        mock_user_service_class.return_value = mock_user_service

        mock_jwt_service.verify_token.return_value = {
            "sub": str(mock_user.id)
        }

        response = test_client.get(
            "/auth/me",
            headers={"Authorization": "Bearer valid_token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(mock_user.id)
        assert data["username"] == mock_user.username
        assert data["email"] == mock_user.email
        assert data["full_name"] == mock_user.full_name
        assert data["roles"] == mock_user.roles
        assert data["is_active"] == mock_user.is_active

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.get_session_dependency')
    @patch('dotmac.platform.auth.router.jwt_service')
    async def test_get_current_user_invalid_token(
        self,
        mock_jwt_service,
        mock_get_session,
        mock_session,
        test_client,
    ):
        """Test current user with invalid token."""
        # Setup mocks
        async def mock_session_generator():
            yield mock_session
        mock_get_session.return_value = mock_session_generator()
        mock_jwt_service.verify_token.side_effect = Exception("Invalid token")

        response = test_client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401
        assert "Invalid or expired token" in response.json()["detail"]

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.get_session_dependency')
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.jwt_service')
    async def test_get_current_user_no_subject(
        self,
        mock_jwt_service,
        mock_user_service_class,
        mock_get_session,
        mock_session,
        test_client,
    ):
        """Test current user when token has no subject."""
        # Setup mocks
        async def mock_session_generator():
            yield mock_session
        mock_get_session.return_value = mock_session_generator()
        mock_jwt_service.verify_token.return_value = {}  # No "sub" field

        response = test_client.get(
            "/auth/me",
            headers={"Authorization": "Bearer token_no_sub"}
        )

        assert response.status_code == 401
        assert "Invalid token" in response.json()["detail"]

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.get_session_dependency')
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.jwt_service')
    async def test_get_current_user_user_not_found(
        self,
        mock_jwt_service,
        mock_user_service_class,
        mock_get_session,
        mock_session,
        test_client,
    ):
        """Test current user when user not found in database."""
        # Setup mocks
        async def mock_session_generator():
            yield mock_session
        mock_get_session.return_value = mock_session_generator()
        mock_user_service = AsyncMock()
        mock_user_service.get_user_by_id.return_value = None
        mock_user_service_class.return_value = mock_user_service

        mock_jwt_service.verify_token.return_value = {
            "sub": "nonexistent_user_id"
        }

        response = test_client.get(
            "/auth/me",
            headers={"Authorization": "Bearer valid_token"}
        )

        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_current_user_no_token(self, test_client):
        """Test current user without authorization header."""
        response = test_client.get("/auth/me")
        assert response.status_code == 403
        assert "Not authenticated" in response.json()["detail"]


class TestRegisterWithWelcomeEmail:
    """Test register endpoint with email integration."""

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.get_session_dependency')
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.jwt_service')
    @patch('dotmac.platform.auth.router.session_manager')
    @patch('dotmac.platform.auth.router.get_auth_email_service')
    @patch('dotmac.platform.auth.router.logger')
    async def test_register_with_welcome_email_failure(
        self,
        mock_logger,
        mock_email_service,
        mock_session_manager,
        mock_jwt_service,
        mock_user_service_class,
        mock_get_session,
        mock_session,
        mock_user,
        test_client,
    ):
        """Test registration when welcome email sending fails."""
        # Setup mocks
        async def mock_session_generator():
            yield mock_session
        mock_get_session.return_value = mock_session_generator()
        mock_user_service = AsyncMock()
        mock_user_service.get_user_by_username.return_value = None
        mock_user_service.get_user_by_email.return_value = None
        mock_user_service.create_user.return_value = mock_user
        mock_user_service_class.return_value = mock_user_service

        mock_jwt_service.create_access_token.return_value = "access_token"
        mock_jwt_service.create_refresh_token.return_value = "refresh_token"
        mock_session_manager.create_session = AsyncMock()

        # Email service fails
        mock_email_facade = MagicMock()
        mock_email_facade.send_welcome_email = AsyncMock(side_effect=Exception("Email error"))
        mock_email_service.return_value = mock_email_facade

        response = test_client.post(
            "/auth/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "password123",
                "full_name": "New User"
            }
        )

        # Registration should still succeed even if email fails
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "access_token"

        # Should log warning but not fail
        mock_logger.warning.assert_called_once()


class TestRequestModels:
    """Test request/response models."""

    def test_login_request_model(self):
        """Test LoginRequest model."""
        request = LoginRequest(username="testuser", password="password123")
        assert request.username == "testuser"
        assert request.password == "password123"

    def test_register_request_model(self):
        """Test RegisterRequest model."""
        request = RegisterRequest(
            username="newuser",
            email="test@example.com",
            password="password123",
            full_name="Test User"
        )
        assert request.username == "newuser"
        assert request.email == "test@example.com"
        assert request.password == "password123"
        assert request.full_name == "Test User"

    def test_register_request_model_no_fullname(self):
        """Test RegisterRequest model without full_name."""
        request = RegisterRequest(
            username="newuser",
            email="test@example.com",
            password="password123"
        )
        assert request.full_name is None

    def test_token_response_model(self):
        """Test TokenResponse model."""
        response = TokenResponse(
            access_token="access",
            refresh_token="refresh",
            token_type="bearer",
            expires_in=3600
        )
        assert response.access_token == "access"
        assert response.refresh_token == "refresh"
        assert response.token_type == "bearer"
        assert response.expires_in == 3600

    def test_refresh_token_request_model(self):
        """Test RefreshTokenRequest model."""
        request = RefreshTokenRequest(refresh_token="refresh_token")
        assert request.refresh_token == "refresh_token"

    def test_password_reset_request_model(self):
        """Test PasswordResetRequest model."""
        from dotmac.platform.auth.router import PasswordResetRequest
        request = PasswordResetRequest(email="test@example.com")
        assert request.email == "test@example.com"

    def test_password_reset_confirm_model(self):
        """Test PasswordResetConfirm model."""
        from dotmac.platform.auth.router import PasswordResetConfirm
        request = PasswordResetConfirm(
            token="reset_token",
            new_password="newpassword123"
        )
        assert request.token == "reset_token"
        assert request.new_password == "newpassword123"