"""
Integration tests for complete banking and payment workflows
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
from decimal import Decimal

from dotmac.platform.billing.bank_accounts.service import (
    BankAccountService,
    ManualPaymentService,
)
from dotmac.platform.billing.bank_accounts.models import (
    CompanyBankAccountCreate,
    CashPaymentCreate,
    CheckPaymentCreate,
    BankTransferCreate,
    PaymentSearchFilters,
    AccountType,
    PaymentMethodType,
    BankAccountStatus,
)


class TestCompletePaymentWorkflow:
    """Test complete payment recording and reconciliation workflow"""

    @pytest.mark.asyncio
    async def test_full_payment_lifecycle(self):
        """Test recording, verifying, and reconciling a payment"""

        # Setup mock database
        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Create services
        account_service = BankAccountService(mock_db)
        payment_service = ManualPaymentService(mock_db)

        tenant_id = "test-tenant"
        user_id = "test-user"

        # Step 1: Create a bank account
        account_data = CompanyBankAccountCreate(
            account_name="Test Company",
            bank_name="Test Bank",
            bank_country="US",
            account_number="1234567890",
            account_type=AccountType.BUSINESS,
            currency="USD",
            is_primary=True,
            accepts_deposits=True
        )

        # Mock the account creation
        mock_account_result = MagicMock()
        mock_account_result.scalar_one_or_none.return_value = None
        mock_account_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_account_result)

        account = await account_service.create_bank_account(
            tenant_id, account_data, user_id
        )

        # Verify account was created
        mock_db.add.assert_called()
        mock_db.commit.assert_called()

        # Step 2: Record a cash payment
        payment_data = CashPaymentCreate(
            customer_id="CUST-001",
            invoice_id="INV-001",
            bank_account_id=1,  # Deposit to the created account
            amount=500.00,
            currency="USD",
            payment_date=datetime.utcnow(),
            cash_register_id="REG-001",
            cashier_name="Jane Smith",
            notes="Cash payment for invoice INV-001"
        )

        payment = await payment_service.record_cash_payment(
            tenant_id, payment_data, user_id
        )

        # Verify payment was recorded
        assert mock_db.add.call_count >= 2  # Account + Payment

        # Step 3: Verify the payment
        mock_payment = MagicMock()
        mock_payment.id = 1
        mock_payment.status = "pending"
        mock_payment.notes = None

        mock_verify_result = MagicMock()
        mock_verify_result.scalar_one_or_none.return_value = mock_payment
        mock_db.execute = AsyncMock(return_value=mock_verify_result)

        verified_payment = await payment_service.verify_payment(
            tenant_id, 1, user_id, "Verified against receipt"
        )

        # Check payment status was updated
        assert mock_payment.status == "verified"
        assert mock_payment.approved_by == user_id

        # Step 4: Reconcile the payment
        mock_payments = [mock_payment]
        mock_reconcile_result = MagicMock()
        mock_reconcile_result.scalars.return_value.all.return_value = mock_payments
        mock_db.execute = AsyncMock(return_value=mock_reconcile_result)

        reconciled_payments = await payment_service.reconcile_payments(
            tenant_id, [1], user_id, "Monthly reconciliation"
        )

        # Check payment was reconciled
        assert mock_payment.reconciled is True
        assert mock_payment.status == "reconciled"

    @pytest.mark.asyncio
    async def test_multiple_payment_methods_workflow(self):
        """Test recording different payment methods for the same customer"""

        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_db.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))))

        payment_service = ManualPaymentService(mock_db)

        tenant_id = "test-tenant"
        user_id = "test-user"
        customer_id = "CUST-001"

        # Record multiple payments with different methods
        payments = []

        # Cash payment
        cash_payment = await payment_service.record_cash_payment(
            tenant_id,
            CashPaymentCreate(
                customer_id=customer_id,
                amount=100.00,
                currency="USD",
                payment_date=datetime.utcnow(),
                cash_register_id="REG-001"
            ),
            user_id
        )
        payments.append(cash_payment)

        # Check payment
        check_payment = await payment_service.record_check_payment(
            tenant_id,
            CheckPaymentCreate(
                customer_id=customer_id,
                amount=250.00,
                currency="USD",
                payment_date=datetime.utcnow(),
                check_number="12345",
                check_bank_name="Customer Bank"
            ),
            user_id
        )
        payments.append(check_payment)

        # Bank transfer
        transfer_payment = await payment_service.record_bank_transfer(
            tenant_id,
            BankTransferCreate(
                customer_id=customer_id,
                amount=500.00,
                currency="USD",
                payment_date=datetime.utcnow(),
                payment_method=PaymentMethodType.BANK_TRANSFER,
                sender_name="Customer Company",
                sender_bank="Their Bank"
            ),
            user_id
        )
        payments.append(transfer_payment)

        # Verify all payments were recorded
        assert mock_db.add.call_count == 3
        assert mock_db.commit.call_count == 3


class TestBankAccountManagement:
    """Test bank account management scenarios"""

    @pytest.mark.asyncio
    async def test_primary_account_switching(self):
        """Test switching primary account designation"""

        mock_db = MagicMock()

        # Create mock accounts
        account1 = MagicMock(id=1, is_primary=True)
        account2 = MagicMock(id=2, is_primary=False)

        # Mock database queries
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [account1]
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        service = BankAccountService(mock_db)

        # Switch primary to account2
        await service._unset_primary_accounts("test-tenant", exclude_id=2)

        # Verify account1 is no longer primary
        assert account1.is_primary is False

    @pytest.mark.asyncio
    async def test_account_verification_workflow(self):
        """Test bank account verification process"""

        mock_db = MagicMock()

        # Create mock unverified account
        mock_account = MagicMock()
        mock_account.id = 1
        mock_account.status = BankAccountStatus.PENDING
        mock_account.verified_at = None
        mock_account.verified_by = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_account
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        service = BankAccountService(mock_db)

        # Verify the account
        result = await service.verify_bank_account(
            "test-tenant",
            1,
            "verifier-user",
            "Verified via test deposits"
        )

        # Check verification was applied
        assert mock_account.status == BankAccountStatus.VERIFIED
        assert mock_account.verified_by == "verifier-user"
        assert mock_account.verified_at is not None
        assert mock_account.verification_notes == "Verified via test deposits"

    @pytest.mark.asyncio
    async def test_account_summary_calculations(self):
        """Test bank account summary statistics calculation"""

        mock_db = MagicMock()

        # Mock account query
        mock_account = MagicMock()
        mock_account.id = 1
        mock_account.tenant_id = "test-tenant"

        mock_account_result = MagicMock()
        mock_account_result.scalar_one_or_none.return_value = mock_account

        # Mock MTD deposits sum
        mock_mtd_result = MagicMock()
        mock_mtd_result.scalar.return_value = Decimal("15000.00")

        # Mock YTD deposits sum
        mock_ytd_result = MagicMock()
        mock_ytd_result.scalar.return_value = Decimal("125000.00")

        # Mock pending payments count
        mock_pending_result = MagicMock()
        mock_pending_result.scalar.return_value = 8

        # Mock last reconciliation
        mock_recon_result = MagicMock()
        mock_recon_result.scalar.return_value = datetime.utcnow() - timedelta(days=5)

        # Setup mock execute to return different results based on query
        call_count = 0
        async def mock_execute(query):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_account_result
            elif call_count == 2:
                return mock_mtd_result
            elif call_count == 3:
                return mock_ytd_result
            elif call_count == 4:
                return mock_pending_result
            else:
                return mock_recon_result

        mock_db.execute = mock_execute

        service = BankAccountService(mock_db)

        # Get account summary
        summary = await service.get_bank_account_summary("test-tenant", 1)

        # Verify calculations
        assert summary.total_deposits_mtd == 15000.00
        assert summary.total_deposits_ytd == 125000.00
        assert summary.pending_payments == 8
        assert summary.last_reconciliation is not None


class TestPaymentSearchAndFiltering:
    """Test payment search and filtering capabilities"""

    @pytest.mark.asyncio
    async def test_complex_payment_search(self):
        """Test searching payments with multiple filters"""

        mock_db = MagicMock()

        # Create mock payments with various attributes
        mock_payments = [
            MagicMock(
                id=1,
                customer_id="CUST-001",
                payment_method=PaymentMethodType.CASH,
                amount=100.00,
                payment_date=datetime.utcnow(),
                status="pending",
                reconciled=False
            ),
            MagicMock(
                id=2,
                customer_id="CUST-001",
                payment_method=PaymentMethodType.CHECK,
                amount=500.00,
                payment_date=datetime.utcnow() - timedelta(days=5),
                status="verified",
                reconciled=False
            ),
            MagicMock(
                id=3,
                customer_id="CUST-002",
                payment_method=PaymentMethodType.BANK_TRANSFER,
                amount=1500.00,
                payment_date=datetime.utcnow() - timedelta(days=10),
                status="reconciled",
                reconciled=True
            )
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_payments[:2]
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = ManualPaymentService(mock_db)

        # Search with multiple filters
        filters = PaymentSearchFilters(
            customer_id="CUST-001",
            reconciled=False,
            date_from=datetime.utcnow() - timedelta(days=30),
            amount_min=50.00,
            amount_max=1000.00
        )

        results = await service.search_payments(
            "test-tenant",
            filters,
            limit=10,
            offset=0
        )

        # Verify search was performed
        mock_db.execute.assert_called_once()


class TestSecurityAndAuthorization:
    """Test security aspects of banking features"""

    @pytest.mark.asyncio
    async def test_tenant_isolation_for_accounts(self):
        """Test that accounts are properly isolated by tenant"""

        mock_db = MagicMock()

        # Setup different tenants' accounts
        tenant1_accounts = [
            MagicMock(id=1, tenant_id="tenant1"),
            MagicMock(id=2, tenant_id="tenant1")
        ]

        tenant2_accounts = [
            MagicMock(id=3, tenant_id="tenant2"),
            MagicMock(id=4, tenant_id="tenant2")
        ]

        async def mock_execute(query):
            # Check if query filters by tenant_id
            query_str = str(query)
            if "tenant1" in query_str:
                result = MagicMock()
                result.scalars.return_value.all.return_value = tenant1_accounts
                return result
            elif "tenant2" in query_str:
                result = MagicMock()
                result.scalars.return_value.all.return_value = tenant2_accounts
                return result
            else:
                result = MagicMock()
                result.scalars.return_value.all.return_value = []
                return result

        mock_db.execute = mock_execute

        service = BankAccountService(mock_db)

        # Get accounts for tenant1
        tenant1_result = await service.get_bank_accounts("tenant1")
        assert len(tenant1_result) == 2

        # Get accounts for tenant2
        tenant2_result = await service.get_bank_accounts("tenant2")
        assert len(tenant2_result) == 2

        # Accounts should be different
        assert tenant1_result != tenant2_result

    @pytest.mark.asyncio
    async def test_audit_trail_for_payments(self):
        """Test that all payment actions are properly audited"""

        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        service = ManualPaymentService(mock_db)

        # Record a payment
        payment_data = CashPaymentCreate(
            customer_id="CUST-001",
            amount=100.00,
            currency="USD",
            payment_date=datetime.utcnow()
        )

        user_id = "audit-user-123"
        tenant_id = "test-tenant"

        await service.record_cash_payment(tenant_id, payment_data, user_id)

        # Verify audit fields were set
        added_payment = mock_db.add.call_args[0][0]
        assert added_payment.recorded_by == user_id
        assert added_payment.created_by == user_id
        assert added_payment.updated_by == user_id

    @pytest.mark.asyncio
    async def test_sensitive_data_handling(self):
        """Test that sensitive bank account data is properly handled"""

        from dotmac.platform.billing.bank_accounts.service import BankAccountService

        service = BankAccountService(MagicMock())

        # Test account number encryption
        account_number = "1234567890"
        encrypted = service._encrypt_account_number(account_number)

        # Encrypted value should not contain the plain account number
        assert account_number not in encrypted

        # Encrypted value should be different each time (due to salt)
        encrypted2 = service._encrypt_account_number(account_number)
        assert encrypted != encrypted2


class TestEdgeCases:
    """Test edge cases and error conditions"""

    @pytest.mark.asyncio
    async def test_duplicate_check_number_handling(self):
        """Test handling of duplicate check numbers"""

        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        service = ManualPaymentService(mock_db)

        # Record check with number 12345
        check1 = CheckPaymentCreate(
            customer_id="CUST-001",
            amount=100.00,
            currency="USD",
            payment_date=datetime.utcnow(),
            check_number="12345",
            check_bank_name="Bank A"
        )

        await service.record_check_payment("test-tenant", check1, "user1")

        # Try to record another check with same number but different customer
        check2 = CheckPaymentCreate(
            customer_id="CUST-002",
            amount=200.00,
            currency="USD",
            payment_date=datetime.utcnow(),
            check_number="12345",
            check_bank_name="Bank B"
        )

        # Should handle gracefully (different reference number)
        await service.record_check_payment("test-tenant", check2, "user1")

        # Both should be recorded
        assert mock_db.add.call_count == 2

    @pytest.mark.asyncio
    async def test_large_payment_amount_handling(self):
        """Test handling of very large payment amounts"""

        # Test with large but valid amount
        payment = CashPaymentCreate(
            customer_id="CUST-001",
            amount=9999999.99,  # Maximum reasonable amount
            currency="USD",
            payment_date=datetime.utcnow()
        )

        assert payment.amount == 9999999.99

    @pytest.mark.asyncio
    async def test_international_currency_handling(self):
        """Test handling of various international currencies"""

        currencies = ["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "CNY"]

        for currency in currencies:
            payment = CashPaymentCreate(
                customer_id="CUST-001",
                amount=100.00,
                currency=currency,
                payment_date=datetime.utcnow()
            )

            assert payment.currency == currency

    @pytest.mark.asyncio
    async def test_payment_date_validation(self):
        """Test validation of payment dates"""

        # Test future date (should be allowed for post-dated checks)
        future_payment = CheckPaymentCreate(
            customer_id="CUST-001",
            amount=100.00,
            currency="USD",
            payment_date=datetime.utcnow() + timedelta(days=30),
            check_number="99999",
            check_bank_name="Future Bank"
        )

        assert future_payment.payment_date > datetime.utcnow()

        # Test past date (should be allowed for historical records)
        past_payment = CashPaymentCreate(
            customer_id="CUST-001",
            amount=100.00,
            currency="USD",
            payment_date=datetime.utcnow() - timedelta(days=365)
        )

        assert past_payment.payment_date < datetime.utcnow()