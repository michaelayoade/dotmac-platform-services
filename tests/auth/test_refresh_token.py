"""
Tests for the token refresh endpoint.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta, UTC
from fastapi import HTTPException, status

from dotmac.platform.auth.router import refresh_token, RefreshTokenRequest, TokenResponse
from dotmac.platform.auth.core import TokenType


class TestRefreshTokenEndpoint:
    """Test the refresh token endpoint."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        return AsyncMock()

    @pytest.fixture
    def mock_user(self):
        """Create a mock user object."""
        user = MagicMock()
        user.id = "user-123"
        user.username = "testuser"
        user.email = "test@example.com"
        user.is_active = True
        user.roles = ["user"]
        user.tenant_id = "tenant-123"
        return user

    @pytest.fixture
    def valid_refresh_token_payload(self):
        """Create a valid refresh token payload."""
        return {
            "sub": "user-123",
            "type": "refresh",
            "exp": datetime.now(UTC) + timedelta(days=7),
            "iat": datetime.now(UTC),
        }

    @pytest.fixture
    def valid_access_token_payload(self):
        """Create a valid access token payload (wrong type for refresh)."""
        return {
            "sub": "user-123",
            "type": "access",
            "exp": datetime.now(UTC) + timedelta(minutes=15),
            "iat": datetime.now(UTC),
        }

    async def test_refresh_token_success(self, mock_session, mock_user, valid_refresh_token_payload):
        """Test successful token refresh."""
        request = RefreshTokenRequest(refresh_token="valid-refresh-token")

        with patch("dotmac.platform.auth.router.jwt_service") as mock_jwt_service:
            with patch("dotmac.platform.auth.router.UserService") as MockUserService:
                # Setup JWT service mock
                mock_jwt_service.verify_token.return_value = valid_refresh_token_payload
                mock_jwt_service.create_access_token.return_value = "new-access-token"
                mock_jwt_service.create_refresh_token.return_value = "new-refresh-token"

                # Setup UserService mock
                mock_user_service = AsyncMock()
                mock_user_service.get_user_by_id = AsyncMock(return_value=mock_user)
                MockUserService.return_value = mock_user_service

                # Call the endpoint
                result = await refresh_token(request, mock_session)

                # Assertions
                assert isinstance(result, TokenResponse)
                assert result.access_token == "new-access-token"
                assert result.refresh_token == "new-refresh-token"
                assert result.token_type == "bearer"

                # Verify JWT service was called correctly
                mock_jwt_service.verify_token.assert_called_once_with("valid-refresh-token")
                mock_jwt_service.create_access_token.assert_called_once()
                mock_jwt_service.create_refresh_token.assert_called_once()

                # Verify user was fetched
                mock_user_service.get_user_by_id.assert_called_once_with("user-123")

    async def test_refresh_token_with_access_token(self, mock_session, valid_access_token_payload):
        """Test that using an access token for refresh fails."""
        request = RefreshTokenRequest(refresh_token="access-token-not-refresh")

        with patch("dotmac.platform.auth.router.jwt_service") as mock_jwt_service:
            # Setup JWT service to return an access token payload
            mock_jwt_service.verify_token.return_value = valid_access_token_payload

            # Should raise HTTPException for wrong token type
            with pytest.raises(HTTPException) as exc_info:
                await refresh_token(request, mock_session)

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Invalid token type" in str(exc_info.value.detail)

    async def test_refresh_token_missing_type(self, mock_session):
        """Test refresh with token missing type field."""
        request = RefreshTokenRequest(refresh_token="malformed-token")

        with patch("dotmac.platform.auth.router.jwt_service") as mock_jwt_service:
            # Token payload without 'type' field
            mock_jwt_service.verify_token.return_value = {
                "sub": "user-123",
                # Missing 'type' field
            }

            with pytest.raises(HTTPException) as exc_info:
                await refresh_token(request, mock_session)

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Invalid token type" in str(exc_info.value.detail)

    async def test_refresh_token_no_user_id(self, mock_session, valid_refresh_token_payload):
        """Test refresh token without user ID."""
        request = RefreshTokenRequest(refresh_token="token-without-sub")

        with patch("dotmac.platform.auth.router.jwt_service") as mock_jwt_service:
            # Remove 'sub' from payload
            payload = valid_refresh_token_payload.copy()
            del payload["sub"]
            mock_jwt_service.verify_token.return_value = payload

            with pytest.raises(HTTPException) as exc_info:
                await refresh_token(request, mock_session)

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Invalid refresh token" in str(exc_info.value.detail)

    async def test_refresh_token_user_not_found(self, mock_session, valid_refresh_token_payload):
        """Test refresh token when user doesn't exist."""
        request = RefreshTokenRequest(refresh_token="valid-refresh-token")

        with patch("dotmac.platform.auth.router.jwt_service") as mock_jwt_service:
            with patch("dotmac.platform.auth.router.UserService") as MockUserService:
                # Setup JWT service mock
                mock_jwt_service.verify_token.return_value = valid_refresh_token_payload

                # Setup UserService to return None (user not found)
                mock_user_service = AsyncMock()
                mock_user_service.get_user_by_id = AsyncMock(return_value=None)
                MockUserService.return_value = mock_user_service

                with pytest.raises(HTTPException) as exc_info:
                    await refresh_token(request, mock_session)

                assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
                assert "User not found" in str(exc_info.value.detail)

    async def test_refresh_token_user_disabled(self, mock_session, mock_user, valid_refresh_token_payload):
        """Test refresh token when user is disabled."""
        request = RefreshTokenRequest(refresh_token="valid-refresh-token")
        mock_user.is_active = False  # Disable user

        with patch("dotmac.platform.auth.router.jwt_service") as mock_jwt_service:
            with patch("dotmac.platform.auth.router.UserService") as MockUserService:
                # Setup JWT service mock
                mock_jwt_service.verify_token.return_value = valid_refresh_token_payload

                # Setup UserService mock
                mock_user_service = AsyncMock()
                mock_user_service.get_user_by_id = AsyncMock(return_value=mock_user)
                MockUserService.return_value = mock_user_service

                with pytest.raises(HTTPException) as exc_info:
                    await refresh_token(request, mock_session)

                assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
                assert "disabled" in str(exc_info.value.detail)

    async def test_refresh_token_expired(self, mock_session):
        """Test refresh with expired token."""
        request = RefreshTokenRequest(refresh_token="expired-token")

        with patch("dotmac.platform.auth.router.jwt_service") as mock_jwt_service:
            # Simulate token verification failure
            mock_jwt_service.verify_token.side_effect = Exception("Token expired")

            with pytest.raises(HTTPException) as exc_info:
                await refresh_token(request, mock_session)

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "expired" in str(exc_info.value.detail).lower()

    async def test_refresh_token_invalid_signature(self, mock_session):
        """Test refresh with invalid token signature."""
        request = RefreshTokenRequest(refresh_token="tampered-token")

        with patch("dotmac.platform.auth.router.jwt_service") as mock_jwt_service:
            # Simulate signature verification failure
            mock_jwt_service.verify_token.side_effect = Exception("Invalid signature")

            with pytest.raises(HTTPException) as exc_info:
                await refresh_token(request, mock_session)

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_refresh_token_generates_new_tokens(self, mock_session, mock_user, valid_refresh_token_payload):
        """Test that refresh generates both new access and refresh tokens."""
        request = RefreshTokenRequest(refresh_token="valid-refresh-token")

        with patch("dotmac.platform.auth.router.jwt_service") as mock_jwt_service:
            with patch("dotmac.platform.auth.router.UserService") as MockUserService:
                # Setup JWT service mock
                mock_jwt_service.verify_token.return_value = valid_refresh_token_payload
                mock_jwt_service.create_access_token.return_value = "new-access-token"
                mock_jwt_service.create_refresh_token.return_value = "new-refresh-token"

                # Setup UserService mock
                mock_user_service = AsyncMock()
                mock_user_service.get_user_by_id = AsyncMock(return_value=mock_user)
                MockUserService.return_value = mock_user_service

                # Call the endpoint
                result = await refresh_token(request, mock_session)

                # Verify new access token was created with correct claims
                mock_jwt_service.create_access_token.assert_called_once_with(
                    subject=str(mock_user.id),
                    additional_claims={
                        "username": mock_user.username,
                        "email": mock_user.email,
                        "roles": mock_user.roles,
                        "tenant_id": mock_user.tenant_id,
                    }
                )

                # Verify new refresh token was created
                mock_jwt_service.create_refresh_token.assert_called_once_with(
                    subject=str(mock_user.id)
                )

                # Both tokens should be different from the original
                assert result.access_token == "new-access-token"
                assert result.refresh_token == "new-refresh-token"


class TestRefreshTokenSecurity:
    """Security-specific tests for the refresh token endpoint."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        return AsyncMock()

    @pytest.fixture
    def mock_user(self):
        """Create a mock user object."""
        user = MagicMock()
        user.id = "user-123"
        user.username = "testuser"
        user.email = "test@example.com"
        user.is_active = True
        user.roles = ["user"]
        user.tenant_id = "tenant-123"
        return user

    @pytest.fixture
    def valid_refresh_token_payload(self):
        """Create a valid refresh token payload."""
        return {
            "sub": "user-123",
            "type": "refresh",
            "exp": datetime.now(UTC) + timedelta(days=7),
            "iat": datetime.now(UTC),
        }

    async def test_refresh_token_rotation(self, mock_session, mock_user, valid_refresh_token_payload):
        """Test that refresh tokens are rotated (new one issued on each refresh)."""
        request = RefreshTokenRequest(refresh_token="old-refresh-token")

        with patch("dotmac.platform.auth.router.jwt_service") as mock_jwt_service:
            with patch("dotmac.platform.auth.router.UserService") as MockUserService:
                # Setup JWT service mock
                mock_jwt_service.verify_token.return_value = valid_refresh_token_payload
                mock_jwt_service.create_access_token.return_value = "new-access-token"
                mock_jwt_service.create_refresh_token.return_value = "rotated-refresh-token"

                # Setup UserService mock
                mock_user_service = AsyncMock()
                mock_user_service.get_user_by_id = AsyncMock(return_value=mock_user)
                MockUserService.return_value = mock_user_service

                # Call the endpoint
                result = await refresh_token(request, mock_session)

                # New refresh token should be different
                assert result.refresh_token == "rotated-refresh-token"
                assert result.refresh_token != request.refresh_token

    async def test_refresh_token_cross_user_protection(self, mock_session, mock_user):
        """Test that tokens can't be used across different users."""
        request = RefreshTokenRequest(refresh_token="token-for-user-456")

        with patch("dotmac.platform.auth.router.jwt_service") as mock_jwt_service:
            with patch("dotmac.platform.auth.router.UserService") as MockUserService:
                # Token is for user-456
                mock_jwt_service.verify_token.return_value = {
                    "sub": "user-456",
                    "type": "refresh",
                }

                # But we fetch a different user (simulating ID mismatch scenario)
                mock_user_service = AsyncMock()
                mock_user_service.get_user_by_id = AsyncMock(return_value=None)
                MockUserService.return_value = mock_user_service

                # Should fail as user doesn't exist
                with pytest.raises(HTTPException) as exc_info:
                    await refresh_token(request, mock_session)

                assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED