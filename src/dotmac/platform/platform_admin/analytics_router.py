"""
Platform Admin - Cross-Tenant Analytics Router

Provides cross-tenant access to analytics data for platform administrators.
All endpoints require platform.admin permission.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, cast

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.auth.core import UserInfo
from dotmac.platform.auth.rbac_dependencies import require_permission
from dotmac.platform.database import get_async_session

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/analytics", tags=["Platform Admin - Analytics"])


# ============================================================================
# Response Models
# ============================================================================


class TenantMetric(BaseModel):
    """Metric data for a single tenant"""

    model_config = ConfigDict()

    tenant_id: str
    tenant_name: str | None = None
    value: float
    timestamp: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CrossTenantMetricResponse(BaseModel):
    """Cross-tenant metric aggregation"""

    model_config = ConfigDict()

    metric_name: str
    total_value: float
    tenant_count: int
    by_tenant: list[TenantMetric]
    aggregation_time: datetime


class PlatformAnalyticsSummary(BaseModel):
    """Platform-wide analytics summary"""

    model_config = ConfigDict()

    total_tenants: int
    active_tenants: int  # Tenants with activity in last 30 days
    total_users: int
    total_events: int
    metrics: dict[str, Any]
    period_start: datetime
    period_end: datetime


class TenantActivitySummary(BaseModel):
    """Tenant activity summary"""

    model_config = ConfigDict()

    tenant_id: str
    tenant_name: str | None = None
    user_count: int
    event_count: int
    last_activity: datetime | None = None
    status: str  # active, inactive, new


# ============================================================================
# Platform Admin Analytics Endpoints
# ============================================================================


@router.get(
    "/summary",
    response_model=PlatformAnalyticsSummary,
    summary="Get platform-wide analytics summary",
    description="Get analytics metrics across all tenants (platform admin only)",
)
async def get_platform_analytics_summary(
    period_days: int = Query(30, ge=1, le=365, description="Analysis period in days"),
    session: AsyncSession = Depends(get_async_session),
    _current_user: UserInfo = Depends(require_permission("platform.admin")),
) -> PlatformAnalyticsSummary:
    """
    Get platform-wide analytics summary with cross-tenant metrics.

    **Required Permission:** platform.admin

    **Returns:**
    - Total and active tenants
    - User and event counts
    - Activity metrics by tenant
    """
    try:
        from dotmac.platform.audit.models import AuditActivity
        from dotmac.platform.user_management.models import User
        from dotmac.platform.tenant.models import Tenant

        period_start = datetime.now(timezone.utc) - timedelta(days=period_days)
        period_end = datetime.now(timezone.utc)

        # Count total tenants
        tenant_count_query = select(func.count(Tenant.id))
        tenant_count_result = await session.execute(tenant_count_query)
        total_tenants = tenant_count_result.scalar_one() or 0

        # Count active tenants (with recent user activity)
        active_tenant_query = select(func.count(func.distinct(User.tenant_id))).where(
            User.last_login >= period_start
        )
        active_tenant_result = await session.execute(active_tenant_query)
        active_tenants = active_tenant_result.scalar_one() or 0

        # Total users
        user_count_query = select(func.count(User.id))
        user_count_result = await session.execute(user_count_query)
        total_users = user_count_result.scalar_one() or 0

        # Query audit activity as proxy for analytics events
        event_count_query = select(func.count(AuditActivity.id)).where(
            AuditActivity.timestamp >= period_start
        )
        event_count_result = await session.execute(event_count_query)
        total_events = event_count_result.scalar_one() or 0

        metrics = {
            "average_users_per_tenant": round(total_users / total_tenants, 2)
            if total_tenants > 0
            else 0,
            "active_tenant_percentage": round((active_tenants / total_tenants) * 100, 2)
            if total_tenants > 0
            else 0,
        }

        return PlatformAnalyticsSummary(
            total_tenants=total_tenants,
            active_tenants=active_tenants,
            total_users=total_users,
            total_events=total_events,
            metrics=metrics,
            period_start=period_start,
            period_end=period_end,
        )

    except Exception as e:
        logger.error("Failed to generate platform analytics summary", error=str(e))
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate summary: {str(e)}",
        )


@router.get(
    "/tenants/activity",
    response_model=list[TenantActivitySummary],
    summary="Get tenant activity summary",
    description="Get activity metrics for all tenants (platform admin only)",
)
async def get_tenant_activity_summary(
    period_days: int = Query(30, ge=1, le=365),
    min_activity: int = Query(0, ge=0, description="Minimum event count to include"),
    session: AsyncSession = Depends(get_async_session),
    _current_user: UserInfo = Depends(require_permission("platform.admin")),
) -> list[TenantActivitySummary]:
    """
    Get activity summary for all tenants.

    **Required Permission:** platform.admin

    **Returns:** List of tenant activity summaries sorted by event count
    """
    try:
        from dotmac.platform.audit.models import AuditActivity
        from dotmac.platform.auth.models import User
        from dotmac.platform.tenant.models import Tenant

        period_start = datetime.now(timezone.utc) - timedelta(days=period_days)

        # Get tenants with user counts and last activity
        tenant_query = (
            select(
                Tenant.id,
                Tenant.name,
                func.count(User.id).label("user_count"),
                func.max(User.last_login).label("last_activity"),
            )
            .outerjoin(User, Tenant.id == User.tenant_id)
            .group_by(Tenant.id, Tenant.name)
        )

        tenant_result = await session.execute(tenant_query)
        tenant_rows = tenant_result.all()

        # Get event counts per tenant from audit activity
        event_query = (
            select(
                AuditActivity.tenant_id,
                func.count(AuditActivity.id).label("event_count"),
            )
            .where(AuditActivity.timestamp >= period_start)
            .group_by(AuditActivity.tenant_id)
        )
        event_result = await session.execute(event_query)
        event_counts = {str(row.tenant_id): row.event_count for row in event_result.all()}

        summaries = []
        for row in tenant_rows:
            # Determine status
            status = "inactive"
            if row.last_activity:
                if row.last_activity >= period_start:
                    status = "active"
                elif row.last_activity >= datetime.now(timezone.utc) - timedelta(days=7):
                    status = "new"

            # Get event count from audit activity
            event_count = event_counts.get(str(row.id), 0)

            if event_count >= min_activity:
                summaries.append(
                    TenantActivitySummary(
                        tenant_id=row.id,
                        tenant_name=row.name,
                        user_count=row.user_count or 0,
                        event_count=event_count,
                        last_activity=row.last_activity,
                        status=status,
                    )
                )

        # Sort by event count descending
        summaries.sort(key=lambda x: x.event_count, reverse=True)

        return summaries

    except Exception as e:
        logger.error("Failed to get tenant activity summary", error=str(e))
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve activity summary: {str(e)}",
        )


@router.get(
    "/metrics/aggregate",
    response_model=CrossTenantMetricResponse,
    summary="Aggregate metric across tenants",
    description="Aggregate a specific metric across all tenants (platform admin only)",
)
async def aggregate_metric_across_tenants(
    metric_name: str = Query(..., description="Metric name to aggregate"),
    tenant_id: str | None = Query(None, description="Optional tenant filter"),
    period_start: datetime | None = Query(None, description="Period start"),
    period_end: datetime | None = Query(None, description="Period end"),
    session: AsyncSession = Depends(get_async_session),
    _current_user: UserInfo = Depends(require_permission("platform.admin")),
) -> CrossTenantMetricResponse:
    """
    Aggregate a specific metric across all tenants.

    **Required Permission:** platform.admin

    **Supported Metrics:**
    - user_count: Total users per tenant
    - login_count: Total logins per tenant
    - revenue: Total revenue per tenant (requires billing data)

    **Returns:** Aggregated metric with per-tenant breakdown
    """
    try:
        if metric_name == "user_count":
            from dotmac.platform.auth.models import User
            from dotmac.platform.tenant.models import Tenant

            # Get user counts by tenant
            query = select(
                User.tenant_id,
                func.count(User.id).label("count"),
            ).group_by(User.tenant_id)

            if tenant_id:
                query = query.where(User.tenant_id == tenant_id)

            result = await session.execute(query)
            rows = result.all()

            # Fetch tenant names
            tenant_ids = [row.tenant_id for row in rows if row.tenant_id]
            tenant_names: dict[str, str] = {}
            if tenant_ids:
                tenant_query = select(Tenant.id, Tenant.name).where(Tenant.id.in_(tenant_ids))
                tenant_result = await session.execute(tenant_query)
                tenant_names = {str(row.id): row.name for row in tenant_result.all()}

            by_tenant = [
                TenantMetric(
                    tenant_id=row.tenant_id,
                    tenant_name=tenant_names.get(row.tenant_id) if row.tenant_id else None,
                    value=cast(float, row.count),
                    timestamp=datetime.now(timezone.utc),
                )
                for row in rows
            ]

            total_value = sum(metric.value for metric in by_tenant)

            return CrossTenantMetricResponse(
                metric_name=metric_name,
                total_value=total_value,
                tenant_count=len(by_tenant),
                by_tenant=by_tenant,
                aggregation_time=datetime.now(timezone.utc),
            )

        if metric_name == "login_count":
            from dotmac.platform.audit.models import ActivityType, AuditActivity
            from dotmac.platform.tenant.models import Tenant

            filters = [
                AuditActivity.activity_type == ActivityType.USER_LOGIN.value,
                AuditActivity.action.in_(["login_success", "login"]),
            ]

            if tenant_id:
                filters.append(AuditActivity.tenant_id == tenant_id)
            if period_start:
                filters.append(AuditActivity.timestamp >= period_start)
            if period_end:
                filters.append(AuditActivity.timestamp <= period_end)

            query = (
                select(
                    AuditActivity.tenant_id,
                    func.count(AuditActivity.id).label("count"),
                )
                .where(*filters)
                .group_by(AuditActivity.tenant_id)
            )

            result = await session.execute(query)
            rows = result.all()

            tenant_ids = [row.tenant_id for row in rows if row.tenant_id]
            tenant_names: dict[str, str] = {}
            if tenant_ids:
                tenant_query = select(Tenant.id, Tenant.name).where(Tenant.id.in_(tenant_ids))
                tenant_result = await session.execute(tenant_query)
                tenant_names = {str(row.id): row.name for row in tenant_result.all()}

            by_tenant = [
                TenantMetric(
                    tenant_id=row.tenant_id,
                    tenant_name=tenant_names.get(row.tenant_id) if row.tenant_id else None,
                    value=cast(float, row.count),
                    timestamp=datetime.now(timezone.utc),
                )
                for row in rows
            ]

            total_value = sum(metric.value for metric in by_tenant)

            return CrossTenantMetricResponse(
                metric_name=metric_name,
                total_value=total_value,
                tenant_count=len(by_tenant),
                by_tenant=by_tenant,
                aggregation_time=datetime.now(timezone.utc),
            )

        if metric_name == "revenue":
            from dotmac.platform.billing.core.entities import InvoiceEntity
            from dotmac.platform.tenant.models import Tenant

            revenue_expr = InvoiceEntity.total_amount - InvoiceEntity.remaining_balance
            filters = [InvoiceEntity.tenant_id.is_not(None)]

            if tenant_id:
                filters.append(InvoiceEntity.tenant_id == tenant_id)
            if period_start:
                filters.append(InvoiceEntity.paid_at >= period_start)
            if period_end:
                filters.append(InvoiceEntity.paid_at <= period_end)

            query = (
                select(
                    InvoiceEntity.tenant_id,
                    func.sum(revenue_expr).label("total"),
                )
                .where(*filters)
                .group_by(InvoiceEntity.tenant_id)
            )

            result = await session.execute(query)
            rows = result.all()

            tenant_ids = [row.tenant_id for row in rows if row.tenant_id]
            tenant_names: dict[str, str] = {}
            if tenant_ids:
                tenant_query = select(Tenant.id, Tenant.name).where(Tenant.id.in_(tenant_ids))
                tenant_result = await session.execute(tenant_query)
                tenant_names = {str(row.id): row.name for row in tenant_result.all()}

            by_tenant = [
                TenantMetric(
                    tenant_id=row.tenant_id,
                    tenant_name=tenant_names.get(row.tenant_id) if row.tenant_id else None,
                    value=float(row.total or 0),
                    timestamp=datetime.now(timezone.utc),
                )
                for row in rows
            ]

            total_value = sum(metric.value for metric in by_tenant)

            return CrossTenantMetricResponse(
                metric_name=metric_name,
                total_value=total_value,
                tenant_count=len(by_tenant),
                by_tenant=by_tenant,
                aggregation_time=datetime.now(timezone.utc),
            )

        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Unsupported metric. Supported: user_count, login_count, revenue",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to aggregate metric", metric=metric_name, error=str(e))
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to aggregate metric: {str(e)}",
        )


__all__ = ["router"]
