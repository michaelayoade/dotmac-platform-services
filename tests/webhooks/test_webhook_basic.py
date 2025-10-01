"""
Basic webhook infrastructure tests.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.webhooks.models import (
    WebhookSubscriptionCreate,
    WebhookEvent,
)
from dotmac.platform.webhooks.service import WebhookSubscriptionService
from dotmac.platform.webhooks.events import EventBus, get_event_bus


@pytest.mark.asyncio
async def test_create_webhook_subscription(async_db: AsyncSession):
    """Test creating a webhook subscription."""
    service = WebhookSubscriptionService(async_db)

    subscription_data = WebhookSubscriptionCreate(
        url="https://example.com/webhook",
        description="Test webhook",
        events=[WebhookEvent.INVOICE_CREATED.value, WebhookEvent.PAYMENT_SUCCEEDED.value],
        headers={"Authorization": "Bearer test-token"},
    )

    subscription = await service.create_subscription(
        tenant_id="test-tenant",
        subscription_data=subscription_data,
    )

    assert subscription.id is not None
    assert subscription.url == "https://example.com/webhook"
    assert subscription.description == "Test webhook"
    assert len(subscription.events) == 2
    assert WebhookEvent.INVOICE_CREATED.value in subscription.events
    assert subscription.secret is not None  # Secret should be auto-generated
    assert len(subscription.secret) > 20  # Should be a secure secret
    assert subscription.is_active is True
    assert subscription.success_count == 0
    assert subscription.failure_count == 0


@pytest.mark.asyncio
async def test_list_webhook_subscriptions(async_db: AsyncSession):
    """Test listing webhook subscriptions."""
    service = WebhookSubscriptionService(async_db)

    # Create two subscriptions
    for i in range(2):
        subscription_data = WebhookSubscriptionCreate(
            url=f"https://example.com/webhook-{i}",
            events=[WebhookEvent.INVOICE_CREATED.value],
        )
        await service.create_subscription(
            tenant_id="test-tenant",
            subscription_data=subscription_data,
        )

    # List subscriptions
    subscriptions = await service.list_subscriptions(tenant_id="test-tenant")

    assert len(subscriptions) == 2


@pytest.mark.asyncio
async def test_get_subscriptions_for_event(async_db: AsyncSession):
    """Test getting subscriptions for a specific event."""
    service = WebhookSubscriptionService(async_db)

    # Create subscription for invoice events
    subscription_data1 = WebhookSubscriptionCreate(
        url="https://example.com/invoice-webhook",
        events=[WebhookEvent.INVOICE_CREATED.value, WebhookEvent.INVOICE_PAID.value],
    )
    await service.create_subscription(
        tenant_id="test-tenant",
        subscription_data=subscription_data1,
    )

    # Create subscription for payment events only
    subscription_data2 = WebhookSubscriptionCreate(
        url="https://example.com/payment-webhook",
        events=[WebhookEvent.PAYMENT_SUCCEEDED.value],
    )
    await service.create_subscription(
        tenant_id="test-tenant",
        subscription_data=subscription_data2,
    )

    # Get subscriptions for invoice.created
    invoice_subs = await service.get_subscriptions_for_event(
        event_type=WebhookEvent.INVOICE_CREATED.value,
        tenant_id="test-tenant",
    )

    assert len(invoice_subs) == 1
    assert invoice_subs[0].url == "https://example.com/invoice-webhook"

    # Get subscriptions for payment.succeeded
    payment_subs = await service.get_subscriptions_for_event(
        event_type=WebhookEvent.PAYMENT_SUCCEEDED.value,
        tenant_id="test-tenant",
    )

    assert len(payment_subs) == 1
    assert payment_subs[0].url == "https://example.com/payment-webhook"


def test_event_bus_initialization():
    """Test EventBus initialization."""
    event_bus = EventBus()

    # Should have standard events registered
    registered_events = event_bus.get_registered_events()

    assert len(registered_events) > 0
    assert WebhookEvent.INVOICE_CREATED.value in registered_events
    assert WebhookEvent.PAYMENT_SUCCEEDED.value in registered_events
    assert WebhookEvent.CUSTOMER_CREATED.value in registered_events


def test_event_bus_register_custom_event():
    """Test registering custom event."""
    event_bus = EventBus()

    event_bus.register_event(
        event_type="custom.event",
        description="Custom event for testing",
        example={"foo": "bar"},
    )

    assert event_bus.is_registered("custom.event")

    registered_events = event_bus.get_registered_events()
    assert "custom.event" in registered_events


def test_get_global_event_bus():
    """Test getting global event bus instance."""
    bus1 = get_event_bus()
    bus2 = get_event_bus()

    # Should return same instance
    assert bus1 is bus2


@pytest.mark.asyncio
async def test_update_subscription(async_db: AsyncSession):
    """Test updating webhook subscription."""
    service = WebhookSubscriptionService(async_db)

    # Create subscription
    subscription_data = WebhookSubscriptionCreate(
        url="https://example.com/webhook",
        events=[WebhookEvent.INVOICE_CREATED.value],
        description="Original description",
    )
    subscription = await service.create_subscription(
        tenant_id="test-tenant",
        subscription_data=subscription_data,
    )

    # Update subscription
    from dotmac.platform.webhooks.models import WebhookSubscriptionUpdate

    update_data = WebhookSubscriptionUpdate(
        description="Updated description",
        is_active=False,
    )

    updated = await service.update_subscription(
        subscription_id=str(subscription.id),
        tenant_id="test-tenant",
        update_data=update_data,
    )

    assert updated is not None
    assert updated.description == "Updated description"
    assert updated.is_active is False


@pytest.mark.asyncio
async def test_delete_subscription(async_db: AsyncSession):
    """Test deleting webhook subscription."""
    service = WebhookSubscriptionService(async_db)

    # Create subscription
    subscription_data = WebhookSubscriptionCreate(
        url="https://example.com/webhook",
        events=[WebhookEvent.INVOICE_CREATED.value],
    )
    subscription = await service.create_subscription(
        tenant_id="test-tenant",
        subscription_data=subscription_data,
    )

    subscription_id = str(subscription.id)

    # Delete subscription
    deleted = await service.delete_subscription(
        subscription_id=subscription_id,
        tenant_id="test-tenant",
    )

    assert deleted is True

    # Verify it's gone
    fetched = await service.get_subscription(
        subscription_id=subscription_id,
        tenant_id="test-tenant",
    )

    assert fetched is None