"""
Observability API router for traces and metrics.

Provides REST endpoints for distributed tracing and metrics collection.
"""

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field, ConfigDict

from dotmac.platform.auth.dependencies import CurrentUser, get_current_user

logger = structlog.get_logger(__name__)


# ============================================================
# Models
# ============================================================


class TraceStatus(str, Enum):
    """Trace status enumeration."""

    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"


class SpanData(BaseModel):
    """Individual span within a trace."""

    model_config = ConfigDict(str_strip_whitespace=True)

    span_id: str = Field(description="Span ID")
    parent_span_id: Optional[str] = Field(None, description="Parent span ID")
    name: str = Field(description="Span operation name")
    service: str = Field(description="Service name")
    duration: int = Field(description="Duration in milliseconds")
    start_time: datetime = Field(description="Span start time")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Span attributes")


class TraceData(BaseModel):
    """Distributed trace information."""

    model_config = ConfigDict(str_strip_whitespace=True)

    trace_id: str = Field(description="Trace ID")
    service: str = Field(description="Root service")
    operation: str = Field(description="Operation name")
    duration: int = Field(description="Total duration in milliseconds")
    status: TraceStatus = Field(description="Trace status")
    timestamp: datetime = Field(description="Trace timestamp")
    spans: int = Field(description="Number of spans")
    span_details: List[SpanData] = Field(
        default_factory=list, description="Detailed span information"
    )


class TracesResponse(BaseModel):
    """Response for trace queries."""

    traces: List[TraceData] = Field(default_factory=list, description="Trace data")
    total: int = Field(description="Total number of traces")
    page: int = Field(description="Current page")
    page_size: int = Field(description="Page size")
    has_more: bool = Field(description="More traces available")


class MetricType(str, Enum):
    """Metric type enumeration."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


class MetricDataPoint(BaseModel):
    """Single metric data point."""

    timestamp: datetime = Field(description="Timestamp")
    value: float = Field(description="Metric value")
    labels: Dict[str, str] = Field(default_factory=dict, description="Metric labels")


class MetricSeries(BaseModel):
    """Time series metric data."""

    name: str = Field(description="Metric name")
    type: MetricType = Field(description="Metric type")
    data_points: List[MetricDataPoint] = Field(default_factory=list, description="Data points")
    unit: str = Field(default="count", description="Metric unit")


class MetricsResponse(BaseModel):
    """Response for metrics queries."""

    metrics: List[MetricSeries] = Field(default_factory=list, description="Metric series")
    time_range: Dict[str, str] = Field(default_factory=dict, description="Time range")


class ServiceDependency(BaseModel):
    """Service dependency information."""

    from_service: str = Field(description="Source service")
    to_service: str = Field(description="Target service")
    request_count: int = Field(description="Number of requests")
    error_rate: float = Field(description="Error rate (0-1)")
    avg_latency: float = Field(description="Average latency in ms")


class ServiceMapResponse(BaseModel):
    """Service dependency map."""

    services: List[str] = Field(default_factory=list, description="All services")
    dependencies: List[ServiceDependency] = Field(
        default_factory=list, description="Service dependencies"
    )
    health_scores: Dict[str, float] = Field(
        default_factory=dict, description="Service health scores (0-100)"
    )


class PerformanceMetrics(BaseModel):
    """Performance percentile metrics."""

    percentile: str = Field(description="Percentile (e.g., P50, P95)")
    value: float = Field(description="Latency value in milliseconds")
    target: float = Field(description="Target SLA value")
    within_sla: bool = Field(description="Whether within SLA target")


class PerformanceResponse(BaseModel):
    """Performance metrics response."""

    percentiles: List[PerformanceMetrics] = Field(
        default_factory=list, description="Percentile data"
    )
    slowest_endpoints: List[Dict[str, Any]] = Field(
        default_factory=list, description="Slowest endpoints"
    )
    most_frequent_errors: List[Dict[str, Any]] = Field(
        default_factory=list, description="Most frequent errors"
    )


# ============================================================
# Router
# ============================================================

traces_router = APIRouter()


# ============================================================
# Service Layer
# ============================================================


class ObservabilityService:
    """Service for observability data.

    Currently returns mock data. In production, this would integrate with:
    - OpenTelemetry Collector
    - Jaeger
    - Tempo
    - Prometheus
    """

    def __init__(self):
        self.logger = structlog.get_logger(__name__)

    async def get_traces(
        self,
        service: Optional[str] = None,
        status: Optional[TraceStatus] = None,
        min_duration: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> TracesResponse:
        """Fetch distributed traces."""
        import random
        from uuid import uuid4

        # Generate mock traces
        statuses = [TraceStatus.SUCCESS, TraceStatus.ERROR, TraceStatus.WARNING]
        services_list = [
            "api-gateway",
            "auth-service",
            "database",
            "payment-service",
            "email-service",
        ]
        operations = [
            "POST /api/users",
            "GET /api/users/{id}",
            "validateToken",
            "SELECT users",
            "processPayment",
            "sendNotification",
        ]

        traces = []
        total_traces = 200

        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size

        for i in range(start_idx, min(end_idx, total_traces)):
            trace_status = status if status else random.choice(statuses)
            trace_service = service if service else random.choice(services_list)
            trace_operation = random.choice(operations)
            trace_duration = random.randint(50, 2000)

            if min_duration and trace_duration < min_duration:
                continue

            trace = TraceData(
                trace_id=f"trace_{uuid4().hex}",
                service=trace_service,
                operation=trace_operation,
                duration=trace_duration,
                status=trace_status,
                timestamp=datetime.now(timezone.utc) - timedelta(minutes=i),
                spans=random.randint(2, 15),
                span_details=[],  # Can be populated on-demand
            )
            traces.append(trace)

        return TracesResponse(
            traces=traces,
            total=total_traces,
            page=page,
            page_size=page_size,
            has_more=end_idx < total_traces,
        )

    async def get_trace_details(self, trace_id: str) -> Optional[TraceData]:
        """Get detailed span information for a trace."""
        import random
        from uuid import uuid4

        # Generate mock trace with detailed spans
        span_count = random.randint(3, 8)
        spans = []

        parent_span_id = None
        for i in range(span_count):
            span_id = uuid4().hex[:16]
            span = SpanData(
                span_id=span_id,
                parent_span_id=parent_span_id if i > 0 else None,
                name=f"operation_{i}",
                service=random.choice(["api-gateway", "auth-service", "database"]),
                duration=random.randint(10, 200),
                start_time=datetime.now(timezone.utc),
                attributes={
                    "http.method": "GET",
                    "http.status_code": 200,
                    "db.query": "SELECT * FROM users" if i % 2 == 0 else None,
                },
            )
            spans.append(span)
            parent_span_id = span_id

        return TraceData(
            trace_id=trace_id,
            service="api-gateway",
            operation="GET /api/users",
            duration=sum(s.duration for s in spans),
            status=TraceStatus.SUCCESS,
            timestamp=datetime.now(timezone.utc),
            spans=len(spans),
            span_details=spans,
        )

    async def get_metrics(
        self,
        metric_names: Optional[List[str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> MetricsResponse:
        """Fetch metrics time series."""
        import random

        if not start_time:
            start_time = datetime.now(timezone.utc) - timedelta(hours=24)
        if not end_time:
            end_time = datetime.now(timezone.utc)

        default_metrics = ["request_count", "error_count", "latency_ms"]
        metrics_to_fetch = metric_names or default_metrics

        metric_series = []
        for metric_name in metrics_to_fetch:
            data_points = []
            current_time = start_time

            while current_time <= end_time:
                data_points.append(
                    MetricDataPoint(
                        timestamp=current_time,
                        value=(
                            random.uniform(100, 1000)
                            if "count" in metric_name
                            else random.uniform(50, 200)
                        ),
                        labels={"service": "api-gateway"},
                    )
                )
                current_time += timedelta(hours=1)

            metric_series.append(
                MetricSeries(
                    name=metric_name,
                    type=MetricType.COUNTER if "count" in metric_name else MetricType.GAUGE,
                    data_points=data_points,
                    unit="count" if "count" in metric_name else "ms",
                )
            )

        return MetricsResponse(
            metrics=metric_series,
            time_range={
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
            },
        )

    async def get_service_map(self) -> ServiceMapResponse:
        """Get service dependency map."""
        import random

        services = [
            "api-gateway",
            "auth-service",
            "user-service",
            "database",
            "cache",
            "payment-service",
        ]

        dependencies = [
            ServiceDependency(
                from_service="api-gateway",
                to_service="auth-service",
                request_count=10000,
                error_rate=0.02,
                avg_latency=45.5,
            ),
            ServiceDependency(
                from_service="api-gateway",
                to_service="user-service",
                request_count=8500,
                error_rate=0.01,
                avg_latency=62.3,
            ),
            ServiceDependency(
                from_service="user-service",
                to_service="database",
                request_count=7200,
                error_rate=0.005,
                avg_latency=25.8,
            ),
            ServiceDependency(
                from_service="auth-service",
                to_service="cache",
                request_count=9800,
                error_rate=0.001,
                avg_latency=8.2,
            ),
        ]

        health_scores = {service: random.uniform(85, 99) for service in services}

        return ServiceMapResponse(
            services=services,
            dependencies=dependencies,
            health_scores=health_scores,
        )

    async def get_performance_metrics(self) -> PerformanceResponse:
        """Get performance percentiles and slow endpoints."""
        percentiles_data = [
            PerformanceMetrics(percentile="P50", value=45.2, target=50.0, within_sla=True),
            PerformanceMetrics(percentile="P75", value=78.5, target=100.0, within_sla=True),
            PerformanceMetrics(percentile="P90", value=145.3, target=200.0, within_sla=True),
            PerformanceMetrics(percentile="P95", value=250.8, target=300.0, within_sla=True),
            PerformanceMetrics(percentile="P99", value=450.2, target=500.0, within_sla=True),
        ]

        slowest_endpoints = [
            {"endpoint": "/api/reports/generate", "avg_latency": 2500, "status_code": 200},
            {"endpoint": "/api/analytics/aggregate", "avg_latency": 1800, "status_code": 200},
            {"endpoint": "/api/search/fulltext", "avg_latency": 1200, "status_code": 200},
        ]

        most_frequent_errors = [
            {"error_type": "Rate Limit Exceeded", "count": 142, "status_code": 429},
            {"error_type": "Invalid Token", "count": 89, "status_code": 401},
            {"error_type": "Resource Not Found", "count": 67, "status_code": 404},
        ]

        return PerformanceResponse(
            percentiles=percentiles_data,
            slowest_endpoints=slowest_endpoints,
            most_frequent_errors=most_frequent_errors,
        )


# Service instance
_observability_service: Optional[ObservabilityService] = None


def get_observability_service() -> ObservabilityService:
    """Get or create observability service instance."""
    global _observability_service
    if _observability_service is None:
        _observability_service = ObservabilityService()
    return _observability_service


# ============================================================
# Endpoints
# ============================================================


@traces_router.get("/traces", response_model=TracesResponse)
async def get_traces(
    service: Optional[str] = Query(None, description="Filter by service name"),
    status: Optional[TraceStatus] = Query(None, description="Filter by trace status"),
    min_duration: Optional[int] = Query(None, description="Minimum duration in milliseconds"),
    start_time: Optional[datetime] = Query(None, description="Start of time range"),
    end_time: Optional[datetime] = Query(None, description="End of time range"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=500, description="Traces per page"),
    current_user: CurrentUser = Depends(get_current_user),
    obs_service: ObservabilityService = Depends(get_observability_service),
) -> TracesResponse:
    """
    Retrieve distributed traces with filtering.

    **Note:** Currently returns mock data. Will integrate with Jaeger/Tempo in production.
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
    current_user: CurrentUser = Depends(get_current_user),
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
    metrics: Optional[str] = Query(None, description="Comma-separated metric names"),
    start_time: Optional[datetime] = Query(None, description="Start time"),
    end_time: Optional[datetime] = Query(None, description="End time"),
    current_user: CurrentUser = Depends(get_current_user),
    obs_service: ObservabilityService = Depends(get_observability_service),
) -> MetricsResponse:
    """
    Retrieve time series metrics.

    **Note:** Currently returns mock data. Will integrate with Prometheus in production.
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
    current_user: CurrentUser = Depends(get_current_user),
    obs_service: ObservabilityService = Depends(get_observability_service),
) -> ServiceMapResponse:
    """Get service dependency map and health scores."""
    logger.info("service_map.query", user_id=current_user.user_id)

    return await obs_service.get_service_map()


@traces_router.get("/performance", response_model=PerformanceResponse)
async def get_performance_metrics(
    current_user: CurrentUser = Depends(get_current_user),
    obs_service: ObservabilityService = Depends(get_observability_service),
) -> PerformanceResponse:
    """Get performance percentiles and slow endpoints."""
    logger.info("performance.query", user_id=current_user.user_id)

    return await obs_service.get_performance_metrics()
