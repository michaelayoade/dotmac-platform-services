"""Tests for the TODO fixes in billing module."""

import pytest
from unittest.mock import AsyncMock, Mock, MagicMock, patch
from datetime import datetime, timezone
from decimal import Decimal

from dotmac.platform.billing.invoicing.money_service import MoneyInvoiceService
from dotmac.platform.billing.integration import BillingIntegrationService, BillingInvoiceRequest, InvoiceItem
from dotmac.platform.billing.money_models import MoneyInvoice, MoneyInvoiceLineItem
from dotmac.platform.billing.core.enums import InvoiceStatus


class TestMoneyServiceFix:
    """Test that the money service properly saves discounts to database."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        return db

    @pytest.fixture
    def money_service(self, mock_db):
        """Create money invoice service."""
        return MoneyInvoiceService(mock_db)

    @pytest.mark.asyncio
    async def test_apply_discount_saves_to_database(self, money_service, mock_db):
        """Test that applying discount saves to database."""
        from dotmac.platform.billing import money_utils

        # Setup mock invoice entity
        mock_invoice_entity = Mock()
        mock_invoice_entity.discount_amount = 0
        mock_invoice_entity.total_amount = 10000
        mock_invoice_entity.internal_notes = None

        # Setup mock invoice - simplified with direct mocking
        mock_invoice = Mock(spec=MoneyInvoice)
        mock_invoice.invoice_id = "inv-123"
        mock_invoice.customer_id = "cust-456"
        mock_invoice.currency = "USD"
        mock_invoice.subtotal = Mock()
        mock_invoice.total_amount = Mock()
        mock_invoice.tax_amount = Mock()
        mock_invoice.discount_amount = None
        mock_invoice.internal_notes = None

        # Mock money operations
        mock_discount_amount = Mock()
        mock_new_total = Mock()

        # Mock the methods
        with patch.object(money_service, 'get_money_invoice', return_value=mock_invoice):
            with patch.object(money_service, '_get_invoice_entity', return_value=mock_invoice_entity):
                with patch.object(money_utils.money_handler, 'multiply_money', return_value=mock_discount_amount):
                    with patch.object(money_utils.money_handler, 'add_money', return_value=mock_new_total):
                        with patch.object(money_utils.money_handler, 'create_money', return_value=Mock()):
                            with patch.object(money_service.adapter, 'money_to_legacy_invoice') as mock_adapter:
                                mock_legacy = Mock()
                                mock_legacy.discount_amount = 2000  # 20% discount in cents
                                mock_legacy.total_amount = 8000
                                mock_legacy.internal_notes = "Discount applied (20%): Test discount"
                                mock_adapter.return_value = mock_legacy

                                # Apply discount
                                result = await money_service.apply_percentage_discount(
                                    tenant_id="tenant-123",
                                    invoice_id="inv-123",
                                    discount_percentage=20.0,
                                    reason="Test discount"
                                )

                                # Verify database update
                                assert mock_invoice_entity.discount_amount == 2000
                                assert mock_invoice_entity.total_amount == 8000
                                assert "Discount applied" in mock_invoice_entity.internal_notes
                                mock_db.commit.assert_called_once()
                                mock_db.refresh.assert_called_once()


class TestBillingIntegrationFix:
    """Test that billing integration properly creates invoices."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return AsyncMock()

    @pytest.fixture
    def billing_service(self, mock_db):
        """Create billing integration service."""
        with patch('dotmac.platform.billing.catalog.service.ProductService'):
            with patch('dotmac.platform.billing.pricing.service.PricingEngine'):
                with patch('dotmac.platform.billing.subscriptions.service.SubscriptionService'):
                    service = BillingIntegrationService(mock_db)
                    # Mock the invoice service methods we need
                    service.invoice_service = Mock()
                    return service

    @pytest.mark.asyncio
    async def test_create_invoice_uses_real_service(self, billing_service):
        """Test that _create_invoice uses the actual invoice service."""
        # Create mock invoice
        mock_invoice = Mock()
        mock_invoice.invoice_id = "inv-789"
        mock_invoice.status = InvoiceStatus.DRAFT
        mock_invoice.customer_id = "cust-123"

        # Mock invoice service methods
        billing_service.invoice_service.create_invoice = AsyncMock(return_value=mock_invoice)
        billing_service.invoice_service.finalize_invoice = AsyncMock(return_value=mock_invoice)

        # Create invoice request
        invoice_request = BillingInvoiceRequest(
            customer_id="cust-123",
            subscription_id="sub-456",
            billing_period_start=datetime.now(timezone.utc),
            billing_period_end=datetime.now(timezone.utc),
            items=[
                InvoiceItem(
                    product_id="prod-1",
                    description="Test Product",
                    quantity=1,
                    unit_price=Decimal("100.00"),
                    total_amount=Decimal("100.00"),
                    final_amount=Decimal("100.00"),
                )
            ],
            subtotal=Decimal("100.00"),
            total_discount=Decimal("0.00"),
            total_amount=Decimal("100.00"),
        )

        # Create invoice
        result = await billing_service._create_invoice(invoice_request, "tenant-123")

        # Verify
        assert result == "inv-789"
        billing_service.invoice_service.create_invoice.assert_called_once()
        billing_service.invoice_service.finalize_invoice.assert_called_once()

        # Check the invoice was created with correct parameters
        create_call = billing_service.invoice_service.create_invoice.call_args
        assert create_call.kwargs["tenant_id"] == "tenant-123"
        assert create_call.kwargs["customer_id"] == "cust-123"
        assert len(create_call.kwargs["line_items"]) == 1
        assert create_call.kwargs["line_items"][0]["unit_price"] == 10000  # Converted to cents

    @pytest.mark.asyncio
    async def test_create_invoice_handles_errors(self, billing_service):
        """Test that _create_invoice handles errors gracefully."""
        # Mock invoice service to raise error
        billing_service.invoice_service.create_invoice = AsyncMock(
            side_effect=Exception("Database error")
        )

        # Create invoice request
        invoice_request = BillingInvoiceRequest(
            customer_id="cust-123",
            subscription_id="sub-456",
            billing_period_start=datetime.now(timezone.utc),
            billing_period_end=datetime.now(timezone.utc),
            items=[],
            subtotal=Decimal("0"),
            total_discount=Decimal("0"),
            total_amount=Decimal("0"),
        )

        # Create invoice should return None on error
        result = await billing_service._create_invoice(invoice_request, "tenant-123")

        assert result is None