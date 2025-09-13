"""
Unit tests for observability logging utilities: LogContext, LogFilter, LogSampler,
LogAggregator, and PerformanceLogger (core behaviors only).
"""

import time

import pytest

from dotmac.platform.observability.logging import (
    LogAggregator,
    LogContext,
    LogFilter,
    LogLevel,
    LogSampler,
    PerformanceLogger,
    StructuredLogger,
)


@pytest.mark.unit
def test_log_context_helpers():
    ctx = LogContext(tenant_id="t", user_id="u")
    d = ctx.to_dict()
    assert d["tenant_id"] == "t" and d["user_id"] == "u"
    c2 = ctx.with_operation("op-x")
    assert c2.operation == "op-x" and c2.correlation_id == ctx.correlation_id
    c3 = ctx.with_context(x=1)
    assert c3.additional_context["x"] == 1


@pytest.mark.unit
def test_log_filter_should_log():
    f = LogFilter(min_level=LogLevel.INFO, tenant_blocklist=["bad"])
    # Below min level rejected
    assert f.should_log("debug", {"tenant_id": "t"}) is False
    # Allowed tenant
    assert f.should_log("info", {"tenant_id": "t"}) is True
    # Blocklisted tenant
    assert f.should_log("info", {"tenant_id": "bad"}) is False
    # Allowlist wins if set
    f2 = LogFilter(min_level=LogLevel.DEBUG, tenant_allowlist=["good"])  # everything else false
    assert f2.should_log("error", {"tenant_id": "good"}) is True
    assert f2.should_log("error", {"tenant_id": "other"}) is False


@pytest.mark.unit
def test_log_sampler_basic_behavior():
    # Always sample errors
    s = LogSampler(sample_rate=0.0, burst_capacity=100)
    assert s.should_sample({"level": "error"}) is True
    # Never sample info when sample_rate=0
    s2 = LogSampler(sample_rate=0.0, burst_capacity=100)
    assert s2.should_sample({"level": "info"}) is False


@pytest.mark.unit
def test_log_aggregator_aggregation():
    agg = LogAggregator(window_size=1)
    ctx = {"operation": "op", "tenant_id": "t"}
    # First time: no aggregate emitted
    assert agg.add_entry("info", "hello", ctx) is None
    # Next occurrences accumulate
    for _ in range(9):
        res = agg.add_entry("info", "hello", ctx)
    # At 10th occurrence, aggregated entry is emitted
    assert isinstance(res, dict)
    assert "AGGREGATED" in res["message"]
    # Flush generates aggregate for remaining entries (>1)
    out = agg._flush_entries()
    assert isinstance(out, list)


@pytest.mark.unit
def test_performance_logger_timing():
    logger = StructuredLogger(service_name="svc")
    perf = PerformanceLogger(logger)
    op_id = perf.start_operation("op", context={"x": 1})
    time.sleep(0.01)
    duration = perf.end_operation(op_id, success=True, result_data={"y": 2})
    assert duration >= 0
    # Unknown operation_id
    assert perf.end_operation("missing") == 0.0
