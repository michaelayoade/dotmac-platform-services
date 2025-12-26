"""
Billing Metrics Router.

Provides comprehensive metrics endpoints for billing overview, payment history,
and tenant insights with caching and tenant isolation.
"""

from datetime import UTC, datetime, timedelta
from inspect import isawaitable
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.auth.core import UserInfo
from dotmac.platform.auth.dependencies import get_current_user
from dotmac.platform.auth.rbac_dependencies import require_permission
from dotmac.platform.billing.dependencies import enforce_tenant_access
from dotmac.platform.billing._typing_helpers import CacheTier, cached_result
from dotmac.platform.billing.core.entities import (
    InvoiceEntity,
    PaymentEntity,
)
from dotmac.platform.billing.core.models import PaymentStatus
from dotmac.platform.billing.models import BillingSubscriptionTable
from dotmac.platform.db import get_session_dependency

logger = structlog.get_logger(__name__)

router = APIRouter(
    prefix="",
    tags=["Billing Metrics"],
)


# ============================================================================
# Caching Configuration
# ============================================================================

# Cache TTLs (in seconds)
METRICS_CACHE_TTL = 300  # 5 minutes for metrics
PAYMENTS_CACHE_TTL = 180  # 3 minutes for payment lists
EXPIRING_SUBS_CACHE_TTL = 600  # 10 minutes for expiring subscriptions


# ============================================================================
# Response Models
# ============================================================================


class BillingMetricsResponse(BaseModel):
    """Billing overview metrics response."""

    model_config = ConfigDict(from_attributes=True)

    # Revenue metrics
    mrr: float = Field(description="Monthly Recurring Revenue")
    arr: float = Field(description="Annual Recurring Revenue")

    # Counts
    active_subscriptions: int = Field(description="Number of active subscriptions")
    total_invoices: int = Field(description="Total invoices this period")
    paid_invoices: int = Field(description="Paid invoices this period")
    overdue_invoices: int = Field(description="Overdue invoices")

    # Payment metrics
    total_payments: int = Field(description="Total payments this period")
    successful_payments: int = Field(description="Successful payments")
    failed_payments: int = Field(description="Failed payments")
    total_payment_amount: float = Field(description="Total payment amount in major units")

    # Time period
    period: str = Field(description="Metrics calculation period")
    timestamp: datetime = Field(description="Metrics generation timestamp")


class PaymentListItem(BaseModel):
    """Individual payment item in list."""

    model_config = ConfigDict(from_attributes=True)

    payment_id: str
    amount: float = Field(description="Amount in major currency units")
    currency: str
    status: str
    tenant_id: str
    payment_method_type: str
    provider: str
    created_at: datetime
    processed_at: datetime | None = None
    failure_reason: str | None = None


class PaymentListResponse(BaseModel):
    """List of recent payments response."""

    model_config = ConfigDict(from_attributes=True)

    payments: list[PaymentListItem] = Field(description="List of payments")
    total_count: int = Field(description="Total number of payments")
    limit: int = Field(description="Result limit applied")
    timestamp: datetime = Field(description="Response generation timestamp")


# ============================================================================
# Cached Helper Functions
# ============================================================================


@cached_result(  # type: ignore[misc]  # Cache decorator is untyped
    ttl=METRICS_CACHE_TTL,
    key_prefix="billing:metrics",
    key_params=["period_days", "tenant_id"],
    tier=CacheTier.L2_REDIS,
)
async def _get_billing_metrics_cached(
    period_days: int,
    tenant_id: str | None,
    session: AsyncSession,
) -> dict[str, Any]:
    """
    Cached helper function for billing metrics calculation.

    This function contains the actual business logic and is cached independently.
    """
    now = datetime.now(UTC)
    period_start = now - timedelta(days=period_days)

    # Query active subscriptions for MRR calculation
    subscription_query = select(
        func.count(BillingSubscriptionTable.subscription_id).label("count"),
        func.coalesce(func.sum(BillingSubscriptionTable.custom_price), 0).label("total_amount"),
    ).where(BillingSubscriptionTable.status == "active")

    if tenant_id:
        subscription_query = subscription_query.where(
            BillingSubscriptionTable.tenant_id == tenant_id
        )

    subscription_result = await session.execute(subscription_query)
    subscription_row = subscription_result.one()

    subscription_mapping = subscription_row._mapping
    active_subscriptions = int(subscription_mapping.get("count") or 0)
    total_subscription_amount = float(subscription_mapping.get("total_amount") or 0)

    # Calculate MRR and ARR
    mrr = total_subscription_amount / 100
    arr = mrr * 12

    # Query invoice statistics
    from sqlalchemy import case

    from dotmac.platform.billing.core.enums import InvoiceStatus

    invoice_query = select(
        func.count(InvoiceEntity.invoice_id).label("total"),
        func.sum(case((InvoiceEntity.status == InvoiceStatus.PAID, 1), else_=0)).label("paid"),
        func.sum(
            case(
                (
                    and_(
                        InvoiceEntity.status == InvoiceStatus.OPEN,
                        InvoiceEntity.due_date < now,
                    ),
                    1,
                ),
                else_=0,
            )
        ).label("overdue"),
    ).where(InvoiceEntity.created_at >= period_start)

    if tenant_id:
        invoice_query = invoice_query.where(InvoiceEntity.tenant_id == tenant_id)

    invoice_result = await session.execute(invoice_query)
    invoice_row = invoice_result.one()

    # Query payment statistics
    payment_query = select(
        func.count(PaymentEntity.payment_id).label("total"),
        func.sum(case((PaymentEntity.status == PaymentStatus.SUCCEEDED, 1), else_=0)).label(
            "successful"
        ),
        func.sum(case((PaymentEntity.status == PaymentStatus.FAILED, 1), else_=0)).label("failed"),
        func.coalesce(
            func.sum(
                case(
                    (PaymentEntity.status == PaymentStatus.SUCCEEDED, PaymentEntity.amount),
                    else_=0,
                )
            ),
            0,
        ).label("total_amount"),
    ).where(PaymentEntity.created_at >= period_start)

    if tenant_id:
        payment_query = payment_query.where(PaymentEntity.tenant_id == tenant_id)

    payment_result = await session.execute(payment_query)
    payment_row = payment_result.one()

    return {
        "mrr": mrr,
        "arr": arr,
        "active_subscriptions": active_subscriptions,
        "total_invoices": invoice_row.total or 0,
        "paid_invoices": invoice_row.paid or 0,
        "overdue_invoices": invoice_row.overdue or 0,
        "total_payments": payment_row.total or 0,
        "successful_payments": payment_row.successful or 0,
        "failed_payments": payment_row.failed or 0,
        "total_payment_amount": float(payment_row.total_amount or 0) / 100,
        "period": f"{period_days}d",
        "timestamp": now,
    }


@cached_result(  # type: ignore[misc]  # Cache decorator is untyped
    ttl=EXPIRING_SUBS_CACHE_TTL,
    key_prefix="billing:expiring_subs",
    key_params=["days", "limit", "tenant_id"],
    tier=CacheTier.L2_REDIS,
)
async def _get_expiring_subscriptions_cached(
    days: int,
    limit: int,
    tenant_id: str | None,
    session: AsyncSession,
) -> dict[str, Any]:
    """
    Cached helper function for expiring subscriptions query.
    """
    now = datetime.now(UTC)
    expiry_threshold = now + timedelta(days=days)

    query = (
        select(BillingSubscriptionTable)
        .where(
            and_(
                BillingSubscriptionTable.current_period_end <= expiry_threshold,
                BillingSubscriptionTable.current_period_end >= now,
                BillingSubscriptionTable.status.in_(["active", "trialing"]),
            )
        )
        .order_by(BillingSubscriptionTable.current_period_end.asc())
    )

    if tenant_id:
        query = query.where(BillingSubscriptionTable.tenant_id == tenant_id)

    query = query.limit(limit)

    result = await session.execute(query)
    scalars_result = result.scalars()
    if isawaitable(scalars_result):
        scalars_result = await scalars_result
    subscriptions = scalars_result.all()
    if isawaitable(subscriptions):
        subscriptions = await subscriptions

    subscription_items = []
    for sub in subscriptions:
        days_until_expiry = (sub.current_period_end - now).days
        subscription_items.append(
            {
                "subscription_id": sub.subscription_id,
                "tenant_id": getattr(sub, "tenant_id", tenant_id),
                "plan_id": sub.plan_id,
                "current_period_end": sub.current_period_end,
                "days_until_expiry": days_until_expiry,
                "status": sub.status,
                "cancel_at_period_end": sub.cancel_at_period_end,
            }
        )

    return {
        "subscriptions": subscription_items,
        "total_count": len(subscription_items),
        "days_threshold": days,
        "timestamp": now,
    }


# ============================================================================
# Billing Metrics Endpoint
# ============================================================================


@router.get("/metrics", response_model=BillingMetricsResponse)
async def get_billing_metrics(
    period_days: int = Query(default=30, ge=1, le=365, description="Time period in days"),
    session: AsyncSession = Depends(get_session_dependency),
    current_user: UserInfo = Depends(require_permission("billing.metrics.view")),
) -> BillingMetricsResponse:
    """
    Get comprehensive billing metrics overview with Redis caching.

    Returns MRR, ARR, subscription counts, invoice statistics, and payment metrics
    for the specified time period with tenant isolation.

    **Caching**: Results cached for 5 minutes per tenant/period combination.
    **Required Permission**: billing.metrics.view
    """
    tenant_id = getattr(current_user, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(
            status_code=400,
            detail="Tenant context is required",
        )
    enforce_tenant_access(tenant_id, current_user)

    try:
        # Use cached helper function
        metrics_data = await _get_billing_metrics_cached(
            period_days=period_days,
            tenant_id=tenant_id,
            session=session,
        )

        return BillingMetricsResponse(**metrics_data)

    except Exception as e:
        logger.error("Failed to fetch billing metrics", error=str(e), exc_info=True)
        # Return safe defaults on error
        return BillingMetricsResponse(
            mrr=0.0,
            arr=0.0,
            active_subscriptions=0,
            total_invoices=0,
            paid_invoices=0,
            overdue_invoices=0,
            total_payments=0,
            successful_payments=0,
            failed_payments=0,
            total_payment_amount=0.0,
            period=f"{period_days}d",
            timestamp=datetime.now(UTC),
        )


# ============================================================================
# Payment List Endpoint
# ============================================================================


@router.get("/payments", response_model=PaymentListResponse)
async def get_recent_payments(
    limit: int = Query(
        default=50, ge=1, le=500, description="Maximum number of payments to return"
    ),
    offset: int = Query(default=0, ge=0, description="Number of payments to skip"),
    status: str | None = Query(default=None, description="Filter by payment status"),
    session: AsyncSession = Depends(get_session_dependency),
    current_user: UserInfo = Depends(require_permission("billing.payments.view")),
) -> PaymentListResponse:
    """
    Get list of recent payments with optional filtering.

    Returns paginated list of payments ordered by creation date (newest first)
    with tenant isolation.

    **Required Permission**: billing.payments.view
    """
    tenant_id = getattr(current_user, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(
            status_code=400,
            detail="Tenant context is required",
        )
    enforce_tenant_access(tenant_id, current_user)

    try:
        # Build query
        query = select(PaymentEntity).order_by(PaymentEntity.created_at.desc())

        if tenant_id:
            query = query.where(PaymentEntity.tenant_id == tenant_id)

        if status:
            query = query.where(PaymentEntity.status == status)

        # Get total count
        count_query = select(func.count(PaymentEntity.payment_id))
        if tenant_id:
            count_query = count_query.where(PaymentEntity.tenant_id == tenant_id)
        if status:
            count_query = count_query.where(PaymentEntity.status == status)

        count_result = await session.execute(count_query)
        total_count = count_result.scalar() or 0

        # Apply pagination
        query = query.limit(limit).offset(offset)

        # Execute query
        result = await session.execute(query)
        payment_entities = result.scalars().all()

        # Convert to response models
        payments = [
            PaymentListItem(
                payment_id=p.payment_id,
                amount=float(p.amount) / 100,  # Convert to major units
                currency=p.currency,
                status=p.status.value if hasattr(p.status, "value") else str(p.status),
                tenant_id=p.tenant_id,
                payment_method_type=(
                    p.payment_method_type.value
                    if hasattr(p.payment_method_type, "value")
                    else str(p.payment_method_type)
                ),
                provider=p.provider,
                created_at=p.created_at,
                processed_at=p.processed_at,
                failure_reason=p.failure_reason,
            )
            for p in payment_entities
        ]

        return PaymentListResponse(
            payments=payments,
            total_count=total_count,
            limit=limit,
            timestamp=datetime.now(UTC),
        )

    except Exception as e:
        logger.error("Failed to fetch recent payments", error=str(e), exc_info=True)
        # Return empty list on error
        return PaymentListResponse(
            payments=[],
            total_count=0,
            limit=limit,
            timestamp=datetime.now(UTC),
        )


# ============================================================================
# Expiring Subscriptions Endpoint
# ============================================================================


class ExpiringSubscriptionItem(BaseModel):
    """Individual subscription expiring soon."""

    model_config = ConfigDict(from_attributes=True)

    subscription_id: str
    tenant_id: str
    plan_id: str
    current_period_end: datetime
    days_until_expiry: int
    status: str
    cancel_at_period_end: bool


class ExpiringSubscriptionsResponse(BaseModel):
    """Expiring subscriptions response."""

    model_config = ConfigDict(from_attributes=True)

    subscriptions: list[ExpiringSubscriptionItem] = Field(
        description="List of expiring subscriptions"
    )
    total_count: int = Field(description="Total number of expiring subscriptions")
    days_threshold: int = Field(description="Days threshold used")
    timestamp: datetime = Field(description="Response generation timestamp")


@router.get(
    "/subscriptions/expiring",
    response_model=ExpiringSubscriptionsResponse,
    operation_id="list_expiring_subscriptions",
)
async def get_expiring_subscriptions(
    days: int = Query(
        default=30,
        ge=1,
        le=90,
        description="Number of days to look ahead for expiring subscriptions",
    ),
    limit: int = Query(
        default=50, ge=1, le=500, description="Maximum number of subscriptions to return"
    ),
    session: AsyncSession = Depends(get_session_dependency),
    current_user: UserInfo = Depends(require_permission("billing.metrics.view")),
) -> ExpiringSubscriptionsResponse:
    """
    Get subscriptions expiring within the specified number of days with Redis caching.

    Returns list of subscriptions that will expire soon, ordered by expiry date
    with tenant isolation.

    **Caching**: Results cached for 10 minutes per tenant/days/limit combination.
    **Required Permission**: billing.metrics.view
    """
    tenant_id = getattr(current_user, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(
            status_code=400,
            detail="Tenant context is required",
        )
    enforce_tenant_access(tenant_id, current_user)

    try:
        # Use cached helper function
        data = await _get_expiring_subscriptions_cached(
            days=days,
            limit=limit,
            tenant_id=tenant_id,
            session=session,
        )

        # Convert subscription items to Pydantic models
        subscription_items = [ExpiringSubscriptionItem(**item) for item in data["subscriptions"]]

        return ExpiringSubscriptionsResponse(
            subscriptions=subscription_items,
            total_count=data["total_count"],
            days_threshold=data["days_threshold"],
            timestamp=data["timestamp"],
        )

    except Exception as e:
        logger.error("Failed to fetch expiring subscriptions", error=str(e), exc_info=True)
        # Return empty list on error
        return ExpiringSubscriptionsResponse(
            subscriptions=[],
            total_count=0,
            days_threshold=days,
            timestamp=datetime.now(UTC),
        )


__all__ = ["router"]
