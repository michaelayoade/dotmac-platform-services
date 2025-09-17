"""
Metrics registry slice tests: register/get/record no external systems.
"""

from dotmac.platform.observability.metrics.registry import (
    MetricDefinition,
    MetricType,
    MetricsRegistry,
)


def test_metrics_registry_register_and_get():
    reg = MetricsRegistry(service_name="svc")

    d = MetricDefinition(
        name="app.requests",
        type=MetricType.COUNTER,
        description="App request count",
        labels=["method"],
    )
    assert reg.register(d) is True
    got = reg.get("app.requests")
    assert got is not None and got.name == "app.requests"
