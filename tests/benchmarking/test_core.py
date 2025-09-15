"""Tests for benchmarking core module."""

import asyncio
import time
from unittest.mock import Mock, patch

import pytest

from dotmac.platform.benchmarking.core import (
    BenchmarkResult,
    BenchmarkRunner,
    benchmark,
    benchmark_async,
)


class TestBenchmarkResult:
    """Test BenchmarkResult class."""

    def test_empty_result(self):
        """Test empty benchmark result."""
        result = BenchmarkResult(name="test")
        assert result.name == "test"
        assert result.count == 0
        assert result.min == 0.0
        assert result.max == 0.0
        assert result.mean == 0.0
        assert result.median == 0.0
        assert result.stdev == 0.0
        assert result.errors == 0

    def test_result_with_samples(self):
        """Test benchmark result with samples."""
        result = BenchmarkResult(name="test", samples=[1.0, 2.0, 3.0, 4.0, 5.0])
        assert result.count == 5
        assert result.min == 1.0
        assert result.max == 5.0
        assert result.mean == 3.0
        assert result.median == 3.0
        assert result.stdev > 0

    def test_result_with_single_sample(self):
        """Test benchmark result with single sample."""
        result = BenchmarkResult(name="test", samples=[2.5])
        assert result.count == 1
        assert result.min == 2.5
        assert result.max == 2.5
        assert result.mean == 2.5
        assert result.median == 2.5
        assert result.stdev == 0.0

    def test_percentile(self):
        """Test percentile calculation."""
        result = BenchmarkResult(name="test", samples=[1.0, 2.0, 3.0, 4.0, 5.0])
        assert result.percentile(50) == 3.0  # median
        assert result.percentile(0) == 1.0  # min
        assert result.percentile(100) == 5.0  # max

    def test_percentile_empty(self):
        """Test percentile with no samples."""
        result = BenchmarkResult(name="test")
        assert result.percentile(50) == 0.0

    def test_ops_per_second(self):
        """Test operations per second calculation."""
        result = BenchmarkResult(name="test", samples=[0.1, 0.2, 0.1])  # 100ms, 200ms, 100ms
        ops = result.ops_per_second
        assert ops > 0
        # Mean is 0.133s, so ~7.5 ops/sec
        assert 7 < ops < 8

    def test_ops_per_second_empty(self):
        """Test ops per second with no samples."""
        result = BenchmarkResult(name="test")
        assert result.ops_per_second == 0.0

    def test_summary(self):
        """Test summary generation."""
        result = BenchmarkResult(name="test", samples=[1.0, 2.0], errors=1)
        summary = result.summary()
        assert summary["name"] == "test"
        assert summary["samples"] == 2
        assert summary["errors"] == 1
        assert "mean_ms" in summary
        assert "p50_ms" in summary
        assert summary["mean_ms"] == 1500.0  # mean of 1.5s = 1500ms


class TestBenchmarkRunner:
    """Test BenchmarkRunner class."""

    def test_benchmark_runner_init(self):
        """Test benchmark runner initialization."""
        runner = BenchmarkRunner(iterations=100, warmup=5)
        assert runner.iterations == 100
        assert runner.warmup == 5

    def test_run_sync_function(self):
        """Test running sync benchmark."""
        counter = {"value": 0}

        def test_func():
            counter["value"] += 1
            time.sleep(0.001)  # 1ms

        runner = BenchmarkRunner(iterations=5, warmup=2)
        result = runner.run(test_func, name="test")

        assert counter["value"] == 7  # 5 iterations + 2 warmup
        assert result.count == 5
        assert all(s >= 0.001 for s in result.samples)

    def test_run_with_error(self):
        """Test benchmark with errors."""
        call_count = {"value": 0}

        def failing_func():
            call_count["value"] += 1
            if call_count["value"] > 2:  # Fail after warmup
                raise ValueError("Test error")

        runner = BenchmarkRunner(iterations=5, warmup=2)
        result = runner.run(failing_func, name="test")

        assert result.errors == 5  # All iterations fail
        assert result.count == 0  # No successful samples

    @pytest.mark.asyncio
    async def test_run_async_function(self):
        """Test running async benchmark."""
        counter = {"value": 0}

        async def test_func():
            counter["value"] += 1
            await asyncio.sleep(0.001)  # 1ms

        runner = BenchmarkRunner(iterations=5, warmup=2)
        result = await runner.run_async(test_func, name="test")

        assert counter["value"] == 7  # 5 iterations + 2 warmup
        assert result.count == 5
        assert all(s >= 0.001 for s in result.samples)

    @pytest.mark.asyncio
    async def test_run_async_with_error(self):
        """Test async benchmark with errors."""
        call_count = {"value": 0}

        async def failing_func():
            call_count["value"] += 1
            if call_count["value"] > 2:  # Fail after warmup
                raise ValueError("Test error")

        runner = BenchmarkRunner(iterations=5, warmup=2)
        result = await runner.run_async(failing_func, name="test")

        assert result.errors == 5  # All iterations fail
        assert result.count == 0  # No successful samples


# Removed TestBenchmarkSuite as it doesn't exist in the actual code
class TestBenchmarkFunctions:
    """Test benchmark functions."""

    def test_benchmark_function(self):
        """Test benchmark function."""
        counter = {"value": 0}

        def test_func():
            counter["value"] += 1
            return counter["value"]

        result = benchmark(test_func, iterations=3, warmup=1, name="test")
        assert result.name == "test"
        assert counter["value"] == 4  # 3 iterations + 1 warmup

    @pytest.mark.asyncio
    async def test_benchmark_async_function(self):
        """Test benchmark_async function."""
        counter = {"value": 0}

        async def test_func():
            counter["value"] += 1
            await asyncio.sleep(0.001)
            return counter["value"]

        result = await benchmark_async(test_func, iterations=3, warmup=1, name="test")
        assert result.name == "test"
        assert counter["value"] == 4  # 3 iterations + 1 warmup




@pytest.mark.unit
class TestBenchmarkIntegration:
    """Integration tests for benchmarking."""

    def test_full_benchmark_flow(self):
        """Test complete benchmark flow."""
        # Functions to benchmark
        def fast_func():
            x = 1 + 1
            return x

        def slow_func():
            time.sleep(0.001)
            return 42

        # Run benchmarks
        fast_result = benchmark(fast_func, iterations=10, warmup=2, name="fast")
        slow_result = benchmark(slow_func, iterations=10, warmup=2, name="slow")

        # Verify results
        assert fast_result.name == "fast"
        assert slow_result.name == "slow"
        assert fast_result.count == 10
        assert slow_result.count == 10
        assert fast_result.mean < slow_result.mean  # fast should be faster

        # Test comparison
        runner = BenchmarkRunner()
        comparison = runner.compare([fast_result, slow_result])
        assert comparison is not None
        assert "baseline" in comparison
        assert "results" in comparison
        # Check that baseline is the fast function (first in list)
        assert comparison["baseline"]["name"] == "fast"
        # Check that results contains the slow function
        assert len(comparison["results"]) == 1
        assert comparison["results"][0]["name"] == "slow"