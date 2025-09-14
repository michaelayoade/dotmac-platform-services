import pytest

from dotmac.platform.communications.config import SMSConfig
from dotmac.platform.communications.sms import SMSMessage, SMSService


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sms_async_send_paths(monkeypatch):
    class Resp:
        def __init__(self, status_code=200):
            self.status_code = status_code
            self.text = "OK"

    class FakeAsyncClient:
        def __init__(self, timeout):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url, params=None, headers=None):
            return Resp(200)

        async def post(self, url, json=None, headers=None):
            return Resp(202)

        async def put(self, url, json=None, headers=None):
            return Resp(500)

    monkeypatch.setattr("httpx.AsyncClient", FakeAsyncClient)

    cfg = SMSConfig(gateway_url="http://gw", gateway_method="GET")
    svc = SMSService(cfg)
    assert await svc.send_async(SMSMessage(to="+15551234567", body="hello")) is True

    svc.config.gateway_method = "POST"
    assert await svc.send_async(SMSMessage(to="+15551234567", body="hello")) is True

    svc.config.gateway_method = "PUT"
    assert await svc.send_async(SMSMessage(to="+15551234567", body="hello")) is False

