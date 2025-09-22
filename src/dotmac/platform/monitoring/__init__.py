"""
Platform monitoring integrations for DotMac Framework.

Provides comprehensive monitoring capabilities including:
- Integration with various monitoring services
- Benchmarking and performance tracking
- Observability data collection
- Alert management
"""

from .benchmarks import (
    BenchmarkManager,
    BenchmarkResult,
    BenchmarkSuite,
    PerformanceBenchmark,
)
from dotmac.platform.settings import settings
from .integrations import (
    IntegrationManager,
    MonitoringIntegration,
    SigNozIntegration,
)

__all__ = [
    # Configuration
    "MonitoringConfig",
    # Integrations
    "MonitoringIntegration",
    "SigNozIntegration",
    "IntegrationManager",
    # Benchmarks
    "BenchmarkManager",
    "PerformanceBenchmark",
    "BenchmarkResult",
    "BenchmarkSuite",
]
