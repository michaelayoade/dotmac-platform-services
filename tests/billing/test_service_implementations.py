"""
Comprehensive service implementation tests for maximum coverage.

Tests all service methods with proper async mocking.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call, ANY
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Dict, List, Any
import uuid

# Mock the database dependencies
with patch('dotmac.platform.db.get_async_session'):
    from dotmac.platform.billing.catalog.service import ProductService
    from dotmac.platform.billing.subscriptions.service import SubscriptionService
    from dotmac.platform.billing.pricing.service import PricingEngine
    from dotmac.platform.billing.integration import BillingIntegrationService


@pytest.fixture
def mock_db_session():
    """Comprehensive mock database session."""
    session = AsyncMock()
    session.add = MagicMock()
    session.delete = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    session.scalar = AsyncMock()
    session.scalars = AsyncMock()
    session.close = AsyncMock()

    # Mock query results
    mock_result = MagicMock()
    mock_result.scalar.return_value = None
    mock_result.scalars.return_value.all.return_value = []
    mock_result.scalars.return_value.first.return_value = None
    mock_result.all.return_value = []
    mock_result.first.return_value = None
    mock_result.one.return_value = None
    mock_result.one_or_none.return_value = None

    session.execute.return_value = mock_result
    return session


class TestProductServiceComplete:
    """Complete tests for ProductService implementation."""

    @pytest.mark.asyncio
    async def test_create_product_full_flow(self, mock_db_session):
        """Test complete product creation flow."""
        from dotmac.platform.billing.catalog.models import ProductCreateRequest, ProductType, TaxClass
        from dotmac.platform.billing.models import BillingProductTable

        service = ProductService()

        # Setup request
        request = ProductCreateRequest(
            sku="TEST-SKU-001",
            name="Test Product",
            description="Test Description",
            product_type=ProductType.SUBSCRIPTION,
            category="software",
            base_price=Decimal("99.99"),
            currency="USD",
            tax_class=TaxClass.STANDARD,
            metadata={"test": True}
        )

        # Mock DB responses
        mock_db_session.scalar.return_value = None  # No existing product

        # Mock the created product
        mock_product = MagicMock(spec=BillingProductTable)
        mock_product.product_id = "prod_test_123"
        mock_product.tenant_id = "tenant_123"
        mock_product.sku = request.sku
        mock_product.name = request.name
        mock_product.base_price = request.base_price
        mock_product.is_active = True
        mock_product.created_at = datetime.now(timezone.utc)

        with patch('dotmac.platform.billing.catalog.service.get_async_session', return_value=mock_db_session):
            with patch('uuid.uuid4', return_value='prod_test_123'):
                # Execute
                result = await service.create_product(request, "tenant_123")

        # Verify
        assert result.sku == request.sku
        assert result.name == request.name
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_product_by_sku(self, mock_db_session):
        """Test getting product by SKU."""
        service = ProductService()

        # Mock product
        mock_product = MagicMock()
        mock_product.product_id = "prod_123"
        mock_product.sku = "TEST-SKU"
        mock_product.name = "Test Product"
        mock_product.is_active = True

        mock_db_session.scalar.return_value = mock_product

        with patch('dotmac.platform.billing.catalog.service.get_async_session', return_value=mock_db_session):
            result = await service.get_product_by_sku("TEST-SKU", "tenant_123")

        assert result.sku == "TEST-SKU"
        mock_db_session.scalar.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_products_with_pagination(self, mock_db_session):
        """Test listing products with pagination."""
        service = ProductService()

        # Mock products
        mock_products = [
            MagicMock(
                product_id=f"prod_{i}",
                sku=f"SKU-{i:03d}",
                name=f"Product {i}",
                base_price=Decimal(str(50 + i * 10)),
                is_active=True
            )
            for i in range(10)
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_products[0:5]  # First page
        mock_db_session.execute.return_value = mock_result

        with patch('dotmac.platform.billing.catalog.service.get_async_session', return_value=mock_db_session):
            result = await service.list_products(
                tenant_id="tenant_123",
                skip=0,
                limit=5
            )

        assert len(result) == 5
        assert result[0].sku == "SKU-000"

    @pytest.mark.asyncio
    async def test_bulk_update_products(self, mock_db_session):
        """Test bulk product updates."""
        service = ProductService()

        # Mock products to update
        mock_products = [
            MagicMock(product_id=f"prod_{i}", base_price=Decimal("50.00"), is_active=False)
            for i in range(3)
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_products
        mock_db_session.execute.return_value = mock_result

        with patch('dotmac.platform.billing.catalog.service.get_async_session', return_value=mock_db_session):
            await service.bulk_update_products(
                product_ids=["prod_0", "prod_1", "prod_2"],
                updates={"is_active": True, "base_price": Decimal("60.00")},
                tenant_id="tenant_123"
            )

        # Verify all products were updated
        for product in mock_products:
            assert product.is_active is True
            assert product.base_price == Decimal("60.00")

        mock_db_session.commit.assert_called_once()


class TestSubscriptionServiceComplete:
    """Complete tests for SubscriptionService implementation."""

    @pytest.mark.asyncio
    async def test_create_subscription_with_trial(self, mock_db_session):
        """Test creating subscription with trial period."""
        from dotmac.platform.billing.subscriptions.models import (
            SubscriptionCreateRequest, BillingCycle, SubscriptionStatus
        )
        from dotmac.platform.billing.models import BillingSubscriptionTable, BillingSubscriptionPlanTable

        service = SubscriptionService()

        # Setup
        request = SubscriptionCreateRequest(
            customer_id="cust_123",
            plan_id="plan_123",
            metadata={"source": "api"}
        )

        # Mock plan with trial
        mock_plan = MagicMock(spec=BillingSubscriptionPlanTable)
        mock_plan.plan_id = "plan_123"
        mock_plan.billing_cycle = BillingCycle.MONTHLY
        mock_plan.price = Decimal("99.99")
        mock_plan.trial_days = 14
        mock_plan.setup_fee = Decimal("0")

        mock_db_session.scalar.return_value = mock_plan

        with patch('dotmac.platform.billing.subscriptions.service.get_async_session', return_value=mock_db_session):
            with patch('uuid.uuid4', return_value='sub_test_123'):
                result = await service.create_subscription(request, "tenant_123")

        assert result.customer_id == "cust_123"
        assert result.plan_id == "plan_123"
        assert result.status == SubscriptionStatus.TRIALING
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_change_subscription_plan_with_proration(self, mock_db_session):
        """Test changing subscription plan with proration."""
        service = SubscriptionService()

        # Mock current subscription
        now = datetime.now(timezone.utc)
        mock_subscription = MagicMock()
        mock_subscription.subscription_id = "sub_123"
        mock_subscription.plan_id = "plan_old"
        mock_subscription.current_period_start = now - timedelta(days=15)
        mock_subscription.current_period_end = now + timedelta(days=15)
        mock_subscription.status = "active"

        # Mock old and new plans
        mock_old_plan = MagicMock()
        mock_old_plan.price = Decimal("50.00")
        mock_old_plan.billing_cycle = "monthly"

        mock_new_plan = MagicMock()
        mock_new_plan.plan_id = "plan_new"
        mock_new_plan.price = Decimal("100.00")
        mock_new_plan.billing_cycle = "monthly"

        mock_db_session.scalar.side_effect = [mock_subscription, mock_old_plan, mock_new_plan]

        with patch('dotmac.platform.billing.subscriptions.service.get_async_session', return_value=mock_db_session):
            result = await service.change_plan(
                subscription_id="sub_123",
                new_plan_id="plan_new",
                tenant_id="tenant_123",
                immediate=True
            )

        assert mock_subscription.plan_id == "plan_new"
        mock_db_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_calculate_subscription_mrr(self, mock_db_session):
        """Test calculating Monthly Recurring Revenue."""
        service = SubscriptionService()

        # Mock active subscriptions with different cycles
        mock_subscriptions = [
            MagicMock(
                subscription_id=f"sub_{i}",
                status="active",
                plan=MagicMock(
                    price=Decimal("100.00"),
                    billing_cycle="monthly" if i % 2 == 0 else "annual"
                )
            )
            for i in range(4)
        ]

        # Monthly: 100 * 2 = 200
        # Annual: (100 * 2) / 12 = 16.67
        # Total MRR: 216.67

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_subscriptions
        mock_db_session.execute.return_value = mock_result

        with patch('dotmac.platform.billing.subscriptions.service.get_async_session', return_value=mock_db_session):
            mrr = await service.calculate_mrr("tenant_123")

        # MRR should be sum of monthly + (annual/12)
        expected_mrr = Decimal("200.00") + (Decimal("200.00") / 12)
        assert abs(mrr - expected_mrr) < Decimal("1.00")  # Allow small rounding difference

    @pytest.mark.asyncio
    async def test_handle_failed_payment(self, mock_db_session):
        """Test handling failed subscription payment."""
        service = SubscriptionService()

        # Mock subscription
        mock_subscription = MagicMock()
        mock_subscription.subscription_id = "sub_123"
        mock_subscription.status = "active"
        mock_subscription.payment_retry_count = 0

        mock_db_session.scalar.return_value = mock_subscription

        with patch('dotmac.platform.billing.subscriptions.service.get_async_session', return_value=mock_db_session):
            await service.handle_payment_failure("sub_123", "tenant_123")

        assert mock_subscription.status == "past_due"
        assert mock_subscription.payment_retry_count == 1
        mock_db_session.commit.assert_called_once()


class TestPricingEngineComplete:
    """Complete tests for PricingEngine implementation."""

    @pytest.mark.asyncio
    async def test_apply_tiered_pricing(self, mock_db_session):
        """Test applying tiered pricing rules."""
        from dotmac.platform.billing.pricing.models import (
            PriceCalculationRequest, DiscountType
        )

        engine = PricingEngine()

        # Mock product
        mock_product = MagicMock()
        mock_product.product_id = "prod_123"
        mock_product.base_price = Decimal("10.00")
        mock_product.category = "software"

        # Mock tiered pricing rules
        mock_rules = [
            MagicMock(
                rule_id="tier1",
                discount_type=DiscountType.PERCENTAGE,
                discount_value=Decimal("5"),
                min_quantity=10,
                max_quantity=50,
                priority=100,
                is_active=True,
                applies_to_product_ids=["prod_123"],
                customer_segments=[],
                starts_at=None,
                ends_at=None,
                current_uses=0,
                max_uses=None
            ),
            MagicMock(
                rule_id="tier2",
                discount_type=DiscountType.PERCENTAGE,
                discount_value=Decimal("10"),
                min_quantity=51,
                max_quantity=100,
                priority=100,
                is_active=True,
                applies_to_product_ids=["prod_123"],
                customer_segments=[],
                starts_at=None,
                ends_at=None,
                current_uses=0,
                max_uses=None
            ),
        ]

        mock_db_session.scalar.return_value = mock_product
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_rules
        mock_db_session.execute.return_value = mock_result

        request = PriceCalculationRequest(
            product_id="prod_123",
            quantity=75,  # Should get tier2 discount
            customer_id="cust_123"
        )

        with patch('dotmac.platform.billing.pricing.service.get_async_session', return_value=mock_db_session):
            result = await engine.calculate_price(request, "tenant_123")

        # 75 * 10 = 750, with 10% discount = 675
        assert result.original_price == Decimal("750.00")
        assert result.final_price == Decimal("675.00")

    @pytest.mark.asyncio
    async def test_apply_customer_segment_pricing(self, mock_db_session):
        """Test applying customer segment-based pricing."""
        from dotmac.platform.billing.pricing.models import DiscountType

        engine = PricingEngine()

        # Mock product
        mock_product = MagicMock()
        mock_product.base_price = Decimal("100.00")

        # Mock segment-based rule
        mock_rule = MagicMock(
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal("20"),
            customer_segments=["premium", "vip"],
            min_quantity=1,
            is_active=True,
            priority=150,
            applies_to_product_ids=["prod_123"],
            starts_at=None,
            ends_at=None,
            current_uses=0,
            max_uses=None
        )

        mock_db_session.scalar.return_value = mock_product
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_rule]
        mock_db_session.execute.return_value = mock_result

        with patch('dotmac.platform.billing.pricing.service.get_async_session', return_value=mock_db_session):
            # Test with premium customer
            from dotmac.platform.billing.pricing.models import PriceCalculationRequest

            request = PriceCalculationRequest(
                product_id="prod_123",
                quantity=1,
                customer_id="cust_123",
                customer_segments=["premium"]
            )

            result = await engine.calculate_price(request, "tenant_123")

        assert result.final_price == Decimal("80.00")  # 20% off

    @pytest.mark.asyncio
    async def test_time_limited_promotion(self, mock_db_session):
        """Test time-limited promotional pricing."""
        from dotmac.platform.billing.pricing.models import DiscountType

        engine = PricingEngine()

        now = datetime.now(timezone.utc)

        # Mock product
        mock_product = MagicMock()
        mock_product.base_price = Decimal("50.00")

        # Mock time-limited rules
        active_promo = MagicMock(
            discount_type=DiscountType.FIXED_AMOUNT,
            discount_value=Decimal("10.00"),
            starts_at=now - timedelta(days=1),
            ends_at=now + timedelta(days=1),
            is_active=True,
            min_quantity=1,
            priority=200,
            applies_to_product_ids=["prod_123"],
            customer_segments=[],
            current_uses=0,
            max_uses=None
        )

        expired_promo = MagicMock(
            discount_type=DiscountType.FIXED_AMOUNT,
            discount_value=Decimal("20.00"),
            starts_at=now - timedelta(days=10),
            ends_at=now - timedelta(days=1),
            is_active=True,
            min_quantity=1,
            priority=200,
            applies_to_product_ids=["prod_123"],
            customer_segments=[],
            current_uses=0,
            max_uses=None
        )

        mock_db_session.scalar.return_value = mock_product
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [active_promo, expired_promo]
        mock_db_session.execute.return_value = mock_result

        with patch('dotmac.platform.billing.pricing.service.get_async_session', return_value=mock_db_session):
            from dotmac.platform.billing.pricing.models import PriceCalculationRequest

            request = PriceCalculationRequest(
                product_id="prod_123",
                quantity=2,
                customer_id="cust_123"
            )

            result = await engine.calculate_price(request, "tenant_123")

        # Only active promo should apply: 100 - 10 = 90
        assert result.final_price == Decimal("90.00")


class TestBillingIntegrationComplete:
    """Complete tests for BillingIntegrationService."""

    @pytest.mark.asyncio
    async def test_process_subscription_renewal(self, mock_db_session):
        """Test processing subscription renewal."""
        service = BillingIntegrationService()

        # Mock subscription and plan
        mock_subscription = MagicMock()
        mock_subscription.subscription_id = "sub_123"
        mock_subscription.customer_id = "cust_123"
        mock_subscription.plan_id = "plan_123"
        mock_subscription.status = "active"
        mock_subscription.current_period_end = datetime.now(timezone.utc)

        mock_plan = MagicMock()
        mock_plan.price = Decimal("99.99")
        mock_plan.billing_cycle = "monthly"

        mock_db_session.scalar.side_effect = [mock_subscription, mock_plan]

        # Mock payment gateway
        mock_payment_result = {"status": "success", "transaction_id": "txn_123"}

        with patch('dotmac.platform.billing.integration.get_async_session', return_value=mock_db_session):
            with patch.object(service, 'payment_gateway') as mock_gateway:
                mock_gateway.charge_customer = AsyncMock(return_value=mock_payment_result)

                result = await service.process_subscription_renewal("sub_123", "tenant_123")

        assert result["status"] == "success"
        assert "invoice_id" in result
        mock_db_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_handle_webhook_event(self, mock_db_session):
        """Test handling webhook events."""
        service = BillingIntegrationService()

        webhook_data = {
            "event_type": "payment.succeeded",
            "payment_id": "pay_123",
            "subscription_id": "sub_123",
            "amount": "99.99"
        }

        # Mock subscription
        mock_subscription = MagicMock()
        mock_subscription.subscription_id = "sub_123"
        mock_subscription.status = "past_due"

        mock_db_session.scalar.return_value = mock_subscription

        with patch('dotmac.platform.billing.integration.get_async_session', return_value=mock_db_session):
            result = await service.handle_webhook(webhook_data, "tenant_123")

        assert result["processed"] is True
        assert mock_subscription.status == "active"
        mock_db_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_generate_invoice_with_tax(self, mock_db_session):
        """Test generating invoice with tax calculation."""
        service = BillingIntegrationService()

        # Mock subscription and items
        invoice_items = [
            {"description": "Subscription", "amount": Decimal("100.00")},
            {"description": "Usage overage", "amount": Decimal("25.00")}
        ]

        customer_data = {
            "customer_id": "cust_123",
            "tax_rate": Decimal("0.10"),  # 10% tax
            "country": "US",
            "state": "CA"
        }

        with patch('dotmac.platform.billing.integration.get_async_session', return_value=mock_db_session):
            result = await service.generate_invoice(
                invoice_items,
                customer_data,
                "tenant_123"
            )

        assert result["subtotal"] == Decimal("125.00")
        assert result["tax_amount"] == Decimal("12.50")
        assert result["total"] == Decimal("137.50")
        mock_db_session.commit.assert_called()


class TestServiceErrorHandling:
    """Test error handling in services."""

    @pytest.mark.asyncio
    async def test_handle_database_error(self, mock_db_session):
        """Test handling database errors gracefully."""
        from sqlalchemy.exc import IntegrityError
        from dotmac.platform.billing.catalog.service import ProductService

        service = ProductService()

        # Mock database error
        mock_db_session.commit.side_effect = IntegrityError("", "", "")

        with patch('dotmac.platform.billing.catalog.service.get_async_session', return_value=mock_db_session):
            from dotmac.platform.billing.catalog.models import ProductCreateRequest, ProductType

            request = ProductCreateRequest(
                sku="TEST-SKU",
                name="Test",
                description="Test",
                product_type=ProductType.ONE_TIME,
                category="test",
                base_price=Decimal("10.00"),
                currency="USD"
            )

            with pytest.raises(IntegrityError):
                await service.create_product(request, "tenant_123")

        mock_db_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_validation_error(self, mock_db_session):
        """Test handling validation errors."""
        from dotmac.platform.billing.pricing.service import PricingEngine

        engine = PricingEngine()

        # Invalid request (negative quantity)
        from dotmac.platform.billing.pricing.models import PriceCalculationRequest

        with pytest.raises(ValueError):
            request = PriceCalculationRequest(
                product_id="prod_123",
                quantity=-1,  # Invalid
                customer_id="cust_123"
            )

    @pytest.mark.asyncio
    async def test_handle_not_found_error(self, mock_db_session):
        """Test handling not found errors."""
        from dotmac.platform.billing.subscriptions.service import SubscriptionService
        from dotmac.platform.billing.exceptions import SubscriptionNotFoundError

        service = SubscriptionService()

        # Mock no subscription found
        mock_db_session.scalar.return_value = None

        with patch('dotmac.platform.billing.subscriptions.service.get_async_session', return_value=mock_db_session):
            with pytest.raises(SubscriptionNotFoundError):
                await service.get_subscription("nonexistent", "tenant_123")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])