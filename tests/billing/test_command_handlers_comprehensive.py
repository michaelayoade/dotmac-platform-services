"""
Tests for billing command handlers that were recently implemented.

NOTE: These unit tests with mocks have been replaced by integration tests
in test_command_handlers_integration.py which use real database and services.

The integration tests are more reliable and test the full stack including:
- Database persistence
- Service layer interactions
- Event publishing
- Tenant isolation

Verifies that:
1. handle_update_invoice calls InvoiceService.update_invoice
2. handle_send_invoice calls InvoiceService.send_invoice_email
3. handle_apply_payment_to_invoice calls InvoiceService.apply_payment_to_invoice
4. handle_cancel_payment calls PaymentService.cancel_payment
5. handle_record_offline_payment calls PaymentService.record_offline_payment
"""

import pytest

# Skip entire module - replaced by integration tests
pytestmark = pytest.mark.skip(
    reason="Replaced by integration tests in test_command_handlers_integration.py"
)
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from dotmac.platform.billing.commands.handlers import (
    InvoiceCommandHandler,
    PaymentCommandHandler,
)
from dotmac.platform.billing.commands.invoice_commands import (
    ApplyPaymentToInvoiceCommand,
    SendInvoiceCommand,
    UpdateInvoiceCommand,
)
from dotmac.platform.billing.commands.payment_commands import (
    CancelPaymentCommand,
    RecordOfflinePaymentCommand,
)
from dotmac.platform.billing.core.enums import PaymentStatus


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    return AsyncMock()


@pytest.mark.asyncio
class TestUpdateInvoiceHandler:
    """Test handle_update_invoice method."""

    async def test_update_invoice_calls_service(self, mock_db_session):
        """Test that handler delegates to InvoiceService.update_invoice."""
        handler = InvoiceCommandHandler(db_session=mock_db_session)

        # Mock return value
        mock_result = MagicMock()
        handler.invoice_service.update_invoice = AsyncMock(return_value=mock_result)

        # Create and execute command
        due_date = datetime.now(UTC)
        command = UpdateInvoiceCommand(
            tenant_id="tenant-123",
            invoice_id="inv-123",
            due_date=due_date,
            notes="Updated notes",
            extra_data={"key": "value"},
        )

        await handler.handle_update_invoice(command)

        # Verify service was called correctly
        handler.invoice_service.update_invoice.assert_called_once_with(
            tenant_id="tenant-123",
            invoice_id="inv-123",
            due_date=due_date,
            notes="Updated notes",
            metadata={"key": "value"},
        )


@pytest.mark.asyncio
class TestSendInvoiceHandler:
    """Test handle_send_invoice method."""

    async def test_send_invoice_email_success(self, mock_db_session):
        """Test successful invoice email sending."""
        handler = InvoiceCommandHandler(db_session=mock_db_session)
        handler.invoice_service.send_invoice_email = AsyncMock(return_value=True)

        command = SendInvoiceCommand(
            tenant_id="tenant-123",
            invoice_id="inv-789",
            recipient_email="customer@example.com",
        )

        result = await handler.handle_send_invoice(command)

        handler.invoice_service.send_invoice_email.assert_called_once_with(
            tenant_id="tenant-123",
            invoice_id="inv-789",
            recipient_email="customer@example.com",
        )

        assert result["success"] is True

    async def test_send_invoice_email_failure(self, mock_db_session):
        """Test invoice email sending failure."""
        handler = InvoiceCommandHandler(db_session=mock_db_session)
        handler.invoice_service.send_invoice_email = AsyncMock(return_value=False)

        command = SendInvoiceCommand(
            tenant_id="tenant-123",
            invoice_id="inv-789",
        )

        result = await handler.handle_send_invoice(command)

        assert result["success"] is False


@pytest.mark.asyncio
class TestApplyPaymentToInvoiceHandler:
    """Test handle_apply_payment_to_invoice method."""

    async def test_apply_payment_to_invoice(self, mock_db_session):
        """Test applying payment to invoice."""
        handler = InvoiceCommandHandler(db_session=mock_db_session)

        mock_result = MagicMock()
        mock_result.status = "paid"
        handler.invoice_service.apply_payment_to_invoice = AsyncMock(return_value=mock_result)

        command = ApplyPaymentToInvoiceCommand(
            tenant_id="tenant-123",
            invoice_id="inv-123",
            payment_id="pay-456",
            amount=Decimal("500.00"),
        )

        result = await handler.handle_apply_payment_to_invoice(command)

        handler.invoice_service.apply_payment_to_invoice.assert_called_once_with(
            tenant_id="tenant-123",
            invoice_id="inv-123",
            payment_id="pay-456",
            amount=Decimal("500.00"),
        )

        assert result.status == "paid"


@pytest.mark.asyncio
class TestCancelPaymentHandler:
    """Test handle_cancel_payment method."""

    async def test_cancel_payment(self, mock_db_session):
        """Test cancelling a payment."""
        handler = PaymentCommandHandler(db_session=mock_db_session)

        mock_result = MagicMock()
        mock_result.status = PaymentStatus.CANCELLED
        handler.payment_service.cancel_payment = AsyncMock(return_value=mock_result)

        command = CancelPaymentCommand(
            tenant_id="tenant-123",
            payment_id="pay-123",
            cancellation_reason="Customer requested cancellation",
        )

        result = await handler.handle_cancel_payment(command)

        handler.payment_service.cancel_payment.assert_called_once_with(
            tenant_id="tenant-123",
            payment_id="pay-123",
            cancellation_reason="Customer requested cancellation",
        )

        assert result.status == PaymentStatus.CANCELLED

    async def test_cancel_payment_without_reason(self, mock_db_session):
        """Test cancelling payment without providing reason."""
        handler = PaymentCommandHandler(db_session=mock_db_session)

        mock_result = MagicMock()
        handler.payment_service.cancel_payment = AsyncMock(return_value=mock_result)

        command = CancelPaymentCommand(
            tenant_id="tenant-123",
            payment_id="pay-456",
        )

        await handler.handle_cancel_payment(command)

        handler.payment_service.cancel_payment.assert_called_once_with(
            tenant_id="tenant-123",
            payment_id="pay-456",
            cancellation_reason=None,
        )


@pytest.mark.asyncio
class TestRecordOfflinePaymentHandler:
    """Test handle_record_offline_payment method."""

    async def test_record_offline_payment_check(self, mock_db_session):
        """Test recording offline payment via check."""
        handler = PaymentCommandHandler(db_session=mock_db_session)

        mock_result = MagicMock()
        mock_result.status = PaymentStatus.SUCCEEDED
        mock_result.provider = "offline"
        handler.payment_service.record_offline_payment = AsyncMock(return_value=mock_result)

        command = RecordOfflinePaymentCommand(
            tenant_id="tenant-123",
            customer_id="cust-456",
            amount=Decimal("1500.00"),
            currency="USD",
            payment_method="check",
            invoice_id="inv-789",
            reference_number="CHK-2025-001",
            notes="Payment received via mail",
        )

        result = await handler.handle_record_offline_payment(command)

        handler.payment_service.record_offline_payment.assert_called_once_with(
            tenant_id="tenant-123",
            customer_id="cust-456",
            amount=Decimal("1500.00"),
            currency="USD",
            payment_method="check",
            invoice_id="inv-789",
            reference_number="CHK-2025-001",
            notes="Payment received via mail",
            payment_date=None,
        )

        assert result.status == PaymentStatus.SUCCEEDED
        assert result.provider == "offline"

    async def test_record_offline_payment_bank_transfer(self, mock_db_session):
        """Test recording offline payment via bank transfer."""
        handler = PaymentCommandHandler(db_session=mock_db_session)

        mock_result = MagicMock()
        handler.payment_service.record_offline_payment = AsyncMock(return_value=mock_result)

        payment_date = datetime.now(UTC)
        command = RecordOfflinePaymentCommand(
            tenant_id="tenant-123",
            customer_id="cust-789",
            amount=Decimal("5000.00"),
            currency="EUR",
            payment_method="bank_transfer",
            reference_number="WIRE-2025-42",
            payment_date=payment_date,
        )

        await handler.handle_record_offline_payment(command)

        handler.payment_service.record_offline_payment.assert_called_once_with(
            tenant_id="tenant-123",
            customer_id="cust-789",
            amount=Decimal("5000.00"),
            currency="EUR",
            payment_method="bank_transfer",
            invoice_id=None,
            reference_number="WIRE-2025-42",
            notes=None,
            payment_date=payment_date,
        )


@pytest.mark.asyncio
class TestCommandHandlerErrorScenarios:
    """Test error handling in command handlers."""

    async def test_update_invoice_service_error(self, mock_db_session):
        """Test handle_update_invoice when service raises error."""
        handler = InvoiceCommandHandler(db_session=mock_db_session)
        handler.invoice_service.update_invoice = AsyncMock(
            side_effect=Exception("Invoice not found")
        )

        command = UpdateInvoiceCommand(
            tenant_id="tenant-123",
            invoice_id="nonexistent",
            notes="Update",
        )

        with pytest.raises(Exception, match="Invoice not found"):
            await handler.handle_update_invoice(command)

    async def test_cancel_payment_invalid_status(self, mock_db_session):
        """Test cancelling payment that's not in cancellable status."""
        from dotmac.platform.billing.core.exceptions import PaymentError

        handler = PaymentCommandHandler(db_session=mock_db_session)
        handler.payment_service.cancel_payment = AsyncMock(
            side_effect=PaymentError("Cannot cancel succeeded payment")
        )

        command = CancelPaymentCommand(
            tenant_id="tenant-123",
            payment_id="pay-succeeded",
        )

        with pytest.raises(PaymentError, match="Cannot cancel succeeded payment"):
            await handler.handle_cancel_payment(command)
