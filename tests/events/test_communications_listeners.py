"""Tests for communications event listeners."""

from unittest.mock import AsyncMock, patch

import pytest

from dotmac.platform.billing.events import (
    emit_invoice_created,
    emit_invoice_paid,
    emit_payment_failed,
)
from dotmac.platform.events import get_event_bus, reset_event_bus


class TestCommunicationsEventListeners:
    """Test communications module event listeners."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup and teardown for each test."""
        reset_event_bus()
        yield
        reset_event_bus()

    @pytest.mark.asyncio
    @patch("dotmac.platform.communications.event_listeners.EmailService")
    async def test_invoice_created_sends_email(self, mock_email_service_class):
        """Test that invoice created event triggers email."""
        # Setup mock
        mock_email_service = AsyncMock()
        mock_email_service_class.return_value = mock_email_service

        # Import to register listeners

        event_bus = get_event_bus(redis_client=None, enable_persistence=False)

        # Emit event
        await emit_invoice_created(
            invoice_id="INV-001",
            customer_id="CUST-001",
            amount=150.00,
            currency="USD",
            customer_email="customer@example.com",
            event_bus=event_bus,
        )

        import asyncio

        await asyncio.sleep(0.1)

        # Verify email was sent
        mock_email_service.send_email.assert_called_once()
        call_kwargs = mock_email_service.send_email.call_args.kwargs

        assert call_kwargs["to_email"] == "customer@example.com"
        assert "Invoice" in call_kwargs["subject"]
        assert "INV-001" in call_kwargs["body"]

    @pytest.mark.asyncio
    @patch("dotmac.platform.communications.event_listeners.EmailService")
    async def test_invoice_paid_sends_confirmation(self, mock_email_service_class):
        """Test that invoice paid event sends confirmation email."""
        mock_email_service = AsyncMock()
        mock_email_service_class.return_value = mock_email_service

        event_bus = get_event_bus(redis_client=None, enable_persistence=False)

        await emit_invoice_paid(
            invoice_id="INV-001",
            customer_id="CUST-001",
            amount=150.00,
            payment_id="PAY-001",
            customer_email="customer@example.com",
            event_bus=event_bus,
        )

        import asyncio

        await asyncio.sleep(0.1)

        mock_email_service.send_email.assert_called_once()
        call_kwargs = mock_email_service.send_email.call_args.kwargs

        assert call_kwargs["to_email"] == "customer@example.com"
        assert "Payment" in call_kwargs["subject"]
        assert "PAY-001" in call_kwargs["body"]

    @pytest.mark.asyncio
    @patch("dotmac.platform.communications.event_listeners.EmailService")
    async def test_payment_failed_sends_notification(self, mock_email_service_class):
        """Test that payment failed event sends notification."""
        mock_email_service = AsyncMock()
        mock_email_service_class.return_value = mock_email_service

        event_bus = get_event_bus(redis_client=None, enable_persistence=False)

        await emit_payment_failed(
            payment_id="PAY-001",
            invoice_id="INV-001",
            customer_id="CUST-001",
            amount=150.00,
            error_message="Card declined",
            customer_email="customer@example.com",
            event_bus=event_bus,
        )

        import asyncio

        await asyncio.sleep(0.1)

        mock_email_service.send_email.assert_called_once()
        call_kwargs = mock_email_service.send_email.call_args.kwargs

        assert call_kwargs["to_email"] == "customer@example.com"
        assert "Failed" in call_kwargs["subject"]
        assert "Card declined" in call_kwargs["body"]

    @pytest.mark.asyncio
    @patch("dotmac.platform.communications.event_listeners.EmailService")
    async def test_multiple_event_types(self, mock_email_service_class):
        """Test handling multiple different event types."""
        mock_email_service = AsyncMock()
        mock_email_service_class.return_value = mock_email_service

        event_bus = get_event_bus(redis_client=None, enable_persistence=False)

        # Emit different events
        await emit_invoice_created(
            invoice_id="INV-001",
            customer_id="CUST-001",
            amount=100.00,
            currency="USD",
            customer_email="customer@example.com",
            event_bus=event_bus,
        )

        await emit_invoice_paid(
            invoice_id="INV-001",
            customer_id="CUST-001",
            amount=100.00,
            payment_id="PAY-001",
            customer_email="customer@example.com",
            event_bus=event_bus,
        )

        import asyncio

        await asyncio.sleep(0.2)

        # Should have called send_email twice
        assert mock_email_service.send_email.call_count == 2

    @pytest.mark.asyncio
    @patch("dotmac.platform.communications.event_listeners.EmailService")
    async def test_listener_error_handling(self, mock_email_service_class):
        """Test that listener errors don't crash the system."""
        # Make email service raise an exception
        mock_email_service = AsyncMock()
        mock_email_service.send_email.side_effect = Exception("SMTP error")
        mock_email_service_class.return_value = mock_email_service

        event_bus = get_event_bus(redis_client=None, enable_persistence=False)

        # Emit event - should not raise exception
        await emit_invoice_created(
            invoice_id="INV-001",
            customer_id="CUST-001",
            amount=100.00,
            currency="USD",
            customer_email="customer@example.com",
            event_bus=event_bus,
        )

        import asyncio

        await asyncio.sleep(0.1)

        # Email service was called but failed
        mock_email_service.send_email.assert_called_once()

        # Event should be marked as failed
        events = await event_bus.get_events(event_type="invoice.created")
        assert len(events) > 0
        # Error should be logged but system continues


class TestEventListenerIntegration:
    """Integration tests for event listeners."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup and teardown."""
        reset_event_bus()
        yield
        reset_event_bus()

    @pytest.mark.asyncio
    @patch("dotmac.platform.communications.event_listeners.EmailService")
    async def test_end_to_end_invoice_flow(self, mock_email_service_class):
        """Test complete invoice flow with communications."""
        mock_email_service = AsyncMock()
        mock_email_service_class.return_value = mock_email_service

        event_bus = get_event_bus(redis_client=None, enable_persistence=False)

        # 1. Invoice created
        await emit_invoice_created(
            invoice_id="INV-001",
            customer_id="CUST-001",
            amount=250.00,
            currency="USD",
            customer_email="customer@example.com",
            event_bus=event_bus,
        )

        import asyncio

        await asyncio.sleep(0.1)

        # 2. Invoice paid
        await emit_invoice_paid(
            invoice_id="INV-001",
            customer_id="CUST-001",
            amount=250.00,
            payment_id="PAY-001",
            customer_email="customer@example.com",
            event_bus=event_bus,
        )

        await asyncio.sleep(0.1)

        # Should have sent 2 emails
        assert mock_email_service.send_email.call_count == 2

        # Verify both emails were for correct recipient
        calls = mock_email_service.send_email.call_args_list
        assert all(call.kwargs["to_email"] == "customer@example.com" for call in calls)
