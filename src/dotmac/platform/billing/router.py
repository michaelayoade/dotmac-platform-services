"""
Main billing module router aggregating all billing sub-routers
"""

from datetime import datetime, timedelta, timezone
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select, case, extract
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.auth.core import UserInfo
from dotmac.platform.auth.rbac_dependencies import require_permission
from dotmac.platform.database import get_async_session

from .addons.router import router as addons_router
from .bank_accounts.router import router as bank_accounts_router
from .catalog.router import router as catalog_router
from .credit_notes.router import router as credit_note_router
from .dunning.router import router as dunning_router
from .invoicing.router import router as invoice_router
from .payment_methods.router import router as payment_methods_router
from .payments.router import router as payments_router
from .settings.router import router as settings_router
from .subscriptions.router import router as subscriptions_router
from .subscriptions.tenant_router import router as tenant_subscriptions_router
from .usage.router import router as usage_router
from .webhooks.router import router as webhook_router

# Create main billing router - no prefix here as it's added in main router registration
router = APIRouter(prefix="/billing", tags=["Billing"])

# Include sub-routers with hierarchical tags for better API docs organization
router.include_router(invoice_router, prefix="", tags=["Billing - Invoices"])
router.include_router(webhook_router, prefix="", tags=["Billing - Webhooks"])
router.include_router(credit_note_router, prefix="", tags=["Billing - Credit Notes"])
router.include_router(settings_router, prefix="", tags=["Billing - Settings"])
router.include_router(bank_accounts_router, prefix="", tags=["Billing - Bank Accounts"])
router.include_router(catalog_router, prefix="", tags=["Billing - Catalog"])
router.include_router(
    subscriptions_router, prefix="/subscriptions", tags=["Billing - Subscriptions"]
)
router.include_router(tenant_subscriptions_router, prefix="", tags=["Tenant - Subscriptions"])
router.include_router(addons_router, prefix="", tags=["Tenant - Add-ons"])
router.include_router(payment_methods_router, prefix="", tags=["Tenant - Payment Methods"])
router.include_router(payments_router, prefix="", tags=["Billing - Payments"])
router.include_router(dunning_router, prefix="/dunning", tags=["Billing - Dunning"])
router.include_router(usage_router, prefix="", tags=["Billing - Usage"])

# Additional billing endpoints can be added here

logger = structlog.get_logger(__name__)


# ============================================================================
# Dashboard Response Models
# ============================================================================


class BillingSummary(BaseModel):
    """Summary statistics for billing dashboard"""

    model_config = ConfigDict()

    total_revenue: float = Field(description="Total revenue in major currency units")
    revenue_this_month: float = Field(description="Revenue this month")
    revenue_last_month: float = Field(description="Revenue last month")
    revenue_change_pct: float = Field(description="Month-over-month change percentage")
    total_invoices: int = Field(description="Total invoice count")
    open_invoices: int = Field(description="Open invoices count")
    overdue_invoices: int = Field(description="Overdue invoices count")
    active_subscriptions: int = Field(description="Active subscriptions count")
    mrr: float = Field(description="Monthly Recurring Revenue")
    outstanding_balance: float = Field(description="Total outstanding balance")


class ChartDataPoint(BaseModel):
    """Single data point for charts"""

    model_config = ConfigDict()

    label: str
    value: float
    metadata: dict[str, Any] = Field(default_factory=dict)


class BillingCharts(BaseModel):
    """Chart data for billing dashboard"""

    model_config = ConfigDict()

    revenue_trend: list[ChartDataPoint] = Field(description="Monthly revenue trend")
    invoices_by_status: list[ChartDataPoint] = Field(description="Invoice breakdown by status")
    subscriptions_by_plan: list[ChartDataPoint] = Field(description="Subscriptions by plan")
    payment_methods: list[ChartDataPoint] = Field(description="Payment method distribution")


class BillingAlert(BaseModel):
    """Alert item for billing dashboard"""

    model_config = ConfigDict()

    type: str = Field(description="Alert type: warning, error, info")
    title: str
    message: str
    count: int = 0
    action_url: str | None = None


class RecentActivity(BaseModel):
    """Recent activity item"""

    model_config = ConfigDict()

    id: str
    type: str = Field(description="Activity type: invoice, payment, subscription")
    description: str
    amount: float | None = None
    status: str
    timestamp: datetime
    tenant_id: str | None = None


class BillingDashboardResponse(BaseModel):
    """Consolidated billing dashboard response"""

    model_config = ConfigDict()

    summary: BillingSummary
    charts: BillingCharts
    alerts: list[BillingAlert]
    recent_activity: list[RecentActivity]
    generated_at: datetime


# ============================================================================
# Dashboard Endpoint
# ============================================================================


@router.get(
    "/dashboard",
    response_model=BillingDashboardResponse,
    summary="Get billing dashboard data",
    description="Returns consolidated billing metrics, charts, and alerts for the dashboard",
)
async def get_billing_dashboard(
    period_months: int = Query(6, ge=1, le=24, description="Months of trend data"),
    session: AsyncSession = Depends(get_async_session),
    _current_user: UserInfo = Depends(require_permission("billing.read")),
) -> BillingDashboardResponse:
    """
    Get consolidated billing dashboard data including:
    - Summary statistics (revenue, invoices, subscriptions)
    - Chart data (trends, breakdowns)
    - Alerts (overdue invoices, failed payments)
    - Recent activity
    """
    try:
        from .core.entities import InvoiceEntity, PaymentEntity
        from .core.enums import InvoiceStatus, PaymentStatus
        from .subscriptions.models import BillingSubscription

        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_start = (month_start - timedelta(days=1)).replace(day=1)

        # ========== SUMMARY STATS ==========
        # Total revenue (paid invoices)
        total_revenue_query = select(
            func.coalesce(func.sum(InvoiceEntity.total_amount - InvoiceEntity.remaining_balance), 0)
        ).where(InvoiceEntity.status == InvoiceStatus.PAID)
        total_revenue_result = await session.execute(total_revenue_query)
        total_revenue = (total_revenue_result.scalar() or 0) / 100  # Convert cents to dollars

        # Revenue this month
        this_month_query = select(
            func.coalesce(func.sum(InvoiceEntity.total_amount - InvoiceEntity.remaining_balance), 0)
        ).where(
            InvoiceEntity.status == InvoiceStatus.PAID,
            InvoiceEntity.paid_at >= month_start,
        )
        this_month_result = await session.execute(this_month_query)
        revenue_this_month = (this_month_result.scalar() or 0) / 100

        # Revenue last month
        last_month_query = select(
            func.coalesce(func.sum(InvoiceEntity.total_amount - InvoiceEntity.remaining_balance), 0)
        ).where(
            InvoiceEntity.status == InvoiceStatus.PAID,
            InvoiceEntity.paid_at >= last_month_start,
            InvoiceEntity.paid_at < month_start,
        )
        last_month_result = await session.execute(last_month_query)
        revenue_last_month = (last_month_result.scalar() or 0) / 100

        # Calculate change percentage
        if revenue_last_month > 0:
            revenue_change_pct = ((revenue_this_month - revenue_last_month) / revenue_last_month) * 100
        else:
            revenue_change_pct = 100.0 if revenue_this_month > 0 else 0.0

        # Invoice counts
        invoice_counts_query = select(
            func.count(InvoiceEntity.invoice_id).label("total"),
            func.sum(case((InvoiceEntity.status == InvoiceStatus.OPEN, 1), else_=0)).label("open"),
            func.sum(case((InvoiceEntity.status == InvoiceStatus.OVERDUE, 1), else_=0)).label("overdue"),
        )
        invoice_counts_result = await session.execute(invoice_counts_query)
        invoice_counts = invoice_counts_result.one()

        # Active subscriptions
        active_subs_query = select(func.count(BillingSubscription.id)).where(
            BillingSubscription.status == "active"
        )
        active_subs_result = await session.execute(active_subs_query)
        active_subscriptions = active_subs_result.scalar() or 0

        # Outstanding balance
        outstanding_query = select(func.coalesce(func.sum(InvoiceEntity.remaining_balance), 0)).where(
            InvoiceEntity.status.in_([InvoiceStatus.OPEN, InvoiceStatus.OVERDUE, InvoiceStatus.PARTIALLY_PAID])
        )
        outstanding_result = await session.execute(outstanding_query)
        outstanding_balance = (outstanding_result.scalar() or 0) / 100

        # MRR calculation (sum of monthly subscription amounts)
        mrr_query = select(func.coalesce(func.sum(BillingSubscription.amount), 0)).where(
            BillingSubscription.status == "active"
        )
        mrr_result = await session.execute(mrr_query)
        mrr = (mrr_result.scalar() or 0) / 100

        summary = BillingSummary(
            total_revenue=total_revenue,
            revenue_this_month=revenue_this_month,
            revenue_last_month=revenue_last_month,
            revenue_change_pct=round(revenue_change_pct, 2),
            total_invoices=invoice_counts.total or 0,
            open_invoices=invoice_counts.open or 0,
            overdue_invoices=invoice_counts.overdue or 0,
            active_subscriptions=active_subscriptions,
            mrr=mrr,
            outstanding_balance=outstanding_balance,
        )

        # ========== CHART DATA ==========
        # Revenue trend (monthly)
        revenue_trend = []
        for i in range(period_months - 1, -1, -1):
            month_date = (now - timedelta(days=i * 30)).replace(day=1)
            next_month = (month_date + timedelta(days=32)).replace(day=1)

            month_revenue_query = select(
                func.coalesce(func.sum(InvoiceEntity.total_amount - InvoiceEntity.remaining_balance), 0)
            ).where(
                InvoiceEntity.status == InvoiceStatus.PAID,
                InvoiceEntity.paid_at >= month_date,
                InvoiceEntity.paid_at < next_month,
            )
            month_revenue_result = await session.execute(month_revenue_query)
            month_revenue = (month_revenue_result.scalar() or 0) / 100

            revenue_trend.append(ChartDataPoint(
                label=month_date.strftime("%b %Y"),
                value=month_revenue,
            ))

        # Invoices by status
        status_query = select(
            InvoiceEntity.status,
            func.count(InvoiceEntity.invoice_id),
        ).group_by(InvoiceEntity.status)
        status_result = await session.execute(status_query)
        invoices_by_status = [
            ChartDataPoint(label=row[0].value if row[0] else "unknown", value=row[1])
            for row in status_result.all()
        ]

        # Subscriptions by plan
        plan_query = select(
            BillingSubscription.plan_id,
            func.count(BillingSubscription.id),
        ).where(BillingSubscription.status == "active").group_by(BillingSubscription.plan_id)
        plan_result = await session.execute(plan_query)
        subscriptions_by_plan = [
            ChartDataPoint(label=row[0] or "Unknown", value=row[1])
            for row in plan_result.all()
        ]

        charts = BillingCharts(
            revenue_trend=revenue_trend,
            invoices_by_status=invoices_by_status,
            subscriptions_by_plan=subscriptions_by_plan,
            payment_methods=[],  # TODO: Add when payment methods are tracked
        )

        # ========== ALERTS ==========
        alerts = []

        if invoice_counts.overdue and invoice_counts.overdue > 0:
            alerts.append(BillingAlert(
                type="warning",
                title="Overdue Invoices",
                message=f"{invoice_counts.overdue} invoice(s) are past due date",
                count=invoice_counts.overdue,
                action_url="/billing/invoices?status=overdue",
            ))

        # Failed payments in last 7 days
        failed_payments_query = select(func.count(PaymentEntity.id)).where(
            PaymentEntity.status == PaymentStatus.FAILED,
            PaymentEntity.created_at >= now - timedelta(days=7),
        )
        failed_payments_result = await session.execute(failed_payments_query)
        failed_payments = failed_payments_result.scalar() or 0

        if failed_payments > 0:
            alerts.append(BillingAlert(
                type="error",
                title="Failed Payments",
                message=f"{failed_payments} payment(s) failed in the last 7 days",
                count=failed_payments,
                action_url="/billing/payments?status=failed",
            ))

        # ========== RECENT ACTIVITY ==========
        recent_invoices_query = (
            select(InvoiceEntity)
            .order_by(InvoiceEntity.created_at.desc())
            .limit(10)
        )
        recent_invoices_result = await session.execute(recent_invoices_query)
        recent_invoices = recent_invoices_result.scalars().all()

        recent_activity = [
            RecentActivity(
                id=str(inv.invoice_id),
                type="invoice",
                description=f"Invoice {inv.invoice_number or inv.invoice_id[:8]}",
                amount=inv.total_amount / 100,
                status=inv.status.value if inv.status else "unknown",
                timestamp=inv.created_at,
                tenant_id=inv.tenant_id,
            )
            for inv in recent_invoices
        ]

        return BillingDashboardResponse(
            summary=summary,
            charts=charts,
            alerts=alerts,
            recent_activity=recent_activity,
            generated_at=now,
        )

    except Exception as e:
        logger.error("Failed to generate billing dashboard", error=str(e))
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate billing dashboard: {str(e)}",
        )


__all__ = ["router"]
