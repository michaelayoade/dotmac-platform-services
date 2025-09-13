"""
Tests for CSRFMiddleware double-submit cookie protection.
"""

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from dotmac.platform.auth.csrf import CSRFMiddleware


@pytest.mark.unit
def test_csrf_cookie_and_validation():
    app = FastAPI()
    app.add_middleware(CSRFMiddleware, secure=False, samesite="lax")

    @app.get("/form")
    async def form():  # type: ignore
        return {"ok": True}

    @app.post("/submit")
    async def submit():  # type: ignore
        return {"ok": True}

    client = TestClient(app)

    # GET should set CSRF cookie
    r_get = client.get("/form")
    assert r_get.status_code == 200
    assert "csrf_token" in r_get.cookies

    # POST without header -> 403
    r_bad = client.post("/submit")
    assert r_bad.status_code == 403

    # POST with matching header -> 200
    token = r_get.cookies.get("csrf_token")
    assert token is not None, "CSRF token should be present in cookies"
    r_ok = client.post("/submit", headers={"X-CSRF-Token": token})
    assert r_ok.status_code == 200
