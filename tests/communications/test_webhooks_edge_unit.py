import pytest

from dotmac.platform.communications.config import WebhookConfig
from dotmac.platform.communications.webhooks import WebhookRequest, WebhookService


@pytest.mark.unit
def test_signing_header_present_even_if_secret_missing():
    cfg = WebhookConfig(sign_requests=True, signature_secret=None)
    svc = WebhookService(cfg)
    req = WebhookRequest(url="https://x", method="POST", payload={"a": 1})
    params = svc._prepare_request(req)
    # Signature header exists but is empty string when secret missing
    assert cfg.signature_header in params["headers"]
    assert params["headers"][cfg.signature_header] == ""


@pytest.mark.unit
def test_test_endpoint_failure_returns_false(monkeypatch):
    class BoomClient:
        def __init__(self, timeout, verify):
            pass

        def head(self, url, timeout):
            raise RuntimeError("x")

        def close(self):
            pass

    monkeypatch.setattr("httpx.Client", BoomClient)
    svc = WebhookService(WebhookConfig())
    assert svc.test_endpoint("https://h") is False

