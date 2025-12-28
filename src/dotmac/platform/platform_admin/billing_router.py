"""
Platform Admin - Cross-Tenant Billing Router

Provides cross-tenant access to billing data for platform administrators.
All endpoints require platform.admin permission.
"""

# mypy: ignore-errors

from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.auth.rbac_dependencies import require_permission
from dotmac.platform.billing.core.entities import InvoiceEntity, PaymentEntity
from dotmac.platform.billing.core.enums import InvoiceStatus, PaymentStatus
from dotmac.platform.billing.models import BillingSubscriptionPlanTable, BillingSubscriptionTable
from dotmac.platform.billing.subscriptions.models import BillingCycle, SubscriptionStatus
from dotmac.platform.database import get_async_session
from dotmac.platform.tenant.models import Tenant

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/billing", tags=["Platform Admin - Billing"])


# ============================================================================
# Response Models
# ============================================================================


class TenantInvoiceSummary(BaseModel):
    """Summary of invoices for a tenant"""

    model_config = ConfigDict(from_attributes=True)

    tenant_id: str
    tenant_name: str | None = None
    total_invoices: int
    draft_count: int
    open_count: int
    paid_count: int
    void_count: int
    uncollectible_count: int
    total_amount: int  # Total across all invoices
    total_paid: int  # Total paid amount
    total_outstanding: int  # Total outstanding amount


class CrossTenantInvoiceListResponse(BaseModel):
    """Cross-tenant invoice list"""

    model_config = ConfigDict()

    invoices: list[dict[str, Any]]
    total_count: int
    has_more: bool
    tenant_summaries: list[TenantInvoiceSummary] | None = None


class CrossTenantPaymentListResponse(BaseModel):
    """Cross-tenant payment list"""

    model_config = ConfigDict()

    payments: list[dict[str, Any]]
    total_count: int
    has_more: bool


class PlatformBillingSummary(BaseModel):
    """Platform-wide billing summary"""

    model_config = ConfigDict()

    total_tenants: int
    total_invoices: int
    total_payments: int
    total_revenue: int  # Total paid
    total_outstanding: int  # Total unpaid
    mrr: int  # Monthly Recurring Revenue
    arr: int  # Annual Recurring Revenue
    by_status: dict[str, int]  # Count by invoice status
    by_tenant: list[TenantInvoiceSummary]


# ============================================================================
# Platform Admin Billing Endpoints
# ============================================================================


@router.get(
    "/invoices",
    response_model=CrossTenantInvoiceListResponse,
    summary="List all invoices across tenants",
    description="Get invoices from all tenants (platform admin only)",
)
async def list_all_invoices(
    tenant_id: str | None = Query(None, description="Optional tenant filter"),
    status: InvoiceStatus | None = Query(None, description="Filter by invoice status"),
    limit: int = Query(100, ge=1, le=1000, description="Max results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    session: AsyncSession = Depends(get_async_session),
    _current_user=Depends(require_permission("platform.admin")),
):
    """
    List invoices across all tenants.

    **Required Permission:** platform.admin

    **Filters:**
    - tenant_id: Drill down to specific tenant
    - status: Filter by invoice status
    - tenant_id: Filter by tenant

    **Returns:** Cross-tenant invoice list with tenant summaries
    """
    try:
        # Build base query
        filters = []

        if tenant_id:
            filters.append(InvoiceEntity.tenant_id == tenant_id)

        if status:
            filters.append(InvoiceEntity.status == status)

        # Count total
        count_query = select(func.count(InvoiceEntity.invoice_id))
        if filters:
            count_query = count_query.where(and_(*filters))

        count_result = await session.execute(count_query)
        total_count = count_result.scalar_one()

        # Get invoices
        query = (
            select(InvoiceEntity)
            .limit(limit)
            .offset(offset)
            .order_by(InvoiceEntity.created_at.desc())
        )

        if filters:
            query = query.where(and_(*filters))

        result = await session.execute(query)
        invoices = result.scalars().all()

        # Convert to dict with tenant_id included
        tenant_ids = {str(invoice.tenant_id) for invoice in invoices if invoice.tenant_id}
        tenant_names: dict[str, str] = {}
        if tenant_ids:
            tenant_query = select(Tenant.id, Tenant.name).where(Tenant.id.in_(tenant_ids))
            tenant_result = await session.execute(tenant_query)
            tenant_names = {str(row.id): row.name for row in tenant_result.all()}

        invoice_dicts = []
        for invoice in invoices:
            tenant_id_value = str(invoice.tenant_id) if invoice.tenant_id else None
            invoice_dict = {
                "id": invoice.invoice_id,
                "tenant_id": tenant_id_value,  # ✅ Include tenant_id
                "tenant_name": tenant_names.get(tenant_id_value),
                "customer_id": invoice.customer_id,
                "status": invoice.status,
                "amount": invoice.total_amount,
                "amount_paid": (invoice.total_amount - invoice.remaining_balance)
                if invoice.remaining_balance is not None
                else 0,
                "amount_remaining": invoice.remaining_balance
                if invoice.remaining_balance is not None
                else invoice.total_amount,
                "currency": invoice.currency,
                "due_date": invoice.due_date.isoformat() if invoice.due_date else None,
                "created_at": invoice.created_at.isoformat(),
                "billing_email": invoice.billing_email,
            }
            invoice_dicts.append(invoice_dict)

        # Get tenant summaries if not filtering by specific tenant
        tenant_summaries = None
        if not tenant_id:
            summary_query = select(
                InvoiceEntity.tenant_id,
                InvoiceEntity.status,
                func.count(InvoiceEntity.invoice_id).label("count"),
                func.sum(InvoiceEntity.total_amount).label("total_amount"),
                func.sum(
                    InvoiceEntity.total_amount - InvoiceEntity.remaining_balance
                ).label("total_paid"),
            ).group_by(InvoiceEntity.tenant_id, InvoiceEntity.status)

            summary_result = await session.execute(summary_query)
            summary_rows = summary_result.all()

            # Aggregate by tenant
            tenant_data: dict[str, dict[str, Any]] = {}
            for row in summary_rows:
                t_id = row.tenant_id
                if t_id not in tenant_data:
                    tenant_data[t_id] = {
                        "tenant_id": t_id,
                        "tenant_name": None,  # Populated below after aggregation
                        "total_invoices": 0,
                        "draft_count": 0,
                        "open_count": 0,
                        "paid_count": 0,
                        "void_count": 0,
                        "uncollectible_count": 0,
                        "total_amount": 0,
                        "total_paid": 0,
                        "total_outstanding": 0,
                    }

                tenant_data[t_id]["total_invoices"] += row.count

                if row.status == InvoiceStatus.DRAFT:
                    tenant_data[t_id]["draft_count"] = row.count
                elif row.status == InvoiceStatus.OPEN:
                    tenant_data[t_id]["open_count"] = row.count
                elif row.status == InvoiceStatus.PAID:
                    tenant_data[t_id]["paid_count"] = row.count
                elif row.status == InvoiceStatus.VOID:
                    tenant_data[t_id]["void_count"] = row.count
                elif row.status == InvoiceStatus.OVERDUE:
                    tenant_data[t_id]["uncollectible_count"] = row.count

                tenant_data[t_id]["total_amount"] += row.total_amount or 0
                tenant_data[t_id]["total_paid"] += row.total_paid or 0

            # Calculate outstanding
            for t_data in tenant_data.values():
                t_data["total_outstanding"] = t_data["total_amount"] - t_data["total_paid"]

            # Fetch tenant names
            if tenant_data:
                tenant_ids = list(tenant_data.keys())
                tenant_query = select(Tenant.id, Tenant.name).where(Tenant.id.in_(tenant_ids))
                tenant_result = await session.execute(tenant_query)
                tenant_names = {str(row.id): row.name for row in tenant_result.all()}
                for t_id, t_data in tenant_data.items():
                    t_data["tenant_name"] = tenant_names.get(t_id)

            tenant_summaries = [TenantInvoiceSummary(**data) for data in tenant_data.values()]

        return CrossTenantInvoiceListResponse(
            invoices=invoice_dicts,
            total_count=total_count,
            has_more=(offset + len(invoice_dicts)) < total_count,
            tenant_summaries=tenant_summaries,
        )

    except Exception as e:
        logger.error("Failed to list cross-tenant invoices", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve invoices: {str(e)}",
        )


@router.get(
    "/payments",
    response_model=CrossTenantPaymentListResponse,
    summary="List all payments across tenants",
    description="Get payments from all tenants (platform admin only)",
)
async def list_all_payments(
    tenant_id: str | None = Query(None, description="Optional tenant filter"),
    status: PaymentStatus | None = Query(None, description="Filter by payment status"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_async_session),
    _current_user=Depends(require_permission("platform.admin")),
):
    """
    List payments across all tenants.

    **Required Permission:** platform.admin

    **Returns:** Cross-tenant payment list
    """
    try:
        filters = []

        if tenant_id:
            filters.append(PaymentEntity.tenant_id == tenant_id)

        if status:
            filters.append(PaymentEntity.status == status)

        # Count total
        count_query = select(func.count(PaymentEntity.payment_id))
        if filters:
            count_query = count_query.where(and_(*filters))

        count_result = await session.execute(count_query)
        total_count = count_result.scalar_one()

        # Get payments
        query = (
            select(PaymentEntity)
            .limit(limit)
            .offset(offset)
            .order_by(PaymentEntity.created_at.desc())
        )

        if filters:
            query = query.where(and_(*filters))

        result = await session.execute(query)
        payments = result.scalars().all()

        # Convert to dict with tenant_id
        tenant_ids = {str(payment.tenant_id) for payment in payments if payment.tenant_id}
        tenant_names: dict[str, str] = {}
        if tenant_ids:
            tenant_query = select(Tenant.id, Tenant.name).where(Tenant.id.in_(tenant_ids))
            tenant_result = await session.execute(tenant_query)
            tenant_names = {str(row.id): row.name for row in tenant_result.all()}

        payment_dicts = []
        for payment in payments:
            tenant_id_value = str(payment.tenant_id) if payment.tenant_id else None
            invoice_ids = []
            if hasattr(payment, "invoices") and payment.invoices:
                invoice_ids = [str(inv.invoice_id) for inv in payment.invoices]
            payment_dict = {
                "id": payment.payment_id,
                "tenant_id": tenant_id_value,  # ✅ Include tenant_id
                "tenant_name": tenant_names.get(tenant_id_value),
                "invoice_id": invoice_ids[0] if invoice_ids else None,
                "invoice_ids": invoice_ids,
                "amount": payment.amount,
                "currency": payment.currency,
                "status": payment.status,
                "payment_method": getattr(payment, "payment_method_type", None),
                "created_at": payment.created_at.isoformat(),
            }
            payment_dicts.append(payment_dict)

        return CrossTenantPaymentListResponse(
            payments=payment_dicts,
            total_count=total_count,
            has_more=(offset + len(payment_dicts)) < total_count,
        )

    except Exception as e:
        logger.error("Failed to list cross-tenant payments", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve payments: {str(e)}",
        )


@router.get(
    "/summary",
    response_model=PlatformBillingSummary,
    summary="Get platform-wide billing summary",
    description="Get billing metrics across all tenants (platform admin only)",
)
async def get_platform_billing_summary(
    session: AsyncSession = Depends(get_async_session),
    _current_user=Depends(require_permission("platform.admin")),
):
    """
    Get platform-wide billing summary with cross-tenant metrics.

    **Required Permission:** platform.admin

    **Returns:**
    - Total tenants
    - Total invoices and payments
    - Revenue metrics (MRR, ARR)
    - Per-tenant breakdown
    """
    try:
        # Count unique tenants
        tenant_count_query = select(func.count(func.distinct(InvoiceEntity.tenant_id)))
        tenant_count_result = await session.execute(tenant_count_query)
        total_tenants = tenant_count_result.scalar_one()

        # Total invoices
        invoice_count_query = select(func.count(InvoiceEntity.invoice_id))
        invoice_count_result = await session.execute(invoice_count_query)
        total_invoices = invoice_count_result.scalar_one()

        # Total payments
        payment_count_query = select(func.count(PaymentEntity.payment_id))
        payment_count_result = await session.execute(payment_count_query)
        total_payments = payment_count_result.scalar_one()

        # Revenue metrics
        revenue_query = select(
            func.sum(InvoiceEntity.total_amount - InvoiceEntity.remaining_balance).label(
                "total_revenue"
            ),
            func.sum(InvoiceEntity.remaining_balance).label("total_outstanding"),
        )
        revenue_result = await session.execute(revenue_query)
        revenue_row = revenue_result.one()

        total_revenue = revenue_row.total_revenue or 0
        total_outstanding = revenue_row.total_outstanding or 0

        # Count by status
        status_query = select(
            InvoiceEntity.status, func.count(InvoiceEntity.invoice_id).label("count")
        ).group_by(InvoiceEntity.status)
        status_result = await session.execute(status_query)
        by_status = {row.status: row.count for row in status_result.all()}

        # Tenant summaries (same as in list_all_invoices)
        summary_query = select(
            InvoiceEntity.tenant_id,
            InvoiceEntity.status,
            func.count(InvoiceEntity.invoice_id).label("count"),
            func.sum(InvoiceEntity.total_amount).label("total_amount"),
            func.sum(
                InvoiceEntity.total_amount - InvoiceEntity.remaining_balance
            ).label("total_paid"),
        ).group_by(InvoiceEntity.tenant_id, InvoiceEntity.status)

        summary_result = await session.execute(summary_query)
        summary_rows = summary_result.all()

        tenant_data: dict[str, dict[str, Any]] = {}
        for row in summary_rows:
            t_id = row.tenant_id
            if t_id not in tenant_data:
                tenant_data[t_id] = {
                    "tenant_id": t_id,
                    "tenant_name": None,
                    "total_invoices": 0,
                    "draft_count": 0,
                    "open_count": 0,
                    "paid_count": 0,
                    "void_count": 0,
                    "uncollectible_count": 0,
                    "total_amount": 0,
                    "total_paid": 0,
                    "total_outstanding": 0,
                }

            tenant_data[t_id]["total_invoices"] += row.count

            if row.status == InvoiceStatus.DRAFT:
                tenant_data[t_id]["draft_count"] = row.count
            elif row.status == InvoiceStatus.OPEN:
                tenant_data[t_id]["open_count"] = row.count
            elif row.status == InvoiceStatus.PAID:
                tenant_data[t_id]["paid_count"] = row.count
            elif row.status == InvoiceStatus.VOID:
                tenant_data[t_id]["void_count"] = row.count
            elif row.status == InvoiceStatus.OVERDUE:
                tenant_data[t_id]["uncollectible_count"] = row.count

            tenant_data[t_id]["total_amount"] += row.total_amount or 0
            tenant_data[t_id]["total_paid"] += row.total_paid or 0

        for t_data in tenant_data.values():
            t_data["total_outstanding"] = t_data["total_amount"] - t_data["total_paid"]

        if tenant_data:
            tenant_ids = list(tenant_data.keys())
            tenant_query = select(Tenant.id, Tenant.name).where(Tenant.id.in_(tenant_ids))
            tenant_result = await session.execute(tenant_query)
            tenant_names = {str(row.id): row.name for row in tenant_result.all()}
            for t_id, t_data in tenant_data.items():
                t_data["tenant_name"] = tenant_names.get(t_id)

        by_tenant = [TenantInvoiceSummary(**data) for data in tenant_data.values()]

        active_statuses = [
            SubscriptionStatus.ACTIVE.value,
            SubscriptionStatus.TRIALING.value,
            SubscriptionStatus.PAST_DUE.value,
        ]
        price_expression = func.coalesce(
            BillingSubscriptionTable.custom_price,
            BillingSubscriptionPlanTable.price,
        )
        mrr_query = select(
            func.sum(
                case(
                    (BillingSubscriptionPlanTable.billing_cycle == BillingCycle.MONTHLY.value, price_expression),
                    (
                        BillingSubscriptionPlanTable.billing_cycle == BillingCycle.QUARTERLY.value,
                        price_expression / 3,
                    ),
                    (
                        BillingSubscriptionPlanTable.billing_cycle == BillingCycle.ANNUAL.value,
                        price_expression / 12,
                    ),
                    else_=0,
                )
            ).label("mrr")
        ).select_from(BillingSubscriptionTable).join(
            BillingSubscriptionPlanTable,
            and_(
                BillingSubscriptionPlanTable.plan_id == BillingSubscriptionTable.plan_id,
                BillingSubscriptionPlanTable.tenant_id == BillingSubscriptionTable.tenant_id,
            ),
        )
        mrr_query = mrr_query.where(BillingSubscriptionTable.status.in_(active_statuses))
        mrr_value = await session.scalar(mrr_query)
        mrr = int(mrr_value or 0)
        arr = int(mrr * 12)

        return PlatformBillingSummary(
            total_tenants=total_tenants,
            total_invoices=total_invoices,
            total_payments=total_payments,
            total_revenue=total_revenue,
            total_outstanding=total_outstanding,
            mrr=mrr,
            arr=arr,
            by_status=by_status,
            by_tenant=by_tenant,
        )

    except Exception as e:
        logger.error("Failed to generate platform billing summary", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate summary: {str(e)}",
        )


__all__ = ["router"]
