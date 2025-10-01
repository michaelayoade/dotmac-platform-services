"""Tests to improve user management router coverage."""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.user_management.router import get_user_service


class TestUserRouterCoverage:
    """Test UserRouter edge cases for better coverage."""

    async def test_get_user_service_dependency(self):
        """Test the get_user_service dependency function (line 91)."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)

        # Act
        service = await get_user_service(mock_session)

        # Assert
        assert service is not None
        assert service.session == mock_session

    async def test_user_service_initialization_with_real_session(self):
        """Test UserService initialization with actual session type."""
        from dotmac.platform.user_management.service import UserService

        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)

        # Act
        service = UserService(mock_session)

        # Assert
        assert service.session == mock_session
        assert hasattr(service, 'get_user_by_id')
        assert hasattr(service, 'create_user')
        assert hasattr(service, 'update_user')
        assert hasattr(service, 'delete_user')

    async def test_user_service_methods_exist(self):
        """Ensure all expected methods exist on UserService."""
        from dotmac.platform.user_management.service import UserService

        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        service = UserService(mock_session)

        # Assert all expected methods exist
        expected_methods = [
            'get_user_by_id', 'get_user_by_username', 'get_user_by_email',
            'create_user', 'update_user', 'delete_user', 'list_users',
            'verify_password', 'change_password', 'authenticate',
            'enable_mfa', 'disable_mfa', 'add_role', 'remove_role'
        ]

        for method_name in expected_methods:
            assert hasattr(service, method_name), f"Method {method_name} not found"
            assert callable(getattr(service, method_name)), f"Method {method_name} is not callable"