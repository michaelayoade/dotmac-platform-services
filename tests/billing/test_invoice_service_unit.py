"""Comprehensive unit tests for InvoiceService to reach 70%+ coverage.

This test suite focuses on covering uncovered lines (55-167, 174-186, etc.)
using proper async mocking to avoid database configuration issues.
"""

import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.billing.invoicing.service import InvoiceService
from dotmac.platform.billing.core.entities import InvoiceEntity, InvoiceLineItemEntity
from dotmac.platform.billing.core.enums import InvoiceStatus, PaymentStatus
from dotmac.platform.billing.core.models import Invoice, InvoiceLineItem
from dotmac.platform.billing.core.exceptions import (
    InvalidInvoiceStatusError,
    InvoiceNotFoundError,
)


@pytest.fixture
def mock_db_session():
    """Create a mock async database session."""
    session = AsyncMock(spec=AsyncSession)
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def invoice_service(mock_db_session):
    """Create InvoiceService with mocked dependencies."""
    with patch("dotmac.platform.billing.invoicing.service.get_billing_metrics"), \
         patch("dotmac.platform.billing.invoicing.service.get_event_bus"):
        service = InvoiceService(db_session=mock_db_session)
        return service


@pytest.fixture
def sample_line_items():
    """Sample line items for invoice creation."""
    return [
        {
            "description": "Product A",
            "quantity": 2,
            "unit_price": Decimal("50.00"),
            "total_price": Decimal("100.00"),
            "tax_rate": Decimal("0.10"),
            "tax_amount": Decimal("10.00"),
            "discount_percentage": Decimal("0.00"),
            "discount_amount": Decimal("0.00"),
            "product_id": "prod_1",
            "subscription_id": None,
            "extra_data": {},
        },
        {
            "description": "Product B",
            "quantity": 1,
            "unit_price": Decimal("75.00"),
            "total_price": Decimal("75.00"),
            "tax_rate": Decimal("0.10"),
            "tax_amount": Decimal("7.50"),
            "discount_percentage": Decimal("0.05"),
            "discount_amount": Decimal("3.75"),
            "product_id": "prod_2",
            "subscription_id": "sub_1",
            "extra_data": {"promo": "SAVE5"},
        },
    ]


class TestInvoiceServiceCreateInvoice:
    """Test create_invoice method - covering lines 55-167."""

    @pytest.mark.asyncio
    async def test_create_invoice_with_idempotency_key_returns_existing(
        self, invoice_service, sample_line_items
    ):
        """Test that idempotency key returns existing invoice - lines 55-58."""
        existing_invoice_entity = InvoiceEntity(
            tenant_id="tenant_1",
            invoice_id="inv_existing",
            invoice_number="INV-001",
            customer_id="cust_1",
            billing_email="test@example.com",
            billing_address={"street": "123 Main St"},
            issue_date=datetime.now(timezone.utc),
            due_date=datetime.now(timezone.utc) + timedelta(days=30),
            currency="USD",
            subtotal=Decimal("100.00"),
            tax_amount=Decimal("10.00"),
            discount_amount=Decimal("0.00"),
            total_amount=Decimal("110.00"),
            remaining_balance=Decimal("110.00"),
            status=InvoiceStatus.DRAFT,
            payment_status=PaymentStatus.PENDING,
        )

        # Mock _get_invoice_by_idempotency_key to return existing
        invoice_service._get_invoice_by_idempotency_key = AsyncMock(
            return_value=existing_invoice_entity
        )

        result = await invoice_service.create_invoice(
            tenant_id="tenant_1",
            customer_id="cust_1",
            billing_email="test@example.com",
            billing_address={"street": "123 Main St"},
            line_items=sample_line_items,
            idempotency_key="test_key_123",
        )

        assert result.invoice_id == "inv_existing"
        assert result.invoice_number == "INV-001"
        invoice_service._get_invoice_by_idempotency_key.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_invoice_calculates_due_date_from_due_days(
        self, invoice_service, sample_line_items
    ):
        """Test that due_date is calculated from due_days - lines 61-63."""
        invoice_service._get_invoice_by_idempotency_key = AsyncMock(return_value=None)
        invoice_service._generate_invoice_number = AsyncMock(return_value="INV-002")
        invoice_service._create_invoice_transaction = AsyncMock()

        # Mock metrics and event bus
        invoice_service.metrics.record_invoice_created = MagicMock()

        before_create = datetime.now(timezone.utc)
        result = await invoice_service.create_invoice(
            tenant_id="tenant_1",
            customer_id="cust_1",
            billing_email="test@example.com",
            billing_address={"street": "123 Main St"},
            line_items=sample_line_items,
            due_days=15,  # Should calculate due_date as today + 15 days
        )

        # Check that due_date is approximately 15 days from now
        expected_due = before_create + timedelta(days=15)
        assert (result.due_date - expected_due).total_seconds() < 60  # Within 1 minute

    @pytest.mark.asyncio
    async def test_create_invoice_calculates_totals_from_line_items(
        self, invoice_service, sample_line_items
    ):
        """Test invoice total calculations - lines 65-79."""
        invoice_service._get_invoice_by_idempotency_key = AsyncMock(return_value=None)
        invoice_service._generate_invoice_number = AsyncMock(return_value="INV-003")
        invoice_service._create_invoice_transaction = AsyncMock()
        invoice_service.metrics.record_invoice_created = MagicMock()

        result = await invoice_service.create_invoice(
            tenant_id="tenant_1",
            customer_id="cust_1",
            billing_email="test@example.com",
            billing_address={"street": "123 Main St"},
            line_items=sample_line_items,
            currency="USD",
        )

        # Verify calculations
        # subtotal = 100.00 + 75.00 = 175.00
        # tax_amount = 10.00 + 7.50 = 17.50
        # discount_amount = 0.00 + 3.75 = 3.75
        # total = 175.00 + 17.50 - 3.75 = 188.75
        assert result.subtotal == Decimal("175.00")
        assert result.tax_amount == Decimal("17.50")
        assert result.discount_amount == Decimal("3.75")
        assert result.total_amount == Decimal("188.75")

    @pytest.mark.asyncio
    async def test_create_invoice_saves_line_items(
        self, invoice_service, sample_line_items
    ):
        """Test that line items are created and added - lines 110-125."""
        invoice_service._get_invoice_by_idempotency_key = AsyncMock(return_value=None)
        invoice_service._generate_invoice_number = AsyncMock(return_value="INV-004")
        invoice_service._create_invoice_transaction = AsyncMock()
        invoice_service.metrics.record_invoice_created = MagicMock()

        result = await invoice_service.create_invoice(
            tenant_id="tenant_1",
            customer_id="cust_1",
            billing_email="test@example.com",
            billing_address={"street": "123 Main St"},
            line_items=sample_line_items,
        )

        # Verify database operations
        invoice_service.db.add.assert_called_once()
        invoice_service.db.commit.assert_awaited_once()
        invoice_service.db.refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_invoice_creates_transaction(
        self, invoice_service, sample_line_items
    ):
        """Test that transaction is created - line 133."""
        invoice_service._get_invoice_by_idempotency_key = AsyncMock(return_value=None)
        invoice_service._generate_invoice_number = AsyncMock(return_value="INV-005")
        invoice_service._create_invoice_transaction = AsyncMock()
        invoice_service.metrics.record_invoice_created = MagicMock()

        await invoice_service.create_invoice(
            tenant_id="tenant_1",
            customer_id="cust_1",
            billing_email="test@example.com",
            billing_address={"street": "123 Main St"},
            line_items=sample_line_items,
        )

        invoice_service._create_invoice_transaction.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_invoice_records_metrics(
        self, invoice_service, sample_line_items
    ):
        """Test that metrics are recorded - lines 136-141."""
        invoice_service._get_invoice_by_idempotency_key = AsyncMock(return_value=None)
        invoice_service._generate_invoice_number = AsyncMock(return_value="INV-006")
        invoice_service._create_invoice_transaction = AsyncMock()
        invoice_service.metrics.record_invoice_created = MagicMock()

        await invoice_service.create_invoice(
            tenant_id="tenant_1",
            customer_id="cust_1",
            billing_email="test@example.com",
            billing_address={"street": "123 Main St"},
            line_items=sample_line_items,
            currency="EUR",
        )

        invoice_service.metrics.record_invoice_created.assert_called_once()
        call_kwargs = invoice_service.metrics.record_invoice_created.call_args.kwargs
        assert call_kwargs["tenant_id"] == "tenant_1"
        assert call_kwargs["customer_id"] == "cust_1"
        assert call_kwargs["currency"] == "EUR"

    @pytest.mark.asyncio
    async def test_create_invoice_publishes_webhook_event(
        self, invoice_service, sample_line_items
    ):
        """Test that webhook event is published - lines 144-160."""
        invoice_service._get_invoice_by_idempotency_key = AsyncMock(return_value=None)
        invoice_service._generate_invoice_number = AsyncMock(return_value="INV-007")
        invoice_service._create_invoice_transaction = AsyncMock()
        invoice_service.metrics.record_invoice_created = MagicMock()

        with patch("dotmac.platform.billing.invoicing.service.get_event_bus") as mock_bus:
            mock_bus.return_value.publish = AsyncMock()

            await invoice_service.create_invoice(
                tenant_id="tenant_1",
                customer_id="cust_1",
                billing_email="test@example.com",
                billing_address={"street": "123 Main St"},
                line_items=sample_line_items,
                subscription_id="sub_123",
            )

            mock_bus.return_value.publish.assert_awaited_once()
            call_kwargs = mock_bus.return_value.publish.call_args.kwargs
            assert call_kwargs["tenant_id"] == "tenant_1"
            assert "invoice_id" in call_kwargs["event_data"]

    @pytest.mark.asyncio
    async def test_create_invoice_handles_webhook_failure(
        self, invoice_service, sample_line_items
    ):
        """Test that webhook failure doesn't break invoice creation - lines 161-165."""
        invoice_service._get_invoice_by_idempotency_key = AsyncMock(return_value=None)
        invoice_service._generate_invoice_number = AsyncMock(return_value="INV-008")
        invoice_service._create_invoice_transaction = AsyncMock()
        invoice_service.metrics.record_invoice_created = MagicMock()

        with patch("dotmac.platform.billing.invoicing.service.get_event_bus") as mock_bus:
            mock_bus.return_value.publish = AsyncMock(side_effect=Exception("Webhook failed"))

            # Should still succeed despite webhook failure
            result = await invoice_service.create_invoice(
                tenant_id="tenant_1",
                customer_id="cust_1",
                billing_email="test@example.com",
                billing_address={"street": "123 Main St"},
                line_items=sample_line_items,
            )

            assert result.invoice_number == "INV-008"


class TestInvoiceServiceGetInvoice:
    """Test get_invoice method - covering lines 174-186."""

    @pytest.mark.asyncio
    async def test_get_invoice_with_line_items(self, invoice_service):
        """Test getting invoice with line items - lines 178-179."""
        mock_invoice = InvoiceEntity(
            tenant_id="tenant_1",
            invoice_id="inv_1",
            invoice_number="INV-001",
            customer_id="cust_1",
            billing_email="test@example.com",
            billing_address={"street": "123 Main St"},
            issue_date=datetime.now(timezone.utc),
            due_date=datetime.now(timezone.utc) + timedelta(days=30),
            currency="USD",
            subtotal=Decimal("100.00"),
            tax_amount=Decimal("10.00"),
            discount_amount=Decimal("0.00"),
            total_amount=Decimal("110.00"),
            remaining_balance=Decimal("110.00"),
            status=InvoiceStatus.DRAFT,
            payment_status=PaymentStatus.PENDING,
        )

        # Mock database query result
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_invoice)
        invoice_service.db.execute = AsyncMock(return_value=mock_result)

        result = await invoice_service.get_invoice(
            tenant_id="tenant_1",
            invoice_id="inv_1",
            include_line_items=True,
        )

        assert result is not None
        assert result.invoice_id == "inv_1"
        invoice_service.db.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_invoice_without_line_items(self, invoice_service):
        """Test getting invoice without line items - line 178 not executed."""
        mock_invoice = InvoiceEntity(
            tenant_id="tenant_1",
            invoice_id="inv_2",
            invoice_number="INV-002",
            customer_id="cust_1",
            billing_email="test@example.com",
            billing_address={"street": "123 Main St"},
            issue_date=datetime.now(timezone.utc),
            due_date=datetime.now(timezone.utc) + timedelta(days=30),
            currency="USD",
            subtotal=Decimal("100.00"),
            tax_amount=Decimal("10.00"),
            discount_amount=Decimal("0.00"),
            total_amount=Decimal("110.00"),
            remaining_balance=Decimal("110.00"),
            status=InvoiceStatus.DRAFT,
            payment_status=PaymentStatus.PENDING,
        )

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_invoice)
        invoice_service.db.execute = AsyncMock(return_value=mock_result)

        result = await invoice_service.get_invoice(
            tenant_id="tenant_1",
            invoice_id="inv_2",
            include_line_items=False,
        )

        assert result is not None
        assert result.invoice_id == "inv_2"

    @pytest.mark.asyncio
    async def test_get_invoice_not_found(self, invoice_service):
        """Test getting non-existent invoice returns None - line 186."""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        invoice_service.db.execute = AsyncMock(return_value=mock_result)

        result = await invoice_service.get_invoice(
            tenant_id="tenant_1",
            invoice_id="inv_nonexistent",
        )

        assert result is None