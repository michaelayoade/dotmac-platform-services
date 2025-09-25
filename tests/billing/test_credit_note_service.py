"""
Tests for credit note service
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from dotmac.platform.billing.core.enums import (
    CreditNoteStatus,
    CreditReason,
    CreditType,
    InvoiceStatus,
    PaymentStatus,
)
from dotmac.platform.billing.core.exceptions import (
    CreditNoteNotFoundError,
    InvalidCreditNoteStatusError,
    InsufficientCreditError,
)
from dotmac.platform.billing.core.models import CreditNote
from dotmac.platform.billing.credit_notes.service import CreditNoteService
from dotmac.platform.billing.core.entities import InvoiceEntity, CreditNoteEntity


@pytest.fixture
def mock_db():
    """Mock database session"""
    db = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest.fixture
def mock_invoice():
    """Mock invoice entity"""
    invoice = MagicMock(spec=InvoiceEntity)
    invoice.invoice_id = "inv_123"
    invoice.customer_id = "550e8400-e29b-41d4-a716-446655440001"
    invoice.total_amount = 10000  # $100.00
    invoice.currency = "USD"
    invoice.status = InvoiceStatus.PAID
    invoice.payment_status = PaymentStatus.SUCCEEDED
    return invoice


@pytest.fixture
def credit_note_service(mock_db):
    """Credit note service with mocked database"""
    service = CreditNoteService(mock_db)
    service.metrics = MagicMock()  # Mock metrics
    return service


class TestCreditNoteService:
    """Test credit note service functionality"""

    @pytest.mark.asyncio
    async def test_create_credit_note_success(self, credit_note_service, mock_invoice):
        """Test successful credit note creation"""
        
        # Mock dependencies
        credit_note_service._get_invoice = AsyncMock(return_value=mock_invoice)
        credit_note_service._generate_credit_note_number = AsyncMock(return_value="CN-2024-000001")
        credit_note_service._create_credit_note_transaction = AsyncMock()
        
        # Mock database operations
        credit_note_service.db.add = MagicMock()
        credit_note_service.db.commit = AsyncMock()
        credit_note_service.db.refresh = AsyncMock()
        
        # Create line items
        line_items = [
            {
                "description": "Refund for Product A",
                "quantity": 1,
                "unit_price": 5000,
                "amount": 5000,
                "original_invoice_item_id": "item_123",
            }
        ]
        
        # Call service method
        result = await credit_note_service.create_credit_note(
            tenant_id="tenant_123",
            invoice_id="inv_123",
            reason=CreditReason.CUSTOMER_REQUEST,
            line_items=line_items,
            notes="Customer returned product",
            created_by="user_123",
            auto_apply=False,
        )
        
        # Verify interactions
        credit_note_service._get_invoice.assert_called_once_with("tenant_123", "inv_123")
        credit_note_service._generate_credit_note_number.assert_called_once_with("tenant_123")
        credit_note_service.db.add.assert_called_once()
        credit_note_service.db.commit.assert_called_once()
        credit_note_service.metrics.record_credit_note_created.assert_called_once()
        
        # Verify result type
        assert isinstance(result, CreditNote)

    @pytest.mark.asyncio
    async def test_create_credit_note_invalid_invoice(self, credit_note_service):
        """Test credit note creation with invalid invoice"""
        
        # Mock invoice not found
        credit_note_service._get_invoice = AsyncMock(return_value=None)
        
        with pytest.raises(ValueError, match="Invoice inv_456 not found"):
            await credit_note_service.create_credit_note(
                tenant_id="tenant_123",
                invoice_id="inv_456",
                reason=CreditReason.BILLING_ERROR,
                line_items=[{"description": "Test", "amount": 1000}],
            )

    @pytest.mark.asyncio
    async def test_create_credit_note_exceeds_invoice_amount(self, credit_note_service, mock_invoice):
        """Test credit note creation that exceeds invoice amount"""
        
        credit_note_service._get_invoice = AsyncMock(return_value=mock_invoice)
        
        # Create line items that exceed invoice total
        line_items = [
            {"description": "Over-refund", "amount": 15000}  # More than invoice total of 10000
        ]
        
        with pytest.raises(ValueError, match="Credit amount 15000 exceeds invoice amount 10000"):
            await credit_note_service.create_credit_note(
                tenant_id="tenant_123",
                invoice_id="inv_123",
                reason=CreditReason.CUSTOMER_REQUEST,
                line_items=line_items,
            )

    @pytest.mark.asyncio
    async def test_issue_credit_note_success(self, credit_note_service):
        """Test successful credit note issuance"""

        # Create a mock credit note entity with real values
        credit_note = MagicMock(spec=CreditNoteEntity)
        credit_note.tenant_id = "tenant_123"
        credit_note.credit_note_id = "cn_123"
        credit_note.credit_note_number = "CN-2024-000001"
        credit_note.idempotency_key = None
        credit_note.created_by = "user_123"
        credit_note.customer_id = "550e8400-e29b-41d4-a716-446655440001"
        credit_note.invoice_id = "inv_123"
        credit_note.issue_date = datetime.utcnow()
        credit_note.currency = "USD"
        credit_note.credit_type = CreditType.REFUND
        credit_note.reason = CreditReason.CUSTOMER_REQUEST
        credit_note.reason_description = None
        credit_note.status = CreditNoteStatus.DRAFT
        credit_note.subtotal = 5000
        credit_note.tax_amount = 0
        credit_note.total_amount = 5000
        credit_note.remaining_credit_amount = 5000
        credit_note.auto_apply_to_invoice = True
        credit_note.notes = None
        credit_note.internal_notes = None
        credit_note.extra_data = {}
        credit_note.created_at = datetime.utcnow()
        credit_note.updated_at = datetime.utcnow()
        credit_note.voided_at = None
        credit_note.line_items = [
            MagicMock(
                line_item_id="li_123",
                description="Test item",
                quantity=1,
                unit_price=5000,
                total_price=5000,
                original_invoice_line_item_id=None,
                product_id=None,
                tax_rate=0.0,
                tax_amount=0,
                extra_data={}
            )
        ]

        credit_note_service._get_credit_note_entity = AsyncMock(return_value=credit_note)

        result = await credit_note_service.issue_credit_note("tenant_123", "cn_123")
        
        # Verify status change
        assert credit_note.status == CreditNoteStatus.ISSUED
        assert credit_note.issued_at is not None
        
        # Verify database operations
        credit_note_service.db.commit.assert_called_once()
        credit_note_service.db.refresh.assert_called_once_with(credit_note)
        credit_note_service.metrics.record_credit_note_issued.assert_called_once()

    @pytest.mark.asyncio
    async def test_issue_credit_note_not_found(self, credit_note_service):
        """Test issuing non-existent credit note"""
        
        credit_note_service._get_credit_note_entity = AsyncMock(return_value=None)
        
        with pytest.raises(CreditNoteNotFoundError):
            await credit_note_service.issue_credit_note("tenant_123", "cn_nonexistent")

    @pytest.mark.asyncio
    async def test_issue_credit_note_invalid_status(self, credit_note_service):
        """Test issuing credit note with invalid status"""
        
        credit_note = MagicMock(spec=CreditNoteEntity)
        credit_note.status = CreditNoteStatus.ISSUED  # Already issued
        
        credit_note_service._get_credit_note_entity = AsyncMock(return_value=credit_note)
        
        with pytest.raises(InvalidCreditNoteStatusError):
            await credit_note_service.issue_credit_note("tenant_123", "cn_123")

    @pytest.mark.asyncio
    async def test_void_credit_note_success(self, credit_note_service):
        """Test successful credit note voiding"""
        
        credit_note = MagicMock(spec=CreditNoteEntity)
        credit_note.status = CreditNoteStatus.ISSUED
        credit_note.internal_notes = "Original notes"
        
        credit_note_service._get_credit_note_entity = AsyncMock(return_value=credit_note)
        credit_note_service._create_void_transaction = AsyncMock()
        
        result = await credit_note_service.void_credit_note(
            "tenant_123", "cn_123", "Customer cancelled", "admin_123"
        )
        
        # Verify status change and notes update
        assert credit_note.status == CreditNoteStatus.VOIDED
        assert credit_note.voided_by == "admin_123"
        assert "Customer cancelled" in credit_note.internal_notes
        
        credit_note_service._create_void_transaction.assert_called_once_with(credit_note)
        credit_note_service.metrics.record_credit_note_voided.assert_called_once()

    @pytest.mark.asyncio
    async def test_void_already_voided_credit_note(self, credit_note_service):
        """Test voiding already voided credit note"""
        
        credit_note = MagicMock(spec=CreditNoteEntity)
        credit_note.status = CreditNoteStatus.VOIDED
        
        credit_note_service._get_credit_note_entity = AsyncMock(return_value=credit_note)
        
        with pytest.raises(InvalidCreditNoteStatusError, match="Credit note is already voided"):
            await credit_note_service.void_credit_note("tenant_123", "cn_123", "Test", "admin")

    @pytest.mark.asyncio
    async def test_void_fully_applied_credit_note(self, credit_note_service):
        """Test voiding fully applied credit note"""
        
        credit_note = MagicMock(spec=CreditNoteEntity)
        credit_note.status = CreditNoteStatus.APPLIED
        
        credit_note_service._get_credit_note_entity = AsyncMock(return_value=credit_note)
        
        with pytest.raises(InvalidCreditNoteStatusError, match="Cannot void fully applied credit note"):
            await credit_note_service.void_credit_note("tenant_123", "cn_123", "Test", "admin")

    @pytest.mark.asyncio
    async def test_apply_credit_to_invoice_success(self, credit_note_service):
        """Test successful credit application to invoice"""
        
        credit_note = MagicMock(spec=CreditNoteEntity)
        credit_note.status = CreditNoteStatus.ISSUED
        credit_note.remaining_credit_amount = 5000
        credit_note.applications = []
        
        credit_note_service._get_credit_note_entity = AsyncMock(return_value=credit_note)
        credit_note_service._create_application_transaction = AsyncMock()
        credit_note_service._update_invoice_balance = AsyncMock()
        
        result = await credit_note_service.apply_credit_to_invoice(
            "tenant_123", "cn_123", "inv_456", 3000
        )
        
        # Verify credit application
        assert credit_note.remaining_credit_amount == 2000  # 5000 - 3000
        assert credit_note.status == CreditNoteStatus.PARTIALLY_APPLIED
        
        credit_note_service._create_application_transaction.assert_called_once()
        credit_note_service._update_invoice_balance.assert_called_once_with(
            "tenant_123", "inv_456", 3000
        )

    @pytest.mark.asyncio
    async def test_apply_credit_insufficient_balance(self, credit_note_service):
        """Test applying credit with insufficient balance"""
        
        credit_note = MagicMock(spec=CreditNoteEntity)
        credit_note.status = CreditNoteStatus.ISSUED
        credit_note.remaining_credit_amount = 1000
        
        credit_note_service._get_credit_note_entity = AsyncMock(return_value=credit_note)
        
        with pytest.raises(InsufficientCreditError):
            await credit_note_service.apply_credit_to_invoice(
                "tenant_123", "cn_123", "inv_456", 2000  # More than available
            )

    @pytest.mark.asyncio
    async def test_apply_credit_invalid_status(self, credit_note_service):
        """Test applying credit with invalid status"""
        
        credit_note = MagicMock(spec=CreditNoteEntity)
        credit_note.status = CreditNoteStatus.DRAFT  # Not issued yet
        
        credit_note_service._get_credit_note_entity = AsyncMock(return_value=credit_note)
        
        with pytest.raises(InvalidCreditNoteStatusError):
            await credit_note_service.apply_credit_to_invoice(
                "tenant_123", "cn_123", "inv_456", 1000
            )

    @pytest.mark.asyncio
    async def test_apply_full_credit_amount(self, credit_note_service):
        """Test applying full credit amount changes status to fully applied"""
        
        credit_note = MagicMock(spec=CreditNoteEntity)
        credit_note.status = CreditNoteStatus.ISSUED
        credit_note.remaining_credit_amount = 3000
        credit_note.applications = []
        
        credit_note_service._get_credit_note_entity = AsyncMock(return_value=credit_note)
        credit_note_service._create_application_transaction = AsyncMock()
        credit_note_service._update_invoice_balance = AsyncMock()
        
        await credit_note_service.apply_credit_to_invoice(
            "tenant_123", "cn_123", "inv_456", 3000  # Full amount
        )
        
        # Verify status change to fully applied
        assert credit_note.remaining_credit_amount == 0
        assert credit_note.status == CreditNoteStatus.APPLIED

    @pytest.mark.asyncio
    async def test_get_available_credits_success(self, credit_note_service):
        """Test getting available credits for customer"""
        
        # Mock database query
        mock_result = MagicMock()
        mock_credit_note = MagicMock(spec=CreditNoteEntity)
        mock_result.scalars.return_value.all.return_value = [mock_credit_note]
        
        credit_note_service.db.execute = AsyncMock(return_value=mock_result)
        
        # Mock CreditNote.model_validate to return a proper model
        with pytest.mock.patch(
            "dotmac.platform.billing.credit_notes.service.CreditNote.model_validate"
        ) as mock_validate:
            mock_validate.return_value = CreditNote(
                tenant_id="tenant_123",
                credit_note_id="cn_123",
                credit_note_number="CN-2024-000001",
                invoice_id="inv_123",
                customer_id="550e8400-e29b-41d4-a716-446655440001",
                reason=CreditReason.CUSTOMER_REQUEST,
                status=CreditNoteStatus.ISSUED,
                currency="USD",
                subtotal=5000,
                tax_amount=0,
                total_amount=5000,
                remaining_credit_amount=3000,
                created_by="user_123",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                line_items=[],
            )
            
            result = await credit_note_service.get_available_credits(
                "tenant_123", "550e8400-e29b-41d4-a716-446655440001"
            )
            
            # Verify query was executed
            credit_note_service.db.execute.assert_called_once()
            
            # Verify result
            assert len(result) == 1
            assert isinstance(result[0], CreditNote)

    @pytest.mark.asyncio
    async def test_generate_credit_note_number(self, credit_note_service):
        """Test credit note number generation"""
        
        # Mock no existing credit notes
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        credit_note_service.db.execute = AsyncMock(return_value=mock_result)
        
        result = await credit_note_service._generate_credit_note_number("tenant_123")
        
        # Verify format
        current_year = datetime.utcnow().year
        expected = f"CN-{current_year}-000001"
        assert result == expected

    @pytest.mark.asyncio
    async def test_generate_credit_note_number_incremental(self, credit_note_service):
        """Test incremental credit note number generation"""
        
        # Mock existing credit note
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = "CN-2024-000005"
        credit_note_service.db.execute = AsyncMock(return_value=mock_result)
        
        result = await credit_note_service._generate_credit_note_number("tenant_123")
        
        # Verify incremented number
        assert result == "CN-2024-000006"

    @pytest.mark.asyncio
    async def test_list_credit_notes_with_filters(self, credit_note_service):
        """Test listing credit notes with various filters"""
        
        # Mock database query result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        credit_note_service.db.execute = AsyncMock(return_value=mock_result)
        
        result = await credit_note_service.list_credit_notes(
            tenant_id="tenant_123",
            customer_id="550e8400-e29b-41d4-a716-446655440002",
            invoice_id="inv_789",
            status=CreditNoteStatus.ISSUED,
            limit=50,
            offset=0,
        )
        
        # Verify query was called with filters
        credit_note_service.db.execute.assert_called_once()
        assert result == []  # Empty result from mock