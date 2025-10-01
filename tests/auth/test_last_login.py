"""
Test last_login tracking functionality.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from dotmac.platform.user_management.service import UserService
from dotmac.platform.user_management.models import User


@pytest.fixture
def mock_session():
    """Create a mock async database session."""
    session = AsyncMock()
    session.commit = AsyncMock()
    return session


@pytest.fixture
def user_service(mock_session):
    """Create UserService instance."""
    return UserService(mock_session)


@pytest.fixture
def sample_user():
    """Create a sample user for testing."""
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.username = "testuser"
    user.email = "test@example.com"
    user.password_hash = "hashed"
    user.is_active = True
    user.last_login = None
    user.last_login_ip = None
    return user


class TestLastLoginTracking:
    """Test last_login tracking functionality."""

    @pytest.mark.asyncio
    async def test_update_last_login_success(self, user_service, mock_session, sample_user):
        """Test successful last_login update."""
        user_id = sample_user.id
        ip_address = "192.168.1.100"

        with patch.object(user_service, "get_user_by_id", return_value=sample_user):
            result = await user_service.update_last_login(user_id, ip_address=ip_address)

            assert result == sample_user
            assert sample_user.last_login is not None
            assert sample_user.last_login_ip == ip_address
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_last_login_without_ip(self, user_service, mock_session, sample_user):
        """Test last_login update without IP address."""
        user_id = sample_user.id

        with patch.object(user_service, "get_user_by_id", return_value=sample_user):
            result = await user_service.update_last_login(user_id)

            assert result == sample_user
            assert sample_user.last_login is not None
            assert sample_user.last_login_ip is None
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_last_login_user_not_found(self, user_service, mock_session):
        """Test last_login update when user doesn't exist."""
        user_id = uuid4()

        with patch.object(user_service, "get_user_by_id", return_value=None):
            result = await user_service.update_last_login(user_id)

            assert result is None
            mock_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_last_login_updates_timestamp(self, user_service, mock_session, sample_user):
        """Test that last_login timestamp is properly updated."""
        user_id = sample_user.id
        before_update = datetime.now(timezone.utc)

        with patch.object(user_service, "get_user_by_id", return_value=sample_user):
            result = await user_service.update_last_login(user_id)

            assert result == sample_user
            assert sample_user.last_login is not None
            assert sample_user.last_login >= before_update
            assert sample_user.last_login <= datetime.now(timezone.utc)


class TestAuthRouterIntegration:
    """Test auth router integration with last_login."""

    @pytest.mark.asyncio
    async def test_login_updates_last_login(self):
        """Test that login endpoint calls update_last_login."""
        from dotmac.platform.auth.router import login
        from dotmac.platform.auth.router import LoginRequest
        from fastapi import Request, Response
        from fastapi.testclient import TestClient

        # Create mock objects
        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.password_hash = "$2b$12$test_hash"  # bcrypt hash format
        mock_user.is_active = True
        mock_user.is_verified = True
        mock_user.roles = ["user"]
        mock_user.tenant_id = "test-tenant"

        mock_session = AsyncMock()
        mock_user_service = AsyncMock()
        mock_user_service.get_user_by_username.return_value = mock_user
        mock_user_service.authenticate.return_value = mock_user
        mock_user_service.update_last_login = AsyncMock(return_value=mock_user)

        mock_request = MagicMock(spec=Request)
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"

        login_request = LoginRequest(
            username="testuser",
            password="password123"
        )

        # Mock all dependencies
        with patch("dotmac.platform.auth.router.UserService", return_value=mock_user_service):
            with patch("dotmac.platform.auth.router.verify_password", return_value=True):
                with patch("dotmac.platform.auth.router.jwt_service") as mock_jwt:
                    mock_jwt.create_access_token.return_value = "access_token"
                    mock_jwt.create_refresh_token.return_value = "refresh_token"

                    with patch("dotmac.platform.auth.router.session_manager") as mock_session_manager:
                        mock_session_manager.create_session = AsyncMock()

                        # Mock audit logging functions
                        with patch("dotmac.platform.auth.router.log_user_activity", new=AsyncMock()):
                            with patch("dotmac.platform.auth.router.log_api_activity", new=AsyncMock()):
                                response = Response()
                                result = await login(
                                    login_request=login_request,
                                    request=mock_request,
                                    response=response,
                                    session=mock_session
                                )

                    # Verify update_last_login was called
                    mock_user_service.update_last_login.assert_called_once_with(
                        mock_user.id,
                        ip_address="127.0.0.1"
                    )

                    assert result.access_token == "access_token"
                    assert result.refresh_token == "refresh_token"