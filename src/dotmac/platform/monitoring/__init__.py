"""
Platform monitoring integrations for DotMac Framework.

Provides comprehensive monitoring capabilities including:
- Integration with various monitoring services
- Benchmarking and performance tracking
- Observability data collection
- Alert management
- REST APIs for logs and traces
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
from .logs_router import logs_router
from .traces_router import traces_router

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
    # Routers
    "logs_router",
    "traces_router",
]
