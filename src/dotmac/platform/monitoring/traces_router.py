"""
Observability API router for traces and metrics.

Provides REST endpoints for distributed tracing and metrics collection.
"""

import os
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import TYPE_CHECKING, Any

import structlog
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field

from dotmac.platform.auth.dependencies import CurrentUser, get_current_user
from dotmac.platform.auth.platform_admin import is_platform_admin
from dotmac.platform.auth.rbac_dependencies import require_permission
from dotmac.platform.db import get_async_session
from dotmac.platform.monitoring.prometheus_client import PrometheusQueryError
from dotmac.platform.settings import settings

logger = structlog.get_logger(__name__)

if TYPE_CHECKING:
    from dotmac.platform.monitoring.prometheus_client import PrometheusClient


# ============================================================
# Models
# ============================================================


class TraceStatus(str, Enum):
    """Trace status enumeration."""

    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"


class SpanData(BaseModel):  # BaseModel resolves to Any in isolation
    """Individual span within a trace."""

    model_config = ConfigDict(str_strip_whitespace=True)

    span_id: str = Field(description="Span ID")
    parent_span_id: str | None = Field(None, description="Parent span ID")
    name: str = Field(description="Span operation name")
    service: str = Field(description="Service name")
    duration: int = Field(description="Duration in milliseconds")
    start_time: datetime = Field(description="Span start time")
    attributes: dict[str, Any] = Field(default_factory=dict, description="Span attributes")


class TraceData(BaseModel):  # BaseModel resolves to Any in isolation
    """Distributed trace information."""

    model_config = ConfigDict(str_strip_whitespace=True)

    trace_id: str = Field(description="Trace ID")
    service: str = Field(description="Root service")
    operation: str = Field(description="Operation name")
    duration: int = Field(description="Total duration in milliseconds")
    status: TraceStatus = Field(description="Trace status")
    timestamp: datetime = Field(description="Trace timestamp")
    spans: int = Field(description="Number of spans")
    span_details: list[SpanData] = Field(
        default_factory=list, description="Detailed span information"
    )


class TracesResponse(BaseModel):  # BaseModel resolves to Any in isolation
    """Response for trace queries."""

    model_config = ConfigDict()

    traces: list[TraceData] = Field(default_factory=list, description="Trace data")
    total: int = Field(description="Total number of traces")
    page: int = Field(description="Current page")
    page_size: int = Field(description="Page size")
    has_more: bool = Field(description="More traces available")


class MetricType(str, Enum):
    """Metric type enumeration."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


class MetricDataPoint(BaseModel):  # BaseModel resolves to Any in isolation
    """Single metric data point."""

    model_config = ConfigDict()

    timestamp: datetime = Field(description="Timestamp")
    value: float = Field(description="Metric value")
    labels: dict[str, str] = Field(default_factory=dict, description="Metric labels")


class MetricSeries(BaseModel):  # BaseModel resolves to Any in isolation
    """Time series metric data."""

    model_config = ConfigDict()

    name: str = Field(description="Metric name")
    type: MetricType = Field(description="Metric type")
    data_points: list[MetricDataPoint] = Field(default_factory=list, description="Data points")
    unit: str = Field(default="count", description="Metric unit")


class MetricsResponse(BaseModel):  # BaseModel resolves to Any in isolation
    """Response for metrics queries."""

    model_config = ConfigDict()

    metrics: list[MetricSeries] = Field(default_factory=list, description="Metric series")
    time_range: dict[str, str] = Field(default_factory=dict, description="Time range")


class ServiceDependency(BaseModel):
    """Service dependency information."""

    model_config = ConfigDict()

    from_service: str = Field(description="Source service")
    to_service: str = Field(description="Target service")
    request_count: int = Field(description="Number of requests")
    error_rate: float = Field(description="Error rate (0-1)")
    avg_latency: float = Field(description="Average latency in ms")


class ServiceMapResponse(BaseModel):  # BaseModel resolves to Any in isolation
    """Service dependency map."""

    model_config = ConfigDict()

    services: list[str] = Field(default_factory=list, description="All services")
    dependencies: list[ServiceDependency] = Field(
        default_factory=list, description="Service dependencies"
    )
    health_scores: dict[str, float] = Field(
        default_factory=dict, description="Service health scores (0-100)"
    )


class PerformanceMetrics(BaseModel):  # BaseModel resolves to Any in isolation
    """Performance percentile metrics."""

    model_config = ConfigDict()

    percentile: str = Field(description="Percentile (e.g., P50, P95)")
    value: float = Field(description="Latency value in milliseconds")
    target: float = Field(description="Target SLA value")
    within_sla: bool = Field(description="Whether within SLA target")


class PerformanceResponse(BaseModel):  # BaseModel resolves to Any in isolation
    """Performance metrics response."""

    model_config = ConfigDict()

    percentiles: list[PerformanceMetrics] = Field(
        default_factory=list, description="Percentile data"
    )
    slowest_endpoints: list[dict[str, Any]] = Field(
        default_factory=list, description="Slowest endpoints"
    )
    most_frequent_errors: list[dict[str, Any]] = Field(
        default_factory=list, description="Most frequent errors"
    )


# ============================================================
# Router
# ============================================================

traces_router = APIRouter(
    prefix="/observability",
)


# ============================================================
# Service Layer
# ============================================================


class ObservabilityService:
    """Service for observability data.

    Integrates with:
    - Jaeger API for distributed traces
    - Prometheus for metrics
    - OpenTelemetry Collector
    """

    def __init__(self, jaeger_url: str = "http://localhost:16686") -> None:
        self.logger = structlog.get_logger(__name__).bind(component="observability_service")
        self.jaeger_url = os.getenv("JAEGER_URL", jaeger_url)

    def _get_prometheus_client(self) -> "PrometheusClient | None":
        prometheus_config = settings.integrations.prometheus
        if not prometheus_config.url:
            return None

        from dotmac.platform.monitoring.prometheus_client import PrometheusClient

        return PrometheusClient(
            base_url=prometheus_config.url,
            api_token=prometheus_config.api_token,
            username=prometheus_config.username,
            password=prometheus_config.password,
            verify_ssl=prometheus_config.verify_ssl,
            timeout_seconds=prometheus_config.timeout_seconds,
            max_retries=prometheus_config.max_retries,
        )

    @staticmethod
    def _tags_to_attributes(tags: list[dict[str, Any]] | None) -> dict[str, Any]:
        attributes: dict[str, Any] = {}
        if not tags:
            return attributes
        for tag in tags:
            key = tag.get("key")
            if key is None:
                continue
            attributes[str(key)] = tag.get("value")
        return attributes

    def _parse_jaeger_trace(self, jaeger_trace: dict[str, Any]) -> TraceData | None:
        if not jaeger_trace.get("spans"):
            return None

        root_span = jaeger_trace["spans"][0]
        process = jaeger_trace["processes"].get(root_span["processID"], {})

        span_times = [
            (s["startTime"], s["startTime"] + s["duration"]) for s in jaeger_trace["spans"]
        ]
        trace_start = min(t[0] for t in span_times)
        trace_end = max(t[1] for t in span_times)
        duration_ms = (trace_end - trace_start) // 1000

        trace_status = TraceStatus.SUCCESS
        for span in jaeger_trace["spans"]:
            for tag in span.get("tags", []):
                if tag.get("key") == "error" and tag.get("value"):
                    trace_status = TraceStatus.ERROR
                    break
                if tag.get("key") == "http.status_code" and tag.get("value", 0) >= 400:
                    trace_status = TraceStatus.ERROR
                    break
            if trace_status == TraceStatus.ERROR:
                break

        return TraceData(
            trace_id=jaeger_trace["traceID"],
            service=process.get("serviceName", "unknown"),
            operation=root_span.get("operationName", "unknown"),
            duration=duration_ms,
            status=trace_status,
            timestamp=datetime.fromtimestamp(trace_start / 1_000_000, tz=UTC),
            spans=len(jaeger_trace["spans"]),
            span_details=[],
        )

    async def get_traces(
        self,
        service: str | None = None,
        status: TraceStatus | None = None,
        min_duration: int | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> TracesResponse:
        """Fetch distributed traces from Jaeger."""
        import httpx

        try:
            # Build Jaeger API query parameters
            params: dict[str, str | int] = {
                "limit": page_size,
                "lookback": "1h",  # Default lookback
            }

            if service:
                params["service"] = service
            if min_duration:
                params["minDuration"] = f"{min_duration}us"  # Jaeger uses microseconds

            # Query Jaeger API
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.jaeger_url}/api/traces",
                    params=params,
                    timeout=10.0,
                )
                response.raise_for_status()
                jaeger_data = response.json()

            # Convert Jaeger traces to our format
            traces = []
            for jaeger_trace in jaeger_data.get("data", []):
                trace = self._parse_jaeger_trace(jaeger_trace)
                if trace:
                    traces.append(trace)

            return TracesResponse(
                traces=traces,
                total=len(traces),
                page=page,
                page_size=page_size,
                has_more=False,  # Jaeger doesn't provide total count
            )

        except Exception as e:
            self.logger.error("Failed to fetch traces from Jaeger", error=str(e), exc_info=True)
            # Return empty response on error
            return TracesResponse(
                traces=[],
                total=0,
                page=page,
                page_size=page_size,
                has_more=False,
            )

    async def get_trace_details(self, trace_id: str) -> TraceData | None:
        """Get detailed span information for a trace."""
        import httpx

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.jaeger_url}/api/traces/{trace_id}")
                response.raise_for_status()
                jaeger_data = response.json()

            trace_payloads = jaeger_data.get("data", [])
            if not trace_payloads:
                return None

            jaeger_trace = trace_payloads[0]
            trace = self._parse_jaeger_trace(jaeger_trace)
            if not trace:
                return None

            span_details: list[SpanData] = []
            for span in jaeger_trace.get("spans", []):
                process = jaeger_trace["processes"].get(span.get("processID"), {})
                span_details.append(
                    SpanData(
                        span_id=span.get("spanID", ""),
                        parent_span_id=span.get("parentSpanID") or None,
                        name=span.get("operationName", "unknown"),
                        service=process.get("serviceName", "unknown"),
                        duration=int(span.get("duration", 0) / 1000),
                        start_time=datetime.fromtimestamp(span.get("startTime", 0) / 1_000_000, tz=UTC),
                        attributes=self._tags_to_attributes(span.get("tags")),
                    )
                )

            return trace.model_copy(update={"span_details": span_details})
        except Exception as e:
            self.logger.error(
                "Failed to fetch trace details from Jaeger", trace_id=trace_id, error=str(e)
            )
            return None

    async def get_metrics(
        self,
        metric_names: list[str] | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> MetricsResponse:
        """Fetch metrics time series."""
        if not start_time:
            start_time = datetime.now(UTC) - timedelta(hours=24)
        if not end_time:
            end_time = datetime.now(UTC)

        default_metrics = ["request_count", "error_count", "latency_ms"]
        metrics_to_fetch = metric_names or default_metrics

        metric_series: list[MetricSeries] = []
        client = self._get_prometheus_client()
        if not client:
            return MetricsResponse(
                metrics=[],
                time_range={
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat(),
                },
            )

        range_seconds = max(0, int((end_time - start_time).total_seconds()))
        step_seconds = max(60, int(range_seconds / 120) if range_seconds else 60)

        for metric_name in metrics_to_fetch:
            try:
                payload = await client.request(
                    "GET",
                    "api/v1/query_range",
                    params={
                        "query": metric_name,
                        "start": start_time.timestamp(),
                        "end": end_time.timestamp(),
                        "step": step_seconds,
                    },
                )
                result_data = payload.get("data", {}).get("result", [])
                if not result_data:
                    metric_series.append(
                        MetricSeries(
                            name=metric_name,
                            type=MetricType.COUNTER if "count" in metric_name else MetricType.GAUGE,
                            data_points=[],
                            unit="count" if "count" in metric_name else "ms",
                        )
                    )
                    continue

                for series in result_data:
                    labels = series.get("metric", {})
                    data_points = [
                        MetricDataPoint(
                            timestamp=datetime.fromtimestamp(float(ts), tz=UTC),
                            value=float(value),
                            labels=labels,
                        )
                        for ts, value in series.get("values", [])
                    ]
                    metric_series.append(
                        MetricSeries(
                            name=metric_name,
                            type=MetricType.COUNTER if "count" in metric_name else MetricType.GAUGE,
                            data_points=data_points,
                            unit="count" if "count" in metric_name else "ms",
                        )
                    )
            except (PrometheusQueryError, Exception) as e:
                self.logger.error("Failed to query Prometheus", metric=metric_name, error=str(e))

        return MetricsResponse(
            metrics=metric_series,
            time_range={
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
            },
        )

    async def get_service_map(self) -> ServiceMapResponse:
        """Get service dependency map."""
        import httpx

        end_ts = int(datetime.now(UTC).timestamp() * 1000)
        lookback_ms = int(os.getenv("OBSERVABILITY_DEPENDENCY_LOOKBACK_MS", "3600000"))

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.jaeger_url}/api/dependencies",
                    params={
                        "endTs": end_ts,
                        "lookback": lookback_ms,
                    },
                    timeout=10.0,
                )
                response.raise_for_status()
                payload = response.json()

            dependencies_data = payload.get("data", [])
            services: set[str] = set()
            dependencies: list[ServiceDependency] = []
            error_rates: dict[str, list[float]] = {}

            for item in dependencies_data:
                parent = item.get("parent")
                child = item.get("child")
                if not parent or not child:
                    continue

                call_count = int(item.get("callCount") or 0)
                error_count = int(item.get("errorCount") or 0)
                error_rate = (error_count / call_count) if call_count else 0.0

                services.update([parent, child])
                error_rates.setdefault(parent, []).append(error_rate)
                error_rates.setdefault(child, []).append(error_rate)

                dependencies.append(
                    ServiceDependency(
                        from_service=parent,
                        to_service=child,
                        request_count=call_count,
                        error_rate=error_rate,
                        avg_latency=float(item.get("avgDuration", 0.0) or 0.0),
                    )
                )

            health_scores = {
                service: max(0.0, 100.0 - (sum(rates) / len(rates)) * 100)
                for service, rates in error_rates.items()
            }

            return ServiceMapResponse(
                services=sorted(services),
                dependencies=dependencies,
                health_scores=health_scores,
            )
        except Exception as e:
            self.logger.error("Failed to fetch service map from Jaeger", error=str(e))
            return ServiceMapResponse(
                services=[],
                dependencies=[],
                health_scores={},
            )

    async def get_performance_metrics(self) -> PerformanceResponse:
        """Get performance percentiles and slow endpoints."""
        client = self._get_prometheus_client()
        if not client:
            return PerformanceResponse(
                percentiles=[],
                slowest_endpoints=[],
                most_frequent_errors=[],
            )

        histogram_metric = os.getenv(
            "OBSERVABILITY_LATENCY_HISTOGRAM", "http_request_duration_seconds_bucket"
        )
        request_metric = os.getenv("OBSERVABILITY_REQUEST_COUNT", "http_requests_total")
        route_label = os.getenv("OBSERVABILITY_ROUTE_LABEL", "path")
        status_label = os.getenv("OBSERVABILITY_STATUS_LABEL", "status")
        window = os.getenv("OBSERVABILITY_LATENCY_WINDOW", "5m")

        percentiles: list[PerformanceMetrics] = []
        for percentile in (0.5, 0.75, 0.9, 0.95, 0.99):
            query = (
                f"histogram_quantile({percentile}, "
                f"sum(rate({histogram_metric}[{window}])) by (le))"
            )
            try:
                payload = await client.query(query)
                result = payload.get("data", {}).get("result", [])
                value = float(result[0]["value"][1]) * 1000 if result else 0.0
            except (PrometheusQueryError, Exception) as e:
                self.logger.error("Prometheus percentile query failed", error=str(e))
                value = 0.0

            percentiles.append(
                PerformanceMetrics(
                    percentile=f"P{int(percentile * 100)}",
                    value=value,
                    target=0.0,
                    within_sla=False,
                )
            )

        slow_query = os.getenv(
            "OBSERVABILITY_SLOW_QUERY",
            (
                "topk(5, histogram_quantile(0.95, "
                f"sum(rate({histogram_metric}[{window}])) by (le, {route_label})))"
            ),
        )
        slowest_endpoints: list[dict[str, Any]] = []
        try:
            slow_payload = await client.query(slow_query)
            slow_result = slow_payload.get("data", {}).get("result", [])
            for row in slow_result:
                labels = row.get("metric", {})
                route = labels.get(route_label) or labels.get("route") or labels.get("handler")
                value = float(row.get("value", [0, 0])[1]) * 1000
                slowest_endpoints.append(
                    {
                        "endpoint": route or "unknown",
                        "avg_latency": value,
                        "status_code": labels.get(status_label),
                    }
                )
        except (PrometheusQueryError, Exception) as e:
            self.logger.error("Prometheus slow endpoints query failed", error=str(e))

        error_query = os.getenv(
            "OBSERVABILITY_ERROR_QUERY",
            (
                "topk(5, sum(rate("
                f"{request_metric}{{{status_label}=~\"5..\"}}[{window}]))"
                f" by ({status_label}, {route_label}))"
            ),
        )
        most_frequent_errors: list[dict[str, Any]] = []
        try:
            error_payload = await client.query(error_query)
            error_result = error_payload.get("data", {}).get("result", [])
            for row in error_result:
                labels = row.get("metric", {})
                status_code = labels.get(status_label)
                route = labels.get(route_label) or labels.get("route") or labels.get("handler")
                count = float(row.get("value", [0, 0])[1])
                most_frequent_errors.append(
                    {
                        "error_type": route or "unknown",
                        "count": int(count),
                        "status_code": status_code,
                    }
                )
        except (PrometheusQueryError, Exception) as e:
            self.logger.error("Prometheus error query failed", error=str(e))

        return PerformanceResponse(
            percentiles=percentiles,
            slowest_endpoints=slowest_endpoints,
            most_frequent_errors=most_frequent_errors,
        )


# Service instance
_observability_service: ObservabilityService | None = None


def get_observability_service() -> ObservabilityService:
    """Get or create observability service instance."""
    global _observability_service
    if _observability_service is None:
        _observability_service = ObservabilityService()
    return _observability_service


async def require_observability_access(
    current_user: CurrentUser = Depends(get_current_user),
    db: Any = Depends(get_async_session),
) -> CurrentUser:
    """Require observability permission or platform admin access."""
    if is_platform_admin(current_user):
        return current_user
    checker = require_permission("monitoring.observability.read")
    return await checker(current_user=current_user, db=db)


# ============================================================
# Endpoints
# ============================================================


@traces_router.get("/traces", response_model=TracesResponse)
async def get_traces(
    service: str | None = Query(None, description="Filter by service name"),
    status: TraceStatus | None = Query(None, description="Filter by trace status"),
    min_duration: int | None = Query(None, description="Minimum duration in milliseconds"),
    start_time: datetime | None = Query(None, description="Start of time range"),
    end_time: datetime | None = Query(None, description="End of time range"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=500, description="Traces per page"),
    current_user: CurrentUser = Depends(require_observability_access),
    obs_service: ObservabilityService = Depends(get_observability_service),
) -> TracesResponse:
    """
    Retrieve distributed traces with filtering.
    """
    logger.info(
        "traces.query",
        user_id=current_user.user_id,
        service=service,
        status=status,
        page=page,
    )

    return await obs_service.get_traces(
        service=service,
        status=status,
        min_duration=min_duration,
        start_time=start_time,
        end_time=end_time,
        page=page,
        page_size=page_size,
    )


@traces_router.get("/traces/{trace_id}", response_model=TraceData)
async def get_trace_details(
    trace_id: str,
    current_user: CurrentUser = Depends(require_observability_access),
    obs_service: ObservabilityService = Depends(get_observability_service),
) -> TraceData:
    """Get detailed span information for a specific trace."""
    logger.info("trace.details", user_id=current_user.user_id, trace_id=trace_id)

    trace = await obs_service.get_trace_details(trace_id)
    if not trace:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Trace not found")

    return trace


@traces_router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    metrics: str | None = Query(None, description="Comma-separated metric names"),
    start_time: datetime | None = Query(None, description="Start time"),
    end_time: datetime | None = Query(None, description="End time"),
    current_user: CurrentUser = Depends(require_observability_access),
    obs_service: ObservabilityService = Depends(get_observability_service),
) -> MetricsResponse:
    """
    Retrieve time series metrics.
    """
    metric_list = metrics.split(",") if metrics else None

    logger.info(
        "metrics.query",
        user_id=current_user.user_id,
        metrics=metric_list,
        start_time=start_time,
        end_time=end_time,
    )

    return await obs_service.get_metrics(
        metric_names=metric_list,
        start_time=start_time,
        end_time=end_time,
    )


@traces_router.get("/service-map", response_model=ServiceMapResponse)
async def get_service_map(
    current_user: CurrentUser = Depends(require_observability_access),
    obs_service: ObservabilityService = Depends(get_observability_service),
) -> ServiceMapResponse:
    """Get service dependency map and health scores."""
    logger.info("service_map.query", user_id=current_user.user_id)

    return await obs_service.get_service_map()


@traces_router.get("/performance", response_model=PerformanceResponse)
async def get_performance_metrics(
    current_user: CurrentUser = Depends(require_observability_access),
    obs_service: ObservabilityService = Depends(get_observability_service),
) -> PerformanceResponse:
    """Get performance percentiles and slow endpoints."""
    logger.info("performance.query", user_id=current_user.user_id)

    return await obs_service.get_performance_metrics()
