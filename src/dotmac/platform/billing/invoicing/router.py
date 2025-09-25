"""
Invoice API router with tenant support
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.auth.dependencies import get_current_user
from dotmac.platform.billing.core.enums import InvoiceStatus, PaymentStatus
from dotmac.platform.billing.core.exceptions import (
    InvalidInvoiceStatusError,
    InvoiceNotFoundError,
)
from dotmac.platform.billing.core.models import Invoice, InvoiceLineItem
from dotmac.platform.billing.invoicing.service import InvoiceService
from dotmac.platform.database import get_async_session


# ============================================================================
# Request/Response Models
# ============================================================================


class CreateInvoiceRequest(BaseModel):
    """Create invoice request model"""

    customer_id: str = Field(..., description="Customer identifier")
    billing_email: str = Field(..., description="Billing email address")
    billing_address: dict[str, str] = Field(..., description="Billing address")
    line_items: list[dict[str, Any]] = Field(..., min_length=1, description="Invoice line items")
    currency: str = Field("USD", min_length=3, max_length=3)
    due_days: int | None = Field(None, ge=1, le=365)
    due_date: datetime | None = None
    notes: str | None = Field(None, max_length=2000)
    internal_notes: str | None = Field(None, max_length=2000)
    subscription_id: str | None = None
    idempotency_key: str | None = Field(None, description="Idempotency key for duplicate prevention")
    extra_data: dict[str, Any] = Field(default_factory=dict)


class UpdateInvoiceRequest(BaseModel):
    """Update invoice request model"""

    notes: str | None = Field(None, max_length=2000)
    internal_notes: str | None = Field(None, max_length=2000)
    due_date: datetime | None = None


class FinalizeInvoiceRequest(BaseModel):
    """Finalize invoice request model"""

    send_email: bool = Field(True, description="Send invoice email to customer")


class VoidInvoiceRequest(BaseModel):
    """Void invoice request model"""

    reason: str = Field(..., min_length=1, max_length=500, description="Reason for voiding")


class ApplyCreditRequest(BaseModel):
    """Apply credit to invoice request model"""

    credit_amount: int = Field(..., gt=0, description="Credit amount in minor currency units")
    credit_application_id: str = Field(..., description="Credit application identifier")


class InvoiceListResponse(BaseModel):
    """Invoice list response model"""

    invoices: list[Invoice]
    total_count: int
    has_more: bool


# ============================================================================
# Router Definition
# ============================================================================

router = APIRouter(prefix="/invoices", tags=["invoices"])


def get_tenant_id_from_request(request: Request) -> str:
    """Extract tenant ID from request"""
    # Check request state (set by middleware)
    if hasattr(request.state, "tenant_id"):
        return request.state.tenant_id

    # Check header
    tenant_id = request.headers.get("X-Tenant-ID")
    if tenant_id:
        return tenant_id

    # Check query parameter
    tenant_id = request.query_params.get("tenant_id")
    if tenant_id:
        return tenant_id

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Tenant ID is required. Provide via X-Tenant-ID header or tenant_id query param.",
    )


# ============================================================================
# Invoice Endpoints
# ============================================================================


@router.post("", response_model=Invoice, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    invoice_data: CreateInvoiceRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user),
) -> Invoice:
    """Create a new invoice with tenant isolation"""

    tenant_id = get_tenant_id_from_request(request)
    invoice_service = InvoiceService(db)

    try:
        invoice = await invoice_service.create_invoice(
            tenant_id=tenant_id,
            customer_id=invoice_data.customer_id,
            billing_email=invoice_data.billing_email,
            billing_address=invoice_data.billing_address,
            line_items=invoice_data.line_items,
            currency=invoice_data.currency,
            due_days=invoice_data.due_days,
            due_date=invoice_data.due_date,
            notes=invoice_data.notes,
            internal_notes=invoice_data.internal_notes,
            subscription_id=invoice_data.subscription_id,
            created_by=current_user.user_id,
            idempotency_key=invoice_data.idempotency_key,
            extra_data=invoice_data.extra_data,
        )
        return invoice
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create invoice: {str(e)}"
        )


@router.get("/{invoice_id}", response_model=Invoice)
async def get_invoice(
    invoice_id: str, request: Request, db: AsyncSession = Depends(get_async_session), current_user=Depends(get_current_user)
) -> Invoice:
    """Get invoice by ID with tenant isolation"""

    tenant_id = get_tenant_id_from_request(request)
    invoice_service = InvoiceService(db)

    invoice = await invoice_service.get_invoice(tenant_id, invoice_id)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")

    return invoice


@router.get("", response_model=InvoiceListResponse)
async def list_invoices(
    request: Request,
    customer_id: str | None = Query(None, description="Filter by customer ID"),
    status: InvoiceStatus | None = Query(None, description="Filter by status"),
    payment_status: PaymentStatus | None = Query(None, description="Filter by payment status"),
    start_date: datetime | None = Query(None, description="Filter by start date"),
    end_date: datetime | None = Query(None, description="Filter by end date"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of invoices to return"),
    offset: int = Query(0, ge=0, description="Number of invoices to skip"),
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user),
) -> InvoiceListResponse:
    """List invoices with filtering and tenant isolation"""

    tenant_id = get_tenant_id_from_request(request)
    invoice_service = InvoiceService(db)

    invoices = await invoice_service.list_invoices(
        tenant_id=tenant_id,
        customer_id=customer_id,
        status=status,
        payment_status=payment_status,
        start_date=start_date,
        end_date=end_date,
        limit=limit + 1,  # Fetch one extra to check if there are more
        offset=offset,
    )

    has_more = len(invoices) > limit
    if has_more:
        invoices = invoices[:limit]

    return InvoiceListResponse(
        invoices=invoices,
        total_count=len(invoices),
        has_more=has_more,
    )


@router.post("/{invoice_id}/finalize", response_model=Invoice)
async def finalize_invoice(
    invoice_id: str,
    finalize_data: FinalizeInvoiceRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user),
) -> Invoice:
    """Finalize a draft invoice to open status"""

    tenant_id = get_tenant_id_from_request(request)
    invoice_service = InvoiceService(db)

    try:
        invoice = await invoice_service.finalize_invoice(tenant_id, invoice_id)
        return invoice
    except InvoiceNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    except InvalidInvoiceStatusError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{invoice_id}/void", response_model=Invoice)
async def void_invoice(
    invoice_id: str,
    void_data: VoidInvoiceRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user),
) -> Invoice:
    """Void an invoice"""

    tenant_id = get_tenant_id_from_request(request)
    invoice_service = InvoiceService(db)

    try:
        invoice = await invoice_service.void_invoice(
            tenant_id, invoice_id, reason=void_data.reason, voided_by=current_user.user_id
        )
        return invoice
    except InvoiceNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    except InvalidInvoiceStatusError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{invoice_id}/mark-paid", response_model=Invoice)
async def mark_invoice_paid(
    invoice_id: str,
    request: Request,
    payment_id: str | None = Query(None, description="Associated payment ID"),
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user),
) -> Invoice:
    """Mark invoice as paid"""

    tenant_id = get_tenant_id_from_request(request)
    invoice_service = InvoiceService(db)

    try:
        invoice = await invoice_service.mark_invoice_paid(tenant_id, invoice_id, payment_id=payment_id)
        return invoice
    except InvoiceNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")


@router.post("/{invoice_id}/apply-credit", response_model=Invoice)
async def apply_credit_to_invoice(
    invoice_id: str,
    credit_data: ApplyCreditRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user),
) -> Invoice:
    """Apply credit to invoice"""

    tenant_id = get_tenant_id_from_request(request)
    invoice_service = InvoiceService(db)

    try:
        invoice = await invoice_service.apply_credit_to_invoice(
            tenant_id, invoice_id, credit_data.credit_amount, credit_data.credit_application_id
        )
        return invoice
    except InvoiceNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")


@router.post("/check-overdue", response_model=list[Invoice])
async def check_overdue_invoices(
    request: Request, db: AsyncSession = Depends(get_async_session), current_user=Depends(get_current_user)
) -> list[Invoice]:
    """Check for overdue invoices and update their status"""

    tenant_id = get_tenant_id_from_request(request)
    invoice_service = InvoiceService(db)

    overdue_invoices = await invoice_service.check_overdue_invoices(tenant_id)
    return overdue_invoices