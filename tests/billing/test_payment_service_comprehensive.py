"""
Comprehensive tests for PaymentService with 90%+ coverage
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any
from decimal import Decimal
from uuid import uuid4

from dotmac.platform.billing.core.entities import (
    PaymentEntity,
    PaymentMethodEntity,
    TransactionEntity,
    PaymentInvoiceEntity,
)
from dotmac.platform.billing.core.enums import (
    PaymentMethodStatus,
    PaymentMethodType,
    PaymentStatus,
    TransactionType,
)
from dotmac.platform.billing.core.exceptions import (
    PaymentError,
    PaymentMethodNotFoundError,
    PaymentNotFoundError,
)
from dotmac.platform.billing.core.models import Payment, PaymentMethod
from dotmac.platform.billing.payments.providers import (
    PaymentResult,
    RefundResult,
    MockPaymentProvider,
)
from dotmac.platform.billing.payments.service import PaymentService


class TestPaymentService:
    """Comprehensive tests for PaymentService"""

    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session"""
        session = AsyncMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.rollback = AsyncMock()

        # Setup default execute mock
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_result.scalars = MagicMock()
        mock_result.scalars.return_value.all = MagicMock(return_value=[])
        session.execute = AsyncMock(return_value=mock_result)

        return session

    @pytest.fixture
    def mock_provider(self):
        """Create mock payment provider"""
        provider = MockPaymentProvider(always_succeed=True)
        return provider

    @pytest.fixture
    def payment_service(self, mock_db_session, mock_provider):
        """Create PaymentService instance"""
        return PaymentService(
            db_session=mock_db_session,
            payment_providers={"stripe": mock_provider, "mock": mock_provider}
        )

    @pytest.fixture
    def sample_payment_method(self):
        """Create sample payment method entity"""
        return PaymentMethodEntity(
            tenant_id="test-tenant",
            payment_method_id=str(uuid4()),
            customer_id="customer_123",
            type=PaymentMethodType.CARD,
            status=PaymentMethodStatus.ACTIVE,
            provider="stripe",
            provider_payment_method_id="stripe_pm_123",
            display_name="Visa ending in 4242",
            last_four="4242",
            brand="visa",
            is_default=True,
            is_active=True,
            auto_pay_enabled=False,
            created_at=datetime.now(timezone.utc),
            extra_data={},
        )

    @pytest.fixture
    def sample_payment(self):
        """Create sample payment entity"""
        return PaymentEntity(
            tenant_id="test-tenant",
            payment_id=str(uuid4()),
            amount=1000,
            currency="USD",
            customer_id="customer_123",
            status=PaymentStatus.SUCCEEDED,
            provider="stripe",
            provider_payment_id="stripe_pay_123",
            payment_method_type=PaymentMethodType.CARD,
            payment_method_details={"last_four": "4242"},
            created_at=datetime.now(timezone.utc),
            retry_count=0,
            extra_data={},
        )

    def setup_db_mock(self, mock_db_session, scalar_value=None, scalars_values=None):
        """Helper to setup database mock results"""
        mock_result = MagicMock()
        if scalar_value is not None:
            mock_result.scalar_one_or_none = MagicMock(return_value=scalar_value)
        if scalars_values is not None:
            mock_result.scalars = MagicMock()
            mock_result.scalars.return_value.all = MagicMock(return_value=scalars_values)
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        return mock_result

    def setup_refresh_mock(self, mock_db_session):
        """Setup refresh mock to populate entity IDs"""
        async def mock_refresh(entity):
            if hasattr(entity, 'payment_id') and entity.payment_id is None:
                entity.payment_id = str(uuid4())
            if hasattr(entity, 'payment_method_id') and entity.payment_method_id is None:
                entity.payment_method_id = str(uuid4())
            if hasattr(entity, 'created_at') and entity.created_at is None:
                entity.created_at = datetime.now(timezone.utc)
            if hasattr(entity, 'retry_count') and entity.retry_count is None:
                entity.retry_count = 0
            if hasattr(entity, 'extra_data') and entity.extra_data is None:
                entity.extra_data = {}
            if hasattr(entity, 'auto_pay_enabled') and entity.auto_pay_enabled is None:
                entity.auto_pay_enabled = False
        mock_db_session.refresh = AsyncMock(side_effect=mock_refresh)

    # ============================================================================
    # Payment Creation Tests
    # ============================================================================

    @pytest.mark.asyncio
    async def test_create_payment_success(
        self, payment_service, mock_db_session, sample_payment_method
    ):
        """Test successful payment creation"""
        # Setup
        self.setup_db_mock(mock_db_session, scalar_value=sample_payment_method)
        self.setup_refresh_mock(mock_db_session)

        # Execute
        result = await payment_service.create_payment(
            tenant_id="test-tenant",
            amount=1000,
            currency="USD",
            customer_id="customer_123",
            payment_method_id="pm_123",
            provider="stripe",
        )

        # Verify
        assert isinstance(result, Payment)
        assert result.amount == 1000
        assert result.currency == "USD"
        assert result.status == PaymentStatus.SUCCEEDED

    @pytest.mark.asyncio
    async def test_create_payment_with_idempotency(
        self, payment_service, mock_db_session, sample_payment, sample_payment_method
    ):
        """Test payment creation with idempotency key"""
        sample_payment.idempotency_key = "idempotent_123"

        # Mock idempotency check returns existing payment
        async def mock_execute(query):
            mock_result = MagicMock()
            query_str = str(query)
            if "idempotency_key" in query_str:
                mock_result.scalar_one_or_none = MagicMock(return_value=sample_payment)
            else:
                mock_result.scalar_one_or_none = MagicMock(return_value=sample_payment_method)
            return mock_result

        mock_db_session.execute = AsyncMock(side_effect=mock_execute)

        # Execute
        result = await payment_service.create_payment(
            tenant_id="test-tenant",
            amount=1000,
            currency="USD",
            customer_id="customer_123",
            payment_method_id="pm_123",
            idempotency_key="idempotent_123",
        )

        # Verify returns existing payment
        assert result.payment_id == sample_payment.payment_id
        mock_db_session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_payment_method_not_found(
        self, payment_service, mock_db_session
    ):
        """Test payment creation when payment method not found"""
        # Setup - return None for both idempotency and payment method checks
        async def mock_execute(query):
            mock_result = MagicMock()
            mock_result.scalar_one_or_none = MagicMock(return_value=None)
            return mock_result

        mock_db_session.execute = AsyncMock(side_effect=mock_execute)

        # Execute & Verify
        with pytest.raises(PaymentMethodNotFoundError):
            await payment_service.create_payment(
                tenant_id="test-tenant",
                amount=1000,
                currency="USD",
                customer_id="customer_123",
                payment_method_id="nonexistent",
            )

    @pytest.mark.asyncio
    async def test_create_payment_inactive_method(
        self, payment_service, mock_db_session, sample_payment_method
    ):
        """Test payment creation with inactive payment method"""
        sample_payment_method.status = PaymentMethodStatus.INACTIVE
        self.setup_db_mock(mock_db_session, scalar_value=sample_payment_method)

        # Execute & Verify
        with pytest.raises(PaymentError, match="is not active"):
            await payment_service.create_payment(
                tenant_id="test-tenant",
                amount=1000,
                currency="USD",
                customer_id="customer_123",
                payment_method_id="pm_123",
            )

    @pytest.mark.asyncio
    async def test_create_payment_provider_failure(
        self, payment_service, mock_db_session, sample_payment_method
    ):
        """Test payment creation when provider fails"""
        # Setup
        self.setup_db_mock(mock_db_session, scalar_value=sample_payment_method)
        self.setup_refresh_mock(mock_db_session)

        # Use failing provider
        failing_provider = MockPaymentProvider(always_succeed=False)
        payment_service.providers["stripe"] = failing_provider

        # Execute
        result = await payment_service.create_payment(
            tenant_id="test-tenant",
            amount=1000,
            currency="USD",
            customer_id="customer_123",
            payment_method_id="pm_123",
            provider="stripe",
        )

        # Verify
        assert result.status == PaymentStatus.FAILED
        assert result.failure_reason == "Mock payment failed"

    @pytest.mark.asyncio
    async def test_create_payment_with_invoice_linking(
        self, payment_service, mock_db_session, sample_payment_method
    ):
        """Test payment creation with invoice linking"""
        # Setup
        self.setup_db_mock(mock_db_session, scalar_value=sample_payment_method)
        self.setup_refresh_mock(mock_db_session)

        # Execute
        result = await payment_service.create_payment(
            tenant_id="test-tenant",
            amount=2000,
            currency="USD",
            customer_id="customer_123",
            payment_method_id="pm_123",
            invoice_ids=["inv_001", "inv_002"],
        )

        # Verify
        assert result.status == PaymentStatus.SUCCEEDED
        # Verify PaymentInvoiceEntity was created for each invoice
        add_calls = mock_db_session.add.call_args_list
        invoice_links = [
            call[0][0] for call in add_calls
            if isinstance(call[0][0], PaymentInvoiceEntity)
        ]
        assert len(invoice_links) == 2

    @pytest.mark.asyncio
    async def test_create_payment_no_provider(
        self, payment_service, mock_db_session, sample_payment_method
    ):
        """Test payment creation when provider not configured"""
        # Setup
        self.setup_db_mock(mock_db_session, scalar_value=sample_payment_method)
        self.setup_refresh_mock(mock_db_session)
        payment_service.providers = {}  # No providers

        # Execute
        with patch('dotmac.platform.billing.payments.service.logger') as mock_logger:
            result = await payment_service.create_payment(
                tenant_id="test-tenant",
                amount=1000,
                currency="USD",
                customer_id="customer_123",
                payment_method_id="pm_123",
                provider="nonexistent",
            )

        # Verify - should mock success
        assert result.status == PaymentStatus.SUCCEEDED
        mock_logger.warning.assert_called_once()

    # ============================================================================
    # Payment Refund Tests
    # ============================================================================

    @pytest.mark.asyncio
    async def test_refund_payment_success(
        self, payment_service, mock_db_session, sample_payment
    ):
        """Test successful payment refund"""
        # Setup
        self.setup_db_mock(mock_db_session, scalar_value=sample_payment)
        self.setup_refresh_mock(mock_db_session)

        # Execute
        result = await payment_service.refund_payment(
            tenant_id="test-tenant",
            payment_id=sample_payment.payment_id,
            reason="Customer request",
        )

        # Verify
        assert result.amount == -sample_payment.amount
        assert result.status == PaymentStatus.REFUNDED

    @pytest.mark.asyncio
    async def test_partial_refund_payment(
        self, payment_service, mock_db_session, sample_payment
    ):
        """Test partial payment refund"""
        # Setup
        self.setup_db_mock(mock_db_session, scalar_value=sample_payment)
        self.setup_refresh_mock(mock_db_session)

        # Execute
        result = await payment_service.refund_payment(
            tenant_id="test-tenant",
            payment_id=sample_payment.payment_id,
            amount=500,  # Half of original
        )

        # Verify
        assert result.amount == -500
        assert result.status == PaymentStatus.REFUNDED
        # Original payment should be marked as partially refunded
        assert sample_payment.status == PaymentStatus.PARTIALLY_REFUNDED

    @pytest.mark.asyncio
    async def test_refund_payment_not_found(
        self, payment_service, mock_db_session
    ):
        """Test refunding non-existent payment"""
        # Setup - return None for all queries
        async def mock_execute(query):
            mock_result = MagicMock()
            mock_result.scalar_one_or_none = MagicMock(return_value=None)
            return mock_result

        mock_db_session.execute = AsyncMock(side_effect=mock_execute)

        # Execute & Verify
        with pytest.raises(PaymentNotFoundError):
            await payment_service.refund_payment(
                tenant_id="test-tenant",
                payment_id="nonexistent",
            )

    @pytest.mark.asyncio
    async def test_refund_failed_payment(
        self, payment_service, mock_db_session, sample_payment
    ):
        """Test refunding a failed payment"""
        sample_payment.status = PaymentStatus.FAILED
        self.setup_db_mock(mock_db_session, scalar_value=sample_payment)

        # Execute & Verify
        with pytest.raises(PaymentError, match="Can only refund successful payments"):
            await payment_service.refund_payment(
                tenant_id="test-tenant",
                payment_id=sample_payment.payment_id,
            )

    @pytest.mark.asyncio
    async def test_refund_exceeds_original(
        self, payment_service, mock_db_session, sample_payment
    ):
        """Test refund amount exceeding original payment"""
        self.setup_db_mock(mock_db_session, scalar_value=sample_payment)

        # Execute & Verify
        with pytest.raises(PaymentError, match="cannot exceed original"):
            await payment_service.refund_payment(
                tenant_id="test-tenant",
                payment_id=sample_payment.payment_id,
                amount=sample_payment.amount + 1,
            )

    # ============================================================================
    # Payment Method Management Tests
    # ============================================================================

    @pytest.mark.asyncio
    async def test_add_payment_method_card(
        self, payment_service, mock_db_session
    ):
        """Test adding a card payment method"""
        # Setup - no existing methods
        self.setup_db_mock(mock_db_session, scalar_value=None, scalars_values=[])
        self.setup_refresh_mock(mock_db_session)

        # Execute
        result = await payment_service.add_payment_method(
            tenant_id="test-tenant",
            customer_id="customer_123",
            payment_method_type=PaymentMethodType.CARD,
            provider="stripe",
            provider_payment_method_id="stripe_pm_123",
            display_name="Visa ending in 4242",
            last_four="4242",
            brand="visa",
            expiry_month=12,
            expiry_year=2025,
        )

        # Verify
        assert isinstance(result, PaymentMethod)
        assert result.type == PaymentMethodType.CARD
        assert result.last_four == "4242"
        assert result.is_default is True  # First method is default

    @pytest.mark.asyncio
    async def test_add_payment_method_bank(
        self, payment_service, mock_db_session, sample_payment_method
    ):
        """Test adding a bank account payment method"""
        # Setup - has existing method
        self.setup_db_mock(mock_db_session, scalar_value=None, scalars_values=[sample_payment_method])
        self.setup_refresh_mock(mock_db_session)

        # Execute
        result = await payment_service.add_payment_method(
            tenant_id="test-tenant",
            customer_id="customer_123",
            payment_method_type=PaymentMethodType.BANK_ACCOUNT,
            provider="stripe",
            provider_payment_method_id="stripe_ba_123",
            display_name="Chase ending in 6789",
            last_four="6789",
            bank_name="Chase Bank",
        )

        # Verify
        assert result.type == PaymentMethodType.BANK_ACCOUNT
        assert result.bank_name == "Chase Bank"
        assert result.is_default is False  # Not first method

    @pytest.mark.asyncio
    async def test_list_payment_methods(
        self, payment_service, mock_db_session, sample_payment_method
    ):
        """Test listing customer payment methods"""
        # Setup
        methods = [sample_payment_method]
        self.setup_db_mock(mock_db_session, scalars_values=methods)

        # Execute
        result = await payment_service.list_payment_methods(
            tenant_id="test-tenant",
            customer_id="customer_123",
        )

        # Verify
        assert len(result) == 1
        assert result[0].payment_method_id == sample_payment_method.payment_method_id

    @pytest.mark.asyncio
    async def test_get_payment_method(
        self, payment_service, mock_db_session, sample_payment_method
    ):
        """Test getting a specific payment method"""
        # Setup
        self.setup_db_mock(mock_db_session, scalar_value=sample_payment_method)

        # Execute
        result = await payment_service.get_payment_method(
            tenant_id="test-tenant",
            payment_method_id=sample_payment_method.payment_method_id,
        )

        # Verify
        assert result is not None
        assert result.payment_method_id == sample_payment_method.payment_method_id

    @pytest.mark.asyncio
    async def test_set_default_payment_method(
        self, payment_service, mock_db_session, sample_payment_method
    ):
        """Test setting payment method as default"""
        # Setup
        sample_payment_method.is_default = False
        self.setup_db_mock(mock_db_session, scalar_value=sample_payment_method, scalars_values=[])
        self.setup_refresh_mock(mock_db_session)

        # Execute
        result = await payment_service.set_default_payment_method(
            tenant_id="test-tenant",
            customer_id="customer_123",
            payment_method_id=sample_payment_method.payment_method_id,
        )

        # Verify
        assert result.is_default is True

    @pytest.mark.asyncio
    async def test_set_default_method_not_found(
        self, payment_service, mock_db_session
    ):
        """Test setting non-existent payment method as default"""
        # Setup - return None for all queries
        async def mock_execute(query):
            mock_result = MagicMock()
            mock_result.scalar_one_or_none = MagicMock(return_value=None)
            mock_result.scalars = MagicMock()
            mock_result.scalars.return_value.all = MagicMock(return_value=[])
            return mock_result

        mock_db_session.execute = AsyncMock(side_effect=mock_execute)

        # Execute & Verify
        with pytest.raises(PaymentMethodNotFoundError):
            await payment_service.set_default_payment_method(
                tenant_id="test-tenant",
                customer_id="customer_123",
                payment_method_id="nonexistent",
            )

    @pytest.mark.asyncio
    async def test_delete_payment_method(
        self, payment_service, mock_db_session, sample_payment_method
    ):
        """Test soft deleting a payment method"""
        # Setup
        self.setup_db_mock(mock_db_session, scalar_value=sample_payment_method)

        # Execute
        result = await payment_service.delete_payment_method(
            tenant_id="test-tenant",
            payment_method_id=sample_payment_method.payment_method_id,
        )

        # Verify
        assert result is True
        assert sample_payment_method.is_active is False
        assert sample_payment_method.status == PaymentMethodStatus.INACTIVE

    # ============================================================================
    # Retry Payment Tests
    # ============================================================================

    @pytest.mark.asyncio
    async def test_retry_failed_payment_success(
        self, payment_service, mock_db_session, sample_payment, sample_payment_method
    ):
        """Test successfully retrying a failed payment"""
        # Setup
        sample_payment.status = PaymentStatus.FAILED
        sample_payment.retry_count = 0
        sample_payment.payment_method_details = {"payment_method_id": "pm_123"}

        async def mock_execute(query):
            mock_result = MagicMock()
            query_str = str(query)
            if "payment_method_id" in query_str:
                mock_result.scalar_one_or_none = MagicMock(return_value=sample_payment_method)
            else:
                mock_result.scalar_one_or_none = MagicMock(return_value=sample_payment)
            return mock_result

        mock_db_session.execute = AsyncMock(side_effect=mock_execute)
        self.setup_refresh_mock(mock_db_session)

        # Execute
        result = await payment_service.retry_failed_payment(
            tenant_id="test-tenant",
            payment_id=sample_payment.payment_id,
        )

        # Verify
        assert result.status == PaymentStatus.SUCCEEDED
        assert sample_payment.retry_count == 1

    @pytest.mark.asyncio
    async def test_retry_payment_max_attempts(
        self, payment_service, mock_db_session, sample_payment
    ):
        """Test retrying payment when max attempts reached"""
        sample_payment.status = PaymentStatus.FAILED
        sample_payment.retry_count = 3  # Max
        self.setup_db_mock(mock_db_session, scalar_value=sample_payment)

        # Execute & Verify
        with pytest.raises(PaymentError, match="Maximum retry attempts"):
            await payment_service.retry_failed_payment(
                tenant_id="test-tenant",
                payment_id=sample_payment.payment_id,
            )

    @pytest.mark.asyncio
    async def test_retry_non_failed_payment(
        self, payment_service, mock_db_session, sample_payment
    ):
        """Test retrying a non-failed payment"""
        sample_payment.status = PaymentStatus.SUCCEEDED
        self.setup_db_mock(mock_db_session, scalar_value=sample_payment)

        # Execute & Verify
        with pytest.raises(PaymentError, match="Can only retry failed"):
            await payment_service.retry_failed_payment(
                tenant_id="test-tenant",
                payment_id=sample_payment.payment_id,
            )

    # ============================================================================
    # Edge Cases and Error Scenarios
    # ============================================================================

    @pytest.mark.asyncio
    async def test_create_payment_zero_amount(
        self, payment_service, mock_db_session, sample_payment_method
    ):
        """Test creating payment with zero amount"""
        # Setup
        self.setup_db_mock(mock_db_session, scalar_value=sample_payment_method)
        self.setup_refresh_mock(mock_db_session)

        # Execute
        result = await payment_service.create_payment(
            tenant_id="test-tenant",
            amount=0,
            currency="USD",
            customer_id="customer_123",
            payment_method_id="pm_123",
        )

        # Verify - should still process
        assert result.amount == 0
        assert result.status == PaymentStatus.SUCCEEDED

    @pytest.mark.asyncio
    async def test_payment_with_metadata(
        self, payment_service, mock_db_session, sample_payment_method
    ):
        """Test payment with special characters in metadata"""
        # Setup
        self.setup_db_mock(mock_db_session, scalar_value=sample_payment_method)
        self.setup_refresh_mock(mock_db_session)

        metadata = {
            "description": "Payment for 'Special' Order #123",
            "unicode": "Payment with emoji 🎉",
        }

        # Execute
        result = await payment_service.create_payment(
            tenant_id="test-tenant",
            amount=1000,
            currency="USD",
            customer_id="customer_123",
            payment_method_id="pm_123",
            metadata=metadata,
        )

        # Verify
        assert result.extra_data == metadata

    # ============================================================================
    # Provider Tests
    # ============================================================================

    @pytest.mark.asyncio
    async def test_mock_provider_operations(self):
        """Test MockPaymentProvider operations"""
        provider = MockPaymentProvider(always_succeed=True)

        # Test charge
        charge_result = await provider.charge_payment_method(
            amount=1000,
            currency="USD",
            payment_method_id="pm_123",
        )
        assert charge_result.success is True
        assert charge_result.provider_payment_id == "mock_payment_1"

        # Test refund
        refund_result = await provider.refund_payment(
            provider_payment_id="payment_123",
            amount=500,
        )
        assert refund_result.success is True
        assert refund_result.provider_refund_id == "mock_refund_1"

        # Test setup intent
        setup_intent = await provider.create_setup_intent(
            customer_id="customer_123",
            payment_method_types=["card"],
        )
        assert setup_intent.intent_id == "mock_setup_intent_customer_123"

        # Test failure mode
        failing_provider = MockPaymentProvider(always_succeed=False)
        charge_result = await failing_provider.charge_payment_method(
            amount=1000,
            currency="USD",
            payment_method_id="pm_123",
        )
        assert charge_result.success is False
        assert charge_result.error_message == "Mock payment failed"

    # ============================================================================
    # Helper Method Tests
    # ============================================================================

    @pytest.mark.asyncio
    async def test_private_helper_methods(
        self, payment_service, mock_db_session, sample_payment, sample_payment_method
    ):
        """Test private helper methods"""
        # Test _get_payment_entity
        self.setup_db_mock(mock_db_session, scalar_value=sample_payment)
        payment = await payment_service._get_payment_entity("test-tenant", "payment_123")
        assert payment == sample_payment

        # Test _get_payment_method
        self.setup_db_mock(mock_db_session, scalar_value=sample_payment_method)
        method = await payment_service._get_payment_method("test-tenant", "pm_123")
        assert method == sample_payment_method

        # Test _count_payment_methods
        self.setup_db_mock(mock_db_session, scalars_values=[sample_payment_method])
        count = await payment_service._count_payment_methods("test-tenant", "customer_123")
        assert count == 1

        # Test _create_transaction
        await payment_service._create_transaction(sample_payment, TransactionType.PAYMENT)
        mock_db_session.add.assert_called()
        add_call = mock_db_session.add.call_args[0][0]
        assert isinstance(add_call, TransactionEntity)
        assert add_call.amount == sample_payment.amount

    @pytest.mark.asyncio
    async def test_payment_method_customer_mismatch(
        self, payment_service, mock_db_session, sample_payment_method
    ):
        """Test payment method belonging to different customer"""
        sample_payment_method.customer_id = "other_customer"
        self.setup_db_mock(mock_db_session, scalar_value=sample_payment_method)

        # Execute & Verify
        with pytest.raises(PaymentError, match="does not belong to customer"):
            await payment_service.set_default_payment_method(
                tenant_id="test-tenant",
                customer_id="customer_123",
                payment_method_id=sample_payment_method.payment_method_id,
            )