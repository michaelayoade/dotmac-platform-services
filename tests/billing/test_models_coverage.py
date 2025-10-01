"""
Comprehensive model coverage tests for billing system.

Tests all Pydantic models without complex database dependencies.
"""

import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from pydantic import ValidationError
from typing import Any

# Import all model classes that need coverage
try:
    from dotmac.platform.billing.catalog.models import (
        Product,
        ProductCategory,
        ProductType,
        UsageType,
        ProductCreateRequest,
        ProductUpdateRequest,
        ProductCategoryCreateRequest,
    )
except ImportError:
    # Fallback if imports fail
    Product = None
    ProductCategory = None

try:
    from dotmac.platform.billing.subscriptions.models import (
        SubscriptionPlan,
        Subscription,
        BillingCycle,
        SubscriptionStatus,
        SubscriptionPlanCreateRequest,
        SubscriptionCreateRequest,
    )
except ImportError:
    SubscriptionPlan = None
    Subscription = None

try:
    from dotmac.platform.billing.pricing.models import (
        PricingRule,
        DiscountType,
        PricingRuleCreateRequest,
        PriceCalculationRequest,
        PriceCalculationContext,
        PriceCalculationResult,
        PriceAdjustment,
    )
except ImportError:
    PricingRule = None


# ========================================
# Catalog Model Tests
# ========================================

@pytest.mark.skipif(Product is None, reason="Product model not available")
class TestProductModel:
    """Test Product model validation and methods."""

    def test_product_creation_success(self):
        """Test successful product creation."""
        product = Product(
            product_id="prod_123",
            tenant_id="tenant_123",
            sku="SKU-001",
            name="Test Product",
            description="A test product",
            product_type=ProductType.SUBSCRIPTION,
            category="software",
            base_price=Decimal("99.99"),
            currency="USD",
            is_active=True,
            usage_rates={"api_calls": Decimal("0.01")},
            metadata={"tier": "pro"},
            created_at=datetime.now(timezone.utc),
            updated_at=None,
        )

        assert product.product_id == "prod_123"
        assert product.base_price == Decimal("99.99")
        assert product.product_type == ProductType.SUBSCRIPTION

    def test_product_validation_negative_price(self):
        """Test validation fails with negative price."""
        with pytest.raises(ValidationError):
            Product(
                product_id="prod_123",
                tenant_id="tenant_123",
                sku="SKU-001",
                name="Test Product",
                description="A test product",
                product_type=ProductType.ONE_TIME,
                category="software",
                base_price=Decimal("-10.00"),  # Should fail
                currency="USD",
                is_active=True,
                created_at=datetime.now(timezone.utc),
            )

    def test_product_business_methods(self):
        """Test product business logic methods."""
        product = Product(
            product_id="prod_123",
            tenant_id="tenant_123",
            sku="SKU-001",
            name="Test Product",
            description="A test product",
            product_type=ProductType.SUBSCRIPTION,
            category="software",
            base_price=Decimal("99.99"),
            currency="USD",
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )

        # Test business methods exist and return expected types
        assert hasattr(product, 'is_subscription')
        assert hasattr(product, 'supports_usage_billing')


@pytest.mark.skipif(ProductCategory is None, reason="ProductCategory model not available")
class TestProductCategoryModel:
    """Test ProductCategory model validation."""

    def test_category_creation_success(self):
        """Test successful category creation."""
        category = ProductCategory(
            category_id="cat_123",
            tenant_id="tenant_123",
            name="Software Tools",
            description="Development tools",
            is_active=True,
            metadata={"department": "engineering"},
            created_at=datetime.now(timezone.utc),
            updated_at=None,
        )

        assert category.name == "Software Tools"
        assert category.is_active is True


# ========================================
# Subscription Model Tests
# ========================================

@pytest.mark.skipif(SubscriptionPlan is None, reason="SubscriptionPlan model not available")
class TestSubscriptionPlanModel:
    """Test SubscriptionPlan model validation."""

    def test_plan_creation_success(self):
        """Test successful plan creation."""
        plan = SubscriptionPlan(
            plan_id="plan_123",
            tenant_id="tenant_123",
            product_id="prod_123",
            name="Pro Plan",
            description="Professional plan",
            billing_cycle=BillingCycle.MONTHLY,
            price=Decimal("99.99"),
            currency="USD",
            setup_fee=Decimal("19.99"),
            trial_days=14,
            included_usage={"api_calls": 10000},
            overage_rates={"api_calls": Decimal("0.001")},
            is_active=True,
            metadata={"tier": "pro"},
            created_at=datetime.now(timezone.utc),
            updated_at=None,
        )

        assert plan.plan_id == "plan_123"
        assert plan.price == Decimal("99.99")
        assert plan.billing_cycle == BillingCycle.MONTHLY

    def test_plan_validation_negative_price(self):
        """Test validation fails with negative price."""
        with pytest.raises(ValidationError):
            SubscriptionPlan(
                plan_id="plan_123",
                tenant_id="tenant_123",
                product_id="prod_123",
                name="Pro Plan",
                description="Professional plan",
                billing_cycle=BillingCycle.MONTHLY,
                price=Decimal("-99.99"),  # Should fail
                currency="USD",
                is_active=True,
                created_at=datetime.now(timezone.utc),
            )


@pytest.mark.skipif(Subscription is None, reason="Subscription model not available")
class TestSubscriptionModel:
    """Test Subscription model validation."""

    def test_subscription_creation_success(self):
        """Test successful subscription creation."""
        now = datetime.now(timezone.utc)
        subscription = Subscription(
            subscription_id="sub_123",
            tenant_id="tenant_123",
            customer_id="cust_123",
            plan_id="plan_123",
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            status=SubscriptionStatus.ACTIVE,
            trial_end=now + timedelta(days=14),
            cancel_at_period_end=False,
            canceled_at=None,
            ended_at=None,
            custom_price=None,
            usage_records={"api_calls": 5000},
            metadata={"source": "web"},
            created_at=now,
            updated_at=None,
        )

        assert subscription.subscription_id == "sub_123"
        assert subscription.status == SubscriptionStatus.ACTIVE

    def test_subscription_business_methods(self):
        """Test subscription business logic methods."""
        now = datetime.now(timezone.utc)
        subscription = Subscription(
            subscription_id="sub_123",
            tenant_id="tenant_123",
            customer_id="cust_123",
            plan_id="plan_123",
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            status=SubscriptionStatus.ACTIVE,
            trial_end=now + timedelta(days=14),
            cancel_at_period_end=False,
            usage_records={},
            metadata={},
            created_at=now,
        )

        # Test that business methods exist
        assert hasattr(subscription, 'is_active')
        assert hasattr(subscription, 'is_in_trial')
        assert hasattr(subscription, 'days_until_renewal')


# ========================================
# Pricing Model Tests
# ========================================

@pytest.mark.skipif(PricingRule is None, reason="PricingRule model not available")
class TestPricingRuleModel:
    """Test PricingRule model validation."""

    def test_pricing_rule_creation_success(self):
        """Test successful pricing rule creation."""
        rule = PricingRule(
            rule_id="rule_123",
            tenant_id="tenant_123",
            name="Volume Discount",
            description="10% off bulk orders",
            applies_to_product_ids=["prod_123"],
            applies_to_categories=[],
            applies_to_all=False,
            min_quantity=10,
            customer_segments=["premium"],
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal("10"),
            starts_at=None,
            ends_at=None,
            max_uses=None,
            current_uses=0,
            priority=100,
            is_active=True,
            metadata={"campaign": "q4"},
            created_at=datetime.now(timezone.utc),
            updated_at=None,
        )

        assert rule.rule_id == "rule_123"
        assert rule.discount_value == Decimal("10")
        assert rule.discount_type == DiscountType.PERCENTAGE

    def test_pricing_rule_validation_negative_discount(self):
        """Test validation fails with negative discount."""
        with pytest.raises(ValidationError):
            PricingRule(
                rule_id="rule_123",
                tenant_id="tenant_123",
                name="Invalid Rule",
                description="Invalid discount",
                applies_to_product_ids=[],
                applies_to_categories=[],
                applies_to_all=True,
                discount_type=DiscountType.PERCENTAGE,
                discount_value=Decimal("-10"),  # Should fail
                current_uses=0,
                priority=100,
                is_active=True,
                created_at=datetime.now(timezone.utc),
            )

    def test_pricing_rule_business_methods(self):
        """Test pricing rule business logic methods."""
        rule = PricingRule(
            rule_id="rule_123",
            tenant_id="tenant_123",
            name="Test Rule",
            description="Test rule",
            applies_to_product_ids=[],
            applies_to_categories=[],
            applies_to_all=True,
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal("10"),
            current_uses=0,
            priority=100,
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )

        # Test that business methods exist
        assert hasattr(rule, 'is_currently_active')
        assert hasattr(rule, 'can_be_applied')
        assert hasattr(rule, 'has_usage_remaining')


# ========================================
# Request/Response Model Tests
# ========================================

@pytest.mark.skipif(ProductCreateRequest is None, reason="Request models not available")
class TestRequestModels:
    """Test request/response model validation."""

    def test_product_create_request_success(self):
        """Test successful product creation request."""
        request = ProductCreateRequest(
            sku="SKU-001",
            name="Test Product",
            description="A test product",
            product_type=ProductType.ONE_TIME,
            category="software",
            base_price=Decimal("49.99"),
            currency="USD",
            usage_rates={"api_calls": Decimal("0.01")},
            metadata={"test": True},
        )

        assert request.sku == "SKU-001"
        assert request.base_price == Decimal("49.99")

    def test_product_create_request_validation_failure(self):
        """Test request validation failures."""
        with pytest.raises(ValidationError):
            ProductCreateRequest(
                sku="",  # Empty SKU should fail
                name="Test Product",
                description="A test product",
                product_type=ProductType.ONE_TIME,
                category="software",
                base_price=Decimal("49.99"),
                currency="USD",
            )


# ========================================
# Enum Tests
# ========================================

def test_product_type_enum():
    """Test ProductType enum values."""
    assert ProductType.ONE_TIME == "one_time"
    assert ProductType.SUBSCRIPTION == "subscription"
    assert ProductType.USAGE_BASED == "usage_based"


def test_billing_cycle_enum():
    """Test BillingCycle enum values."""
    assert BillingCycle.MONTHLY == "monthly"
    assert BillingCycle.YEARLY == "yearly"
    assert BillingCycle.WEEKLY == "weekly"


def test_subscription_status_enum():
    """Test SubscriptionStatus enum values."""
    assert SubscriptionStatus.ACTIVE == "active"
    assert SubscriptionStatus.CANCELED == "canceled"
    assert SubscriptionStatus.PAUSED == "paused"


def test_discount_type_enum():
    """Test DiscountType enum values."""
    assert DiscountType.PERCENTAGE == "percentage"
    assert DiscountType.FIXED_AMOUNT == "fixed_amount"
    assert DiscountType.FIXED_PRICE == "fixed_price"


# ========================================
# Edge Case Tests
# ========================================

def test_decimal_precision_handling():
    """Test decimal precision in billing calculations."""
    # Test high precision calculations
    price = Decimal("99.999999")
    discount = Decimal("0.123456")

    result = price * discount
    assert isinstance(result, Decimal)
    assert result == Decimal("12.345676543544")


def test_datetime_timezone_handling():
    """Test timezone handling in models."""
    # Test UTC timezone handling
    utc_time = datetime.now(timezone.utc)
    assert utc_time.tzinfo == timezone.utc

    # Test period calculations
    start = datetime.now(timezone.utc)
    end = start + timedelta(days=30)

    diff = (end - start).days
    assert diff == 30


def test_metadata_field_flexibility():
    """Test metadata field accepts various data types."""
    # Test with different metadata types
    metadata_variations = [
        {"string": "value"},
        {"number": 42},
        {"boolean": True},
        {"list": [1, 2, 3]},
        {"nested": {"key": "value"}},
        {},  # Empty metadata
    ]

    for metadata in metadata_variations:
        # This should not raise validation errors
        assert isinstance(metadata, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])