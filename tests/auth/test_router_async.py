"""
Async integration tests for auth router endpoints using httpx.AsyncClient.

Following Option A: Use AsyncClient for proper async session handling.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.auth.core import hash_password
from dotmac.platform.auth.router import auth_router
from dotmac.platform.user_management.models import User

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def app():
    """Create FastAPI app with auth router and tenant middleware."""
    from dotmac.platform.tenant import TenantConfiguration, TenantMiddleware, TenantMode

    app = FastAPI()

    # Add tenant middleware for multi-tenant support
    tenant_config = TenantConfiguration(
        mode=TenantMode.MULTI,
        require_tenant_header=True,
        tenant_header_name="X-Tenant-ID",
    )
    app.add_middleware(TenantMiddleware, config=tenant_config)

    app.include_router(auth_router, prefix="/auth")
    return app


@pytest.fixture
async def async_client(app, async_db_session):
    """Create async HTTP client with session dependency override."""
    # CRITICAL: Auth router uses get_auth_session, not get_session_dependency!
    # We need to import and override the actual dependency used by the router
    from dotmac.platform.auth.router import get_auth_session

    # Override to always return the SAME test session
    # This is critical - we need to return the exact same session object,
    # not create a new one, so that fixtures and endpoints see the same data
    async def override_get_auth_session():
        yield async_db_session

    app.dependency_overrides[get_auth_session] = override_get_auth_session

    # Create async client with ASGI transport
    from httpx import ASGITransport

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    # Clean up override after test
    app.dependency_overrides.clear()


@pytest.fixture
async def active_user(async_db_session: AsyncSession):
    """Create an active test user in the database."""
    user = User(
        id=uuid4(),
        username="activeuser",
        email="active@example.com",
        password_hash=hash_password("SecurePass123!"),
        tenant_id="test-tenant",
        is_active=True,
        is_verified=True,
        roles=["user"],
        permissions=["read:own"],
    )
    async_db_session.add(user)
    # Use flush() instead of commit() to keep everything in one transaction
    # This makes the data visible to all queries in the same session/transaction
    await async_db_session.flush()
    await async_db_session.refresh(user)
    return user


@pytest.fixture
async def inactive_user(async_db_session: AsyncSession):
    """Create an inactive test user."""
    user = User(
        id=uuid4(),
        username="inactiveuser",
        email="inactive@example.com",
        password_hash=hash_password("SecurePass123!"),
        tenant_id="test-tenant",
        is_active=False,
        is_verified=True,
    )
    async_db_session.add(user)
    # Use flush() instead of commit() to keep in same transaction
    await async_db_session.flush()
    await async_db_session.refresh(user)
    return user


@pytest.fixture
def tenant_headers():
    """Standard tenant headers for API requests."""
    return {"X-Tenant-ID": "test-tenant"}


# ============================================================================
# Login Endpoint Tests
# ============================================================================


class TestLoginEndpoint:
    """Test POST /auth/login endpoint."""

    @pytest.mark.asyncio
    async def test_login_success_with_username(self, async_client, tenant_headers, active_user):
        """Test successful login using username."""
        # Mock audit logging (external service)
        with patch("dotmac.platform.auth.router.log_user_activity", new_callable=AsyncMock):
            with patch("dotmac.platform.auth.router.log_api_activity", new_callable=AsyncMock):
                response = await async_client.post(
                    "/auth/login",
                    json={
                        "username": "activeuser",
                        "password": "SecurePass123!",
                    },
                    headers=tenant_headers,
                )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

        # Verify cookies are set
        assert "access_token" in response.cookies
        assert "refresh_token" in response.cookies

    @pytest.mark.asyncio
    async def test_login_success_with_email(self, async_client, tenant_headers, active_user):
        """Test successful login using email instead of username."""
        with patch("dotmac.platform.auth.router.log_user_activity", new_callable=AsyncMock):
            with patch("dotmac.platform.auth.router.log_api_activity", new_callable=AsyncMock):
                response = await async_client.post(
                    "/auth/login",
                    json={
                        "username": "active@example.com",  # Email in username field
                        "password": "SecurePass123!",
                    },
                    headers=tenant_headers,
                )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    @pytest.mark.asyncio
    async def test_login_invalid_password(self, async_client, tenant_headers, active_user):
        """Test login with invalid password."""
        with patch(
            "dotmac.platform.auth.router.log_api_activity", new_callable=AsyncMock
        ) as mock_log:
            response = await async_client.post(
                "/auth/login",
                json={
                    "username": "activeuser",
                    "password": "WrongPassword",
                },
                headers=tenant_headers,
            )

        assert response.status_code == 401
        assert "Invalid username or password" in response.json()["detail"]

        # Verify failed login was logged
        mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, async_client, tenant_headers):
        """Test login with non-existent user."""
        with patch("dotmac.platform.auth.router.log_api_activity", new_callable=AsyncMock):
            response = await async_client.post(
                "/auth/login",
                json={
                    "username": "nonexistent",
                    "password": "AnyPassword123!",
                },
                headers=tenant_headers,
            )

        assert response.status_code == 401
        assert "Invalid username or password" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_inactive_account(self, async_client, tenant_headers, inactive_user):
        """Test login with inactive account."""
        with patch(
            "dotmac.platform.auth.router.log_user_activity", new_callable=AsyncMock
        ) as mock_log:
            response = await async_client.post(
                "/auth/login",
                json={
                    "username": "inactiveuser",
                    "password": "SecurePass123!",
                },
                headers=tenant_headers,
            )

        assert response.status_code == 403
        assert "Account is disabled" in response.json()["detail"]

        # Verify disabled account login was logged
        mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_login_missing_username(self, async_client, tenant_headers):
        """Test login with missing username."""
        response = await async_client.post(
            "/auth/login",
            json={"password": "SecurePass123!"},
            headers=tenant_headers,
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_login_missing_password(self, async_client, tenant_headers):
        """Test login with missing password."""
        response = await async_client.post(
            "/auth/login",
            json={"username": "activeuser"},
            headers=tenant_headers,
        )

        assert response.status_code == 422  # Validation error


# ============================================================================
# Token Endpoint Tests (OAuth2 password flow)
# ============================================================================


class TestTokenEndpoint:
    """Test POST /auth/token endpoint (OAuth2 password flow)."""

    @pytest.mark.asyncio
    async def test_token_endpoint_success(self, async_client, tenant_headers, active_user):
        """Test successful token request using OAuth2 form."""
        with patch("dotmac.platform.auth.router.log_user_activity", new_callable=AsyncMock):
            with patch("dotmac.platform.auth.router.log_api_activity", new_callable=AsyncMock):
                response = await async_client.post(
                    "/auth/token",
                    data={
                        "username": "activeuser",
                        "password": "SecurePass123!",
                    },
                    headers={**tenant_headers, "Content-Type": "application/x-www-form-urlencoded"},
                )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_token_endpoint_invalid_credentials(
        self, async_client, tenant_headers, active_user
    ):
        """Test token endpoint with invalid credentials."""
        with patch("dotmac.platform.auth.router.log_api_activity", new_callable=AsyncMock):
            response = await async_client.post(
                "/auth/token",
                data={
                    "username": "activeuser",
                    "password": "WrongPassword",
                },
                headers={**tenant_headers, "Content-Type": "application/x-www-form-urlencoded"},
            )

        assert response.status_code == 401


# ============================================================================
# Register Endpoint Tests
# ============================================================================


class TestRegisterEndpoint:
    """Test POST /auth/register endpoint."""

    @pytest.mark.asyncio
    async def test_register_success(self, async_client, tenant_headers, async_db_session):
        """Test successful user registration."""
        with patch("dotmac.platform.auth.router.log_user_activity", new_callable=AsyncMock):
            response = await async_client.post(
                "/auth/register",
                json={
                    "username": "newuser",
                    "email": "newuser@example.com",
                    "password": "NewSecurePass123!",
                    "full_name": "New User",
                },
                headers=tenant_headers,
            )

        assert response.status_code == 200  # Router returns 200, not 201
        data = response.json()
        assert "access_token" in data
        # User ID is in the token claims, not response body directly

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, async_client, tenant_headers, active_user):
        """Test registration with duplicate username."""
        response = await async_client.post(
            "/auth/register",
            json={
                "username": "activeuser",  # Already exists
                "email": "different@example.com",
                "password": "NewSecurePass123!",
            },
            headers=tenant_headers,
        )

        assert response.status_code == 400
        # Router returns generic error message to avoid user enumeration
        assert (
            "registration failed" in response.json()["detail"].lower()
            or "already" in response.json()["detail"].lower()
        )

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, async_client, tenant_headers, active_user):
        """Test registration with duplicate email."""
        response = await async_client.post(
            "/auth/register",
            json={
                "username": "differentuser",
                "email": "active@example.com",  # Already exists
                "password": "NewSecurePass123!",
            },
            headers=tenant_headers,
        )

        assert response.status_code == 400
        # Router returns generic error message to avoid user enumeration
        assert (
            "registration failed" in response.json()["detail"].lower()
            or "already" in response.json()["detail"].lower()
        )

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, async_client, tenant_headers):
        """Test registration with invalid email format."""
        response = await async_client.post(
            "/auth/register",
            json={
                "username": "newuser",
                "email": "not-an-email",
                "password": "NewSecurePass123!",
            },
            headers=tenant_headers,
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_register_short_password(self, async_client, tenant_headers):
        """Test registration with password too short."""
        response = await async_client.post(
            "/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "short",  # Less than 8 characters
            },
            headers=tenant_headers,
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_register_short_username(self, async_client, tenant_headers):
        """Test registration with username too short."""
        response = await async_client.post(
            "/auth/register",
            json={
                "username": "ab",  # Less than 3 characters
                "email": "newuser@example.com",
                "password": "NewSecurePass123!",
            },
            headers=tenant_headers,
        )

        assert response.status_code == 422  # Validation error


# ============================================================================
# Logout Endpoint Tests
# ============================================================================


class TestLogoutEndpoint:
    """Test POST /auth/logout endpoint."""

    @pytest.mark.asyncio
    async def test_logout_success(self, async_client, tenant_headers, active_user):
        """Test successful logout."""
        # First login to get a token
        with patch("dotmac.platform.auth.router.log_user_activity", new_callable=AsyncMock):
            with patch("dotmac.platform.auth.router.log_api_activity", new_callable=AsyncMock):
                login_response = await async_client.post(
                    "/auth/login",
                    json={
                        "username": "activeuser",
                        "password": "SecurePass123!",
                    },
                    headers=tenant_headers,
                )

        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]

        # Now logout
        with patch("dotmac.platform.auth.router.log_user_activity", new_callable=AsyncMock):
            logout_response = await async_client.post(
                "/auth/logout",
                headers={**tenant_headers, "Authorization": f"Bearer {access_token}"},
            )

        assert logout_response.status_code == 200
        assert logout_response.json()["message"] == "Logged out successfully"

        # Note: httpx doesn't return Set-Cookie headers in cookies dict
        # In production, cookies are cleared via Set-Cookie headers


# ============================================================================
# Refresh Token Endpoint Tests
# ============================================================================


class TestRefreshEndpoint:
    """Test POST /auth/refresh endpoint."""

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, async_client, tenant_headers, active_user):
        """Test successful token refresh."""
        # First login to get tokens
        with patch("dotmac.platform.auth.router.log_user_activity", new_callable=AsyncMock):
            with patch("dotmac.platform.auth.router.log_api_activity", new_callable=AsyncMock):
                login_response = await async_client.post(
                    "/auth/login",
                    json={
                        "username": "activeuser",
                        "password": "SecurePass123!",
                    },
                    headers=tenant_headers,
                )

        refresh_token = login_response.json()["refresh_token"]

        # Now refresh
        refresh_response = await async_client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token},
            headers=tenant_headers,
        )

        assert refresh_response.status_code == 200
        data = refresh_response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    @pytest.mark.asyncio
    async def test_refresh_invalid_token(self, async_client, tenant_headers):
        """Test refresh with invalid token."""
        response = await async_client.post(
            "/auth/refresh",
            json={"refresh_token": "invalid.token.here"},
            headers=tenant_headers,
        )

        assert response.status_code in [401, 422]  # Could be either


# ============================================================================
# Password Reset Endpoint Tests
# ============================================================================


class TestPasswordResetEndpoint:
    """Test password reset endpoints."""

    @pytest.mark.asyncio
    async def test_password_reset_request_success(self, async_client, tenant_headers, active_user):
        """Test successful password reset request."""
        # Mock email service
        with patch("dotmac.platform.auth.router.get_auth_email_service") as mock_email:
            mock_service = MagicMock()
            mock_service.send_password_reset_email = AsyncMock()
            mock_email.return_value = mock_service

            response = await async_client.post(
                "/auth/password-reset",
                json={"email": "active@example.com"},
                headers=tenant_headers,
            )

        assert response.status_code == 200
        assert "reset" in response.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_password_reset_nonexistent_email(self, async_client, tenant_headers):
        """Test password reset request for non-existent email."""
        with patch("dotmac.platform.auth.router.get_auth_email_service") as mock_email:
            mock_service = MagicMock()
            mock_email.return_value = mock_service

            response = await async_client.post(
                "/auth/password-reset",
                json={"email": "nonexistent@example.com"},
                headers=tenant_headers,
            )

        # Should still return 200 to avoid user enumeration
        assert response.status_code == 200


# ============================================================================
# Verify Token Endpoint Tests
# ============================================================================


class TestVerifyEndpoint:
    """Test GET /auth/verify endpoint."""

    @pytest.mark.asyncio
    async def test_verify_valid_token(self, async_client, tenant_headers, active_user):
        """Test token verification with valid token."""
        # First login to get a token
        with patch("dotmac.platform.auth.router.log_user_activity", new_callable=AsyncMock):
            with patch("dotmac.platform.auth.router.log_api_activity", new_callable=AsyncMock):
                login_response = await async_client.post(
                    "/auth/login",
                    json={
                        "username": "activeuser",
                        "password": "SecurePass123!",
                    },
                    headers=tenant_headers,
                )

        access_token = login_response.json()["access_token"]

        # Verify the token
        verify_response = await async_client.get(
            "/auth/verify",
            headers={**tenant_headers, "Authorization": f"Bearer {access_token}"},
        )

        assert verify_response.status_code == 200
        data = verify_response.json()
        assert data["valid"] is True
        assert "user_id" in data

    @pytest.mark.asyncio
    async def test_verify_invalid_token(self, async_client, tenant_headers):
        """Test token verification with invalid token."""
        response = await async_client.get(
            "/auth/verify",
            headers={**tenant_headers, "Authorization": "Bearer invalid.token.here"},
        )

        assert response.status_code == 401


# ============================================================================
# Me Endpoint Tests
# ============================================================================


class TestMeEndpoint:
    """Test GET /auth/me endpoint."""

    @pytest.mark.asyncio
    async def test_me_endpoint_authenticated(self, async_client, tenant_headers, active_user):
        """Test /me endpoint with authenticated user."""
        # First login to get a token
        with patch("dotmac.platform.auth.router.log_user_activity", new_callable=AsyncMock):
            with patch("dotmac.platform.auth.router.log_api_activity", new_callable=AsyncMock):
                login_response = await async_client.post(
                    "/auth/login",
                    json={
                        "username": "activeuser",
                        "password": "SecurePass123!",
                    },
                    headers=tenant_headers,
                )

        access_token = login_response.json()["access_token"]

        # Get current user info
        me_response = await async_client.get(
            "/auth/me",
            headers={**tenant_headers, "Authorization": f"Bearer {access_token}"},
        )

        assert me_response.status_code == 200
        data = me_response.json()
        assert data["username"] == "activeuser"
        assert data["email"] == "active@example.com"

    @pytest.mark.asyncio
    async def test_me_endpoint_unauthenticated(self, async_client, tenant_headers):
        """Test /me endpoint without authentication."""
        response = await async_client.get("/auth/me", headers=tenant_headers)

        assert response.status_code == 401
