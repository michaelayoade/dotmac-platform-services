# mypy: disable-error-code="no-untyped-def"
"""
Comprehensive tests for billing reconciliation and recovery service.

Tests cover:
- Reconciliation session management
- Payment reconciliation
- Retry logic with circuit breaker
- Idempotency
- Recovery operations
"""

import os
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

# Set test environment
os.environ["TESTING"] = "1"

from dotmac.platform.billing.bank_accounts.entities import (
    CompanyBankAccount,
    ManualPayment,
    PaymentMethodType,
    PaymentReconciliation,
)
from dotmac.platform.billing.reconciliation_service import ReconciliationService


@pytest.fixture
def mock_db():
    """Mock async database session."""
    session = AsyncMock(spec=AsyncSession)

    # Mock basic operations
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()

    # Mock execute() to return proper result chain
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all = MagicMock(return_value=[])
    mock_scalars.first = MagicMock(return_value=None)
    mock_result.scalars = MagicMock(return_value=mock_scalars)
    mock_result.scalar_one_or_none = MagicMock(return_value=None)
    mock_result.one = MagicMock()
    session.execute = AsyncMock(return_value=mock_result)

    # Mock refresh() to set database-generated fields
    def set_db_fields(obj):
        if not hasattr(obj, "id") or obj.id is None:
            obj.id = 123
        if not hasattr(obj, "created_at") or obj.created_at is None:
            obj.created_at = datetime.now(UTC)
        if not hasattr(obj, "updated_at") or obj.updated_at is None:
            obj.updated_at = datetime.now(UTC)
        if isinstance(obj, PaymentReconciliation):
            if not hasattr(obj, "status") or obj.status is None:
                obj.status = "in_progress"

    session.refresh = AsyncMock(side_effect=set_db_fields)

    return session


@pytest.fixture
def mock_audit_service():
    """Mock audit service."""
    audit = AsyncMock()
    audit.log_activity = AsyncMock()
    return audit


@pytest.fixture
def reconciliation_service(mock_db, mock_audit_service):
    """ReconciliationService with mocked dependencies."""
    return ReconciliationService(db=mock_db, audit_service=mock_audit_service)


@pytest.fixture
def sample_bank_account():
    """Sample bank account for testing."""
    return CompanyBankAccount(
        id=1,
        tenant_id="test-tenant-123",
        account_name="Test Account",
        bank_name="Test Bank",
        account_type="checking",
        currency="USD",
        is_primary=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_payment():
    """Sample manual payment for testing."""
    return ManualPayment(
        id=101,
        tenant_id="test-tenant-123",
        payment_reference="PAY-001",
        customer_id=uuid4(),
        bank_account_id=1,
        payment_method=PaymentMethodType.BANK_TRANSFER,
        amount=1000.00,
        currency="USD",
        payment_date=datetime.now(UTC),
        status="verified",
        reconciled=False,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


# ==================== Reconciliation Session Tests ====================


@pytest.mark.asyncio
async def test_start_reconciliation_session(reconciliation_service, mock_db):
    """Test starting a new reconciliation session."""
    period_start = datetime.now(UTC) - timedelta(days=30)
    period_end = datetime.now(UTC)

    result = await reconciliation_service.start_reconciliation_session(
        tenant_id="test-tenant-123",
        bank_account_id=1,
        period_start=period_start,
        period_end=period_end,
        opening_balance=Decimal("5000.00"),
        statement_balance=Decimal("6000.00"),
        user_id="user-123",
        statement_file_url="https://example.com/statement.pdf",
    )

    # Verify session was created
    assert mock_db.add.called
    assert mock_db.commit.called
    assert result.id == 123
    assert result.status == "in_progress"
    assert result.opening_balance == Decimal("5000.00")
    assert result.statement_balance == Decimal("6000.00")


@pytest.mark.asyncio
async def test_start_reconciliation_invalid_period(reconciliation_service):
    """Test validation for invalid period dates."""
    period_end = datetime.now(UTC) - timedelta(days=30)
    period_start = datetime.now(UTC)  # Start after end

    with pytest.raises(ValueError, match="period_start must be before period_end"):
        await reconciliation_service.start_reconciliation_session(
            tenant_id="test-tenant-123",
            bank_account_id=1,
            period_start=period_start,
            period_end=period_end,
            opening_balance=Decimal("5000.00"),
            statement_balance=Decimal("6000.00"),
            user_id="user-123",
        )


@pytest.mark.asyncio
async def test_add_reconciled_payment(reconciliation_service, mock_db, sample_payment):
    """Test adding a payment to reconciliation session."""
    # Mock getting reconciliation
    mock_reconciliation = PaymentReconciliation(
        id=123,
        tenant_id="test-tenant-123",
        bank_account_id=1,
        reconciliation_date=datetime.now(UTC),
        period_start=datetime.now(UTC) - timedelta(days=30),
        period_end=datetime.now(UTC),
        opening_balance=5000.00,
        closing_balance=5000.00,
        statement_balance=6000.00,
        total_deposits=0.0,
        total_withdrawals=0.0,
        unreconciled_count=0,
        discrepancy_amount=0.0,
        status="in_progress",
        reconciled_items=[],
        meta_data={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    mock_db.execute.return_value.scalar_one_or_none.side_effect = [
        mock_reconciliation,
        sample_payment,
    ]

    result = await reconciliation_service.add_reconciled_payment(
        tenant_id="test-tenant-123",
        reconciliation_id=123,
        payment_id=101,
        user_id="user-123",
        notes="Matched bank statement",
    )

    assert mock_db.commit.called
    assert sample_payment.reconciled is True


@pytest.mark.asyncio
async def test_add_payment_to_completed_reconciliation(reconciliation_service, mock_db):
    """Test that payments cannot be added to completed reconciliation."""
    mock_reconciliation = PaymentReconciliation(
        id=123,
        tenant_id="test-tenant-123",
        bank_account_id=1,
        reconciliation_date=datetime.now(UTC),
        period_start=datetime.now(UTC) - timedelta(days=30),
        period_end=datetime.now(UTC),
        opening_balance=5000.00,
        closing_balance=6000.00,
        statement_balance=6000.00,
        total_deposits=1000.00,
        total_withdrawals=0.0,
        unreconciled_count=0,
        discrepancy_amount=0.0,
        status="completed",  # Already completed
        reconciled_items=[],
        meta_data={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    mock_db.execute.return_value.scalar_one_or_none.return_value = mock_reconciliation

    with pytest.raises(ValueError, match="can only add payments to in_progress sessions"):
        await reconciliation_service.add_reconciled_payment(
            tenant_id="test-tenant-123",
            reconciliation_id=123,
            payment_id=101,
            user_id="user-123",
        )


@pytest.mark.asyncio
async def test_complete_reconciliation(reconciliation_service, mock_db):
    """Test completing a reconciliation session."""
    mock_reconciliation = PaymentReconciliation(
        id=123,
        tenant_id="test-tenant-123",
        bank_account_id=1,
        reconciliation_date=datetime.now(UTC),
        period_start=datetime.now(UTC) - timedelta(days=30),
        period_end=datetime.now(UTC),
        opening_balance=5000.00,
        closing_balance=5000.00,
        statement_balance=6000.00,
        total_deposits=1000.00,
        total_withdrawals=0.0,
        unreconciled_count=0,
        discrepancy_amount=0.0,
        status="in_progress",
        reconciled_items=[],
        meta_data={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    mock_db.execute.return_value.scalar_one_or_none.return_value = mock_reconciliation

    result = await reconciliation_service.complete_reconciliation(
        tenant_id="test-tenant-123",
        reconciliation_id=123,
        user_id="user-123",
        notes="All items reconciled",
    )

    assert result.status == "completed"
    assert result.completed_by == "user-123"
    assert result.completed_at is not None
    assert mock_db.commit.called


@pytest.mark.asyncio
async def test_approve_reconciliation(reconciliation_service, mock_db, mock_audit_service):
    """Test approving a completed reconciliation."""
    mock_reconciliation = PaymentReconciliation(
        id=123,
        tenant_id="test-tenant-123",
        bank_account_id=1,
        reconciliation_date=datetime.now(UTC),
        period_start=datetime.now(UTC) - timedelta(days=30),
        period_end=datetime.now(UTC),
        opening_balance=5000.00,
        closing_balance=6000.00,
        statement_balance=6000.00,
        total_deposits=1000.00,
        total_withdrawals=0.0,
        unreconciled_count=0,
        discrepancy_amount=0.0,
        status="completed",  # Must be completed to approve
        completed_by="user-123",
        completed_at=datetime.now(UTC),
        reconciled_items=[],
        meta_data={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    mock_db.execute.return_value.scalar_one_or_none.return_value = mock_reconciliation

    result = await reconciliation_service.approve_reconciliation(
        tenant_id="test-tenant-123",
        reconciliation_id=123,
        user_id="finance-admin",
        notes="Approved by finance team",
    )

    assert result.status == "approved"
    assert result.approved_by == "finance-admin"
    assert result.approved_at is not None
    assert mock_db.commit.called
    assert mock_audit_service.log_activity.called


@pytest.mark.asyncio
async def test_approve_unapproved_reconciliation_fails(reconciliation_service, mock_db):
    """Test that only completed reconciliations can be approved."""
    mock_reconciliation = PaymentReconciliation(
        id=123,
        tenant_id="test-tenant-123",
        bank_account_id=1,
        reconciliation_date=datetime.now(UTC),
        period_start=datetime.now(UTC) - timedelta(days=30),
        period_end=datetime.now(UTC),
        opening_balance=5000.00,
        closing_balance=5000.00,
        statement_balance=6000.00,
        total_deposits=0.0,
        total_withdrawals=0.0,
        unreconciled_count=5,
        discrepancy_amount=1000.0,
        status="in_progress",  # Not completed yet
        reconciled_items=[],
        meta_data={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    mock_db.execute.return_value.scalar_one_or_none.return_value = mock_reconciliation

    with pytest.raises(ValueError, match="can only approve completed sessions"):
        await reconciliation_service.approve_reconciliation(
            tenant_id="test-tenant-123",
            reconciliation_id=123,
            user_id="finance-admin",
        )


# ==================== Recovery & Retry Tests ====================


@pytest.mark.asyncio
async def test_retry_failed_payment_success(reconciliation_service, mock_db, sample_payment):
    """Test successful payment retry with recovery."""
    sample_payment.status = "failed"
    mock_db.execute.return_value.scalar_one_or_none.return_value = sample_payment

    # Mock successful retry
    with patch.object(
        reconciliation_service.retry_manager, "execute", new_callable=AsyncMock
    ) as mock_retry:
        mock_retry.return_value = sample_payment

        result = await reconciliation_service.retry_failed_payment_with_recovery(
            tenant_id="test-tenant-123",
            payment_id=101,
            user_id="system",
            max_attempts=3,
        )

    assert result["success"] is True
    assert result["attempts"] <= 3
    assert result["circuit_breaker_state"] in ["closed", "open", "half_open"]


@pytest.mark.asyncio
async def test_retry_verified_payment_fails(reconciliation_service, mock_db, sample_payment):
    """Test that verified payments cannot be retried."""
    sample_payment.status = "verified"  # Already verified
    mock_db.execute.return_value.scalar_one_or_none.return_value = sample_payment

    with pytest.raises(ValueError, match="can only retry failed payments"):
        await reconciliation_service.retry_failed_payment_with_recovery(
            tenant_id="test-tenant-123",
            payment_id=101,
            user_id="system",
        )


@pytest.mark.asyncio
async def test_circuit_breaker_prevents_retry(reconciliation_service, mock_db, sample_payment):
    """Test that circuit breaker prevents retries when open."""
    sample_payment.status = "failed"
    mock_db.execute.return_value.scalar_one_or_none.return_value = sample_payment

    # Force circuit breaker to open state
    reconciliation_service.circuit_breaker.state = "open"

    result = await reconciliation_service.retry_failed_payment_with_recovery(
        tenant_id="test-tenant-123",
        payment_id=101,
        user_id="system",
    )

    assert result["success"] is False
    assert result["circuit_breaker_state"] == "open"


@pytest.mark.asyncio
async def test_idempotent_operation(reconciliation_service):
    """Test idempotent operation execution."""

    async def sample_operation():
        return {"status": "success", "value": 42}

    result = await reconciliation_service.execute_with_idempotency(
        operation_key="test-operation-123",
        operation=sample_operation,
    )

    assert result["status"] == "success"
    assert result["value"] == 42


# ==================== List and Summary Tests ====================


@pytest.mark.asyncio
async def test_list_reconciliations(reconciliation_service, mock_db):
    """Test listing reconciliation sessions with pagination."""
    mock_reconciliations = [
        PaymentReconciliation(
            id=i,
            tenant_id="test-tenant-123",
            bank_account_id=1,
            reconciliation_date=datetime.now(UTC) - timedelta(days=i),
            period_start=datetime.now(UTC) - timedelta(days=30 + i),
            period_end=datetime.now(UTC) - timedelta(days=i),
            opening_balance=5000.00,
            closing_balance=6000.00,
            statement_balance=6000.00,
            total_deposits=1000.00,
            total_withdrawals=0.0,
            unreconciled_count=0,
            discrepancy_amount=0.0,
            status="approved" if i % 2 == 0 else "completed",
            reconciled_items=[],
            meta_data={},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        for i in range(1, 6)
    ]

    mock_db.execute.return_value.scalars.return_value.all.return_value = mock_reconciliations
    mock_db.execute.return_value.scalar_one.return_value = 5

    result = await reconciliation_service.list_reconciliations(
        tenant_id="test-tenant-123",
        bank_account_id=1,
        page=1,
        page_size=10,
    )

    assert result["total"] == 5
    assert result["page"] == 1
    assert result["page_size"] == 10
    assert len(result["reconciliations"]) == 5


@pytest.mark.asyncio
async def test_get_reconciliation_summary(reconciliation_service, mock_db):
    """Test getting reconciliation summary statistics."""
    # Mock count and sum aggregations
    mock_result = MagicMock()
    mock_result.total_sessions = 10
    mock_result.approved_sessions = 8
    mock_result.pending_sessions = 2
    mock_result.total_discrepancies = Decimal("500.00")
    mock_result.total_items = 150

    mock_db.execute.return_value.one.return_value = mock_result

    summary = await reconciliation_service.get_reconciliation_summary(
        tenant_id="test-tenant-123",
        bank_account_id=1,
        days=30,
    )

    assert summary["period_days"] == 30
    assert summary["total_sessions"] == 10
    assert summary["approved_sessions"] == 8
    assert summary["pending_sessions"] == 2
    assert summary["total_discrepancies"] == Decimal("500.00")


# ==================== Edge Cases and Error Handling ====================


@pytest.mark.asyncio
async def test_reconciliation_not_found(reconciliation_service, mock_db):
    """Test handling of non-existent reconciliation."""
    mock_db.execute.return_value.scalar_one_or_none.return_value = None

    with pytest.raises(ValueError, match="Reconciliation .* not found"):
        await reconciliation_service._get_reconciliation(
            tenant_id="test-tenant-123",
            reconciliation_id=999,
        )


@pytest.mark.asyncio
async def test_payment_not_found(reconciliation_service, mock_db):
    """Test handling of non-existent payment."""
    mock_reconciliation = PaymentReconciliation(
        id=123,
        tenant_id="test-tenant-123",
        bank_account_id=1,
        reconciliation_date=datetime.now(UTC),
        period_start=datetime.now(UTC) - timedelta(days=30),
        period_end=datetime.now(UTC),
        opening_balance=5000.00,
        closing_balance=5000.00,
        statement_balance=6000.00,
        total_deposits=0.0,
        total_withdrawals=0.0,
        unreconciled_count=0,
        discrepancy_amount=0.0,
        status="in_progress",
        reconciled_items=[],
        meta_data={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    mock_db.execute.return_value.scalar_one_or_none.side_effect = [
        mock_reconciliation,
        None,  # Payment not found
    ]

    with pytest.raises(ValueError, match="Payment .* not found"):
        await reconciliation_service.add_reconciled_payment(
            tenant_id="test-tenant-123",
            reconciliation_id=123,
            payment_id=999,
            user_id="user-123",
        )


@pytest.mark.asyncio
async def test_discrepancy_calculation(reconciliation_service, mock_db):
    """Test that discrepancy is calculated correctly."""
    mock_reconciliation = PaymentReconciliation(
        id=123,
        tenant_id="test-tenant-123",
        bank_account_id=1,
        reconciliation_date=datetime.now(UTC),
        period_start=datetime.now(UTC) - timedelta(days=30),
        period_end=datetime.now(UTC),
        opening_balance=5000.00,
        closing_balance=5800.00,  # Opening + deposits - withdrawals
        statement_balance=6000.00,  # Different from closing
        total_deposits=1000.00,
        total_withdrawals=200.00,
        unreconciled_count=0,
        discrepancy_amount=0.0,
        status="in_progress",
        reconciled_items=[],
        meta_data={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    mock_db.execute.return_value.scalar_one_or_none.return_value = mock_reconciliation

    result = await reconciliation_service.complete_reconciliation(
        tenant_id="test-tenant-123",
        reconciliation_id=123,
        user_id="user-123",
    )

    # Discrepancy = statement_balance - closing_balance = 6000 - 5800 = 200
    assert result.discrepancy_amount == 200.00
    assert result.status == "completed"


@pytest.mark.asyncio
async def test_tenant_isolation(reconciliation_service, mock_db):
    """Test that tenant isolation is enforced."""
    mock_reconciliation = PaymentReconciliation(
        id=123,
        tenant_id="other-tenant-999",  # Different tenant
        bank_account_id=1,
        reconciliation_date=datetime.now(UTC),
        period_start=datetime.now(UTC) - timedelta(days=30),
        period_end=datetime.now(UTC),
        opening_balance=5000.00,
        closing_balance=5000.00,
        statement_balance=6000.00,
        total_deposits=0.0,
        total_withdrawals=0.0,
        unreconciled_count=0,
        discrepancy_amount=0.0,
        status="in_progress",
        reconciled_items=[],
        meta_data={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    mock_db.execute.return_value.scalar_one_or_none.return_value = mock_reconciliation

    # Should not find reconciliation for different tenant
    with pytest.raises(ValueError, match="not found"):
        await reconciliation_service._get_reconciliation(
            tenant_id="test-tenant-123",  # Different from mock
            reconciliation_id=123,
        )
