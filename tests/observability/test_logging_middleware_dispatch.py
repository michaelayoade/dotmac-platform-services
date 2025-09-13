"""
Unit test for LoggingMiddleware dispatch path with sanitized headers.
"""

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient


@pytest.mark.unit
def test_logging_middleware_dispatch_sanitizes_headers(monkeypatch):
    from dotmac.platform.observability import middleware as mod

    captured = {"events": []}

    class FakeLogger:
        def __init__(self, *a, **kw):
            pass

        def with_log_context(self, ctx):
            return self

        def info(self, msg: str, **kwargs):
            captured["events"].append(("info", msg, kwargs))

        def error(self, msg: str, **kwargs):
            captured["events"].append(("error", msg, kwargs))

    # Replace StructuredLogger with our fake
    monkeypatch.setattr(mod, "StructuredLogger", FakeLogger)

    app = FastAPI()

    @app.get("/hello")
    async def hello():  # type: ignore
        return {"message": "ok"}

    app.add_middleware(mod.LoggingMiddleware)

    client = TestClient(app)
    r = client.get(
        "/hello",
        headers={
            "Authorization": "Bearer tok",
            "X-Api-Key": "aaa",
            "Cookie": "s=1",
            "User-Agent": "pytest",
        },
    )
    assert r.status_code == 200

    # The first info event should be "Request started"
    kinds = [e[0] for e in captured["events"]]
    assert "info" in kinds
    # Find the request started event and validate redactions
    req_events = [e for e in captured["events"] if e[1] == "Request started"]
    assert req_events, f"No 'Request started' event captured: {captured['events']}"
    headers = req_events[0][2]["headers"]
    # Headers are normalized to lowercase
    assert headers["authorization"] == "***REDACTED***"
    assert headers["x-api-key"] == "***REDACTED***"
    assert headers["cookie"] == "***REDACTED***"
