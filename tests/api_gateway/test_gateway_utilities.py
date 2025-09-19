"""Additional unit coverage for API gateway helpers."""

import json
from types import SimpleNamespace

import pytest

from dotmac.platform.api_gateway.config import GatewayConfig
from dotmac.platform.api_gateway.gateway import (
    APIGateway,
    ObservabilityFacade,
    HeaderVersioning,
    PathVersioning,
    QueryVersioning,
)


class _FakeSpan:
    def __init__(self):
        self.ended = False

    def end(self):
        self.ended = True


class _FakeTracer:
    def __init__(self):
        self.started = []

    def start_span(self, name: str, attributes=None):
        self.started.append((name, attributes or {}))
        return _FakeSpan()


@pytest.fixture(autouse=True)
def stub_gateway_analytics(monkeypatch):
    tracer = _FakeTracer()
    analytics = SimpleNamespace(collector=SimpleNamespace(tracer=tracer))
    adapter = SimpleNamespace(analytics=analytics, create_request_span=lambda **_: _FakeSpan())
    monkeypatch.setattr(
        "dotmac.platform.api_gateway.gateway.get_gateway_analytics",
        lambda **kwargs: adapter,
    )
    return adapter


def test_observability_facade_spans(monkeypatch):
    tracer = _FakeTracer()
    monkeypatch.setattr(
        "dotmac.platform.api_gateway.gateway.trace.get_tracer", lambda _: tracer
    )

    facade = ObservabilityFacade("api-gateway", "localhost:4317", analytics_adapter=None)

    span = facade.start_span("test-span", {"key": "value"})
    assert tracer.started == [("test-span", {"key": "value"})]

    facade.end_span(span)
    assert span.ended is True


def test_create_jwt_service_falls_back_to_hs256(monkeypatch):
    monkeypatch.setenv("DOTMAC_JWT_ALGORITHM", "RS256")
    monkeypatch.delenv("DOTMAC_JWT_PRIVATE_KEY", raising=False)
    monkeypatch.delenv("DOTMAC_JWT_PUBLIC_KEY", raising=False)
    monkeypatch.setenv("DOTMAC_JWT_SECRET_KEY", "fallback-secret")

    config = GatewayConfig()
    gateway = APIGateway(config=config)

    assert gateway.jwt_service.algorithm == "HS256"


def test_json_error_shapes_payload(monkeypatch):
    monkeypatch.delenv("DOTMAC_JWT_ALGORITHM", raising=False)
    gateway = APIGateway(config=GatewayConfig.for_development())

    response = gateway._json_error(
        status_code=403,
        code="forbidden",
        message="Access denied",
        details={"scope": "admin"},
        headers={"X-Custom": "value"},
    )

    body = json.loads(response.body.decode())
    assert response.status_code == 403
    assert response.headers["X-Custom"] == "value"
    assert body == {
        "error": {
            "code": "forbidden",
            "message": "Access denied",
            "details": {"scope": "admin"},
        }
    }


def test_version_strategy_selection(monkeypatch):
    monkeypatch.delenv("DOTMAC_JWT_ALGORITHM", raising=False)
    gateway = APIGateway(config=GatewayConfig.for_development())

    assert isinstance(gateway._create_version_strategy("header"), HeaderVersioning)
    assert isinstance(gateway._create_version_strategy("path"), PathVersioning)
    assert isinstance(gateway._create_version_strategy("query"), QueryVersioning)
    assert isinstance(gateway._create_version_strategy("unknown"), HeaderVersioning)


def test_observability_facade_metrics_and_status():
    facade = ObservabilityFacade("service", "collector")

    metrics = facade.get_metrics()
    status = facade.export_otlp_status()

    assert metrics == {"counters": {}, "histograms": {}}
    assert status["enabled"] is True
    assert status["service_name"] == "service"
