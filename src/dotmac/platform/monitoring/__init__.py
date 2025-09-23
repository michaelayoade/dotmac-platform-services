"""
Platform monitoring integrations for DotMac Framework.

Provides comprehensive monitoring capabilities including:
- Integration with various monitoring services
- Benchmarking and performance tracking
- Observability data collection
- Alert management
"""

from dotmac.platform.settings import settings

from .benchmarks import (
    BenchmarkManager,
    BenchmarkResult,
    BenchmarkSuite,
    PerformanceBenchmark,
)
from .integrations import (
    MetricData,
    PrometheusIntegration,
)

__all__ = [
    # Settings
    "settings",
    # Integrations
    "MetricData",
    "PrometheusIntegration",
    # Benchmarks
    "BenchmarkManager",
    "PerformanceBenchmark",
    "BenchmarkResult",
    "BenchmarkSuite",
]
