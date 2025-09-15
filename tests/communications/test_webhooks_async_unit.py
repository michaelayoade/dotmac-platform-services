import asyncio
import pytest

from dotmac.platform.communications.config import WebhookConfig
from dotmac.platform.communications.webhooks import WebhookRequest, WebhookService


@pytest.mark.unit
@pytest.mark.asyncio
async def test_webhook_send_async_success_and_failure(monkeypatch):
    class Resp:
        def __init__(self, status_code=200):
            self.status_code = status_code
            self.headers = {"X": "1"}
            self.text = "BODY"

    class FakeAsyncClient:
        def __init__(self, timeout, verify):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def request(self, **params):
            return Resp(200 if params.get("url").endswith("ok") else 500)

    monkeypatch.setattr("httpx.AsyncClient", FakeAsyncClient)

    svc = WebhookService(WebhookConfig())
    ok = await svc.send_async(WebhookRequest(url="https://h/ok"))
    bad = await svc.send_async(WebhookRequest(url="https://h/fail"))
    assert ok.success is True and bad.success is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_webhook_send_with_retry_async(monkeypatch):
    class FakeSvc(WebhookService):
        def __init__(self, cfg):
            super().__init__(cfg)
            self.calls = 0

        async def send_async(self, webhook):
            self.calls += 1
            if self.calls < 2:
                return type("R", (), {"success": False, "status_code": 500})()
            return type("R", (), {"success": True, "status_code": 200})()

    async def fast_sleep(_):
        return None

    monkeypatch.setattr(asyncio, "sleep", lambda s: fast_sleep(s))

    svc = FakeSvc(WebhookConfig(retry_delay=1))
    resp = await svc.send_with_retry_async(WebhookRequest(url="https://h/ok"), max_retries=3)
    assert resp.success is True and svc.calls == 2

