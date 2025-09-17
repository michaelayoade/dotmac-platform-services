import asyncio

import pytest

from dotmac.platform.monitoring.benchmarks import (
    BenchmarkResult,
    BenchmarkStatus,
    CPUBenchmark,
    PerformanceBenchmark,
)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_benchmarkresult_metrics_and_duration_property():
    br = BenchmarkResult(
        id="1",
        name="n",
        benchmark_type=None,  # type: ignore[arg-type]
        status=BenchmarkStatus.PENDING,
        start_time=__import__("datetime").datetime.utcnow(),
    )
    br.add_metric("m1", 1, "ms", category="c")
    assert br.get_metric("m1").unit == "ms"
    assert br.get_metrics_by_category("c")[0].name == "m1"
    assert isinstance(br.duration_seconds, float) and br.duration_seconds >= 0.0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_performance_benchmark_run_success_and_cancel(monkeypatch):
    class DummyBenchmark(PerformanceBenchmark):
        async def setup(self) -> bool:
            return True

        async def execute(self) -> dict:
            return {"x": 1.0}

        async def teardown(self):
            return None

    bm = DummyBenchmark("d", None)  # type: ignore[arg-type]
    res = await bm.run()
    assert res.status in {BenchmarkStatus.COMPLETED, BenchmarkStatus.FAILED}
    # Our Dummy returns True for setup and provides raw metric, so should complete
    assert res.status == BenchmarkStatus.COMPLETED
    assert res.get_metric("x").value == 1.0

    # Test cancelled path by patching execute to raise CancelledError
    class CancelBenchmark(PerformanceBenchmark):
        async def setup(self) -> bool:
            return True

        async def execute(self) -> dict:
            raise asyncio.CancelledError()

        async def teardown(self):
            return None

    cb = CancelBenchmark("c", None)  # type: ignore[arg-type]
    res2 = await cb.run()
    assert res2.status == BenchmarkStatus.CANCELLED
