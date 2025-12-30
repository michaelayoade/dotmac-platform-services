"""
Monitoring compatibility router.

Exposes frontend-friendly monitoring endpoints expected by the UI under
the /monitoring prefix (e.g. /monitoring/metrics and /monitoring/infrastructure/metrics).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import structlog
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.auth.dependencies import CurrentUser, get_current_user
from dotmac.platform.db import get_session_dependency
from dotmac.platform.infrastructure_health import HealthStatus, check_all_infrastructure_health
from dotmac.platform.monitoring.metrics_router import _get_monitoring_metrics_cached

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/monitoring", tags=["Monitoring - Compatibility"])


def _period_to_days(period: str | None) -> int:
    """Convert a period like 1h/24h/7d into days for metrics helpers."""
    if not period:
        return 1

    cleaned = period.strip().lower()
    if cleaned.endswith("h"):
        try:
            hours = int(cleaned[:-1] or 0)
            return max(1, hours // 24 or 1)
        except Exception:
            return 1

    if cleaned.endswith("d"):
        try:
            return max(1, int(cleaned[:-1] or 0))
        except Exception:
            return 1

    try:
        return max(1, int(cleaned))
    except Exception:
        return 1


async def _build_infrastructure_metrics() -> dict[str, Any]:
    """Build infrastructure metrics from health checks."""
    results = await check_all_infrastructure_health()
    latencies = [r.response_time_ms for r in results if r.response_time_ms is not None]
    latencies_sorted = sorted(latencies)

    avg_latency = sum(latencies_sorted) / len(latencies_sorted) if latencies_sorted else None
    p99_latency = (
        latencies_sorted[max(int(len(latencies_sorted) * 0.99) - 1, 0)]
        if latencies_sorted
        else None
    )

    healthy_count = sum(1 for r in results if r.status == HealthStatus.HEALTHY)
    degraded_count = sum(1 for r in results if r.status == HealthStatus.DEGRADED)
    unhealthy_count = sum(1 for r in results if r.status == HealthStatus.UNHEALTHY)

    overall_status = "healthy"
    if unhealthy_count:
        overall_status = "critical"
    elif degraded_count:
        overall_status = "degraded"

    return {
        "health": {
            "status": overall_status,
            "uptime": None,
            "services": [
                {
                    "name": r.service,
                    "status": r.status.value,
                    "latency": r.response_time_ms,
                    "uptime": None,
                }
                for r in results
            ],
        },
        "performance": {
            "avgLatency": avg_latency,
            "p99Latency": p99_latency,
            "throughput": None,
            "errorRate": None,
            "requestsPerSecond": None,
        },
        "logs": {
            "totalLogs": None,
            "errors": None,
            "warnings": None,
        },
        "uptime": None,
        "services": {
            "total": len(results),
            "healthy": healthy_count,
            "degraded": degraded_count,
            "critical": unhealthy_count,
        },
        "resources": {
            "cpu": None,
            "memory": None,
            "disk": None,
            "network": None,
        },
        "timestamp": datetime.now(UTC),
    }


@router.get("/metrics")
async def get_monitoring_metrics(
    period: str = Query("24h", description="Period for metrics aggregation (1h, 24h, 7d)"),
    session: AsyncSession = Depends(get_session_dependency),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    """Return monitoring metrics with camelCase keys expected by the frontend."""
    tenant_id = getattr(current_user, "tenant_id", None)
    stats_data = await _get_monitoring_metrics_cached(
        period_days=_period_to_days(period),
        tenant_id=tenant_id,
        session=session,
    )

    total_requests = int(stats_data.get("total_requests", 0) or 0)
    failed_requests = int(stats_data.get("failed_requests", 0) or 0)
    uptime_percent = (
        ((total_requests - failed_requests) / total_requests) * 100 if total_requests else 100.0
    )
    error_rate = float(stats_data.get("error_rate", 0.0) or 0.0)

    system_health = "healthy"
    if error_rate >= 5:
        system_health = "critical"
    elif error_rate >= 1:
        system_health = "degraded"

    return {
        "totalRequests": total_requests,
        "errorRate": error_rate,
        "avgResponseTimeMs": float(stats_data.get("avg_response_time_ms", 0.0) or 0.0),
        "p95ResponseTimeMs": float(stats_data.get("p95_response_time_ms", 0.0) or 0.0),
        "activeUsers": int(stats_data.get("user_activities", 0) or 0),
        "systemUptime": uptime_percent,
        "criticalErrors": int(stats_data.get("critical_errors", 0) or 0),
        "warningCount": int(stats_data.get("warning_count", 0) or 0),
        # Optional/legacy fields expected by UI components
        "requestsTimeSeries": [],
        "responseTimeTimeSeries": [],
        "errorRateTimeSeries": [],
        "systemHealth": system_health,
        "uptime": uptime_percent,
        "responseTime": float(stats_data.get("avg_response_time_ms", 0.0) or 0.0),
        "activeConnections": int(stats_data.get("api_requests", 0) or 0),
        "cpuUsage": 0.0,
        "memoryUsage": 0.0,
        "diskUsage": 0.0,
        "recentAlerts": [],
        "timestamp": datetime.now(UTC),
    }


@router.get("/infrastructure/metrics")
async def get_infrastructure_metrics(
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    """Expose infrastructure metrics under /monitoring for frontend dashboards."""
    return await _build_infrastructure_metrics()


__all__ = ["router"]
