"""
Test suite for Invoice Service with tenant isolation
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.billing.core.enums import InvoiceStatus, PaymentStatus
from dotmac.platform.billing.core.exceptions import (
    InvalidInvoiceStatusError,
    InvoiceNotFoundError,
)
from dotmac.platform.billing.invoicing.service import InvoiceService


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    session = AsyncMock(spec=AsyncSession)
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def invoice_service(mock_db_session):
    """Invoice service instance"""
    return InvoiceService(mock_db_session)


@pytest.fixture
def sample_tenant_id():
    """Sample tenant ID"""
    return "tenant-123"


@pytest.fixture
def sample_customer_id():
    """Sample customer ID"""
    return "550e8400-e29b-41d4-a716-446655440003"


@pytest.fixture
def sample_line_items():
    """Sample invoice line items"""
    return [
        {
            "description": "Product A",
            "quantity": 2,
            "unit_price": 5000,  # $50.00
            "total_price": 10000,  # $100.00
            "tax_rate": 10.0,
            "tax_amount": 1000,  # $10.00
        },
        {
            "description": "Service B",
            "quantity": 1,
            "unit_price": 7500,  # $75.00
            "total_price": 7500,  # $75.00
            "tax_rate": 10.0,
            "tax_amount": 750,  # $7.50
        },
    ]


@pytest.fixture
def sample_billing_address():
    """Sample billing address"""
    return {
        "street": "123 Main St",
        "city": "San Francisco",
        "state": "CA",
        "postal_code": "94105",
        "country": "US",
    }


class TestInvoiceService:
    """Test invoice service functionality"""

    @pytest.mark.asyncio
    async def test_create_invoice_with_tenant_isolation(
        self,
        invoice_service,
        mock_db_session,
        sample_tenant_id,
        sample_customer_id,
        sample_line_items,
        sample_billing_address,
    ):
        """Test creating an invoice with tenant isolation"""

        # Mock the database operations for all queries
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # No existing invoices
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Create invoice
        result = await invoice_service.create_invoice(
            tenant_id=sample_tenant_id,
            customer_id=sample_customer_id,
            billing_email="customer@example.com",
            billing_address=sample_billing_address,
            line_items=sample_line_items,
            currency="USD",
            due_days=30,
            notes="Test invoice",
            created_by="test-user",
        )

        # Verify tenant ID was set
        mock_db_session.add.assert_called()
        added_invoice = mock_db_session.add.call_args_list[0][0][0]
        assert added_invoice.tenant_id == sample_tenant_id
        assert added_invoice.customer_id == sample_customer_id
        assert added_invoice.subtotal == 17500  # $175.00
        assert added_invoice.tax_amount == 1750  # $17.50
        assert added_invoice.total_amount == 19250  # $192.50
        assert added_invoice.status == InvoiceStatus.DRAFT

    @pytest.mark.asyncio
    async def test_create_invoice_with_idempotency(
        self,
        invoice_service,
        mock_db_session,
        sample_tenant_id,
        sample_customer_id,
        sample_line_items,
        sample_billing_address,
    ):
        """Test idempotency in invoice creation"""

        idempotency_key = "test-key-123"

        # Mock existing invoice with same idempotency key
        existing_invoice = MagicMock()
        existing_invoice.tenant_id = sample_tenant_id
        existing_invoice.invoice_id = "existing-invoice-id"
        existing_invoice.total_amount = 10000

        mock_db_session.execute.return_value.scalar_one_or_none.return_value = existing_invoice

        # Create invoice with same idempotency key
        result = await invoice_service.create_invoice(
            tenant_id=sample_tenant_id,
            customer_id=sample_customer_id,
            billing_email="customer@example.com",
            billing_address=sample_billing_address,
            line_items=sample_line_items,
            idempotency_key=idempotency_key,
        )

        # Verify no new invoice was added
        mock_db_session.add.assert_not_called()
        mock_db_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_invoice_with_tenant_isolation(
        self, invoice_service, mock_db_session, sample_tenant_id
    ):
        """Test getting invoice with tenant isolation"""

        invoice_id = str(uuid4())

        # Mock invoice entity
        mock_invoice = MagicMock()
        mock_invoice.tenant_id = sample_tenant_id
        mock_invoice.invoice_id = invoice_id
        mock_invoice.total_amount = 10000

        mock_db_session.execute.return_value.scalar_one_or_none.return_value = mock_invoice

        # Get invoice
        result = await invoice_service.get_invoice(sample_tenant_id, invoice_id)

        # Verify query included tenant_id
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_invoice_wrong_tenant(
        self, invoice_service, mock_db_session, sample_tenant_id
    ):
        """Test that invoice from wrong tenant is not accessible"""

        invoice_id = str(uuid4())
        wrong_tenant_id = "wrong-tenant-456"

        # Mock no invoice found (wrong tenant)
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None

        # Get invoice with wrong tenant
        result = await invoice_service.get_invoice(wrong_tenant_id, invoice_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_list_invoices_with_filtering(
        self, invoice_service, mock_db_session, sample_tenant_id, sample_customer_id
    ):
        """Test listing invoices with filtering and tenant isolation"""

        # Mock invoice entities
        mock_invoices = [MagicMock() for _ in range(3)]
        for i, inv in enumerate(mock_invoices):
            inv.tenant_id = sample_tenant_id
            inv.invoice_id = str(uuid4())
            inv.customer_id = sample_customer_id
            inv.status = InvoiceStatus.OPEN

        mock_db_session.execute.return_value.scalars.return_value.all.return_value = mock_invoices

        # List invoices with filters
        result = await invoice_service.list_invoices(
            tenant_id=sample_tenant_id,
            customer_id=sample_customer_id,
            status=InvoiceStatus.OPEN,
            limit=10,
        )

        # Verify query was called
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_finalize_invoice(self, invoice_service, mock_db_session, sample_tenant_id):
        """Test finalizing a draft invoice"""

        invoice_id = str(uuid4())

        # Mock draft invoice
        mock_invoice = MagicMock()
        mock_invoice.tenant_id = sample_tenant_id
        mock_invoice.invoice_id = invoice_id
        mock_invoice.status = InvoiceStatus.DRAFT

        mock_db_session.execute.return_value.scalar_one_or_none.return_value = mock_invoice

        # Finalize invoice
        result = await invoice_service.finalize_invoice(sample_tenant_id, invoice_id)

        # Verify status was updated
        assert mock_invoice.status == InvoiceStatus.OPEN
        mock_db_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_finalize_non_draft_invoice_fails(
        self, invoice_service, mock_db_session, sample_tenant_id
    ):
        """Test that finalizing a non-draft invoice fails"""

        invoice_id = str(uuid4())

        # Mock open invoice
        mock_invoice = MagicMock()
        mock_invoice.tenant_id = sample_tenant_id
        mock_invoice.invoice_id = invoice_id
        mock_invoice.status = InvoiceStatus.OPEN

        mock_db_session.execute.return_value.scalar_one_or_none.return_value = mock_invoice

        # Try to finalize open invoice
        with pytest.raises(InvalidInvoiceStatusError):
            await invoice_service.finalize_invoice(sample_tenant_id, invoice_id)

    @pytest.mark.asyncio
    async def test_void_invoice(self, invoice_service, mock_db_session, sample_tenant_id):
        """Test voiding an invoice"""

        invoice_id = str(uuid4())

        # Mock open invoice
        mock_invoice = MagicMock()
        mock_invoice.tenant_id = sample_tenant_id
        mock_invoice.invoice_id = invoice_id
        mock_invoice.status = InvoiceStatus.OPEN
        mock_invoice.payment_status = PaymentStatus.PENDING
        mock_invoice.internal_notes = None

        mock_db_session.execute.return_value.scalar_one_or_none.return_value = mock_invoice

        # Void invoice
        result = await invoice_service.void_invoice(
            sample_tenant_id, invoice_id, reason="Test void", voided_by="test-user"
        )

        # Verify status was updated
        assert mock_invoice.status == InvoiceStatus.VOID
        assert mock_invoice.voided_at is not None
        assert "Voided: Test void" in mock_invoice.internal_notes
        mock_db_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_void_paid_invoice_fails(
        self, invoice_service, mock_db_session, sample_tenant_id
    ):
        """Test that voiding a paid invoice fails"""

        invoice_id = str(uuid4())

        # Mock paid invoice
        mock_invoice = MagicMock()
        mock_invoice.tenant_id = sample_tenant_id
        mock_invoice.invoice_id = invoice_id
        mock_invoice.status = InvoiceStatus.PAID
        mock_invoice.payment_status = PaymentStatus.SUCCEEDED

        mock_db_session.execute.return_value.scalar_one_or_none.return_value = mock_invoice

        # Try to void paid invoice
        with pytest.raises(InvalidInvoiceStatusError):
            await invoice_service.void_invoice(sample_tenant_id, invoice_id)

    @pytest.mark.asyncio
    async def test_mark_invoice_paid(self, invoice_service, mock_db_session, sample_tenant_id):
        """Test marking invoice as paid"""

        invoice_id = str(uuid4())
        payment_id = str(uuid4())

        # Mock open invoice
        mock_invoice = MagicMock()
        mock_invoice.tenant_id = sample_tenant_id
        mock_invoice.invoice_id = invoice_id
        mock_invoice.status = InvoiceStatus.OPEN
        mock_invoice.payment_status = PaymentStatus.PENDING
        mock_invoice.total_amount = 10000

        mock_db_session.execute.return_value.scalar_one_or_none.return_value = mock_invoice

        # Mark as paid
        result = await invoice_service.mark_invoice_paid(
            sample_tenant_id, invoice_id, payment_id=payment_id
        )

        # Verify status was updated
        assert mock_invoice.status == InvoiceStatus.PAID
        assert mock_invoice.payment_status == PaymentStatus.SUCCEEDED
        assert mock_invoice.remaining_balance == 0
        assert mock_invoice.paid_at is not None
        mock_db_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_apply_credit_to_invoice(
        self, invoice_service, mock_db_session, sample_tenant_id
    ):
        """Test applying credit to invoice"""

        invoice_id = str(uuid4())
        credit_application_id = str(uuid4())
        credit_amount = 5000  # $50.00

        # Mock open invoice
        mock_invoice = MagicMock()
        mock_invoice.tenant_id = sample_tenant_id
        mock_invoice.invoice_id = invoice_id
        mock_invoice.invoice_number = "INV-2024-000001"
        mock_invoice.currency = "USD"
        mock_invoice.customer_id = "550e8400-e29b-41d4-a716-446655440004"
        mock_invoice.status = InvoiceStatus.OPEN
        mock_invoice.total_amount = 10000  # $100.00
        mock_invoice.total_credits_applied = 0
        mock_invoice.remaining_balance = 10000
        mock_invoice.credit_applications = []

        mock_db_session.execute.return_value.scalar_one_or_none.return_value = mock_invoice

        # Apply credit
        result = await invoice_service.apply_credit_to_invoice(
            sample_tenant_id, invoice_id, credit_amount, credit_application_id
        )

        # Verify credit was applied
        assert mock_invoice.total_credits_applied == 5000
        assert mock_invoice.remaining_balance == 5000
        assert credit_application_id in mock_invoice.credit_applications
        mock_db_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_check_overdue_invoices(
        self, invoice_service, mock_db_session, sample_tenant_id
    ):
        """Test checking and marking overdue invoices"""

        # Mock overdue invoices
        mock_invoices = []
        for i in range(2):
            inv = MagicMock()
            inv.tenant_id = sample_tenant_id
            inv.invoice_id = str(uuid4())
            inv.status = InvoiceStatus.OPEN
            inv.due_date = datetime.utcnow() - timedelta(days=10)  # 10 days overdue
            inv.payment_status = PaymentStatus.PENDING
            mock_invoices.append(inv)

        mock_db_session.execute.return_value.scalars.return_value.all.return_value = mock_invoices

        # Check overdue invoices
        result = await invoice_service.check_overdue_invoices(sample_tenant_id)

        # Verify status was updated
        for inv in mock_invoices:
            assert inv.status == InvoiceStatus.OVERDUE
        mock_db_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_invoice_number_generation(
        self, invoice_service, mock_db_session, sample_tenant_id
    ):
        """Test invoice number generation"""

        # Mock no existing invoices
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None

        # Generate first invoice number
        invoice_number = await invoice_service._generate_invoice_number(sample_tenant_id)

        year = datetime.utcnow().year
        assert invoice_number == f"INV-{year}-000001"

        # Mock existing invoice
        mock_last_invoice = MagicMock()
        mock_last_invoice.invoice_number = f"INV-{year}-000005"
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = mock_last_invoice

        # Generate next invoice number
        invoice_number = await invoice_service._generate_invoice_number(sample_tenant_id)
        assert invoice_number == f"INV-{year}-000006"