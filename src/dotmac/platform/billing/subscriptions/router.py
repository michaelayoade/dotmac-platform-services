"""
Subscription management API router.

Provides REST endpoints for managing subscription plans and customer subscriptions.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from sqlalchemy.ext.asyncio import AsyncSession
from dotmac.platform.db import get_async_session
from dotmac.platform.auth.dependencies import get_current_user
from dotmac.platform.auth.core import UserInfo
from dotmac.platform.tenant import get_tenant_context

from .models import (
    SubscriptionPlanCreateRequest,
    SubscriptionPlanResponse,
    SubscriptionCreateRequest,
    SubscriptionResponse,
    SubscriptionUpdateRequest,
    SubscriptionPlanChangeRequest,
    UsageRecordRequest,
    ProrationResult,
)
from .service import SubscriptionService


router = APIRouter(prefix="/api/v1/billing/subscriptions", tags=["billing-subscriptions"])


# Subscription Plans Management

@router.post(
    "/plans",
    response_model=SubscriptionPlanResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_subscription_plan(
    plan_data: SubscriptionPlanCreateRequest,
    db_session: AsyncSession = Depends(get_async_session),
    current_user: UserInfo = Depends(get_current_user),
    tenant_context = Depends(get_tenant_context),
) -> SubscriptionPlanResponse:
    """Create a new subscription plan."""
    service = SubscriptionService(db_session)
    try:
        plan = await service.create_plan(plan_data, tenant_context.tenant_id)
        return SubscriptionPlanResponse.model_validate(plan.model_dump())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/plans", response_model=List[SubscriptionPlanResponse])
async def list_subscription_plans(
    db_session: AsyncSession = Depends(get_async_session),
    current_user: UserInfo = Depends(get_current_user),
    tenant_context = Depends(get_tenant_context),
    product_id: str | None = Query(None, description="Filter by product ID"),
    active_only: bool = Query(True, description="Show only active plans"),
) -> List[SubscriptionPlanResponse]:
    """List subscription plans."""
    service = SubscriptionService(db_session)
    plans = await service.list_plans(
        tenant_context.tenant_id,
        product_id=product_id,
        active_only=active_only,
    )
    return [SubscriptionPlanResponse.model_validate(plan.model_dump()) for plan in plans]


@router.get("/plans/{plan_id}", response_model=SubscriptionPlanResponse)
async def get_subscription_plan(
    plan_id: str,
    db_session: AsyncSession = Depends(get_async_session),
    current_user: UserInfo = Depends(get_current_user),
    tenant_context = Depends(get_tenant_context),
) -> SubscriptionPlanResponse:
    """Get a specific subscription plan."""
    service = SubscriptionService(db_session)
    plan = await service.get_plan(plan_id, tenant_context.tenant_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription plan not found"
        )
    return SubscriptionPlanResponse.model_validate(plan.model_dump())


@router.patch("/plans/{plan_id}", response_model=SubscriptionPlanResponse)
async def update_subscription_plan(
    plan_id: str,
    plan_data: dict,  # Using dict for flexible updates
    db_session: AsyncSession = Depends(get_async_session),
    current_user: UserInfo = Depends(get_current_user),
    tenant_context = Depends(get_tenant_context),
) -> SubscriptionPlanResponse:
    """Update a subscription plan."""
    service = SubscriptionService(db_session)
    try:
        plan = await service.update_plan(plan_id, plan_data, tenant_context.tenant_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription plan not found"
            )
        return SubscriptionPlanResponse.model_validate(plan.model_dump())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/plans/{plan_id}")
async def deactivate_subscription_plan(
    plan_id: str,
    db_session: AsyncSession = Depends(get_async_session),
    current_user: UserInfo = Depends(get_current_user),
    tenant_context = Depends(get_tenant_context),
) -> JSONResponse:
    """Deactivate a subscription plan (soft delete)."""
    service = SubscriptionService(db_session)
    success = await service.deactivate_plan(plan_id, tenant_context.tenant_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription plan not found"
        )
    return JSONResponse(
        content={"message": "Subscription plan deactivated successfully"},
        status_code=status.HTTP_200_OK
    )


# Customer Subscriptions Management

@router.post(
    "/",
    response_model=SubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_subscription(
    subscription_data: SubscriptionCreateRequest,
    db_session: AsyncSession = Depends(get_async_session),
    current_user: UserInfo = Depends(get_current_user),
    tenant_context = Depends(get_tenant_context),
) -> SubscriptionResponse:
    """Create a new customer subscription."""
    service = SubscriptionService(db_session)
    try:
        subscription = await service.create_subscription(subscription_data, tenant_context.tenant_id)
        response_data = subscription.model_dump()
        # Add computed fields
        response_data["is_in_trial"] = subscription.is_in_trial()
        response_data["days_until_renewal"] = subscription.days_until_renewal()
        return SubscriptionResponse.model_validate(response_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=List[SubscriptionResponse])
async def list_subscriptions(
    db_session: AsyncSession = Depends(get_async_session),
    current_user: UserInfo = Depends(get_current_user),
    tenant_context = Depends(get_tenant_context),
    customer_id: str | None = Query(None, description="Filter by customer ID"),
    plan_id: str | None = Query(None, description="Filter by plan ID"),
    status: str | None = Query(None, description="Filter by status"),
) -> List[SubscriptionResponse]:
    """List customer subscriptions."""
    service = SubscriptionService(db_session)
    subscriptions = await service.list_subscriptions(
        tenant_context.tenant_id,
        customer_id=customer_id,
        plan_id=plan_id,
        status=status,
    )

    response_list = []
    for sub in subscriptions:
        response_data = sub.model_dump()
        response_data["is_in_trial"] = sub.is_in_trial()
        response_data["days_until_renewal"] = sub.days_until_renewal()
        response_list.append(SubscriptionResponse.model_validate(response_data))

    return response_list


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(
    subscription_id: str,
    db_session: AsyncSession = Depends(get_async_session),
    current_user: UserInfo = Depends(get_current_user),
    tenant_context = Depends(get_tenant_context),
) -> SubscriptionResponse:
    """Get a specific subscription."""
    service = SubscriptionService(db_session)
    subscription = await service.get_subscription(subscription_id, tenant_context.tenant_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )

    response_data = subscription.model_dump()
    response_data["is_in_trial"] = subscription.is_in_trial()
    response_data["days_until_renewal"] = subscription.days_until_renewal()
    return SubscriptionResponse.model_validate(response_data)


@router.patch("/{subscription_id}", response_model=SubscriptionResponse)
async def update_subscription(
    subscription_id: str,
    update_data: SubscriptionUpdateRequest,
    db_session: AsyncSession = Depends(get_async_session),
    current_user: UserInfo = Depends(get_current_user),
    tenant_context = Depends(get_tenant_context),
) -> SubscriptionResponse:
    """Update a subscription."""
    service = SubscriptionService(db_session)
    try:
        subscription = await service.update_subscription(
            subscription_id, update_data, tenant_context.tenant_id
        )
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )

        response_data = subscription.model_dump()
        response_data["is_in_trial"] = subscription.is_in_trial()
        response_data["days_until_renewal"] = subscription.days_until_renewal()
        return SubscriptionResponse.model_validate(response_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# Subscription Lifecycle Operations

@router.post("/{subscription_id}/cancel")
async def cancel_subscription(
    subscription_id: str,
    at_period_end: bool = Query(True, description="Cancel at current period end"),
    db_session: AsyncSession = Depends(get_async_session),
    current_user: UserInfo = Depends(get_current_user),
    tenant_context = Depends(get_tenant_context),
) -> JSONResponse:
    """Cancel a subscription."""
    service = SubscriptionService(db_session)
    try:
        success = await service.cancel_subscription(
            subscription_id, tenant_context.tenant_id, at_period_end
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )

        message = (
            "Subscription will be canceled at the end of current period"
            if at_period_end
            else "Subscription canceled immediately"
        )
        return JSONResponse(
            content={"message": message},
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{subscription_id}/reactivate")
async def reactivate_subscription(
    subscription_id: str,
    db_session: AsyncSession = Depends(get_async_session),
    current_user: UserInfo = Depends(get_current_user),
    tenant_context = Depends(get_tenant_context),
) -> JSONResponse:
    """Reactivate a canceled subscription."""
    service = SubscriptionService(db_session)
    try:
        success = await service.reactivate_subscription(subscription_id, tenant_context.tenant_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found or cannot be reactivated"
            )

        return JSONResponse(
            content={"message": "Subscription reactivated successfully"},
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{subscription_id}/change-plan", response_model=dict)
async def change_subscription_plan(
    subscription_id: str,
    change_data: SubscriptionPlanChangeRequest,
    db_session: AsyncSession = Depends(get_async_session),
    current_user: UserInfo = Depends(get_current_user),
    tenant_context = Depends(get_tenant_context),
) -> dict:
    """Change subscription plan with proration calculation."""
    service = SubscriptionService(db_session)
    try:
        proration_result = await service.change_plan(
            subscription_id, change_data, tenant_context.tenant_id
        )
        if not proration_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )

        return {
            "message": "Plan change completed successfully",
            "proration": proration_result.model_dump()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# Usage Tracking for Hybrid Plans

@router.post("/{subscription_id}/usage")
async def record_usage(
    subscription_id: str,
    usage_data: UsageRecordRequest,
    db_session: AsyncSession = Depends(get_async_session),
    current_user: UserInfo = Depends(get_current_user),
    tenant_context = Depends(get_tenant_context),
) -> JSONResponse:
    """Record usage for usage-based or hybrid subscriptions."""
    service = SubscriptionService(db_session)
    try:
        success = await service.record_usage(usage_data, tenant_context.tenant_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )

        return JSONResponse(
            content={"message": "Usage recorded successfully"},
            status_code=status.HTTP_201_CREATED
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{subscription_id}/usage")
async def get_subscription_usage(
    subscription_id: str,
    db_session: AsyncSession = Depends(get_async_session),
    current_user: UserInfo = Depends(get_current_user),
    tenant_context = Depends(get_tenant_context),
) -> dict:
    """Get current usage for a subscription."""
    service = SubscriptionService(db_session)
    usage = await service.get_usage(subscription_id, tenant_context.tenant_id)
    if usage is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )

    return {"subscription_id": subscription_id, "usage": usage}


# Proration Preview

@router.post("/proration-preview", response_model=ProrationResult)
async def preview_plan_change_proration(
    subscription_id: str,
    new_plan_id: str,
    db_session: AsyncSession = Depends(get_async_session),
    current_user: UserInfo = Depends(get_current_user),
    tenant_context = Depends(get_tenant_context),
) -> ProrationResult:
    """Preview proration calculation for plan change."""
    service = SubscriptionService(db_session)
    try:
        proration = await service.calculate_proration_preview(
            subscription_id, new_plan_id, tenant_context.tenant_id
        )
        if not proration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription or plan not found"
            )

        return proration
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )