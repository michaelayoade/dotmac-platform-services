"""
Comprehensive tests for manual payment recording and reconciliation
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from dotmac.platform.main import app
from dotmac.platform.billing.bank_accounts.models import (
    CashPaymentCreate,
    CheckPaymentCreate,
    BankTransferCreate,
    MobileMoneyCreate,
    ManualPaymentResponse,
    PaymentSearchFilters,
    PaymentMethodType,
)
from dotmac.platform.billing.bank_accounts.service import ManualPaymentService

client = TestClient(app)


@pytest.fixture
def auth_headers():
    """Mock authentication headers"""
    return {"Authorization": "Bearer test-token"}


@pytest.fixture
def mock_current_user():
    """Mock current user dependency"""
    return {
        "user_id": "test-user-123",
        "tenant_id": "test-tenant",
        "email": "test@example.com"
    }


class TestCashPaymentRecording:
    """Test cash payment recording"""

    @pytest.mark.asyncio
    async def test_record_cash_payment(self, auth_headers, mock_current_user):
        """Test recording a cash payment"""
        with patch('dotmac.platform.auth.dependencies.get_current_user', return_value=mock_current_user):
            with patch('dotmac.platform.billing.bank_accounts.service.ManualPaymentService.record_cash_payment') as mock_record:
                cash_payment = CashPaymentCreate(
                    customer_id="CUST-001",
                    invoice_id="INV-001",
                    amount=150.00,
                    currency="USD",
                    payment_date=datetime.utcnow(),
                    cash_register_id="REG-001",
                    cashier_name="John Doe",
                    notes="Cash payment received at store"
                )

                mock_response = ManualPaymentResponse(
                    id=1,
                    tenant_id="test-tenant",
                    payment_reference="CASH-20240101120000-ABC123",
                    customer_id=cash_payment.customer_id,
                    invoice_id=cash_payment.invoice_id,
                    payment_method=PaymentMethodType.CASH,
                    amount=cash_payment.amount,
                    currency=cash_payment.currency,
                    payment_date=cash_payment.payment_date,
                    received_date=cash_payment.payment_date,
                    cash_register_id=cash_payment.cash_register_id,
                    cashier_name=cash_payment.cashier_name,
                    status="pending",
                    reconciled=False,
                    notes=cash_payment.notes,
                    recorded_by="test-user-123",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                mock_record.return_value = mock_response

                response = client.post(
                    "/api/v1/billing/payments/cash",
                    json=cash_payment.dict(),
                    headers=auth_headers
                )

                assert response.status_code == 200
                data = response.json()
                assert data["payment_method"] == "cash"
                assert data["amount"] == 150.00
                assert data["cash_register_id"] == "REG-001"
                assert data["cashier_name"] == "John Doe"

    @pytest.mark.asyncio
    async def test_cash_payment_without_register(self, auth_headers, mock_current_user):
        """Test recording cash payment without register ID"""
        with patch('dotmac.platform.auth.dependencies.get_current_user', return_value=mock_current_user):
            with patch('dotmac.platform.billing.bank_accounts.service.ManualPaymentService.record_cash_payment') as mock_record:
                cash_payment = CashPaymentCreate(
                    customer_id="CUST-002",
                    amount=75.50,
                    currency="USD",
                    payment_date=datetime.utcnow(),
                    notes="Manual cash collection"
                )

                mock_response = ManualPaymentResponse(
                    id=2,
                    tenant_id="test-tenant",
                    payment_reference="CASH-20240101120100-XYZ789",
                    customer_id=cash_payment.customer_id,
                    payment_method=PaymentMethodType.CASH,
                    amount=cash_payment.amount,
                    currency=cash_payment.currency,
                    payment_date=cash_payment.payment_date,
                    received_date=cash_payment.payment_date,
                    status="pending",
                    reconciled=False,
                    notes=cash_payment.notes,
                    recorded_by="test-user-123",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                mock_record.return_value = mock_response

                response = client.post(
                    "/api/v1/billing/payments/cash",
                    json=cash_payment.dict(),
                    headers=auth_headers
                )

                assert response.status_code == 200
                data = response.json()
                assert data["cash_register_id"] is None


class TestCheckPaymentRecording:
    """Test check payment recording"""

    @pytest.mark.asyncio
    async def test_record_check_payment(self, auth_headers, mock_current_user):
        """Test recording a check payment"""
        with patch('dotmac.platform.auth.dependencies.get_current_user', return_value=mock_current_user):
            with patch('dotmac.platform.billing.bank_accounts.service.ManualPaymentService.record_check_payment') as mock_record:
                check_payment = CheckPaymentCreate(
                    customer_id="CUST-003",
                    invoice_id="INV-003",
                    amount=500.00,
                    currency="USD",
                    payment_date=datetime.utcnow(),
                    check_number="12345",
                    check_bank_name="Wells Fargo",
                    notes="Check received via mail"
                )

                mock_response = ManualPaymentResponse(
                    id=3,
                    tenant_id="test-tenant",
                    payment_reference="CHK-20240101120200-DEF456",
                    external_reference="12345",
                    customer_id=check_payment.customer_id,
                    invoice_id=check_payment.invoice_id,
                    payment_method=PaymentMethodType.CHECK,
                    amount=check_payment.amount,
                    currency=check_payment.currency,
                    payment_date=check_payment.payment_date,
                    received_date=check_payment.payment_date,
                    check_number=check_payment.check_number,
                    check_bank_name=check_payment.check_bank_name,
                    status="pending",
                    reconciled=False,
                    notes=check_payment.notes,
                    recorded_by="test-user-123",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                mock_record.return_value = mock_response

                response = client.post(
                    "/api/v1/billing/payments/check",
                    json=check_payment.dict(),
                    headers=auth_headers
                )

                assert response.status_code == 200
                data = response.json()
                assert data["payment_method"] == "check"
                assert data["check_number"] == "12345"
                assert data["check_bank_name"] == "Wells Fargo"

    @pytest.mark.asyncio
    async def test_check_payment_requires_number(self):
        """Test that check payments require a check number"""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            CheckPaymentCreate(
                customer_id="CUST-004",
                amount=100.00,
                currency="USD",
                payment_date=datetime.utcnow(),
                # Missing check_number - should fail validation
            )


class TestBankTransferRecording:
    """Test bank transfer recording"""

    @pytest.mark.asyncio
    async def test_record_bank_transfer(self, auth_headers, mock_current_user):
        """Test recording a bank transfer"""
        with patch('dotmac.platform.auth.dependencies.get_current_user', return_value=mock_current_user):
            with patch('dotmac.platform.billing.bank_accounts.service.ManualPaymentService.record_bank_transfer') as mock_record:
                transfer = BankTransferCreate(
                    customer_id="CUST-005",
                    invoice_id="INV-005",
                    bank_account_id=1,
                    amount=1500.00,
                    currency="USD",
                    payment_date=datetime.utcnow(),
                    payment_method=PaymentMethodType.BANK_TRANSFER,
                    sender_name="ABC Corporation",
                    sender_bank="Chase Bank",
                    sender_account_last_four="9876",
                    external_reference="TRF123456",
                    notes="Monthly payment"
                )

                mock_response = ManualPaymentResponse(
                    id=5,
                    tenant_id="test-tenant",
                    payment_reference="TRF-20240101120300-GHI789",
                    external_reference=transfer.external_reference,
                    customer_id=transfer.customer_id,
                    invoice_id=transfer.invoice_id,
                    bank_account_id=transfer.bank_account_id,
                    payment_method=transfer.payment_method,
                    amount=transfer.amount,
                    currency=transfer.currency,
                    payment_date=transfer.payment_date,
                    received_date=transfer.payment_date,
                    sender_name=transfer.sender_name,
                    sender_bank=transfer.sender_bank,
                    sender_account_last_four=transfer.sender_account_last_four,
                    status="pending",
                    reconciled=False,
                    notes=transfer.notes,
                    recorded_by="test-user-123",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                mock_record.return_value = mock_response

                response = client.post(
                    "/api/v1/billing/payments/bank-transfer",
                    json=transfer.dict(),
                    headers=auth_headers
                )

                assert response.status_code == 200
                data = response.json()
                assert data["payment_method"] == "bank_transfer"
                assert data["sender_name"] == "ABC Corporation"
                assert data["sender_bank"] == "Chase Bank"
                assert data["sender_account_last_four"] == "9876"

    @pytest.mark.asyncio
    async def test_wire_transfer_recording(self, auth_headers, mock_current_user):
        """Test recording an international wire transfer"""
        with patch('dotmac.platform.auth.dependencies.get_current_user', return_value=mock_current_user):
            with patch('dotmac.platform.billing.bank_accounts.service.ManualPaymentService.record_bank_transfer') as mock_record:
                wire_transfer = BankTransferCreate(
                    customer_id="CUST-006",
                    amount=5000.00,
                    currency="EUR",
                    payment_date=datetime.utcnow(),
                    payment_method=PaymentMethodType.WIRE_TRANSFER,
                    sender_name="European Client Ltd",
                    sender_bank="Deutsche Bank",
                    external_reference="WIRE789012",
                    notes="International wire transfer"
                )

                mock_response = ManualPaymentResponse(
                    id=6,
                    tenant_id="test-tenant",
                    payment_reference="TRF-20240101120400-JKL012",
                    external_reference=wire_transfer.external_reference,
                    customer_id=wire_transfer.customer_id,
                    payment_method=wire_transfer.payment_method,
                    amount=wire_transfer.amount,
                    currency=wire_transfer.currency,
                    payment_date=wire_transfer.payment_date,
                    received_date=wire_transfer.payment_date,
                    sender_name=wire_transfer.sender_name,
                    sender_bank=wire_transfer.sender_bank,
                    status="pending",
                    reconciled=False,
                    notes=wire_transfer.notes,
                    recorded_by="test-user-123",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                mock_record.return_value = mock_response

                response = client.post(
                    "/api/v1/billing/payments/bank-transfer",
                    json=wire_transfer.dict(),
                    headers=auth_headers
                )

                assert response.status_code == 200
                data = response.json()
                assert data["payment_method"] == "wire_transfer"
                assert data["currency"] == "EUR"


class TestMobileMoneyRecording:
    """Test mobile money payment recording"""

    @pytest.mark.asyncio
    async def test_record_mpesa_payment(self, auth_headers, mock_current_user):
        """Test recording an M-Pesa mobile money payment"""
        with patch('dotmac.platform.auth.dependencies.get_current_user', return_value=mock_current_user):
            with patch('dotmac.platform.billing.bank_accounts.service.ManualPaymentService.record_mobile_money') as mock_record:
                mobile_payment = MobileMoneyCreate(
                    customer_id="CUST-007",
                    invoice_id="INV-007",
                    amount=250.00,
                    currency="KES",
                    payment_date=datetime.utcnow(),
                    mobile_number="+254700000000",
                    mobile_provider="M-Pesa",
                    external_reference="MPESA123ABC",
                    notes="Mobile payment from Kenya"
                )

                mock_response = ManualPaymentResponse(
                    id=7,
                    tenant_id="test-tenant",
                    payment_reference="MOB-20240101120500-MNO345",
                    external_reference=mobile_payment.external_reference,
                    customer_id=mobile_payment.customer_id,
                    invoice_id=mobile_payment.invoice_id,
                    payment_method=PaymentMethodType.MOBILE_MONEY,
                    amount=mobile_payment.amount,
                    currency=mobile_payment.currency,
                    payment_date=mobile_payment.payment_date,
                    received_date=mobile_payment.payment_date,
                    mobile_number=mobile_payment.mobile_number,
                    mobile_provider=mobile_payment.mobile_provider,
                    status="pending",
                    reconciled=False,
                    notes=mobile_payment.notes,
                    recorded_by="test-user-123",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                mock_record.return_value = mock_response

                response = client.post(
                    "/api/v1/billing/payments/mobile-money",
                    json=mobile_payment.dict(),
                    headers=auth_headers
                )

                assert response.status_code == 200
                data = response.json()
                assert data["payment_method"] == "mobile_money"
                assert data["mobile_number"] == "+254700000000"
                assert data["mobile_provider"] == "M-Pesa"
                assert data["currency"] == "KES"


class TestPaymentVerification:
    """Test payment verification workflow"""

    @pytest.mark.asyncio
    async def test_verify_payment(self, auth_headers, mock_current_user):
        """Test verifying a pending payment"""
        with patch('dotmac.platform.auth.dependencies.get_current_user', return_value=mock_current_user):
            with patch('dotmac.platform.billing.bank_accounts.service.ManualPaymentService.verify_payment') as mock_verify:
                mock_response = ManualPaymentResponse(
                    id=10,
                    tenant_id="test-tenant",
                    payment_reference="CASH-20240101120600-PQR678",
                    customer_id="CUST-010",
                    payment_method=PaymentMethodType.CASH,
                    amount=200.00,
                    currency="USD",
                    payment_date=datetime.utcnow(),
                    received_date=datetime.utcnow(),
                    status="verified",
                    reconciled=False,
                    approved_by="test-user-123",
                    approved_at=datetime.utcnow(),
                    recorded_by="another-user",
                    created_at=datetime.utcnow() - timedelta(hours=1),
                    updated_at=datetime.utcnow()
                )
                mock_verify.return_value = mock_response

                response = client.post(
                    "/api/v1/billing/payments/10/verify",
                    json={"notes": "Verified against receipt"},
                    headers=auth_headers
                )

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "verified"
                assert data["approved_by"] == "test-user-123"
                assert data["approved_at"] is not None

    @pytest.mark.asyncio
    async def test_cannot_verify_already_verified(self):
        """Test that already verified payments cannot be re-verified"""
        from dotmac.platform.billing.bank_accounts.service import ManualPaymentService

        mock_db = MagicMock()
        mock_payment = MagicMock()
        mock_payment.status = "verified"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_payment
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = ManualPaymentService(mock_db)

        # Should handle already verified payment gracefully
        result = await service.verify_payment("test-tenant", 1, "user123", "Re-verify attempt")

        # Payment status should remain verified
        assert mock_payment.status == "verified"


class TestPaymentReconciliation:
    """Test payment reconciliation features"""

    @pytest.mark.asyncio
    async def test_reconcile_multiple_payments(self, auth_headers, mock_current_user):
        """Test reconciling multiple payments at once"""
        with patch('dotmac.platform.auth.dependencies.get_current_user', return_value=mock_current_user):
            with patch('dotmac.platform.billing.bank_accounts.service.ManualPaymentService.reconcile_payments') as mock_reconcile:
                payment_ids = [1, 2, 3, 4, 5]

                mock_responses = []
                for pid in payment_ids:
                    mock_responses.append(ManualPaymentResponse(
                        id=pid,
                        tenant_id="test-tenant",
                        payment_reference=f"PAY-{pid}",
                        customer_id=f"CUST-{pid:03d}",
                        payment_method=PaymentMethodType.CASH,
                        amount=100.00 * pid,
                        currency="USD",
                        payment_date=datetime.utcnow(),
                        received_date=datetime.utcnow(),
                        status="reconciled",
                        reconciled=True,
                        reconciled_at=datetime.utcnow(),
                        reconciled_by="test-user-123",
                        recorded_by="various-users",
                        created_at=datetime.utcnow() - timedelta(days=pid),
                        updated_at=datetime.utcnow()
                    ))

                mock_reconcile.return_value = mock_responses

                response = client.post(
                    "/api/v1/billing/payments/reconcile",
                    json={
                        "payment_ids": payment_ids,
                        "reconciliation_notes": "Monthly bank statement reconciliation"
                    },
                    headers=auth_headers
                )

                assert response.status_code == 200
                data = response.json()
                assert len(data) == 5
                assert all(p["reconciled"] is True for p in data)
                assert all(p["status"] == "reconciled" for p in data)


class TestPaymentSearch:
    """Test payment search and filtering"""

    @pytest.mark.asyncio
    async def test_search_payments_by_customer(self, auth_headers, mock_current_user):
        """Test searching payments by customer ID"""
        with patch('dotmac.platform.auth.dependencies.get_current_user', return_value=mock_current_user):
            with patch('dotmac.platform.billing.bank_accounts.service.ManualPaymentService.search_payments') as mock_search:
                mock_payments = [
                    ManualPaymentResponse(
                        id=1,
                        tenant_id="test-tenant",
                        payment_reference="CASH-001",
                        customer_id="CUST-001",
                        payment_method=PaymentMethodType.CASH,
                        amount=100.00,
                        currency="USD",
                        payment_date=datetime.utcnow(),
                        status="pending",
                        reconciled=False,
                        recorded_by="user1",
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    ),
                    ManualPaymentResponse(
                        id=2,
                        tenant_id="test-tenant",
                        payment_reference="CHECK-001",
                        customer_id="CUST-001",
                        payment_method=PaymentMethodType.CHECK,
                        amount=200.00,
                        currency="USD",
                        payment_date=datetime.utcnow() - timedelta(days=1),
                        status="verified",
                        reconciled=False,
                        recorded_by="user2",
                        created_at=datetime.utcnow() - timedelta(days=1),
                        updated_at=datetime.utcnow()
                    )
                ]
                mock_search.return_value = mock_payments

                filters = PaymentSearchFilters(customer_id="CUST-001")

                response = client.post(
                    "/api/v1/billing/payments/search",
                    json=filters.dict(),
                    headers=auth_headers
                )

                assert response.status_code == 200
                data = response.json()
                assert len(data) == 2
                assert all(p["customer_id"] == "CUST-001" for p in data)

    @pytest.mark.asyncio
    async def test_search_payments_by_date_range(self, auth_headers, mock_current_user):
        """Test searching payments by date range"""
        with patch('dotmac.platform.auth.dependencies.get_current_user', return_value=mock_current_user):
            with patch('dotmac.platform.billing.bank_accounts.service.ManualPaymentService.search_payments') as mock_search:
                start_date = datetime.utcnow() - timedelta(days=30)
                end_date = datetime.utcnow()

                mock_search.return_value = []

                filters = PaymentSearchFilters(
                    date_from=start_date,
                    date_to=end_date
                )

                response = client.post(
                    "/api/v1/billing/payments/search",
                    json=filters.dict(),
                    headers=auth_headers
                )

                assert response.status_code == 200

                # Verify the service was called with correct filters
                mock_search.assert_called_once()
                call_args = mock_search.call_args
                assert call_args[1]["filters"].date_from == start_date
                assert call_args[1]["filters"].date_to == end_date

    @pytest.mark.asyncio
    async def test_search_payments_by_method(self, auth_headers, mock_current_user):
        """Test searching payments by payment method"""
        with patch('dotmac.platform.auth.dependencies.get_current_user', return_value=mock_current_user):
            with patch('dotmac.platform.billing.bank_accounts.service.ManualPaymentService.search_payments') as mock_search:
                mock_search.return_value = []

                filters = PaymentSearchFilters(payment_method=PaymentMethodType.CHECK)

                response = client.post(
                    "/api/v1/billing/payments/search",
                    json=filters.dict(),
                    headers=auth_headers
                )

                assert response.status_code == 200

                # Verify the service was called with check filter
                mock_search.assert_called_once()
                call_args = mock_search.call_args
                assert call_args[1]["filters"].payment_method == PaymentMethodType.CHECK

    @pytest.mark.asyncio
    async def test_search_unreconciled_payments(self, auth_headers, mock_current_user):
        """Test searching for unreconciled payments"""
        with patch('dotmac.platform.auth.dependencies.get_current_user', return_value=mock_current_user):
            with patch('dotmac.platform.billing.bank_accounts.service.ManualPaymentService.search_payments') as mock_search:
                mock_search.return_value = []

                filters = PaymentSearchFilters(reconciled=False)

                response = client.post(
                    "/api/v1/billing/payments/search",
                    json=filters.dict(),
                    headers=auth_headers
                )

                assert response.status_code == 200

                # Verify the service was called with reconciled=False
                mock_search.assert_called_once()
                call_args = mock_search.call_args
                assert call_args[1]["filters"].reconciled is False


class TestPaymentReferenceGeneration:
    """Test payment reference generation"""

    def test_payment_reference_format(self):
        """Test that payment references are generated correctly"""
        from dotmac.platform.billing.bank_accounts.service import ManualPaymentService

        service = ManualPaymentService(MagicMock())

        # Test different payment type prefixes
        cash_ref = service._generate_payment_reference("CASH")
        assert cash_ref.startswith("CASH-")

        check_ref = service._generate_payment_reference("CHK")
        assert check_ref.startswith("CHK-")

        transfer_ref = service._generate_payment_reference("TRF")
        assert transfer_ref.startswith("TRF-")

        # Verify format: PREFIX-TIMESTAMP-RANDOM
        parts = cash_ref.split("-")
        assert len(parts) == 3
        assert parts[0] == "CASH"
        assert len(parts[1]) == 14  # YYYYMMDDHHMMss
        assert len(parts[2]) == 6  # Random hex

    def test_payment_reference_uniqueness(self):
        """Test that payment references are unique"""
        from dotmac.platform.billing.bank_accounts.service import ManualPaymentService

        service = ManualPaymentService(MagicMock())

        refs = set()
        for _ in range(100):
            ref = service._generate_payment_reference("TEST")
            assert ref not in refs  # Should be unique
            refs.add(ref)


class TestPaymentValidation:
    """Test payment data validation"""

    def test_negative_amount_rejected(self):
        """Test that negative payment amounts are rejected"""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            CashPaymentCreate(
                customer_id="CUST-001",
                amount=-100.00,  # Negative amount
                currency="USD",
                payment_date=datetime.utcnow()
            )

    def test_zero_amount_rejected(self):
        """Test that zero payment amounts are rejected"""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            CashPaymentCreate(
                customer_id="CUST-001",
                amount=0.00,  # Zero amount
                currency="USD",
                payment_date=datetime.utcnow()
            )

    def test_amount_precision(self):
        """Test that payment amounts are rounded to 2 decimal places"""
        payment = CashPaymentCreate(
            customer_id="CUST-001",
            amount=100.999,  # More than 2 decimal places
            currency="USD",
            payment_date=datetime.utcnow()
        )

        # Should be rounded to 2 decimal places
        assert payment.amount == 101.00

    def test_mobile_number_required_for_mobile_money(self):
        """Test that mobile number is required for mobile money payments"""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            MobileMoneyCreate(
                customer_id="CUST-001",
                amount=100.00,
                currency="KES",
                payment_date=datetime.utcnow(),
                # Missing mobile_number
                mobile_provider="M-Pesa"
            )

    def test_currency_code_validation(self):
        """Test that currency codes are validated"""
        payment = CashPaymentCreate(
            customer_id="CUST-001",
            amount=100.00,
            currency="usd",  # Lowercase
            payment_date=datetime.utcnow()
        )

        # Should be uppercase
        assert payment.currency == "USD"