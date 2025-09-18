"""
Analytics service factory and management.
"""


from typing import Optional, Dict, Any
from .otel_collector import OpenTelemetryCollector, OTelConfig, create_otel_collector

from dotmac.platform.observability.unified_logging import get_logger
logger = get_logger(__name__)

_analytics_instances: Dict[str, OpenTelemetryCollector] = {}

class AnalyticsService:
    """Unified analytics service wrapper."""

    def __init__(self, collector: OpenTelemetryCollector):
        self.collector = collector
        self.api_gateway = APIGatewayMetrics(collector)

    async def track_api_request(self, **kwargs):
        """Track API request metrics."""
        await self.collector.record_metric(
            name="api_request", value=1, metric_type="counter", labels=kwargs
        )

    async def track_circuit_breaker(self, **kwargs):
        """Track circuit breaker state."""
        await self.collector.record_metric(
            name="circuit_breaker_state", value=1, metric_type="gauge", labels=kwargs
        )

    async def track_rate_limit(self, **kwargs):
        """Track rate limit metrics."""
        await self.collector.record_metric(
            name="rate_limit", value=kwargs.get("remaining", 0), metric_type="gauge", labels=kwargs
        )

    def get_aggregated_metrics(self, aggregation_type: str, time_window_seconds: int):
        """Get aggregated metrics."""
        return self.collector.get_metrics_summary()

    async def close(self):
        """Close the analytics service."""
        await self.collector.flush()

class APIGatewayMetrics:
    """API Gateway specific metrics handling."""

    def __init__(self, collector: OpenTelemetryCollector):
        self.collector = collector

    def create_request_span(self, endpoint: str, method: str, attributes: Dict[str, Any]):
        """Create a request span for tracing."""
        return self.collector.tracer.start_span(name=f"{method} {endpoint}", attributes=attributes)

def get_analytics_service(
    tenant_id: str, service_name: str = "platform", signoz_endpoint: Optional[str] = None, **kwargs
) -> AnalyticsService:
    """
    Get or create an analytics service instance.

    Args:
        tenant_id: Tenant identifier
        service_name: Service name for telemetry
        signoz_endpoint: Optional SigNoz endpoint

    Returns:
        AnalyticsService instance
    """
    cache_key = f"{tenant_id}:{service_name}"

    if cache_key not in _analytics_instances:
        endpoint = signoz_endpoint or kwargs.get("otlp_endpoint")
        # Fall back to the standard OTLP gRPC endpoint if nothing is supplied
        endpoint = endpoint or "http://localhost:4317"

        config = OTelConfig(
            service_name=f"{service_name}-{tenant_id}",
            endpoint=endpoint,
        )

        collector = OpenTelemetryCollector(
            tenant_id=tenant_id,
            service_name=config.service_name,
            config=config,
        )
        _analytics_instances[cache_key] = collector
        logger.info(f"Created analytics service for {cache_key}")

    return AnalyticsService(_analytics_instances[cache_key])
