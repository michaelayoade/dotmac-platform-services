"""
Integration tests for the billing module
"""

import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from dotmac.platform.billing.config import BillingConfig, StripeConfig
from dotmac.platform.billing.core.enums import InvoiceStatus, PaymentStatus
from dotmac.platform.billing.core.models import Invoice, Payment
from dotmac.platform.billing.invoicing.service import InvoiceService
from dotmac.platform.billing.payments.service import PaymentService
from dotmac.platform.billing.webhooks.handlers import StripeWebhookHandler
from dotmac.platform.db import Base


@pytest.fixture
async def test_db():
    """Create test database"""
    # Create in-memory SQLite database
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.fixture
def billing_config():
    """Test billing configuration"""
    return BillingConfig(
        stripe=StripeConfig(
            api_key="sk_test_123",
            webhook_secret="whsec_test123",
            publishable_key="pk_test_123",
        ),
        enable_webhooks=True,
        enable_subscriptions=True,
        enable_tax_calculation=True,
    )


@pytest.fixture
def mock_payment_provider():
    """Mock payment provider"""
    provider = AsyncMock()
    provider.charge_payment_method = AsyncMock(
        return_value={
            "success": True,
            "transaction_id": "txn_test123",
            "amount": 1000,
            "currency": "USD",
        }
    )
    provider.refund_payment = AsyncMock(
        return_value={
            "success": True,
            "refund_id": "ref_test123",
            "amount": 500,
        }
    )
    return provider


class TestBillingIntegration:
    """Test billing module integration"""

    @pytest.mark.asyncio
    async def test_complete_invoice_lifecycle(self, test_db):
        """Test creating, finalizing, and paying an invoice"""
        invoice_service = InvoiceService(test_db)

        # Create invoice
        invoice = await invoice_service.create_invoice(
            tenant_id="test_tenant",
            customer_id="550e8400-e29b-41d4-a716-446655440005",
            billing_email="customer@example.com",
            billing_address={
                "line1": "123 Main St",
                "city": "San Francisco",
                "state": "CA",
                "postal_code": "94105",
                "country": "US",
            },
            line_items=[
                {
                    "description": "Product A",
                    "quantity": 2,
                    "unit_price": 500,
                    "total_price": 1000,
                },
                {
                    "description": "Product B",
                    "quantity": 1,
                    "unit_price": 1500,
                    "total_price": 1500,
                },
            ],
            currency="USD",
            due_days=30,
        )

        assert invoice is not None
        assert invoice.tenant_id == "test_tenant"
        assert invoice.status == InvoiceStatus.DRAFT
        assert invoice.total_amount == 2500
        assert len(invoice.line_items) == 2

        # Finalize invoice
        finalized = await invoice_service.finalize_invoice(
            "test_tenant", invoice.invoice_id
        )
        assert finalized.status == InvoiceStatus.OPEN
        assert finalized.invoice_number is not None

        # Mark as paid
        paid = await invoice_service.mark_invoice_paid(
            "test_tenant", invoice.invoice_id, payment_id="pay_123"
        )
        assert paid.status == InvoiceStatus.PAID
        assert paid.payment_status == PaymentStatus.PAID

    @pytest.mark.asyncio
    async def test_invoice_with_idempotency(self, test_db):
        """Test invoice creation with idempotency key"""
        invoice_service = InvoiceService(test_db)
        idempotency_key = "test_idempotency_123"

        # First creation
        invoice1 = await invoice_service.create_invoice(
            tenant_id="test_tenant",
            customer_id="550e8400-e29b-41d4-a716-446655440005",
            billing_email="customer@example.com",
            billing_address={"line1": "123 Main St"},
            line_items=[
                {"description": "Product", "quantity": 1, "unit_price": 1000, "total_price": 1000}
            ],
            idempotency_key=idempotency_key,
        )

        # Second creation with same idempotency key
        invoice2 = await invoice_service.create_invoice(
            tenant_id="test_tenant",
            customer_id="550e8400-e29b-41d4-a716-446655440005",
            billing_email="customer@example.com",
            billing_address={"line1": "123 Main St"},
            line_items=[
                {"description": "Different Product", "quantity": 2, "unit_price": 2000, "total_price": 4000}
            ],
            idempotency_key=idempotency_key,
        )

        # Should return the same invoice
        assert invoice1.invoice_id == invoice2.invoice_id
        assert invoice2.total_amount == 1000  # Original amount, not 4000

    @pytest.mark.asyncio
    async def test_payment_processing(self, test_db, mock_payment_provider):
        """Test payment processing flow"""
        payment_service = PaymentService(test_db)
        payment_service._get_payment_provider = lambda x: mock_payment_provider

        # Create payment
        payment = await payment_service.create_payment(
            tenant_id="test_tenant",
            invoice_id="inv_123",
            amount=1000,
            currency="USD",
            payment_method_id="pm_test123",
            provider="stripe",
            customer_id="550e8400-e29b-41d4-a716-446655440005",
        )

        assert payment is not None
        assert payment.status == PaymentStatus.PENDING
        assert payment.amount == 1000

        # Process payment
        result = await payment_service.process_payment(
            "test_tenant", payment.payment_id
        )

        assert result.status == PaymentStatus.SUCCEEDED
        assert result.provider_payment_id == "txn_test123"

        # Process refund
        refund = await payment_service.process_refund(
            "test_tenant", payment.payment_id, 500, "Customer request"
        )

        assert refund.status == PaymentStatus.PARTIALLY_REFUNDED
        assert refund.amount_refunded == 500

    @pytest.mark.asyncio
    async def test_webhook_processing(self, test_db, billing_config):
        """Test webhook event processing"""
        handler = StripeWebhookHandler(test_db, billing_config)

        # Mock services
        handler.payment_service = AsyncMock()
        handler.invoice_service = AsyncMock()
        handler.payment_service.get_payment = AsyncMock(
            return_value=Payment(
                tenant_id="test_tenant",
                payment_id="pay_123",
                invoice_id="inv_123",
                amount=1000,
                currency="USD",
                status=PaymentStatus.PENDING,
                provider="stripe",
                customer_id="550e8400-e29b-41d4-a716-446655440005",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        )

        # Process payment succeeded event
        event_data = {
            "id": "pi_test123",
            "amount": 1000,
            "currency": "usd",
            "metadata": {
                "tenant_id": "test_tenant",
                "payment_id": "pay_123",
                "invoice_id": "inv_123",
            },
        }

        result = await handler.process_event("payment_intent.succeeded", event_data)

        assert result["status"] == "processed"
        assert result["payment_intent_id"] == "pi_test123"

        # Verify service calls
        handler.payment_service.update_payment_status.assert_called_once()
        handler.invoice_service.mark_invoice_paid.assert_called_once()

    @pytest.mark.asyncio
    async def test_overdue_invoice_check(self, test_db):
        """Test checking for overdue invoices"""
        invoice_service = InvoiceService(test_db)

        # Create invoice with past due date
        past_due = datetime.utcnow() - timedelta(days=5)
        invoice = await invoice_service.create_invoice(
            tenant_id="test_tenant",
            customer_id="550e8400-e29b-41d4-a716-446655440005",
            billing_email="customer@example.com",
            billing_address={"line1": "123 Main St"},
            line_items=[
                {"description": "Product", "quantity": 1, "unit_price": 1000, "total_price": 1000}
            ],
            due_date=past_due,
        )

        # Finalize invoice
        await invoice_service.finalize_invoice("test_tenant", invoice.invoice_id)

        # Check for overdue invoices
        overdue = await invoice_service.check_overdue_invoices("test_tenant")

        assert len(overdue) == 1
        assert overdue[0].invoice_id == invoice.invoice_id
        assert overdue[0].status == InvoiceStatus.OVERDUE

    @pytest.mark.asyncio
    async def test_invoice_void(self, test_db):
        """Test voiding an invoice"""
        invoice_service = InvoiceService(test_db)

        # Create and finalize invoice
        invoice = await invoice_service.create_invoice(
            tenant_id="test_tenant",
            customer_id="550e8400-e29b-41d4-a716-446655440005",
            billing_email="customer@example.com",
            billing_address={"line1": "123 Main St"},
            line_items=[
                {"description": "Product", "quantity": 1, "unit_price": 1000, "total_price": 1000}
            ],
        )

        finalized = await invoice_service.finalize_invoice(
            "test_tenant", invoice.invoice_id
        )

        # Void invoice
        voided = await invoice_service.void_invoice(
            "test_tenant",
            invoice.invoice_id,
            reason="Customer cancelled order",
            voided_by="admin_user",
        )

        assert voided.status == InvoiceStatus.VOIDED
        assert "Customer cancelled order" in (voided.internal_notes or "")

    @pytest.mark.asyncio
    async def test_tenant_isolation(self, test_db):
        """Test that tenant isolation works correctly"""
        invoice_service = InvoiceService(test_db)

        # Create invoices for different tenants
        invoice1 = await invoice_service.create_invoice(
            tenant_id="tenant1",
            customer_id="550e8400-e29b-41d4-a716-446655440005",
            billing_email="customer1@example.com",
            billing_address={"line1": "123 Main St"},
            line_items=[
                {"description": "Product", "quantity": 1, "unit_price": 1000, "total_price": 1000}
            ],
        )

        invoice2 = await invoice_service.create_invoice(
            tenant_id="tenant2",
            customer_id="550e8400-e29b-41d4-a716-446655440006",
            billing_email="customer2@example.com",
            billing_address={"line1": "456 Oak Ave"},
            line_items=[
                {"description": "Service", "quantity": 1, "unit_price": 2000, "total_price": 2000}
            ],
        )

        # Try to get invoice1 with tenant2 - should return None
        wrong_tenant = await invoice_service.get_invoice(
            "tenant2", invoice1.invoice_id
        )
        assert wrong_tenant is None

        # Get invoice1 with correct tenant
        correct_tenant = await invoice_service.get_invoice(
            "tenant1", invoice1.invoice_id
        )
        assert correct_tenant is not None
        assert correct_tenant.invoice_id == invoice1.invoice_id

        # List invoices for each tenant
        tenant1_invoices = await invoice_service.list_invoices(tenant_id="tenant1")
        tenant2_invoices = await invoice_service.list_invoices(tenant_id="tenant2")

        assert len(tenant1_invoices) == 1
        assert len(tenant2_invoices) == 1
        assert tenant1_invoices[0].invoice_id == invoice1.invoice_id
        assert tenant2_invoices[0].invoice_id == invoice2.invoice_id