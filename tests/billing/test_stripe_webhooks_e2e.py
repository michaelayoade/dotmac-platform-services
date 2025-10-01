"""
End-to-end tests for Stripe webhook integration.
These tests simulate real webhook events from Stripe to verify complete workflow.
"""

import json
import hmac
import hashlib
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from dotmac.platform.main import app
from dotmac.platform.billing.models import (
    Customer, Subscription, Invoice, InvoiceItem, Price, Product
)
from dotmac.platform.database import get_db_session

client = TestClient(app)

# Test webhook signing key
STRIPE_WEBHOOK_SECRET = "whsec_test123456789"


def generate_stripe_signature(payload: str, secret: str) -> str:
    """Generate Stripe webhook signature for testing."""
    timestamp = int(datetime.now().timestamp())
    signature = hmac.new(
        secret.encode("utf-8"),
        f"{timestamp}.{payload}".encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    return f"t={timestamp},v1={signature}"


@pytest.fixture
async def stripe_customer(db):
    """Create a test customer with Stripe ID."""
    customer = Customer(
        user_id="test-user-1",
        stripe_customer_id="cus_test123456",
        email="test@example.com",
        name="Test Customer",
        payment_method_id="pm_test123456"
    )
    db.add(customer)
    await db.commit()
    return customer


@pytest.fixture
async def stripe_product(db):
    """Create a test product and price."""
    product = Product(
        name="Test Product",
        description="Test product for webhook testing",
        stripe_product_id="prod_test123456"
    )
    db.add(product)
    await db.commit()

    price = Price(
        product_id=product.id,
        stripe_price_id="price_test123456",
        amount=2999,  # $29.99
        currency="usd",
        interval="month"
    )
    db.add(price)
    await db.commit()

    return product, price


class TestStripeWebhooks:
    """Test Stripe webhook event handling."""

    @pytest.mark.asyncio
    async def test_customer_subscription_created(self, db, stripe_customer, stripe_product):
        """Test subscription creation webhook."""
        product, price = stripe_product

        webhook_payload = {
            "id": "evt_test123456",
            "object": "event",
            "type": "customer.subscription.created",
            "data": {
                "object": {
                    "id": "sub_test123456",
                    "object": "subscription",
                    "customer": stripe_customer.stripe_customer_id,
                    "status": "active",
                    "current_period_start": int(datetime.now().timestamp()),
                    "current_period_end": int((datetime.now() + timedelta(days=30)).timestamp()),
                    "items": {
                        "data": [{
                            "id": "si_test123456",
                            "price": {
                                "id": price.stripe_price_id,
                                "unit_amount": 2999,
                                "currency": "usd",
                                "recurring": {"interval": "month"}
                            },
                            "quantity": 1
                        }]
                    },
                    "metadata": {
                        "tenant_id": "tenant-123"
                    }
                }
            }
        }

        payload_json = json.dumps(webhook_payload)
        signature = generate_stripe_signature(payload_json, STRIPE_WEBHOOK_SECRET)

        # Send webhook
        with patch('dotmac.platform.billing.webhook_handlers.STRIPE_WEBHOOK_SECRET', STRIPE_WEBHOOK_SECRET):
            response = client.post(
                "/api/v1/billing/webhooks/stripe",
                data=payload_json,
                headers={
                    "Content-Type": "application/json",
                    "Stripe-Signature": signature
                }
            )

        assert response.status_code == 200

        # Verify subscription was created in database
        subscription = await db.execute(
            "SELECT * FROM subscriptions WHERE stripe_subscription_id = 'sub_test123456'"
        )
        sub_record = subscription.first()
        assert sub_record is not None
        assert sub_record.customer_id == stripe_customer.id
        assert sub_record.status == "active"

    @pytest.mark.asyncio
    async def test_invoice_payment_succeeded(self, db, stripe_customer):
        """Test successful invoice payment webhook."""
        webhook_payload = {
            "id": "evt_test789",
            "object": "event",
            "type": "invoice.payment_succeeded",
            "data": {
                "object": {
                    "id": "in_test123456",
                    "object": "invoice",
                    "customer": stripe_customer.stripe_customer_id,
                    "amount_paid": 2999,
                    "currency": "usd",
                    "status": "paid",
                    "paid_at": int(datetime.now().timestamp()),
                    "subscription": "sub_test123456",
                    "lines": {
                        "data": [{
                            "id": "il_test123456",
                            "amount": 2999,
                            "description": "Test Product subscription",
                            "price": {
                                "id": "price_test123456",
                                "unit_amount": 2999
                            },
                            "quantity": 1
                        }]
                    }
                }
            }
        }

        payload_json = json.dumps(webhook_payload)
        signature = generate_stripe_signature(payload_json, STRIPE_WEBHOOK_SECRET)

        with patch('dotmac.platform.billing.webhook_handlers.STRIPE_WEBHOOK_SECRET', STRIPE_WEBHOOK_SECRET):
            response = client.post(
                "/api/v1/billing/webhooks/stripe",
                data=payload_json,
                headers={
                    "Content-Type": "application/json",
                    "Stripe-Signature": signature
                }
            )

        assert response.status_code == 200

        # Verify invoice was created and marked as paid
        invoice = await db.execute(
            "SELECT * FROM invoices WHERE stripe_invoice_id = 'in_test123456'"
        )
        invoice_record = invoice.first()
        assert invoice_record is not None
        assert invoice_record.status == "paid"
        assert invoice_record.amount_total == 2999

    @pytest.mark.asyncio
    async def test_payment_method_attached(self, db, stripe_customer):
        """Test payment method attachment webhook."""
        webhook_payload = {
            "id": "evt_test999",
            "object": "event",
            "type": "payment_method.attached",
            "data": {
                "object": {
                    "id": "pm_test987654",
                    "object": "payment_method",
                    "customer": stripe_customer.stripe_customer_id,
                    "type": "card",
                    "card": {
                        "brand": "visa",
                        "last4": "4242",
                        "exp_month": 12,
                        "exp_year": 2025
                    }
                }
            }
        }

        payload_json = json.dumps(webhook_payload)
        signature = generate_stripe_signature(payload_json, STRIPE_WEBHOOK_SECRET)

        with patch('dotmac.platform.billing.webhook_handlers.STRIPE_WEBHOOK_SECRET', STRIPE_WEBHOOK_SECRET):
            response = client.post(
                "/api/v1/billing/webhooks/stripe",
                data=payload_json,
                headers={
                    "Content-Type": "application/json",
                    "Stripe-Signature": signature
                }
            )

        assert response.status_code == 200

        # Verify payment method was updated
        updated_customer = await db.get(Customer, stripe_customer.id)
        assert updated_customer.payment_method_id == "pm_test987654"

    @pytest.mark.asyncio
    async def test_subscription_updated(self, db, stripe_customer):
        """Test subscription update webhook."""
        # First create a subscription
        subscription = Subscription(
            customer_id=stripe_customer.id,
            stripe_subscription_id="sub_test123456",
            status="active",
            current_period_start=datetime.now(),
            current_period_end=datetime.now() + timedelta(days=30)
        )
        db.add(subscription)
        await db.commit()

        webhook_payload = {
            "id": "evt_test111",
            "object": "event",
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "id": "sub_test123456",
                    "object": "subscription",
                    "customer": stripe_customer.stripe_customer_id,
                    "status": "past_due",
                    "current_period_start": int(datetime.now().timestamp()),
                    "current_period_end": int((datetime.now() + timedelta(days=30)).timestamp()),
                    "cancel_at_period_end": True
                }
            }
        }

        payload_json = json.dumps(webhook_payload)
        signature = generate_stripe_signature(payload_json, STRIPE_WEBHOOK_SECRET)

        with patch('dotmac.platform.billing.webhook_handlers.STRIPE_WEBHOOK_SECRET', STRIPE_WEBHOOK_SECRET):
            response = client.post(
                "/api/v1/billing/webhooks/stripe",
                data=payload_json,
                headers={
                    "Content-Type": "application/json",
                    "Stripe-Signature": signature
                }
            )

        assert response.status_code == 200

        # Verify subscription status updated
        await db.refresh(subscription)
        assert subscription.status == "past_due"
        assert subscription.cancel_at_period_end is True

    @pytest.mark.asyncio
    async def test_subscription_deleted(self, db, stripe_customer):
        """Test subscription cancellation webhook."""
        subscription = Subscription(
            customer_id=stripe_customer.id,
            stripe_subscription_id="sub_test123456",
            status="active",
            current_period_start=datetime.now(),
            current_period_end=datetime.now() + timedelta(days=30)
        )
        db.add(subscription)
        await db.commit()

        webhook_payload = {
            "id": "evt_test222",
            "object": "event",
            "type": "customer.subscription.deleted",
            "data": {
                "object": {
                    "id": "sub_test123456",
                    "object": "subscription",
                    "customer": stripe_customer.stripe_customer_id,
                    "status": "canceled",
                    "canceled_at": int(datetime.now().timestamp()),
                    "ended_at": int(datetime.now().timestamp())
                }
            }
        }

        payload_json = json.dumps(webhook_payload)
        signature = generate_stripe_signature(payload_json, STRIPE_WEBHOOK_SECRET)

        with patch('dotmac.platform.billing.webhook_handlers.STRIPE_WEBHOOK_SECRET', STRIPE_WEBHOOK_SECRET):
            response = client.post(
                "/api/v1/billing/webhooks/stripe",
                data=payload_json,
                headers={
                    "Content-Type": "application/json",
                    "Stripe-Signature": signature
                }
            )

        assert response.status_code == 200

        # Verify subscription was canceled
        await db.refresh(subscription)
        assert subscription.status == "canceled"
        assert subscription.ended_at is not None

    @pytest.mark.asyncio
    async def test_invalid_signature_rejected(self, db):
        """Test that webhooks with invalid signatures are rejected."""
        webhook_payload = {
            "id": "evt_invalid",
            "object": "event",
            "type": "invoice.payment_succeeded",
            "data": {"object": {}}
        }

        payload_json = json.dumps(webhook_payload)
        invalid_signature = "t=123456789,v1=invalid_signature"

        response = client.post(
            "/api/v1/billing/webhooks/stripe",
            data=payload_json,
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": invalid_signature
            }
        )

        assert response.status_code == 400
        assert "Invalid signature" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_duplicate_webhook_event_ignored(self, db, stripe_customer):
        """Test that duplicate webhook events are ignored."""
        # Create webhook event record
        from dotmac.platform.billing.models import WebhookEvent

        event = WebhookEvent(
            stripe_event_id="evt_duplicate_test",
            event_type="invoice.payment_succeeded",
            processed_at=datetime.now()
        )
        db.add(event)
        await db.commit()

        webhook_payload = {
            "id": "evt_duplicate_test",
            "object": "event",
            "type": "invoice.payment_succeeded",
            "data": {"object": {"id": "in_duplicate"}}
        }

        payload_json = json.dumps(webhook_payload)
        signature = generate_stripe_signature(payload_json, STRIPE_WEBHOOK_SECRET)

        with patch('dotmac.platform.billing.webhook_handlers.STRIPE_WEBHOOK_SECRET', STRIPE_WEBHOOK_SECRET):
            response = client.post(
                "/api/v1/billing/webhooks/stripe",
                data=payload_json,
                headers={
                    "Content-Type": "application/json",
                    "Stripe-Signature": signature
                }
            )

        assert response.status_code == 200
        assert "already processed" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_webhook_retry_mechanism(self, db, stripe_customer):
        """Test webhook retry mechanism for failed processing."""
        webhook_payload = {
            "id": "evt_retry_test",
            "object": "event",
            "type": "invoice.payment_succeeded",
            "data": {
                "object": {
                    "id": "in_retry_test",
                    "customer": "cus_nonexistent"  # This will cause an error
                }
            }
        }

        payload_json = json.dumps(webhook_payload)
        signature = generate_stripe_signature(payload_json, STRIPE_WEBHOOK_SECRET)

        # Mock the webhook handler to fail first time, succeed second time
        call_count = 0
        original_handler = None

        def mock_failing_handler(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Simulated processing failure")
            return original_handler(*args, **kwargs)

        with patch('dotmac.platform.billing.webhook_handlers.STRIPE_WEBHOOK_SECRET', STRIPE_WEBHOOK_SECRET):
            with patch('dotmac.platform.billing.webhook_handlers.process_invoice_payment_succeeded', side_effect=mock_failing_handler):
                # First attempt should fail
                response1 = client.post(
                    "/api/v1/billing/webhooks/stripe",
                    data=payload_json,
                    headers={
                        "Content-Type": "application/json",
                        "Stripe-Signature": signature
                    }
                )

                assert response1.status_code == 500

                # Second attempt should succeed (in real scenario, Stripe would retry)
                # Reset the mock to simulate success on retry
                with patch('dotmac.platform.billing.webhook_handlers.process_invoice_payment_succeeded', return_value=True):
                    response2 = client.post(
                        "/api/v1/billing/webhooks/stripe",
                        data=payload_json,
                        headers={
                            "Content-Type": "application/json",
                            "Stripe-Signature": signature
                        }
                    )

                    assert response2.status_code == 200


class TestBillingWorkflowIntegration:
    """Test complete billing workflows end-to-end."""

    @pytest.mark.asyncio
    async def test_complete_subscription_lifecycle(self, db, stripe_customer, stripe_product):
        """Test complete subscription lifecycle from creation to cancellation."""
        product, price = stripe_product

        # 1. Subscription created
        create_payload = {
            "id": "evt_lifecycle_1",
            "type": "customer.subscription.created",
            "data": {
                "object": {
                    "id": "sub_lifecycle_test",
                    "customer": stripe_customer.stripe_customer_id,
                    "status": "active",
                    "current_period_start": int(datetime.now().timestamp()),
                    "current_period_end": int((datetime.now() + timedelta(days=30)).timestamp()),
                    "items": {"data": [{"price": {"id": price.stripe_price_id}}]}
                }
            }
        }

        # 2. First invoice payment
        payment_payload = {
            "id": "evt_lifecycle_2",
            "type": "invoice.payment_succeeded",
            "data": {
                "object": {
                    "id": "in_lifecycle_1",
                    "customer": stripe_customer.stripe_customer_id,
                    "subscription": "sub_lifecycle_test",
                    "amount_paid": 2999,
                    "status": "paid"
                }
            }
        }

        # 3. Subscription updated (e.g., plan change)
        update_payload = {
            "id": "evt_lifecycle_3",
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "id": "sub_lifecycle_test",
                    "customer": stripe_customer.stripe_customer_id,
                    "status": "active",
                    "current_period_start": int(datetime.now().timestamp()),
                    "current_period_end": int((datetime.now() + timedelta(days=30)).timestamp())
                }
            }
        }

        # 4. Subscription canceled
        cancel_payload = {
            "id": "evt_lifecycle_4",
            "type": "customer.subscription.deleted",
            "data": {
                "object": {
                    "id": "sub_lifecycle_test",
                    "customer": stripe_customer.stripe_customer_id,
                    "status": "canceled",
                    "canceled_at": int(datetime.now().timestamp())
                }
            }
        }

        # Execute workflow
        payloads = [create_payload, payment_payload, update_payload, cancel_payload]

        with patch('dotmac.platform.billing.webhook_handlers.STRIPE_WEBHOOK_SECRET', STRIPE_WEBHOOK_SECRET):
            for payload in payloads:
                payload_json = json.dumps(payload)
                signature = generate_stripe_signature(payload_json, STRIPE_WEBHOOK_SECRET)

                response = client.post(
                    "/api/v1/billing/webhooks/stripe",
                    data=payload_json,
                    headers={
                        "Content-Type": "application/json",
                        "Stripe-Signature": signature
                    }
                )

                assert response.status_code == 200

        # Verify final state
        subscription = await db.execute(
            "SELECT * FROM subscriptions WHERE stripe_subscription_id = 'sub_lifecycle_test'"
        )
        sub_record = subscription.first()
        assert sub_record.status == "canceled"

        invoice = await db.execute(
            "SELECT * FROM invoices WHERE stripe_invoice_id = 'in_lifecycle_1'"
        )
        invoice_record = invoice.first()
        assert invoice_record.status == "paid"
