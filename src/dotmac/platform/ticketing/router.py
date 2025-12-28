"""
Ticketing API endpoints.

Enables structured support ticket workflows across customers, tenant teams,
partners, and platform administrators.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from typing import Any, NoReturn
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.auth.core import UserInfo, get_current_user
from dotmac.platform.database import get_session
from dotmac.platform.tenant import get_current_tenant_id

from .assignment_service import TicketAssignmentService
from .dependencies import get_ticket_service
from .models import TicketStatus
from .schemas import (
    AgentPerformanceMetrics,
    TicketCountStats,
    TicketCreate,
    TicketDetail,
    TicketMessageCreate,
    TicketMessageResponse,
    TicketPriority,
    TicketStats,
    TicketSummary,
    TicketUpdate,
)
from .service import (
    TicketAccessDeniedError,
    TicketNotFoundError,
    TicketService,
    TicketValidationError,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/tickets", tags=["Ticketing"])


def _handle_ticket_error(exc: Exception) -> NoReturn:
    """Transform service exceptions into HTTP errors."""
    if isinstance(exc, TicketValidationError):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if isinstance(exc, TicketAccessDeniedError):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    if isinstance(exc, TicketNotFoundError):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    raise HTTPException(
        status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ticketing operation failed"
    ) from exc


@router.post(
    "/",
    response_model=TicketDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create a support ticket",
)
async def create_ticket(
    payload: TicketCreate,
    service: TicketService = Depends(get_ticket_service),
    current_user: UserInfo = Depends(get_current_user),
) -> TicketDetail:
    """Create a new ticket and persist the initial message."""
    tenant_id = get_current_tenant_id()
    try:
        ticket = await service.create_ticket(payload, current_user, tenant_id)
        return TicketDetail.model_validate(ticket, from_attributes=True)
    except Exception as exc:  # pragma: no cover - mapped below
        logger.warning("ticket.create.failed", error=str(exc))
        _handle_ticket_error(exc)


@router.get(
    "/",
    response_model=list[TicketSummary],
    summary="List tickets visible to the current actor",
)
async def list_tickets(
    status_filter: TicketStatus | None = Query(
        None,
        alias="status",
        description="Optional status filter (open, in_progress, waiting, resolved, closed).",
    ),
    priority: str | None = Query(
        None,
        description="Optional priority filter (low, normal, high, urgent). 'medium' is accepted as 'normal'.",
    ),
    search: str | None = Query(
        None,
        min_length=2,
        description="Search across ticket number or subject (case-insensitive).",
    ),
    service: TicketService = Depends(get_ticket_service),
    current_user: UserInfo = Depends(get_current_user),
) -> Sequence[TicketSummary]:
    """List tickets scoped to the current actor."""
    tenant_id = get_current_tenant_id()

    priority_filter: TicketPriority | None = None
    if priority:
        try:
            priority_filter = TicketPriority(priority)
        except ValueError:
            if priority.lower() == "medium":
                priority_filter = TicketPriority.NORMAL
            else:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    detail="Invalid priority value. Expected one of: low, normal, high, urgent.",
                )

    search_value = search.strip() if search else None
    try:
        tickets = await service.list_tickets(
            current_user=current_user,
            tenant_id=tenant_id,
            status=status_filter,
            priority=priority_filter,
            search=search_value,
            include_messages=False,
        )
        return [TicketSummary.model_validate(ticket, from_attributes=True) for ticket in tickets]
    except Exception as exc:  # pragma: no cover
        logger.warning("ticket.list.failed", error=str(exc))
        _handle_ticket_error(exc)


@router.post(
    "/{ticket_id}/messages",
    response_model=TicketDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Append a message to a ticket",
)
async def add_ticket_message(
    ticket_id: UUID,
    payload: TicketMessageCreate,
    service: TicketService = Depends(get_ticket_service),
    current_user: UserInfo = Depends(get_current_user),
) -> TicketDetail:
    """Append a new message to an existing ticket."""
    tenant_id = get_current_tenant_id()
    try:
        ticket = await service.add_message(ticket_id, payload, current_user, tenant_id)
        return TicketDetail.model_validate(ticket, from_attributes=True)
    except Exception as exc:  # pragma: no cover
        logger.warning("ticket.message.failed", ticket_id=str(ticket_id), error=str(exc))
        _handle_ticket_error(exc)


@router.get(
    "/{ticket_id}/messages",
    response_model=list[TicketMessageResponse],
    summary="List messages for a ticket",
)
async def list_ticket_messages(
    ticket_id: UUID,
    service: TicketService = Depends(get_ticket_service),
    current_user: UserInfo = Depends(get_current_user),
) -> list[TicketMessageResponse]:
    """Return all messages for a ticket."""
    tenant_id = get_current_tenant_id()
    try:
        ticket = await service.get_ticket(ticket_id, current_user, tenant_id, include_messages=True)
        return [
            TicketMessageResponse.model_validate(m, from_attributes=True) for m in ticket.messages
        ]
    except Exception as exc:  # pragma: no cover
        logger.warning("ticket.messages.list.failed", ticket_id=str(ticket_id), error=str(exc))
        _handle_ticket_error(exc)


@router.get(
    "/stats",
    response_model=TicketCountStats,
    summary="Get ticket count statistics by status",
)
async def get_ticket_stats(
    service: TicketService = Depends(get_ticket_service),
    current_user: UserInfo = Depends(get_current_user),
) -> TicketCountStats:
    """Return counts of tickets by status for the current tenant/actor."""
    tenant_id = get_current_tenant_id()
    try:
        stats = await service.get_ticket_counts(current_user=current_user, tenant_id=tenant_id)
        return TicketCountStats.model_validate(stats)
    except Exception as exc:  # pragma: no cover
        logger.warning("ticket.stats.failed", error=str(exc))
        _handle_ticket_error(exc)


@router.get(
    "/metrics",
    response_model=TicketStats,
    summary="Get aggregated ticket metrics",
)
async def get_ticket_metrics(
    service: TicketService = Depends(get_ticket_service),
    current_user: UserInfo = Depends(get_current_user),
) -> TicketStats:
    """Aggregated counts grouped by status, priority, and type with SLA breaches."""
    tenant_id = get_current_tenant_id()
    try:
        metrics = await service.get_ticket_metrics(current_user=current_user, tenant_id=tenant_id)
        return TicketStats.model_validate(metrics)
    except Exception as exc:  # pragma: no cover
        logger.warning("ticket.metrics.failed", error=str(exc))
        _handle_ticket_error(exc)


@router.get(
    "/{ticket_id}",
    response_model=TicketDetail,
    summary="Retrieve ticket details",
)
async def get_ticket(
    ticket_id: UUID = Path(..., description="Ticket identifier"),
    service: TicketService = Depends(get_ticket_service),
    current_user: UserInfo = Depends(get_current_user),
) -> TicketDetail:
    """Fetch ticket details and threaded messages."""
    tenant_id = get_current_tenant_id()
    try:
        ticket = await service.get_ticket(ticket_id, current_user, tenant_id, include_messages=True)
        return TicketDetail.model_validate(ticket, from_attributes=True)
    except Exception as exc:  # pragma: no cover
        logger.warning("ticket.get.failed", ticket_id=str(ticket_id), error=str(exc))
        _handle_ticket_error(exc)


@router.patch(
    "/{ticket_id}",
    response_model=TicketDetail,
    summary="Update ticket metadata",
)
async def update_ticket(
    ticket_id: UUID,
    payload: TicketUpdate,
    service: TicketService = Depends(get_ticket_service),
    current_user: UserInfo = Depends(get_current_user),
) -> TicketDetail:
    """Update ticket status, priority, assignee, or metadata."""
    tenant_id = get_current_tenant_id()
    try:
        ticket = await service.update_ticket(ticket_id, payload, current_user, tenant_id)
        return TicketDetail.model_validate(ticket, from_attributes=True)
    except Exception as exc:  # pragma: no cover
        logger.warning("ticket.update.failed", ticket_id=str(ticket_id), error=str(exc))
        _handle_ticket_error(exc)


@router.get(
    "/agents/performance",
    response_model=list[AgentPerformanceMetrics],
    summary="Get agent performance metrics",
)
async def get_agent_performance(
    start_date: str | None = Query(None, description="Start date for metrics (ISO format)"),
    end_date: str | None = Query(None, description="End date for metrics (ISO format)"),
    service: TicketService = Depends(get_ticket_service),
    current_user: UserInfo = Depends(get_current_user),
) -> list[AgentPerformanceMetrics]:
    """Get performance metrics for all agents (assigned users)."""
    tenant_id = get_current_tenant_id()
    try:
        metrics = await service.get_agent_performance(
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date,
        )
        return metrics
    except Exception as exc:  # pragma: no cover
        logger.warning("agent.performance.failed", error=str(exc))
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve agent performance metrics",
        ) from exc


@router.post(
    "/{ticket_id}/assign/auto",
    response_model=TicketDetail,
    summary="Automatically assign ticket to available agent",
)
async def auto_assign_ticket(
    ticket_id: UUID,
    session: AsyncSession = Depends(get_session),
    service: TicketService = Depends(get_ticket_service),
    current_user: UserInfo = Depends(get_current_user),
) -> TicketDetail:
    """Automatically assign a ticket using round-robin with load balancing."""
    tenant_id = get_current_tenant_id()
    try:
        # Verify ticket exists and user has access
        await service.get_ticket(ticket_id, current_user, tenant_id, include_messages=False)

        # Use assignment service to auto-assign
        assignment_service = TicketAssignmentService(session)
        assigned_agent_id = await assignment_service.assign_ticket_automatically(
            ticket_id=ticket_id,
            tenant_id=tenant_id,
        )

        if not assigned_agent_id:
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No available agents to assign ticket",
            )

        # Fetch updated ticket with messages
        updated_ticket = await service.get_ticket(
            ticket_id, current_user, tenant_id, include_messages=True
        )
        return TicketDetail.model_validate(updated_ticket, from_attributes=True)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        logger.warning("ticket.auto_assign.failed", ticket_id=str(ticket_id), error=str(exc))
        _handle_ticket_error(exc)


# =============================================================================
# Dashboard Endpoint
# =============================================================================


class TicketDashboardSummary(BaseModel):
    """Summary statistics for ticket dashboard."""

    model_config = ConfigDict()

    total_tickets: int = Field(description="Total ticket count")
    open_tickets: int = Field(description="Open tickets count")
    in_progress_tickets: int = Field(description="In progress tickets count")
    waiting_tickets: int = Field(description="Waiting on customer count")
    resolved_tickets: int = Field(description="Resolved tickets count")
    closed_tickets: int = Field(description="Closed tickets count")
    sla_breached: int = Field(description="SLA breached tickets")
    avg_resolution_time_hours: float | None = Field(description="Average resolution time in hours")


class TicketChartDataPoint(BaseModel):
    """Single data point for ticket charts."""

    model_config = ConfigDict()

    label: str
    value: float
    metadata: dict[str, Any] = Field(default_factory=dict)


class TicketCharts(BaseModel):
    """Chart data for ticket dashboard."""

    model_config = ConfigDict()

    tickets_by_status: list[TicketChartDataPoint] = Field(description="Tickets by status")
    tickets_by_priority: list[TicketChartDataPoint] = Field(description="Tickets by priority")
    tickets_trend: list[TicketChartDataPoint] = Field(description="Monthly ticket trend")
    resolution_trend: list[TicketChartDataPoint] = Field(description="Monthly resolution trend")


class TicketAlert(BaseModel):
    """Alert item for ticket dashboard."""

    model_config = ConfigDict()

    type: str = Field(description="Alert type: warning, error, info")
    title: str
    message: str
    count: int = 0
    action_url: str | None = None


class TicketRecentActivity(BaseModel):
    """Recent activity item for ticket dashboard."""

    model_config = ConfigDict()

    id: str
    type: str = Field(description="Activity type: ticket, message")
    description: str
    status: str
    priority: str
    timestamp: datetime
    tenant_id: str | None = None


class TicketDashboardResponse(BaseModel):
    """Consolidated ticket dashboard response."""

    model_config = ConfigDict()

    summary: TicketDashboardSummary
    charts: TicketCharts
    alerts: list[TicketAlert]
    recent_activity: list[TicketRecentActivity]
    generated_at: datetime


@router.get(
    "/dashboard",
    response_model=TicketDashboardResponse,
    summary="Get ticket dashboard data",
    description="Returns consolidated ticket metrics, charts, and alerts for the dashboard",
)
async def get_ticket_dashboard(
    period_months: int = Query(6, ge=1, le=24, description="Months of trend data"),
    service: TicketService = Depends(get_ticket_service),
    current_user: UserInfo = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> TicketDashboardResponse:
    """
    Get consolidated ticket dashboard data including:
    - Summary statistics (ticket counts, SLA breaches)
    - Chart data (trends, breakdowns)
    - Alerts (urgent tickets, SLA breaches)
    - Recent activity
    """
    from .models import Ticket, TicketPriority as TicketPriorityModel

    try:
        tenant_id = get_current_tenant_id()
        now = datetime.now(timezone.utc)

        # ========== SUMMARY STATS ==========
        # Ticket counts by status
        ticket_counts_query = select(
            func.count(Ticket.id).label("total"),
            func.sum(case((Ticket.status == TicketStatus.OPEN, 1), else_=0)).label("open"),
            func.sum(case((Ticket.status == TicketStatus.IN_PROGRESS, 1), else_=0)).label("in_progress"),
            func.sum(case((Ticket.status == TicketStatus.WAITING, 1), else_=0)).label("waiting"),
            func.sum(case((Ticket.status == TicketStatus.RESOLVED, 1), else_=0)).label("resolved"),
            func.sum(case((Ticket.status == TicketStatus.CLOSED, 1), else_=0)).label("closed"),
            func.sum(case((Ticket.sla_breached.is_(True), 1), else_=0)).label("sla_breached"),
        )
        if tenant_id:
            ticket_counts_query = ticket_counts_query.where(Ticket.tenant_id == tenant_id)
        ticket_counts_result = await session.execute(ticket_counts_query)
        ticket_counts = ticket_counts_result.one()

        # Average resolution time
        avg_resolution_query = select(func.avg(Ticket.resolution_time_minutes))
        if tenant_id:
            avg_resolution_query = avg_resolution_query.where(Ticket.tenant_id == tenant_id)
        avg_resolution_result = await session.execute(avg_resolution_query)
        avg_resolution_minutes = avg_resolution_result.scalar()
        avg_resolution_hours = (avg_resolution_minutes / 60) if avg_resolution_minutes else None

        summary = TicketDashboardSummary(
            total_tickets=ticket_counts.total or 0,
            open_tickets=ticket_counts.open or 0,
            in_progress_tickets=ticket_counts.in_progress or 0,
            waiting_tickets=ticket_counts.waiting or 0,
            resolved_tickets=ticket_counts.resolved or 0,
            closed_tickets=ticket_counts.closed or 0,
            sla_breached=ticket_counts.sla_breached or 0,
            avg_resolution_time_hours=round(avg_resolution_hours, 2) if avg_resolution_hours else None,
        )

        # ========== CHART DATA ==========
        # Tickets by status
        status_query = select(
            Ticket.status,
            func.count(Ticket.id),
        )
        if tenant_id:
            status_query = status_query.where(Ticket.tenant_id == tenant_id)
        status_query = status_query.group_by(Ticket.status)
        status_result = await session.execute(status_query)
        tickets_by_status = [
            TicketChartDataPoint(label=row[0].value if row[0] else "unknown", value=row[1])
            for row in status_result.all()
        ]

        # Tickets by priority
        priority_query = select(
            Ticket.priority,
            func.count(Ticket.id),
        )
        if tenant_id:
            priority_query = priority_query.where(Ticket.tenant_id == tenant_id)
        priority_query = priority_query.group_by(Ticket.priority)
        priority_result = await session.execute(priority_query)
        tickets_by_priority = [
            TicketChartDataPoint(label=row[0].value if row[0] else "unknown", value=row[1])
            for row in priority_result.all()
        ]

        # Tickets trend (monthly)
        tickets_trend = []
        for i in range(period_months - 1, -1, -1):
            month_date = (now - timedelta(days=i * 30)).replace(day=1)
            next_month = (month_date + timedelta(days=32)).replace(day=1)

            month_count_query = select(func.count(Ticket.id)).where(
                Ticket.created_at >= month_date,
                Ticket.created_at < next_month,
            )
            if tenant_id:
                month_count_query = month_count_query.where(Ticket.tenant_id == tenant_id)
            month_count_result = await session.execute(month_count_query)
            month_count = month_count_result.scalar() or 0

            tickets_trend.append(TicketChartDataPoint(
                label=month_date.strftime("%b %Y"),
                value=month_count,
            ))

        # Resolution trend (monthly resolved)
        resolution_trend = []
        for i in range(period_months - 1, -1, -1):
            month_date = (now - timedelta(days=i * 30)).replace(day=1)
            next_month = (month_date + timedelta(days=32)).replace(day=1)

            resolved_query = select(func.count(Ticket.id)).where(
                Ticket.status.in_([TicketStatus.RESOLVED, TicketStatus.CLOSED]),
                Ticket.updated_at >= month_date,
                Ticket.updated_at < next_month,
            )
            if tenant_id:
                resolved_query = resolved_query.where(Ticket.tenant_id == tenant_id)
            resolved_result = await session.execute(resolved_query)
            resolved_count = resolved_result.scalar() or 0

            resolution_trend.append(TicketChartDataPoint(
                label=month_date.strftime("%b %Y"),
                value=resolved_count,
            ))

        charts = TicketCharts(
            tickets_by_status=tickets_by_status,
            tickets_by_priority=tickets_by_priority,
            tickets_trend=tickets_trend,
            resolution_trend=resolution_trend,
        )

        # ========== ALERTS ==========
        alerts = []

        # Urgent tickets
        urgent_query = select(func.count(Ticket.id)).where(
            Ticket.priority == TicketPriorityModel.URGENT,
            Ticket.status.in_([TicketStatus.OPEN, TicketStatus.IN_PROGRESS]),
        )
        if tenant_id:
            urgent_query = urgent_query.where(Ticket.tenant_id == tenant_id)
        urgent_result = await session.execute(urgent_query)
        urgent_count = urgent_result.scalar() or 0

        if urgent_count > 0:
            alerts.append(TicketAlert(
                type="error",
                title="Urgent Tickets",
                message=f"{urgent_count} urgent ticket(s) require immediate attention",
                count=urgent_count,
                action_url="/tickets?priority=urgent",
            ))

        # SLA breached
        if ticket_counts.sla_breached and ticket_counts.sla_breached > 0:
            alerts.append(TicketAlert(
                type="warning",
                title="SLA Breaches",
                message=f"{ticket_counts.sla_breached} ticket(s) have breached SLA",
                count=ticket_counts.sla_breached,
                action_url="/tickets?sla_breached=true",
            ))

        # ========== RECENT ACTIVITY ==========
        recent_tickets_query = select(Ticket).order_by(Ticket.created_at.desc()).limit(10)
        if tenant_id:
            recent_tickets_query = recent_tickets_query.where(Ticket.tenant_id == tenant_id)
        recent_tickets_result = await session.execute(recent_tickets_query)
        recent_tickets = recent_tickets_result.scalars().all()

        recent_activity = [
            TicketRecentActivity(
                id=str(t.id),
                type="ticket",
                description=f"Ticket: {t.ticket_number or str(t.id)[:8]} - {t.subject[:50] if t.subject else 'No subject'}",
                status=t.status.value if t.status else "unknown",
                priority=t.priority.value if t.priority else "normal",
                timestamp=t.created_at,
                tenant_id=t.tenant_id,
            )
            for t in recent_tickets
        ]

        return TicketDashboardResponse(
            summary=summary,
            charts=charts,
            alerts=alerts,
            recent_activity=recent_activity,
            generated_at=now,
        )

    except Exception as e:
        logger.error("Failed to generate ticket dashboard", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate ticket dashboard: {str(e)}",
        )


__all__ = ["router"]
