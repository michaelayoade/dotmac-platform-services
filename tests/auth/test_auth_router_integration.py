"""
Integration tests for Auth Router with real code execution.

These tests use FastAPI TestClient to execute the actual router code
and achieve high coverage by testing all endpoints and error paths.
"""

import json
from datetime import datetime, timedelta, UTC
from typing import Optional, Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from uuid import uuid4

import pytest
from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.auth.router import auth_router
from dotmac.platform.user_management.models import User


# Create test app
app = FastAPI()
app.include_router(auth_router, prefix="/auth")


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Create a mock user for testing."""
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.username = "testuser"
    user.email = "test@example.com"
    # This hash is for password "password123"
    user.password_hash = "$2b$12$LQv3c1yqBWVHLkqgqeHuYOqlJmP3LxWJYCbHyF8TtLFGhvKRLcChe"
    user.full_name = "Test User"
    user.roles = ["user", "admin"]
    user.is_active = True
    user.tenant_id = "tenant123"
    return user


@pytest.fixture
def mock_inactive_user():
    """Create an inactive mock user."""
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.username = "inactive"
    user.email = "inactive@example.com"
    user.password_hash = "$2b$12$LQv3c1yqBWVHLkqgqeHuYOqlJmP3LxWJYCbHyF8TtLFGhvKRLcChe"
    user.is_active = False
    user.roles = []
    return user


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def mock_user_service(mock_user):
    """Create a mock UserService."""
    service = MagicMock()
    service.get_user_by_username = AsyncMock(return_value=mock_user)
    service.get_user_by_email = AsyncMock(return_value=mock_user)
    service.get_user_by_id = AsyncMock(return_value=mock_user)
    service.create_user = AsyncMock(return_value=mock_user)
    return service


class TestLoginEndpoint:
    """Test /auth/login endpoint."""

    @patch('dotmac.platform.auth.router.get_auth_session')
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.jwt_service')
    @patch('dotmac.platform.auth.router.session_manager')
    def test_login_success_with_username(
        self, mock_session_manager, mock_jwt_service, mock_user_service_class,
        mock_get_session, client, mock_user, mock_user_service, mock_session
    ):
        """Test successful login with username."""
        # Setup mocks
        mock_get_session.return_value = mock_session
        mock_user_service_class.return_value = mock_user_service
        mock_jwt_service.create_access_token.return_value = "access_token_123"
        mock_jwt_service.create_refresh_token.return_value = "refresh_token_123"
        mock_session_manager.create_session = AsyncMock()

        # Make request
        response = client.post(
            "/auth/login",
            json={"username": "testuser", "password": "password123"}
        )

        # Assert response
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "access_token_123"
        assert data["refresh_token"] == "refresh_token_123"
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 900  # 15 * 60

        # Verify calls
        mock_user_service.get_user_by_username.assert_called_once_with("testuser")
        mock_jwt_service.create_access_token.assert_called_once()
        mock_jwt_service.create_refresh_token.assert_called_once()
        mock_session_manager.create_session.assert_called_once()

    @patch('dotmac.platform.auth.router.get_auth_session')
    @patch('dotmac.platform.auth.router.UserService')
    def test_login_success_with_email(
        self, mock_user_service_class, mock_get_session, client,
        mock_user, mock_session
    ):
        """Test successful login with email."""
        # Setup mocks
        mock_get_session.return_value = mock_session
        mock_user_service = MagicMock()
        mock_user_service.get_user_by_username = AsyncMock(return_value=None)
        mock_user_service.get_user_by_email = AsyncMock(return_value=mock_user)
        mock_user_service_class.return_value = mock_user_service

        with patch('dotmac.platform.auth.router.jwt_service') as mock_jwt:
            mock_jwt.create_access_token.return_value = "access_token"
            mock_jwt.create_refresh_token.return_value = "refresh_token"

            with patch('dotmac.platform.auth.router.session_manager') as mock_sm:
                mock_sm.create_session = AsyncMock()

                response = client.post(
                    "/auth/login",
                    json={"username": "test@example.com", "password": "password123"}
                )

                assert response.status_code == 200
                # Verify email lookup was used
                mock_user_service.get_user_by_email.assert_called_once_with("test@example.com")

    @patch('dotmac.platform.auth.router.get_auth_session')
    @patch('dotmac.platform.auth.router.UserService')
    def test_login_invalid_password(
        self, mock_user_service_class, mock_get_session, client,
        mock_user, mock_user_service, mock_session
    ):
        """Test login with invalid password."""
        mock_get_session.return_value = mock_session
        mock_user_service_class.return_value = mock_user_service

        response = client.post(
            "/auth/login",
            json={"username": "testuser", "password": "wrongpassword"}
        )

        assert response.status_code == 401
        assert "Invalid username or password" in response.json()["detail"]

    @patch('dotmac.platform.auth.router.get_auth_session')
    @patch('dotmac.platform.auth.router.UserService')
    def test_login_user_not_found(
        self, mock_user_service_class, mock_get_session, client, mock_session
    ):
        """Test login with non-existent user."""
        mock_get_session.return_value = mock_session
        mock_user_service = MagicMock()
        mock_user_service.get_user_by_username = AsyncMock(return_value=None)
        mock_user_service.get_user_by_email = AsyncMock(return_value=None)
        mock_user_service_class.return_value = mock_user_service

        response = client.post(
            "/auth/login",
            json={"username": "nonexistent", "password": "password123"}
        )

        assert response.status_code == 401
        assert "Invalid username or password" in response.json()["detail"]

    @patch('dotmac.platform.auth.router.get_auth_session')
    @patch('dotmac.platform.auth.router.UserService')
    def test_login_inactive_user(
        self, mock_user_service_class, mock_get_session, client,
        mock_inactive_user, mock_session
    ):
        """Test login with inactive user account."""
        mock_get_session.return_value = mock_session
        mock_user_service = MagicMock()
        mock_user_service.get_user_by_username = AsyncMock(return_value=mock_inactive_user)
        mock_user_service_class.return_value = mock_user_service

        response = client.post(
            "/auth/login",
            json={"username": "inactive", "password": "password123"}
        )

        assert response.status_code == 403
        assert "Account is disabled" in response.json()["detail"]


class TestRegisterEndpoint:
    """Test /auth/register endpoint."""

    @patch('dotmac.platform.auth.router.get_auth_session')
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.jwt_service')
    @patch('dotmac.platform.auth.router.session_manager')
    @patch('dotmac.platform.auth.router.get_auth_email_service')
    def test_register_success(
        self, mock_email_service, mock_session_manager, mock_jwt_service,
        mock_user_service_class, mock_get_session, client, mock_session
    ):
        """Test successful user registration."""
        # Setup mocks
        mock_get_session.return_value = mock_session

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

        # Make request
        response = client.post(
            "/auth/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "SecurePass123!",
                "full_name": "New User"
            }
        )

        # Assert response
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "access_token"
        assert data["refresh_token"] == "refresh_token"

        # Verify calls
        mock_user_service.create_user.assert_called_once()
        mock_facade.send_welcome_email.assert_called_once()

    @patch('dotmac.platform.auth.router.get_auth_session')
    @patch('dotmac.platform.auth.router.UserService')
    def test_register_username_exists(
        self, mock_user_service_class, mock_get_session, client,
        mock_user, mock_session
    ):
        """Test registration with existing username."""
        mock_get_session.return_value = mock_session
        mock_user_service = MagicMock()
        mock_user_service.get_user_by_username = AsyncMock(return_value=mock_user)
        mock_user_service_class.return_value = mock_user_service

        response = client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "another@example.com",
                "password": "SecurePass123!"
            }
        )

        assert response.status_code == 400
        assert "Username already exists" in response.json()["detail"]

    @patch('dotmac.platform.auth.router.get_auth_session')
    @patch('dotmac.platform.auth.router.UserService')
    def test_register_email_exists(
        self, mock_user_service_class, mock_get_session, client,
        mock_user, mock_session
    ):
        """Test registration with existing email."""
        mock_get_session.return_value = mock_session
        mock_user_service = MagicMock()
        mock_user_service.get_user_by_username = AsyncMock(return_value=None)
        mock_user_service.get_user_by_email = AsyncMock(return_value=mock_user)
        mock_user_service_class.return_value = mock_user_service

        response = client.post(
            "/auth/register",
            json={
                "username": "newuser",
                "email": "test@example.com",
                "password": "SecurePass123!"
            }
        )

        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    @patch('dotmac.platform.auth.router.get_auth_session')
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.jwt_service')
    @patch('dotmac.platform.auth.router.session_manager')
    @patch('dotmac.platform.auth.router.get_auth_email_service')
    def test_register_email_failure_continues(
        self, mock_email_service, mock_session_manager, mock_jwt_service,
        mock_user_service_class, mock_get_session, client, mock_session
    ):
        """Test registration continues even if welcome email fails."""
        mock_get_session.return_value = mock_session

        new_user = MagicMock()
        new_user.id = uuid4()
        new_user.username = "newuser"
        new_user.email = "new@example.com"
        new_user.full_name = None
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

        # Email service fails
        mock_facade = MagicMock()
        mock_facade.send_welcome_email = AsyncMock(side_effect=Exception("Email error"))
        mock_email_service.return_value = mock_facade

        response = client.post(
            "/auth/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "SecurePass123!"
            }
        )

        # Registration should still succeed
        assert response.status_code == 200

    @patch('dotmac.platform.auth.router.get_auth_session')
    @patch('dotmac.platform.auth.router.UserService')
    def test_register_create_user_failure(
        self, mock_user_service_class, mock_get_session, client, mock_session
    ):
        """Test registration when user creation fails."""
        mock_get_session.return_value = mock_session
        mock_user_service = MagicMock()
        mock_user_service.get_user_by_username = AsyncMock(return_value=None)
        mock_user_service.get_user_by_email = AsyncMock(return_value=None)
        mock_user_service.create_user = AsyncMock(side_effect=Exception("DB error"))
        mock_user_service_class.return_value = mock_user_service

        response = client.post(
            "/auth/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "SecurePass123!"
            }
        )

        assert response.status_code == 500
        assert "Failed to create user" in response.json()["detail"]


class TestRefreshEndpoint:
    """Test /auth/refresh endpoint."""

    @patch('dotmac.platform.auth.router.get_auth_session')
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.jwt_service')
    def test_refresh_token_success(
        self, mock_jwt_service, mock_user_service_class, mock_get_session,
        client, mock_user, mock_session
    ):
        """Test successful token refresh."""
        mock_get_session.return_value = mock_session
        mock_user_service = MagicMock()
        mock_user_service.get_user_by_id = AsyncMock(return_value=mock_user)
        mock_user_service_class.return_value = mock_user_service

        # Setup JWT service
        mock_jwt_service.verify_token.return_value = {
            "sub": str(mock_user.id),
            "type": "refresh"
        }
        mock_jwt_service.revoke_token = AsyncMock()
        mock_jwt_service.create_access_token.return_value = "new_access_token"
        mock_jwt_service.create_refresh_token.return_value = "new_refresh_token"

        response = client.post(
            "/auth/refresh",
            json={"refresh_token": "old_refresh_token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "new_access_token"
        assert data["refresh_token"] == "new_refresh_token"

        # Verify old token was revoked
        mock_jwt_service.revoke_token.assert_called_once_with("old_refresh_token")

    @patch('dotmac.platform.auth.router.get_auth_session')
    @patch('dotmac.platform.auth.router.jwt_service')
    def test_refresh_token_invalid_type(
        self, mock_jwt_service, mock_get_session, client, mock_session
    ):
        """Test refresh with wrong token type."""
        mock_get_session.return_value = mock_session
        mock_jwt_service.verify_token.return_value = {
            "sub": "user_id",
            "type": "access"  # Wrong type
        }

        response = client.post(
            "/auth/refresh",
            json={"refresh_token": "access_token"}
        )

        assert response.status_code == 401
        assert "Invalid token type" in response.json()["detail"]

    @patch('dotmac.platform.auth.router.get_auth_session')
    @patch('dotmac.platform.auth.router.jwt_service')
    def test_refresh_token_no_subject(
        self, mock_jwt_service, mock_get_session, client, mock_session
    ):
        """Test refresh with token missing subject."""
        mock_get_session.return_value = mock_session
        mock_jwt_service.verify_token.return_value = {
            "type": "refresh"
            # Missing "sub"
        }

        response = client.post(
            "/auth/refresh",
            json={"refresh_token": "invalid_token"}
        )

        assert response.status_code == 401
        assert "Invalid refresh token" in response.json()["detail"]

    @patch('dotmac.platform.auth.router.get_auth_session')
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.jwt_service')
    def test_refresh_token_user_not_found(
        self, mock_jwt_service, mock_user_service_class, mock_get_session,
        client, mock_session
    ):
        """Test refresh when user no longer exists."""
        mock_get_session.return_value = mock_session
        mock_user_service = MagicMock()
        mock_user_service.get_user_by_id = AsyncMock(return_value=None)
        mock_user_service_class.return_value = mock_user_service

        mock_jwt_service.verify_token.return_value = {
            "sub": "deleted_user_id",
            "type": "refresh"
        }

        response = client.post(
            "/auth/refresh",
            json={"refresh_token": "valid_refresh_token"}
        )

        assert response.status_code == 401
        assert "User not found or disabled" in response.json()["detail"]

    @patch('dotmac.platform.auth.router.get_auth_session')
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.jwt_service')
    def test_refresh_token_revoke_failure_continues(
        self, mock_jwt_service, mock_user_service_class, mock_get_session,
        client, mock_user, mock_session
    ):
        """Test refresh continues even if token revocation fails."""
        mock_get_session.return_value = mock_session
        mock_user_service = MagicMock()
        mock_user_service.get_user_by_id = AsyncMock(return_value=mock_user)
        mock_user_service_class.return_value = mock_user_service

        mock_jwt_service.verify_token.return_value = {
            "sub": str(mock_user.id),
            "type": "refresh"
        }
        # Revocation fails but should not stop refresh
        mock_jwt_service.revoke_token = AsyncMock(side_effect=Exception("Redis error"))
        mock_jwt_service.create_access_token.return_value = "new_access_token"
        mock_jwt_service.create_refresh_token.return_value = "new_refresh_token"

        response = client.post(
            "/auth/refresh",
            json={"refresh_token": "old_refresh_token"}
        )

        # Should still succeed
        assert response.status_code == 200

    @patch('dotmac.platform.auth.router.get_auth_session')
    @patch('dotmac.platform.auth.router.jwt_service')
    def test_refresh_token_invalid_token(
        self, mock_jwt_service, mock_get_session, client, mock_session
    ):
        """Test refresh with completely invalid token."""
        mock_get_session.return_value = mock_session
        mock_jwt_service.verify_token.side_effect = Exception("Invalid token")

        response = client.post(
            "/auth/refresh",
            json={"refresh_token": "garbage_token"}
        )

        assert response.status_code == 401
        assert "Invalid or expired refresh token" in response.json()["detail"]


class TestLogoutEndpoint:
    """Test /auth/logout endpoint."""

    @patch('dotmac.platform.auth.router.jwt_service')
    @patch('dotmac.platform.auth.router.session_manager')
    def test_logout_success(self, mock_session_manager, mock_jwt_service, client):
        """Test successful logout."""
        mock_jwt_service.verify_token.return_value = {"sub": "user123"}
        mock_jwt_service.revoke_token = AsyncMock()
        mock_session_manager.delete_user_sessions = AsyncMock(return_value=3)

        response = client.post(
            "/auth/logout",
            headers={"Authorization": "Bearer valid_token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Logged out successfully"
        assert data["sessions_deleted"] == 3

        mock_jwt_service.revoke_token.assert_called_once_with("valid_token")
        mock_session_manager.delete_user_sessions.assert_called_once_with("user123")

    @patch('dotmac.platform.auth.router.jwt_service')
    def test_logout_invalid_token(self, mock_jwt_service, client):
        """Test logout with invalid token still completes."""
        mock_jwt_service.verify_token.side_effect = Exception("Invalid token")
        mock_jwt_service.revoke_token = AsyncMock()

        response = client.post(
            "/auth/logout",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Logout completed"

        # Should still try to revoke the token
        mock_jwt_service.revoke_token.assert_called_once_with("invalid_token")

    @patch('dotmac.platform.auth.router.jwt_service')
    def test_logout_no_user_id(self, mock_jwt_service, client):
        """Test logout with token missing user ID."""
        mock_jwt_service.verify_token.return_value = {}  # No "sub" field
        mock_jwt_service.revoke_token = AsyncMock()

        response = client.post(
            "/auth/logout",
            headers={"Authorization": "Bearer token_no_sub"}
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Logout completed"

    def test_logout_no_authorization(self, client):
        """Test logout without authorization header."""
        response = client.post("/auth/logout")
        assert response.status_code == 403
        assert "Not authenticated" in response.json()["detail"]


class TestVerifyEndpoint:
    """Test /auth/verify endpoint."""

    @patch('dotmac.platform.auth.router.jwt_service')
    def test_verify_valid_token(self, mock_jwt_service, client):
        """Test verification of valid token."""
        mock_jwt_service.verify_token.return_value = {
            "sub": "user123",
            "username": "testuser",
            "roles": ["user", "admin"]
        }

        response = client.get(
            "/auth/verify",
            headers={"Authorization": "Bearer valid_token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["user_id"] == "user123"
        assert data["username"] == "testuser"
        assert data["roles"] == ["user", "admin"]

    @patch('dotmac.platform.auth.router.jwt_service')
    def test_verify_invalid_token(self, mock_jwt_service, client):
        """Test verification of invalid token."""
        mock_jwt_service.verify_token.side_effect = Exception("Token expired")

        response = client.get(
            "/auth/verify",
            headers={"Authorization": "Bearer expired_token"}
        )

        assert response.status_code == 401
        assert "Invalid or expired token" in response.json()["detail"]

    def test_verify_no_authorization(self, client):
        """Test verify without authorization header."""
        response = client.get("/auth/verify")
        assert response.status_code == 403
        assert "Not authenticated" in response.json()["detail"]


class TestPasswordResetEndpoints:
    """Test password reset endpoints."""

    @patch('dotmac.platform.auth.router.get_auth_session')
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.get_auth_email_service')
    def test_request_password_reset_success(
        self, mock_email_service, mock_user_service_class, mock_get_session,
        client, mock_user, mock_session
    ):
        """Test successful password reset request."""
        mock_get_session.return_value = mock_session
        mock_user_service = MagicMock()
        mock_user_service.get_user_by_email = AsyncMock(return_value=mock_user)
        mock_user_service_class.return_value = mock_user_service

        mock_email = MagicMock()
        mock_email.send_password_reset_email = MagicMock(return_value=("sent", "token123"))
        mock_email_service.return_value = mock_email

        response = client.post(
            "/auth/password-reset",
            json={"email": "test@example.com"}
        )

        assert response.status_code == 200
        assert "password reset link has been sent" in response.json()["message"]

        mock_email.send_password_reset_email.assert_called_once()

    @patch('dotmac.platform.auth.router.get_auth_session')
    @patch('dotmac.platform.auth.router.UserService')
    def test_request_password_reset_user_not_found(
        self, mock_user_service_class, mock_get_session, client, mock_session
    ):
        """Test password reset request for non-existent user."""
        mock_get_session.return_value = mock_session
        mock_user_service = MagicMock()
        mock_user_service.get_user_by_email = AsyncMock(return_value=None)
        mock_user_service_class.return_value = mock_user_service

        response = client.post(
            "/auth/password-reset",
            json={"email": "nonexistent@example.com"}
        )

        # Should still return success to prevent email enumeration
        assert response.status_code == 200
        assert "password reset link has been sent" in response.json()["message"]

    @patch('dotmac.platform.auth.router.get_auth_session')
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.get_auth_email_service')
    def test_request_password_reset_email_failure(
        self, mock_email_service, mock_user_service_class, mock_get_session,
        client, mock_user, mock_session
    ):
        """Test password reset request when email fails."""
        mock_get_session.return_value = mock_session
        mock_user_service = MagicMock()
        mock_user_service.get_user_by_email = AsyncMock(return_value=mock_user)
        mock_user_service_class.return_value = mock_user_service

        mock_email = MagicMock()
        mock_email.send_password_reset_email.side_effect = Exception("SMTP error")
        mock_email_service.return_value = mock_email

        response = client.post(
            "/auth/password-reset",
            json={"email": "test@example.com"}
        )

        # Should still return success
        assert response.status_code == 200
        assert "password reset link has been sent" in response.json()["message"]

    @patch('dotmac.platform.auth.router.get_auth_session')
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.get_auth_email_service')
    def test_confirm_password_reset_success(
        self, mock_email_service, mock_user_service_class, mock_get_session,
        client, mock_user, mock_session
    ):
        """Test successful password reset confirmation."""
        mock_get_session.return_value = mock_session
        mock_user_service = MagicMock()
        mock_user_service.get_user_by_email = AsyncMock(return_value=mock_user)
        mock_user_service_class.return_value = mock_user_service

        mock_email = MagicMock()
        mock_email.verify_reset_token = MagicMock(return_value="test@example.com")
        mock_email.send_password_reset_success_email = MagicMock()
        mock_email_service.return_value = mock_email

        response = client.post(
            "/auth/password-reset/confirm",
            json={"token": "valid_token", "new_password": "NewSecurePass123!"}
        )

        assert response.status_code == 200
        assert "Password has been reset successfully" in response.json()["message"]

        # Verify password was updated
        mock_session.commit.assert_called_once()
        mock_email.send_password_reset_success_email.assert_called_once()

    @patch('dotmac.platform.auth.router.get_auth_session')
    @patch('dotmac.platform.auth.router.get_auth_email_service')
    def test_confirm_password_reset_invalid_token(
        self, mock_email_service, mock_get_session, client, mock_session
    ):
        """Test password reset with invalid token."""
        mock_get_session.return_value = mock_session

        mock_email = MagicMock()
        mock_email.verify_reset_token = MagicMock(return_value=None)
        mock_email_service.return_value = mock_email

        response = client.post(
            "/auth/password-reset/confirm",
            json={"token": "invalid_token", "new_password": "NewPass123!"}
        )

        assert response.status_code == 400
        assert "Invalid or expired reset token" in response.json()["detail"]

    @patch('dotmac.platform.auth.router.get_auth_session')
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.get_auth_email_service')
    def test_confirm_password_reset_user_not_found(
        self, mock_email_service, mock_user_service_class, mock_get_session,
        client, mock_session
    ):
        """Test password reset when user not found."""
        mock_get_session.return_value = mock_session
        mock_user_service = MagicMock()
        mock_user_service.get_user_by_email = AsyncMock(return_value=None)
        mock_user_service_class.return_value = mock_user_service

        mock_email = MagicMock()
        mock_email.verify_reset_token = MagicMock(return_value="deleted@example.com")
        mock_email_service.return_value = mock_email

        response = client.post(
            "/auth/password-reset/confirm",
            json={"token": "valid_token", "new_password": "NewPass123!"}
        )

        assert response.status_code == 400
        assert "User not found" in response.json()["detail"]

    @patch('dotmac.platform.auth.router.get_auth_session')
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.get_auth_email_service')
    def test_confirm_password_reset_db_failure(
        self, mock_email_service, mock_user_service_class, mock_get_session,
        client, mock_user, mock_session
    ):
        """Test password reset with database failure."""
        mock_get_session.return_value = mock_session
        mock_user_service = MagicMock()
        mock_user_service.get_user_by_email = AsyncMock(return_value=mock_user)
        mock_user_service_class.return_value = mock_user_service

        mock_email = MagicMock()
        mock_email.verify_reset_token = MagicMock(return_value="test@example.com")
        mock_email_service.return_value = mock_email

        # Database commit fails
        def commit_side_effect():
            raise Exception("DB error")
        mock_session.commit = AsyncMock(side_effect=commit_side_effect)

        response = client.post(
            "/auth/password-reset/confirm",
            json={"token": "valid_token", "new_password": "NewPass123!"}
        )

        assert response.status_code == 500
        assert "Failed to reset password" in response.json()["detail"]

        # Verify rollback was called
        mock_session.rollback.assert_called_once()


class TestMeEndpoint:
    """Test /auth/me endpoint."""

    @patch('dotmac.platform.auth.router.get_auth_session')
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.jwt_service')
    def test_get_me_success(
        self, mock_jwt_service, mock_user_service_class, mock_get_session,
        client, mock_user, mock_session
    ):
        """Test getting current user information."""
        mock_get_session.return_value = mock_session
        mock_user_service = MagicMock()
        mock_user_service.get_user_by_id = AsyncMock(return_value=mock_user)
        mock_user_service_class.return_value = mock_user_service

        mock_jwt_service.verify_token.return_value = {"sub": str(mock_user.id)}

        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer valid_token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(mock_user.id)
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert data["is_active"] is True

    @patch('dotmac.platform.auth.router.get_auth_session')
    @patch('dotmac.platform.auth.router.jwt_service')
    def test_get_me_no_user_id(
        self, mock_jwt_service, mock_get_session, client, mock_session
    ):
        """Test getting current user with token missing user ID."""
        mock_get_session.return_value = mock_session
        mock_jwt_service.verify_token.return_value = {}  # No "sub" field

        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401
        assert "Invalid token" in response.json()["detail"]

    @patch('dotmac.platform.auth.router.get_auth_session')
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.jwt_service')
    def test_get_me_user_not_found(
        self, mock_jwt_service, mock_user_service_class, mock_get_session,
        client, mock_session
    ):
        """Test getting current user when user doesn't exist."""
        mock_get_session.return_value = mock_session
        mock_user_service = MagicMock()
        mock_user_service.get_user_by_id = AsyncMock(return_value=None)
        mock_user_service_class.return_value = mock_user_service

        mock_jwt_service.verify_token.return_value = {"sub": "deleted_user"}

        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer valid_token"}
        )

        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]

    @patch('dotmac.platform.auth.router.jwt_service')
    def test_get_me_invalid_token(self, mock_jwt_service, client):
        """Test getting current user with invalid token."""
        mock_jwt_service.verify_token.side_effect = Exception("Token expired")

        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer expired_token"}
        )

        assert response.status_code == 401
        assert "Invalid or expired token" in response.json()["detail"]

    def test_get_me_no_authorization(self, client):
        """Test getting current user without authorization."""
        response = client.get("/auth/me")
        assert response.status_code == 403
        assert "Not authenticated" in response.json()["detail"]


class TestValidation:
    """Test request validation."""

    def test_register_invalid_email(self, client):
        """Test registration with invalid email format."""
        response = client.post(
            "/auth/register",
            json={
                "username": "newuser",
                "email": "not-an-email",
                "password": "SecurePass123!"
            }
        )
        assert response.status_code == 422

    def test_register_short_username(self, client):
        """Test registration with too short username."""
        response = client.post(
            "/auth/register",
            json={
                "username": "ab",  # Too short
                "email": "test@example.com",
                "password": "SecurePass123!"
            }
        )
        assert response.status_code == 422

    def test_register_short_password(self, client):
        """Test registration with too short password."""
        response = client.post(
            "/auth/register",
            json={
                "username": "newuser",
                "email": "test@example.com",
                "password": "short"  # Too short
            }
        )
        assert response.status_code == 422

    def test_login_missing_fields(self, client):
        """Test login with missing required fields."""
        response = client.post(
            "/auth/login",
            json={"username": "testuser"}  # Missing password
        )
        assert response.status_code == 422

    def test_password_reset_invalid_email(self, client):
        """Test password reset with invalid email."""
        response = client.post(
            "/auth/password-reset",
            json={"email": "invalid-email"}
        )
        assert response.status_code == 422