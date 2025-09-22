"""
Test suite for Casbin-based RBAC engine.
"""

import pytest

from dotmac.platform.auth.rbac_engine import (
    CasbinRBACEngine,
    RBACEngine,
    Permission,
    Role,
    Action,
    Resource,
)


class TestCasbinRBACEngine:
    """Test Casbin RBAC engine functionality."""

    @pytest.fixture
    def engine(self):
        """Create test RBAC engine."""
        return CasbinRBACEngine()

    def test_basic_permission_check(self, engine):
        """Test basic permission checking."""
        # Add role and permission
        engine.add_role_for_user("user1", "admin")
        engine.add_permission("admin", "document", "read", "allow")

        # Check permission
        assert engine.check_permission("user1", "document", "read") is True
        assert engine.check_permission("user1", "document", "write") is False
        assert engine.check_permission("user2", "document", "read") is False

    def test_role_hierarchy(self, engine):
        """Test role inheritance."""
        # Setup role hierarchy
        engine.add_role_inheritance("editor", "viewer")
        engine.add_permission("viewer", "document", "read", "allow")
        engine.add_permission("editor", "document", "write", "allow")

        # Assign roles
        engine.add_role_for_user("alice", "viewer")
        engine.add_role_for_user("bob", "editor")

        # Test viewer permissions
        assert engine.check_permission("alice", "document", "read") is True
        assert engine.check_permission("alice", "document", "write") is False

        # Test editor permissions (inherits viewer)
        assert engine.check_permission("bob", "document", "read") is True
        assert engine.check_permission("bob", "document", "write") is True

    def test_wildcard_permissions(self, engine):
        """Test wildcard permissions."""
        # Add admin with wildcard permissions
        engine.add_permission("admin", "*", "*", "allow")
        engine.add_role_for_user("superuser", "admin")

        # Check various permissions
        assert engine.check_permission("superuser", "anything", "everything") is True
        assert engine.check_permission("superuser", "document", "delete") is True

    def test_multi_tenant_support(self, engine):
        """Test multi-tenant isolation."""
        # Add users to different tenants
        engine.add_role_for_user("user1", "editor", tenant="tenant1")
        engine.add_role_for_user("user1", "viewer", tenant="tenant2")

        engine.add_permission("editor", "document", "write", "allow")
        engine.add_permission("viewer", "document", "read", "allow")

        # Check tenant-specific permissions
        assert engine.check_permission("user1", "document", "write", tenant="tenant1") is True
        assert engine.check_permission("user1", "document", "write", tenant="tenant2") is False
        assert engine.check_permission("user1", "document", "read", tenant="tenant2") is True

    def test_batch_permission_check(self, engine):
        """Test batch permission checking."""
        engine.add_role_for_user("user1", "editor")
        engine.add_permission("editor", "document", "read", "allow")
        engine.add_permission("editor", "document", "write", "allow")

        permissions = [
            ("document", "read"),
            ("document", "write"),
            ("document", "delete"),
            ("user", "read"),
        ]

        results = engine.check_permissions_batch("user1", permissions)

        assert results[("document", "read")] is True
        assert results[("document", "write")] is True
        assert results[("document", "delete")] is False
        assert results[("user", "read")] is False

    def test_get_user_roles(self, engine):
        """Test getting user roles."""
        engine.add_role_for_user("alice", "viewer")
        engine.add_role_for_user("alice", "editor")
        engine.add_role_for_user("bob", "admin")

        alice_roles = engine.get_roles_for_user("alice")
        bob_roles = engine.get_roles_for_user("bob")

        assert "viewer" in alice_roles
        assert "editor" in alice_roles
        assert "admin" in bob_roles

    def test_remove_role_from_user(self, engine):
        """Test removing roles from users."""
        engine.add_role_for_user("user1", "admin")
        engine.add_permission("admin", "system", "manage", "allow")

        # Verify permission exists
        assert engine.check_permission("user1", "system", "manage") is True

        # Remove role
        engine.delete_role_for_user("user1", "admin")

        # Verify permission removed
        assert engine.check_permission("user1", "system", "manage") is False


class TestBackwardCompatibility:
    """Test backward compatibility with original RBAC engine."""

    @pytest.fixture
    def engine(self):
        """Create backward compatible engine."""
        return RBACEngine()

    def test_permission_class(self):
        """Test Permission class compatibility."""
        perm = Permission(Action.READ, Resource.USER)
        assert perm.action == "read"
        assert perm.resource == "user"

        # Test string format
        assert perm.to_string() == "read:user"

        # Test from_string
        perm2 = Permission.from_string("write:document")
        assert perm2.action == "write"
        assert perm2.resource == "document"

    def test_role_class(self, engine):
        """Test Role class compatibility."""
        permissions = [
            Permission(Action.READ, Resource.USER),
            Permission(Action.WRITE, Resource.USER),
        ]

        role = Role(
            name="user_manager",
            permissions=permissions,
            parent_roles=["viewer"],
            description="User management role"
        )

        assert role.name == "user_manager"
        assert len(role.permissions) == 2
        assert role.has_permission("read", "user") is True
        assert role.has_permission("delete", "user") is False

    def test_can_access_method(self, engine):
        """Test can_access backward compatibility."""
        # Setup roles and permissions
        engine.add_permission("editor", "document", "write", "allow")
        engine.add_role_for_user("alice", "editor")

        # Test can_access
        perm = Permission(Action.WRITE, Resource.DOCUMENT)
        assert engine.can_access(
            user_roles=["editor"],
            required_permission=perm
        ) is True

        # Test with user_id
        assert engine.can_access(
            user_roles=[],
            required_permission=perm,
            user_id="alice"
        ) is True

    def test_add_role_method(self, engine):
        """Test add_role backward compatibility."""
        permissions = [
            Permission(Action.READ, "reports"),
            Permission(Action.WRITE, "reports"),
        ]

        role = Role(
            name="analyst",
            permissions=permissions,
            parent_roles=["viewer"]
        )

        engine.add_role(role)

        # Verify role was added
        retrieved = engine.get_role("analyst")
        assert retrieved is not None
        assert retrieved.name == "analyst"
        assert len(retrieved.permissions) == 2

    def test_get_effective_permissions(self, engine):
        """Test getting effective permissions."""
        # Setup role hierarchy
        engine.add_permission("viewer", "document", "read")
        engine.add_permission("editor", "document", "write")
        engine.add_role_inheritance("editor", "viewer")

        # Get effective permissions
        perms = engine.get_effective_permissions(["editor"])

        # Should have both read and write
        actions = {p.action for p in perms}
        assert "read" in actions
        assert "write" in actions


class TestPerformance:
    """Test performance characteristics."""

    @pytest.fixture
    def engine(self):
        """Create test engine."""
        return CasbinRBACEngine()

    def test_large_policy_set(self, engine):
        """Test with large number of policies."""
        # Add many users and roles
        for i in range(100):
            user = f"user{i}"
            role = f"role{i % 10}"
            engine.add_role_for_user(user, role)

        # Add permissions for each role
        for i in range(10):
            role = f"role{i}"
            for j in range(10):
                resource = f"resource{j}"
                engine.add_permission(role, resource, "read")

        # Test permission checks
        assert engine.check_permission("user0", "resource0", "read") is True
        assert engine.check_permission("user99", "resource9", "read") is True
        assert engine.check_permission("user0", "resource0", "write") is False

    def test_complex_hierarchy(self, engine):
        """Test complex role hierarchies."""
        # Create multi-level hierarchy
        engine.add_role_inheritance("level3", "level2")
        engine.add_role_inheritance("level2", "level1")
        engine.add_role_inheritance("level1", "base")

        engine.add_permission("base", "resource", "read")
        engine.add_permission("level1", "resource", "write")
        engine.add_permission("level2", "resource", "update")
        engine.add_permission("level3", "resource", "delete")

        engine.add_role_for_user("user", "level3")

        # User should have all permissions through inheritance
        assert engine.check_permission("user", "resource", "read") is True
        assert engine.check_permission("user", "resource", "write") is True
        assert engine.check_permission("user", "resource", "update") is True
        assert engine.check_permission("user", "resource", "delete") is True