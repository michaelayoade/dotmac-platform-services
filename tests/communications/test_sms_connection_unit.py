import pytest

from dotmac.platform.communications.config import SMSConfig
from dotmac.platform.communications.sms import SMSService


@pytest.mark.unit
def test_sms_test_connection_true_and_exception(monkeypatch):
    class Resp:
        def __init__(self, status_code):
            self.status_code = status_code

    class OkClient:
        def __init__(self, timeout):
            pass

        def get(self, url, headers=None, timeout=None):
            return Resp(200)

        def close(self):
            pass

    monkeypatch.setattr("httpx.Client", OkClient)
    svc = SMSService(SMSConfig(gateway_url="http://gw"))
    assert svc.test_connection() is True

    class BoomClient(OkClient):
        def get(self, url, headers=None, timeout=None):
            raise RuntimeError("boom")

    monkeypatch.setattr("httpx.Client", BoomClient)
    svc2 = SMSService(SMSConfig(gateway_url="http://gw"))
    assert svc2.test_connection() is False

