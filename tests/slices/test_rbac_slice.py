"""
RBAC slice tests without mocks: focus on real permission checks.
"""

from dotmac.platform.auth.rbac_engine import (
    Action,
    Policy,
    PolicyEffect,
    RBACEngine,
    Resource,
    Role,
    create_permission,
)


def test_rbac_permissions_and_policies_basic():
    engine = RBACEngine()

    # Create an editor role that can read and update users
    editor = Role(
        name="editor",
        permissions=[
            create_permission(Action.READ.value, Resource.USER.value),
            create_permission(Action.UPDATE.value, Resource.USER.value),
        ],
    )
    engine.add_role(editor)
    engine.assign_user_role("u1", "editor")

    # Direct permission checks
    assert engine.check_permission(["editor"], Resource.USER, Action.READ) is True
    assert engine.check_permission(["editor"], Resource.USER, Action.UPDATE) is True
    assert engine.check_permission(["editor"], Resource.USER, Action.DELETE) is False

    # Policy that denies updates during maintenance
    deny_updates = Policy(
        name="maintenance",
        effect=PolicyEffect.DENY,
        principals=["*"],
        resources=[Resource.USER.value],
        actions=[Action.UPDATE.value],
        conditions={"maintenance": True},
    )
    engine.add_policy(deny_updates)

    assert (
        engine.check_permission_with_context(
            ["editor"], Resource.USER, Action.UPDATE, {"maintenance": True}
        )
        is False
    )
    assert (
        engine.check_permission_with_context(
            ["editor"], Resource.USER, Action.UPDATE, {"maintenance": False}
        )
        is True
    )
