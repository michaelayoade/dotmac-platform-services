import pytest

from dotmac.platform.observability.config import (
    Environment,
    ExporterConfig,
    ExporterType,
    OTelConfig,
    _to_exporter_config,
    create_default_config,
    create_otel_config,
)


@pytest.mark.unit
def test_to_exporter_config_string_variants():
    grpc_cfg = _to_exporter_config("otlp", "grpc://collector:4317")
    assert grpc_cfg is not None
    assert grpc_cfg.type == ExporterType.OTLP_GRPC
    assert grpc_cfg.endpoint == "grpc://collector:4317"

    http_cfg = _to_exporter_config(" otlp_http ", "http://collector:4318")
    assert http_cfg is not None
    assert http_cfg.type == ExporterType.OTLP_HTTP
    assert http_cfg.endpoint == "http://collector:4318"

    console_cfg = _to_exporter_config("console", None)
    assert console_cfg is not None
    assert console_cfg.type == ExporterType.CONSOLE

    assert _to_exporter_config("unknown", "ignored") is None


@pytest.mark.unit
def test_to_exporter_config_dict_variants():
    cfg = _to_exporter_config(
        {"type": "otlp_http", "headers": {"x-api-key": "secret"}, "timeout": 1234},
        "http://fallback",
    )
    assert cfg is not None
    assert cfg.type == ExporterType.OTLP_HTTP
    # Values in dict should be preserved and endpoint default used when missing
    assert cfg.endpoint == "http://fallback"
    assert cfg.headers == {"x-api-key": "secret"}
    assert cfg.timeout == 1234

    # Existing ExporterConfig should be returned unchanged
    original = ExporterConfig(type=ExporterType.CONSOLE, endpoint="std")
    assert _to_exporter_config(original, None) is original

    # Dicts with missing or invalid types should be rejected
    assert _to_exporter_config({"endpoint": "x"}, None) is None
    assert _to_exporter_config({"type": "unsupported"}, None) is None


@pytest.mark.unit
def test_create_default_config_env_defaults_and_exporters():
    dev_cfg = create_default_config("svc", environment=Environment.DEVELOPMENT)
    assert any(e.type == ExporterType.CONSOLE for e in dev_cfg.tracing_exporters)
    assert dev_cfg.trace_sampler_ratio == 1.0

    prod_cfg = create_default_config(
        "svc", environment=Environment.PRODUCTION, otlp_endpoint="https://otlp"
    )
    assert any(e.type == ExporterType.OTLP_GRPC for e in prod_cfg.tracing_exporters)
    assert any((e.endpoint == "https://otlp") for e in prod_cfg.tracing_exporters)
    assert prod_cfg.trace_sampler_ratio == 0.1


@pytest.mark.unit
def test_otel_config_resource_fallback_and_normalization():
    cfg = OTelConfig(service_name="s", environment="staging")
    res = cfg.get_resource()
    # Works even without OTEL installed (dict fallback allowed)
    assert (
        "service.name" in getattr(res, "attributes", getattr(res, "keys", lambda: [])())
        or "service.name" in res
    )


@pytest.mark.unit
def test_create_otel_config_overrides():
    cfg = create_otel_config(
        "svc",
        service_version="2",
        environment="test",
        trace_sampler_ratio=0.5,
        metric_export_interval=10,
    )
    assert cfg.service_version == "2" and cfg.environment == Environment.TEST
    assert cfg.trace_sampler_ratio == 0.5 and cfg.metric_export_interval == 10


@pytest.mark.unit
def test_create_default_config_custom_exporters_and_filtering():
    cfg = create_default_config(
        "svc",
        environment="production",
        tracing_exporters=["otlp", "console", "invalid"],
        metrics_exporters=[ExporterConfig(type=ExporterType.CONSOLE), {"type": "otlp_http"}],
        otlp_endpoint="grpc://collector:4317",
    )

    tracing_types = [exp.type for exp in cfg.tracing_exporters]
    assert tracing_types.count(ExporterType.OTLP_GRPC) == 1
    assert tracing_types.count(ExporterType.CONSOLE) == 1
    assert len(tracing_types) == 2  # "invalid" entry filtered out

    metric_types = [exp.type for exp in cfg.metrics_exporters]
    assert ExporterType.CONSOLE in metric_types
    assert ExporterType.OTLP_HTTP in metric_types
    assert cfg.trace_sampler_ratio == 0.1


@pytest.mark.unit
def test_otel_config_resource_fallback(monkeypatch):
    cfg = OTelConfig(
        service_name="svc",
        environment=Environment.TEST,
        custom_resource_attributes={"team": "platform"},
    )

    try:
        import opentelemetry.sdk.resources as resources  # type: ignore
    except ImportError:
        res = cfg.get_resource()
        assert isinstance(res, dict)
        assert res["team"] == "platform"
    else:
        def boom(*_args, **_kwargs):
            raise RuntimeError("Resource error")

        monkeypatch.setattr(resources.Resource, "create", staticmethod(boom))
        res = cfg.get_resource()
        assert isinstance(res, dict)
        assert res["team"] == "platform"
