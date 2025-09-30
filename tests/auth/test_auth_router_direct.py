"""
Direct tests for Auth Router to achieve high coverage.

These tests call router endpoints directly using actual FastAPI
mechanisms while mocking dependencies to avoid database issues.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from uuid import uuid4

# This import ensures the module is loaded
from dotmac.platform.auth.router import auth_router


class TestAuthRouterDirect:
    """Direct tests of auth router endpoints."""

    @pytest.fixture
    def app(self):
        """Create FastAPI app with auth router."""
        app = FastAPI()
        app.include_router(auth_router, prefix="/auth")
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    @patch('dotmac.platform.auth.router.get_auth_session')
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.verify_password')
    @patch('dotmac.platform.auth.router.jwt_service')
    @patch('dotmac.platform.auth.router.session_manager')
    def test_login_endpoint_coverage(
        self, mock_session_manager, mock_jwt_service, mock_verify_password,
        mock_user_service_class, mock_get_session, client
    ):
        """Test login endpoint for coverage."""
        # Setup mocks
        mock_session = AsyncMock()
        mock_get_session.return_value = mock_session

        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.is_active = True
        mock_user.roles = ["user"]
        mock_user.tenant_id = "tenant1"

        mock_user_service = MagicMock()
        mock_user_service.get_user_by_username = AsyncMock(return_value=mock_user)
        mock_user_service_class.return_value = mock_user_service

        mock_verify_password.return_value = True
        mock_jwt_service.create_access_token.return_value = "access_token"
        mock_jwt_service.create_refresh_token.return_value = "refresh_token"
        mock_session_manager.create_session = AsyncMock()

        # Make request
        response = client.post(
            "/auth/login",
            json={"username": "testuser", "password": "password123"}
        )

        assert response.status_code == 200

    @patch('dotmac.platform.auth.router.get_auth_session')
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.jwt_service')
    @patch('dotmac.platform.auth.router.session_manager')
    @patch('dotmac.platform.auth.router.get_auth_email_service')
    def test_register_endpoint_coverage(
        self, mock_email_service, mock_session_manager, mock_jwt_service,
        mock_user_service_class, mock_get_session, client
    ):
        """Test register endpoint for coverage."""
        # Setup mocks
        mock_session = AsyncMock()
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

        response = client.post(
            "/auth/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "SecurePass123!",
                "full_name": "New User"
            }
        )

        assert response.status_code == 200

    @patch('dotmac.platform.auth.router.get_auth_session')
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.jwt_service')
    def test_refresh_endpoint_coverage(
        self, mock_jwt_service, mock_user_service_class, mock_get_session, client
    ):
        """Test refresh endpoint for coverage."""
        mock_session = AsyncMock()
        mock_get_session.return_value = mock_session

        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.is_active = True
        mock_user.roles = ["user"]
        mock_user.tenant_id = "tenant1"

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

        response = client.post(
            "/auth/refresh",
            json={"refresh_token": "old_refresh_token"}
        )

        assert response.status_code == 200

    @patch('dotmac.platform.auth.router.jwt_service')
    @patch('dotmac.platform.auth.router.session_manager')
    def test_logout_endpoint_coverage(self, mock_session_manager, mock_jwt_service, client):
        """Test logout endpoint for coverage."""
        mock_jwt_service.verify_token.return_value = {"sub": "user123"}
        mock_jwt_service.revoke_token = AsyncMock()
        mock_session_manager.delete_user_sessions = AsyncMock(return_value=2)

        response = client.post(
            "/auth/logout",
            headers={"Authorization": "Bearer valid_token"}
        )

        assert response.status_code == 200

    @patch('dotmac.platform.auth.router.jwt_service')
    def test_verify_endpoint_coverage(self, mock_jwt_service, client):
        """Test verify endpoint for coverage."""
        mock_jwt_service.verify_token.return_value = {
            "sub": "user123",
            "username": "testuser",
            "roles": ["user"]
        }

        response = client.get(
            "/auth/verify",
            headers={"Authorization": "Bearer valid_token"}
        )

        assert response.status_code == 200

    @patch('dotmac.platform.auth.router.get_auth_session')
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.get_auth_email_service')
    def test_password_reset_endpoint_coverage(
        self, mock_email_service, mock_user_service_class, mock_get_session, client
    ):
        """Test password reset endpoint for coverage."""
        mock_session = AsyncMock()
        mock_get_session.return_value = mock_session

        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.username = "testuser"
        mock_user.full_name = "Test User"
        mock_user.is_active = True

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

    @patch('dotmac.platform.auth.router.get_auth_session')
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.get_auth_email_service')
    @patch('dotmac.platform.auth.router.hash_password')
    def test_confirm_password_reset_endpoint_coverage(
        self, mock_hash_password, mock_email_service,
        mock_user_service_class, mock_get_session, client
    ):
        """Test confirm password reset endpoint for coverage."""
        mock_session = AsyncMock()
        mock_get_session.return_value = mock_session

        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.username = "testuser"
        mock_user.full_name = "Test User"

        mock_user_service = MagicMock()
        mock_user_service.get_user_by_email = AsyncMock(return_value=mock_user)
        mock_user_service_class.return_value = mock_user_service

        mock_email = MagicMock()
        mock_email.verify_reset_token = MagicMock(return_value="test@example.com")
        mock_email.send_password_reset_success_email = MagicMock()
        mock_email_service.return_value = mock_email

        mock_hash_password.return_value = "new_hashed_password"

        response = client.post(
            "/auth/password-reset/confirm",
            json={"token": "valid_token", "new_password": "NewSecurePass123!"}
        )

        assert response.status_code == 200

    @patch('dotmac.platform.auth.router.get_auth_session')
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.jwt_service')
    def test_me_endpoint_coverage(
        self, mock_jwt_service, mock_user_service_class, mock_get_session, client
    ):
        """Test me endpoint for coverage."""
        mock_session = AsyncMock()
        mock_get_session.return_value = mock_session

        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.full_name = "Test User"
        mock_user.roles = ["user", "admin"]
        mock_user.is_active = True
        mock_user.tenant_id = "tenant1"

        mock_user_service = MagicMock()
        mock_user_service.get_user_by_id = AsyncMock(return_value=mock_user)
        mock_user_service_class.return_value = mock_user_service

        mock_jwt_service.verify_token.return_value = {"sub": str(mock_user.id)}

        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer valid_token"}
        )

        assert response.status_code == 200

    def test_error_paths(self, client):
        """Test various error paths for coverage."""
        # Test unauthorized access
        response = client.get("/auth/verify")
        assert response.status_code == 403

        response = client.post("/auth/logout")
        assert response.status_code == 403

        response = client.get("/auth/me")
        assert response.status_code == 403

        # Test validation errors
        response = client.post("/auth/login", json={"username": "test"})
        assert response.status_code == 422

        response = client.post("/auth/register", json={"username": "ab", "email": "invalid", "password": "123"})
        assert response.status_code == 422

        response = client.post("/auth/password-reset", json={"email": "invalid"})
        assert response.status_code == 422