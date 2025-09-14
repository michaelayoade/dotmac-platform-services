"""
Benchmarking utilities for performance testing.

Provides tools for:
- Function timing and profiling
- HTTP request benchmarking
- Database query benchmarking
- Statistical analysis of results
"""

from .core import (
    BenchmarkResult,
    BenchmarkRunner,
    benchmark,
    benchmark_async,
)
from .http import (
    benchmark_http_request,
    benchmark_http_batch,
)

__all__ = [
    # Core benchmarking
    "BenchmarkResult",
    "BenchmarkRunner",
    "benchmark",
    "benchmark_async",
    # HTTP benchmarking
    "benchmark_http_request",
    "benchmark_http_batch",
]