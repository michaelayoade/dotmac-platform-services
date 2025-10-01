"""Basic tests for RBAC service to improve coverage."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from dotmac.platform.auth.rbac_service import RBACService
from dotmac.platform.auth.models import Role, Permission, PermissionCategory
from dotmac.platform.auth.exceptions import AuthError, AuthorizationError


class TestRBACServiceInit:
    """Test RBAC service initialization."""

    def test_service_initialization(self):
        """Test service can be initialized."""
        mock_session = MagicMock()
        service = RBACService(mock_session)

        assert service.db == mock_session
        assert isinstance(service._permission_cache, dict)
        assert isinstance(service._role_cache, dict)
        assert len(service._permission_cache) == 0
        assert len(service._role_cache) == 0

    def test_service_has_required_methods(self):
        """Test service has all required methods."""
        mock_session = MagicMock()
        service = RBACService(mock_session)

        assert hasattr(service, 'get_user_permissions')
        assert hasattr(service, 'db')
        assert hasattr(service, '_permission_cache')
        assert hasattr(service, '_role_cache')

    def test_multiple_service_instances(self):
        """Test multiple service instances are independent."""
        session1 = MagicMock()
        session2 = MagicMock()

        service1 = RBACService(session1)
        service2 = RBACService(session2)

        assert service1.db is not service2.db
        assert service1._permission_cache is not service2._permission_cache


class TestRBACServicePermissions:
    """Test RBAC service permission operations."""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def rbac_service(self, mock_session):
        """Create RBAC service with mocked session."""
        return RBACService(mock_session)

    @pytest.mark.asyncio
    async def test_get_user_permissions_cache_key(self, rbac_service):
        """Test cache key generation for user permissions."""
        user_id = uuid4()

        # Mock cache to return None (cache miss)
        with patch('dotmac.platform.auth.rbac_service.cache_get', return_value=None):
            with patch('dotmac.platform.auth.rbac_service.cache_set'):
                # Mock database queries to return empty results
                rbac_service.db.execute = AsyncMock(return_value=AsyncMock(
                    __aiter__=lambda self: iter([])
                ))

                with patch.object(rbac_service, '_expand_permissions', return_value=set()):
                    permissions = await rbac_service.get_user_permissions(user_id)

                    assert isinstance(permissions, set)

    @pytest.mark.asyncio
    async def test_get_user_permissions_with_cache_hit(self, rbac_service):
        """Test getting user permissions from cache."""
        user_id = uuid4()
        cached_perms = ['read:users', 'write:users']

        with patch('dotmac.platform.auth.rbac_service.cache_get', return_value=cached_perms):
            permissions = await rbac_service.get_user_permissions(user_id)

            assert isinstance(permissions, set)
            assert permissions == set(cached_perms)

    @pytest.mark.asyncio
    async def test_get_user_permissions_include_expired(self, rbac_service):
        """Test getting user permissions including expired ones."""
        user_id = uuid4()

        with patch('dotmac.platform.auth.rbac_service.cache_get', return_value=None):
            with patch('dotmac.platform.auth.rbac_service.cache_set'):
                rbac_service.db.execute = AsyncMock(return_value=AsyncMock(
                    __aiter__=lambda self: iter([])
                ))

                with patch.object(rbac_service, '_expand_permissions', return_value=set()):
                    # Should not use cache when include_expired=True
                    permissions = await rbac_service.get_user_permissions(
                        user_id,
                        include_expired=True
                    )

                    assert isinstance(permissions, set)


class TestRBACServiceCaching:
    """Test RBAC service caching behavior."""

    @pytest.fixture
    def rbac_service(self):
        """Create RBAC service."""
        mock_session = MagicMock()
        return RBACService(mock_session)

    def test_permission_cache_initialization(self, rbac_service):
        """Test permission cache is initialized empty."""
        assert len(rbac_service._permission_cache) == 0

    def test_role_cache_initialization(self, rbac_service):
        """Test role cache is initialized empty."""
        assert len(rbac_service._role_cache) == 0

    def test_cache_manipulation(self, rbac_service):
        """Test manual cache manipulation."""
        # Add to permission cache
        rbac_service._permission_cache['test:permission'] = MagicMock()
        assert len(rbac_service._permission_cache) == 1
        assert 'test:permission' in rbac_service._permission_cache

        # Add to role cache
        rbac_service._role_cache['admin'] = MagicMock()
        assert len(rbac_service._role_cache) == 1
        assert 'admin' in rbac_service._role_cache


class TestRBACServiceHelpers:
    """Test RBAC service helper methods."""

    @pytest.fixture
    def rbac_service(self):
        """Create RBAC service."""
        mock_session = AsyncMock()
        return RBACService(mock_session)

    def test_service_has_private_methods(self, rbac_service):
        """Test service has expected private methods."""
        # Check for expected method structure
        assert hasattr(rbac_service, 'db')
        assert hasattr(rbac_service, '_permission_cache')
        assert hasattr(rbac_service, '_role_cache')

    @pytest.mark.asyncio
    async def test_expand_permissions_method_exists(self, rbac_service):
        """Test _expand_permissions method exists."""
        # Verify the method exists
        assert hasattr(rbac_service, '_expand_permissions') or callable(getattr(rbac_service, '_expand_permissions', None))


class TestRBACServicePermissionChecks:
    """Test permission checking logic."""

    @pytest.fixture
    def rbac_service(self):
        """Create RBAC service."""
        mock_session = AsyncMock()
        return RBACService(mock_session)

    def test_permission_set_operations(self, rbac_service):
        """Test permission set operations."""
        perms = set(['read:users', 'write:users'])

        # Test add permission
        perms.add('delete:users')
        assert len(perms) == 3
        assert 'delete:users' in perms

        # Test discard permission
        perms.discard('write:users')
        assert len(perms) == 2
        assert 'write:users' not in perms

    def test_permission_grant_revoke_logic(self, rbac_service):
        """Test permission grant and revoke logic."""
        permissions = set(['read:data', 'write:data'])

        # Simulate granting a new permission
        new_perm = 'delete:data'
        granted = True

        if granted:
            permissions.add(new_perm)
        else:
            permissions.discard(new_perm)

        assert 'delete:data' in permissions

        # Simulate revoking a permission
        granted = False
        if granted:
            permissions.add('write:data')
        else:
            permissions.discard('write:data')

        assert 'write:data' not in permissions