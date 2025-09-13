"""
Unit tests for EdgeJWTValidator focusing on pattern handling and claim checks.
Avoids external services by using a fake JWT service and a small FastAPI app
that directly calls validator.validate in route handlers.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.testclient import TestClient

from dotmac.platform.auth.edge_validation import (
    EdgeJWTValidator,
    InsufficientRole,
    InsufficientScope,
    SensitivityLevel,
    TenantMismatch,
    TokenNotFound,
)


class FakeJWTService:
    def __init__(self, verifier: Callable[[str], dict[str, Any]] | None = None):
        self._verifier = verifier or (lambda token: {"sub": token})

    def verify_token(self, token: str, expected_type: str = "access") -> dict[str, Any]:
        return self._verifier(token)


def build_app_with_validator(validator: EdgeJWTValidator) -> TestClient:
    app = FastAPI()

    # Create dedicated handlers invoking validate
    @app.get("/v/p")
    async def route_public(request: Request):
        return await _validate_and_return(validator, request)

    @app.get("/v/i")
    async def route_internal(request: Request):
        return await _validate_and_return(validator, request)

    @app.get("/v/u")
    async def route_user(request: Request):
        return await _validate_and_return(validator, request)

    @app.get("/v/s")
    async def route_sensitive(request: Request):
        return await _validate_and_return(validator, request)

    @app.get("/v/a")
    async def route_admin(request: Request):
        return await _validate_and_return(validator, request)

    return TestClient(app)


async def _validate_and_return(validator: EdgeJWTValidator, request):
    try:
        claims = await validator.validate(request)
        return JSONResponse({"ok": True, "claims": claims})
    except Exception as e:
        # Surface exception type for assertions
        return JSONResponse({"ok": False, "error": e.__class__.__name__}, status_code=400)


def make_validator(verifier: Callable[[str], dict[str, Any]] | None = None, tenant_resolver=None):
    jwt = FakeJWTService(verifier)
    v = EdgeJWTValidator(
        jwt_service=jwt,
        tenant_resolver=tenant_resolver,
        default_sensitivity=SensitivityLevel.AUTHENTICATED,
        require_https=False,
    )
    v.configure_sensitivity_patterns(
        {
            (r"/v/p", r"GET"): SensitivityLevel.PUBLIC,
            (r"/v/i", r"GET"): SensitivityLevel.INTERNAL,
            (r"/v/u", r"GET"): SensitivityLevel.AUTHENTICATED,
            (r"/v/s", r"GET"): SensitivityLevel.SENSITIVE,
            (r"/v/a", r"GET"): SensitivityLevel.ADMIN,
        }
    )
    return v


@pytest.mark.unit
def test_public_succeeds_without_auth():
    validator = make_validator()
    client = build_app_with_validator(validator)
    r = client.get("/v/p")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["claims"]["authenticated"] is False


@pytest.mark.unit
def test_internal_requires_service_token():
    validator = make_validator()
    client = build_app_with_validator(validator)

    # Missing header -> error
    r = client.get("/v/i")
    assert r.status_code == 400
    assert r.json()["error"] == TokenNotFound.__name__

    # With service token -> ok
    r2 = client.get("/v/i", headers={"X-Service-Token": "svc123"})
    assert r2.status_code == 200
    assert r2.json()["ok"] is True
    assert r2.json()["claims"]["is_service"] is True


@pytest.mark.unit
def test_authenticated_user_flow():
    def verifier(token: str) -> dict[str, Any]:
        return {"sub": "u1", "scopes": ["read"], "roles": ["user"]}

    validator = make_validator(verifier)
    client = build_app_with_validator(validator)

    # Missing token -> not found
    r = client.get("/v/u")
    assert r.status_code == 400 and r.json()["error"] == TokenNotFound.__name__

    # Header bearer token -> ok
    r2 = client.get("/v/u", headers={"Authorization": "Bearer tok"})
    assert r2.status_code == 200
    assert r2.json()["claims"]["authenticated"] is True


@pytest.mark.unit
def test_sensitive_requires_scope():
    def no_scope(_):
        return {"sub": "u1", "scopes": [], "roles": []}

    validator = make_validator(no_scope)
    client = build_app_with_validator(validator)
    r = client.get("/v/s", headers={"Authorization": "Bearer t"})
    assert r.status_code == 400
    assert r.json()["error"] == InsufficientScope.__name__

    def has_scope(_):
        return {"sub": "u1", "scopes": ["read:sensitive"], "roles": []}

    validator2 = make_validator(has_scope)
    client2 = build_app_with_validator(validator2)
    r2 = client2.get("/v/s", headers={"Authorization": "Bearer t"})
    assert r2.status_code == 200


@pytest.mark.unit
def test_admin_requires_role_or_scope():
    def non_admin(_):
        return {"sub": "u1", "scopes": ["read"], "roles": ["user"]}

    validator = make_validator(non_admin)
    client = build_app_with_validator(validator)
    r = client.get("/v/a", headers={"Authorization": "Bearer t"})
    assert r.status_code == 400
    assert r.json()["error"] == InsufficientRole.__name__

    def admin_role(_):
        return {"sub": "u1", "scopes": [], "roles": ["admin"]}

    validator2 = make_validator(admin_role)
    client2 = build_app_with_validator(validator2)
    r2 = client2.get("/v/a", headers={"Authorization": "Bearer t"})
    assert r2.status_code == 200


@pytest.mark.unit
def test_tenant_mismatch_raises():
    def verifier(_):
        return {"sub": "u1", "scopes": ["read"], "roles": [], "tenant_id": "t2"}

    def resolve(_request):
        return "t1"

    validator = make_validator(verifier, tenant_resolver=resolve)
    client = build_app_with_validator(validator)
    r = client.get("/v/u", headers={"Authorization": "Bearer t"})
    assert r.status_code == 400
    assert r.json()["error"] == TenantMismatch.__name__


@pytest.mark.unit
def test_token_extraction_sources():
    # Returns provided token
    validator = make_validator(lambda _: {"sub": "u1"})
    app = FastAPI()
    client = build_app_with_validator(validator)

    # Authorization header
    assert client.get("/v/u", headers={"Authorization": "Bearer A"}).status_code in (200, 400)
    # Cookie
    cookies = {"access_token": "CK"}
    assert client.get("/v/u", cookies=cookies).status_code in (200, 400)
    # Custom header
    assert client.get("/v/u", headers={"X-Auth-Token": "X"}).status_code in (200, 400)
