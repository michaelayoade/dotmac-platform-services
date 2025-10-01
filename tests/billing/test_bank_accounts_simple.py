"""Simple tests for bank account features."""

import pytest
from unittest.mock import AsyncMock, Mock, MagicMock
from datetime import datetime, timezone

from dotmac.platform.billing.bank_accounts.models import (
    CashRegisterCreate,
    CashRegisterResponse,
    CashRegisterReconciliationCreate,
)
from dotmac.platform.billing.bank_accounts.cash_register_service import CashRegisterService
from dotmac.platform.billing.exceptions import BillingError


class TestCashRegisterService:
    """Test cash register service."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        db.rollback = AsyncMock()
        db.refresh = AsyncMock()
        db.add = Mock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create cash register service."""
        return CashRegisterService(mock_db)

    @pytest.mark.asyncio
    async def test_create_cash_register_success(self, service, mock_db):
        """Test successful cash register creation."""
        # Setup
        mock_db.execute.return_value.scalar_one_or_none.return_value = None  # No existing register

        register_data = CashRegisterCreate(
            register_id="REG001",
            register_name="Main Register",
            location="Store Front",
            initial_float=100.00,
            requires_daily_reconciliation=True,
            max_cash_limit=5000.00
        )

        # Execute
        result = await service.create_cash_register(
            tenant_id="tenant-123",
            data=register_data,
            created_by="user-456"
        )

        # Verify
        assert isinstance(result, CashRegisterResponse)
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_cash_register_duplicate(self, service, mock_db):
        """Test duplicate cash register creation fails."""
        # Setup - existing register found
        existing_register = Mock()
        mock_db.execute.return_value.scalar_one_or_none.return_value = existing_register

        register_data = CashRegisterCreate(
            register_id="REG001",
            register_name="Main Register",
            location="Store Front",
            initial_float=100.00,
            requires_daily_reconciliation=True
        )

        # Execute and verify
        with pytest.raises(BillingError) as exc_info:
            await service.create_cash_register(
                tenant_id="tenant-123",
                data=register_data,
                created_by="user-456"
            )

        assert "already exists" in str(exc_info.value)
        assert exc_info.value.error_code == "DUPLICATE_REGISTER"

    @pytest.mark.asyncio
    async def test_reconcile_register_success(self, service, mock_db):
        """Test successful cash register reconciliation."""
        # Setup - mock existing register
        mock_register = Mock()
        mock_register.current_float = 500.00
        mock_register.initial_float = 100.00
        mock_register.last_reconciled = None
        mock_register.metadata = {}

        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_register

        reconciliation_data = CashRegisterReconciliationCreate(
            actual_cash=520.00,
            notes="End of day reconciliation"
        )

        # Execute
        result = await service.reconcile_register(
            tenant_id="tenant-123",
            register_id="REG001",
            data=reconciliation_data,
            reconciled_by="user-456"
        )

        # Verify
        assert result.id is not None
        assert result.discrepancy == 20.00  # 520 actual - 500 expected
        assert result.reconciled_by == "user-456"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_float_exceeds_limit(self, service, mock_db):
        """Test float update that exceeds limit fails."""
        # Setup - mock existing register with limit
        mock_register = Mock()
        mock_register.max_cash_limit = 1000.00
        mock_register.current_float = 500.00
        mock_register.metadata = {}

        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_register

        # Execute and verify
        with pytest.raises(BillingError) as exc_info:
            await service.update_float(
                tenant_id="tenant-123",
                register_id="REG001",
                new_float=1500.00,  # Exceeds limit
                reason="Adding more cash",
                updated_by="user-456"
            )

        assert "exceeds maximum limit" in str(exc_info.value)
        assert exc_info.value.error_code == "FLOAT_EXCEEDS_LIMIT"
