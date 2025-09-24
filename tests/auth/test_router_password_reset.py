"""Tests for password reset functionality in auth router."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
import uuid

from dotmac.platform.auth.router import (
    PasswordResetRequest,
    PasswordResetConfirm,
    auth_router,
)
from dotmac.platform.auth.email_service import NotificationResponse, NotificationStatus
from dotmac.platform.user_management.models import User
from dotmac.platform.communications import NotificationType


@pytest.fixture
def mock_session():
    """Create mock async session."""
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
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
def mock_user_service():
    """Create mock user service."""
    service = MagicMock()
    return service


@pytest.fixture
def mock_email_service():
    """Create mock email service."""
    service = MagicMock()
    service.send_password_reset_email.return_value = (
        NotificationResponse(
            id="test-notification",
            status=NotificationStatus.SENT,
            message="Password reset email sent",
            metadata={"timestamp": datetime.now(timezone.utc).isoformat()}
        ),
        "test-reset-token"
    )
    service.send_password_reset_success_email.return_value = NotificationResponse(
        id="test-notification-2",
        status=NotificationStatus.SENT,
        message="Password reset success email sent",
        metadata={"timestamp": datetime.now(timezone.utc).isoformat()}
    )
    service.verify_reset_token.return_value = "test@example.com"
    return service


@pytest.fixture
def test_client():
    """Create test client for the auth router."""
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(auth_router, prefix="/auth")
    return TestClient(app)


class TestPasswordResetRequest:
    """Test password reset request endpoint."""

    @pytest.mark.asyncio
    async def test_request_password_reset_success(
        self, mock_session, mock_user, mock_user_service, mock_email_service
    ):
        """Test successful password reset request."""
        from dotmac.platform.auth.router import request_password_reset
        from dotmac.platform.user_management.service import UserService

        # Setup mocks
        mock_user_service.get_user_by_email = AsyncMock(return_value=mock_user)

        with patch('dotmac.platform.auth.router.UserService', return_value=mock_user_service):
            with patch('dotmac.platform.auth.router.get_auth_email_service', return_value=mock_email_service):
                result = await request_password_reset(
                    PasswordResetRequest(email="test@example.com"),
                    mock_session
                )

        assert result["message"] == "If the email exists, a password reset link has been sent."
        mock_user_service.get_user_by_email.assert_called_once_with("test@example.com")
        mock_email_service.send_password_reset_email.assert_called_once_with(
            email="test@example.com",
            user_name="Test User"
        )

    @pytest.mark.asyncio
    async def test_request_password_reset_user_not_found(
        self, mock_session, mock_user_service, mock_email_service
    ):
        """Test password reset request when user not found."""
        from dotmac.platform.auth.router import request_password_reset

        # User doesn't exist
        mock_user_service.get_user_by_email = AsyncMock(return_value=None)

        with patch('dotmac.platform.auth.router.UserService', return_value=mock_user_service):
            with patch('dotmac.platform.auth.router.get_auth_email_service', return_value=mock_email_service):
                result = await request_password_reset(
                    PasswordResetRequest(email="nonexistent@example.com"),
                    mock_session
                )

        # Should still return success message (prevent email enumeration)
        assert result["message"] == "If the email exists, a password reset link has been sent."
        mock_email_service.send_password_reset_email.assert_not_called()

    @pytest.mark.asyncio
    async def test_request_password_reset_inactive_user(
        self, mock_session, mock_user, mock_user_service, mock_email_service
    ):
        """Test password reset request for inactive user."""
        from dotmac.platform.auth.router import request_password_reset

        # User is inactive
        mock_user.is_active = False
        mock_user_service.get_user_by_email = AsyncMock(return_value=mock_user)

        with patch('dotmac.platform.auth.router.UserService', return_value=mock_user_service):
            with patch('dotmac.platform.auth.router.get_auth_email_service', return_value=mock_email_service):
                result = await request_password_reset(
                    PasswordResetRequest(email="test@example.com"),
                    mock_session
                )

        # Should still return success message but not send email
        assert result["message"] == "If the email exists, a password reset link has been sent."
        mock_email_service.send_password_reset_email.assert_not_called()

    @pytest.mark.asyncio
    async def test_request_password_reset_email_failure(
        self, mock_session, mock_user, mock_user_service, mock_email_service
    ):
        """Test password reset request when email sending fails."""
        from dotmac.platform.auth.router import request_password_reset

        mock_user_service.get_user_by_email = AsyncMock(return_value=mock_user)
        mock_email_service.send_password_reset_email.side_effect = Exception("Email service error")

        with patch('dotmac.platform.auth.router.UserService', return_value=mock_user_service):
            with patch('dotmac.platform.auth.router.get_auth_email_service', return_value=mock_email_service):
                # Should not raise exception, just log error
                result = await request_password_reset(
                    PasswordResetRequest(email="test@example.com"),
                    mock_session
                )

        assert result["message"] == "If the email exists, a password reset link has been sent."


class TestPasswordResetConfirm:
    """Test password reset confirmation endpoint."""

    @pytest.mark.asyncio
    async def test_confirm_password_reset_success(
        self, mock_session, mock_user, mock_user_service, mock_email_service
    ):
        """Test successful password reset confirmation."""
        from dotmac.platform.auth.router import confirm_password_reset

        mock_user_service.get_user_by_email = AsyncMock(return_value=mock_user)
        mock_email_service.verify_reset_token.return_value = "test@example.com"

        with patch('dotmac.platform.auth.router.UserService', return_value=mock_user_service):
            with patch('dotmac.platform.auth.router.get_auth_email_service', return_value=mock_email_service):
                with patch('dotmac.platform.auth.router.hash_password', return_value="new_hashed_password"):
                    result = await confirm_password_reset(
                        PasswordResetConfirm(token="valid-token", new_password="newpassword123"),
                        mock_session
                    )

        assert result["message"] == "Password has been reset successfully."
        assert mock_user.password_hash == "new_hashed_password"
        mock_session.commit.assert_called_once()
        mock_email_service.send_password_reset_success_email.assert_called_once_with(
            email="test@example.com",
            user_name="Test User"
        )

    @pytest.mark.asyncio
    async def test_confirm_password_reset_invalid_token(
        self, mock_session, mock_email_service
    ):
        """Test password reset confirmation with invalid token."""
        from dotmac.platform.auth.router import confirm_password_reset

        mock_email_service.verify_reset_token.return_value = None

        with patch('dotmac.platform.auth.router.get_auth_email_service', return_value=mock_email_service):
            with pytest.raises(HTTPException) as exc_info:
                await confirm_password_reset(
                    PasswordResetConfirm(token="invalid-token", new_password="newpassword123"),
                    mock_session
                )

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "Invalid or expired reset token"

    @pytest.mark.asyncio
    async def test_confirm_password_reset_user_not_found(
        self, mock_session, mock_user_service, mock_email_service
    ):
        """Test password reset confirmation when user not found."""
        from dotmac.platform.auth.router import confirm_password_reset

        mock_user_service.get_user_by_email = AsyncMock(return_value=None)
        mock_email_service.verify_reset_token.return_value = "test@example.com"

        with patch('dotmac.platform.auth.router.UserService', return_value=mock_user_service):
            with patch('dotmac.platform.auth.router.get_auth_email_service', return_value=mock_email_service):
                with pytest.raises(HTTPException) as exc_info:
                    await confirm_password_reset(
                        PasswordResetConfirm(token="valid-token", new_password="newpassword123"),
                        mock_session
                    )

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "User not found"

    @pytest.mark.asyncio
    async def test_confirm_password_reset_database_error(
        self, mock_session, mock_user, mock_user_service, mock_email_service
    ):
        """Test password reset confirmation with database error."""
        from dotmac.platform.auth.router import confirm_password_reset

        mock_user_service.get_user_by_email = AsyncMock(return_value=mock_user)
        mock_email_service.verify_reset_token.return_value = "test@example.com"
        mock_session.commit.side_effect = Exception("Database error")

        with patch('dotmac.platform.auth.router.UserService', return_value=mock_user_service):
            with patch('dotmac.platform.auth.router.get_auth_email_service', return_value=mock_email_service):
                with patch('dotmac.platform.auth.router.hash_password', return_value="new_hashed_password"):
                    with pytest.raises(HTTPException) as exc_info:
                        await confirm_password_reset(
                            PasswordResetConfirm(token="valid-token", new_password="newpassword123"),
                            mock_session
                        )

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc_info.value.detail == "Failed to reset password"
        mock_session.rollback.assert_called_once()


class TestGetCurrentUser:
    """Test get current user endpoint."""

    @pytest.mark.asyncio
    async def test_get_current_user_success(
        self, mock_session, mock_user, mock_user_service
    ):
        """Test successful get current user."""
        from dotmac.platform.auth.router import get_current_user
        from fastapi.security import HTTPAuthorizationCredentials

        mock_user_service.get_user_by_id = AsyncMock(return_value=mock_user)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid-token")

        with patch('dotmac.platform.auth.router.UserService', return_value=mock_user_service):
            with patch('dotmac.platform.auth.router.jwt_service') as mock_jwt:
                mock_jwt.verify_token.return_value = {
                    "sub": str(mock_user.id),
                    "username": mock_user.username,
                    "email": mock_user.email
                }

                result = await get_current_user(credentials, mock_session)

        assert result["id"] == str(mock_user.id)
        assert result["username"] == "testuser"
        assert result["email"] == "test@example.com"
        assert result["full_name"] == "Test User"
        assert result["roles"] == ["user"]
        assert result["is_active"] is True
        assert result["tenant_id"] == "test-tenant"

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(
        self, mock_session
    ):
        """Test get current user with invalid token."""
        from dotmac.platform.auth.router import get_current_user
        from fastapi.security import HTTPAuthorizationCredentials

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid-token")

        with patch('dotmac.platform.auth.router.jwt_service') as mock_jwt:
            mock_jwt.verify_token.side_effect = Exception("Invalid token")

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials, mock_session)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Invalid or expired token"

    @pytest.mark.asyncio
    async def test_get_current_user_missing_user_id(
        self, mock_session
    ):
        """Test get current user with token missing user ID."""
        from dotmac.platform.auth.router import get_current_user
        from fastapi.security import HTTPAuthorizationCredentials

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid-token")

        with patch('dotmac.platform.auth.router.jwt_service') as mock_jwt:
            mock_jwt.verify_token.return_value = {
                "username": "testuser",
                "email": "test@example.com"
                # Missing 'sub' field
            }

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials, mock_session)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Invalid token"

    @pytest.mark.asyncio
    async def test_get_current_user_not_found(
        self, mock_session, mock_user_service
    ):
        """Test get current user when user not found in database."""
        from dotmac.platform.auth.router import get_current_user
        from fastapi.security import HTTPAuthorizationCredentials

        mock_user_service.get_user_by_id = AsyncMock(return_value=None)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid-token")

        with patch('dotmac.platform.auth.router.UserService', return_value=mock_user_service):
            with patch('dotmac.platform.auth.router.jwt_service') as mock_jwt:
                mock_jwt.verify_token.return_value = {
                    "sub": "user-id",
                    "username": "testuser",
                    "email": "test@example.com"
                }

                with pytest.raises(HTTPException) as exc_info:
                    await get_current_user(credentials, mock_session)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "User not found"


class TestPasswordResetModels:
    """Test password reset request/response models."""

    def test_password_reset_request_model(self):
        """Test PasswordResetRequest model."""
        request = PasswordResetRequest(email="test@example.com")
        assert request.email == "test@example.com"

    def test_password_reset_confirm_model(self):
        """Test PasswordResetConfirm model."""
        confirm = PasswordResetConfirm(
            token="reset-token",
            new_password="newpassword123"
        )
        assert confirm.token == "reset-token"
        assert confirm.new_password == "newpassword123"

    def test_password_reset_confirm_validation(self):
        """Test PasswordResetConfirm validation."""
        from pydantic import ValidationError

        # Test minimum password length
        with pytest.raises(ValidationError):
            PasswordResetConfirm(
                token="reset-token",
                new_password="short"  # Less than 8 characters
            )