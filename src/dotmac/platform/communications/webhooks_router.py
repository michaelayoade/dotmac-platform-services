"""Webhook subscription management endpoints."""

import hmac
import hashlib
import secrets
from datetime import datetime, UTC
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field, HttpUrl

from ..auth.core import UserInfo, get_current_user
from .webhook_service import WebhookService, webhook_service

router = APIRouter(prefix="/api/v1/webhooks", tags=["Webhooks"])


# ============================================
# Pydantic Models
# ============================================


class WebhookEvent(str, Enum):
    """Available webhook events."""
    CUSTOMER_CREATED = "customer.created"
    CUSTOMER_UPDATED = "customer.updated"
    CUSTOMER_DELETED = "customer.deleted"
    ORDER_CREATED = "order.created"
    ORDER_UPDATED = "order.updated"
    ORDER_COMPLETED = "order.completed"
    PAYMENT_SUCCESS = "payment.success"
    PAYMENT_FAILED = "payment.failed"
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    SYSTEM_ALERT = "system.alert"


class WebhookSubscriptionCreate(BaseModel):
    """Request to create webhook subscription."""
    url: HttpUrl = Field(description="Webhook endpoint URL")
    events: List[WebhookEvent] = Field(description="List of events to subscribe to")
    name: str = Field(min_length=1, max_length=255, description="Human-readable name")
    description: Optional[str] = Field(None, max_length=500, description="Optional description")
    secret: Optional[str] = Field(None, description="Optional webhook secret for signature validation")
    headers: Optional[Dict[str, str]] = Field(default_factory=dict, description="Custom headers to include")
    is_active: bool = Field(default=True, description="Whether subscription is active")


class WebhookSubscriptionUpdate(BaseModel):
    """Request to update webhook subscription."""
    url: Optional[HttpUrl] = Field(None, description="Webhook endpoint URL")
    events: Optional[List[WebhookEvent]] = Field(None, description="List of events to subscribe to")
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Human-readable name")
    description: Optional[str] = Field(None, max_length=500, description="Optional description")
    secret: Optional[str] = Field(None, description="Webhook secret for signature validation")
    headers: Optional[Dict[str, str]] = Field(None, description="Custom headers to include")
    is_active: Optional[bool] = Field(None, description="Whether subscription is active")


class WebhookSubscriptionResponse(BaseModel):
    """Webhook subscription information."""
    id: str = Field(description="Subscription ID")
    user_id: str = Field(description="Owner user ID")
    name: str = Field(description="Human-readable name")
    url: str = Field(description="Webhook endpoint URL")
    events: List[str] = Field(description="Subscribed events")
    description: Optional[str] = Field(None, description="Optional description")
    headers: Dict[str, str] = Field(description="Custom headers")
    is_active: bool = Field(description="Whether subscription is active")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    last_delivery_at: Optional[datetime] = Field(None, description="Last successful delivery")
    total_deliveries: int = Field(default=0, description="Total delivery attempts")
    failed_deliveries: int = Field(default=0, description="Failed delivery attempts")
    has_secret: bool = Field(description="Whether secret is configured")


class WebhookSubscriptionListResponse(BaseModel):
    """List of webhook subscriptions."""
    subscriptions: List[WebhookSubscriptionResponse]
    total: int
    page: int
    limit: int


class WebhookDelivery(BaseModel):
    """Webhook delivery record."""
    id: str = Field(description="Delivery ID")
    subscription_id: str = Field(description="Subscription ID")
    event_type: str = Field(description="Event that triggered delivery")
    status: str = Field(description="Delivery status")
    response_status: Optional[int] = Field(None, description="HTTP response status")
    response_body: Optional[str] = Field(None, description="Response body")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    delivered_at: datetime = Field(description="Delivery timestamp")
    retry_count: int = Field(default=0, description="Number of retries")
    next_retry_at: Optional[datetime] = Field(None, description="Next retry timestamp")


class WebhookDeliveryListResponse(BaseModel):
    """List of webhook deliveries."""
    deliveries: List[WebhookDelivery]
    total: int
    page: int
    limit: int


class WebhookTestRequest(BaseModel):
    """Request to test webhook."""
    event_type: WebhookEvent = Field(description="Event type to simulate")
    payload: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Test payload")


class WebhookTestResponse(BaseModel):
    """Webhook test response."""
    success: bool = Field(description="Whether test succeeded")
    status_code: Optional[int] = Field(None, description="HTTP response status")
    response_body: Optional[str] = Field(None, description="Response body")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    delivery_time_ms: int = Field(description="Delivery time in milliseconds")


# ============================================
# API Endpoints
# ============================================


@router.post("", response_model=WebhookSubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook_subscription(
    request: WebhookSubscriptionCreate,
    current_user: UserInfo = Depends(get_current_user),
) -> WebhookSubscriptionResponse:
    """Create a new webhook subscription."""
    try:
        subscription_id = str(uuid4())

        # Generate secret if not provided
        webhook_secret = request.secret or secrets.token_urlsafe(32)

        subscription_data = {
            "id": subscription_id,
            "user_id": current_user.user_id,
            "name": request.name,
            "url": str(request.url),
            "events": [event.value for event in request.events],
            "description": request.description,
            "secret": webhook_secret,
            "headers": request.headers or {},
            "is_active": request.is_active,
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
            "last_delivery_at": None,
            "total_deliveries": 0,
            "failed_deliveries": 0,
        }

        await webhook_service.create_subscription(subscription_data)

        return WebhookSubscriptionResponse(
            id=subscription_id,
            user_id=current_user.user_id,
            name=request.name,
            url=str(request.url),
            events=[event.value for event in request.events],
            description=request.description,
            headers=request.headers or {},
            is_active=request.is_active,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            last_delivery_at=None,
            total_deliveries=0,
            failed_deliveries=0,
            has_secret=True,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create webhook subscription: {str(e)}"
        )


@router.get("", response_model=WebhookSubscriptionListResponse)
async def list_webhook_subscriptions(
    page: int = 1,
    limit: int = 50,
    event_filter: Optional[str] = None,
    active_only: bool = False,
    current_user: UserInfo = Depends(get_current_user),
) -> WebhookSubscriptionListResponse:
    """List user's webhook subscriptions."""
    try:
        subscriptions = await webhook_service.list_user_subscriptions(
            user_id=current_user.user_id,
            event_filter=event_filter,
            active_only=active_only,
            page=page,
            limit=limit,
        )

        subscription_responses = []
        for sub_data in subscriptions["subscriptions"]:
            subscription_responses.append(WebhookSubscriptionResponse(
                id=sub_data["id"],
                user_id=sub_data["user_id"],
                name=sub_data["name"],
                url=sub_data["url"],
                events=sub_data["events"],
                description=sub_data.get("description"),
                headers=sub_data.get("headers", {}),
                is_active=sub_data.get("is_active", True),
                created_at=datetime.fromisoformat(sub_data["created_at"]),
                updated_at=datetime.fromisoformat(sub_data["updated_at"]),
                last_delivery_at=datetime.fromisoformat(sub_data["last_delivery_at"]) if sub_data.get("last_delivery_at") else None,
                total_deliveries=sub_data.get("total_deliveries", 0),
                failed_deliveries=sub_data.get("failed_deliveries", 0),
                has_secret=bool(sub_data.get("secret")),
            ))

        return WebhookSubscriptionListResponse(
            subscriptions=subscription_responses,
            total=subscriptions["total"],
            page=page,
            limit=limit,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list webhook subscriptions: {str(e)}"
        )


@router.get("/{subscription_id}", response_model=WebhookSubscriptionResponse)
async def get_webhook_subscription(
    subscription_id: str,
    current_user: UserInfo = Depends(get_current_user),
) -> WebhookSubscriptionResponse:
    """Get webhook subscription details."""
    try:
        subscription = await webhook_service.get_subscription(subscription_id)

        if not subscription or subscription.get("user_id") != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook subscription not found"
            )

        return WebhookSubscriptionResponse(
            id=subscription["id"],
            user_id=subscription["user_id"],
            name=subscription["name"],
            url=subscription["url"],
            events=subscription["events"],
            description=subscription.get("description"),
            headers=subscription.get("headers", {}),
            is_active=subscription.get("is_active", True),
            created_at=datetime.fromisoformat(subscription["created_at"]),
            updated_at=datetime.fromisoformat(subscription["updated_at"]),
            last_delivery_at=datetime.fromisoformat(subscription["last_delivery_at"]) if subscription.get("last_delivery_at") else None,
            total_deliveries=subscription.get("total_deliveries", 0),
            failed_deliveries=subscription.get("failed_deliveries", 0),
            has_secret=bool(subscription.get("secret")),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get webhook subscription: {str(e)}"
        )


@router.patch("/{subscription_id}", response_model=WebhookSubscriptionResponse)
async def update_webhook_subscription(
    subscription_id: str,
    request: WebhookSubscriptionUpdate,
    current_user: UserInfo = Depends(get_current_user),
) -> WebhookSubscriptionResponse:
    """Update webhook subscription."""
    try:
        subscription = await webhook_service.get_subscription(subscription_id)

        if not subscription or subscription.get("user_id") != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook subscription not found"
            )

        # Prepare updates
        updates = {"updated_at": datetime.now(UTC).isoformat()}
        if request.url is not None:
            updates["url"] = str(request.url)
        if request.events is not None:
            updates["events"] = [event.value for event in request.events]
        if request.name is not None:
            updates["name"] = request.name
        if request.description is not None:
            updates["description"] = request.description
        if request.secret is not None:
            updates["secret"] = request.secret
        if request.headers is not None:
            updates["headers"] = request.headers
        if request.is_active is not None:
            updates["is_active"] = request.is_active

        success = await webhook_service.update_subscription(subscription_id, updates)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update webhook subscription"
            )

        # Get updated subscription
        updated_subscription = await webhook_service.get_subscription(subscription_id)

        return WebhookSubscriptionResponse(
            id=updated_subscription["id"],
            user_id=updated_subscription["user_id"],
            name=updated_subscription["name"],
            url=updated_subscription["url"],
            events=updated_subscription["events"],
            description=updated_subscription.get("description"),
            headers=updated_subscription.get("headers", {}),
            is_active=updated_subscription.get("is_active", True),
            created_at=datetime.fromisoformat(updated_subscription["created_at"]),
            updated_at=datetime.fromisoformat(updated_subscription["updated_at"]),
            last_delivery_at=datetime.fromisoformat(updated_subscription["last_delivery_at"]) if updated_subscription.get("last_delivery_at") else None,
            total_deliveries=updated_subscription.get("total_deliveries", 0),
            failed_deliveries=updated_subscription.get("failed_deliveries", 0),
            has_secret=bool(updated_subscription.get("secret")),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update webhook subscription: {str(e)}"
        )


@router.delete("/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook_subscription(
    subscription_id: str,
    current_user: UserInfo = Depends(get_current_user),
):
    """Delete webhook subscription."""
    try:
        subscription = await webhook_service.get_subscription(subscription_id)

        if not subscription or subscription.get("user_id") != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook subscription not found"
            )

        success = await webhook_service.delete_subscription(subscription_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete webhook subscription"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete webhook subscription: {str(e)}"
        )


@router.get("/{subscription_id}/deliveries", response_model=WebhookDeliveryListResponse)
async def list_webhook_deliveries(
    subscription_id: str,
    page: int = 1,
    limit: int = 50,
    status_filter: Optional[str] = None,
    current_user: UserInfo = Depends(get_current_user),
) -> WebhookDeliveryListResponse:
    """List webhook deliveries for a subscription."""
    try:
        subscription = await webhook_service.get_subscription(subscription_id)

        if not subscription or subscription.get("user_id") != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook subscription not found"
            )

        deliveries = await webhook_service.list_deliveries(
            subscription_id=subscription_id,
            status_filter=status_filter,
            page=page,
            limit=limit,
        )

        delivery_responses = []
        for delivery_data in deliveries["deliveries"]:
            delivery_responses.append(WebhookDelivery(
                id=delivery_data["id"],
                subscription_id=delivery_data["subscription_id"],
                event_type=delivery_data["event_type"],
                status=delivery_data["status"],
                response_status=delivery_data.get("response_status"),
                response_body=delivery_data.get("response_body"),
                error_message=delivery_data.get("error_message"),
                delivered_at=datetime.fromisoformat(delivery_data["delivered_at"]),
                retry_count=delivery_data.get("retry_count", 0),
                next_retry_at=datetime.fromisoformat(delivery_data["next_retry_at"]) if delivery_data.get("next_retry_at") else None,
            ))

        return WebhookDeliveryListResponse(
            deliveries=delivery_responses,
            total=deliveries["total"],
            page=page,
            limit=limit,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list webhook deliveries: {str(e)}"
        )


@router.post("/{subscription_id}/test", response_model=WebhookTestResponse)
async def test_webhook_subscription(
    subscription_id: str,
    request: WebhookTestRequest,
    background_tasks: BackgroundTasks,
    current_user: UserInfo = Depends(get_current_user),
) -> WebhookTestResponse:
    """Test webhook subscription."""
    try:
        subscription = await webhook_service.get_subscription(subscription_id)

        if not subscription or subscription.get("user_id") != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook subscription not found"
            )

        # Create test payload
        test_payload = request.payload or {
            "id": "test-" + str(uuid4()),
            "event_type": request.event_type.value,
            "created_at": datetime.now(UTC).isoformat(),
            "data": {
                "test": True,
                "message": "This is a test webhook delivery"
            }
        }

        # Trigger test delivery
        result = await webhook_service.test_delivery(
            subscription_id=subscription_id,
            event_type=request.event_type.value,
            payload=test_payload,
        )

        return WebhookTestResponse(
            success=result["success"],
            status_code=result.get("status_code"),
            response_body=result.get("response_body"),
            error_message=result.get("error_message"),
            delivery_time_ms=result.get("delivery_time_ms", 0),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test webhook subscription: {str(e)}"
        )


@router.post("/{subscription_id}/retry/{delivery_id}", status_code=status.HTTP_202_ACCEPTED)
async def retry_webhook_delivery(
    subscription_id: str,
    delivery_id: str,
    background_tasks: BackgroundTasks,
    current_user: UserInfo = Depends(get_current_user),
):
    """Retry failed webhook delivery."""
    try:
        subscription = await webhook_service.get_subscription(subscription_id)

        if not subscription or subscription.get("user_id") != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook subscription not found"
            )

        # Queue retry in background
        background_tasks.add_task(
            webhook_service.retry_delivery,
            delivery_id
        )

        return {"message": "Delivery retry queued"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retry webhook delivery: {str(e)}"
        )


# ============================================
# Available Events Endpoint
# ============================================


@router.get("/events/available", response_model=dict)
async def get_available_events(
    current_user: UserInfo = Depends(get_current_user),
) -> dict:
    """Get available webhook events."""
    events = {}
    for event in WebhookEvent:
        events[event.value] = {
            "name": event.value.replace(".", " ").title(),
            "description": f"Triggered when {event.value.replace('.', ' ')} occurs"
        }

    return {"events": events}