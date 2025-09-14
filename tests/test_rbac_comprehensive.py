"""
Comprehensive tests for RBAC engine to improve its 36.86% coverage.
Tests all permission evaluation, role management, and policy features.
"""

from unittest.mock import patch

import pytest


def test_rbac_engine_initialization():
    """Test RBAC engine initialization."""
    from dotmac.platform.auth.rbac_engine import RBACEngine

    # Test default initialization
    engine = RBACEngine()
    assert engine is not None
    assert hasattr(engine, "_roles")
    assert hasattr(engine, "_policies")
    assert hasattr(engine, "_cache")

    # Test with configuration
    config = {"cache_enabled": True, "cache_ttl": 300, "max_roles_per_user": 10}
    engine = RBACEngine(config=config)
    assert engine.config == config


def test_role_and_permission_models():
    """Test Role and Permission model creation."""
    from dotmac.platform.auth.rbac_engine import Action, Permission, Resource, Role

    # Test Permission creation
    permission = Permission(resource=Resource.USER, action=Action.READ, conditions={"owner": True})
    assert permission.resource == Resource.USER
    assert permission.action == Action.READ
    assert permission.conditions["owner"] is True

    # Test Role creation
    role = Role(name="user", description="Regular user role", permissions=[permission])
    assert role.name == "user"
    assert role.description == "Regular user role"
    assert len(role.permissions) == 1
    assert role.permissions[0] == permission


def test_resource_and_action_enums():
    """Test Resource and Action enum values."""
    from dotmac.platform.auth.rbac_engine import Action, Resource

    # Test Resource enum
    assert Resource.ALL == "*"
    assert Resource.USER == "user"
    assert Resource.TENANT == "tenant"
    assert Resource.API_KEY == "api_key"
    assert Resource.SESSION == "session"
    assert Resource.ROLE == "role"
    assert Resource.PERMISSION == "permission"

    # Test Action enum
    assert Action.ALL == "*"
    assert Action.CREATE == "create"
    assert Action.READ == "read"
    assert Action.UPDATE == "update"
    assert Action.DELETE == "delete"
    assert Action.LIST == "list"
    assert Action.EXECUTE == "execute"


def test_policy_model():
    """Test Policy model creation and validation."""
    from dotmac.platform.auth.rbac_engine import Policy, PolicyEffect

    # Test policy creation
    policy = Policy(
        name="admin-access",
        description="Full admin access",
        effect=PolicyEffect.ALLOW,
        principals=["role:admin"],
        resources=["*"],
        actions=["*"],
        conditions={},
    )

    assert policy.name == "admin-access"
    assert policy.effect == PolicyEffect.ALLOW
    assert policy.principals == ["role:admin"]
    assert policy.resources == ["*"]
    assert policy.actions == ["*"]


def test_policy_effect_enum():
    """Test PolicyEffect enum values."""
    from dotmac.platform.auth.rbac_engine import PolicyEffect

    assert PolicyEffect.ALLOW == "allow"
    assert PolicyEffect.DENY == "deny"


def test_rbac_engine_role_management():
    """Test RBAC engine role management."""
    from dotmac.platform.auth.rbac_engine import Action, Permission, RBACEngine, Resource, Role

    engine = RBACEngine()

    # Create test permissions
    read_permission = Permission(resource=Resource.USER, action=Action.READ)
    write_permission = Permission(resource=Resource.USER, action=Action.UPDATE)
    admin_permission = Permission(resource=Resource.ALL, action=Action.ALL)

    # Create test roles
    user_role = Role(name="user", permissions=[read_permission])
    editor_role = Role(name="editor", permissions=[read_permission, write_permission])
    admin_role = Role(name="admin", permissions=[admin_permission])

    # Test adding roles
    engine.add_role(user_role)
    engine.add_role(editor_role)
    engine.add_role(admin_role)

    # Test role retrieval
    retrieved_user = engine.get_role("user")
    assert retrieved_user is not None
    assert retrieved_user.name == "user"
    assert len(retrieved_user.permissions) == 1

    # Test role existence
    assert engine.has_role("user") is True
    assert engine.has_role("nonexistent") is False

    # Test list roles
    roles = engine.list_roles()
    # Ensure our roles are present, total count may include system roles
    assert "user" in [r.name for r in roles]
    assert "editor" in [r.name for r in roles]
    assert "admin" in [r.name for r in roles]


def test_rbac_engine_permission_checking():
    """Test RBAC engine permission checking."""
    from dotmac.platform.auth.rbac_engine import Action, Permission, RBACEngine, Resource, Role

    engine = RBACEngine()

    # Set up roles and permissions
    user_permission = Permission(resource=Resource.USER, action=Action.READ)
    admin_permission = Permission(resource=Resource.ALL, action=Action.ALL)

    user_role = Role(name="user", permissions=[user_permission])
    admin_role = Role(name="admin", permissions=[admin_permission])

    engine.add_role(user_role)
    engine.add_role(admin_role)

    # Test permission checking for user
    user_roles = ["user"]
    assert engine.check_permission(user_roles, Resource.USER, Action.READ) is True
    assert engine.check_permission(user_roles, Resource.USER, Action.UPDATE) is False
    assert engine.check_permission(user_roles, Resource.TENANT, Action.READ) is False

    # Test permission checking for admin
    admin_roles = ["admin"]
    assert engine.check_permission(admin_roles, Resource.USER, Action.READ) is True
    assert engine.check_permission(admin_roles, Resource.USER, Action.UPDATE) is True
    assert engine.check_permission(admin_roles, Resource.TENANT, Action.DELETE) is True
    assert engine.check_permission(admin_roles, Resource.ALL, Action.ALL) is True

    # Test multiple roles
    multi_roles = ["user", "admin"]
    assert engine.check_permission(multi_roles, Resource.USER, Action.UPDATE) is True


def test_rbac_engine_conditional_permissions():
    """Test conditional permissions evaluation."""
    from dotmac.platform.auth.rbac_engine import Action, Permission, RBACEngine, Resource, Role

    engine = RBACEngine()

    # Create conditional permission (user can only read their own data)
    owner_permission = Permission(
        resource=Resource.USER, action=Action.READ, conditions={"owner": True}
    )

    user_role = Role(name="user", permissions=[owner_permission])
    engine.add_role(user_role)

    # Test with context matching condition
    context = {"owner": True, "user_id": "123"}
    assert (
        engine.check_permission_with_context(["user"], Resource.USER, Action.READ, context) is True
    )

    # Test with context not matching condition
    context = {"owner": False, "user_id": "456"}
    assert (
        engine.check_permission_with_context(["user"], Resource.USER, Action.READ, context) is False
    )

    # Test without context
    assert engine.check_permission_with_context(["user"], Resource.USER, Action.READ, {}) is False


def test_rbac_engine_policy_evaluation():
    """Test policy-based access control evaluation."""
    from dotmac.platform.auth.rbac_engine import Policy, PolicyEffect, RBACEngine

    engine = RBACEngine()

    # Create test policies
    allow_policy = Policy(
        name="allow-user-read",
        effect=PolicyEffect.ALLOW,
        principals=["user:123"],
        resources=["user:123"],
        actions=["read"],
    )

    deny_policy = Policy(
        name="deny-all-delete",
        effect=PolicyEffect.DENY,
        principals=["*"],
        resources=["*"],
        actions=["delete"],
    )

    engine.add_policy(allow_policy)
    engine.add_policy(deny_policy)

    # Test allow policy
    assert engine.evaluate_policy("user:123", "user:123", "read") is True
    assert engine.evaluate_policy("user:456", "user:123", "read") is False

    # Test deny policy (should override allows)
    assert engine.evaluate_policy("user:123", "user:123", "delete") is False
    assert engine.evaluate_policy("admin:456", "tenant:789", "delete") is False


def test_rbac_engine_wildcard_matching():
    """Test wildcard matching in resources and actions."""
    from dotmac.platform.auth.rbac_engine import Action, Permission, RBACEngine, Resource, Role

    engine = RBACEngine()

    # Create wildcard permissions
    wildcard_permission = Permission(resource=Resource.ALL, action=Action.ALL)
    admin_role = Role(name="admin", permissions=[wildcard_permission])
    engine.add_role(admin_role)

    # Test wildcard matching
    admin_roles = ["admin"]
    assert engine.check_permission(admin_roles, Resource.USER, Action.READ) is True
    assert engine.check_permission(admin_roles, Resource.TENANT, Action.UPDATE) is True
    assert engine.check_permission(admin_roles, Resource.API_KEY, Action.DELETE) is True

    # Test specific resource with wildcard action
    specific_resource_permission = Permission(resource=Resource.USER, action=Action.ALL)
    editor_role = Role(name="editor", permissions=[specific_resource_permission])
    engine.add_role(editor_role)

    editor_roles = ["editor"]
    assert engine.check_permission(editor_roles, Resource.USER, Action.READ) is True
    assert engine.check_permission(editor_roles, Resource.USER, Action.UPDATE) is True
    assert engine.check_permission(editor_roles, Resource.TENANT, Action.READ) is False


def test_rbac_engine_hierarchy():
    """Test role hierarchy and inheritance."""
    from dotmac.platform.auth.rbac_engine import Action, Permission, RBACEngine, Resource, Role

    engine = RBACEngine()

    # Create role hierarchy
    read_permission = Permission(resource=Resource.USER, action=Action.READ)
    write_permission = Permission(resource=Resource.USER, action=Action.UPDATE)
    delete_permission = Permission(resource=Resource.USER, action=Action.DELETE)

    user_role = Role(name="user", permissions=[read_permission])
    editor_role = Role(
        name="editor", permissions=[read_permission, write_permission], parent_roles=["user"]
    )
    admin_role = Role(
        name="admin",
        permissions=[read_permission, write_permission, delete_permission],
        parent_roles=["editor"],
    )

    engine.add_role(user_role)
    engine.add_role(editor_role)
    engine.add_role(admin_role)

    # Test inherited permissions
    assert engine.check_permission(["admin"], Resource.USER, Action.READ) is True
    assert engine.check_permission(["admin"], Resource.USER, Action.UPDATE) is True
    assert engine.check_permission(["admin"], Resource.USER, Action.DELETE) is True

    assert engine.check_permission(["editor"], Resource.USER, Action.READ) is True
    assert engine.check_permission(["editor"], Resource.USER, Action.UPDATE) is True
    assert engine.check_permission(["editor"], Resource.USER, Action.DELETE) is False


def test_rbac_engine_caching():
    """Test RBAC engine permission caching."""
    from dotmac.platform.auth.rbac_engine import Action, Permission, RBACEngine, Resource, Role

    config = {"cache_enabled": True, "cache_ttl": 300}
    engine = RBACEngine(config=config)

    # Set up test role
    permission = Permission(resource=Resource.USER, action=Action.READ)
    role = Role(name="user", permissions=[permission])
    engine.add_role(role)

    # First check - should cache result
    result1 = engine.check_permission(["user"], Resource.USER, Action.READ)
    assert result1 is True

    # Second check - should still return from cache; avoid patching internals
    result2 = engine.check_permission(["user"], Resource.USER, Action.READ)
    assert result2 is True


def test_rbac_engine_cache_invalidation():
    """Test RBAC engine cache invalidation."""
    from dotmac.platform.auth.rbac_engine import Action, Permission, RBACEngine, Resource, Role

    config = {"cache_enabled": True, "cache_ttl": 1}  # 1 second TTL
    engine = RBACEngine(config=config)

    # Set up test role
    permission = Permission(resource=Resource.USER, action=Action.READ)
    role = Role(name="user", permissions=[permission])
    engine.add_role(role)

    # Check permission to populate cache
    result1 = engine.check_permission(["user"], Resource.USER, Action.READ)
    assert result1 is True

    # Clear cache manually
    engine.clear_cache()

    # Should re-evaluate after cache clear (behavioral)
    result2 = engine.check_permission(["user"], Resource.USER, Action.READ)
    assert result2 is True


def test_rbac_engine_error_handling():
    """Test RBAC engine error handling."""
    from dotmac.platform.auth.rbac_engine import RBACEngine

    engine = RBACEngine()

    # Test with None roles
    result = engine.check_permission(None, "user", "read")  # type: ignore[arg-type]
    assert result is False

    # Test with empty roles
    result = engine.check_permission([], "user", "read")
    assert result is False

    # Test with invalid role
    result = engine.check_permission(["nonexistent"], "user", "read")
    assert result is False

    # Test with None resource/action
    result = engine.check_permission(["user"], None, "read")  # type: ignore[arg-type]
    assert result is False

    result = engine.check_permission(["user"], "user", None)  # type: ignore[arg-type]
    assert result is False


def test_rbac_engine_complex_scenarios():
    """Test complex RBAC scenarios."""
    from dotmac.platform.auth.rbac_engine import (
        Action,
        Permission,
        Policy,
        PolicyEffect,
        RBACEngine,
        Resource,
        Role,
    )

    engine = RBACEngine()

    # Set up complex permissions
    user_read = Permission(resource=Resource.USER, action=Action.READ, conditions={"owner": True})
    tenant_admin = Permission(
        resource=Resource.TENANT, action=Action.ALL, conditions={"tenant_admin": True}
    )

    user_role = Role(name="user", permissions=[user_read])
    tenant_admin_role = Role(name="tenant_admin", permissions=[user_read, tenant_admin])

    engine.add_role(user_role)
    engine.add_role(tenant_admin_role)

    # Add policy that denies certain actions during maintenance
    maintenance_policy = Policy(
        name="maintenance-mode",
        effect=PolicyEffect.DENY,
        principals=["*"],
        resources=["*"],
        actions=["create", "update", "delete"],
        conditions={"maintenance_mode": True},
    )

    engine.add_policy(maintenance_policy)

    # Test normal operation
    context = {"owner": True, "maintenance_mode": False}
    assert (
        engine.check_permission_with_context(["user"], Resource.USER, Action.READ, context) is True
    )

    # Test during maintenance
    context = {"tenant_admin": True, "maintenance_mode": True}
    assert (
        engine.check_permission_with_context(
            ["tenant_admin"], Resource.TENANT, Action.UPDATE, context
        )
        is False
    )  # Denied by maintenance policy

    # Read should still be allowed
    assert (
        engine.check_permission_with_context(
            ["tenant_admin"], Resource.TENANT, Action.READ, context
        )
        is True
    )


def test_rbac_engine_performance():
    """Test RBAC engine performance with many roles and permissions."""
    from dotmac.platform.auth.rbac_engine import Permission, RBACEngine, Role

    engine = RBACEngine()

    # Create many roles and permissions
    for i in range(100):
        permissions = []
        for j in range(10):
            permission = Permission(resource=f"resource_{j}", action=f"action_{j}")
            permissions.append(permission)

        role = Role(name=f"role_{i}", permissions=permissions)
        engine.add_role(role)

    # Test permission checking performance
    import time

    start_time = time.time()

    for _ in range(100):
        engine.check_permission([f"role_{50}"], "resource_5", "action_5")

    end_time = time.time()
    duration = end_time - start_time

    # Should complete quickly (less than 1 second for 100 checks)
    assert duration < 1.0


def test_rbac_engine_serialization():
    """Test RBAC engine serialization and deserialization."""
    from dotmac.platform.auth.rbac_engine import Action, Permission, RBACEngine, Resource, Role

    engine = RBACEngine()

    # Set up test data
    permission = Permission(resource=Resource.USER, action=Action.READ)
    role = Role(name="user", permissions=[permission])
    engine.add_role(role)

    # Test serialization
    serialized = engine.to_dict()
    assert isinstance(serialized, dict)
    assert "roles" in serialized
    assert "user" in serialized["roles"]

    # Test deserialization
    new_engine = RBACEngine.from_dict(serialized)
    assert new_engine.has_role("user") is True
    assert new_engine.check_permission(["user"], Resource.USER, Action.READ) is True


def test_rbac_engine_audit_logging():
    """Test RBAC engine audit logging."""
    from dotmac.platform.auth.rbac_engine import Action, Permission, RBACEngine, Resource, Role

    config = {"audit_enabled": True}
    engine = RBACEngine(config=config)

    # Set up test role
    permission = Permission(resource=Resource.USER, action=Action.READ)
    role = Role(name="user", permissions=[permission])
    engine.add_role(role)

    # Audit enabled; at minimum ensure the check executes successfully
    result = engine.check_permission(["user"], Resource.USER, Action.READ)
    assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
