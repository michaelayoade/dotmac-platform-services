"""
Unit tests for current_user dependencies without running a FastAPI server.
We simulate Request.state contents to exercise paths.
"""

from types import SimpleNamespace
from typing import Any
from unittest.mock import Mock

import pytest
from fastapi import HTTPException, Request

from dotmac.platform.auth.current_user import (
    ServiceClaims,
    UserClaims,
    get_current_service,
    get_current_tenant,
    get_current_user,
    get_optional_user,
    require_admin,
    require_roles,
    require_scopes,
    require_tenant_access,
)


def make_request_with_state(**state_kwargs: Any) -> Request:
    """Create a mock Request object with the specified state attributes."""
    req = Mock(spec=Request)
    state = SimpleNamespace()
    for key, value in state_kwargs.items():
        setattr(state, key, value)
    req.state = state
    req.client = Mock(host="127.0.0.1")
    req.headers = {}
    return req


@pytest.mark.unit
def test_get_current_user_success_and_failures():
    req_ok = make_request_with_state(user_claims={"sub": "u1", "authenticated": True})
    u = get_current_user(req_ok)
    assert isinstance(u, UserClaims) and u.user_id == "u1"

    # Not authenticated
    req_noauth = make_request_with_state(user_claims={"sub": "u1", "authenticated": False})
    with pytest.raises(HTTPException):
        get_current_user(req_noauth)

    # Service token not allowed
    req_service = make_request_with_state(
        user_claims={"sub": "svc", "authenticated": True, "is_service": True}
    )
    with pytest.raises(HTTPException):
        get_current_user(req_service)


@pytest.mark.unit
def test_get_optional_user():
    req_none = make_request_with_state()
    assert get_optional_user(req_none) is None


@pytest.mark.unit
def test_require_scopes_and_roles():
    # user with read scope
    req_user = make_request_with_state(
        user_claims={"sub": "u1", "authenticated": True, "scopes": ["read"], "roles": ["user"]}
    )
    # any scope
    user = get_current_user(req_user)
    dep_any = require_scopes(["read", "write"], require_all=False)
    assert dep_any(user) == user  # type: ignore[arg-type]
    # require missing role
    dep_role = require_roles(["admin"], require_all=False)
    with pytest.raises(HTTPException):
        dep_role(user)  # type: ignore[arg-type]


@pytest.mark.unit
def test_require_admin_and_get_current_tenant():
    req_admin = make_request_with_state(
        user_claims={"sub": "u1", "authenticated": True, "roles": ["admin"], "tenant_id": "t1"}
    )
    user_admin = get_current_user(req_admin)
    dep_admin = require_admin()
    assert dep_admin(user_admin) == user_admin  # type: ignore[arg-type]

    # Tenant
    assert get_current_tenant(req_admin) == "t1"

    # Missing tenant
    req_no_tenant = make_request_with_state(user_claims={"sub": "u1", "authenticated": True})
    with pytest.raises(HTTPException):
        get_current_tenant(req_no_tenant)


@pytest.mark.unit
def test_get_current_service():
    req = make_request_with_state(
        service_claims={
            "sub": "svc",
            "service_authenticated": True,
            "target_service": "api",
            "allowed_operations": ["op"],
            "identity_id": "id1",
        }
    )
    s = get_current_service(req)
    assert isinstance(s, ServiceClaims) and s.service_name == "svc"


@pytest.mark.unit
def test_get_current_user_missing_claims():
    req = make_request_with_state()
    with pytest.raises(HTTPException) as exc:
        get_current_user(req)

    detail = exc.value.detail
    assert isinstance(detail, dict)
    assert detail.get("error") == "TOKEN_NOT_FOUND"


@pytest.mark.unit
def test_user_claims_scope_and_role_helpers():
    claims = UserClaims(
        sub="user-123",
        scopes=["read", "write"],
        roles=["editor", "reviewer"],
    )

    assert claims.has_scope("read")
    assert claims.has_any_scope(["delete", "write"])
    assert claims.has_all_scopes(["read", "write"])
    assert not claims.has_all_scopes(["read", "admin"])

    assert claims.has_role("editor")
    assert claims.has_any_role(["moderator", "reviewer"])
    assert claims.has_all_roles(["editor", "reviewer"])
    assert not claims.has_all_roles(["editor", "admin"])


@pytest.mark.unit
def test_user_claims_admin_and_tenant_access():
    admin_by_role = UserClaims(
        sub="admin-role",
        roles=["admin"],
        scopes=["read"],
        tenant_id="tenant-a",
    )
    admin_by_scope = UserClaims(
        sub="admin-scope",
        roles=["user"],
        scopes=["admin:write"],
        tenant_id="tenant-b",
    )

    assert admin_by_role.is_admin()
    assert admin_by_scope.is_admin()

    # Same tenant access
    assert admin_by_role.can_access_tenant("tenant-a")
    # Admin can access any tenant
    assert admin_by_role.can_access_tenant("tenant-other")
    # Cross-tenant scope allows access without admin role
    scoped_user = UserClaims(
        sub="scoped",
        scopes=["tenant:access:tenant-x"],
        tenant_id="tenant-y",
    )
    assert scoped_user.can_access_tenant("tenant-x")
    assert not scoped_user.can_access_tenant("tenant-z")


@pytest.mark.unit
def test_require_scopes_and_tenant_access_errors():
    req = make_request_with_state(
        user_claims={
            "sub": "u1",
            "authenticated": True,
            "scopes": ["read"],
            "tenant_id": "tenant-a",
        }
    )
    user = get_current_user(req)

    require_all = require_scopes(["read", "write"], require_all=True)
    with pytest.raises(HTTPException) as exc:
        require_all(user)  # type: ignore[arg-type]
    detail = exc.value.detail
    assert isinstance(detail, dict)
    assert detail.get("error") == "INSUFFICIENT_SCOPE"
    assert detail["details"]["required_scopes"] == ["read", "write"]

    tenant_dep = require_tenant_access("tenant-b")
    with pytest.raises(HTTPException) as tenant_exc:
        tenant_dep(user)  # type: ignore[arg-type]
    tenant_detail = tenant_exc.value.detail
    assert tenant_detail["error"] == "TENANT_ACCESS_DENIED"

    # Grant explicit scope for tenant and ensure access works
    req_allowed = make_request_with_state(
        user_claims={
            "sub": "u1",
            "authenticated": True,
            "scopes": ["tenant:access:tenant-b"],
            "tenant_id": "tenant-a",
        }
    )
    allowed_user = get_current_user(req_allowed)
    assert tenant_dep(allowed_user) == allowed_user  # type: ignore[arg-type]
