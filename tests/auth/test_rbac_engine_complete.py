"""
Comprehensive tests for RBAC Engine with full coverage.
Tests roles, permissions, hierarchies, wildcards, and caching.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, Mock, patch
import pytest

from dotmac.platform.auth.rbac_engine import (
    RBACEngine,
    Role,
    Permission,
    PermissionCache,
)
from dotmac.platform.auth.exceptions import (
    AuthorizationError,
)


class TestPermissionModel:
    """Test Permission model functionality."""

    def test_permission_creation(self):
        """Test creating a permission."""
        perm = Permission(resource="users", action="read")
        assert perm.resource == "users"
        assert perm.action == "read"
        assert str(perm) == "users:read"

    def test_permission_with_wildcard(self):
        """Test permission with wildcard."""
        perm = Permission(resource="users", action="*")
        assert perm.action == "*"
        assert str(perm) == "users:*"

    def test_permission_equality(self):
        """Test permission equality comparison."""
        perm1 = Permission(resource="users", action="read")
        perm2 = Permission(resource="users", action="read")
        perm3 = Permission(resource="users", action="write")

        assert perm1 == perm2
        assert perm1 != perm3

    def test_permission_from_string(self):
        """Test creating permission from string."""
        perm = Permission.from_string("users:read")
        assert perm.resource == "users"
        assert perm.action == "read"

        perm2 = Permission.from_string("admin:*")
        assert perm2.resource == "admin"
        assert perm2.action == "*"

    def test_permission_invalid_string(self):
        """Test creating permission from invalid string."""
        with pytest.raises(ValueError):
            Permission.from_string("invalid")

        with pytest.raises(ValueError):
            Permission.from_string("")

    def test_permission_matches(self):
        """Test permission matching logic."""
        perm_all = Permission(resource="users", action="*")
        perm_read = Permission(resource="users", action="read")
        perm_write = Permission(resource="users", action="write")

        # Wildcard matches any action
        assert perm_all.matches(perm_read)
        assert perm_all.matches(perm_write)

        # Specific permission only matches itself
        assert perm_read.matches(perm_read)
        assert not perm_read.matches(perm_write)


class TestRoleModel:
    """Test Role model functionality."""

    def test_role_creation(self):
        """Test creating a role."""
        permissions = [
            Permission(resource="users", action="read"),
            Permission(resource="users", action="write")
        ]
        role = Role(
            name="editor",
            permissions=permissions,
            description="Editor role"
        )

        assert role.name == "editor"
        assert len(role.permissions) == 2
        assert role.description == "Editor role"

    def test_role_add_permission(self):
        """Test adding permission to role."""
        role = Role(name="viewer")
        perm = Permission(resource="posts", action="read")

        role.add_permission(perm)
        assert perm in role.permissions

    def test_role_remove_permission(self):
        """Test removing permission from role."""
        perm = Permission(resource="posts", action="read")
        role = Role(name="viewer", permissions=[perm])

        role.remove_permission(perm)
        assert perm not in role.permissions

    def test_role_has_permission(self):
        """Test checking if role has permission."""
        role = Role(
            name="admin",
            permissions=[Permission(resource="users", action="*")]
        )

        assert role.has_permission(Permission(resource="users", action="read"))
        assert role.has_permission(Permission(resource="users", action="write"))
        assert not role.has_permission(Permission(resource="posts", action="read"))

    def test_role_inheritance(self):
        """Test role with parent roles."""
        parent_role = Role(
            name="viewer",
            permissions=[Permission(resource="posts", action="read")]
        )

        child_role = Role(
            name="editor",
            permissions=[Permission(resource="posts", action="write")],
            parent_roles=["viewer"]
        )

        assert "viewer" in child_role.parent_roles
        assert len(child_role.permissions) == 1  # Only direct permissions


@pytest.mark.asyncio
class TestRBACEngine:
    """Test RBAC Engine functionality."""

    @pytest.fixture
    async def rbac_engine(self):
        """Create RBAC engine instance."""
        engine = RBACEngine()
        await engine.initialize_default_roles()
        return engine

    async def test_engine_initialization(self, rbac_engine):
        """Test RBAC engine initialization."""
        assert rbac_engine._roles is not None
        assert rbac_engine._permission_cache is not None
        assert rbac_engine._role_hierarchy is not None

    async def test_add_role(self, rbac_engine):
        """Test adding a role to the engine."""
        role = Role(
            name="custom_role",
            permissions=[Permission(resource="custom", action="read")]
        )

        await rbac_engine.add_role(role)
        retrieved = await rbac_engine.get_role("custom_role")
        assert retrieved.name == "custom_role"

    async def test_add_duplicate_role(self, rbac_engine):
        """Test adding duplicate role."""
        role = Role(name="duplicate")
        await rbac_engine.add_role(role)

        # Adding same role again should update
        role2 = Role(name="duplicate", description="Updated")
        await rbac_engine.add_role(role2)

        retrieved = await rbac_engine.get_role("duplicate")
        assert retrieved.description == "Updated"

    async def test_get_nonexistent_role(self, rbac_engine):
        """Test getting non-existent role."""
        with pytest.raises(AuthorizationError):
            await rbac_engine.get_role("nonexistent")

    async def test_remove_role(self, rbac_engine):
        """Test removing a role."""
        role = Role(name="to_remove")
        await rbac_engine.add_role(role)

        await rbac_engine.remove_role("to_remove")

        with pytest.raises(AuthorizationError):
            await rbac_engine.get_role("to_remove")

    async def test_remove_nonexistent_role(self, rbac_engine):
        """Test removing non-existent role."""
        result = await rbac_engine.remove_role("nonexistent")
        assert result is False

    async def test_list_roles(self, rbac_engine):
        """Test listing all roles."""
        # Add some roles
        await rbac_engine.add_role(Role(name="role1"))
        await rbac_engine.add_role(Role(name="role2"))

        roles = await rbac_engine.list_roles()
        role_names = [r.name for r in roles]

        assert "role1" in role_names
        assert "role2" in role_names


@pytest.mark.asyncio
class TestPermissionChecking:
    """Test permission checking functionality."""

    @pytest.fixture
    async def rbac_engine(self):
        """Create RBAC engine with test roles."""
        engine = RBACEngine()

        # Create test roles
        viewer = Role(
            name="viewer",
            permissions=[
                Permission(resource="posts", action="read"),
                Permission(resource="comments", action="read")
            ]
        )

        editor = Role(
            name="editor",
            permissions=[
                Permission(resource="posts", action="*"),
                Permission(resource="comments", action="*")
            ],
            parent_roles=["viewer"]
        )

        admin = Role(
            name="admin",
            permissions=[Permission(resource="*", action="*")]
        )

        await engine.add_role(viewer)
        await engine.add_role(editor)
        await engine.add_role(admin)

        return engine

    async def test_check_permission_with_string_list(self, rbac_engine):
        """Test checking permissions with string list."""
        user_perms = ["posts:read", "comments:read"]

        assert await rbac_engine.check_permission(user_perms, "posts:read")
        assert await rbac_engine.check_permission(user_perms, "comments:read")
        assert not await rbac_engine.check_permission(user_perms, "posts:write")

    async def test_check_permission_with_wildcard(self, rbac_engine):
        """Test checking permissions with wildcards."""
        user_perms = ["posts:*", "comments:read"]

        assert await rbac_engine.check_permission(user_perms, "posts:read")
        assert await rbac_engine.check_permission(user_perms, "posts:write")
        assert await rbac_engine.check_permission(user_perms, "posts:delete")
        assert not await rbac_engine.check_permission(user_perms, "comments:write")

    async def test_check_permission_with_global_wildcard(self, rbac_engine):
        """Test checking permissions with global wildcard."""
        admin_perms = ["*:*"]

        assert await rbac_engine.check_permission(admin_perms, "posts:read")
        assert await rbac_engine.check_permission(admin_perms, "users:delete")
        assert await rbac_engine.check_permission(admin_perms, "anything:everything")

    async def test_check_permission_empty_list(self, rbac_engine):
        """Test checking permissions with empty list."""
        assert not await rbac_engine.check_permission([], "posts:read")

    async def test_check_permission_none_list(self, rbac_engine):
        """Test checking permissions with None."""
        assert not await rbac_engine.check_permission(None, "posts:read")

    async def test_check_permissions_for_role(self, rbac_engine):
        """Test checking permissions for a specific role."""
        viewer_perms = await rbac_engine.get_role_permissions("viewer")

        assert "posts:read" in viewer_perms
        assert "comments:read" in viewer_perms
        assert "posts:write" not in viewer_perms

    async def test_check_permissions_for_role_with_inheritance(self, rbac_engine):
        """Test permissions with role inheritance."""
        editor_perms = await rbac_engine.get_role_permissions("editor")

        # Editor should have all viewer permissions plus its own
        assert "posts:read" in editor_perms  # From viewer
        assert "posts:write" in editor_perms  # From editor (via wildcard)
        assert "comments:*" in editor_perms or "comments:write" in editor_perms


@pytest.mark.asyncio
class TestRoleInheritance:
    """Test role inheritance functionality."""

    @pytest.fixture
    async def rbac_engine(self):
        """Create RBAC engine with hierarchical roles."""
        engine = RBACEngine()

        # Create hierarchy: guest -> user -> moderator -> admin
        guest = Role(
            name="guest",
            permissions=[Permission(resource="public", action="read")]
        )

        user = Role(
            name="user",
            permissions=[Permission(resource="posts", action="read")],
            parent_roles=["guest"]
        )

        moderator = Role(
            name="moderator",
            permissions=[Permission(resource="posts", action="moderate")],
            parent_roles=["user"]
        )

        admin = Role(
            name="admin",
            permissions=[Permission(resource="*", action="*")],
            parent_roles=["moderator"]
        )

        await engine.add_role(guest)
        await engine.add_role(user)
        await engine.add_role(moderator)
        await engine.add_role(admin)

        return engine

    async def test_role_hierarchy_inheritance(self, rbac_engine):
        """Test permission inheritance through hierarchy."""
        # User should have guest permissions
        user_perms = await rbac_engine.get_all_role_permissions("user")
        assert any(p.resource == "public" and p.action == "read" for p in user_perms)
        assert any(p.resource == "posts" and p.action == "read" for p in user_perms)

        # Moderator should have user and guest permissions
        mod_perms = await rbac_engine.get_all_role_permissions("moderator")
        assert any(p.resource == "public" and p.action == "read" for p in mod_perms)
        assert any(p.resource == "posts" and p.action == "read" for p in mod_perms)
        assert any(p.resource == "posts" and p.action == "moderate" for p in mod_perms)

    async def test_circular_hierarchy_detection(self, rbac_engine):
        """Test detection of circular role dependencies."""
        role_a = Role(name="role_a", parent_roles=["role_b"])
        role_b = Role(name="role_b", parent_roles=["role_c"])
        role_c = Role(name="role_c", parent_roles=["role_a"])  # Creates circle

        await rbac_engine.add_role(role_a)
        await rbac_engine.add_role(role_b)

        # Should detect and handle circular dependency
        await rbac_engine.add_role(role_c)

        # Engine should still function despite circular dependency
        perms = await rbac_engine.get_all_role_permissions("role_a")
        assert perms is not None

    async def test_missing_parent_role(self, rbac_engine):
        """Test role with missing parent."""
        role = Role(
            name="orphan",
            parent_roles=["nonexistent_parent"]
        )

        await rbac_engine.add_role(role)

        # Should handle missing parent gracefully
        perms = await rbac_engine.get_all_role_permissions("orphan")
        assert perms is not None


@pytest.mark.asyncio
class TestPermissionCache:
    """Test permission caching functionality."""

    @pytest.fixture
    async def rbac_engine(self):
        """Create RBAC engine with caching."""
        engine = RBACEngine(cache_ttl=60)
        return engine

    async def test_cache_hit(self, rbac_engine):
        """Test permission cache hits."""
        role = Role(
            name="cached_role",
            permissions=[Permission(resource="test", action="read")]
        )
        await rbac_engine.add_role(role)

        # First call should cache
        perms1 = await rbac_engine.get_role_permissions("cached_role")

        # Second call should hit cache
        with patch.object(rbac_engine._permission_cache, 'get') as mock_get:
            mock_get.return_value = perms1
            perms2 = await rbac_engine.get_role_permissions("cached_role")
            assert perms1 == perms2

    async def test_cache_invalidation_on_role_update(self, rbac_engine):
        """Test cache invalidation when role is updated."""
        role = Role(
            name="update_role",
            permissions=[Permission(resource="test", action="read")]
        )
        await rbac_engine.add_role(role)

        # Cache the permissions
        perms1 = await rbac_engine.get_role_permissions("update_role")

        # Update the role
        updated_role = Role(
            name="update_role",
            permissions=[
                Permission(resource="test", action="read"),
                Permission(resource="test", action="write")
            ]
        )
        await rbac_engine.add_role(updated_role)

        # Should get updated permissions
        perms2 = await rbac_engine.get_role_permissions("update_role")
        assert len(perms2) > len(perms1)

    async def test_cache_clear(self, rbac_engine):
        """Test clearing permission cache."""
        role = Role(name="clear_test")
        await rbac_engine.add_role(role)

        # Populate cache
        await rbac_engine.get_role_permissions("clear_test")

        # Clear cache
        await rbac_engine.clear_permission_cache()

        # Verify cache is cleared
        assert len(rbac_engine._permission_cache._cache) == 0


@pytest.mark.asyncio
class TestAuthorizationDecorators:
    """Test authorization decorators and utilities."""

    async def test_require_permission_decorator(self):
        """Test require_permission decorator."""
        from dotmac.platform.auth.rbac_engine import require_permission

        @require_permission("posts:read")
        async def read_posts(user_permissions):
            return "posts"

        # User with permission
        result = await read_posts(["posts:read", "comments:read"])
        assert result == "posts"

        # User without permission
        with pytest.raises(AuthorizationError):
            await read_posts(["comments:read"])

    async def test_require_any_permission_decorator(self):
        """Test require_any_permission decorator."""
        from dotmac.platform.auth.rbac_engine import require_any_permission

        @require_any_permission(["posts:read", "posts:write"])
        async def access_posts(user_permissions):
            return "posts"

        # User with one permission
        result = await access_posts(["posts:read"])
        assert result == "posts"

        # User with another permission
        result = await access_posts(["posts:write"])
        assert result == "posts"

        # User with no matching permission
        with pytest.raises(AuthorizationError):
            await access_posts(["comments:read"])

    async def test_require_all_permissions_decorator(self):
        """Test require_all_permissions decorator."""
        from dotmac.platform.auth.rbac_engine import require_all_permissions

        @require_all_permissions(["posts:read", "posts:write"])
        async def full_access_posts(user_permissions):
            return "full access"

        # User with all permissions
        result = await full_access_posts(["posts:read", "posts:write", "comments:read"])
        assert result == "full access"

        # User missing one permission
        with pytest.raises(AuthorizationError):
            await full_access_posts(["posts:read"])


@pytest.mark.asyncio
class TestDefaultRoles:
    """Test default role initialization."""

    async def test_initialize_default_roles(self):
        """Test initialization of default roles."""
        engine = RBACEngine()
        await engine.initialize_default_roles()

        # Check default roles exist
        roles = await engine.list_roles()
        role_names = [r.name for r in roles]

        assert "super_admin" in role_names
        assert "admin" in role_names
        assert "user" in role_names
        assert "guest" in role_names

    async def test_super_admin_permissions(self):
        """Test super admin has all permissions."""
        engine = RBACEngine()
        await engine.initialize_default_roles()

        perms = await engine.get_role_permissions("super_admin")

        # Super admin should have wildcard permission
        assert "*:*" in perms or any("*" in p for p in perms)

    async def test_guest_limited_permissions(self):
        """Test guest has limited permissions."""
        engine = RBACEngine()
        await engine.initialize_default_roles()

        perms = await engine.get_role_permissions("guest")

        # Guest should only have read permissions
        for perm in perms:
            assert "read" in perm or "view" in perm


class TestPermissionSerialization:
    """Test permission serialization and deserialization."""

    def test_permission_to_dict(self):
        """Test converting permission to dictionary."""
        perm = Permission(resource="users", action="write")
        perm_dict = perm.to_dict()

        assert perm_dict["resource"] == "users"
        assert perm_dict["action"] == "write"

    def test_permission_from_dict(self):
        """Test creating permission from dictionary."""
        perm_dict = {"resource": "posts", "action": "delete"}
        perm = Permission.from_dict(perm_dict)

        assert perm.resource == "posts"
        assert perm.action == "delete"

    def test_role_to_dict(self):
        """Test converting role to dictionary."""
        role = Role(
            name="test_role",
            permissions=[
                Permission(resource="users", action="read"),
                Permission(resource="posts", action="write")
            ],
            description="Test role",
            parent_roles=["parent1", "parent2"]
        )

        role_dict = role.to_dict()

        assert role_dict["name"] == "test_role"
        assert len(role_dict["permissions"]) == 2
        assert role_dict["description"] == "Test role"
        assert len(role_dict["parent_roles"]) == 2

    def test_role_from_dict(self):
        """Test creating role from dictionary."""
        role_dict = {
            "name": "test_role",
            "permissions": [
                {"resource": "users", "action": "read"},
                {"resource": "posts", "action": "write"}
            ],
            "description": "Test role",
            "parent_roles": ["parent1"]
        }

        role = Role.from_dict(role_dict)

        assert role.name == "test_role"
        assert len(role.permissions) == 2
        assert role.description == "Test role"
        assert "parent1" in role.parent_roles