"""
Tests for service-to-service request signing with ServiceAuthMiddleware.
"""

import time

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from dotmac.platform.auth.service_auth import (
    ServiceAuthMiddleware,
    sign_request,
)


class FakeTokenManager:
    def verify_service_token(
        self, token: str, expected_target=None, required_operations=None
    ):  # noqa: ARG002
        # Always accept in tests
        return {"sub": "caller", "allowed_operations": ["*"], "target_service": expected_target}


@pytest.mark.unit
def test_signed_internal_request_passes():
    app = FastAPI()

    app.add_middleware(
        ServiceAuthMiddleware,
        token_manager=FakeTokenManager(),
        service_name="svc",
        require_request_signature=True,
        signing_secret="secret",
    )

    @app.post("/internal/echo")
    async def echo():  # type: ignore
        return {"ok": True}

    client = TestClient(app)

    body = b"{}"
    ts = str(int(time.time()))
    sig = sign_request("secret", "POST", "/internal/echo", body, ts)
    headers = {
        "X-Signature": sig,
        "X-Timestamp": ts,
        "X-Service-Token": "tok",
        "content-type": "application/json",
    }
    r = client.post("/internal/echo", headers=headers, data=body)
    assert r.status_code == 200

    # Bad signature -> 401
    bad = client.post(
        "/internal/echo",
        headers={**headers, "X-Signature": "deadbeef"},
        data=body,
    )
    assert bad.status_code in (401, 403)
