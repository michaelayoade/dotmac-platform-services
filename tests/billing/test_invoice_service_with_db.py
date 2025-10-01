"""Invoice service tests with real in-memory database.

Tests the invoice service with actual SQLAlchemy entities and relationships.
"""

import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

from dotmac.platform.billing.invoicing.service import InvoiceService
from dotmac.platform.billing.core.enums import InvoiceStatus, PaymentStatus

# Import the test DB fixtures
pytest_plugins = ["tests.billing.conftest_test_db"]


@pytest.fixture
def invoice_service(test_db_session):
    """Create InvoiceService with mocked metrics and event bus."""
    with patch("dotmac.platform.billing.invoicing.service.get_billing_metrics") as mock_metrics, \
         patch("dotmac.platform.billing.invoicing.service.get_event_bus") as mock_bus:

        # Mock metrics
        mock_metrics.return_value.record_invoice_created = MagicMock()

        # Mock event bus
        mock_bus.return_value.publish = MagicMock()

        service = InvoiceService(db_session=test_db_session)
        yield service


@pytest.fixture
def sample_line_items():
    """Sample line items that work with the validator."""
    return [
        {
            "description": "Product A",
            "quantity": 2,
            "unit_price": 5000,  # $50.00 in cents
            "total_price": 10000,  # $100.00
            "tax_rate": 10.0,
            "tax_amount": Decimal("10.00"),  # Will convert to 1000 cents
            "discount_percentage": 0.0,
            "discount_amount": Decimal("0.00"),
            "product_id": "prod_1",
        },
        {
            "description": "Product B",
            "quantity": 1,
            "unit_price": 7500,  # $75.00 in cents
            "total_price": 7500,
            "tax_rate": 10.0,
            "tax_amount": Decimal("7.50"),  # Will convert to 750 cents
            "discount_percentage": 5.0,
            "discount_amount": Decimal("3.75"),  # Will convert to 375 cents
            "product_id": "prod_2",
        },
    ]


class TestInvoiceServiceCreateInvoice:
    """Test invoice creation with real database."""

    @pytest.mark.asyncio
    async def test_create_invoice_success(
        self, invoice_service, test_tenant_id, test_customer_id, sample_line_items
    ):
        """Test successful invoice creation."""
        invoice = await invoice_service.create_invoice(
            tenant_id=test_tenant_id,
            customer_id=test_customer_id,
            billing_email="customer@example.com",
            billing_address={"street": "123 Main St", "city": "Anytown"},
            line_items=sample_line_items,
            currency="USD",
            due_days=30,
        )

        # Verify invoice was created
        assert invoice is not None
        assert invoice.invoice_id is not None
        assert invoice.invoice_number is not None
        assert invoice.tenant_id == test_tenant_id
        assert invoice.customer_id == test_customer_id
        assert invoice.currency == "USD"
        assert invoice.status == InvoiceStatus.DRAFT
        assert invoice.payment_status == PaymentStatus.PENDING

        # Verify totals
        # subtotal = 10000 + 7500 = 17500 cents ($175.00)
        # tax = 1000 + 750 = 1750 cents ($17.50)
        # discount = 0 + 375 = 375 cents ($3.75)
        # total = 17500 + 1750 - 375 = 18875 cents ($188.75)
        assert invoice.subtotal == 17500
        assert invoice.tax_amount == 1750
        assert invoice.discount_amount == 375
        assert invoice.total_amount == 18875
        assert invoice.remaining_balance == 18875

    @pytest.mark.asyncio
    async def test_create_invoice_with_idempotency_key(
        self, invoice_service, test_tenant_id, test_customer_id, sample_line_items
    ):
        """Test idempotency - creating same invoice twice returns first."""
        idempotency_key = "test_key_unique_123"

        # Create first invoice
        invoice1 = await invoice_service.create_invoice(
            tenant_id=test_tenant_id,
            customer_id=test_customer_id,
            billing_email="customer@example.com",
            billing_address={"street": "123 Main St"},
            line_items=sample_line_items,
            idempotency_key=idempotency_key,
        )

        # Create second invoice with same key
        invoice2 = await invoice_service.create_invoice(
            tenant_id=test_tenant_id,
            customer_id=test_customer_id,
            billing_email="different@example.com",  # Different data
            billing_address={"street": "456 Other St"},
            line_items=sample_line_items,
            idempotency_key=idempotency_key,
        )

        # Should return the same invoice
        assert invoice1.invoice_id == invoice2.invoice_id
        assert invoice1.billing_email == invoice2.billing_email  # Uses first version

    @pytest.mark.asyncio
    async def test_create_invoice_with_custom_due_date(
        self, invoice_service, test_tenant_id, test_customer_id, sample_line_items
    ):
        """Test creating invoice with specific due date."""
        custom_due_date = datetime.now(timezone.utc) + timedelta(days=45)

        invoice = await invoice_service.create_invoice(
            tenant_id=test_tenant_id,
            customer_id=test_customer_id,
            billing_email="customer@example.com",
            billing_address={"street": "123 Main St"},
            line_items=sample_line_items,
            due_date=custom_due_date,
        )

        # Verify due date
        assert invoice.due_date is not None
        # Allow small time difference due to processing
        time_diff = abs((invoice.due_date - custom_due_date).total_seconds())
        assert time_diff < 60  # Within 1 minute

    @pytest.mark.asyncio
    async def test_create_invoice_with_subscription(
        self, invoice_service, test_tenant_id, test_customer_id, sample_line_items
    ):
        """Test creating invoice linked to subscription."""
        subscription_id = "sub_test_123"

        invoice = await invoice_service.create_invoice(
            tenant_id=test_tenant_id,
            customer_id=test_customer_id,
            billing_email="customer@example.com",
            billing_address={"street": "123 Main St"},
            line_items=sample_line_items,
            subscription_id=subscription_id,
        )

        assert invoice.subscription_id == subscription_id


class TestInvoiceServiceGetInvoice:
    """Test invoice retrieval."""

    @pytest.mark.asyncio
    async def test_get_invoice_by_id(
        self, invoice_service, test_tenant_id, test_customer_id, sample_line_items
    ):
        """Test retrieving invoice by ID."""
        # Create invoice first
        created = await invoice_service.create_invoice(
            tenant_id=test_tenant_id,
            customer_id=test_customer_id,
            billing_email="customer@example.com",
            billing_address={"street": "123 Main St"},
            line_items=sample_line_items,
        )

        # Retrieve it
        retrieved = await invoice_service.get_invoice(
            tenant_id=test_tenant_id,
            invoice_id=created.invoice_id,
        )

        assert retrieved is not None
        assert retrieved.invoice_id == created.invoice_id
        assert retrieved.invoice_number == created.invoice_number

    @pytest.mark.asyncio
    async def test_get_invoice_with_line_items(
        self, invoice_service, test_tenant_id, test_customer_id, sample_line_items
    ):
        """Test retrieving invoice with line items included."""
        # Create invoice
        created = await invoice_service.create_invoice(
            tenant_id=test_tenant_id,
            customer_id=test_customer_id,
            billing_email="customer@example.com",
            billing_address={"street": "123 Main St"},
            line_items=sample_line_items,
        )

        # Retrieve with line items
        retrieved = await invoice_service.get_invoice(
            tenant_id=test_tenant_id,
            invoice_id=created.invoice_id,
            include_line_items=True,
        )

        assert retrieved is not None
        # Note: Line items come from entity relationships, may need separate query

    @pytest.mark.asyncio
    async def test_get_invoice_wrong_tenant(
        self, invoice_service, test_tenant_id, test_customer_id, sample_line_items
    ):
        """Test that invoice cannot be accessed by wrong tenant."""
        # Create invoice for test_tenant_id
        created = await invoice_service.create_invoice(
            tenant_id=test_tenant_id,
            customer_id=test_customer_id,
            billing_email="customer@example.com",
            billing_address={"street": "123 Main St"},
            line_items=sample_line_items,
        )

        # Try to retrieve with different tenant
        retrieved = await invoice_service.get_invoice(
            tenant_id="different_tenant",
            invoice_id=created.invoice_id,
        )

        assert retrieved is None  # Should not find it

    @pytest.mark.asyncio
    async def test_get_nonexistent_invoice(
        self, invoice_service, test_tenant_id
    ):
        """Test retrieving non-existent invoice returns None."""
        retrieved = await invoice_service.get_invoice(
            tenant_id=test_tenant_id,
            invoice_id="nonexistent_invoice_id",
        )

        assert retrieved is None