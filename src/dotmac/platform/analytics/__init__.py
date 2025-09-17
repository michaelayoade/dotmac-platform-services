"""
Unified Analytics Core Infrastructure with OpenTelemetry.

This module provides the foundational components for centralized analytics
collection, processing, and export to SigNoz via OpenTelemetry.
"""

from .base import (
    AnalyticsCollector,
    MetricType,
    Metric,
    CounterMetric,
    GaugeMetric,
    HistogramMetric,
    SpanContext,
)
from .otel_collector import (
    OpenTelemetryCollector,
    OTelConfig,
    create_otel_collector,
)
from .aggregators import (
    MetricAggregator,
    TimeWindowAggregator,
    StatisticalAggregator,
)
from .service import get_analytics_service, AnalyticsService

__all__ = [
    # Base classes
    "AnalyticsCollector",
    "MetricType",
    "Metric",
    "CounterMetric",
    "GaugeMetric",
    "HistogramMetric",
    "SpanContext",
    # OpenTelemetry
    "OpenTelemetryCollector",
    "OTelConfig",
    "create_otel_collector",
    # Aggregators
    "MetricAggregator",
    "TimeWindowAggregator",
    "StatisticalAggregator",
    # Service
    "get_analytics_service",
    "AnalyticsService",
]
