import asyncio
from dataclasses import dataclass

import pytest

from dotmac.platform.monitoring.integrations import (
    IntegrationConfig,
    IntegrationManager,
    IntegrationStatus,
    MetricData,
    MonitoringIntegration,
    SigNozIntegration,
)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_signoz_integration_health_metrics_alert(monkeypatch):
    # Fake AsyncClient response
    class Resp:
        def __init__(self, payload=None, status_code=200):
            self._payload = payload or {"status": "ok"}
            self.status_code = status_code

        def json(self):
            return self._payload

        def raise_for_status(self):
            if self.status_code >= 400:
                raise Exception("bad status")

    class FakeClient:
        async def request(self, method, url, json=None):
            # health endpoint
            if url.endswith("/api/v1/health"):
                return Resp({"status": "ok"})
            # metrics and alerts
            return Resp({"ok": True})

        async def aclose(self):
            return None

    cfg = IntegrationConfig(name="signoz", endpoint="https://s.example")
    integ = SigNozIntegration(cfg)
    integ.client = FakeClient()

    assert await integ.health_check() is True
    m = MetricData(name="requests", value=1)
    assert await integ.send_metrics([m]) is True
    assert await integ.send_alert({"msg": "hi"}) is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_integration_manager_add_broadcast_status_shutdown(monkeypatch):
    class Dummy(MonitoringIntegration):
        def __init__(self, config: IntegrationConfig):
            super().__init__(config)

        async def health_check(self) -> bool:
            return True

        async def send_metrics(self, metrics):
            return True

        async def send_alert(self, alert_data):
            return True

    cfg = IntegrationConfig(name="dummy", endpoint="https://dummy")
    d = Dummy(cfg)

    # Inject fake client and healthy init
    class NoopClient:
        async def aclose(self):
            return None

    async def fake_initialize(self):
        self.client = NoopClient()
        self.status = IntegrationStatus.ACTIVE
        return True

    monkeypatch.setattr(Dummy, "initialize", fake_initialize)

    mgr = IntegrationManager()
    assert await mgr.add_integration(d) is True
    statuses = await mgr.get_integration_status()
    assert statuses["dummy"] == IntegrationStatus.ACTIVE

    results = await mgr.broadcast_metrics([MetricData(name="x", value=1)])
    assert results["dummy"] is True
    alerts = await mgr.broadcast_alert({"x": 1})
    assert alerts["dummy"] is True

    # Health check all keeps status ACTIVE for healthy integrations
    hc = await mgr.health_check_all()
    assert hc["dummy"] is True

    assert await mgr.remove_integration("dummy") is True
    await mgr.shutdown_all()  # no integrations remain
