import pytest

from dotmac.platform.observability.config import (
    Environment,
    ExporterConfig,
    ExporterType,
    OTelConfig,
    create_default_config,
    create_otel_config,
)


@pytest.mark.unit
def test_create_default_config_env_defaults_and_exporters():
    dev_cfg = create_default_config("svc", environment=Environment.DEVELOPMENT)
    assert any(e.type == ExporterType.CONSOLE for e in dev_cfg.tracing_exporters)
    assert dev_cfg.trace_sampler_ratio == 1.0

    prod_cfg = create_default_config("svc", environment=Environment.PRODUCTION, otlp_endpoint="https://otlp")
    assert any(e.type == ExporterType.OTLP_GRPC for e in prod_cfg.tracing_exporters)
    assert any((e.endpoint == "https://otlp") for e in prod_cfg.tracing_exporters)
    assert prod_cfg.trace_sampler_ratio == 0.1


@pytest.mark.unit
def test_otel_config_resource_fallback_and_normalization():
    cfg = OTelConfig(service_name="s", environment="staging")
    res = cfg.get_resource()
    # Works even without OTEL installed (dict fallback allowed)
    assert "service.name" in getattr(res, "attributes", getattr(res, "keys", lambda: [])()) or "service.name" in res


@pytest.mark.unit
def test_create_otel_config_overrides():
    cfg = create_otel_config("svc", service_version="2", environment="test", trace_sampler_ratio=0.5, metric_export_interval=10)
    assert cfg.service_version == "2" and cfg.environment == Environment.TEST
    assert cfg.trace_sampler_ratio == 0.5 and cfg.metric_export_interval == 10

