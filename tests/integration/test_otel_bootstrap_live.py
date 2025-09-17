"""
Integration test for OTLP export via ObservabilityManager against a live
OpenTelemetry Collector (e.g., backing SigNoz).

Requires the following environment variable (or defaults to localhost):
- DOTMAC_OTLP_ENDPOINT (e.g., http://localhost:4317)
"""

import os

import pytest
import os

from dotmac.platform.observability import ObservabilityManager

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("DOTMAC_LIVE") != "1", reason="Live integration disabled (set DOTMAC_LIVE=1)"
    ),
]


def test_observability_manager_with_otlp() -> None:
    endpoint = os.getenv("DOTMAC_OTLP_ENDPOINT", "http://localhost:4317")

    mgr = ObservabilityManager(
        service_name="integration-observability",
        environment="development",
        otlp_endpoint=endpoint,
        enable_tracing=True,
        enable_metrics=True,
        enable_logging=True,
    )

    # Initialize and ensure no exceptions
    mgr.initialize()
    assert mgr.is_initialized is True

    # Start a traced operation
    tracer_mgr = mgr.get_tracing_manager()
    assert tracer_mgr is not None
    with tracer_mgr.trace("integration-operation"):
        # Record a default metric using the registry
        reg = mgr.get_metrics_registry()
        assert reg is not None
        reg.increment_counter(
            "http_requests_total",
            1,
            {"method": "GET", "endpoint": "/integration", "status_code": "200"},
        )

        # Log a message to ensure logger is available
        logger = mgr.get_logger()
        logger.info("integration log", path="/integration", status=200)

    # Shutdown cleanly
    mgr.shutdown()
