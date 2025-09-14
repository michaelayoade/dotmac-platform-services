import pytest

from dotmac.platform.communications.config import WebhookConfig
from dotmac.platform.communications.webhooks import WebhookRequest, WebhookService


@pytest.mark.unit
def test_webhook_delete_no_json_and_patch_with_json(monkeypatch):
    captured = []

    class FakeClient:
        def __init__(self, timeout, verify):
            pass

        def request(self, **params):
            # Capture and return 200 OK
            captured.append(params)
            return type("R", (), {"status_code": 200, "headers": {}, "text": ""})()

        def close(self):
            pass

    monkeypatch.setattr("httpx.Client", FakeClient)
    svc = WebhookService(WebhookConfig())

    # DELETE with payload should not include json body per _prepare_request
    del_req = WebhookRequest(url="https://h/del", method="DELETE", payload={"x": 1})
    resp = svc.send(del_req)
    assert resp.success is True
    p1 = captured[-1]
    assert p1["method"] == "DELETE" and p1.get("json") is None

    # PATCH should include json when payload present
    patch_req = WebhookRequest(url="https://h/p", method="PATCH", payload={"a": 2})
    resp2 = svc.send(patch_req)
    assert resp2.success is True
    p2 = captured[-1]
    assert p2["method"] == "PATCH" and p2.get("json") == {"a": 2}

