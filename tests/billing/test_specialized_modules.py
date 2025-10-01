"""
Tests for specialized billing modules (tax, reports, receipts, webhooks).

Achieves high coverage for previously untested modules.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Dict, List, Any
import json


class TestTaxCalculator:
    """Complete tests for tax calculation module."""

    @pytest.mark.asyncio
    async def test_calculate_us_sales_tax(self):
        """Test US sales tax calculation."""
        from dotmac.platform.billing.tax.calculator import TaxCalculator

        calculator = TaxCalculator()

        # Test different US states
        test_cases = [
            {"state": "CA", "amount": Decimal("100.00"), "rate": Decimal("0.0725")},  # California
            {"state": "TX", "amount": Decimal("100.00"), "rate": Decimal("0.0625")},  # Texas
            {"state": "NY", "amount": Decimal("100.00"), "rate": Decimal("0.08")},     # New York
            {"state": "FL", "amount": Decimal("100.00"), "rate": Decimal("0.06")},     # Florida
            {"state": "OR", "amount": Decimal("100.00"), "rate": Decimal("0.00")},     # Oregon (no sales tax)
        ]

        for case in test_cases:
            result = calculator.calculate_sales_tax(
                amount=case["amount"],
                country="US",
                state=case["state"]
            )
            expected_tax = case["amount"] * case["rate"]
            assert abs(result - expected_tax) < Decimal("0.01")

    @pytest.mark.asyncio
    async def test_calculate_eu_vat(self):
        """Test EU VAT calculation."""
        from dotmac.platform.billing.tax.calculator import TaxCalculator

        calculator = TaxCalculator()

        # Test different EU countries
        test_cases = [
            {"country": "DE", "amount": Decimal("100.00"), "rate": Decimal("0.19")},   # Germany
            {"country": "FR", "amount": Decimal("100.00"), "rate": Decimal("0.20")},   # France
            {"country": "GB", "amount": Decimal("100.00"), "rate": Decimal("0.20")},   # UK
            {"country": "IE", "amount": Decimal("100.00"), "rate": Decimal("0.23")},   # Ireland
        ]

        for case in test_cases:
            result = calculator.calculate_vat(
                amount=case["amount"],
                country=case["country"]
            )
            expected_vat = case["amount"] * case["rate"]
            assert abs(result - expected_vat) < Decimal("0.01")

    @pytest.mark.asyncio
    async def test_calculate_digital_services_tax(self):
        """Test digital services tax calculation."""
        from dotmac.platform.billing.tax.calculator import TaxCalculator

        calculator = TaxCalculator()

        # Countries with digital services tax
        test_cases = [
            {"country": "FR", "amount": Decimal("1000.00"), "rate": Decimal("0.03")},  # France 3%
            {"country": "IT", "amount": Decimal("1000.00"), "rate": Decimal("0.03")},  # Italy 3%
            {"country": "ES", "amount": Decimal("1000.00"), "rate": Decimal("0.03")},  # Spain 3%
        ]

        for case in test_cases:
            result = calculator.calculate_digital_services_tax(
                amount=case["amount"],
                country=case["country"]
            )
            expected_tax = case["amount"] * case["rate"]
            assert abs(result - expected_tax) < Decimal("0.01")

    @pytest.mark.asyncio
    async def test_tax_exemption_handling(self):
        """Test tax exemption handling."""
        from dotmac.platform.billing.tax.calculator import TaxCalculator

        calculator = TaxCalculator()

        # Tax-exempt customer
        result = calculator.calculate_tax(
            amount=Decimal("100.00"),
            country="US",
            state="CA",
            tax_exempt=True
        )

        assert result == Decimal("0.00")

    @pytest.mark.asyncio
    async def test_compound_tax_calculation(self):
        """Test compound tax calculation (multiple tax types)."""
        from dotmac.platform.billing.tax.calculator import TaxCalculator

        calculator = TaxCalculator()

        # Quebec, Canada has both federal and provincial tax
        result = calculator.calculate_compound_tax(
            amount=Decimal("100.00"),
            country="CA",
            province="QC"
        )

        # GST (5%) + QST (9.975%) = ~14.975%
        expected_tax = Decimal("14.98")
        assert abs(result - expected_tax) < Decimal("0.10")


class TestTaxService:
    """Tests for tax service integration."""

    @pytest.mark.asyncio
    async def test_apply_tax_to_invoice(self, mock_db_session):
        """Test applying tax to invoice."""
        from dotmac.platform.billing.tax.service import TaxService

        service = TaxService()

        invoice_data = {
            "subtotal": Decimal("100.00"),
            "customer_country": "US",
            "customer_state": "CA",
            "tax_exempt": False
        }

        result = await service.apply_tax_to_invoice(invoice_data)

        assert "tax_amount" in result
        assert "total" in result
        assert result["total"] > invoice_data["subtotal"]

    @pytest.mark.asyncio
    async def test_validate_tax_id(self):
        """Test tax ID validation."""
        from dotmac.platform.billing.tax.service import TaxService

        service = TaxService()

        # Valid VAT IDs
        valid_ids = [
            {"country": "DE", "tax_id": "DE123456789"},
            {"country": "FR", "tax_id": "FR12345678901"},
            {"country": "GB", "tax_id": "GB123456789"},
        ]

        for case in valid_ids:
            result = await service.validate_tax_id(case["tax_id"], case["country"])
            assert result["valid"] is True

        # Invalid VAT ID
        result = await service.validate_tax_id("INVALID123", "DE")
        assert result["valid"] is False


class TestReportsGenerator:
    """Tests for report generation."""

    @pytest.mark.asyncio
    async def test_generate_monthly_revenue_report(self, mock_db_session):
        """Test monthly revenue report generation."""
        from dotmac.platform.billing.reports.generators import RevenueReportGenerator

        generator = RevenueReportGenerator()

        # Mock revenue data
        mock_data = [
            {"date": "2024-01-01", "revenue": Decimal("1000.00")},
            {"date": "2024-01-15", "revenue": Decimal("1500.00")},
            {"date": "2024-01-31", "revenue": Decimal("2000.00")},
        ]

        mock_result = MagicMock()
        mock_result.all.return_value = mock_data
        mock_db_session.execute.return_value = mock_result

        with patch('dotmac.platform.billing.reports.generators.get_async_session', return_value=mock_db_session):
            report = await generator.generate_monthly_report(
                year=2024,
                month=1,
                tenant_id="tenant_123"
            )

        assert report["total_revenue"] == Decimal("4500.00")
        assert report["transaction_count"] == 3
        assert report["average_transaction"] == Decimal("1500.00")

    @pytest.mark.asyncio
    async def test_generate_subscription_metrics_report(self, mock_db_session):
        """Test subscription metrics report."""
        from dotmac.platform.billing.reports.generators import SubscriptionMetricsGenerator

        generator = SubscriptionMetricsGenerator()

        # Mock subscription data
        mock_data = {
            "total_subscriptions": 100,
            "new_subscriptions": 20,
            "canceled_subscriptions": 5,
            "mrr": Decimal("10000.00"),
            "arr": Decimal("120000.00"),
            "churn_rate": Decimal("5.0")
        }

        mock_result = MagicMock()
        mock_result.one.return_value = mock_data
        mock_db_session.execute.return_value = mock_result

        with patch('dotmac.platform.billing.reports.generators.get_async_session', return_value=mock_db_session):
            report = await generator.generate_metrics_report(
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 31),
                tenant_id="tenant_123"
            )

        assert report["mrr"] == Decimal("10000.00")
        assert report["churn_rate"] == Decimal("5.0")

    @pytest.mark.asyncio
    async def test_generate_customer_lifetime_value_report(self, mock_db_session):
        """Test customer lifetime value report."""
        from dotmac.platform.billing.reports.generators import CLVReportGenerator

        generator = CLVReportGenerator()

        # Mock CLV data
        mock_customers = [
            {"customer_id": "cust_1", "total_revenue": Decimal("5000.00"), "months_active": 12},
            {"customer_id": "cust_2", "total_revenue": Decimal("3000.00"), "months_active": 6},
            {"customer_id": "cust_3", "total_revenue": Decimal("10000.00"), "months_active": 24},
        ]

        mock_result = MagicMock()
        mock_result.all.return_value = mock_customers
        mock_db_session.execute.return_value = mock_result

        with patch('dotmac.platform.billing.reports.generators.get_async_session', return_value=mock_db_session):
            report = await generator.generate_clv_report(tenant_id="tenant_123")

        assert len(report["customers"]) == 3
        assert report["average_clv"] > Decimal("0")

    @pytest.mark.asyncio
    async def test_generate_product_performance_report(self, mock_db_session):
        """Test product performance report."""
        from dotmac.platform.billing.reports.generators import ProductPerformanceGenerator

        generator = ProductPerformanceGenerator()

        # Mock product performance data
        mock_products = [
            {"product_id": "prod_1", "name": "Product A", "sales": 100, "revenue": Decimal("10000.00")},
            {"product_id": "prod_2", "name": "Product B", "sales": 50, "revenue": Decimal("7500.00")},
        ]

        mock_result = MagicMock()
        mock_result.all.return_value = mock_products
        mock_db_session.execute.return_value = mock_result

        with patch('dotmac.platform.billing.reports.generators.get_async_session', return_value=mock_db_session):
            report = await generator.generate_performance_report(
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 31),
                tenant_id="tenant_123"
            )

        assert len(report["products"]) == 2
        assert report["top_product"]["product_id"] == "prod_1"


class TestReceiptGenerator:
    """Tests for receipt generation."""

    @pytest.mark.asyncio
    async def test_generate_payment_receipt(self):
        """Test payment receipt generation."""
        from dotmac.platform.billing.receipts.generators import ReceiptGenerator

        generator = ReceiptGenerator()

        payment_data = {
            "payment_id": "pay_123",
            "amount": Decimal("99.99"),
            "currency": "USD",
            "customer_name": "John Doe",
            "customer_email": "john@example.com",
            "items": [
                {"description": "Subscription - Pro Plan", "amount": Decimal("99.99")}
            ],
            "payment_date": datetime.now(timezone.utc)
        }

        receipt = await generator.generate_payment_receipt(payment_data)

        assert receipt["receipt_number"] is not None
        assert receipt["amount"] == Decimal("99.99")
        assert receipt["customer_email"] == "john@example.com"
        assert "pdf_url" in receipt or "html_content" in receipt

    @pytest.mark.asyncio
    async def test_generate_invoice_receipt(self):
        """Test invoice receipt generation."""
        from dotmac.platform.billing.receipts.generators import ReceiptGenerator

        generator = ReceiptGenerator()

        invoice_data = {
            "invoice_id": "inv_123",
            "invoice_number": "INV-2024-001",
            "subtotal": Decimal("100.00"),
            "tax_amount": Decimal("10.00"),
            "total": Decimal("110.00"),
            "currency": "USD",
            "customer_details": {
                "name": "Acme Corp",
                "address": "123 Business St",
                "tax_id": "US123456789"
            },
            "line_items": [
                {"description": "Service A", "quantity": 1, "unit_price": Decimal("50.00")},
                {"description": "Service B", "quantity": 2, "unit_price": Decimal("25.00")},
            ]
        }

        receipt = await generator.generate_invoice_receipt(invoice_data)

        assert receipt["invoice_number"] == "INV-2024-001"
        assert receipt["total"] == Decimal("110.00")
        assert len(receipt["line_items"]) == 2

    @pytest.mark.asyncio
    async def test_generate_refund_receipt(self):
        """Test refund receipt generation."""
        from dotmac.platform.billing.receipts.generators import ReceiptGenerator

        generator = ReceiptGenerator()

        refund_data = {
            "refund_id": "ref_123",
            "original_payment_id": "pay_123",
            "refund_amount": Decimal("50.00"),
            "currency": "USD",
            "reason": "Customer request",
            "refund_date": datetime.now(timezone.utc)
        }

        receipt = await generator.generate_refund_receipt(refund_data)

        assert receipt["refund_id"] == "ref_123"
        assert receipt["refund_amount"] == Decimal("50.00")
        assert receipt["reason"] == "Customer request"


class TestWebhookHandlers:
    """Tests for webhook handlers."""

    @pytest.mark.asyncio
    async def test_handle_stripe_payment_succeeded(self, mock_db_session):
        """Test handling Stripe payment succeeded webhook."""
        from dotmac.platform.billing.webhooks.handlers import StripeWebhookHandler

        handler = StripeWebhookHandler()

        event = {
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_123",
                    "amount": 9999,
                    "currency": "usd",
                    "metadata": {
                        "subscription_id": "sub_123",
                        "tenant_id": "tenant_123"
                    }
                }
            }
        }

        # Mock subscription update
        mock_subscription = MagicMock()
        mock_subscription.subscription_id = "sub_123"
        mock_subscription.status = "past_due"

        mock_db_session.scalar.return_value = mock_subscription

        with patch('dotmac.platform.billing.webhooks.handlers.get_async_session', return_value=mock_db_session):
            result = await handler.handle_payment_succeeded(event)

        assert result["processed"] is True
        assert mock_subscription.status == "active"
        mock_db_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_handle_stripe_payment_failed(self, mock_db_session):
        """Test handling Stripe payment failed webhook."""
        from dotmac.platform.billing.webhooks.handlers import StripeWebhookHandler

        handler = StripeWebhookHandler()

        event = {
            "type": "payment_intent.payment_failed",
            "data": {
                "object": {
                    "id": "pi_456",
                    "amount": 9999,
                    "metadata": {
                        "subscription_id": "sub_123",
                        "tenant_id": "tenant_123"
                    }
                }
            }
        }

        # Mock subscription
        mock_subscription = MagicMock()
        mock_subscription.subscription_id = "sub_123"
        mock_subscription.status = "active"
        mock_subscription.payment_failures = 0

        mock_db_session.scalar.return_value = mock_subscription

        with patch('dotmac.platform.billing.webhooks.handlers.get_async_session', return_value=mock_db_session):
            result = await handler.handle_payment_failed(event)

        assert result["processed"] is True
        assert mock_subscription.status == "past_due"
        assert mock_subscription.payment_failures == 1

    @pytest.mark.asyncio
    async def test_handle_stripe_subscription_created(self, mock_db_session):
        """Test handling Stripe subscription created webhook."""
        from dotmac.platform.billing.webhooks.handlers import StripeWebhookHandler

        handler = StripeWebhookHandler()

        event = {
            "type": "customer.subscription.created",
            "data": {
                "object": {
                    "id": "sub_stripe_123",
                    "customer": "cus_123",
                    "items": {
                        "data": [
                            {"price": {"id": "price_123", "unit_amount": 9999}}
                        ]
                    },
                    "metadata": {
                        "tenant_id": "tenant_123"
                    }
                }
            }
        }

        with patch('dotmac.platform.billing.webhooks.handlers.get_async_session', return_value=mock_db_session):
            result = await handler.handle_subscription_created(event)

        assert result["processed"] is True
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_handle_webhook_signature_verification(self):
        """Test webhook signature verification."""
        from dotmac.platform.billing.webhooks.handlers import verify_webhook_signature

        payload = b'{"test": "data"}'
        secret = "whsec_test_secret"
        timestamp = str(int(datetime.now().timestamp()))

        # Generate valid signature
        import hmac
        import hashlib

        signed_payload = f"{timestamp}.{payload.decode()}"
        expected_sig = hmac.new(
            secret.encode(),
            signed_payload.encode(),
            hashlib.sha256
        ).hexdigest()

        signature = f"t={timestamp},v1={expected_sig}"

        # Test valid signature
        assert verify_webhook_signature(payload, signature, secret) is True

        # Test invalid signature
        invalid_signature = f"t={timestamp},v1=invalid_sig"
        assert verify_webhook_signature(payload, invalid_signature, secret) is False


class TestMetricsCollection:
    """Tests for billing metrics collection."""

    @pytest.mark.asyncio
    async def test_collect_billing_metrics(self, mock_db_session):
        """Test collecting billing metrics."""
        from dotmac.platform.billing.metrics import BillingMetricsCollector

        collector = BillingMetricsCollector()

        # Mock metric data
        mock_metrics = {
            "active_subscriptions": 100,
            "mrr": Decimal("10000.00"),
            "churn_rate": Decimal("5.0"),
            "average_revenue_per_user": Decimal("100.00")
        }

        mock_result = MagicMock()
        mock_result.one.return_value = mock_metrics
        mock_db_session.execute.return_value = mock_result

        with patch('dotmac.platform.billing.metrics.get_async_session', return_value=mock_db_session):
            metrics = await collector.collect_metrics("tenant_123")

        assert metrics["active_subscriptions"] == 100
        assert metrics["mrr"] == Decimal("10000.00")

    @pytest.mark.asyncio
    async def test_export_metrics_to_observability(self):
        """Test exporting metrics to observability platform."""
        from dotmac.platform.billing.metrics import BillingMetricsExporter

        exporter = BillingMetricsExporter()

        metrics = {
            "active_subscriptions": 100,
            "mrr": Decimal("10000.00"),
            "churn_rate": Decimal("5.0")
        }

        with patch('dotmac.platform.billing.metrics.send_to_observability') as mock_send:
            await exporter.export_metrics(metrics, "tenant_123")

        mock_send.assert_called()
        call_args = mock_send.call_args[0][0]
        assert "billing.subscriptions.active" in call_args
        assert "billing.revenue.mrr" in call_args


class TestConfigurationManagement:
    """Tests for billing configuration management."""

    @pytest.mark.asyncio
    async def test_load_billing_config(self):
        """Test loading billing configuration."""
        from dotmac.platform.billing.config import BillingConfig

        config = BillingConfig()

        assert config.stripe_api_key is not None
        assert config.webhook_secret is not None
        assert config.default_currency == "USD"
        assert config.tax_calculation_enabled in [True, False]

    @pytest.mark.asyncio
    async def test_update_billing_settings(self, mock_db_session):
        """Test updating billing settings."""
        from dotmac.platform.billing.settings.service import BillingSettingsService

        service = BillingSettingsService()

        settings = {
            "enable_automatic_tax": True,
            "default_payment_terms": 30,
            "dunning_max_attempts": 3,
            "trial_period_days": 14
        }

        with patch('dotmac.platform.billing.settings.service.get_async_session', return_value=mock_db_session):
            result = await service.update_settings(settings, "tenant_123")

        assert result["enable_automatic_tax"] is True
        assert result["trial_period_days"] == 14
        mock_db_session.commit.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])