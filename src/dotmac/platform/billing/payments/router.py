"""Payment router for billing management."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.auth.core import UserInfo
from dotmac.platform.auth.dependencies import get_current_user
from dotmac.platform.auth.rbac_dependencies import require_permission
from dotmac.platform.billing.core.entities import PaymentEntity
from dotmac.platform.billing.core.enums import PaymentMethodType, PaymentStatus
from dotmac.platform.contacts.models import Contact
from dotmac.platform.billing.core.exceptions import PaymentError
from dotmac.platform.billing.core.models import Payment
from dotmac.platform.billing.dependencies import enforce_tenant_access, get_tenant_id
from dotmac.platform.billing.payments.service import PaymentService
from dotmac.platform.db import get_session_dependency

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/payments", tags=["Billing - Payments"])


class FailedPaymentsSummary(BaseModel):
    """Summary of failed payments."""

    model_config = ConfigDict()

    count: int
    total_amount: float
    oldest_failure: datetime | None = None
    newest_failure: datetime | None = None


@router.get("/failed", response_model=FailedPaymentsSummary)
async def get_failed_payments(
    session: AsyncSession = Depends(get_session_dependency),
    current_user: UserInfo = Depends(require_permission("billing.payments.view")),
    tenant_id: str = Depends(get_tenant_id),
) -> FailedPaymentsSummary:
    """
    Get summary of failed payments for monitoring.

    Returns count and total amount of payments that have failed for the current tenant.
    """
    try:
        effective_tenant_id: str | None = tenant_id if isinstance(tenant_id, str) else None
        if not effective_tenant_id:
            effective_tenant_id = getattr(current_user, "tenant_id", None)

        if not effective_tenant_id:
            return FailedPaymentsSummary(
                count=0,
                total_amount=0.0,
                oldest_failure=None,
                newest_failure=None,
            )

        enforce_tenant_access(effective_tenant_id, current_user)

        # Query failed payments from last 30 days for current tenant only
        thirty_days_ago = datetime.now(UTC) - timedelta(days=30)

        # Count and sum failed payments scoped by tenant_id
        # Use .value to compare enum as string to avoid PostgreSQL ENUM type mismatch
        query = select(
            func.count(PaymentEntity.payment_id).label("count"),
            func.sum(PaymentEntity.amount).label("total_amount"),
            func.min(PaymentEntity.created_at).label("oldest"),
            func.max(PaymentEntity.created_at).label("newest"),
        ).where(
            PaymentEntity.status == PaymentStatus.FAILED.value,
            PaymentEntity.created_at >= thirty_days_ago,
            PaymentEntity.tenant_id == effective_tenant_id,  # CRITICAL: Scope by tenant
        )

        result = await session.execute(query)
        row = result.one()
        row_mapping = row._mapping

        count_value = int(row_mapping.get("count") or 0)
        # FIXED: Convert from minor units (cents) to major units (dollars/naira)
        # PaymentEntity.amount is stored in cents, so ₦42.50 is stored as 4250
        # Without conversion, would display as "4250.0" instead of "42.50"
        total_amount_minor = float(row_mapping.get("total_amount") or 0)
        total_amount_value = total_amount_minor / 100.0
        oldest = row_mapping.get("oldest")
        newest = row_mapping.get("newest")

        return FailedPaymentsSummary(
            count=count_value,
            total_amount=total_amount_value,
            oldest_failure=oldest,
            newest_failure=newest,
        )

    except Exception as e:
        logger.error("Failed to fetch failed payments", error=str(e), exc_info=True)
        # Return empty summary on error
        return FailedPaymentsSummary(
            count=0,
            total_amount=0.0,
        )


# ========================================
# Request/Response Models
# ========================================


class RecordOfflinePaymentRequest(BaseModel):
    """Request to record an offline payment."""

    model_config = ConfigDict()

    customer_id: str = Field(..., description="Customer ID to record payment for")
    amount: Decimal = Field(..., gt=0, description="Payment amount in major currency units")
    currency: str = Field("USD", min_length=3, max_length=3, description="Currency code (ISO 4217)")
    payment_method: str = Field(
        ...,
        description="Payment method: cash, check, bank_transfer, or wire_transfer",
    )
    invoice_id: str | None = Field(None, description="Optional invoice to apply payment to")
    reference_number: str | None = Field(None, description="Reference number (check #, wire ID)")
    notes: str | None = Field(None, description="Additional notes about the payment")
    payment_date: datetime | None = Field(None, description="Date payment was received")


class PaymentResponse(BaseModel):
    """Payment response model."""

    model_config = ConfigDict()

    id: str
    payment_id: str
    customer_id: str
    customer_name: str | None = None
    amount: int = Field(..., description="Amount in minor currency units (cents)")
    amount_display: float = Field(..., description="Amount in major currency units")
    currency: str
    status: str
    method: str | None = None
    payment_method_type: str
    payment_method_details: dict[str, Any] = Field(default_factory=dict)
    provider: str
    provider_payment_id: str | None = None
    reference_number: str | None = None
    notes: str | None = None
    invoice_id: str | None = None
    invoice_number: str | None = None
    invoice_ids: list[str] = Field(default_factory=list)
    payment_date: datetime | None = None
    created_at: datetime | None = None
    processed_at: datetime | None = None

    @classmethod
    def from_payment(
        cls, payment: Payment, *, customer_name: str | None = None
    ) -> "PaymentResponse":
        """Create response from Payment model."""
        payment_method = payment.payment_method_details.get("payment_method")
        reference_number = payment.payment_method_details.get("reference_number")
        notes = payment.extra_data.get("notes")
        invoice_id = None
        if payment.invoice_ids:
            invoice_id = payment.invoice_ids[0]
        elif isinstance(payment.extra_data.get("invoice_id"), str):
            invoice_id = payment.extra_data.get("invoice_id")
        invoice_number = payment.extra_data.get("invoice_number")
        payment_date = payment.processed_at or payment.created_at

        return cls(
            id=payment.payment_id,
            payment_id=payment.payment_id,
            customer_id=payment.customer_id,
            customer_name=customer_name or payment.extra_data.get("customer_name"),
            amount=payment.amount,
            amount_display=payment.amount / 100.0,
            currency=payment.currency,
            status=payment.status.value if hasattr(payment.status, "value") else str(payment.status),
            method=payment_method or (
                payment.payment_method_type.value
                if hasattr(payment.payment_method_type, "value")
                else str(payment.payment_method_type)
            ),
            payment_method_type=(
                payment.payment_method_type.value
                if hasattr(payment.payment_method_type, "value")
                else str(payment.payment_method_type)
            ),
            payment_method_details=payment.payment_method_details,
            provider=payment.provider,
            provider_payment_id=payment.provider_payment_id,
            reference_number=reference_number,
            notes=notes,
            invoice_id=invoice_id,
            invoice_number=invoice_number,
            invoice_ids=payment.invoice_ids,
            payment_date=payment_date,
            created_at=payment.created_at,
            processed_at=payment.processed_at,
        )


class PaymentListResponse(BaseModel):
    """Paginated payment list response."""

    model_config = ConfigDict()

    payments: list[PaymentResponse]
    total_count: int
    page: int
    page_size: int
    has_more: bool


# ========================================
# Endpoints
# ========================================


@router.post("/offline", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def record_offline_payment(
    request: RecordOfflinePaymentRequest,
    session: AsyncSession = Depends(get_session_dependency),
    current_user: UserInfo = Depends(require_permission("billing.payments.create")),
    tenant_id: str = Depends(get_tenant_id),
) -> PaymentResponse:
    """
    Record an offline payment (cash, check, bank transfer, etc.).

    Use this endpoint to record payments received outside the platform,
    such as checks, wire transfers, or cash payments.
    """
    try:
        effective_tenant_id = tenant_id if isinstance(tenant_id, str) else None
        if not effective_tenant_id:
            effective_tenant_id = getattr(current_user, "tenant_id", None)

        if not effective_tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant ID is required",
            )

        enforce_tenant_access(effective_tenant_id, current_user)

        service = PaymentService(session)
        payment = await service.record_offline_payment(
            tenant_id=effective_tenant_id,
            customer_id=request.customer_id,
            amount=request.amount,
            currency=request.currency,
            payment_method=request.payment_method,
            invoice_id=request.invoice_id,
            reference_number=request.reference_number,
            notes=request.notes,
            payment_date=request.payment_date,
        )

        return PaymentResponse.from_payment(payment)

    except PaymentError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Failed to record offline payment", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record payment",
        )


@router.get("", response_model=PaymentListResponse)
async def list_payments(
    customer_id: str | None = Query(None, description="Filter by customer ID"),
    payment_status: str | None = Query(None, alias="status", description="Filter by status"),
    payment_method: str | None = Query(None, alias="method", description="Filter by method"),
    start_date: datetime | None = Query(None, description="Filter by start date"),
    end_date: datetime | None = Query(None, description="Filter by end date"),
    search: str | None = Query(None, description="Search by payment ID or provider ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    session: AsyncSession = Depends(get_session_dependency),
    current_user: UserInfo = Depends(require_permission("billing.payments.view")),
    tenant_id: str = Depends(get_tenant_id),
) -> PaymentListResponse:
    """
    List payments with optional filtering and pagination.
    """
    try:
        effective_tenant_id = tenant_id if isinstance(tenant_id, str) else None
        if not effective_tenant_id:
            effective_tenant_id = getattr(current_user, "tenant_id", None)

        if not effective_tenant_id:
            return PaymentListResponse(
                payments=[],
                total_count=0,
                page=page,
                page_size=page_size,
                has_more=False,
            )

        enforce_tenant_access(effective_tenant_id, current_user)

        # Build query
        query = select(PaymentEntity).where(PaymentEntity.tenant_id == effective_tenant_id)

        if customer_id:
            query = query.where(PaymentEntity.customer_id == customer_id)

        if payment_status:
            try:
                status_enum = PaymentStatus(payment_status)
                # Use .value to compare as string to avoid PostgreSQL ENUM type mismatch
                query = query.where(PaymentEntity.status == status_enum.value)
            except ValueError:
                pass  # Ignore invalid status filter

        if payment_method:
            method_value = payment_method
            if method_value == "bank_transfer":
                method_value = PaymentMethodType.BANK_ACCOUNT.value
            try:
                method_enum = PaymentMethodType(method_value)
                # Use .value to compare as string to avoid PostgreSQL ENUM type mismatch
                query = query.where(PaymentEntity.payment_method_type == method_enum.value)
            except ValueError:
                pass  # Ignore invalid method filter

        if start_date:
            query = query.where(PaymentEntity.created_at >= start_date)

        if end_date:
            query = query.where(PaymentEntity.created_at <= end_date)

        if search:
            like_pattern = f"%{search}%"
            query = query.where(
                PaymentEntity.payment_id.ilike(like_pattern)
                | PaymentEntity.customer_id.ilike(like_pattern)
                | PaymentEntity.provider_payment_id.ilike(like_pattern)
            )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total_count = total_result.scalar() or 0

        # Apply pagination and ordering
        query = query.order_by(PaymentEntity.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await session.execute(query)
        payment_entities = result.scalars().all()

        # Convert to response models
        service = PaymentService(session)
        payments = []
        customer_ids = {entity.customer_id for entity in payment_entities if entity.customer_id}
        customer_names: dict[str, str] = {}
        if customer_ids:
            resolved_ids = []
            for customer_id in customer_ids:
                try:
                    resolved_ids.append(UUID(customer_id))
                except (ValueError, TypeError):
                    continue
            if resolved_ids:
                customer_result = await session.execute(
                    select(Contact.id, Contact.display_name)
                    .where(Contact.tenant_id == effective_tenant_id)
                    .where(Contact.id.in_(resolved_ids))
                )
                customer_names = {
                    str(row.id): row.display_name
                    for row in customer_result.all()
                    if row.display_name
                }
        for entity in payment_entities:
            payment = service._payment_from_entity(entity)
            payments.append(
                PaymentResponse.from_payment(
                    payment,
                    customer_name=customer_names.get(payment.customer_id),
                )
            )

        return PaymentListResponse(
            payments=payments,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_more=(page * page_size) < total_count,
        )

    except Exception as e:
        logger.error("Failed to list payments", error=str(e), exc_info=True)
        return PaymentListResponse(
            payments=[],
            total_count=0,
            page=page,
            page_size=page_size,
            has_more=False,
        )


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: str,
    session: AsyncSession = Depends(get_session_dependency),
    current_user: UserInfo = Depends(require_permission("billing.payments.view")),
    tenant_id: str = Depends(get_tenant_id),
) -> PaymentResponse:
    """
    Get a specific payment by ID.
    """
    try:
        effective_tenant_id = tenant_id if isinstance(tenant_id, str) else None
        if not effective_tenant_id:
            effective_tenant_id = getattr(current_user, "tenant_id", None)

        if not effective_tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant ID is required",
            )

        enforce_tenant_access(effective_tenant_id, current_user)

        service = PaymentService(session)
        payment = await service.get_payment(tenant_id=effective_tenant_id, payment_id=payment_id)

        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payment {payment_id} not found",
            )

        customer_name = None
        try:
            customer_uuid = UUID(payment.customer_id)
            customer_result = await session.execute(
                select(Contact.display_name)
                .where(Contact.tenant_id == effective_tenant_id)
                .where(Contact.id == customer_uuid)
            )
            customer_name = customer_result.scalar_one_or_none()
        except (ValueError, TypeError):
            customer_name = None

        return PaymentResponse.from_payment(payment, customer_name=customer_name)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get payment", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get payment",
        )


__all__ = ["router"]
