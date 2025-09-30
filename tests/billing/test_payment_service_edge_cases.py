"""
Additional edge case tests for PaymentService to achieve 90%+ coverage
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from dotmac.platform.billing.core.entities import (
    PaymentEntity,
    PaymentMethodEntity,
    TransactionEntity,
)
from dotmac.platform.billing.core.enums import (
    PaymentMethodStatus,
    PaymentMethodType,
    PaymentStatus,
)
from dotmac.platform.billing.core.exceptions import (
    PaymentError,
)
from dotmac.platform.billing.payments.providers import MockPaymentProvider
from dotmac.platform.billing.payments.service import PaymentService


class TestPaymentServiceEdgeCases:
    """Edge cases to achieve 90% coverage"""

    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        session = AsyncMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.rollback = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def service(self, mock_db):
        """Payment service with mock dependencies"""
        return PaymentService(
            db_session=mock_db,
            payment_providers={"mock": MockPaymentProvider()}
        )

    @pytest.mark.asyncio
    async def test_create_payment_with_existing_idempotency_key_returns_early(
        self, service, mock_db
    ):
        """Test that idempotency returns existing payment before checking payment method"""
        # Setup existing payment with idempotency key
        existing_payment = PaymentEntity(
            tenant_id="test",
            payment_id=str(uuid4()),
            amount=1000,
            currency="USD",
            customer_id="cust_123",
            status=PaymentStatus.SUCCEEDED,
            idempotency_key="idem_key_123",
            provider="mock",
            payment_method_type=PaymentMethodType.CARD,
            payment_method_details={},
            retry_count=0,
            created_at=datetime.now(timezone.utc),
            extra_data={},
        )

        # Mock execute to return existing payment on idempotency check
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=existing_payment)
        mock_db.execute.return_value = mock_result

        # Execute
        result = await service.create_payment(
            tenant_id="test",
            amount=1000,
            currency="USD",
            customer_id="cust_123",
            payment_method_id="pm_123",
            idempotency_key="idem_key_123",
        )

        # Verify returns existing payment without further processing
        assert result.payment_id == existing_payment.payment_id
        # Should only call execute once for idempotency check
        assert mock_db.execute.call_count == 1
        mock_db.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_refund_with_existing_idempotency_key_returns_early(
        self, service, mock_db
    ):
        """Test refund idempotency returns existing refund"""
        # Setup existing refund
        existing_refund = PaymentEntity(
            tenant_id="test",
            payment_id=str(uuid4()),
            amount=-500,
            currency="USD",
            customer_id="cust_123",
            status=PaymentStatus.REFUNDED,
            idempotency_key="refund_key_123",
            provider="mock",
            payment_method_type=PaymentMethodType.CARD,
            payment_method_details={},
            retry_count=0,
            created_at=datetime.now(timezone.utc),
            extra_data={},
        )

        # Mock returns existing refund on idempotency check, then original payment
        call_count = 0

        async def mock_execute(query):
            nonlocal call_count
            mock_result = MagicMock()
            call_count += 1
            if call_count == 1:
                # First call - check for existing payment
                mock_result.scalar_one_or_none = MagicMock(return_value=PaymentEntity(
                    tenant_id="test",
                    payment_id=str(uuid4()),
                    amount=1000,
                    currency="USD",
                    customer_id="cust_123",
                    status=PaymentStatus.SUCCEEDED,
                    provider="mock",
                    payment_method_type=PaymentMethodType.CARD,
                    payment_method_details={},
                    retry_count=0,
                    created_at=datetime.now(timezone.utc),
                ))
            else:
                # Second call - idempotency check returns existing refund
                mock_result.scalar_one_or_none = MagicMock(return_value=existing_refund)
            return mock_result

        mock_db.execute = AsyncMock(side_effect=mock_execute)

        # Execute
        result = await service.refund_payment(
            tenant_id="test",
            payment_id="pay_123",
            idempotency_key="refund_key_123",
        )

        # Verify returns existing refund
        assert result.payment_id == existing_refund.payment_id
        assert result.amount == -500

    @pytest.mark.asyncio
    async def test_refund_no_provider_configured_mocks_success(
        self, service, mock_db
    ):
        """Test refund when provider not configured mocks success"""
        # Remove providers
        service.providers = {}

        # Setup original payment
        original_payment = PaymentEntity(
            tenant_id="test",
            payment_id=str(uuid4()),
            amount=1000,
            currency="USD",
            customer_id="cust_123",
            status=PaymentStatus.SUCCEEDED,
            provider="nonexistent",
            payment_method_type=PaymentMethodType.CARD,
            payment_method_details={},
            retry_count=0,
            created_at=datetime.now(timezone.utc),
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=original_payment)
        mock_db.execute.return_value = mock_result

        # Mock refresh to populate IDs
        async def mock_refresh(entity):
            if hasattr(entity, 'payment_id') and entity.payment_id is None:
                entity.payment_id = str(uuid4())
            if hasattr(entity, 'created_at') and entity.created_at is None:
                entity.created_at = datetime.now(timezone.utc)
            if hasattr(entity, 'extra_data') and entity.extra_data is None:
                entity.extra_data = {}

        mock_db.refresh = AsyncMock(side_effect=mock_refresh)

        # Execute with logging check
        with patch('dotmac.platform.billing.payments.service.logger') as mock_logger:
            result = await service.refund_payment(
                tenant_id="test",
                payment_id=original_payment.payment_id,
            )

        # Verify mocked success
        assert result.status == PaymentStatus.REFUNDED
        mock_logger.warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_retry_payment_no_provider_mocks_success(
        self, service, mock_db
    ):
        """Test retry when provider not configured mocks success"""
        # Remove providers
        service.providers = {}

        # Setup failed payment
        failed_payment = PaymentEntity(
            tenant_id="test",
            payment_id=str(uuid4()),
            amount=1000,
            currency="USD",
            customer_id="cust_123",
            status=PaymentStatus.FAILED,
            provider="nonexistent",
            payment_method_type=PaymentMethodType.CARD,
            payment_method_details={"payment_method_id": "pm_123"},
            retry_count=0,
            created_at=datetime.now(timezone.utc),
            extra_data={},
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=failed_payment)
        mock_db.execute.return_value = mock_result

        # Mock refresh
        async def mock_refresh(entity):
            if hasattr(entity, 'payment_id') and entity.payment_id is None:
                entity.payment_id = str(uuid4())
            if hasattr(entity, 'extra_data') and entity.extra_data is None:
                entity.extra_data = {}

        mock_db.refresh = AsyncMock(side_effect=mock_refresh)

        # Execute
        result = await service.retry_failed_payment(
            tenant_id="test",
            payment_id=failed_payment.payment_id,
        )

        # Verify mocked success
        assert result.status == PaymentStatus.SUCCEEDED
        assert failed_payment.retry_count == 1

    @pytest.mark.asyncio
    async def test_retry_payment_exception_handling(
        self, service, mock_db
    ):
        """Test retry payment exception is properly handled"""
        # Setup failed payment with payment method
        failed_payment = PaymentEntity(
            tenant_id="test",
            payment_id=str(uuid4()),
            amount=1000,
            currency="USD",
            customer_id="cust_123",
            status=PaymentStatus.FAILED,
            provider="mock",
            payment_method_type=PaymentMethodType.CARD,
            payment_method_details={"payment_method_id": "pm_123"},
            retry_count=0,
            created_at=datetime.now(timezone.utc),
            extra_data={},
        )

        payment_method = PaymentMethodEntity(
            tenant_id="test",
            payment_method_id="pm_123",
            customer_id="cust_123",
            type=PaymentMethodType.CARD,
            status=PaymentMethodStatus.ACTIVE,
            provider="mock",
            provider_payment_method_id="mock_pm_123",
            display_name="Test Card",
            is_active=True,
            is_default=True,
            auto_pay_enabled=False,
            extra_data={},
        )

        # Mock execute to return payment and payment method
        call_count = 0

        async def mock_execute(query):
            nonlocal call_count
            mock_result = MagicMock()
            call_count += 1
            if call_count == 1:
                mock_result.scalar_one_or_none = MagicMock(return_value=failed_payment)
            else:
                mock_result.scalar_one_or_none = MagicMock(return_value=payment_method)
            return mock_result

        mock_db.execute = AsyncMock(side_effect=mock_execute)

        # Mock refresh
        async def mock_refresh(entity):
            entity.extra_data = {}

        mock_db.refresh = AsyncMock(side_effect=mock_refresh)

        # Make the provider raise an exception
        service.providers["mock"].charge_payment_method = AsyncMock(
            side_effect=Exception("Provider error")
        )

        # Execute with logging check
        with patch('dotmac.platform.billing.payments.service.logger') as mock_logger:
            result = await service.retry_failed_payment(
                tenant_id="test",
                payment_id=failed_payment.payment_id,
            )

        # Verify failure is handled
        assert result.status == PaymentStatus.FAILED
        assert result.failure_reason == "Provider error"
        mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_clear_default_payment_methods_with_existing_defaults(
        self, service, mock_db
    ):
        """Test clearing existing default payment methods"""
        # Setup multiple payment methods with one default
        default_method = PaymentMethodEntity(
            tenant_id="test",
            payment_method_id="pm_default",
            customer_id="cust_123",
            type=PaymentMethodType.CARD,
            status=PaymentMethodStatus.ACTIVE,
            provider="mock",
            provider_payment_method_id="mock_pm_1",
            display_name="Default Card",
            is_active=True,
            is_default=True,
        )

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all = MagicMock(return_value=[default_method])
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        mock_db.execute.return_value = mock_result

        # Execute
        await service._clear_default_payment_methods("test", "cust_123")

        # Verify default was cleared
        assert default_method.is_default is False
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_payment_method_first_becomes_default(
        self, service, mock_db
    ):
        """Test first payment method automatically becomes default"""
        # Mock no existing payment methods
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all = MagicMock(return_value=[])
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        mock_db.execute.return_value = mock_result

        # Mock refresh to populate fields
        async def mock_refresh(entity):
            entity.payment_method_id = str(uuid4())
            entity.created_at = datetime.now(timezone.utc)
            entity.extra_data = {}
            entity.auto_pay_enabled = False

        mock_db.refresh = AsyncMock(side_effect=mock_refresh)

        # Execute - not explicitly setting as default
        result = await service.add_payment_method(
            tenant_id="test",
            customer_id="cust_123",
            payment_method_type=PaymentMethodType.CARD,
            provider="mock",
            provider_payment_method_id="mock_pm_123",
            display_name="First Card",
            set_as_default=False,  # Explicitly false
        )

        # Verify first method becomes default anyway
        assert result.is_default is True

    @pytest.mark.asyncio
    async def test_add_payment_method_clear_existing_defaults(
        self, service, mock_db
    ):
        """Test adding payment method as default clears existing defaults"""
        # Setup existing default method
        existing_default = PaymentMethodEntity(
            tenant_id="test",
            payment_method_id="pm_old",
            customer_id="cust_123",
            type=PaymentMethodType.CARD,
            status=PaymentMethodStatus.ACTIVE,
            provider="mock",
            provider_payment_method_id="mock_pm_old",
            display_name="Old Default",
            is_active=True,
            is_default=True,
        )

        # Mock execute to return existing default for clearing
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all = MagicMock(return_value=[existing_default])
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        mock_db.execute.return_value = mock_result

        # Mock refresh
        async def mock_refresh(entity):
            entity.payment_method_id = str(uuid4())
            entity.created_at = datetime.now(timezone.utc)
            entity.extra_data = {}
            entity.auto_pay_enabled = False

        mock_db.refresh = AsyncMock(side_effect=mock_refresh)

        # Execute - explicitly set as default
        result = await service.add_payment_method(
            tenant_id="test",
            customer_id="cust_123",
            payment_method_type=PaymentMethodType.CARD,
            provider="mock",
            provider_payment_method_id="mock_pm_new",
            display_name="New Default",
            set_as_default=True,
        )

        # Verify old default was cleared
        assert existing_default.is_default is False
        assert result.is_default is True