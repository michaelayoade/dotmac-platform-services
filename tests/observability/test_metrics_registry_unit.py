import pytest

from dotmac.platform.observability.metrics.registry import (
    MetricDefinition,
    MetricInstrument,
    MetricType,
    MetricsRegistry,
)


@pytest.mark.unit
def test_register_metrics_and_list_info_and_duplicates():
    reg = MetricsRegistry(service_name="svc")
    d1 = MetricDefinition(name="m1", type=MetricType.COUNTER, description="c")
    d2 = MetricDefinition(name="m2", type=MetricType.HISTOGRAM, description="h")

    assert reg.register_metric(d1) is True
    assert reg.register_metric(d2) is True
    # duplicate
    assert reg.register_metric(d1) is False

    names = reg.list_metrics()
    assert set(names) == {"m1", "m2"}

    info = reg.get_metrics_info()
    assert info["m1"]["type"] == MetricType.COUNTER.value
    assert info["m2"]["type"] == MetricType.HISTOGRAM.value
    assert isinstance(info["m1"]["labels"], list)

    # record missing metric -> warn but no exception
    reg.record_metric("nope", 1)


@pytest.mark.unit
def test_register_flexible_signatures_and_record_paths():
    reg = MetricsRegistry(service_name="svc")
    d = MetricDefinition(name="a", type=MetricType.GAUGE, description="g")

    # register(definition)
    assert reg.register(d) is True
    # register(name, definition) legacy
    d2 = MetricDefinition(name="ignored", type=MetricType.UP_DOWN_COUNTER, description="u")
    assert reg.register("b", d2) is True
    # register(definition=..., name=...) kwargs
    d3 = MetricDefinition(name="ignored2", type=MetricType.HISTOGRAM, description="h")
    assert reg.register(definition=d3, name="c") is True

    # record calls should not raise even without OTEL
    reg.increment_counter("b", 2)
    reg.set_gauge("a", 5)
    reg.observe_histogram("c", 0.5)
