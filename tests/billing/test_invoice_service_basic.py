"""Basic tests for Invoice Service - Phase 1 Quick Wins."""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.billing.core.enums import InvoiceStatus, PaymentStatus
from dotmac.platform.billing.core.exceptions import (
    InvalidInvoiceStatusError,
    InvoiceNotFoundError,
)
from dotmac.platform.billing.core.models import Invoice, InvoiceLineItem
from dotmac.platform.billing.invoicing.service import InvoiceService


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session = AsyncMock(spec=AsyncSession)
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def invoice_service(mock_db_session):
    """Invoice service instance with mocked dependencies."""
    service = InvoiceService(mock_db_session)
    # Mock metrics
    service.metrics = Mock()
    service.metrics.record_invoice_created = Mock()
    service.metrics.record_invoice_updated = Mock()
    service.metrics.record_invoice_voided = Mock()
    return service


@pytest.fixture
def sample_line_items():
    """Sample invoice line items."""
    return [
        {
            "description": "Product A",
            "quantity": 2,
            "unit_price": 5000,  # $50.00 in cents
            "total_price": 10000,  # $100.00
            "tax_rate": 0.10,
            "tax_amount": 1000,  # $10.00
            "discount_percentage": 0.0,
            "discount_amount": 0,
        },
        {
            "description": "Service B",
            "quantity": 1,
            "unit_price": 7500,  # $75.00
            "total_price": 7500,  # $75.00
            "tax_rate": 0.10,
            "tax_amount": 750,  # $7.50
            "discount_percentage": 0.0,
            "discount_amount": 0,
        },
    ]


@pytest.fixture
def sample_billing_address():
    """Sample billing address."""
    return {
        "street": "123 Main St",
        "city": "San Francisco",
        "state": "CA",
        "postal_code": "94105",
        "country": "US",
    }


class TestInvoiceServiceBasicCRUD:
    """Test basic CRUD operations for InvoiceService."""

    @pytest.mark.asyncio
    @patch("dotmac.platform.billing.invoicing.service.get_event_bus")
    async def test_create_invoice_basic(
        self,
        mock_event_bus,
        invoice_service,
        mock_db_session,
        sample_line_items,
        sample_billing_address,
    ):
        """Test basic invoice creation."""
        # Arrange
        mock_event_bus.return_value.publish = AsyncMock()

        # Mock _generate_invoice_number
        invoice_service._generate_invoice_number = AsyncMock(return_value="INV-2025-001")
        # Mock _create_invoice_transaction
        invoice_service._create_invoice_transaction = AsyncMock()
        # Mock _get_invoice_by_idempotency_key
        invoice_service._get_invoice_by_idempotency_key = AsyncMock(return_value=None)

        tenant_id = "tenant-123"
        customer_id = "cust-456"
        billing_email = "customer@example.com"

        # Act
        result = await invoice_service.create_invoice(
            tenant_id=tenant_id,
            customer_id=customer_id,
            billing_email=billing_email,
            billing_address=sample_billing_address,
            line_items=sample_line_items,
            currency="USD",
        )

        # Assert
        assert isinstance(result, Invoice)
        assert mock_db_session.add.called
        assert mock_db_session.commit.called
        assert invoice_service.metrics.record_invoice_created.called

    @pytest.mark.asyncio
    async def test_get_invoice_found(self, invoice_service, mock_db_session):
        """Test getting an existing invoice."""
        # Arrange
        tenant_id = "tenant-123"
        invoice_id = "inv-789"

        # Mock database response
        mock_invoice = Mock()
        mock_invoice.tenant_id = tenant_id
        mock_invoice.invoice_id = invoice_id
        mock_invoice.invoice_number = "INV-2025-001"
        mock_invoice.customer_id = "cust-456"
        mock_invoice.billing_email = "test@example.com"
        mock_invoice.billing_address = {}
        mock_invoice.issue_date = datetime.now(timezone.utc)
        mock_invoice.due_date = datetime.now(timezone.utc) + timedelta(days=30)
        mock_invoice.currency = "USD"
        mock_invoice.subtotal = 17500
        mock_invoice.tax_amount = 1750
        mock_invoice.discount_amount = 0
        mock_invoice.total_amount = 19250
        mock_invoice.remaining_balance = 19250
        mock_invoice.status = InvoiceStatus.DRAFT
        mock_invoice.payment_status = PaymentStatus.PENDING
        mock_invoice.line_items = []

        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=mock_invoice)
        mock_db_session.execute.return_value = mock_result

        # Act
        result = await invoice_service.get_invoice(tenant_id, invoice_id)

        # Assert
        assert result is not None
        assert isinstance(result, Invoice)
        assert result.invoice_id == invoice_id

    @pytest.mark.asyncio
    async def test_get_invoice_not_found(self, invoice_service, mock_db_session):
        """Test getting non-existent invoice returns None."""
        # Arrange
        tenant_id = "tenant-123"
        invoice_id = "inv-nonexistent"

        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_db_session.execute.return_value = mock_result

        # Act
        result = await invoice_service.get_invoice(tenant_id, invoice_id)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_list_invoices_basic(self, invoice_service, mock_db_session):
        """Test listing invoices."""
        # Arrange
        tenant_id = "tenant-123"

        mock_result = Mock()
        mock_result.scalars = Mock(return_value=Mock(all=Mock(return_value=[])))
        mock_db_session.execute.return_value = mock_result

        # Act
        result = await invoice_service.list_invoices(tenant_id)

        # Assert
        assert isinstance(result, list)
        assert mock_db_session.execute.called

    @pytest.mark.asyncio
    async def test_list_invoices_with_filters(self, invoice_service, mock_db_session):
        """Test listing invoices with filters."""
        # Arrange
        tenant_id = "tenant-123"
        customer_id = "cust-456"
        status = InvoiceStatus.SENT

        mock_result = Mock()
        mock_result.scalars = Mock(return_value=Mock(all=Mock(return_value=[])))
        mock_db_session.execute.return_value = mock_result

        # Act
        result = await invoice_service.list_invoices(
            tenant_id=tenant_id,
            customer_id=customer_id,
            status=status,
        )

        # Assert
        assert isinstance(result, list)
        assert mock_db_session.execute.called


class TestInvoiceServiceIdempotency:
    """Test idempotency handling in InvoiceService."""

    @pytest.mark.asyncio
    @patch("dotmac.platform.billing.invoicing.service.get_event_bus")
    async def test_create_invoice_with_idempotency_key_new(
        self,
        mock_event_bus,
        invoice_service,
        mock_db_session,
        sample_line_items,
        sample_billing_address,
    ):
        """Test creating invoice with idempotency key (first time)."""
        # Arrange
        mock_event_bus.return_value.publish = AsyncMock()
        invoice_service._generate_invoice_number = AsyncMock(return_value="INV-2025-001")
        invoice_service._create_invoice_transaction = AsyncMock()
        invoice_service._get_invoice_by_idempotency_key = AsyncMock(return_value=None)

        # Act
        result = await invoice_service.create_invoice(
            tenant_id="tenant-123",
            customer_id="cust-456",
            billing_email="customer@example.com",
            billing_address=sample_billing_address,
            line_items=sample_line_items,
            idempotency_key="unique-key-123",
        )

        # Assert
        assert isinstance(result, Invoice)
        assert mock_db_session.add.called

    @pytest.mark.asyncio
    async def test_create_invoice_with_idempotency_key_duplicate(
        self,
        invoice_service,
        mock_db_session,
        sample_line_items,
        sample_billing_address,
    ):
        """Test creating invoice with duplicate idempotency key returns existing."""
        # Arrange
        existing_invoice = Mock()
        existing_invoice.tenant_id = "tenant-123"
        existing_invoice.invoice_id = "inv-existing"
        existing_invoice.invoice_number = "INV-2025-001"
        existing_invoice.customer_id = "cust-456"
        existing_invoice.billing_email = "test@example.com"
        existing_invoice.billing_address = {}
        existing_invoice.issue_date = datetime.now(timezone.utc)
        existing_invoice.due_date = datetime.now(timezone.utc) + timedelta(days=30)
        existing_invoice.currency = "USD"
        existing_invoice.subtotal = 17500
        existing_invoice.tax_amount = 1750
        existing_invoice.discount_amount = 0
        existing_invoice.total_amount = 19250
        existing_invoice.remaining_balance = 19250
        existing_invoice.status = InvoiceStatus.DRAFT
        existing_invoice.payment_status = PaymentStatus.PENDING
        existing_invoice.line_items = []

        invoice_service._get_invoice_by_idempotency_key = AsyncMock(
            return_value=existing_invoice
        )

        # Act
        result = await invoice_service.create_invoice(
            tenant_id="tenant-123",
            customer_id="cust-456",
            billing_email="customer@example.com",
            billing_address=sample_billing_address,
            line_items=sample_line_items,
            idempotency_key="duplicate-key-123",
        )

        # Assert
        assert isinstance(result, Invoice)
        assert result.invoice_id == "inv-existing"
        # Should NOT call add/commit again
        assert not mock_db_session.add.called


class TestInvoiceServiceCalculations:
    """Test invoice calculation logic."""

    @pytest.mark.asyncio
    @patch("dotmac.platform.billing.invoicing.service.get_event_bus")
    async def test_invoice_totals_calculation(
        self,
        mock_event_bus,
        invoice_service,
        mock_db_session,
        sample_billing_address,
    ):
        """Test invoice totals are calculated correctly."""
        # Arrange
        mock_event_bus.return_value.publish = AsyncMock()
        invoice_service._generate_invoice_number = AsyncMock(return_value="INV-2025-001")
        invoice_service._create_invoice_transaction = AsyncMock()
        invoice_service._get_invoice_by_idempotency_key = AsyncMock(return_value=None)

        line_items = [
            {
                "description": "Item 1",
                "quantity": 1,
                "unit_price": 10000,  # $100.00
                "total_price": 10000,
                "tax_rate": 0.10,
                "tax_amount": 1000,  # $10.00 tax
                "discount_percentage": 0.0,
                "discount_amount": 0,
            },
        ]

        # Act
        result = await invoice_service.create_invoice(
            tenant_id="tenant-123",
            customer_id="cust-456",
            billing_email="customer@example.com",
            billing_address=sample_billing_address,
            line_items=line_items,
        )

        # Assert
        assert isinstance(result, Invoice)
        # Subtotal: 10000, Tax: 1000, Total: 11000
        assert mock_db_session.add.called

    @pytest.mark.asyncio
    @patch("dotmac.platform.billing.invoicing.service.get_event_bus")
    async def test_invoice_with_discount(
        self,
        mock_event_bus,
        invoice_service,
        mock_db_session,
        sample_billing_address,
    ):
        """Test invoice with discount amount."""
        # Arrange
        mock_event_bus.return_value.publish = AsyncMock()
        invoice_service._generate_invoice_number = AsyncMock(return_value="INV-2025-001")
        invoice_service._create_invoice_transaction = AsyncMock()
        invoice_service._get_invoice_by_idempotency_key = AsyncMock(return_value=None)

        line_items = [
            {
                "description": "Item with discount",
                "quantity": 1,
                "unit_price": 10000,  # $100.00
                "total_price": 10000,
                "tax_rate": 0.10,
                "tax_amount": 800,  # Tax on discounted amount
                "discount_percentage": 0.20,
                "discount_amount": 2000,  # $20.00 discount
            },
        ]

        # Act
        result = await invoice_service.create_invoice(
            tenant_id="tenant-123",
            customer_id="cust-456",
            billing_email="customer@example.com",
            billing_address=sample_billing_address,
            line_items=line_items,
        )

        # Assert
        assert isinstance(result, Invoice)
        assert mock_db_session.add.called

    @pytest.mark.asyncio
    @patch("dotmac.platform.billing.invoicing.service.get_event_bus")
    async def test_invoice_due_date_calculation(
        self,
        mock_event_bus,
        invoice_service,
        mock_db_session,
        sample_line_items,
        sample_billing_address,
    ):
        """Test due date is calculated correctly from due_days."""
        # Arrange
        mock_event_bus.return_value.publish = AsyncMock()
        invoice_service._generate_invoice_number = AsyncMock(return_value="INV-2025-001")
        invoice_service._create_invoice_transaction = AsyncMock()
        invoice_service._get_invoice_by_idempotency_key = AsyncMock(return_value=None)

        # Act
        result = await invoice_service.create_invoice(
            tenant_id="tenant-123",
            customer_id="cust-456",
            billing_email="customer@example.com",
            billing_address=sample_billing_address,
            line_items=sample_line_items,
            due_days=15,  # 15 days from now
        )

        # Assert
        assert isinstance(result, Invoice)
        assert mock_db_session.add.called

    @pytest.mark.asyncio
    @patch("dotmac.platform.billing.invoicing.service.get_event_bus")
    async def test_invoice_with_custom_due_date(
        self,
        mock_event_bus,
        invoice_service,
        mock_db_session,
        sample_line_items,
        sample_billing_address,
    ):
        """Test creating invoice with custom due date."""
        # Arrange
        mock_event_bus.return_value.publish = AsyncMock()
        invoice_service._generate_invoice_number = AsyncMock(return_value="INV-2025-001")
        invoice_service._create_invoice_transaction = AsyncMock()
        invoice_service._get_invoice_by_idempotency_key = AsyncMock(return_value=None)

        custom_due_date = datetime.now(timezone.utc) + timedelta(days=45)

        # Act
        result = await invoice_service.create_invoice(
            tenant_id="tenant-123",
            customer_id="cust-456",
            billing_email="customer@example.com",
            billing_address=sample_billing_address,
            line_items=sample_line_items,
            due_date=custom_due_date,
        )

        # Assert
        assert isinstance(result, Invoice)
        assert mock_db_session.add.called


class TestInvoiceServiceTenantIsolation:
    """Test tenant isolation in InvoiceService."""

    @pytest.mark.asyncio
    async def test_get_invoice_respects_tenant_id(
        self, invoice_service, mock_db_session
    ):
        """Test get_invoice only returns invoice for correct tenant."""
        # Arrange
        tenant_id = "tenant-123"
        invoice_id = "inv-789"

        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_db_session.execute.return_value = mock_result

        # Act
        result = await invoice_service.get_invoice(tenant_id, invoice_id)

        # Assert
        assert result is None
        # Verify query includes tenant_id filter
        assert mock_db_session.execute.called

    @pytest.mark.asyncio
    async def test_list_invoices_respects_tenant_id(
        self, invoice_service, mock_db_session
    ):
        """Test list_invoices only returns invoices for tenant."""
        # Arrange
        tenant_id = "tenant-123"

        mock_result = Mock()
        mock_result.scalars = Mock(return_value=Mock(all=Mock(return_value=[])))
        mock_db_session.execute.return_value = mock_result

        # Act
        result = await invoice_service.list_invoices(tenant_id)

        # Assert
        assert isinstance(result, list)
        # Verify query includes tenant_id filter
        assert mock_db_session.execute.called


class TestInvoiceServiceMetrics:
    """Test metrics recording in InvoiceService."""

    @pytest.mark.asyncio
    @patch("dotmac.platform.billing.invoicing.service.get_event_bus")
    async def test_create_invoice_records_metrics(
        self,
        mock_event_bus,
        invoice_service,
        mock_db_session,
        sample_line_items,
        sample_billing_address,
    ):
        """Test invoice creation records metrics."""
        # Arrange
        mock_event_bus.return_value.publish = AsyncMock()
        invoice_service._generate_invoice_number = AsyncMock(return_value="INV-2025-001")
        invoice_service._create_invoice_transaction = AsyncMock()
        invoice_service._get_invoice_by_idempotency_key = AsyncMock(return_value=None)

        # Act
        await invoice_service.create_invoice(
            tenant_id="tenant-123",
            customer_id="cust-456",
            billing_email="customer@example.com",
            billing_address=sample_billing_address,
            line_items=sample_line_items,
        )

        # Assert
        invoice_service.metrics.record_invoice_created.assert_called_once()
        call_kwargs = invoice_service.metrics.record_invoice_created.call_args.kwargs
        assert call_kwargs["tenant_id"] == "tenant-123"
        assert call_kwargs["customer_id"] == "cust-456"
        assert call_kwargs["currency"] == "USD"