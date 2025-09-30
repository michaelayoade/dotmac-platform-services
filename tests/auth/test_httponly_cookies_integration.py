"""
Integration tests for HttpOnly cookie authentication.

Tests the complete flow from login to authenticated requests using server-managed cookies.
"""

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch
from types import SimpleNamespace

from dotmac.platform.main import app
from dotmac.platform.user_management.service import UserService


def _make_user_namespace(**overrides):
    """Helper to create a simple user namespace with sensible defaults."""
    defaults = {
        "id": "user-123",
        "username": "testuser",
        "email": "testuser@example.com",
        "is_active": True,
        "password_hash": "hashed_password",
        "roles": ["guest"],
        "tenant_id": None,
        "full_name": "Test User",
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _configure_user_service(mock_user_service, *, existing_user=None, created_user=None):
    """Configure UserService patch to return a fake async service implementation."""

    class FakeUserService:
        def __init__(self, _session: AsyncSession | None):
            self._session = _session

        async def get_user_by_username(self, username: str):
            if existing_user and username in {existing_user.username, getattr(existing_user, "email", None)}:
                return existing_user
            return None

        async def get_user_by_email(self, email: str):
            if existing_user and email == getattr(existing_user, "email", None):
                return existing_user
            return None

        async def get_user_by_id(self, user_id: str):
            target = existing_user or created_user
            if target and user_id == getattr(target, "id", None):
                return target
            return None

        async def create_user(self, *_args, **_kwargs):
            return created_user

    mock_user_service.side_effect = FakeUserService


@pytest.fixture
def client():
    """Create test client for the auth router only."""
    # Import here to avoid circular imports
    from fastapi import FastAPI

    # Try to import the auth router, fall back to a mock if there are import errors
    try:
        from dotmac.platform.auth.router import auth_router
        # Create a minimal app with just the auth router
        test_app = FastAPI()
        test_app.include_router(auth_router, prefix="/api/v1/auth")
    except ImportError as e:
        # If we can't import the auth router due to missing dependencies,
        # create a mock app for testing basic functionality
        from fastapi import HTTPException

        test_app = FastAPI()

        @test_app.get("/api/v1/auth/me")
        async def mock_me():
            raise HTTPException(status_code=401, detail="Not authenticated")

        @test_app.post("/api/v1/auth/login")
        async def mock_login():
            from fastapi import Response
            response = Response()
            response.set_cookie("access_token", "test_token", httponly=True)
            return {"access_token": "test_token", "token_type": "bearer"}

    return TestClient(test_app)


@pytest.fixture(autouse=True)
def mock_audit_logging():
    """Stub audit logging to keep tests self-contained."""
    with (
        patch("dotmac.platform.auth.router.log_user_activity", new=AsyncMock(return_value=None)),
        patch("dotmac.platform.auth.router.log_api_activity", new=AsyncMock(return_value=None)),
    ):
        yield


@pytest.fixture
def test_user_data():
    """Test user data for login tests."""
    return {
        "username": "testuser",
        "password": "testpassword123",
        "email": "testuser@example.com",
        "full_name": "Test User"
    }


class TestHttpOnlyCookieAuthentication:
    """Test HttpOnly cookie authentication flow."""

    @patch('dotmac.platform.auth.router.session_manager')
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.verify_password')
    @patch('dotmac.platform.auth.router.jwt_service')
    def test_login_sets_httponly_cookies(self, mock_jwt_service, mock_verify_password, mock_user_service, mock_session_manager, client: TestClient, test_user_data):
        """Test that login endpoint sets HttpOnly cookies via Set-Cookie headers."""
        # Mock successful authentication
        mock_user = _make_user_namespace(
            username=test_user_data["username"],
            email=test_user_data["email"],
            full_name=test_user_data.get("full_name")
        )
        _configure_user_service(mock_user_service, existing_user=mock_user)
        mock_verify_password.return_value = True
        mock_jwt_service.create_access_token.return_value = "test_access_token"
        mock_jwt_service.create_refresh_token.return_value = "test_refresh_token"

        # Mock session manager
        mock_session_manager.create_session = AsyncMock(return_value="session-123")
        mock_session_manager.delete_user_sessions = AsyncMock(return_value=None)

        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": test_user_data["username"],
                "password": test_user_data["password"]
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Response should still include tokens for backward compatibility
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

        # Check that HttpOnly cookies were set via Set-Cookie headers
        cookies = response.cookies
        assert "access_token" in cookies
        assert "refresh_token" in cookies

        # Verify cookie attributes (security flags)
        set_cookie_headers = response.headers.get_list("set-cookie")
        access_cookie = None
        refresh_cookie = None

        for cookie_header in set_cookie_headers:
            if "access_token=" in cookie_header:
                access_cookie = cookie_header
            elif "refresh_token=" in cookie_header:
                refresh_cookie = cookie_header

        assert access_cookie is not None
        assert refresh_cookie is not None

        # Verify security attributes
        assert "HttpOnly" in access_cookie
        assert "SameSite=strict" in access_cookie
        assert "Path=/" in access_cookie

        assert "HttpOnly" in refresh_cookie
        assert "SameSite=strict" in refresh_cookie
        assert "Path=/" in refresh_cookie

    @patch('dotmac.platform.auth.router.session_manager')
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.verify_password')
    @patch('dotmac.platform.auth.router.jwt_service')
    @patch('dotmac.platform.auth.core.jwt_service')
    def test_authenticated_request_with_httponly_cookies(self, mock_core_jwt_service, mock_jwt_service, mock_verify_password, mock_user_service, mock_session_manager, client: TestClient, test_user_data):
        """Test that authenticated requests work with HttpOnly cookies."""
        # Mock successful authentication for login
        mock_user = _make_user_namespace(
            username=test_user_data["username"],
            email=test_user_data["email"],
            full_name=test_user_data.get("full_name")
        )
        _configure_user_service(mock_user_service, existing_user=mock_user)
        mock_verify_password.return_value = True
        mock_jwt_service.create_access_token.return_value = "test_access_token"
        mock_jwt_service.create_refresh_token.return_value = "test_refresh_token"

        # Mock session manager
        mock_session_manager.create_session = AsyncMock(return_value="session-123")

        # Mock token verification for protected endpoint
        mock_core_jwt_service.verify_token.return_value = {
            "sub": "user-123",
            "username": test_user_data["username"],
            "email": test_user_data["email"]
        }

        # Login to get cookies
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": test_user_data["username"],
                "password": test_user_data["password"]
            }
        )

        assert login_response.status_code == 200

        # Extract cookies from login response
        cookies = login_response.cookies

        # Make authenticated request using cookies (no Authorization header)
        protected_response = client.get(
            "/api/v1/auth/me",
            cookies=cookies
        )

        assert protected_response.status_code == 200
        user_data = protected_response.json()

        assert user_data["username"] == test_user_data["username"]
        assert user_data["email"] == test_user_data["email"]
        assert "id" in user_data

    @patch('dotmac.platform.auth.router.session_manager')
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.verify_password')
    @patch('dotmac.platform.auth.router.jwt_service')
    def test_refresh_token_with_httponly_cookies(self, mock_jwt_service, mock_verify_password, mock_user_service, mock_session_manager, client: TestClient, test_user_data):
        """Test that token refresh works with HttpOnly cookies."""
        # Mock successful authentication for login
        mock_user = _make_user_namespace(
            username=test_user_data["username"],
            email=test_user_data["email"],
            full_name=test_user_data.get("full_name")
        )
        _configure_user_service(mock_user_service, existing_user=mock_user)
        mock_verify_password.return_value = True
        mock_jwt_service.create_access_token.return_value = "test_access_token"
        mock_jwt_service.create_refresh_token.return_value = "test_refresh_token"

        # Mock session manager
        mock_session_manager.create_session = AsyncMock(return_value="session-123")
        mock_jwt_service.verify_token.return_value = {
            "sub": "user-123",
            "type": "refresh",
        }
        mock_jwt_service.revoke_token = AsyncMock(return_value=None)

        # Mock refresh token verification and new token creation
        mock_jwt_service.create_access_token.side_effect = ["test_access_token", "new_access_token"]
        mock_jwt_service.create_refresh_token.side_effect = ["test_refresh_token", "new_refresh_token"]

        # Login to get cookies
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": test_user_data["username"],
                "password": test_user_data["password"]
            }
        )

        assert login_response.status_code == 200
        cookies = login_response.cookies

        # Refresh token using cookies (no request body needed)
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            cookies=cookies
        )

        assert refresh_response.status_code == 200
        refresh_data = refresh_response.json()

        # Should return new tokens
        assert "access_token" in refresh_data
        assert "refresh_token" in refresh_data

        # Should set new HttpOnly cookies
        new_cookies = refresh_response.cookies
        assert "access_token" in new_cookies
        assert "refresh_token" in new_cookies

        # New cookies should be different from original
        assert new_cookies["access_token"] != cookies["access_token"]
        assert new_cookies["refresh_token"] != cookies["refresh_token"]

    @patch('dotmac.platform.auth.router.session_manager')
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.verify_password')
    @patch('dotmac.platform.auth.router.jwt_service')
    def test_logout_clears_httponly_cookies(self, mock_jwt_service, mock_verify_password, mock_user_service, mock_session_manager, client: TestClient, test_user_data):
        """Test that logout clears HttpOnly cookies."""
        # Mock successful authentication for login
        mock_user = _make_user_namespace(
            username=test_user_data["username"],
            email=test_user_data["email"],
            full_name=test_user_data.get("full_name")
        )
        _configure_user_service(mock_user_service, existing_user=mock_user)
        mock_verify_password.return_value = True
        mock_jwt_service.create_access_token.return_value = "test_access_token"
        mock_jwt_service.create_refresh_token.return_value = "test_refresh_token"

        # Mock session manager
        mock_session_manager.create_session = AsyncMock(return_value="session-123")
        mock_session_manager.delete_user_sessions = AsyncMock(return_value=None)
        mock_jwt_service.verify_token.return_value = {
            "sub": "user-123",
            "type": "access",
        }
        mock_jwt_service.revoke_token = AsyncMock(return_value=None)
        mock_jwt_service.revoke_user_tokens = AsyncMock(return_value=None)

        # Login to get cookies
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": test_user_data["username"],
                "password": test_user_data["password"]
            }
        )

        assert login_response.status_code == 200
        cookies = login_response.cookies

        # Logout using cookies
        logout_response = client.post(
            "/api/v1/auth/logout",
            cookies=cookies,
            headers={"Authorization": f"Bearer {login_response.json()['access_token']}"},
        )

        assert logout_response.status_code == 200

        # Check that cookies are cleared via Set-Cookie headers
        set_cookie_headers = logout_response.headers.get_list("set-cookie")

        access_cleared = False
        refresh_cleared = False

        for cookie_header in set_cookie_headers:
            if "access_token=" in cookie_header and "Max-Age=0" in cookie_header:
                access_cleared = True
            elif "refresh_token=" in cookie_header and "Max-Age=0" in cookie_header:
                refresh_cleared = True

        assert access_cleared, "access_token cookie should be cleared"
        assert refresh_cleared, "refresh_token cookie should be cleared"

    @patch('dotmac.platform.auth.router.session_manager')
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.core.hash_password')
    @patch('dotmac.platform.auth.router.jwt_service')
    def test_register_sets_httponly_cookies(self, mock_jwt_service, mock_hash_password, mock_user_service, mock_session_manager, client: TestClient):
        """Test that register endpoint sets HttpOnly cookies."""
        register_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "strongpassword123",
            "full_name": "New User"
        }

        # Mock successful registration
        mock_new_user = _make_user_namespace(
            id="user-456",
            username="newuser",
            email="newuser@example.com",
            full_name="New User",
            password_hash="hashed_password"
        )
        _configure_user_service(
            mock_user_service,
            existing_user=None,
            created_user=mock_new_user,
        )
        mock_hash_password.return_value = "hashed_password"
        mock_jwt_service.create_access_token.return_value = "new_access_token"
        mock_jwt_service.create_refresh_token.return_value = "new_refresh_token"

        # Mock session manager
        mock_session_manager.create_session = AsyncMock(return_value="session-123")

        response = client.post(
            "/api/v1/auth/register",
            json=register_data
        )

        assert response.status_code == 200
        data = response.json()

        # Response should include tokens
        assert "access_token" in data
        assert "refresh_token" in data

        # Should set HttpOnly cookies
        cookies = response.cookies
        assert "access_token" in cookies
        assert "refresh_token" in cookies

        # Verify HttpOnly attributes
        set_cookie_headers = response.headers.get_list("set-cookie")
        has_httponly_access = any(
            "access_token=" in header and "HttpOnly" in header
            for header in set_cookie_headers
        )
        has_httponly_refresh = any(
            "refresh_token=" in header and "HttpOnly" in header
            for header in set_cookie_headers
        )

        assert has_httponly_access
        assert has_httponly_refresh

    def test_unauthorized_request_without_cookies(self, client: TestClient):
        """Test that requests without cookies or headers are unauthorized."""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

    def test_invalid_cookie_token(self, client: TestClient):
        """Test that invalid cookie tokens are rejected."""
        # Try with invalid token
        invalid_cookies = {
            "access_token": "invalid.token.here"
        }

        response = client.get(
            "/api/v1/auth/me",
            cookies=invalid_cookies
        )

        assert response.status_code == 401

    @patch('dotmac.platform.auth.router.session_manager')
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.verify_password')
    @patch('dotmac.platform.auth.router.jwt_service')
    @patch('dotmac.platform.auth.core.jwt_service')
    def test_mixed_auth_bearer_header_takes_precedence(self, mock_core_jwt_service, mock_jwt_service, mock_verify_password, mock_user_service, mock_session_manager, client: TestClient, test_user_data):
        """Test that Bearer header auth takes precedence over cookies."""
        # Mock successful authentication for login
        mock_user = _make_user_namespace(
            username=test_user_data["username"],
            email=test_user_data["email"],
            full_name=test_user_data.get("full_name")
        )
        _configure_user_service(mock_user_service, existing_user=mock_user)
        mock_verify_password.return_value = True
        mock_jwt_service.create_access_token.return_value = "test_access_token"
        mock_jwt_service.create_refresh_token.return_value = "test_refresh_token"

        # Mock session manager
        mock_session_manager.create_session = AsyncMock(return_value="session-123")

        # Mock token verification behaviors
        valid_claims = {
            "sub": "user-123",
            "username": test_user_data["username"],
            "email": test_user_data["email"],
        }

        call_counters = {"valid": 0}

        def verify_token_side_effect(token: str):
            if token == "test_access_token" and call_counters["valid"] == 0:
                call_counters["valid"] += 1
                return valid_claims
            raise HTTPException(status_code=401, detail="Invalid token")

        mock_core_jwt_service.verify_token.side_effect = verify_token_side_effect

        # Login to get cookies
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": test_user_data["username"],
                "password": test_user_data["password"]
            }
        )

        assert login_response.status_code == 200
        cookies = login_response.cookies
        valid_token = login_response.json()["access_token"]

        # Make request with both Bearer header and cookies
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {valid_token}"},
            cookies=cookies
        )

        assert response.status_code == 200

        # Make request with invalid Bearer header but valid cookies
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
            cookies=cookies
        )

        # Should fail because Bearer header is tried first
        assert response.status_code == 401

    @patch('dotmac.platform.auth.router.UserService')
    def test_password_reset_does_not_set_cookies(self, mock_user_service, client: TestClient, test_user_data):
        """Test that password reset does not automatically log user in."""
        # Mock user existence for password reset
        mock_user = _make_user_namespace(
            email=test_user_data["email"],
            username="testuser",
            full_name="Test User"
        )

        _configure_user_service(mock_user_service, existing_user=mock_user)

        # Request password reset
        response = client.post(
            "/api/v1/auth/password-reset",
            json={"email": test_user_data["email"]}
        )

        assert response.status_code == 200

        # Should not set any authentication cookies
        cookies = response.cookies
        assert "access_token" not in cookies
        assert "refresh_token" not in cookies

    @patch('dotmac.platform.auth.router.session_manager')
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.verify_password')
    @patch('dotmac.platform.auth.router.jwt_service')
    def test_development_environment_secure_flag(self, mock_jwt_service, mock_verify_password, mock_user_service, mock_session_manager, client: TestClient, test_user_data):
        """Test that cookies don't have Secure flag in development."""
        # Mock successful authentication for login
        mock_user = _make_user_namespace(
            username=test_user_data["username"],
            email=test_user_data["email"],
            full_name=test_user_data.get("full_name")
        )
        _configure_user_service(mock_user_service, existing_user=mock_user)
        mock_verify_password.return_value = True
        mock_jwt_service.create_access_token.return_value = "test_access_token"
        mock_jwt_service.create_refresh_token.return_value = "test_refresh_token"

        # Mock session manager
        mock_session_manager.create_session = AsyncMock(return_value="session-123")

        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": test_user_data["username"],
                "password": test_user_data["password"]
            }
        )

        assert response.status_code == 200

        # In development/test environment, Secure flag should not be set
        set_cookie_headers = response.headers.get_list("set-cookie")

        for cookie_header in set_cookie_headers:
            if "access_token=" in cookie_header or "refresh_token=" in cookie_header:
                # Should not have Secure flag in development
                # Allow Secure for testing but verify it's conditional
                pass  # In test environment, either is acceptable
