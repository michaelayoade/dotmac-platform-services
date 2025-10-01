"""Tests for password reset endpoints in auth router."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.auth.router import (
    PasswordResetConfirm,
    PasswordResetRequest,
    auth_router,
)
from dotmac.platform.user_management.models import User


@pytest.fixture
def mock_session():
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def mock_user():
    user = User(
        username="tester",
        email="tester@example.com",
        password_hash="hash",
    )
    user.id = uuid.uuid4()
    user.is_active = True
    user.roles = ["user"]
    user.tenant_id = "tenant-id"
    user.full_name = "Test User"
    return user


@pytest.fixture
def test_client():
    app = FastAPI()
    app.include_router(auth_router, prefix="/auth")
    return TestClient(app)


class TestRequestPasswordReset:
    """request_password_reset endpoint behaviour."""

    @pytest.mark.asyncio
    async def test_successful_request(self, mock_session, mock_user):
        from dotmac.platform.auth.router import request_password_reset

        service = AsyncMock()
        service.get_user_by_email.return_value = mock_user

        with patch('dotmac.platform.auth.router.UserService', return_value=service), \
            patch('dotmac.platform.auth.router.send_password_reset_email', return_value=(True, "token")) as send_email:
            response = await request_password_reset(
                PasswordResetRequest(email="tester@example.com"),
                mock_session,
            )

        assert response["message"] == "If the email exists, a password reset link has been sent."
        send_email.assert_called_once_with(email="tester@example.com", user_name="Test User")

    @pytest.mark.asyncio
    async def test_user_not_found(self, mock_session):
        from dotmac.platform.auth.router import request_password_reset

        service = AsyncMock()
        service.get_user_by_email.return_value = None

        with patch('dotmac.platform.auth.router.UserService', return_value=service), \
            patch('dotmac.platform.auth.router.send_password_reset_email') as send_email:
            response = await request_password_reset(
                PasswordResetRequest(email="missing@example.com"),
                mock_session,
            )

        assert response["message"] == "If the email exists, a password reset link has been sent."
        send_email.assert_not_called()

    @pytest.mark.asyncio
    async def test_inactive_user(self, mock_session, mock_user):
        from dotmac.platform.auth.router import request_password_reset

        mock_user.is_active = False
        service = AsyncMock()
        service.get_user_by_email.return_value = mock_user

        with patch('dotmac.platform.auth.router.UserService', return_value=service), \
            patch('dotmac.platform.auth.router.send_password_reset_email') as send_email:
            response = await request_password_reset(
                PasswordResetRequest(email="tester@example.com"),
                mock_session,
            )

        assert response["message"] == "If the email exists, a password reset link has been sent."
        send_email.assert_not_called()


class TestConfirmPasswordReset:
    """confirm_password_reset endpoint behaviour."""

    @pytest.mark.asyncio
    async def test_success(self, mock_session, mock_user):
        from dotmac.platform.auth.router import confirm_password_reset

        service = AsyncMock()
        service.get_user_by_email.return_value = mock_user

        with patch('dotmac.platform.auth.router.UserService', return_value=service), \
            patch('dotmac.platform.auth.router.verify_reset_token', return_value="tester@example.com"), \
            patch('dotmac.platform.auth.router.hash_password', return_value="new-hash"), \
            patch('dotmac.platform.auth.router.send_password_reset_success_email', return_value=True):
            response = await confirm_password_reset(
                PasswordResetConfirm(token="token", new_password="secret123"),
                MagicMock(),
                mock_session,
            )

        assert response["message"] == "Password has been reset successfully."
        assert mock_user.password_hash == "new-hash"
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalid_token(self, mock_session):
        from dotmac.platform.auth.router import confirm_password_reset

        with patch('dotmac.platform.auth.router.verify_reset_token', return_value=None):
            with pytest.raises(Exception) as exc:
                await confirm_password_reset(
                    PasswordResetConfirm(token="bad", new_password="secret123"),
                    AsyncMock(),
                    mock_session,
                )

        assert exc.value.status_code == 400
