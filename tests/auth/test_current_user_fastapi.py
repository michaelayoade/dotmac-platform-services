"""
End-to-end style FastAPI route tests using current_user dependencies.
We inject user claims via a lightweight dependency to avoid real auth.
"""

import pytest
from fastapi import Depends, FastAPI, Request
from starlette.testclient import TestClient

from dotmac.platform.auth.current_user import (
    RequireAdmin,
    require_roles,
    require_scopes,
)


def make_claims(**kwargs):
    base = {
        "sub": "u1",
        "authenticated": True,
        "scopes": ["read"],
        "roles": ["user"],
        "tenant_id": "t1",
    }
    base.update(kwargs)
    return base


def set_claims(claims: dict):
    async def _inject(request: Request):
        request.state.user_claims = claims

    return _inject


@pytest.mark.unit
def test_routes_with_dependencies():
    app = FastAPI()

    @app.get("/read")
    async def read_endpoint(
        _: None = Depends(set_claims(make_claims())),  # inject claims
        __: None = Depends(require_scopes(["read"], require_all=False)),
    ):
        return {"ok": True}

    @app.get("/admin")
    async def admin_endpoint(
        _: None = Depends(set_claims(make_claims())),  # user is not admin
        __: None = Depends(RequireAdmin),
    ):
        return {"ok": True}

    @app.get("/role")
    async def role_endpoint(
        _: None = Depends(set_claims(make_claims(roles=["moderator"]))),
        __: None = Depends(require_roles(["moderator"], require_all=False)),
    ):
        return {"ok": True}

    client = TestClient(app)

    # read access ok
    assert client.get("/read").status_code == 200
    # admin should fail (403)
    assert client.get("/admin").status_code == 403
    # role match ok
    assert client.get("/role").status_code == 200
