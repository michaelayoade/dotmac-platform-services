"""
Basic import and smoke tests for benchmarking module.
"""

import pytest


@pytest.mark.unit
def test_basic_imports():
    """Test that basic modules can be imported."""
    from dotmac.platform.benchmarking import BenchmarkResult, BenchmarkRunner
    from dotmac.platform.benchmarking.core import benchmark, benchmark_async

    assert BenchmarkRunner is not None
    assert BenchmarkResult is not None
    assert benchmark is not None
    assert benchmark_async is not None


@pytest.mark.unit
def test_benchmarking_functionality():
    """Basic smoke test of core functionality."""
    import time

    from dotmac.platform.benchmarking.core import BenchmarkResult, benchmark

    def test_function():
        time.sleep(0.001)
        return "test"

    # Run benchmark
    result = benchmark(test_function, iterations=2, warmup=1, name="smoke_test")

    assert result.name == "smoke_test"
    assert result.count == 2
    assert result.mean > 0
    assert isinstance(result, BenchmarkResult)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_async_benchmarking():
    """Test async benchmarking functionality."""
    import asyncio

    from dotmac.platform.benchmarking.core import benchmark_async

    async def test_function():
        await asyncio.sleep(0.001)
        return "test"

    # Run async benchmark
    result = await benchmark_async(test_function, iterations=2, warmup=1, name="async_test")

    assert result.name == "async_test"
    assert result.count == 2
    assert result.mean > 0.001  # Should be at least 1ms


@pytest.mark.unit
def test_benchmark_result_properties():
    """Test BenchmarkResult properties and methods."""
    from dotmac.platform.benchmarking.core import BenchmarkResult

    # Create result with samples
    result = BenchmarkResult(name="test", samples=[0.1, 0.2, 0.3])

    assert result.name == "test"
    assert result.count == 3
    assert result.min == 0.1
    assert result.max == 0.3
    assert result.mean == 0.2
    assert result.median == 0.2
    assert result.ops_per_second == 5.0  # 1 / 0.2

    # Test summary
    summary = result.summary()
    assert summary["name"] == "test"
    assert summary["samples"] == 3
    assert "mean_ms" in summary
    assert "ops_per_second" in summary