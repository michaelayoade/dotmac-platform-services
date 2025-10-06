"""
Tests for Two-Factor Authentication (2FA) Login Flow.

Tests the complete 2FA login integration including:
- Login with 2FA enabled (challenge response)
- 2FA verification with TOTP codes
- 2FA verification with backup codes
- Session management during 2FA
- Error handling and edge cases
"""

import pytest
import uuid
from unittest.mock import patch, MagicMock
from httpx import AsyncClient
from fastapi import FastAPI
from sqlalchemy import select

from dotmac.platform.auth.router import auth_router
from dotmac.platform.auth.mfa_service import mfa_service
from dotmac.platform.auth.core import hash_password
from dotmac.platform.user_management.models import User, BackupCode
from dotmac.platform.auth.dependencies import UserInfo


@pytest.fixture
def app():
    """Create FastAPI app for testing."""
    app = FastAPI()
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
    return app


@pytest.fixture
async def test_user_with_2fa(async_db_session):
    """Create a test user with 2FA enabled."""
    secret = mfa_service.generate_secret()

    user = User(
        id=uuid.UUID("550e8400-e29b-41d4-a716-446655440001"),
        username="testuser_2fa",
        email="test2fa@example.com",
        password_hash=hash_password("test_password"),
        tenant_id="test-tenant",
        mfa_enabled=True,
        mfa_secret=secret,
        is_active=True,
        is_verified=True,
        phone_verified=False,
        is_superuser=False,
        is_platform_admin=False,
        failed_login_attempts=0,
        roles=[],
        permissions=[],
        metadata_={},
    )
    async_db_session.add(user)
    await async_db_session.commit()
    await async_db_session.refresh(user)
    return user


@pytest.fixture
async def test_user_without_2fa(async_db_session):
    """Create a test user without 2FA."""
    user = User(
        id=uuid.UUID("550e8400-e29b-41d4-a716-446655440002"),
        username="testuser_no2fa",
        email="testno2fa@example.com",
        password_hash=hash_password("test_password"),
        tenant_id="test-tenant",
        mfa_enabled=False,
        mfa_secret=None,
        is_active=True,
        is_verified=True,
        phone_verified=False,
        is_superuser=False,
        is_platform_admin=False,
        failed_login_attempts=0,
        roles=[],
        permissions=[],
        metadata_={},
    )
    async_db_session.add(user)
    await async_db_session.commit()
    await async_db_session.refresh(user)
    return user


@pytest.fixture
async def client(app, async_db_session):
    """Create async test client."""
    from httpx import ASGITransport
    from dotmac.platform.db import get_session_dependency

    app.dependency_overrides[get_session_dependency] = lambda: async_db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ========================================
# Login Flow Tests
# ========================================


@pytest.mark.asyncio
async def test_login_without_2fa_success(
    client: AsyncClient,
    test_user_without_2fa: User,
):
    """Test successful login for user without 2FA enabled."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": test_user_without_2fa.username,
            "password": "test_password",
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Should receive tokens immediately
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_with_2fa_returns_challenge(
    client: AsyncClient,
    test_user_with_2fa: User,
):
    """Test login with 2FA returns challenge instead of tokens."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": test_user_with_2fa.username,
            "password": "test_password",
        },
    )

    # Should return 403 with 2FA required headers
    assert response.status_code == 403
    assert response.json()["detail"] == "2FA verification required"

    # Check headers
    assert response.headers.get("X-2FA-Required") == "true"
    assert response.headers.get("X-User-ID") == str(test_user_with_2fa.id)


@pytest.mark.asyncio
async def test_login_with_2fa_creates_pending_session(
    client: AsyncClient,
    test_user_with_2fa: User,
):
    """Test that login with 2FA creates a pending session."""
    from dotmac.platform.auth.session_manager import session_manager

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": test_user_with_2fa.username,
            "password": "test_password",
        },
    )

    assert response.status_code == 403

    # Verify pending session exists
    session_data = await session_manager.get_session(f"2fa_pending:{test_user_with_2fa.id}")
    assert session_data is not None
    assert session_data["username"] == test_user_with_2fa.username
    assert session_data["pending_2fa"] is True


# ========================================
# 2FA Verification Tests
# ========================================


@pytest.mark.asyncio
async def test_verify_2fa_with_valid_totp(
    client: AsyncClient,
    test_user_with_2fa: User,
):
    """Test successful 2FA verification with TOTP code."""
    # First, login to create pending session
    await client.post(
        "/api/v1/auth/login",
        json={
            "username": test_user_with_2fa.username,
            "password": "test_password",
        },
    )

    # Get current TOTP token
    token = mfa_service.get_current_token(test_user_with_2fa.mfa_secret)

    # Verify 2FA
    response = await client.post(
        "/api/v1/auth/login/verify-2fa",
        json={
            "user_id": str(test_user_with_2fa.id),
            "code": token,
            "is_backup_code": False,
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Should receive tokens
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_verify_2fa_with_invalid_totp(
    client: AsyncClient,
    test_user_with_2fa: User,
):
    """Test 2FA verification with invalid TOTP code."""
    # First, login to create pending session
    await client.post(
        "/api/v1/auth/login",
        json={
            "username": test_user_with_2fa.username,
            "password": "test_password",
        },
    )

    # Verify with invalid code
    response = await client.post(
        "/api/v1/auth/login/verify-2fa",
        json={
            "user_id": str(test_user_with_2fa.id),
            "code": "000000",
            "is_backup_code": False,
        },
    )

    assert response.status_code == 401
    assert "Invalid 2FA code" in response.json()["detail"]


@pytest.mark.asyncio
async def test_verify_2fa_without_pending_session(
    client: AsyncClient,
    test_user_with_2fa: User,
):
    """Test 2FA verification without pending session fails."""
    token = mfa_service.get_current_token(test_user_with_2fa.mfa_secret)

    response = await client.post(
        "/api/v1/auth/login/verify-2fa",
        json={
            "user_id": str(test_user_with_2fa.id),
            "code": token,
            "is_backup_code": False,
        },
    )

    assert response.status_code == 400
    assert "2FA session expired" in response.json()["detail"]


@pytest.mark.asyncio
async def test_verify_2fa_deletes_pending_session(
    client: AsyncClient,
    test_user_with_2fa: User,
):
    """Test that successful 2FA verification deletes pending session."""
    from dotmac.platform.auth.session_manager import session_manager

    # Login to create pending session
    await client.post(
        "/api/v1/auth/login",
        json={
            "username": test_user_with_2fa.username,
            "password": "test_password",
        },
    )

    # Verify pending session exists
    session_data = await session_manager.get_session(f"2fa_pending:{test_user_with_2fa.id}")
    assert session_data is not None

    # Verify 2FA
    token = mfa_service.get_current_token(test_user_with_2fa.mfa_secret)
    await client.post(
        "/api/v1/auth/login/verify-2fa",
        json={
            "user_id": str(test_user_with_2fa.id),
            "code": token,
            "is_backup_code": False,
        },
    )

    # Verify pending session was deleted
    session_data = await session_manager.get_session(f"2fa_pending:{test_user_with_2fa.id}")
    assert session_data is None


# ========================================
# Backup Code Verification Tests
# ========================================


@pytest.mark.asyncio
async def test_verify_2fa_with_valid_backup_code(
    client: AsyncClient,
    test_user_with_2fa: User,
    async_db_session,
):
    """Test successful 2FA verification with backup code."""
    # Create backup codes
    backup_codes = mfa_service.generate_backup_codes(count=10)
    await mfa_service.store_backup_codes(
        user_id=test_user_with_2fa.id,
        codes=backup_codes,
        session=async_db_session,
        tenant_id=test_user_with_2fa.tenant_id,
    )

    # Login to create pending session
    await client.post(
        "/api/v1/auth/login",
        json={
            "username": test_user_with_2fa.username,
            "password": "test_password",
        },
    )

    # Verify with backup code
    response = await client.post(
        "/api/v1/auth/login/verify-2fa",
        json={
            "user_id": str(test_user_with_2fa.id),
            "code": backup_codes[0],
            "is_backup_code": True,
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Should receive tokens
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_verify_2fa_with_used_backup_code(
    client: AsyncClient,
    test_user_with_2fa: User,
    async_db_session,
):
    """Test that used backup codes cannot be reused."""
    # Create backup codes
    backup_codes = mfa_service.generate_backup_codes(count=10)
    await mfa_service.store_backup_codes(
        user_id=test_user_with_2fa.id,
        codes=backup_codes,
        session=async_db_session,
        tenant_id=test_user_with_2fa.tenant_id,
    )

    # Login and verify with backup code
    await client.post(
        "/api/v1/auth/login",
        json={
            "username": test_user_with_2fa.username,
            "password": "test_password",
        },
    )

    await client.post(
        "/api/v1/auth/login/verify-2fa",
        json={
            "user_id": str(test_user_with_2fa.id),
            "code": backup_codes[0],
            "is_backup_code": True,
        },
    )

    # Try to login again with same backup code
    await client.post(
        "/api/v1/auth/login",
        json={
            "username": test_user_with_2fa.username,
            "password": "test_password",
        },
    )

    response = await client.post(
        "/api/v1/auth/login/verify-2fa",
        json={
            "user_id": str(test_user_with_2fa.id),
            "code": backup_codes[0],
            "is_backup_code": True,
        },
    )

    assert response.status_code == 401
    assert "Invalid 2FA code" in response.json()["detail"]


@pytest.mark.asyncio
async def test_backup_code_marked_as_used(
    client: AsyncClient,
    test_user_with_2fa: User,
    async_db_session,
):
    """Test that backup codes are marked as used after verification."""
    # Create backup codes
    backup_codes = mfa_service.generate_backup_codes(count=10)
    await mfa_service.store_backup_codes(
        user_id=test_user_with_2fa.id,
        codes=backup_codes,
        session=async_db_session,
        tenant_id=test_user_with_2fa.tenant_id,
    )

    # Login and verify with backup code
    await client.post(
        "/api/v1/auth/login",
        json={
            "username": test_user_with_2fa.username,
            "password": "test_password",
        },
    )

    await client.post(
        "/api/v1/auth/login/verify-2fa",
        json={
            "user_id": str(test_user_with_2fa.id),
            "code": backup_codes[0],
            "is_backup_code": True,
        },
    )

    # Check that backup code is marked as used
    result = await async_db_session.execute(
        select(BackupCode).where(
            BackupCode.user_id == test_user_with_2fa.id,
            BackupCode.used == True,
        )
    )
    used_codes = result.scalars().all()
    assert len(used_codes) == 1
    assert used_codes[0].used is True
    assert used_codes[0].used_at is not None


# ========================================
# Edge Cases and Error Handling
# ========================================


@pytest.mark.asyncio
async def test_login_with_incorrect_password(
    client: AsyncClient,
    test_user_with_2fa: User,
):
    """Test login with incorrect password."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": test_user_with_2fa.username,
            "password": "wrong_password",
        },
    )

    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]


@pytest.mark.asyncio
async def test_verify_2fa_for_nonexistent_user(
    client: AsyncClient,
):
    """Test 2FA verification for nonexistent user."""
    response = await client.post(
        "/api/v1/auth/login/verify-2fa",
        json={
            "user_id": str(uuid.uuid4()),
            "code": "123456",
            "is_backup_code": False,
        },
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_verify_2fa_for_user_without_2fa(
    client: AsyncClient,
    test_user_without_2fa: User,
):
    """Test 2FA verification for user without 2FA enabled."""
    response = await client.post(
        "/api/v1/auth/login/verify-2fa",
        json={
            "user_id": str(test_user_without_2fa.id),
            "code": "123456",
            "is_backup_code": False,
        },
    )

    assert response.status_code == 400
    assert "2FA is not enabled" in response.json()["detail"]
