"""
Unit tests for current_user dependencies without running a FastAPI server.
We simulate Request.state contents to exercise paths.
"""

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
)


def make_request_with_state(**state_kwargs: Any) -> Request:
    """Create a mock Request object with the specified state attributes."""
    req = Mock(spec=Request)
    req.state = Mock()
    for key, value in state_kwargs.items():
        setattr(req.state, key, value)
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
