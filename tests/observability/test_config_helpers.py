import pytest

from dotmac.platform.observability.config import (
    Environment,
    ExporterConfig,
    ExporterType,
    OTelConfig,
    _to_exporter_config,
    create_default_config,
)


@pytest.mark.unit
def test_normalize_environment_from_string():
    cfg = OTelConfig(service_name="svc", environment="production")
    assert cfg.environment is Environment.PRODUCTION


@pytest.mark.unit
def test_to_exporter_config_is_case_insensitive():
    cfg = _to_exporter_config("OTLP_GRPC", "grpc://collector:4317")
    assert cfg is not None
    assert cfg.type == ExporterType.OTLP_GRPC


@pytest.mark.unit
def test_to_exporter_config_rejects_unknown_dict():
    assert _to_exporter_config({"type": "zipkin"}, "ignored") is None


@pytest.mark.unit
def test_create_default_config_preserves_exporter_config_instances():
    custom_console = ExporterConfig(type=ExporterType.CONSOLE)
    cfg = create_default_config(
        "svc",
        environment=Environment.DEVELOPMENT,
        tracing_exporters=[custom_console],
        metrics_exporters=["console"],
    )
    assert cfg.tracing_exporters[0] is custom_console
    assert cfg.metrics_exporters[0].type == ExporterType.CONSOLE
