"""
Test invoice notification integration with communications service
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

from dotmac.platform.billing.core.enums import InvoiceStatus
from dotmac.platform.billing.invoicing.service import InvoiceService
from dotmac.platform.billing.settings.models import (
    BillingSettings,
    CompanyInfo,
    InvoiceSettings,
    NotificationSettings,
    PaymentSettings,
    TaxSettings
)


@pytest.fixture
def mock_invoice_entity():
    """Create a mock invoice entity for testing"""
    invoice = MagicMock()
    invoice.id = uuid4()
    invoice.tenant_id = "test-tenant"
    invoice.invoice_number = "INV-2024-001"
    invoice.billing_email = "customer@example.com"
    invoice.currency = "USD"
    invoice.total_amount = 1250.00
    invoice.issue_date = datetime.now(timezone.utc)
    invoice.due_date = datetime.now(timezone.utc) + timedelta(days=30)
    invoice.notes = "Thank you for your business!"
    invoice.created_by = "user-123"
    invoice.status = InvoiceStatus.DRAFT
    return invoice


class TestInvoiceNotificationIntegration:
    """Test invoice notification functionality"""

    @pytest.mark.asyncio
    @patch('dotmac.platform.audit.log_api_activity')
    @patch('dotmac.platform.billing.settings.service.BillingSettingsService')
    @patch('dotmac.platform.communications.email_service.EmailService')
    async def test_send_invoice_notification_success(
        self,
        mock_email_service_class,
        mock_settings_service_class,
        mock_log_activity,
        mock_invoice_entity
    ):
        """Test successful invoice notification sending"""
        # Setup billing settings with both settings enabled
        mock_settings = BillingSettings(
            tenant_id="test-tenant",
            company_info=CompanyInfo(
                name="Test Company",
                address_line1="123 Test St",
                city="Test City",
                postal_code="12345",
                country="US"
            ),
            invoice_settings=InvoiceSettings(
                send_invoice_emails=True,
                send_payment_reminders=True
            ),
            notification_settings=NotificationSettings(
                send_invoice_notifications=True
            ),
            payment_settings=PaymentSettings(),
            tax_settings=TaxSettings()
        )

        mock_settings_service = AsyncMock()
        mock_settings_service.get_settings = AsyncMock(return_value=mock_settings)
        mock_settings_service_class.return_value = mock_settings_service

        # Setup mocks
        mock_email_service = AsyncMock()
        mock_email_service.send_email = AsyncMock(return_value={
            "id": "msg-123",
            "status": "sent"
        })
        mock_email_service_class.return_value = mock_email_service
        mock_log_activity.return_value = None

        # Create service and send notification
        db_session = MagicMock()
        service = InvoiceService(db_session)
        await service._send_invoice_notification(mock_invoice_entity)

        # Verify email was sent
        mock_email_service.send_email.assert_called_once()

        # Check email content
        email_call = mock_email_service.send_email.call_args[0][0]
        assert email_call.to == ["customer@example.com"]
        assert "INV-2024-001" in email_call.subject
        assert "USD 1250.00" in email_call.subject
        assert "INV-2024-001" in email_call.html_body
        assert "Thank you for your business!" in email_call.html_body
        assert "INV-2024-001" in email_call.text_body

        # Verify audit log was created
        mock_log_activity.assert_called_once()
        log_call = mock_log_activity.call_args[1]
        assert log_call["action"] == "invoice_notification_sent"
        assert log_call["resource_type"] == "invoice"
        assert log_call["request_data"]["email"] == "customer@example.com"

    @pytest.mark.asyncio
    @patch('structlog.get_logger')
    @patch('dotmac.platform.communications.email_service.EmailService')
    async def test_send_invoice_notification_email_failure(
        self,
        mock_email_service_class,
        mock_get_logger,
        mock_invoice_entity
    ):
        """Test invoice notification handles email service failures gracefully"""
        # Setup mocks
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        mock_email_service = AsyncMock()
        mock_email_service.send_email = AsyncMock(
            side_effect=Exception("SMTP connection failed")
        )
        mock_email_service_class.return_value = mock_email_service

        # Create service and send notification
        db_session = MagicMock()
        service = InvoiceService(db_session)

        # Should not raise exception even if email fails
        await service._send_invoice_notification(mock_invoice_entity)

        # Verify error was logged
        mock_logger.error.assert_called_once()
        error_call = mock_logger.error.call_args[0]
        assert "Failed to send invoice notification" in error_call[0]
        error_kwargs = mock_logger.error.call_args[1]
        assert error_kwargs["invoice_number"] == "INV-2024-001"
        assert error_kwargs["email"] == "customer@example.com"
        assert "SMTP connection failed" in error_kwargs["error"]

    @pytest.mark.asyncio
    @patch('dotmac.platform.billing.settings.service.BillingSettingsService')
    @patch('dotmac.platform.communications.email_service.EmailService')
    async def test_send_invoice_notification_without_notes(
        self,
        mock_email_service_class,
        mock_settings_service_class,
        mock_invoice_entity
    ):
        """Test invoice notification without notes field"""
        # Remove notes from invoice
        mock_invoice_entity.notes = None

        # Setup billing settings with both settings enabled
        mock_settings = BillingSettings(
            tenant_id="test-tenant",
            company_info=CompanyInfo(
                name="Test Company",
                address_line1="123 Test St",
                city="Test City",
                postal_code="12345",
                country="US"
            ),
            invoice_settings=InvoiceSettings(
                send_invoice_emails=True,
                send_payment_reminders=True
            ),
            notification_settings=NotificationSettings(
                send_invoice_notifications=True
            ),
            payment_settings=PaymentSettings(),
            tax_settings=TaxSettings()
        )

        mock_settings_service = AsyncMock()
        mock_settings_service.get_settings = AsyncMock(return_value=mock_settings)
        mock_settings_service_class.return_value = mock_settings_service

        # Setup mocks
        mock_email_service = AsyncMock()
        mock_email_service.send_email = AsyncMock(return_value={
            "id": "msg-124",
            "status": "sent"
        })
        mock_email_service_class.return_value = mock_email_service

        # Create service and send notification
        db_session = MagicMock()
        service = InvoiceService(db_session)
        await service._send_invoice_notification(mock_invoice_entity)

        # Verify email was sent
        mock_email_service.send_email.assert_called_once()

        # Check that notes section is not included
        email_call = mock_email_service.send_email.call_args[0][0]
        assert "Notes:" not in email_call.text_body
        assert "<strong>Notes:</strong>" not in email_call.html_body

    @pytest.mark.asyncio
    async def test_finalize_invoice_sends_notification(self):
        """Test that finalizing an invoice sends a notification"""
        from dotmac.platform.billing.core.entities import InvoiceEntity
        from dotmac.platform.billing.core.enums import PaymentStatus

        with patch.object(InvoiceService, '_send_invoice_notification') as mock_send:
            mock_send.return_value = None

            # Create a proper invoice entity instance
            invoice_id = uuid4()
            invoice_entity = InvoiceEntity(
                tenant_id="test-tenant",
                invoice_id=str(invoice_id),
                idempotency_key=str(uuid4()),
                created_by="user-123",
                customer_id="customer-123",
                billing_email="customer@example.com",
                billing_address={},
                invoice_number="INV-2024-002",
                currency="USD",
                subtotal=1000.00,
                tax_amount=100.00,
                discount_amount=0,
                total_amount=1100.00,
                payment_status=PaymentStatus.PENDING,
                status=InvoiceStatus.DRAFT,
                issue_date=datetime.now(timezone.utc),
                due_date=datetime.now(timezone.utc) + timedelta(days=30),
                items=[],
                taxes=[],
                discounts=[],
                payment_terms="net_30",
                notes="",
                extra_data={}
            )
            invoice_entity.id = invoice_id  # Set id after creation

            # Mock database operations
            db_session = AsyncMock()
            db_session.commit = AsyncMock()
            db_session.refresh = AsyncMock()

            # Mock the _get_invoice_entity method
            with patch.object(
                InvoiceService,
                '_get_invoice_entity',
                return_value=invoice_entity
            ):
                # Create service and finalize invoice
                service = InvoiceService(db_session)
                service.metrics = MagicMock()
                service.metrics.record_invoice_finalized = MagicMock()

                result = await service.finalize_invoice("test-tenant", str(invoice_id))

                # Verify notification was sent
                mock_send.assert_called_once_with(invoice_entity)

                # Verify status was updated
                assert invoice_entity.status == InvoiceStatus.OPEN
                assert result.status == InvoiceStatus.OPEN

    @pytest.mark.asyncio
    @patch('dotmac.platform.billing.settings.service.BillingSettingsService')
    @patch('dotmac.platform.communications.email_service.EmailService')
    async def test_invoice_notification_respects_invoice_email_setting(
        self,
        mock_email_service_class,
        mock_settings_service_class,
        mock_invoice_entity
    ):
        """Test that invoice notifications respect send_invoice_emails setting"""
        # Setup billing settings with notifications disabled
        mock_settings = BillingSettings(
            tenant_id="test-tenant",
            company_info=CompanyInfo(
                name="Test Company",
                address_line1="123 Test St",
                city="Test City",
                postal_code="12345",
                country="US"
            ),
            invoice_settings=InvoiceSettings(
                send_invoice_emails=False,  # Disabled
                send_payment_reminders=True
            ),
            notification_settings=NotificationSettings(
                send_invoice_notifications=True  # Enabled
            ),
            payment_settings=PaymentSettings(),
            tax_settings=TaxSettings()
        )

        mock_settings_service = AsyncMock()
        mock_settings_service.get_settings = AsyncMock(return_value=mock_settings)
        mock_settings_service_class.return_value = mock_settings_service

        mock_email_service = AsyncMock()
        mock_email_service.send_email = AsyncMock()
        mock_email_service_class.return_value = mock_email_service

        # Create service and try to send notification
        db_session = MagicMock()
        service = InvoiceService(db_session)
        await service._send_invoice_notification(mock_invoice_entity)

        # Verify settings were checked
        mock_settings_service.get_settings.assert_called_once_with("test-tenant")

        # Verify email was NOT sent because send_invoice_emails is False
        mock_email_service.send_email.assert_not_called()

    @pytest.mark.asyncio
    @patch('dotmac.platform.billing.settings.service.BillingSettingsService')
    @patch('dotmac.platform.communications.email_service.EmailService')
    async def test_invoice_notification_respects_notification_setting(
        self,
        mock_email_service_class,
        mock_settings_service_class,
        mock_invoice_entity
    ):
        """Test that invoice notifications respect send_invoice_notifications setting"""
        # Setup billing settings with invoice emails enabled but notifications disabled
        mock_settings = BillingSettings(
            tenant_id="test-tenant",
            company_info=CompanyInfo(
                name="Test Company",
                address_line1="123 Test St",
                city="Test City",
                postal_code="12345",
                country="US"
            ),
            invoice_settings=InvoiceSettings(
                send_invoice_emails=True,  # Enabled
                send_payment_reminders=True
            ),
            notification_settings=NotificationSettings(
                send_invoice_notifications=False  # Disabled
            ),
            payment_settings=PaymentSettings(),
            tax_settings=TaxSettings()
        )

        mock_settings_service = AsyncMock()
        mock_settings_service.get_settings = AsyncMock(return_value=mock_settings)
        mock_settings_service_class.return_value = mock_settings_service

        mock_email_service = AsyncMock()
        mock_email_service.send_email = AsyncMock()
        mock_email_service_class.return_value = mock_email_service

        # Create service and try to send notification
        db_session = MagicMock()
        service = InvoiceService(db_session)
        await service._send_invoice_notification(mock_invoice_entity)

        # Verify settings were checked
        mock_settings_service.get_settings.assert_called_once_with("test-tenant")

        # Verify email was NOT sent because send_invoice_notifications is False
        mock_email_service.send_email.assert_not_called()

    @pytest.mark.asyncio
    @patch('dotmac.platform.audit.log_api_activity')
    @patch('dotmac.platform.billing.settings.service.BillingSettingsService')
    @patch('dotmac.platform.communications.email_service.EmailService')
    async def test_invoice_notification_sends_when_both_settings_enabled(
        self,
        mock_email_service_class,
        mock_settings_service_class,
        mock_log_activity,
        mock_invoice_entity
    ):
        """Test that invoice notifications are sent when both settings are enabled"""
        # Setup billing settings with both settings enabled
        mock_settings = BillingSettings(
            tenant_id="test-tenant",
            invoice_settings=InvoiceSettings(
                send_invoice_emails=True,  # Enabled
                send_payment_reminders=True
            ),
            notification_settings=NotificationSettings(
                send_invoice_notifications=True  # Enabled
            ),
            payment_settings=PaymentSettings(),
            tax_settings=TaxSettings()
        )

        mock_settings_service = AsyncMock()
        mock_settings_service.get_settings = AsyncMock(return_value=mock_settings)
        mock_settings_service_class.return_value = mock_settings_service

        mock_email_service = AsyncMock()
        mock_email_service.send_email = AsyncMock(return_value={
            "id": "msg-125",
            "status": "sent"
        })
        mock_email_service_class.return_value = mock_email_service
        mock_log_activity.return_value = None

        # Create service and send notification
        db_session = MagicMock()
        service = InvoiceService(db_session)
        await service._send_invoice_notification(mock_invoice_entity)

        # Verify settings were checked
        mock_settings_service.get_settings.assert_called_once_with("test-tenant")

        # Verify email WAS sent because both settings are True
        mock_email_service.send_email.assert_called_once()

        # Verify audit log was created
        mock_log_activity.assert_called_once()