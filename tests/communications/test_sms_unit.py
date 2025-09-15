import base64

import pytest

from dotmac.platform.communications.config import SMSConfig
from dotmac.platform.communications.sms import MockSMSService, SMSMessage, SMSService


@pytest.mark.unit
def test_smsmessage_validators():
    m = SMSMessage(to="(555) 123-4567", body=" hi ")
    assert m.to.replace("+", "").isdigit()
    assert m.body == "hi"
    with pytest.raises(Exception):
        SMSMessage(to="12", body="hello")
    with pytest.raises(Exception):
        SMSMessage(to="+1234567", body="   ")


@pytest.mark.unit
def test_smsservice_auth_headers_prepare():
    cfg = SMSConfig(gateway_auth_type="bearer", gateway_auth_value="tok")
    svc = SMSService(cfg)
    h = svc._prepare_auth_headers()
    assert h.get("Authorization") == "Bearer tok"

    svc.config.gateway_auth_type = "api_key"
    h = svc._prepare_auth_headers()
    assert h.get("X-API-Key") == "tok"

    svc.config.gateway_auth_type = "basic"
    svc.config.gateway_auth_value = "u:p"
    h = svc._prepare_auth_headers()
    assert h.get("Authorization").startswith("Basic ")
    assert base64.b64decode(h["Authorization"].split()[1]).decode() == "u:p"


@pytest.mark.unit
def test_smsservice_send_methods_and_status(monkeypatch):
    class Resp:
        def __init__(self, status_code=200):
            self.status_code = status_code
            self.text = "OK"

    class FakeClient:
        def __init__(self, timeout):
            pass

        def get(self, url, params=None, headers=None):
            assert params and headers is not None
            return Resp(200)

        def post(self, url, json=None, headers=None):
            assert json and headers is not None
            return Resp(202)

        def put(self, url, json=None, headers=None):
            return Resp(500)

        def close(self):
            pass

    monkeypatch.setattr("httpx.Client", FakeClient)

    cfg = SMSConfig(gateway_url="http://gw", gateway_method="GET")
    svc = SMSService(cfg)
    assert svc.send(SMSMessage(to="+15551234567", body="hello")) is True

    svc.config.gateway_method = "POST"
    assert svc.send(SMSMessage(to="+15551234567", body="hello")) is True

    svc.config.gateway_method = "PUT"
    assert svc.send(SMSMessage(to="+15551234567", body="hello")) is False

    # Not configured gateway -> False
    svc.config.gateway_url = None
    assert svc.send(SMSMessage(to="+15551234567", body="hello")) is False


@pytest.mark.unit
def test_mocksmsservice_basic():
    mock = MockSMSService()
    ok = mock.send(SMSMessage(to="+15551234567", body="hello"))
    assert ok and mock.sent_messages and mock.sent_messages[0].body == "hello"

