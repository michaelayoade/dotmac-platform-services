import asyncio

import httpx
import pytest

from dotmac.platform.monitoring.integrations import (
    IntegrationConfig,
    IntegrationManager,
    IntegrationStatus,
    SigNozIntegration,
)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_make_request_handles_missing_json_and_content(monkeypatch):
    class RespNoJsonEmpty:
        content = b""

        def raise_for_status(self):
            return None

    class RespNoJsonWithContent(RespNoJsonEmpty):
        content = b"x"

    class FakeClient:
        def __init__(self):
            self.calls = 0

        async def request(self, method, url, json=None):
            self.calls += 1
            return RespNoJsonEmpty() if self.calls == 1 else RespNoJsonWithContent()

        async def aclose(self):
            return None

    integ = SigNozIntegration(IntegrationConfig(name="a", endpoint="http://h"))
    integ.client = FakeClient()
    # First call: empty content -> {}
    r1 = await integ._make_request("GET", "/health")
    assert r1 == {}
    # Second call: content present -> {"ok": True}
    r2 = await integ._make_request("GET", "/health")
    assert r2 == {"ok": True}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_make_request_retries_and_raises(monkeypatch):
    # No sleep - use a proper async no-op
    async def no_sleep(s):
        return
    monkeypatch.setattr(asyncio, "sleep", no_sleep)

    req = httpx.Request("GET", "http://x")
    resp = httpx.Response(500, request=req)
    err = httpx.HTTPStatusError("boom", request=req, response=resp)

    class FailClient:
        async def request(self, method, url, json=None):
            raise err

        async def aclose(self):
            return None

    integ = SigNozIntegration(IntegrationConfig(name="b", endpoint="http://h", retry_count=2))
    integ.client = FailClient()
    with pytest.raises(httpx.HTTPStatusError):
        await integ._make_request("GET", "/fail")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_initialize_failure_sets_error_status(monkeypatch):
    class FakeClient:
        async def aclose(self):
            return None

    integ = SigNozIntegration(IntegrationConfig(name="c", endpoint="http://h"))
    # Force health_check to False
    async def bad_health(self):
        return False

    monkeypatch.setattr(SigNozIntegration, "health_check", bad_health)

    # Avoid real client creation
    async def fake_init(self):
        self.client = FakeClient()
        if await self.health_check():
            self.status = IntegrationStatus.ACTIVE
            return True
        self.status = IntegrationStatus.ERROR
        return False

    monkeypatch.setattr(SigNozIntegration, "initialize", fake_init)
    ok = await integ.initialize()
    assert ok is False and integ.status == IntegrationStatus.ERROR


@pytest.mark.unit
@pytest.mark.asyncio
async def test_manager_remove_nonexistent_and_inactive_broadcast():
    mgr = IntegrationManager()
    assert await mgr.remove_integration("missing") is False
    # No integrations -> empty dicts
    assert await mgr.broadcast_metrics([]) == {}
    assert await mgr.broadcast_alert({}) == {}

