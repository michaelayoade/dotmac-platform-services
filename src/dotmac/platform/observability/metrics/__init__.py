"""Metrics collection and registry for DotMac observability."""

from .business import (
    BusinessMetricSpec,
    BusinessMetricType,
    SLOEvaluation,
    TenantContext,
    TenantMetrics,
    initialize_tenant_metrics,
)
from .registry import (
    MetricDefinition,
    MetricsRegistry,
    MetricType,
    initialize_metrics_registry,
)

__all__ = [
    "BusinessMetricSpec",
    "BusinessMetricType",
    "MetricDefinition",
    "MetricType",
    "MetricsRegistry",
    "SLOEvaluation",
    "TenantContext",
    "TenantMetrics",
    "initialize_metrics_registry",
    "initialize_tenant_metrics",
]
