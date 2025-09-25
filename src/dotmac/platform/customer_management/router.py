"""
Customer Management API Router.

Provides RESTful endpoints for customer management operations.
"""

from typing import Annotated, Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.auth.dependencies import get_current_user
from dotmac.platform.auth.core import UserInfo
from dotmac.platform.customer_management.schemas import (
    CustomerActivityCreate,
    CustomerActivityResponse,
    CustomerCreate,
    CustomerListResponse,
    CustomerMetrics,
    CustomerNoteCreate,
    CustomerNoteResponse,
    CustomerResponse,
    CustomerSearchParams,
    CustomerSegmentCreate,
    CustomerSegmentResponse,
    CustomerUpdate,
)
from dotmac.platform.customer_management.service import CustomerService
from dotmac.platform.db import get_session_dependency

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/customers", tags=["customers"])


# Dependency for customer service
async def get_customer_service(
    session: AsyncSession = Depends(get_session_dependency),
) -> CustomerService:
    """Get customer service instance."""
    return CustomerService(session)


@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    data: CustomerCreate,
    service: Annotated[CustomerService, Depends(get_customer_service)],
    current_user: Annotated[UserInfo, Depends(get_current_user)],
) -> CustomerResponse:
    """
    Create a new customer.

    Requires authentication.
    """
    try:
        # Check if email already exists
        existing = await service.get_customer_by_email(data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Customer with email {data.email} already exists",
            )

        customer = await service.create_customer(
            data=data,
            created_by=current_user.user_id,
        )
        return CustomerResponse.model_validate(customer)
    except HTTPException:
        # Re-raise HTTPException as-is (for duplicate email check)
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Failed to create customer", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create customer",
        )


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: UUID,
    service: Annotated[CustomerService, Depends(get_customer_service)],
    current_user: Annotated[UserInfo, Depends(get_current_user)],
    include_activities: bool = Query(False, description="Include customer activities"),
    include_notes: bool = Query(False, description="Include customer notes"),
) -> CustomerResponse:
    """
    Get customer by ID.

    Requires authentication.
    """
    customer = await service.get_customer(
        customer_id=customer_id,
        include_activities=include_activities,
        include_notes=include_notes,
    )
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer {customer_id} not found",
        )
    return CustomerResponse.model_validate(customer)


@router.get("/by-number/{customer_number}", response_model=CustomerResponse)
async def get_customer_by_number(
    customer_number: str,
    service: Annotated[CustomerService, Depends(get_customer_service)],
    current_user: Annotated[UserInfo, Depends(get_current_user)],
) -> CustomerResponse:
    """
    Get customer by customer number.

    Requires authentication.
    """
    customer = await service.get_customer_by_number(customer_number)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with number {customer_number} not found",
        )
    return CustomerResponse.model_validate(customer)


@router.patch("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: UUID,
    data: CustomerUpdate,
    service: Annotated[CustomerService, Depends(get_customer_service)],
    current_user: Annotated[UserInfo, Depends(get_current_user)],
) -> CustomerResponse:
    """
    Update customer information.

    Requires authentication.
    """
    try:
        customer = await service.update_customer(
            customer_id=customer_id,
            data=data,
            updated_by=current_user.user_id,
        )
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer {customer_id} not found",
            )
        return CustomerResponse.model_validate(customer)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Failed to update customer", customer_id=str(customer_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update customer",
        )


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    customer_id: UUID,
    service: Annotated[CustomerService, Depends(get_customer_service)],
    current_user: Annotated[UserInfo, Depends(get_current_user)],
    hard_delete: bool = Query(False, description="Permanently delete customer"),
) -> None:
    """
    Delete a customer.

    By default performs soft delete. Set hard_delete=true for permanent deletion.
    Requires authentication.
    """
    success = await service.delete_customer(
        customer_id=customer_id,
        hard_delete=hard_delete,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer {customer_id} not found",
        )


@router.post("/search", response_model=CustomerListResponse)
async def search_customers(
    params: CustomerSearchParams,
    service: Annotated[CustomerService, Depends(get_customer_service)],
    current_user: Annotated[UserInfo, Depends(get_current_user)],
) -> CustomerListResponse:
    """
    Search and filter customers.

    Supports various filters including status, type, tier, location, and more.
    Requires authentication.
    """
    try:
        customers, total = await service.search_customers(params)

        has_next = (params.page * params.page_size) < total
        has_prev = params.page > 1

        return CustomerListResponse(
            customers=[CustomerResponse.model_validate(c) for c in customers],
            total=total,
            page=params.page,
            page_size=params.page_size,
            has_next=has_next,
            has_prev=has_prev,
        )
    except Exception as e:
        logger.error("Failed to search customers", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search customers",
        )


@router.post("/{customer_id}/activities", response_model=CustomerActivityResponse, status_code=status.HTTP_201_CREATED)
async def add_customer_activity(
    customer_id: UUID,
    data: CustomerActivityCreate,
    service: Annotated[CustomerService, Depends(get_customer_service)],
    current_user: Annotated[UserInfo, Depends(get_current_user)],
) -> CustomerActivityResponse:
    """
    Add an activity to customer timeline.

    Requires authentication.
    """
    try:
        activity = await service.add_activity(
            customer_id=customer_id,
            data=data,
            performed_by=UUID(current_user.user_id),
        )
        return CustomerActivityResponse.model_validate(activity)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Failed to add activity", customer_id=str(customer_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add activity",
        )


@router.get("/{customer_id}/activities", response_model=list[CustomerActivityResponse])
async def get_customer_activities(
    customer_id: UUID,
    service: Annotated[CustomerService, Depends(get_customer_service)],
    current_user: Annotated[UserInfo, Depends(get_current_user)],
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[CustomerActivityResponse]:
    """
    Get customer activity timeline.

    Requires authentication.
    """
    activities = await service.get_activities(
        customer_id=customer_id,
        limit=limit,
        offset=offset,
    )
    return [CustomerActivityResponse.model_validate(a) for a in activities]


@router.post("/{customer_id}/notes", response_model=CustomerNoteResponse, status_code=status.HTTP_201_CREATED)
async def add_customer_note(
    customer_id: UUID,
    data: CustomerNoteCreate,
    service: Annotated[CustomerService, Depends(get_customer_service)],
    current_user: Annotated[UserInfo, Depends(get_current_user)],
) -> CustomerNoteResponse:
    """
    Add a note to customer.

    Requires authentication.
    """
    try:
        note = await service.add_note(
            customer_id=customer_id,
            data=data,
            created_by_id=UUID(current_user.user_id),
        )
        return CustomerNoteResponse.model_validate(note)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Failed to add note", customer_id=str(customer_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add note",
        )


@router.get("/{customer_id}/notes", response_model=list[CustomerNoteResponse])
async def get_customer_notes(
    customer_id: UUID,
    service: Annotated[CustomerService, Depends(get_customer_service)],
    current_user: Annotated[UserInfo, Depends(get_current_user)],
    include_internal: bool = Query(True, description="Include internal notes"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[CustomerNoteResponse]:
    """
    Get customer notes.

    Requires authentication.
    """
    notes = await service.get_notes(
        customer_id=customer_id,
        include_internal=include_internal,
        limit=limit,
        offset=offset,
    )
    return [CustomerNoteResponse.model_validate(n) for n in notes]


@router.post("/{customer_id}/metrics/purchase", status_code=status.HTTP_204_NO_CONTENT)
async def record_purchase(
    customer_id: UUID,
    service: Annotated[CustomerService, Depends(get_customer_service)],
    current_user: Annotated[UserInfo, Depends(get_current_user)],
    amount: float = Query(..., gt=0, description="Purchase amount"),
) -> None:
    """
    Record a customer purchase and update metrics.

    Requires authentication.
    """
    await service.update_metrics(
        customer_id=customer_id,
        purchase_amount=amount,
    )


@router.post("/segments", response_model=CustomerSegmentResponse, status_code=status.HTTP_201_CREATED)
async def create_segment(
    data: CustomerSegmentCreate,
    service: Annotated[CustomerService, Depends(get_customer_service)],
    current_user: Annotated[UserInfo, Depends(get_current_user)],
) -> CustomerSegmentResponse:
    """
    Create a customer segment.

    Requires authentication.
    """
    try:
        segment = await service.create_segment(data)
        return CustomerSegmentResponse.model_validate(segment)
    except Exception as e:
        logger.error("Failed to create segment", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create segment",
        )


@router.post("/segments/{segment_id}/recalculate", response_model=dict)
async def recalculate_segment(
    segment_id: UUID,
    service: Annotated[CustomerService, Depends(get_customer_service)],
    current_user: Annotated[UserInfo, Depends(get_current_user)],
) -> dict:
    """
    Recalculate dynamic segment membership.

    Requires authentication.
    """
    member_count = await service.recalculate_segment(segment_id)
    return {"segment_id": str(segment_id), "member_count": member_count}


@router.get("/metrics/overview", response_model=CustomerMetrics)
async def get_customer_metrics(
    service: Annotated[CustomerService, Depends(get_customer_service)],
    current_user: Annotated[UserInfo, Depends(get_current_user)],
) -> CustomerMetrics:
    """
    Get aggregated customer metrics.

    Requires authentication.
    """
    metrics = await service.get_customer_metrics()

    # This is simplified - you would expand this with real calculations
    return CustomerMetrics(
        total_customers=metrics["total_customers"],
        active_customers=metrics["active_customers"],
        new_customers_this_month=0,  # Would calculate from data
        churn_rate=metrics["churn_rate"],
        average_lifetime_value=metrics["average_lifetime_value"],
        total_revenue=metrics["total_revenue"],
        customers_by_status={},  # Would aggregate from data
        customers_by_tier={},  # Would aggregate from data
        customers_by_type={},  # Would aggregate from data
        top_segments=[],  # Would fetch top segments
    )
