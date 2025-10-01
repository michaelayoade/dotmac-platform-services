"""
Tests for billing integration service.

Covers integration with invoice and payment systems.
"""

import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock

from dotmac.platform.billing.integration import (
    BillingIntegrationService,
    InvoiceItem,
    BillingInvoiceRequest,
)
from dotmac.platform.billing.subscriptions.models import (
    SubscriptionStatus,
    SubscriptionEventType,
    BillingCycle,
)


class TestBillingIntegrationServiceProcessing:
    """Test billing processing functionality."""

    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        return BillingIntegrationService()

    @pytest.mark.asyncio
    async def test_process_subscription_billing_success(
        self,
        service,
        tenant_id,
        sample_subscription,
        sample_subscription_plan
    ):
        """Test successful subscription billing processing."""
        # Setup subscription in active state (not in trial)
        sample_subscription.status = SubscriptionStatus.ACTIVE
        sample_subscription.trial_end = None  # Not in trial

        with patch.object(service.subscription_service, 'get_subscription') as mock_get_sub:
            mock_get_sub.return_value = sample_subscription

            with patch.object(service.subscription_service, 'get_plan') as mock_get_plan:
                mock_get_plan.return_value = sample_subscription_plan

                with patch.object(service.pricing_service, 'calculate_price') as mock_calc_price:
                    # Mock pricing calculation result
                    from dotmac.platform.billing.pricing.models import PriceCalculationResult
                    mock_pricing_result = PriceCalculationResult(
                        product_id=sample_subscription_plan.product_id,
                        quantity=1,
                        customer_id=sample_subscription.customer_id,
                        base_price=sample_subscription_plan.price,
                        subtotal=sample_subscription_plan.price,
                        total_discount_amount=Decimal("10.00"),
                        final_price=sample_subscription_plan.price - Decimal("10.00"),
                    )
                    mock_calc_price.return_value = mock_pricing_result

                    with patch.object(service, '_create_invoice') as mock_create_invoice:
                        mock_create_invoice.return_value = "inv_123456"

                        with patch.object(service.subscription_service, 'record_event') as mock_record_event:
                            result = await service.process_subscription_billing(
                                sample_subscription.subscription_id, tenant_id
                            )

                            assert result == "inv_123456"
                            mock_create_invoice.assert_called_once()
                            mock_record_event.assert_called_once()

                            # Verify invoice request structure
                            invoice_call = mock_create_invoice.call_args[0][0]
                            assert isinstance(invoice_call, BillingInvoiceRequest)
                            assert invoice_call.customer_id == sample_subscription.customer_id
                            assert len(invoice_call.items) >= 1  # At least subscription item

    @pytest.mark.asyncio
    async def test_process_subscription_billing_with_setup_fee(
        self,
        service,
        tenant_id,
        sample_subscription,
        sample_subscription_plan
    ):
        """Test subscription billing with setup fee for first billing."""
        # Setup as first billing (recent creation)
        sample_subscription.created_at = datetime.now(timezone.utc) - timedelta(days=1)
        sample_subscription.trial_end = None

        # Plan has setup fee
        sample_subscription_plan.setup_fee = Decimal("25.00")

        with patch.object(service.subscription_service, 'get_subscription') as mock_get_sub:
            mock_get_sub.return_value = sample_subscription

            with patch.object(service.subscription_service, 'get_plan') as mock_get_plan:
                mock_get_plan.return_value = sample_subscription_plan

                with patch.object(service.pricing_service, 'calculate_price') as mock_calc_price:
                    from dotmac.platform.billing.pricing.models import PriceCalculationResult
                    mock_pricing_result = PriceCalculationResult(
                        product_id=sample_subscription_plan.product_id,
                        quantity=1,
                        customer_id=sample_subscription.customer_id,
                        base_price=sample_subscription_plan.price,
                        subtotal=sample_subscription_plan.price,
                        total_discount_amount=Decimal("0"),
                        final_price=sample_subscription_plan.price,
                    )
                    mock_calc_price.return_value = mock_pricing_result

                    with patch.object(service, '_create_invoice') as mock_create_invoice:
                        mock_create_invoice.return_value = "inv_with_setup"

                        result = await service.process_subscription_billing(
                            sample_subscription.subscription_id, tenant_id
                        )

                        assert result == "inv_with_setup"

                        # Verify setup fee was included
                        invoice_call = mock_create_invoice.call_args[0][0]
                        assert len(invoice_call.items) >= 2  # Subscription + setup fee

                        setup_items = [item for item in invoice_call.items if "Setup Fee" in item.description]
                        assert len(setup_items) == 1
                        assert setup_items[0].unit_price == Decimal("25.00")

    @pytest.mark.asyncio
    async def test_process_subscription_billing_with_usage(
        self,
        service,
        tenant_id,
        sample_subscription,
        sample_subscription_plan
    ):
        """Test subscription billing with usage-based charges."""
        # Setup subscription with usage
        sample_subscription.usage_records = {
            "api_calls": 15000,  # 5000 over the 10000 limit
            "storage_gb": 120    # 20 over the 100 limit
        }
        sample_subscription.trial_end = None

        with patch.object(service.subscription_service, 'get_subscription') as mock_get_sub:
            mock_get_sub.return_value = sample_subscription

            with patch.object(service.subscription_service, 'get_plan') as mock_get_plan:
                mock_get_plan.return_value = sample_subscription_plan

                with patch.object(service.pricing_service, 'calculate_price') as mock_calc_price:
                    from dotmac.platform.billing.pricing.models import PriceCalculationResult
                    mock_pricing_result = PriceCalculationResult(
                        product_id=sample_subscription_plan.product_id,
                        quantity=1,
                        customer_id=sample_subscription.customer_id,
                        base_price=sample_subscription_plan.price,
                        subtotal=sample_subscription_plan.price,
                        total_discount_amount=Decimal("0"),
                        final_price=sample_subscription_plan.price,
                    )
                    mock_calc_price.return_value = mock_pricing_result

                    with patch.object(service, '_calculate_usage_charges') as mock_usage_charges:
                        # Mock usage charges calculation
                        usage_items = [
                            InvoiceItem(
                                description="Usage Overage: Api Calls",
                                product_id=sample_subscription_plan.product_id,
                                quantity=5000,
                                unit_price=Decimal("0.001"),
                                total_amount=Decimal("5.00"),
                                discount_amount=Decimal("0"),
                                final_amount=Decimal("5.00"),
                            ),
                            InvoiceItem(
                                description="Usage Overage: Storage Gb",
                                product_id=sample_subscription_plan.product_id,
                                quantity=20,
                                unit_price=Decimal("0.50"),
                                total_amount=Decimal("10.00"),
                                discount_amount=Decimal("0"),
                                final_amount=Decimal("10.00"),
                            ),
                        ]
                        mock_usage_charges.return_value = usage_items

                        with patch.object(service, '_create_invoice') as mock_create_invoice:
                            mock_create_invoice.return_value = "inv_with_usage"

                            result = await service.process_subscription_billing(
                                sample_subscription.subscription_id, tenant_id
                            )

                            assert result == "inv_with_usage"

                            # Verify usage charges were included
                            invoice_call = mock_create_invoice.call_args[0][0]
                            assert len(invoice_call.items) >= 3  # Subscription + 2 usage items

    @pytest.mark.asyncio
    async def test_process_subscription_billing_inactive_subscription(
        self,
        service,
        tenant_id,
        sample_subscription
    ):
        """Test billing processing skips inactive subscriptions."""
        sample_subscription.status = SubscriptionStatus.CANCELED

        with patch.object(service.subscription_service, 'get_subscription') as mock_get_sub:
            mock_get_sub.return_value = sample_subscription

            result = await service.process_subscription_billing(
                sample_subscription.subscription_id, tenant_id
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_process_subscription_billing_in_trial(
        self,
        service,
        tenant_id,
        sample_subscription
    ):
        """Test billing processing skips subscriptions in trial."""
        # Set subscription in trial
        sample_subscription.trial_end = datetime.now(timezone.utc) + timedelta(days=7)

        with patch.object(service.subscription_service, 'get_subscription') as mock_get_sub:
            mock_get_sub.return_value = sample_subscription

            result = await service.process_subscription_billing(
                sample_subscription.subscription_id, tenant_id
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_process_subscription_billing_plan_not_found(
        self,
        service,
        tenant_id,
        sample_subscription
    ):
        """Test billing processing when plan not found."""
        sample_subscription.trial_end = None

        with patch.object(service.subscription_service, 'get_subscription') as mock_get_sub:
            mock_get_sub.return_value = sample_subscription

            with patch.object(service.subscription_service, 'get_plan') as mock_get_plan:
                mock_get_plan.return_value = None

                result = await service.process_subscription_billing(
                    sample_subscription.subscription_id, tenant_id
                )

                assert result is None


class TestBillingIntegrationServicePaymentHandling:
    """Test payment success/failure handling."""

    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        return BillingIntegrationService()

    @pytest.mark.asyncio
    async def test_process_failed_payment_first_failure(
        self,
        service,
        tenant_id,
        sample_subscription
    ):
        """Test first payment failure handling."""
        sample_subscription.status = SubscriptionStatus.ACTIVE

        with patch.object(service.subscription_service, 'get_subscription') as mock_get_sub:
            mock_get_sub.return_value = sample_subscription

            with patch.object(service.subscription_service, '_update_subscription_status') as mock_update_status:
                with patch.object(service.subscription_service, 'record_event') as mock_record_event:
                    result = await service.process_failed_payment(
                        sample_subscription.subscription_id, "inv_123", tenant_id, retry_count=0
                    )

                    assert result is True  # Should remain active for retry
                    mock_update_status.assert_called_once_with(
                        sample_subscription.subscription_id, SubscriptionStatus.PAST_DUE, tenant_id
                    )
                    mock_record_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_failed_payment_multiple_failures(
        self,
        service,
        tenant_id,
        sample_subscription
    ):
        """Test multiple payment failures within retry window."""
        with patch.object(service.subscription_service, 'get_subscription') as mock_get_sub:
            mock_get_sub.return_value = sample_subscription

            # Test second failure (still in retry window)
            result = await service.process_failed_payment(
                sample_subscription.subscription_id, "inv_123", tenant_id, retry_count=1
            )
            assert result is True

            # Test third failure (still in retry window)
            result = await service.process_failed_payment(
                sample_subscription.subscription_id, "inv_123", tenant_id, retry_count=2
            )
            assert result is True

    @pytest.mark.asyncio
    async def test_process_failed_payment_too_many_failures(
        self,
        service,
        tenant_id,
        sample_subscription
    ):
        """Test payment failure exceeding retry limit."""
        with patch.object(service.subscription_service, 'get_subscription') as mock_get_sub:
            mock_get_sub.return_value = sample_subscription

            with patch.object(service.subscription_service, 'cancel_subscription') as mock_cancel:
                with patch.object(service.subscription_service, 'record_event') as mock_record_event:
                    result = await service.process_failed_payment(
                        sample_subscription.subscription_id, "inv_123", tenant_id, retry_count=3
                    )

                    assert result is False  # Subscription should be canceled
                    mock_cancel.assert_called_once_with(
                        sample_subscription.subscription_id, tenant_id, at_period_end=False
                    )
                    mock_record_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_successful_payment(
        self,
        service,
        tenant_id,
        sample_subscription
    ):
        """Test successful payment processing."""
        # Set subscription as past due
        sample_subscription.status = SubscriptionStatus.PAST_DUE

        with patch.object(service.subscription_service, 'get_subscription') as mock_get_sub:
            mock_get_sub.return_value = sample_subscription

            with patch.object(service.subscription_service, '_update_subscription_status') as mock_update_status:
                with patch.object(service.subscription_service, 'record_event') as mock_record_event:
                    with patch.object(service.subscription_service, '_reset_usage_for_new_period') as mock_reset_usage:
                        result = await service.process_successful_payment(
                            sample_subscription.subscription_id, "inv_123", tenant_id
                        )

                        assert result is True
                        mock_update_status.assert_called_once_with(
                            sample_subscription.subscription_id, SubscriptionStatus.ACTIVE, tenant_id
                        )
                        mock_record_event.assert_called_once()
                        mock_reset_usage.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_successful_payment_already_active(
        self,
        service,
        tenant_id,
        sample_subscription
    ):
        """Test successful payment for already active subscription."""
        # Subscription already active
        sample_subscription.status = SubscriptionStatus.ACTIVE

        with patch.object(service.subscription_service, 'get_subscription') as mock_get_sub:
            mock_get_sub.return_value = sample_subscription

            with patch.object(service.subscription_service, '_update_subscription_status') as mock_update_status:
                with patch.object(service.subscription_service, 'record_event') as mock_record_event:
                    with patch.object(service.subscription_service, '_reset_usage_for_new_period') as mock_reset_usage:
                        result = await service.process_successful_payment(
                            sample_subscription.subscription_id, "inv_123", tenant_id
                        )

                        assert result is True
                        # Status update should not be called for already active subscription
                        mock_update_status.assert_not_called()
                        mock_record_event.assert_called_once()
                        mock_reset_usage.assert_called_once()


class TestBillingIntegrationServiceRenewalProcessing:
    """Test subscription renewal processing."""

    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        return BillingIntegrationService()

    @pytest.mark.asyncio
    async def test_process_subscription_renewals_success(
        self,
        service,
        tenant_id,
        sample_subscription
    ):
        """Test successful renewal processing."""
        subscriptions_due = [sample_subscription]

        with patch.object(service.subscription_service, 'get_subscriptions_due_for_renewal') as mock_get_due:
            mock_get_due.return_value = subscriptions_due

            with patch.object(service, 'process_subscription_billing') as mock_process_billing:
                mock_process_billing.return_value = "inv_renewal_123"

                results = await service.process_subscription_renewals(tenant_id)

                assert results["processed"] == 1
                assert results["created_invoices"] == 1
                assert results["errors"] == 0
                assert results["skipped"] == 0

                mock_process_billing.assert_called_once_with(
                    sample_subscription.subscription_id, tenant_id
                )

    @pytest.mark.asyncio
    async def test_process_subscription_renewals_with_failures(
        self,
        service,
        tenant_id
    ):
        """Test renewal processing with some failures."""
        # Create multiple subscriptions
        subscriptions_due = [
            MagicMock(subscription_id="sub_1"),
            MagicMock(subscription_id="sub_2"),
            MagicMock(subscription_id="sub_3"),
        ]

        with patch.object(service.subscription_service, 'get_subscriptions_due_for_renewal') as mock_get_due:
            mock_get_due.return_value = subscriptions_due

            with patch.object(service, 'process_subscription_billing') as mock_process_billing:
                # First succeeds with invoice, second succeeds without invoice, third fails
                mock_process_billing.side_effect = ["inv_1", None, Exception("Billing error")]

                results = await service.process_subscription_renewals(tenant_id)

                assert results["processed"] == 3
                assert results["created_invoices"] == 1  # Only first created invoice
                assert results["errors"] == 1  # Third subscription failed
                assert results["skipped"] == 1  # Second returned None

    @pytest.mark.asyncio
    async def test_process_subscription_renewals_no_subscriptions(
        self,
        service,
        tenant_id
    ):
        """Test renewal processing with no due subscriptions."""
        with patch.object(service.subscription_service, 'get_subscriptions_due_for_renewal') as mock_get_due:
            mock_get_due.return_value = []

            results = await service.process_subscription_renewals(tenant_id)

            assert results["processed"] == 0
            assert results["created_invoices"] == 0
            assert results["errors"] == 0
            assert results["skipped"] == 0


class TestBillingIntegrationServiceUsageInvoices:
    """Test usage-based invoice generation."""

    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        return BillingIntegrationService()

    @pytest.mark.asyncio
    async def test_generate_usage_invoice_success(
        self,
        service,
        tenant_id,
        customer_id,
        usage_based_product
    ):
        """Test successful usage invoice generation."""
        usage_data = {
            "api_calls": 50000,
            "bandwidth_gb": 100,
        }

        with patch.object(service.catalog_service, 'get_product') as mock_get_product:
            mock_get_product.return_value = usage_based_product

            with patch.object(service.pricing_service, 'calculate_price') as mock_calc_price:
                from dotmac.platform.billing.pricing.models import PriceCalculationResult

                # Mock pricing results for each usage type
                def pricing_side_effect(request, tenant_id):
                    base_price = usage_based_product.usage_rates.get(request.metadata.get("usage_type", ""), Decimal("0"))
                    total = base_price * request.quantity
                    return PriceCalculationResult(
                        product_id=usage_based_product.product_id,
                        quantity=request.quantity,
                        customer_id=customer_id,
                        base_price=base_price,
                        subtotal=total,
                        total_discount_amount=Decimal("1.00"),  # Small discount
                        final_price=total - Decimal("1.00"),
                    )

                mock_calc_price.side_effect = pricing_side_effect

                with patch.object(service, '_create_invoice') as mock_create_invoice:
                    mock_create_invoice.return_value = "inv_usage_123"

                    result = await service.generate_usage_invoice(
                        customer_id,
                        usage_based_product.product_id,
                        usage_data,
                        tenant_id,
                    )

                    assert result == "inv_usage_123"
                    mock_create_invoice.assert_called_once()

                    # Verify invoice structure
                    invoice_call = mock_create_invoice.call_args[0][0]
                    assert isinstance(invoice_call, BillingInvoiceRequest)
                    assert invoice_call.customer_id == customer_id
                    assert len(invoice_call.items) == 2  # Two usage types

    @pytest.mark.asyncio
    async def test_generate_usage_invoice_product_not_found(
        self,
        service,
        tenant_id,
        customer_id
    ):
        """Test usage invoice generation when product not found."""
        usage_data = {"api_calls": 1000}

        with patch.object(service.catalog_service, 'get_product') as mock_get_product:
            mock_get_product.return_value = None

            result = await service.generate_usage_invoice(
                customer_id, "nonexistent_product", usage_data, tenant_id
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_generate_usage_invoice_not_usage_based(
        self,
        service,
        tenant_id,
        customer_id,
        sample_product  # Regular subscription product
    ):
        """Test usage invoice generation for non-usage-based product."""
        usage_data = {"api_calls": 1000}

        with patch.object(service.catalog_service, 'get_product') as mock_get_product:
            mock_get_product.return_value = sample_product

            result = await service.generate_usage_invoice(
                customer_id, sample_product.product_id, usage_data, tenant_id
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_generate_usage_invoice_no_charges(
        self,
        service,
        tenant_id,
        customer_id,
        usage_based_product
    ):
        """Test usage invoice generation with no billable usage."""
        usage_data = {"api_calls": 0}  # No usage

        with patch.object(service.catalog_service, 'get_product') as mock_get_product:
            mock_get_product.return_value = usage_based_product

            result = await service.generate_usage_invoice(
                customer_id, usage_based_product.product_id, usage_data, tenant_id
            )

            assert result is None


class TestBillingIntegrationServiceHelpers:
    """Test helper methods in integration service."""

    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        return BillingIntegrationService()

    def test_calculate_usage_charges(
        self,
        service,
        sample_subscription,
        sample_subscription_plan
    ):
        """Test usage charge calculation."""
        # Set up subscription with overages
        sample_subscription.usage_records = {
            "api_calls": 15000,  # 5000 over limit
            "storage_gb": 80,    # Under limit
        }

        result = service._calculate_usage_charges(
            sample_subscription, sample_subscription_plan, "test-tenant"
        )

        # Should return list of invoice items for overages
        # In this case, only api_calls should have overage
        overage_items = [item for item in result if "Overage" in item.description]
        assert len(overage_items) >= 1

        # Check api_calls overage
        api_overage = next((item for item in result if "Api Calls" in item.description), None)
        if api_overage:
            assert api_overage.quantity == 5000  # Overage amount
            assert api_overage.unit_price == sample_subscription_plan.overage_rates["api_calls"]

    def test_is_first_billing(self, service, sample_subscription):
        """Test first billing detection."""
        # Recent subscription should be first billing
        sample_subscription.created_at = datetime.now(timezone.utc) - timedelta(days=1)
        assert service._is_first_billing(sample_subscription) is True

        # Old subscription should not be first billing
        sample_subscription.created_at = datetime.now(timezone.utc) - timedelta(days=30)
        assert service._is_first_billing(sample_subscription) is False

    @pytest.mark.asyncio
    async def test_create_invoice(self, service, tenant_id):
        """Test invoice creation (mock implementation)."""
        invoice_request = BillingInvoiceRequest(
            customer_id="customer-123",
            subscription_id="sub-123",
            billing_period_start=datetime.now(timezone.utc),
            billing_period_end=datetime.now(timezone.utc) + timedelta(days=30),
            items=[
                InvoiceItem(
                    description="Test Item",
                    product_id="prod-123",
                    quantity=1,
                    unit_price=Decimal("29.99"),
                    total_amount=Decimal("29.99"),
                    discount_amount=Decimal("0"),
                    final_amount=Decimal("29.99"),
                )
            ],
            subtotal=Decimal("29.99"),
            total_discount=Decimal("0"),
            total_amount=Decimal("29.99"),
        )

        result = await service._create_invoice(invoice_request, tenant_id)

        # Should return a simulated invoice ID
        assert result is not None
        assert result.startswith("inv_")


class TestBillingIntegrationModels:
    """Test integration service models."""

    def test_invoice_item_creation(self):
        """Test InvoiceItem model creation."""
        item = InvoiceItem(
            description="Test Product",
            product_id="prod_123",
            quantity=2,
            unit_price=Decimal("25.00"),
            total_amount=Decimal("50.00"),
            discount_amount=Decimal("5.00"),
            final_amount=Decimal("45.00"),
        )

        assert item.description == "Test Product"
        assert item.quantity == 2
        assert item.final_amount == Decimal("45.00")

    def test_billing_invoice_request_creation(self):
        """Test BillingInvoiceRequest model creation."""
        now = datetime.now(timezone.utc)

        item = InvoiceItem(
            description="Test Item",
            product_id="prod_123",
            quantity=1,
            unit_price=Decimal("29.99"),
            total_amount=Decimal("29.99"),
            discount_amount=Decimal("0"),
            final_amount=Decimal("29.99"),
        )

        invoice_request = BillingInvoiceRequest(
            customer_id="customer-456",
            subscription_id="sub-123",
            billing_period_start=now,
            billing_period_end=now + timedelta(days=30),
            items=[item],
            subtotal=Decimal("29.99"),
            total_discount=Decimal("0"),
            total_amount=Decimal("29.99"),
        )

        assert invoice_request.customer_id == "customer-456"
        assert invoice_request.subscription_id == "sub-123"
        assert len(invoice_request.items) == 1
        assert invoice_request.total_amount == Decimal("29.99")


class TestBillingIntegrationErrorHandling:
    """Test error handling in integration service."""

    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        return BillingIntegrationService()

    @pytest.mark.asyncio
    async def test_process_subscription_billing_error_handling(
        self,
        service,
        tenant_id,
        sample_subscription
    ):
        """Test error handling in subscription billing processing."""
        with patch.object(service.subscription_service, 'get_subscription') as mock_get_sub:
            # Simulate service error
            mock_get_sub.side_effect = Exception("Service error")

            with pytest.raises(Exception) as exc_info:
                await service.process_subscription_billing(
                    sample_subscription.subscription_id, tenant_id
                )

            assert "Service error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_process_failed_payment_error_handling(
        self,
        service,
        tenant_id
    ):
        """Test error handling in payment failure processing."""
        with patch.object(service.subscription_service, 'get_subscription') as mock_get_sub:
            # Simulate service error
            mock_get_sub.side_effect = Exception("Database error")

            with pytest.raises(Exception) as exc_info:
                await service.process_failed_payment("sub_123", "inv_123", tenant_id)

            assert "Database error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_process_subscription_renewals_handles_individual_failures(
        self,
        service,
        tenant_id
    ):
        """Test that renewal processing continues despite individual failures."""
        subscriptions_due = [
            MagicMock(subscription_id="sub_1"),
            MagicMock(subscription_id="sub_2"),
        ]

        with patch.object(service.subscription_service, 'get_subscriptions_due_for_renewal') as mock_get_due:
            mock_get_due.return_value = subscriptions_due

            with patch.object(service, 'process_subscription_billing') as mock_process_billing:
                # First fails, second succeeds
                mock_process_billing.side_effect = [Exception("Billing failed"), "inv_success"]

                # Should not raise exception, but handle errors gracefully
                results = await service.process_subscription_renewals(tenant_id)

                assert results["processed"] == 2
                assert results["created_invoices"] == 1
                assert results["errors"] == 1