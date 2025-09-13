"""
Unit tests for RBACEngine covering roles, permissions, inheritance and cache.
"""

import pytest

from dotmac.platform.auth.rbac_engine import (
    Permission,
    RBACEngine,
    create_role,
)


@pytest.mark.unit
def test_permission_matching_patterns_and_wildcards():
    p1 = Permission("read", "user")
    assert p1.matches("read", "user") is True
    assert p1.matches("write", "user") is False

    p2 = Permission("*", "*")
    assert p2.matches("delete", "anything") is True

    p3 = Permission("read|write", "user|billing")
    assert p3.matches("write", "billing") is True
    assert p3.matches("execute", "billing") is False


@pytest.mark.unit
def test_add_remove_roles_and_system_protection():
    eng = RBACEngine(enable_caching=True)
    # System role cannot be removed
    with pytest.raises(ValueError):
        eng.remove_role("admin")

    # Custom role add/remove
    role = create_role("editor", ["read:user", "write:user"])
    eng.add_role(role)
    assert eng.get_role("editor") is not None
    assert eng.remove_role("editor") is True
    assert eng.get_role("editor") is None


@pytest.mark.unit
def test_role_inheritance_and_cycle_detection():
    eng = RBACEngine()
    parent = create_role("parent", ["read:user"])
    child = create_role("child", ["write:user"])
    child.add_parent_role("parent")
    eng.add_role(parent)
    eng.add_role(child)

    eng.assign_user_role("u1", "child")
    roles = eng.get_user_roles("u1")
    assert "child" in roles and "parent" in roles

    # Create cycle
    cyclic = create_role("cyclic", ["read:billing"])
    cyclic.add_parent_role("child")
    eng.add_role(cyclic)
    # Now try to make parent inherit cyclic -> cycle
    parent.add_parent_role("cyclic")
    with pytest.raises(ValueError):
        eng.add_role(parent)


@pytest.mark.unit
def test_cache_stats_and_clear():
    eng = RBACEngine(enable_caching=True)
    eng.assign_user_role("u1", "user")
    # First check may miss, second should hit cache

    # No explicit check_permission method in engine; emulate via permission matching using user role
    # We will call get_user_roles to populate some cache paths indirectly by calling internal methods.
    roles1 = eng.get_user_roles("u1")
    roles2 = eng.get_user_roles("u1")
    assert roles1 == roles2
    stats = eng.get_cache_stats()
    # Cache may be None if caching disabled; here it is enabled
    assert stats is not None
    eng.clear_cache()
    stats2 = eng.get_cache_stats()
    assert stats2 is not None and stats2["hits"] == 0
