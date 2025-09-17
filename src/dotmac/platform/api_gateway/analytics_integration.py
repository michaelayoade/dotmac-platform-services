"""
API Gateway integration with unified analytics system.
"""


from typing import Optional
from datetime import datetime

from ..analytics import get_analytics_service

from dotmac.platform.observability.unified_logging import get_logger
logger = get_logger(__name__)

class APIGatewayAnalyticsAdapter:
    """
    Adapter to integrate API Gateway with the unified analytics system.
    This replaces the old GatewayMetrics class.
    """

    def __init__(self, tenant_id: str, signoz_endpoint: Optional[str] = None):
        """
        Initialize API Gateway analytics adapter.

        Args:
            tenant_id: Tenant identifier
            signoz_endpoint: SigNoz endpoint
        """
        self.tenant_id = tenant_id
        try:
            self.analytics = get_analytics_service(
                tenant_id=tenant_id,
                service_name="api-gateway",
                signoz_endpoint=signoz_endpoint,
            )
            logger.info(f"Analytics adapter initialized for tenant {tenant_id}")
        except Exception as e:
            logger.error(f"Failed to initialize analytics service: {e}")
            raise

    async def record_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time: float,
        service: Optional[str] = None,
        cache_hit: bool = False,
        rate_limited: bool = False,
        request_size: int = 0,
        response_size: int = 0,
        user_id: Optional[str] = None,
        api_version: Optional[str] = None,
        error_message: Optional[str] = None,
        trace_id: Optional[str] = None,
    ):
        """
        Record API request metrics using the new analytics system.

        Args:
            endpoint: API endpoint path
            method: HTTP method
            status_code: Response status code
            response_time: Response time in milliseconds
            service: Backend service name
            cache_hit: Whether response was from cache
            rate_limited: Whether request was rate limited
            request_size: Request payload size
            response_size: Response payload size
            user_id: User identifier
            api_version: API version
            error_message: Error message if any
            trace_id: Distributed trace ID
        """
        logger.debug(f"Recording request: {method} {endpoint} - {status_code}")
        await self.analytics.track_api_request(
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time_ms=response_time,
            request_size=request_size,
            response_size=response_size,
            user_id=user_id,
            api_version=api_version,
            cache_hit=cache_hit,
            rate_limited=rate_limited,
            error_message=error_message,
            trace_id=trace_id,
        )

    async def record_circuit_breaker_state(
        self,
        service_name: str,
        state: str,
        failure_count: int = 0,
        success_count: int = 0,
    ):
        """
        Record circuit breaker state changes.

        Args:
            service_name: Name of the service
            state: Circuit breaker state
            failure_count: Number of failures
            success_count: Number of successes
        """
        logger.info(f"Circuit breaker state change: {service_name} -> {state}")
        await self.analytics.track_circuit_breaker(
            service_name=service_name,
            state=state,
            failure_count=failure_count,
            success_count=success_count,
        )

    async def record_rate_limit(
        self,
        user_id: str,
        endpoint: str,
        limit: int,
        remaining: int,
        reset_time: datetime,
    ):
        """
        Record rate limiting metrics.

        Args:
            user_id: User identifier
            endpoint: API endpoint
            limit: Rate limit maximum
            remaining: Remaining requests
            reset_time: When rate limit resets
        """
        logger.debug(f"Rate limit recorded: {user_id} on {endpoint} ({remaining}/{limit})")
        await self.analytics.track_rate_limit(
            user_id=user_id,
            endpoint=endpoint,
            limit=limit,
            remaining=remaining,
            reset_time=reset_time,
        )

    def create_request_span(
        self,
        endpoint: str,
        method: str,
        **attributes,
    ):
        """
        Create an OpenTelemetry span for request tracing.

        Args:
            endpoint: API endpoint
            method: HTTP method
            **attributes: Additional span attributes

        Returns:
            OpenTelemetry span
        """
        return self.analytics.api_gateway.create_request_span(
            endpoint=endpoint,
            method=method,
            attributes=attributes,
        )

    async def get_metrics_summary(self) -> dict:
        """
        Get aggregated metrics summary.

        Returns:
            Dictionary of aggregated metrics
        """
        return self.analytics.get_aggregated_metrics(
            aggregation_type="avg",
            time_window_seconds=300,  # 5 minutes
        )

    async def close(self):
        """Close analytics connection."""
        await self.analytics.close()

# Global instance management for backward compatibility
_gateway_analytics_instances = {}

def get_gateway_analytics(
    tenant_id: str,
    signoz_endpoint: Optional[str] = None,
) -> APIGatewayAnalyticsAdapter:
    """
    Get or create API Gateway analytics instance.

    Args:
        tenant_id: Tenant identifier
        signoz_endpoint: SigNoz endpoint

    Returns:
        APIGatewayAnalyticsAdapter instance
    """
    if tenant_id not in _gateway_analytics_instances:
        logger.info(f"Creating new analytics adapter for tenant {tenant_id}")
        _gateway_analytics_instances[tenant_id] = APIGatewayAnalyticsAdapter(
            tenant_id=tenant_id,
            signoz_endpoint=signoz_endpoint,
        )
    return _gateway_analytics_instances[tenant_id]
