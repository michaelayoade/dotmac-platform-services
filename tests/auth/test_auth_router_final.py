"""
Final tests to achieve 100% coverage for auth router.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

# Import router components
from dotmac.platform.auth.router import (
    logout, confirm_password_reset, get_auth_session,
    PasswordResetConfirm
)


class TestAuthRouterFinalCoverage:
    """Final tests to hit remaining uncovered lines."""

    @pytest.fixture
    def mock_session(self):
        """Mock database session."""
        session = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        return session

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.jwt_service')
    @patch('dotmac.platform.auth.router.session_manager')
    async def test_logout_successful_with_sessions(self, mock_session_manager, mock_jwt_service):
        """Test successful logout path that hits line 354."""
        mock_jwt_service.verify_token.return_value = {"sub": "user123"}
        mock_jwt_service.revoke_token = AsyncMock()
        mock_session_manager.delete_user_sessions = AsyncMock(return_value=2)

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid_token")
        result = await logout(credentials)

        # This should hit line 354 (return with sessions info)
        assert result["message"] == "Logged out successfully"
        assert result["sessions_deleted"] == 2

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.get_auth_email_service')
    async def test_password_reset_user_with_full_name(
        self, mock_email_service, mock_user_service_class, mock_session
    ):
        """Test password reset with user that has full_name (line 441)."""
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.username = "testuser"
        mock_user.full_name = "Test User"  # This triggers line 441
        mock_user.is_active = True

        mock_user_service = MagicMock()
        mock_user_service.get_user_by_email = AsyncMock(return_value=mock_user)
        mock_user_service_class.return_value = mock_user_service

        mock_email = MagicMock()
        mock_email.verify_reset_token = MagicMock(return_value="test@example.com")
        mock_email.send_password_reset_success_email = MagicMock()
        mock_email_service.return_value = mock_email

        with patch('dotmac.platform.auth.router.hash_password') as mock_hash:
            mock_hash.return_value = "new_hashed_password"

            request = PasswordResetConfirm(token="valid_token", new_password="NewSecurePass123!")
            result = await confirm_password_reset(request, mock_session)

            assert "Password has been reset successfully" in result["message"]
            # This should have used full_name in the success email
            mock_email.send_password_reset_success_email.assert_called_once_with(
                email=mock_user.email,
                user_name=mock_user.full_name  # This is the line 441 path
            )

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.get_auth_email_service')
    @patch('dotmac.platform.auth.router.hash_password')
    async def test_confirm_password_reset_rollback_success(
        self, mock_hash_password, mock_email_service,
        mock_user_service_class, mock_session
    ):
        """Test confirm password reset where rollback works (line 462)."""
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.username = "testuser"
        mock_user.full_name = "Test User"

        mock_user_service = MagicMock()
        mock_user_service.get_user_by_email = AsyncMock(return_value=mock_user)
        mock_user_service_class.return_value = mock_user_service

        mock_email = MagicMock()
        mock_email.verify_reset_token = MagicMock(return_value="test@example.com")
        mock_email_service.return_value = mock_email

        mock_hash_password.return_value = "new_hashed_password"

        # Commit fails, rollback succeeds (line 462)
        mock_session.commit = AsyncMock(side_effect=Exception("DB error"))
        mock_session.rollback = AsyncMock()  # This succeeds

        request = PasswordResetConfirm(token="valid_token", new_password="NewSecurePass123!")

        with pytest.raises(HTTPException) as exc_info:
            await confirm_password_reset(request, mock_session)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to reset password" in str(exc_info.value.detail)

        # Verify rollback was called (hits line 462)
        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_auth_session_complete_iteration(self):
        """Test complete iteration of get_auth_session dependency (line 38-39)."""
        with patch('dotmac.platform.auth.router.get_session_dependency') as mock_dep:
            mock_session = AsyncMock()

            async def mock_generator():
                yield mock_session

            mock_dep.return_value = mock_generator()

            # Fully consume the generator
            sessions = []
            async for session in get_auth_session():
                sessions.append(session)

            assert len(sessions) == 1
            assert sessions[0] == mock_session