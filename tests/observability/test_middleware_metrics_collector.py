"""
Unit tests for MetricsCollector helper methods in observability middleware.
Focuses on metric API calls without requiring ASGI lifecycle.
"""

import pytest

from dotmac.platform.observability.middleware import MetricsCollector


@pytest.mark.unit
def test_metrics_collector_records():
    mc = MetricsCollector(service_name="svc")

    # Record a variety of metrics to exercise code paths
    mc.record_active_request("GET", "/path", tenant_id="t1", delta=1)
    mc.record_request_size("GET", "/path", 123, tenant_id="t1")
    mc.record_response_size("GET", "/path", 200, 456, tenant_id="t1")
    mc.record_error("GET", "/path", "client_error", tenant_id="t1")
    mc.record_business_operation("op_a", status="success", tenant_id="t1")
    mc.record_security_event("login", severity="low", client_ip="127.0.0.1")
    mc.record_request("GET", "/path", 200, 0.01, tenant_id="t1")

    text = mc.get_metrics()
    assert isinstance(text, str) and "Metrics" in text
