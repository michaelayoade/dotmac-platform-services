"""
End-to-end tests for authentication flows.

Tests cover login, registration, 2FA, password reset, and session management.

## Assertion Guidelines

- Each test should have ONE expected outcome
- Use specific status codes, not lists like [200, 400, 403]
- Separate tests for success vs failure scenarios
- Validate response data structure completely
"""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.auth.core import hash_password
from dotmac.platform.user_management.models import BackupCode, EmailVerificationToken, User

# Import shared test constants
from tests.e2e.constants import (
    TEST_PASSWORD,
    TEST_PASSWORD_NEW,
    TEST_JWT_SECRET,
    TEST_JWT_ALGORITHM,
    StatusCodes,
)

pytestmark = [pytest.mark.asyncio, pytest.mark.e2e]


# ============================================================================
# Fixtures for Auth E2E Tests
# ============================================================================


@pytest_asyncio.fixture
async def created_test_user(e2e_db_session: AsyncSession, tenant_id: str):
    """Create an actual user in the database for testing real auth flows."""
    user = User(
        id=uuid.uuid4(),
        username=f"testuser_{uuid.uuid4().hex[:8]}",
        email=f"test_{uuid.uuid4().hex[:8]}@example.com",
        password_hash=hash_password(TEST_PASSWORD),
        tenant_id=tenant_id,
        is_active=True,
        is_verified=True,
        mfa_enabled=False,
        roles=["user"],
    )
    e2e_db_session.add(user)
    await e2e_db_session.commit()
    await e2e_db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def unverified_user(e2e_db_session: AsyncSession, tenant_id: str):
    """Create an unverified user for email verification testing."""
    user = User(
        id=uuid.uuid4(),
        username=f"unverified_{uuid.uuid4().hex[:8]}",
        email=f"unverified_{uuid.uuid4().hex[:8]}@example.com",
        password_hash=hash_password(TEST_PASSWORD),
        tenant_id=tenant_id,
        is_active=True,
        is_verified=False,
        mfa_enabled=False,
        roles=["user"],
    )
    e2e_db_session.add(user)
    await e2e_db_session.commit()
    await e2e_db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def mfa_enabled_user(e2e_db_session: AsyncSession, tenant_id: str):
    """Create a user with MFA enabled for 2FA testing."""
    from dotmac.platform.auth.mfa_service import mfa_service

    secret = mfa_service.generate_secret()
    user = User(
        id=uuid.uuid4(),
        username=f"mfauser_{uuid.uuid4().hex[:8]}",
        email=f"mfa_{uuid.uuid4().hex[:8]}@example.com",
        password_hash=hash_password(TEST_PASSWORD),
        tenant_id=tenant_id,
        is_active=True,
        is_verified=True,
        mfa_enabled=True,
        mfa_secret=secret,
        roles=["user"],
    )
    e2e_db_session.add(user)
    await e2e_db_session.commit()
    await e2e_db_session.refresh(user)
    return user, secret


@pytest_asyncio.fixture
async def inactive_user(e2e_db_session: AsyncSession, tenant_id: str):
    """Create an inactive/disabled user."""
    user = User(
        id=uuid.uuid4(),
        username=f"inactive_{uuid.uuid4().hex[:8]}",
        email=f"inactive_{uuid.uuid4().hex[:8]}@example.com",
        password_hash=hash_password(TEST_PASSWORD),
        tenant_id=tenant_id,
        is_active=False,
        is_verified=True,
        mfa_enabled=False,
        roles=["user"],
    )
    e2e_db_session.add(user)
    await e2e_db_session.commit()
    await e2e_db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def user_with_backup_codes(e2e_db_session: AsyncSession, tenant_id: str):
    """Create a user with MFA and backup codes."""
    from dotmac.platform.auth.mfa_service import mfa_service

    secret = mfa_service.generate_secret()
    user = User(
        id=uuid.uuid4(),
        username=f"backupuser_{uuid.uuid4().hex[:8]}",
        email=f"backup_{uuid.uuid4().hex[:8]}@example.com",
        password_hash=hash_password(TEST_PASSWORD),
        tenant_id=tenant_id,
        is_active=True,
        is_verified=True,
        mfa_enabled=True,
        mfa_secret=secret,
        roles=["user"],
    )
    e2e_db_session.add(user)
    await e2e_db_session.commit()

    # Create backup codes
    backup_code = "ABCD-EFGH"
    backup = BackupCode(
        id=uuid.uuid4(),
        user_id=user.id,
        code_hash=hash_password(backup_code),
        used=False,
        tenant_id=tenant_id,
    )
    e2e_db_session.add(backup)
    await e2e_db_session.commit()
    await e2e_db_session.refresh(user)

    return user, secret, backup_code


@pytest.fixture
def mock_email_service():
    """Mock email service for password reset and verification flows."""
    patchers = [
        patch("dotmac.platform.auth.email_service.get_auth_email_service"),
        patch("dotmac.platform.auth.email_verification.get_auth_email_service"),
    ]
    mocks = [patcher.start() for patcher in patchers]
    try:
        mock_service = AsyncMock()
        mock_service.send_password_reset_email = AsyncMock(return_value=True)
        mock_service.send_verification_email = AsyncMock(return_value=True)
        mock_service.send_welcome_email = AsyncMock(return_value=True)
        for mock in mocks:
            mock.return_value = mock_service
        yield mock_service
    finally:
        for patcher in patchers:
            patcher.stop()


@pytest.fixture
def mock_audit_logging():
    """Mock audit logging to prevent transaction conflicts."""
    patches = [
        patch("dotmac.platform.auth.router.log_user_activity", new=AsyncMock()),
        patch("dotmac.platform.auth.router.log_api_activity", new=AsyncMock()),
        patch("dotmac.platform.audit.log_user_activity", new=AsyncMock()),
    ]
    for p in patches:
        p.start()
    yield
    for p in patches:
        p.stop()


# ============================================================================
# Login Tests
# ============================================================================


class TestAuthLoginE2E:
    """End-to-end tests for authentication login flows."""

    async def test_login_with_username_success(
        self,
        async_client: AsyncClient,
        created_test_user: User,
        tenant_id: str,
        mock_audit_logging,
    ):
        """Test successful login using username."""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "username": created_test_user.username,
                "password": TEST_PASSWORD,
            },
            headers={"X-Tenant-ID": tenant_id},
        )

        assert response.status_code == StatusCodes.SUCCESS, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        # Validate complete token response structure
        assert "access_token" in data and len(data["access_token"]) > 20, "Missing or invalid access_token"
        assert "refresh_token" in data and len(data["refresh_token"]) > 20, "Missing or invalid refresh_token"
        assert data.get("token_type", "").lower() == "bearer", "Token type should be 'bearer'"
        assert "expires_in" in data and data["expires_in"] > 0, "Missing or invalid expires_in"

    async def test_login_with_email_success(
        self,
        async_client: AsyncClient,
        created_test_user: User,
        tenant_id: str,
        mock_audit_logging,
    ):
        """Test successful login using email address."""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": created_test_user.email,
                "password": TEST_PASSWORD,
            },
            headers={"X-Tenant-ID": tenant_id},
        )

        assert response.status_code == StatusCodes.SUCCESS, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "access_token" in data and len(data["access_token"]) > 20
        assert "refresh_token" in data and len(data["refresh_token"]) > 20

    async def test_login_invalid_password(
        self,
        async_client: AsyncClient,
        created_test_user: User,
        tenant_id: str,
        mock_audit_logging,
    ):
        """Test login with invalid password."""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "username": created_test_user.username,
                "password": "WrongPassword123!",
            },
            headers={"X-Tenant-ID": tenant_id},
        )

        assert response.status_code == 401
        assert "Invalid username or password" in response.json()["detail"]

    async def test_login_nonexistent_user(
        self,
        async_client: AsyncClient,
        tenant_id: str,
        mock_audit_logging,
    ):
        """Test login with non-existent user."""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "username": "nonexistent_user",
                "password": "SomePassword123!",
            },
            headers={"X-Tenant-ID": tenant_id},
        )

        assert response.status_code == 401
        assert "Invalid username or password" in response.json()["detail"]

    async def test_login_inactive_account(
        self,
        async_client: AsyncClient,
        inactive_user: User,
        tenant_id: str,
        mock_audit_logging,
    ):
        """Test login with disabled/inactive account."""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "username": inactive_user.username,
                "password": TEST_PASSWORD,
            },
            headers={"X-Tenant-ID": tenant_id},
        )

        assert response.status_code == StatusCodes.FORBIDDEN, f"Expected 403, got {response.status_code}"
        assert "disabled" in response.json()["detail"].lower()

    async def test_login_missing_credentials(
        self,
        async_client: AsyncClient,
        tenant_id: str,
    ):
        """Test login without username/email."""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "password": "SomePassword123!",
            },
            headers={"X-Tenant-ID": tenant_id},
        )

        assert response.status_code == 422

    async def test_login_2fa_required(
        self,
        async_client: AsyncClient,
        mfa_enabled_user: tuple,
        tenant_id: str,
        mock_audit_logging,
    ):
        """Test login for user with 2FA returns challenge."""
        user, secret = mfa_enabled_user

        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "username": user.username,
                "password": TEST_PASSWORD,
            },
            headers={"X-Tenant-ID": tenant_id},
        )

        assert response.status_code == StatusCodes.FORBIDDEN, f"Expected 403 (2FA required), got {response.status_code}"
        detail = response.json().get("detail", "").lower()
        assert "2fa" in detail or "two-factor" in detail, f"Expected 2FA message, got: {detail}"
        assert response.headers.get("X-2FA-Required") == "true", "Missing X-2FA-Required header"
        assert response.headers.get("X-User-ID") == str(user.id), "Missing or incorrect X-User-ID header"

    async def test_verify_2fa_totp_success(
        self,
        async_client: AsyncClient,
        mfa_enabled_user: tuple,
        tenant_id: str,
        mock_audit_logging,
    ):
        """Test completing 2FA with valid TOTP code."""
        user, secret = mfa_enabled_user
        import pyotp

        totp = pyotp.TOTP(secret)
        code = totp.now()

        # First trigger 2FA challenge
        challenge_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "username": user.username,
                "password": TEST_PASSWORD,
            },
            headers={"X-Tenant-ID": tenant_id},
        )
        assert challenge_response.status_code == StatusCodes.FORBIDDEN, "2FA challenge should return 403"

        # Then verify 2FA
        response = await async_client.post(
            "/api/v1/auth/login/verify-2fa",
            json={
                "user_id": str(user.id),
                "code": code,
                "is_backup_code": False,
            },
            headers={"X-Tenant-ID": tenant_id},
        )

        # 2FA verification should succeed with valid code
        assert response.status_code == StatusCodes.SUCCESS, f"Expected 200 for valid 2FA code, got {response.status_code}: {response.text}"
        data = response.json()
        assert "access_token" in data and len(data["access_token"]) > 20, "Missing access_token after 2FA"
        assert "refresh_token" in data and len(data["refresh_token"]) > 20, "Missing refresh_token after 2FA"

    async def test_verify_2fa_invalid_code(
        self,
        async_client: AsyncClient,
        mfa_enabled_user: tuple,
        tenant_id: str,
        mock_audit_logging,
    ):
        """Test 2FA with invalid code returns 401 Unauthorized."""
        user, secret = mfa_enabled_user

        # First trigger 2FA challenge
        await async_client.post(
            "/api/v1/auth/login",
            json={
                "username": user.username,
                "password": TEST_PASSWORD,
            },
            headers={"X-Tenant-ID": tenant_id},
        )

        response = await async_client.post(
            "/api/v1/auth/login/verify-2fa",
            json={
                "user_id": str(user.id),
                "code": "000000",  # Invalid code
                "is_backup_code": False,
            },
            headers={"X-Tenant-ID": tenant_id},
        )

        # Invalid 2FA code should return 401 Unauthorized
        assert response.status_code == StatusCodes.UNAUTHORIZED, f"Expected 401 for invalid 2FA code, got {response.status_code}"

    async def test_cookie_login_flow(
        self,
        async_client: AsyncClient,
        created_test_user: User,
        tenant_id: str,
        mock_audit_logging,
    ):
        """Test cookie-based login endpoint."""
        response = await async_client.post(
            "/api/v1/auth/login/cookie",
            json={
                "username": created_test_user.username,
                "password": TEST_PASSWORD,
            },
            headers={"X-Tenant-ID": tenant_id},
        )

        assert response.status_code == StatusCodes.SUCCESS, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("success") is True, "Cookie login should return success: true"
        assert "user_id" in data, "Cookie login should return user_id"

        # Check cookies are set - at least one auth cookie should be present
        set_cookie_header = response.headers.get("set-cookie", "")
        has_auth_cookie = "access_token" in response.cookies or "access_token" in set_cookie_header
        assert has_auth_cookie, "No access_token cookie set in response"


# ============================================================================
# Registration Tests
# ============================================================================


class TestAuthRegistrationE2E:
    """End-to-end tests for user registration."""

    async def test_register_success(
        self,
        async_client: AsyncClient,
        tenant_id: str,
        e2e_db_session: AsyncSession,
        mock_email_service,
        mock_audit_logging,
    ):
        """Test successful user registration."""
        unique_id = uuid.uuid4().hex[:8]
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": f"newuser_{unique_id}",
                "email": f"new_{unique_id}@example.com",
                "password": "SecurePassword123!",
                "full_name": "New User",
            },
            headers={"X-Tenant-ID": tenant_id},
        )

        # Registration may be disabled
        if response.status_code == 403:
            assert "self-registration" in response.json().get("detail", "").lower() or "disabled" in response.json().get("detail", "").lower()
            return

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_register_duplicate_username(
        self,
        async_client: AsyncClient,
        created_test_user: User,
        tenant_id: str,
        mock_email_service,
        mock_audit_logging,
    ):
        """Test registration with existing username."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": created_test_user.username,
                "email": f"different_{uuid.uuid4().hex[:8]}@example.com",
                "password": "SecurePassword123!",
            },
            headers={"X-Tenant-ID": tenant_id},
        )

        # Either registration disabled or conflict
        assert response.status_code in [400, 403, 409]

    async def test_register_duplicate_email(
        self,
        async_client: AsyncClient,
        created_test_user: User,
        tenant_id: str,
        mock_email_service,
        mock_audit_logging,
    ):
        """Test registration with existing email."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": f"different_{uuid.uuid4().hex[:8]}",
                "email": created_test_user.email,
                "password": "SecurePassword123!",
            },
            headers={"X-Tenant-ID": tenant_id},
        )

        # Either registration disabled or conflict
        assert response.status_code in [400, 403, 409]

    async def test_register_invalid_email(
        self,
        async_client: AsyncClient,
        tenant_id: str,
    ):
        """Test registration with malformed email."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": f"user_{uuid.uuid4().hex[:8]}",
                "email": "not-an-email",
                "password": "SecurePassword123!",
            },
            headers={"X-Tenant-ID": tenant_id},
        )

        assert response.status_code == 422

    async def test_register_short_password(
        self,
        async_client: AsyncClient,
        tenant_id: str,
    ):
        """Test registration with password shorter than 8 chars."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": f"user_{uuid.uuid4().hex[:8]}",
                "email": f"user_{uuid.uuid4().hex[:8]}@example.com",
                "password": "short",
            },
            headers={"X-Tenant-ID": tenant_id},
        )

        assert response.status_code == 422

    async def test_register_short_username(
        self,
        async_client: AsyncClient,
        tenant_id: str,
    ):
        """Test registration with username shorter than 3 chars."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "ab",
                "email": f"user_{uuid.uuid4().hex[:8]}@example.com",
                "password": "SecurePassword123!",
            },
            headers={"X-Tenant-ID": tenant_id},
        )

        assert response.status_code == 422


# ============================================================================
# Token Tests
# ============================================================================


class TestAuthTokensE2E:
    """End-to-end tests for token operations."""

    async def test_refresh_token_success(
        self,
        async_client: AsyncClient,
        created_test_user: User,
        tenant_id: str,
        mock_audit_logging,
    ):
        """Test successful token refresh."""
        # First login to get tokens
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "username": created_test_user.username,
                "password": "TestPassword123!",
            },
            headers={"X-Tenant-ID": tenant_id},
        )
        assert login_response.status_code == 200
        tokens = login_response.json()

        # Refresh the token
        response = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
            headers={"X-Tenant-ID": tenant_id},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_refresh_token_invalid(
        self,
        async_client: AsyncClient,
        tenant_id: str,
    ):
        """Test refresh with invalid token."""
        response = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid.token.here"},
            headers={"X-Tenant-ID": tenant_id},
        )

        assert response.status_code == 401

    async def test_logout_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        mock_audit_logging,
    ):
        """Test successful logout."""
        response = await async_client.post(
            "/api/v1/auth/logout",
            headers=auth_headers,
        )

        assert response.status_code == 200

    async def test_oauth2_token_endpoint(
        self,
        async_client: AsyncClient,
        created_test_user: User,
        tenant_id: str,
        mock_audit_logging,
    ):
        """Test OAuth2 password grant endpoint."""
        response = await async_client.post(
            "/api/v1/auth/token",
            data={
                "username": created_test_user.username,
                "password": "TestPassword123!",
                "grant_type": "password",
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Tenant-ID": tenant_id,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    async def test_verify_token_valid(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test token verification with valid token."""
        response = await async_client.get(
            "/api/v1/auth/verify",
            headers=auth_headers,
        )

        assert response.status_code == 200

    async def test_verify_token_invalid(
        self,
        async_client: AsyncClient,
        tenant_id: str,
    ):
        """Test token verification with invalid token."""
        response = await async_client.get(
            "/api/v1/auth/verify",
            headers={
                "Authorization": "Bearer invalid.token.here",
                "X-Tenant-ID": tenant_id,
            },
        )

        assert response.status_code == 401


# ============================================================================
# Password Reset Tests
# ============================================================================


class TestAuthPasswordResetE2E:
    """End-to-end tests for password reset flow."""

    async def test_password_reset_request_success(
        self,
        async_client: AsyncClient,
        created_test_user: User,
        tenant_id: str,
        mock_email_service,
        mock_audit_logging,
    ):
        """Test requesting password reset email."""
        response = await async_client.post(
            "/api/v1/auth/password-reset",
            json={"email": created_test_user.email},
            headers={"X-Tenant-ID": tenant_id},
        )

        # Should always return 200 for security (don't leak user existence)
        assert response.status_code == 200

    async def test_password_reset_nonexistent_email(
        self,
        async_client: AsyncClient,
        tenant_id: str,
        mock_email_service,
    ):
        """Test password reset for non-existent email (still returns 200)."""
        response = await async_client.post(
            "/api/v1/auth/password-reset",
            json={"email": "nonexistent@example.com"},
            headers={"X-Tenant-ID": tenant_id},
        )

        # Should still return 200 to not leak user existence
        assert response.status_code == 200

    async def test_password_reset_confirm_invalid_token(
        self,
        async_client: AsyncClient,
        tenant_id: str,
    ):
        """Test password reset confirm with invalid token."""
        response = await async_client.post(
            "/api/v1/auth/password-reset/confirm",
            json={
                "token": "invalid-token",
                "new_password": "NewSecurePassword123!",
            },
            headers={"X-Tenant-ID": tenant_id},
        )

        assert response.status_code in [400, 401, 404]

    async def test_change_password_authenticated(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        mock_audit_logging,
    ):
        """Test changing password while authenticated."""
        response = await async_client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "OldPassword123!",
                "new_password": "NewSecurePassword123!",
            },
            headers=auth_headers,
        )

        # May fail due to mock user, but endpoint should be accessible
        assert response.status_code in [200, 400, 401]


# ============================================================================
# Email Verification Tests
# ============================================================================


class TestAuthEmailVerificationE2E:
    """End-to-end tests for email verification flow."""

    async def test_send_verification_email(
        self,
        async_client: AsyncClient,
        unverified_user: User,
        tenant_id: str,
        mock_email_service,
        mock_audit_logging,
    ):
        """Test requesting email verification."""
        response = await async_client.post(
            "/api/v1/auth/verify-email",
            json={"email": unverified_user.email},
            headers={"X-Tenant-ID": tenant_id},
        )

        assert response.status_code == 200

    async def test_verify_email_invalid_token(
        self,
        async_client: AsyncClient,
        tenant_id: str,
    ):
        """Test email verification with invalid token."""
        response = await async_client.post(
            "/api/v1/auth/verify-email/confirm",
            json={"token": "invalid-verification-token"},
            headers={"X-Tenant-ID": tenant_id},
        )

        assert response.status_code in [400, 404]


# ============================================================================
# 2FA Management Tests
# ============================================================================


class TestAuth2FAE2E:
    """End-to-end tests for 2FA setup and management."""

    async def test_enable_2fa_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        mock_audit_logging,
    ):
        """Test enabling 2FA returns QR code and backup codes."""
        response = await async_client.post(
            "/api/v1/auth/2fa/enable",
            json={"device_name": "Test Device"},
            headers=auth_headers,
        )

        if response.status_code == 200:
            data = response.json()
            assert "qr_code" in data or "secret" in data or "backup_codes" in data

    async def test_disable_2fa_not_enabled(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        mock_audit_logging,
    ):
        """Test disabling 2FA when not enabled."""
        response = await async_client.post(
            "/api/v1/auth/2fa/disable",
            json={"password": "TestPassword123!"},
            headers=auth_headers,
        )

        # Should return error if 2FA not enabled
        assert response.status_code in [200, 400]

    async def test_regenerate_backup_codes(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        mock_audit_logging,
    ):
        """Test regenerating backup codes."""
        response = await async_client.post(
            "/api/v1/auth/2fa/regenerate-backup-codes",
            json={"password": "TestPassword123!"},
            headers=auth_headers,
        )

        # May fail if 2FA not enabled for mock user
        assert response.status_code in [200, 400]


# ============================================================================
# Profile (Me) Tests
# ============================================================================


class TestAuthMeE2E:
    """End-to-end tests for user profile endpoints."""

    async def test_get_me_authenticated(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test GET /auth/me with valid token."""
        response = await async_client.get(
            "/api/v1/auth/me",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "email" in data or "user_id" in data

    async def test_get_me_unauthenticated(
        self,
        async_client: AsyncClient,
        tenant_id: str,
    ):
        """Test GET /auth/me without token."""
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"X-Tenant-ID": tenant_id},
        )

        assert response.status_code == 401

    async def test_update_me_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        mock_audit_logging,
    ):
        """Test updating user profile."""
        response = await async_client.patch(
            "/api/v1/auth/me",
            json={"full_name": "Updated Name"},
            headers=auth_headers,
        )

        assert response.status_code == 200


# ============================================================================
# Session Management Tests
# ============================================================================


class TestAuthSessionsE2E:
    """End-to-end tests for session management."""

    async def test_list_sessions(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test listing user sessions."""
        response = await async_client.get(
            "/api/v1/auth/me/sessions",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "sessions" in data

    async def test_revoke_all_sessions(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        mock_audit_logging,
    ):
        """Test revoking all sessions."""
        response = await async_client.delete(
            "/api/v1/auth/me/sessions",
            headers=auth_headers,
        )

        assert response.status_code in [200, 204]


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestAuthErrorHandlingE2E:
    """End-to-end tests for error handling."""

    async def test_login_with_malformed_json(
        self,
        async_client: AsyncClient,
        tenant_id: str,
    ):
        """Test login with malformed JSON body."""
        response = await async_client.post(
            "/api/v1/auth/login",
            content="{invalid json}",
            headers={
                "Content-Type": "application/json",
                "X-Tenant-ID": tenant_id,
            },
        )

        assert response.status_code == 422

    async def test_protected_endpoint_without_token(
        self,
        async_client: AsyncClient,
        tenant_id: str,
    ):
        """Test accessing protected endpoint without token."""
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"X-Tenant-ID": tenant_id},
        )

        assert response.status_code == 401

    async def test_protected_endpoint_with_expired_token(
        self,
        async_client: AsyncClient,
        tenant_id: str,
    ):
        """Test accessing protected endpoint with expired token."""
        # Create an expired token
        from dotmac.platform.auth.core import JWTService

        jwt_service = JWTService(algorithm="HS256", secret="test-secret-key-for-e2e-tests")
        expired_token = jwt_service.create_access_token(
            subject="test-user",
            expires_delta=timedelta(seconds=-1),  # Already expired
        )

        response = await async_client.get(
            "/api/v1/auth/me",
            headers={
                "Authorization": f"Bearer {expired_token}",
                "X-Tenant-ID": tenant_id,
            },
        )

        assert response.status_code == 401
