"""
Invoice API router with tenant support
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.auth.core import UserInfo
from dotmac.platform.auth.dependencies import get_current_user
from dotmac.platform.auth.rbac_dependencies import require_permission
from dotmac.platform.billing.core.enums import InvoiceStatus, PaymentStatus
from dotmac.platform.billing.core.exceptions import (
    InvalidInvoiceStatusError,
    InvoiceNotFoundError,
)
from dotmac.platform.billing.core.models import Invoice
from dotmac.platform.billing.dependencies import enforce_tenant_access, get_tenant_id
from dotmac.platform.billing.invoicing.service import InvoiceService
from dotmac.platform.database import get_async_session

# ============================================================================
# Request/Response Models
# ============================================================================


class CreateInvoiceRequest(BaseModel):
    """Create invoice request model"""

    model_config = ConfigDict()

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
    idempotency_key: str | None = Field(
        None, description="Idempotency key for duplicate prevention"
    )
    extra_data: dict[str, Any] = Field(default_factory=lambda: {})


class UpdateInvoiceRequest(BaseModel):
    """Update invoice request model"""

    model_config = ConfigDict()

    notes: str | None = Field(None, max_length=2000)
    internal_notes: str | None = Field(None, max_length=2000)
    due_date: datetime | None = None


class FinalizeInvoiceRequest(BaseModel):
    """Finalize invoice request model"""

    model_config = ConfigDict()

    send_email: bool = Field(True, description="Send invoice email to customer")


class VoidInvoiceRequest(BaseModel):
    """Void invoice request model"""

    model_config = ConfigDict()

    reason: str = Field(..., min_length=1, max_length=500, description="Reason for voiding")


class SendInvoiceEmailRequest(BaseModel):
    """Send invoice email request model"""

    model_config = ConfigDict()

    email: str | None = Field(
        None, description="Override recipient email (uses invoice billing_email if not provided)"
    )


class SendPaymentReminderRequest(BaseModel):
    """Send payment reminder request model"""

    model_config = ConfigDict()

    message: str | None = Field(None, max_length=1000, description="Custom reminder message")


class ApplyCreditRequest(BaseModel):
    """Apply credit to invoice request model"""

    model_config = ConfigDict()

    credit_amount: int = Field(..., gt=0, description="Credit amount in minor currency units")
    credit_application_id: str = Field(..., description="Credit application identifier")


class InvoiceListResponse(BaseModel):
    """Invoice list response model"""

    model_config = ConfigDict()

    invoices: list[Invoice]
    total_count: int
    has_more: bool


class PDFGenerationRequest(BaseModel):
    """PDF generation options."""

    model_config = ConfigDict()

    company_info: dict[str, Any] | None = Field(None, description="Company information")
    customer_info: dict[str, Any] | None = Field(None, description="Additional customer info")
    payment_instructions: str | None = Field(None, description="Payment instructions text")
    locale: str = Field("en_US", description="Locale for currency formatting")
    include_qr_code: bool = Field(False, description="Include QR code for payment")


class BatchPDFRequest(BaseModel):
    """Batch PDF generation request."""

    model_config = ConfigDict()

    invoice_ids: list[str] = Field(..., min_length=1, max_length=100)
    company_info: dict[str, Any] | None = None
    locale: str = Field("en_US")


class InvoiceDiscountRequest(BaseModel):
    """Apply discount to invoice."""

    model_config = ConfigDict()

    discount_percentage: float = Field(..., gt=0, le=100, description="Discount percentage")
    reason: str = Field(..., min_length=1, max_length=500)


# ============================================================================
# Router Definition
# ============================================================================

router = APIRouter(prefix="/invoices", tags=["Billing - Invoices"])


# ============================================================================
# Invoice Endpoints
# ============================================================================


@router.post(
    "",
    response_model=Invoice,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("billing.invoices.manage"))],
)
async def create_invoice(
    invoice_data: CreateInvoiceRequest,
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_async_session),
    current_user: UserInfo = Depends(get_current_user),
) -> Invoice:
    """Create a new invoice with tenant isolation. Requires billing.invoices.manage permission."""

    enforce_tenant_access(tenant_id, current_user)
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
        invoice.internal_notes = None
        return invoice
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create invoice: {str(e)}",
        )


@router.get(
    "",
    response_model=InvoiceListResponse,
    dependencies=[Depends(require_permission("billing.invoices.view"))],
)
async def list_invoices(
    tenant_id: str = Depends(get_tenant_id),
    customer_id: str | None = Query(None, description="Filter by customer ID"),
    status: InvoiceStatus | None = Query(None, description="Filter by status"),
    payment_status: PaymentStatus | None = Query(None, description="Filter by payment status"),
    start_date: datetime | None = Query(None, description="Filter by start date"),
    end_date: datetime | None = Query(None, description="Filter by end date"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of invoices to return"),
    offset: int = Query(0, ge=0, description="Number of invoices to skip"),
    db: AsyncSession = Depends(get_async_session),
    current_user: UserInfo = Depends(get_current_user),
) -> InvoiceListResponse:
    """List invoices with filtering and tenant isolation"""

    enforce_tenant_access(tenant_id, current_user)
    invoice_service = InvoiceService(db)

    try:
        invoices, total_count = await invoice_service.list_invoices_with_count(
            tenant_id=tenant_id,
            customer_id=customer_id,
            status=status,
            payment_status=payment_status,
            start_date=start_date,
            end_date=end_date,
            limit=limit + 1,  # Fetch one extra to check if there are more
            offset=offset,
        )
    except (AttributeError, TypeError):
        invoices = await invoice_service.list_invoices(
            tenant_id=tenant_id,
            customer_id=customer_id,
            status=status,
            payment_status=payment_status,
            start_date=start_date,
            end_date=end_date,
            limit=limit + 1,
            offset=offset,
        )
        total_count = len(invoices)

    has_more = len(invoices) > limit
    if has_more:
        invoices = invoices[:limit]

    for invoice in invoices:
        invoice.internal_notes = None

    return InvoiceListResponse(
        invoices=invoices,
        total_count=total_count,
        has_more=has_more,
    )

@router.get(
    "/{invoice_id}",
    response_model=Invoice,
    dependencies=[Depends(require_permission("billing.invoices.view"))],
)
async def get_invoice(
    invoice_id: str,
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_async_session),
    current_user: UserInfo = Depends(get_current_user),
) -> Invoice:
    """Get invoice by ID with tenant isolation"""

    enforce_tenant_access(tenant_id, current_user)
    invoice_service = InvoiceService(db)

    invoice = await invoice_service.get_invoice(tenant_id, invoice_id)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")

    invoice.internal_notes = None
    return invoice


@router.post(
    "/{invoice_id}/finalize",
    response_model=Invoice,
    dependencies=[Depends(require_permission("billing.invoices.manage"))],
)
async def finalize_invoice(
    invoice_id: str,
    finalize_data: FinalizeInvoiceRequest,
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_async_session),
    current_user: UserInfo = Depends(get_current_user),
) -> Invoice:
    """Finalize a draft invoice to open status. Requires billing.invoices.manage permission."""

    enforce_tenant_access(tenant_id, current_user)
    invoice_service = InvoiceService(db)

    try:
        invoice = await invoice_service.finalize_invoice(tenant_id, invoice_id)
        invoice.internal_notes = None
        return invoice
    except InvoiceNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    except InvalidInvoiceStatusError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{invoice_id}/void",
    response_model=Invoice,
    dependencies=[Depends(require_permission("billing.invoices.manage"))],
)
async def void_invoice(
    invoice_id: str,
    void_data: VoidInvoiceRequest,
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_async_session),
    current_user: UserInfo = Depends(get_current_user),
) -> Invoice:
    """Void an invoice. Requires billing.invoices.manage permission."""

    enforce_tenant_access(tenant_id, current_user)
    invoice_service = InvoiceService(db)

    try:
        invoice = await invoice_service.void_invoice(
            tenant_id, invoice_id, reason=void_data.reason, voided_by=current_user.user_id
        )
        invoice.internal_notes = None
        return invoice
    except InvoiceNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    except InvalidInvoiceStatusError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{invoice_id}/send",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("billing.invoices.manage"))],
)
async def send_invoice_email(
    invoice_id: str,
    send_data: SendInvoiceEmailRequest,
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_async_session),
    current_user: UserInfo = Depends(get_current_user),
) -> dict[str, Any]:
    """Send invoice email to customer"""

    enforce_tenant_access(tenant_id, current_user)
    invoice_service = InvoiceService(db)

    try:
        success = await invoice_service.send_invoice_email(
            tenant_id, invoice_id, recipient_email=send_data.email
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send invoice email",
            )

        # Get invoice to return details
        invoice = await invoice_service.get_invoice(tenant_id, invoice_id)
        recipient = send_data.email or (invoice.billing_email if invoice else "unknown")

        return {
            "success": True,
            "message": f"Invoice email sent successfully to {recipient}",
            "invoice_id": invoice_id,
        }
    except InvoiceNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")


@router.post(
    "/{invoice_id}/remind",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("billing.invoices.manage"))],
)
async def send_payment_reminder(
    invoice_id: str,
    reminder_data: SendPaymentReminderRequest,
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_async_session),
    current_user: UserInfo = Depends(get_current_user),
) -> dict[str, Any]:
    """Send payment reminder for invoice"""

    enforce_tenant_access(tenant_id, current_user)
    invoice_service = InvoiceService(db)

    try:
        success = await invoice_service.send_payment_reminder(
            tenant_id, invoice_id, custom_message=reminder_data.message
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send payment reminder",
            )

        # Get invoice to return details
        invoice = await invoice_service.get_invoice(tenant_id, invoice_id)
        invoice_number = invoice.invoice_number if invoice else invoice_id

        return {
            "success": True,
            "message": f"Payment reminder sent successfully for invoice {invoice_number}",
            "invoice_id": invoice_id,
        }
    except InvoiceNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    except InvalidInvoiceStatusError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{invoice_id}/pdf",
    dependencies=[Depends(require_permission("billing.invoices.download"))],
)
async def generate_invoice_pdf(
    invoice_id: str,
    pdf_options: PDFGenerationRequest,
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_async_session),
    current_user: UserInfo = Depends(get_current_user),
) -> Response:
    """Generate PDF for an invoice."""
    enforce_tenant_access(tenant_id, current_user)
    service = InvoiceService(db)

    try:
        pdf_bytes = await service.generate_invoice_pdf(
            tenant_id=tenant_id,
            invoice_id=invoice_id,
            company_info=pdf_options.company_info,
            customer_info=pdf_options.customer_info,
            payment_instructions=pdf_options.payment_instructions,
            locale=pdf_options.locale,
        )

        invoice = await service.get_invoice(tenant_id, invoice_id)
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invoice {invoice_id} not found",
            )
        filename = f"invoice_{invoice.invoice_number or invoice.invoice_id}.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF: {str(e)}",
        )


@router.get(
    "/{invoice_id}/pdf/preview",
    dependencies=[Depends(require_permission("billing.invoices.download"))],
)
async def preview_invoice_pdf(
    invoice_id: str,
    locale: str = Query("en_US"),
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_async_session),
    current_user: UserInfo = Depends(get_current_user),
) -> Response:
    """Preview invoice PDF in browser."""
    enforce_tenant_access(tenant_id, current_user)
    service = InvoiceService(db)

    try:
        pdf_bytes = await service.generate_invoice_pdf(
            tenant_id=tenant_id,
            invoice_id=invoice_id,
            locale=locale,
        )

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "inline"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF preview: {str(e)}",
        )


@router.post(
    "/batch/pdf",
    dependencies=[Depends(require_permission("billing.invoices.download"))],
)
async def generate_batch_pdfs(
    batch_request: BatchPDFRequest,
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_async_session),
    current_user: UserInfo = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Generate PDFs for multiple invoices.
    """
    enforce_tenant_access(tenant_id, current_user)
    service = InvoiceService(db)

    import os
    import tempfile

    temp_dir = tempfile.mkdtemp(prefix="invoice_batch_")

    try:
        output_paths = await service.generate_batch_invoices_pdf(
            tenant_id=tenant_id,
            invoice_ids=batch_request.invoice_ids,
            output_dir=temp_dir,
            company_info=batch_request.company_info,
            locale=batch_request.locale,
        )

        return {
            "success": True,
            "count": len(output_paths),
            "message": f"Generated {len(output_paths)} PDF files",
            "temp_directory": temp_dir,
            "files": [os.path.basename(path) for path in output_paths],
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate batch PDFs: {str(e)}",
        )


@router.post(
    "/{invoice_id}/discount",
    response_model=Invoice,
    dependencies=[Depends(require_permission("billing.invoices.manage"))],
)
async def apply_discount(
    invoice_id: str,
    discount_request: InvoiceDiscountRequest,
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_async_session),
    current_user: UserInfo = Depends(get_current_user),
) -> Invoice:
    """Apply a percentage discount to an invoice."""
    enforce_tenant_access(tenant_id, current_user)
    service = InvoiceService(db)

    try:
        await service.apply_percentage_discount(
            tenant_id=tenant_id,
            invoice_id=invoice_id,
            discount_percentage=discount_request.discount_percentage,
            reason=discount_request.reason,
        )
        invoice = await service.get_invoice(tenant_id, invoice_id)
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Invoice {invoice_id} not found"
            )
        invoice.internal_notes = None
        return invoice
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply discount: {str(e)}",
        )


@router.post(
    "/{invoice_id}/recalculate-tax",
    response_model=Invoice,
    dependencies=[Depends(require_permission("billing.invoices.manage"))],
)
async def recalculate_tax(
    invoice_id: str,
    tax_jurisdiction: str,
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_async_session),
    current_user: UserInfo = Depends(get_current_user),
) -> Invoice:
    """Recalculate tax for an invoice based on jurisdiction."""
    enforce_tenant_access(tenant_id, current_user)
    service = InvoiceService(db)

    tax_rates = {
        "default": 10.0,
        "CA": 8.75,
        "NY": 8.0,
        "TX": 6.25,
    }

    try:
        await service.calculate_tax_for_jurisdiction(
            tenant_id=tenant_id,
            invoice_id=invoice_id,
            tax_jurisdiction=tax_jurisdiction,
            tax_rates={"default": tax_rates.get(tax_jurisdiction, 10.0)},
        )
        invoice = await service.get_invoice(tenant_id, invoice_id)
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Invoice {invoice_id} not found"
            )
        invoice.internal_notes = None
        return invoice
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to recalculate tax: {str(e)}",
        )


@router.post(
    "/{invoice_id}/mark-paid",
    response_model=Invoice,
    dependencies=[Depends(require_permission("billing.invoices.manage"))],
)
async def mark_invoice_paid(
    invoice_id: str,
    tenant_id: str = Depends(get_tenant_id),
    payment_id: str | None = Query(None, description="Associated payment ID"),
    db: AsyncSession = Depends(get_async_session),
    current_user: UserInfo = Depends(get_current_user),
) -> Invoice:
    """Mark invoice as paid"""

    enforce_tenant_access(tenant_id, current_user)
    invoice_service = InvoiceService(db)

    try:
        invoice = await invoice_service.mark_invoice_paid(
            tenant_id, invoice_id, payment_id=payment_id
        )
        invoice.internal_notes = None
        return invoice
    except InvoiceNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")


@router.post(
    "/{invoice_id}/apply-credit",
    response_model=Invoice,
    dependencies=[Depends(require_permission("billing.invoices.manage"))],
)
async def apply_credit_to_invoice(
    invoice_id: str,
    credit_data: ApplyCreditRequest,
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_async_session),
    current_user: UserInfo = Depends(get_current_user),
) -> Invoice:
    """Apply credit to invoice"""

    enforce_tenant_access(tenant_id, current_user)
    invoice_service = InvoiceService(db)

    try:
        invoice = await invoice_service.apply_credit_to_invoice(
            tenant_id, invoice_id, credit_data.credit_amount, credit_data.credit_application_id
        )
        invoice.internal_notes = None
        return invoice
    except InvoiceNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")


@router.post(
    "/check-overdue",
    response_model=list[Invoice],
    dependencies=[Depends(require_permission("billing.invoices.manage"))],
)
async def check_overdue_invoices(
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_async_session),
    current_user: UserInfo = Depends(get_current_user),
) -> list[Invoice]:
    """Check for overdue invoices and update their status"""

    enforce_tenant_access(tenant_id, current_user)
    invoice_service = InvoiceService(db)

    overdue_invoices: list[Invoice] = await invoice_service.check_overdue_invoices(tenant_id)
    for invoice in overdue_invoices:
        invoice.internal_notes = None
    return overdue_invoices
