"""
Unit tests for bootstrap behaviors when OTEL is not available.
We monkeypatch the module variable to simulate missing extras.
"""

import pytest

from dotmac.platform.observability.bootstrap import (
    OTelBootstrap,
    create_child_span,
    get_current_span_context,
    initialize_otel,
    shutdown_otel,
)
from dotmac.platform.observability.config import ExporterConfig, ExporterType, OTelConfig


@pytest.mark.unit
def test_initialize_and_shutdown_with_no_otel(monkeypatch):
    import dotmac.platform.observability.bootstrap as mod

    monkeypatch.setattr(mod, "OTEL_AVAILABLE", False, raising=False)

    cfg = OTelConfig(
        service_name="svc",
        environment="test",
        enable_tracing=True,
        enable_metrics=True,
        tracing_exporters=[ExporterConfig(type=ExporterType.CONSOLE)],
        metrics_exporters=[ExporterConfig(type=ExporterType.CONSOLE)],
    )

    boot = initialize_otel(cfg)
    assert isinstance(boot, OTelBootstrap)
    assert boot.tracer_provider is None and boot.meter_provider is None
    assert boot.is_initialized is False

    # Shutdown should no-op
    shutdown_otel(boot)

    # Span helpers return None
    assert get_current_span_context() in (None, {})
    assert create_child_span("x") is None
