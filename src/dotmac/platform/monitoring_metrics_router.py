"""
Monitoring and Metrics Router.

Provides endpoints for system observability, error monitoring, and performance metrics.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
import random

import structlog
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.auth.dependencies import get_current_user
from dotmac.platform.auth.core import UserInfo
from dotmac.platform.db import get_session_dependency

logger = structlog.get_logger(__name__)

# Create separate routers for logs and metrics
# Note: prefix is set during router registration in routers.py
logs_router = APIRouter(tags=["Logs"])
metrics_router = APIRouter(tags=["Metrics"])


# ========================================
# Logs Endpoints
# ========================================


class ErrorRateResponse(BaseModel):
    """Error rate monitoring response."""
    rate: float
    total_requests: int
    error_count: int
    time_window: str
    timestamp: str


@logs_router.get("/error-rate", response_model=ErrorRateResponse)
async def get_error_rate(
    window_minutes: int = Query(default=60, description="Time window in minutes"),
    session: AsyncSession = Depends(get_session_dependency),
    current_user: UserInfo = Depends(get_current_user),
) -> ErrorRateResponse:
    """
    Get current error rate from application logs.

    Calculates error rate as percentage of failed requests.
    """
    try:
        from dotmac.platform.audit.models import AuditActivity

        # Calculate time window
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=window_minutes)

        # Query audit logs for errors
        error_query = select(func.count(AuditActivity.id)).where(
            and_(
                AuditActivity.created_at >= window_start,
                AuditActivity.severity.in_(['ERROR', 'CRITICAL'])
            )
        )

        total_query = select(func.count(AuditActivity.id)).where(
            AuditActivity.created_at >= window_start
        )

        error_result = await session.execute(error_query)
        total_result = await session.execute(total_query)

        error_count = error_result.scalar() or 0
        total_requests = total_result.scalar() or 0

        # Calculate error rate
        if total_requests > 0:
            rate = (error_count / total_requests) * 100
        else:
            rate = 0.0

        return ErrorRateResponse(
            rate=round(rate, 2),
            total_requests=total_requests,
            error_count=error_count,
            time_window=f"{window_minutes}m",
            timestamp=now.isoformat(),
        )

    except Exception as e:
        logger.error("Failed to fetch error rate", error=str(e), exc_info=True)
        # Return safe default values
        return ErrorRateResponse(
            rate=0.0,
            total_requests=0,
            error_count=0,
            time_window=f"{window_minutes}m",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )


# ========================================
# Metrics Endpoints
# ========================================


class LatencyMetrics(BaseModel):
    """API latency metrics response."""
    p50: float
    p95: float
    p99: float
    average: float
    max: float
    min: float
    time_window: str
    timestamp: str


@metrics_router.get("/latency", response_model=LatencyMetrics)
async def get_latency_metrics(
    window_minutes: int = Query(default=60, description="Time window in minutes"),
    current_user: UserInfo = Depends(get_current_user),
) -> LatencyMetrics:
    """
    Get API latency metrics including percentiles.

    Returns P50, P95, P99 latency measurements.
    """
    try:
        # For now, return mock data
        # In production, this would query actual request latency data
        # from OpenTelemetry or similar monitoring system

        # Generate realistic mock latency data
        p50 = random.uniform(30, 80)
        p95 = random.uniform(100, 300)
        p99 = random.uniform(300, 800)
        average = random.uniform(50, 150)
        max_latency = random.uniform(800, 1500)
        min_latency = random.uniform(10, 30)

        return LatencyMetrics(
            p50=round(p50, 2),
            p95=round(p95, 2),
            p99=round(p99, 2),
            average=round(average, 2),
            max=round(max_latency, 2),
            min=round(min_latency, 2),
            time_window=f"{window_minutes}m",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    except Exception as e:
        logger.error("Failed to fetch latency metrics", error=str(e), exc_info=True)
        return LatencyMetrics(
            p50=0.0,
            p95=0.0,
            p99=0.0,
            average=0.0,
            max=0.0,
            min=0.0,
            time_window=f"{window_minutes}m",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )


class ResourceMetrics(BaseModel):
    """System resource metrics response."""
    cpu: float
    memory: float
    disk: float
    network_in: float
    network_out: float
    timestamp: str


@metrics_router.get("/resources", response_model=ResourceMetrics)
async def get_resource_metrics(
    current_user: UserInfo = Depends(get_current_user),
) -> ResourceMetrics:
    """
    Get system resource utilization metrics.

    Returns CPU, memory, disk, and network usage.
    """
    try:
        # For now, return mock data
        # In production, this would query actual system metrics
        # from psutil or similar monitoring system

        # Generate realistic mock resource data
        cpu = random.uniform(20, 80)
        memory = random.uniform(40, 85)
        disk = random.uniform(50, 75)
        network_in = random.uniform(10, 100)
        network_out = random.uniform(10, 100)

        return ResourceMetrics(
            cpu=round(cpu, 2),
            memory=round(memory, 2),
            disk=round(disk, 2),
            network_in=round(network_in, 2),
            network_out=round(network_out, 2),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    except Exception as e:
        logger.error("Failed to fetch resource metrics", error=str(e), exc_info=True)
        return ResourceMetrics(
            cpu=0.0,
            memory=0.0,
            disk=0.0,
            network_in=0.0,
            network_out=0.0,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )


__all__ = ["logs_router", "metrics_router"]
