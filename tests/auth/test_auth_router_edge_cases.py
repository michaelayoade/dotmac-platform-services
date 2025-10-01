"""
Additional tests for auth router edge cases and missing coverage.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

# Import all router components and dependencies
from dotmac.platform.auth.router import (
    login, register, refresh_token, logout, verify_token,
    request_password_reset, confirm_password_reset, get_current_user,
    get_async_session, get_auth_session,
    LoginRequest, RegisterRequest, RefreshTokenRequest,
    PasswordResetRequest, PasswordResetConfirm
)


class TestAuthRouterEdgeCases:
    """Test edge cases and missing coverage paths."""

    @pytest.fixture
    def mock_session(self):
        """Mock database session."""
        session = AsyncMock(spec=AsyncSession)
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_get_auth_session_dependency(self):
        """Test get_auth_session dependency function."""
        # This tests the wrapper function at lines 36-39
        with patch('dotmac.platform.auth.router.get_session_dependency') as mock_dep:
            mock_session = AsyncMock()

            async def mock_generator():
                yield mock_session

            mock_dep.return_value = mock_generator()

            # Test the generator
            async for session in get_auth_session():
                assert session == mock_session
                break

    @pytest.mark.asyncio
    async def test_get_async_session_compatibility(self):
        """Test get_async_session compatibility wrapper."""
        # This tests the compatibility function at lines 43-45
        with patch('dotmac.platform.auth.router.get_session_dependency') as mock_dep:
            mock_session = AsyncMock()

            async def mock_generator():
                yield mock_session

            mock_dep.return_value = mock_generator()

            # Test the compatibility wrapper
            async for session in get_async_session():
                assert session == mock_session
                break

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.jwt_service')
    @patch('dotmac.platform.auth.router.session_manager')
    @patch('dotmac.platform.auth.router.get_auth_email_service')
    async def test_register_email_service_failure_edge_case(
        self, mock_email_service, mock_session_manager, mock_jwt_service,
        mock_user_service_class, mock_session
    ):
        """Test register when email service creation fails."""
        # Setup successful user creation
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

        # Email service creation itself fails
        mock_email_service.side_effect = Exception("Email service unavailable")

        request = RegisterRequest(
            username="newuser",
            email="new@example.com",
            password="SecurePass123!"
        )

        # Should still succeed even if email service fails (line 239-240)
        result = await register(request, mock_session)
        assert result.access_token == "access_token"

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.verify_password')
    async def test_login_user_by_email_fallback(
        self, mock_verify_password, mock_user_service_class, mock_session
    ):
        """Test login fallback to email lookup when username fails."""
        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.is_active = True
        mock_user.roles = ["user"]
        mock_user.tenant_id = None

        mock_user_service = MagicMock()
        # Username lookup returns None, email lookup succeeds
        mock_user_service.get_user_by_username = AsyncMock(return_value=None)
        mock_user_service.get_user_by_email = AsyncMock(return_value=mock_user)
        mock_user_service_class.return_value = mock_user_service

        mock_verify_password.return_value = True

        with patch('dotmac.platform.auth.router.jwt_service') as mock_jwt:
            mock_jwt.create_access_token.return_value = "access_token"
            mock_jwt.create_refresh_token.return_value = "refresh_token"

            with patch('dotmac.platform.auth.router.session_manager') as mock_sm:
                mock_sm.create_session = AsyncMock()

                request = LoginRequest(username="test@example.com", password="password123")
                result = await login(request, mock_session)

                assert result.access_token == "access_token"
                # Verify fallback to email was used
                mock_user_service.get_user_by_email.assert_called_once_with("test@example.com")

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.jwt_service')
    async def test_refresh_token_user_inactive(
        self, mock_jwt_service, mock_user_service_class, mock_session
    ):
        """Test refresh token when user becomes inactive."""
        inactive_user = MagicMock()
        inactive_user.id = uuid4()
        inactive_user.is_active = False

        mock_user_service = MagicMock()
        mock_user_service.get_user_by_id = AsyncMock(return_value=inactive_user)
        mock_user_service_class.return_value = mock_user_service

        mock_jwt_service.verify_token.return_value = {
            "sub": str(inactive_user.id),
            "type": "refresh"
        }

        request = RefreshTokenRequest(refresh_token="valid_refresh_token")

        with pytest.raises(HTTPException) as exc_info:
            await refresh_token(request, mock_session)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "User not found or disabled" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.jwt_service')
    async def test_refresh_token_revocation_failure(
        self, mock_jwt_service, mock_user_service_class, mock_session
    ):
        """Test refresh token when revocation fails but process continues."""
        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.is_active = True
        mock_user.roles = ["user"]
        mock_user.tenant_id = None

        mock_user_service = MagicMock()
        mock_user_service.get_user_by_id = AsyncMock(return_value=mock_user)
        mock_user_service_class.return_value = mock_user_service

        mock_jwt_service.verify_token.return_value = {
            "sub": str(mock_user.id),
            "type": "refresh"
        }
        # Revocation fails (line 291-292)
        mock_jwt_service.revoke_token = AsyncMock(side_effect=Exception("Redis down"))
        mock_jwt_service.create_access_token.return_value = "new_access_token"
        mock_jwt_service.create_refresh_token.return_value = "new_refresh_token"

        request = RefreshTokenRequest(refresh_token="old_refresh_token")
        result = await refresh_token(request, mock_session)

        # Should succeed despite revocation failure
        assert result.access_token == "new_access_token"

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.jwt_service')
    @patch('dotmac.platform.auth.router.session_manager')
    async def test_logout_exception_handling(self, mock_session_manager, mock_jwt_service):
        """Test logout exception handling paths."""
        # Test when token verification fails but revocation succeeds (lines 354-362)
        mock_jwt_service.verify_token.side_effect = Exception("Invalid token")
        mock_jwt_service.revoke_token = AsyncMock()

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid_token")
        result = await logout(credentials)

        assert result["message"] == "Logout completed"
        mock_jwt_service.revoke_token.assert_called_once_with("invalid_token")

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.jwt_service')
    @patch('dotmac.platform.auth.router.session_manager')
    async def test_logout_complete_failure(self, mock_session_manager, mock_jwt_service):
        """Test logout when everything fails."""
        mock_jwt_service.verify_token.side_effect = Exception("Invalid token")
        mock_jwt_service.revoke_token = AsyncMock(side_effect=Exception("Redis down"))

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="bad_token")
        result = await logout(credentials)

        # Should still return success message
        assert result["message"] == "Logout completed"

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.get_auth_email_service')
    async def test_password_reset_inactive_user(
        self, mock_email_service, mock_user_service_class, mock_session
    ):
        """Test password reset for inactive user (should not send email)."""
        inactive_user = MagicMock()
        inactive_user.email = "inactive@example.com"
        inactive_user.username = "inactive"
        inactive_user.is_active = False

        mock_user_service = MagicMock()
        mock_user_service.get_user_by_email = AsyncMock(return_value=inactive_user)
        mock_user_service_class.return_value = mock_user_service

        # Email service should not be called for inactive users (line 403)
        mock_email = MagicMock()
        mock_email_service.return_value = mock_email

        request = PasswordResetRequest(email="inactive@example.com")
        result = await request_password_reset(request, mock_session)

        # Should return success message but not send email
        assert "password reset link has been sent" in result["message"]
        mock_email.send_password_reset_email.assert_not_called()

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.get_auth_email_service')
    async def test_password_reset_email_send_failure(
        self, mock_email_service, mock_user_service_class, mock_session
    ):
        """Test password reset when email sending fails (lines 411-412)."""
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.username = "testuser"
        mock_user.full_name = "Test User"
        mock_user.is_active = True

        mock_user_service = MagicMock()
        mock_user_service.get_user_by_email = AsyncMock(return_value=mock_user)
        mock_user_service_class.return_value = mock_user_service

        mock_email = MagicMock()
        # Email sending fails
        mock_email.send_password_reset_email.side_effect = Exception("SMTP error")
        mock_email_service.return_value = mock_email

        request = PasswordResetRequest(email="test@example.com")
        result = await request_password_reset(request, mock_session)

        # Should still return success message
        assert "password reset link has been sent" in result["message"]

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.get_auth_email_service')
    @patch('dotmac.platform.auth.router.hash_password')
    async def test_confirm_password_reset_database_rollback_failure(
        self, mock_hash_password, mock_email_service,
        mock_user_service_class, mock_session
    ):
        """Test confirm password reset when even rollback fails."""
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

        # Both commit and rollback fail (lines 459-462)
        mock_session.commit = AsyncMock(side_effect=Exception("DB error"))
        mock_session.rollback = AsyncMock(side_effect=Exception("Rollback failed too"))

        request = PasswordResetConfirm(token="valid_token", new_password="NewSecurePass123!")

        with pytest.raises(Exception) as exc_info:
            await confirm_password_reset(request, mock_session)

        # The second exception (rollback failure) is what gets raised
        assert str(exc_info.value) == "Rollback failed too"

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.UserService')
    @patch('dotmac.platform.auth.router.jwt_service')
    async def test_get_current_user_token_no_subject(
        self, mock_jwt_service, mock_user_service_class, mock_session
    ):
        """Test get current user when token has no subject (line 483)."""
        mock_jwt_service.verify_token.return_value = {}  # No "sub" field

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token_no_sub")

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, mock_session)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid token" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.jwt_service')
    async def test_get_current_user_token_verification_failure(
        self, mock_jwt_service, mock_session
    ):
        """Test get current user when token verification completely fails (lines 508-510)."""
        mock_jwt_service.verify_token.side_effect = Exception("Token malformed")

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="malformed_token")

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, mock_session)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid or expired token" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.UserService')
    async def test_register_create_user_exception_logging(
        self, mock_user_service_class, mock_session
    ):
        """Test register when create_user raises exception (lines 199-201)."""
        mock_user_service = MagicMock()
        mock_user_service.get_user_by_username = AsyncMock(return_value=None)
        mock_user_service.get_user_by_email = AsyncMock(return_value=None)
        # create_user raises exception
        mock_user_service.create_user = AsyncMock(side_effect=ValueError("Database constraint violation"))
        mock_user_service_class.return_value = mock_user_service

        request = RegisterRequest(
            username="newuser",
            email="new@example.com",
            password="SecurePass123!"
        )

        with pytest.raises(HTTPException) as exc_info:
            await register(request, mock_session)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to create user" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.UserService')
    async def test_register_email_already_exists(
        self, mock_user_service_class, mock_session
    ):
        """Test register when email already exists (line 184)."""
        existing_user = MagicMock()
        existing_user.email = "existing@example.com"

        mock_user_service = MagicMock()
        mock_user_service.get_user_by_username = AsyncMock(return_value=None)
        mock_user_service.get_user_by_email = AsyncMock(return_value=existing_user)
        mock_user_service_class.return_value = mock_user_service

        request = RegisterRequest(
            username="newuser",
            email="existing@example.com",
            password="SecurePass123!"
        )

        with pytest.raises(HTTPException) as exc_info:
            await register(request, mock_session)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        # Our security fix uses generic error message to prevent enumeration
        assert "Registration failed" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    @patch('dotmac.platform.auth.router.jwt_service')
    async def test_refresh_token_generic_exception(
        self, mock_jwt_service, mock_session
    ):
        """Test refresh token with generic exception (lines 319-321)."""
        # Make verify_token raise a generic exception (not HTTPException)
        mock_jwt_service.verify_token.side_effect = ValueError("Unexpected error")

        request = RefreshTokenRequest(refresh_token="problem_token")

        with pytest.raises(HTTPException) as exc_info:
            await refresh_token(request, mock_session)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid or expired refresh token" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_refresh_token_http_exception_passthrough(self, mock_session):
        """Test refresh token passes through HTTPException (line 317)."""
        with patch('dotmac.platform.auth.router.jwt_service') as mock_jwt:
            # Raise an HTTPException, which should be re-raised as-is
            original_exception = HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token blacklisted"
            )
            mock_jwt.verify_token.side_effect = original_exception

            request = RefreshTokenRequest(refresh_token="blacklisted_token")

            with pytest.raises(HTTPException) as exc_info:
                await refresh_token(request, mock_session)

            # Should be the same exception, not wrapped
            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
            assert "Token blacklisted" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_current_user_http_exception_passthrough(self, mock_session):
        """Test get_current_user passes through HTTPException (line 506)."""
        with patch('dotmac.platform.auth.router.jwt_service') as mock_jwt:
            # Raise an HTTPException, which should be re-raised as-is
            original_exception = HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token revoked"
            )
            mock_jwt.verify_token.side_effect = original_exception

            credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="revoked_token")

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials, mock_session)

            # Should be the same exception, not wrapped
            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
            assert "Token revoked" in str(exc_info.value.detail)