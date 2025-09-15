"""Core benchmarking utilities."""

import asyncio
import statistics
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from pydantic import BaseModel, Field


@dataclass
class BenchmarkResult:
    """Results from a benchmark run."""

    name: str
    samples: list[float] = field(default_factory=list)
    errors: int = 0

    @property
    def count(self) -> int:
        """Number of successful samples."""
        return len(self.samples)

    @property
    def min(self) -> float:
        """Minimum time in seconds."""
        return min(self.samples) if self.samples else 0.0

    @property
    def max(self) -> float:
        """Maximum time in seconds."""
        return max(self.samples) if self.samples else 0.0

    @property
    def mean(self) -> float:
        """Mean time in seconds."""
        return statistics.mean(self.samples) if self.samples else 0.0

    @property
    def median(self) -> float:
        """Median time in seconds."""
        return statistics.median(self.samples) if self.samples else 0.0

    @property
    def stdev(self) -> float:
        """Standard deviation in seconds."""
        return statistics.stdev(self.samples) if len(self.samples) > 1 else 0.0

    def percentile(self, p: float) -> float:
        """
        Get percentile value.

        Args:
            p: Percentile (0-100)

        Returns:
            Time at percentile
        """
        if not self.samples:
            return 0.0

        sorted_samples = sorted(self.samples)
        index = int(len(sorted_samples) * p / 100)
        return sorted_samples[min(index, len(sorted_samples) - 1)]

    @property
    def p50(self) -> float:
        """50th percentile (median)."""
        return self.percentile(50)

    @property
    def p95(self) -> float:
        """95th percentile."""
        return self.percentile(95)

    @property
    def p99(self) -> float:
        """99th percentile."""
        return self.percentile(99)

    @property
    def ops_per_second(self) -> float:
        """Operations per second based on mean time."""
        return 1.0 / self.mean if self.mean > 0 else 0.0

    def summary(self) -> dict[str, Any]:
        """Get summary statistics."""
        return {
            "name": self.name,
            "samples": self.count,
            "errors": self.errors,
            "min_ms": self.min * 1000,
            "max_ms": self.max * 1000,
            "mean_ms": self.mean * 1000,
            "median_ms": self.median * 1000,
            "stdev_ms": self.stdev * 1000,
            "p50_ms": self.p50 * 1000,
            "p95_ms": self.p95 * 1000,
            "p99_ms": self.p99 * 1000,
            "ops_per_second": self.ops_per_second,
        }

    def __str__(self) -> str:
        """String representation."""
        return (
            f"{self.name}: "
            f"samples={self.count}, "
            f"mean={self.mean*1000:.2f}ms, "
            f"p95={self.p95*1000:.2f}ms, "
            f"ops/s={self.ops_per_second:.1f}"
        )


class BenchmarkRunner:
    """Runner for benchmarks."""

    def __init__(
        self,
        warmup: int = 5,
        iterations: int = 100,
        timeout: float = 30.0,
    ):
        """
        Initialize benchmark runner.

        Args:
            warmup: Number of warmup iterations
            iterations: Number of benchmark iterations
            timeout: Maximum time per iteration in seconds
        """
        self.warmup = warmup
        self.iterations = iterations
        self.timeout = timeout

    def run(
        self,
        func: Callable[[], Any],
        name: str | None = None,
    ) -> BenchmarkResult:
        """
        Run synchronous benchmark.

        Args:
            func: Function to benchmark
            name: Benchmark name

        Returns:
            Benchmark results
        """
        name = name or func.__name__
        result = BenchmarkResult(name)

        # Warmup
        for _ in range(self.warmup):
            try:
                func()
            except Exception:
                pass

        # Benchmark
        for _ in range(self.iterations):
            try:
                start = time.perf_counter()
                func()
                duration = time.perf_counter() - start
                result.samples.append(duration)
            except Exception:
                result.errors += 1

        return result

    async def run_async(
        self,
        func: Callable[[], Any],
        name: str | None = None,
    ) -> BenchmarkResult:
        """
        Run asynchronous benchmark.

        Args:
            func: Async function to benchmark
            name: Benchmark name

        Returns:
            Benchmark results
        """
        name = name or func.__name__
        result = BenchmarkResult(name)

        # Warmup
        for _ in range(self.warmup):
            try:
                await asyncio.wait_for(func(), timeout=self.timeout)
            except Exception:
                pass

        # Benchmark
        for _ in range(self.iterations):
            try:
                start = time.perf_counter()
                await asyncio.wait_for(func(), timeout=self.timeout)
                duration = time.perf_counter() - start
                result.samples.append(duration)
            except Exception:
                result.errors += 1

        return result

    def compare(
        self,
        results: list[BenchmarkResult],
    ) -> dict[str, Any]:
        """
        Compare multiple benchmark results.

        Args:
            results: List of results to compare

        Returns:
            Comparison data
        """
        if not results:
            return {}

        baseline = results[0]
        comparison: dict[str, Any] = {
            "baseline": baseline.summary(),
            "results": [],
        }
        # Also map results by name for convenience in consumers/tests
        comparison[baseline.name] = comparison["baseline"]

        for result in results[1:]:
            speedup = baseline.mean / result.mean if result.mean > 0 else 0
            entry = {
                **result.summary(),
                "speedup": speedup,
                "speedup_pct": (speedup - 1) * 100,
            }
            comparison["results"].append(entry)
            comparison[result.name] = entry

        return comparison


def benchmark(
    func: Callable[[], Any],
    warmup: int = 5,
    iterations: int = 100,
    name: str | None = None,
) -> BenchmarkResult:
    """
    Quick benchmark function.

    Args:
        func: Function to benchmark
        warmup: Warmup iterations
        iterations: Benchmark iterations
        name: Benchmark name

    Returns:
        Benchmark results
    """
    runner = BenchmarkRunner(warmup=warmup, iterations=iterations)
    return runner.run(func, name)


async def benchmark_async(
    func: Callable[[], Any],
    warmup: int = 5,
    iterations: int = 100,
    name: str | None = None,
) -> BenchmarkResult:
    """
    Quick async benchmark function.

    Args:
        func: Async function to benchmark
        warmup: Warmup iterations
        iterations: Benchmark iterations
        name: Benchmark name

    Returns:
        Benchmark results
    """
    runner = BenchmarkRunner(warmup=warmup, iterations=iterations)
    return await runner.run_async(func, name)
