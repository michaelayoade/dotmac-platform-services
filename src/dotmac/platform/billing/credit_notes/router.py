"""
Credit note API router
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.auth.dependencies import get_current_user
from dotmac.platform.billing.core.enums import CreditNoteStatus, CreditReason
from dotmac.platform.billing.core.exceptions import (
    CreditNoteNotFoundError,
    InvalidCreditNoteStatusError,
    InsufficientCreditError,
)
from dotmac.platform.billing.core.models import CreditNote
from dotmac.platform.billing.credit_notes.service import CreditNoteService
from dotmac.platform.billing.invoicing.router import get_tenant_id_from_request
from dotmac.platform.database import get_async_session

# ============================================================================
# Request/Response Models
# ============================================================================


class CreateCreditNoteRequest(BaseModel):
    """Create credit note request"""

    invoice_id: str = Field(..., description="Invoice to credit")
    reason: CreditReason = Field(..., description="Reason for credit")
    line_items: List[dict] = Field(..., min_length=1, description="Credit line items")
    notes: Optional[str] = Field(None, max_length=2000, description="Customer-visible notes")
    internal_notes: Optional[str] = Field(None, max_length=2000, description="Internal notes")
    auto_apply: bool = Field(True, description="Auto-apply credit to invoice")


class IssueCreditNoteRequest(BaseModel):
    """Issue credit note request"""

    send_notification: bool = Field(True, description="Send notification to customer")


class VoidCreditNoteRequest(BaseModel):
    """Void credit note request"""

    reason: str = Field(..., min_length=1, max_length=500, description="Void reason")


class ApplyCreditRequest(BaseModel):
    """Apply credit request"""

    invoice_id: str = Field(..., description="Invoice to apply credit to")
    amount: int = Field(..., gt=0, description="Amount to apply in minor currency units")


class CreditNoteListResponse(BaseModel):
    """Credit note list response"""

    credit_notes: List[CreditNote]
    total_count: int
    has_more: bool
    total_available_credit: int = Field(0, description="Total available credit in minor units")


# ============================================================================
# Router Definition
# ============================================================================

router = APIRouter(prefix="/credit-notes", tags=["credit-notes"])


# ============================================================================
# Credit Note Endpoints
# ============================================================================


@router.post("", response_model=CreditNote, status_code=status.HTTP_201_CREATED)
async def create_credit_note(
    credit_data: CreateCreditNoteRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user),
) -> CreditNote:
    """Create a new credit note"""

    tenant_id = get_tenant_id_from_request(request)
    service = CreditNoteService(db)

    try:
        credit_note = await service.create_credit_note(
            tenant_id=tenant_id,
            invoice_id=credit_data.invoice_id,
            reason=credit_data.reason,
            line_items=credit_data.line_items,
            notes=credit_data.notes,
            internal_notes=credit_data.internal_notes,
            created_by=current_user.user_id,
            auto_apply=credit_data.auto_apply,
        )
        return credit_note
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create credit note: {str(e)}",
        )


@router.get("/{credit_note_id}", response_model=CreditNote)
async def get_credit_note(
    credit_note_id: str,
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user),
) -> CreditNote:
    """Get credit note by ID"""

    tenant_id = get_tenant_id_from_request(request)
    service = CreditNoteService(db)

    credit_note = await service.get_credit_note(tenant_id, credit_note_id)
    if not credit_note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credit note not found",
        )

    return credit_note


@router.get("", response_model=CreditNoteListResponse)
async def list_credit_notes(
    request: Request,
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    invoice_id: Optional[str] = Query(None, description="Filter by invoice ID"),
    status: Optional[CreditNoteStatus] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number to return"),
    offset: int = Query(0, ge=0, description="Number to skip"),
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user),
) -> CreditNoteListResponse:
    """List credit notes with filtering"""

    tenant_id = get_tenant_id_from_request(request)
    service = CreditNoteService(db)

    credit_notes = await service.list_credit_notes(
        tenant_id=tenant_id,
        customer_id=customer_id,
        invoice_id=invoice_id,
        status=status,
        limit=limit + 1,
        offset=offset,
    )

    has_more = len(credit_notes) > limit
    if has_more:
        credit_notes = credit_notes[:limit]

    # Calculate total available credit
    total_available = sum(
        cn.remaining_credit_amount for cn in credit_notes
        if cn.status in [CreditNoteStatus.ISSUED, CreditNoteStatus.PARTIALLY_APPLIED]
    )

    return CreditNoteListResponse(
        credit_notes=credit_notes,
        total_count=len(credit_notes),
        has_more=has_more,
        total_available_credit=total_available,
    )


@router.post("/{credit_note_id}/issue", response_model=CreditNote)
async def issue_credit_note(
    credit_note_id: str,
    issue_data: IssueCreditNoteRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user),
) -> CreditNote:
    """Issue a draft credit note"""

    tenant_id = get_tenant_id_from_request(request)
    service = CreditNoteService(db)

    try:
        credit_note = await service.issue_credit_note(tenant_id, credit_note_id)
        return credit_note
    except CreditNoteNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credit note not found",
        )
    except InvalidCreditNoteStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{credit_note_id}/void", response_model=CreditNote)
async def void_credit_note(
    credit_note_id: str,
    void_data: VoidCreditNoteRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user),
) -> CreditNote:
    """Void a credit note"""

    tenant_id = get_tenant_id_from_request(request)
    service = CreditNoteService(db)

    try:
        credit_note = await service.void_credit_note(
            tenant_id,
            credit_note_id,
            reason=void_data.reason,
            voided_by=current_user.user_id,
        )
        return credit_note
    except CreditNoteNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credit note not found",
        )
    except InvalidCreditNoteStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{credit_note_id}/apply", response_model=CreditNote)
async def apply_credit_note(
    credit_note_id: str,
    apply_data: ApplyCreditRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user),
) -> CreditNote:
    """Apply credit note to an invoice"""

    tenant_id = get_tenant_id_from_request(request)
    service = CreditNoteService(db)

    try:
        credit_note = await service.apply_credit_to_invoice(
            tenant_id,
            credit_note_id,
            apply_data.invoice_id,
            apply_data.amount,
        )
        return credit_note
    except CreditNoteNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credit note not found",
        )
    except (InvalidCreditNoteStatusError, InsufficientCreditError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/customer/{customer_id}/available", response_model=List[CreditNote])
async def get_available_credits(
    customer_id: str,
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user),
) -> List[CreditNote]:
    """Get available credit notes for a customer"""

    tenant_id = get_tenant_id_from_request(request)
    service = CreditNoteService(db)

    credit_notes = await service.get_available_credits(tenant_id, customer_id)
    return credit_notes