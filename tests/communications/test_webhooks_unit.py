import json as _json
import time

import pytest

from dotmac.platform.communications.config import WebhookConfig
from dotmac.platform.communications.webhooks import WebhookRequest, WebhookService


@pytest.mark.unit
def test_webhook_request_validation_and_prepare_and_signature(monkeypatch):
    cfg = WebhookConfig(sign_requests=True, signature_secret="sec", allowed_schemes=["http", "https"])
    svc = WebhookService(cfg)

    wh = WebhookRequest(url="http://example.com/hook", method="POST", payload={"a": 1})
    params = svc._prepare_request(wh)
    assert params["headers"]["User-Agent"].startswith("DotMac-Platform-Webhook")
    assert params["json"] == {"a": 1}
    assert cfg.signature_header in params["headers"]

    # Disallowed scheme
    svc.config.allowed_schemes = ["https"]
    with pytest.raises(ValueError):
        svc._prepare_request(WebhookRequest(url="http://not-allowed"))


@pytest.mark.unit
def test_webhook_send_success_and_error(monkeypatch):
    class Resp:
        def __init__(self, status_code=200):
            self.status_code = status_code
            self.headers = {"X": "1"}
            self.text = "BODY"

    class FakeClient:
        def __init__(self, timeout, verify):
            pass

        def request(self, **params):
            return Resp(200 if params.get("url").endswith("ok") else 500)

        def head(self, url, timeout):
            return Resp(200)

        def close(self):
            pass

    monkeypatch.setattr("httpx.Client", FakeClient)

    svc = WebhookService(WebhookConfig())
    ok = svc.send(WebhookRequest(url="https://h/ok"))
    bad = svc.send(WebhookRequest(url="https://h/fail"))
    assert ok.success is True and bad.success is False and bad.error is None and bad.status_code == 500
    assert svc.test_endpoint("https://h/test") is True


@pytest.mark.unit
def test_webhook_send_with_retry(monkeypatch):
    calls = {"n": 0}

    class FakeSvc(WebhookService):
        def send(self, webhook):
            calls["n"] += 1
            # Fail first, then succeed
            if calls["n"] < 2:
                return type("R", (), {"success": False, "status_code": 500})()
            return type("R", (), {"success": True, "status_code": 200})()

    svc = FakeSvc(WebhookConfig(retry_delay=1))
    delays = []
    monkeypatch.setattr(time, "sleep", lambda s: delays.append(s))
    resp = svc.send_with_retry(WebhookRequest(url="https://h/ok"), max_retries=3)
    assert resp.success is True and calls["n"] == 2 and delays == [1]
