"""
Tests for ObservabilityManager (pytest-style, no prints or sys.path hacks).
"""

import pytest
from fastapi import FastAPI

from dotmac.platform.observability import ObservabilityManager


@pytest.mark.unit
def test_basic_usage():
    mgr = ObservabilityManager(
        service_name="test-service",
        environment="development",
        otlp_endpoint="http://localhost:4317",
        log_level="INFO",
    )

    mgr.initialize()
    assert mgr.is_initialized is True

    # Logger available and callable
    logger = mgr.get_logger()
    assert logger is not None
    logger.info("test log from unit test")

    # Apply middleware on a minimal FastAPI app
    app = FastAPI(title="Test App")
    mgr.apply_middleware(app)

    # Components accessible
    assert mgr.get_metrics_registry() is not None
    assert mgr.get_tracing_manager() is not None
    assert mgr.get_otel_bootstrap() is not None

    mgr.shutdown()
    assert mgr.is_initialized is False


@pytest.mark.unit
def test_context_manager():
    with ObservabilityManager(service_name="ctx-service", environment="development") as mgr:
        assert mgr.is_initialized is True
        logger = mgr.get_logger()
        assert logger is not None


@pytest.mark.unit
def test_selective_middleware():
    mgr = ObservabilityManager(
        service_name="selective-service",
        enable_security=False,
        enable_performance=True,
    )
    mgr.initialize()

    app = FastAPI(title="Selective Middleware App")
    mgr.apply_middleware(
        app,
        enable_metrics=True,
        enable_tracing=True,
        enable_logging=True,
        enable_performance=False,
        enable_security=True,
    )

    mgr.shutdown()
