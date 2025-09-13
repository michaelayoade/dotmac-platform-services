"""
Unit tests for ServiceTokenManager and ServiceAuthMiddleware.
Uses HS256 with in-memory setup; no external services.
"""

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from dotmac.platform.auth.exceptions import ConfigurationError, TokenExpired, UnauthorizedService
from dotmac.platform.auth.service_auth import (
    ServiceAuthMiddleware,
    ServiceTokenManager,
    create_service_token_manager,
)


def make_manager():
    return create_service_token_manager(algorithm="HS256", signing_secret="secret")


@pytest.mark.unit
def test_manager_register_issue_verify_and_revoke():
    mgr = make_manager()

    ident = mgr.create_service_identity(
        service_name="svc-a",
        allowed_targets=["svc-b"],
        allowed_operations=["read", "write"],
    )

    # Issue a token for svc-b
    token = mgr.issue_service_token(ident, target_service="svc-b", allowed_operations=["read"])
    assert isinstance(token, str)

    # Must register target to pass verify check
    mgr.create_service_identity("svc-b", allowed_targets=["*"])
    claims = mgr.verify_service_token(token, expected_target="svc-b", required_operations=["read"])
    assert claims["sub"] == "svc-a"
    assert claims["aud"] == "svc-b"

    # Missing required operation fails
    with pytest.raises(UnauthorizedService):
        mgr.verify_service_token(token, expected_target="svc-b", required_operations=["delete"])

    # Revoke source service; verification should fail thereafter
    mgr.revoke_service_tokens("svc-a")
    with pytest.raises(UnauthorizedService):
        mgr.verify_service_token(token, expected_target="svc-b")


@pytest.mark.unit
def test_manager_config_errors_and_rs256():
    # HS256 without secret -> error
    with pytest.raises(ConfigurationError):
        ServiceTokenManager(algorithm="HS256")

    # RS256 without keypair -> error
    with pytest.raises(ConfigurationError):
        ServiceTokenManager(algorithm="RS256", keypair=None)


@pytest.mark.unit
def test_service_auth_middleware_flow():
    mgr = make_manager()
    src = mgr.create_service_identity("A", allowed_targets=["B"], allowed_operations=["op"])
    mgr.create_service_identity("B", allowed_targets=["*"])  # target registered
    token = mgr.issue_service_token(src, target_service="B", allowed_operations=["op"])

    app = FastAPI()

    @app.get("/internal/hello")
    async def protected():  # type: ignore
        return {"ok": True}

    app.add_middleware(
        ServiceAuthMiddleware,
        token_manager=mgr,
        service_name="B",
        required_operations=["op"],
        protected_paths=["/internal"],
    )

    client = TestClient(app)

    # Missing token -> 401
    r = client.get("/internal/hello")
    assert r.status_code == 401

    # With token -> 200
    r2 = client.get("/internal/hello", headers={"X-Service-Token": token})
    assert r2.status_code == 200


@pytest.mark.unit
def test_expired_service_token_raises():
    mgr = make_manager()
    src = mgr.create_service_identity("svcX", allowed_targets=["svcY"], allowed_operations=["op"])
    mgr.create_service_identity("svcY", allowed_targets=["*"])

    # Force past expiration
    token = mgr.issue_service_token(
        src, target_service="svcY", allowed_operations=["op"], expires_in=-1
    )

    with pytest.raises(TokenExpired):
        mgr.verify_service_token(token, expected_target="svcY")
