"""
Platform monitoring integrations for DotMac Framework.

Provides comprehensive monitoring capabilities including:
- Integration with various monitoring services
- Benchmarking and performance tracking
- Observability data collection
- Alert management
- Health checks
- REST APIs for logs and traces
"""

from dotmac.platform.settings import settings

from .benchmarks import (
    BenchmarkManager,
    BenchmarkResult,
    BenchmarkSuite,
    PerformanceBenchmark,
)
from .health_checks import (
    HealthChecker,
    ServiceHealth,
    ServiceStatus,
    check_startup_dependencies,
    ensure_infrastructure_running,
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
    # Health checks
    "HealthChecker",
    "ServiceHealth",
    "ServiceStatus",
    "check_startup_dependencies",
    "ensure_infrastructure_running",
    # Routers
    "logs_router",
    "traces_router",
]
