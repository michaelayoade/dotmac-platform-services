"""
Tests for FastAPI API key dependency.
"""

import pytest
from fastapi import Depends, FastAPI
from starlette.testclient import TestClient

from dotmac.platform.auth.api_keys import api_key_dependency


class FakeAPIKeyService:
    async def authenticate_api_key(
        self, api_key: str, request_info: dict | None = None
    ):  # noqa: ARG002
        if api_key == "good":
            return {"key_id": "kid", "scopes": ["read:users", "write:users"]}
        raise Exception("Invalid API key")


@pytest.mark.unit
def test_api_key_dependency_success_and_scope_enforcement():
    app = FastAPI()
    app.state.api_key_service = FakeAPIKeyService()

    @app.get("/ok", dependencies=[Depends(api_key_dependency(["read:users"]))])
    async def ok():  # type: ignore
        return {"ok": True}

    @app.get("/forbidden", dependencies=[Depends(api_key_dependency(["admin:users"]))])
    async def forbidden():  # type: ignore
        return {"ok": True}

    client = TestClient(app)

    # Missing key -> 401
    r0 = client.get("/ok")
    assert r0.status_code == 401

    # Good key -> 200
    r1 = client.get("/ok", headers={"X-API-Key": "good"})
    assert r1.status_code == 200

    # Insufficient scope -> 403
    r2 = client.get("/forbidden", headers={"Authorization": "ApiKey good"})
    assert r2.status_code == 403
