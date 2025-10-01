"""Tests for pricing models to reach 90%+ coverage.

Targeting uncovered lines: 82-87, 93-95, 101-103, 107-118, 122-125, 129-138, 229-232, 264-266
"""

import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pydantic import ValidationError

from dotmac.platform.billing.pricing.models import (
    DiscountRule,
    DiscountType,
    PricingRule,
    PricingTier,
)


class TestDiscountRuleValidators:
    """Test DiscountRule validator methods - lines 82-87, 93-95, 101-103."""

    def test_validate_discount_value_negative(self):
        """Test discount value cannot be negative - lines 82-83."""
        with pytest.raises(ValidationError) as exc_info:
            DiscountRule(
                tenant_id="tenant_1",
                rule_id="rule_1",
                name="Test Discount",
                discount_type=DiscountType.PERCENTAGE,
                discount_value=Decimal("-10.00"),  # Negative
            )

        assert "Discount value cannot be negative" in str(exc_info.value)

    def test_validate_discount_value_zero_allowed(self):
        """Test zero discount value is allowed - line 87."""
        rule = DiscountRule(
            tenant_id="tenant_1",
            rule_id="rule_1",
            name="Test Discount",
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal("0.00"),
        )

        assert rule.discount_value == Decimal("0.00")

    def test_validate_min_quantity_zero(self):
        """Test min_quantity cannot be zero - lines 93-94."""
        with pytest.raises(ValidationError) as exc_info:
            DiscountRule(
                tenant_id="tenant_1",
                rule_id="rule_1",
                name="Test Discount",
                discount_type=DiscountType.PERCENTAGE,
                discount_value=Decimal("10.00"),
                min_quantity=0,  # Zero not allowed
            )

        assert "Minimum quantity must be positive" in str(exc_info.value)

    def test_validate_min_quantity_negative(self):
        """Test min_quantity cannot be negative - lines 93-94."""
        with pytest.raises(ValidationError) as exc_info:
            DiscountRule(
                tenant_id="tenant_1",
                rule_id="rule_1",
                name="Test Discount",
                discount_type=DiscountType.PERCENTAGE,
                discount_value=Decimal("10.00"),
                min_quantity=-5,  # Negative not allowed
            )

        assert "Minimum quantity must be positive" in str(exc_info.value)

    def test_validate_max_uses_zero(self):
        """Test max_uses cannot be zero - lines 101-102."""
        with pytest.raises(ValidationError) as exc_info:
            DiscountRule(
                tenant_id="tenant_1",
                rule_id="rule_1",
                name="Test Discount",
                discount_type=DiscountType.PERCENTAGE,
                discount_value=Decimal("10.00"),
                max_uses=0,  # Zero not allowed
            )

        assert "Max uses must be positive" in str(exc_info.value)

    def test_validate_max_uses_negative(self):
        """Test max_uses cannot be negative - lines 101-102."""
        with pytest.raises(ValidationError) as exc_info:
            DiscountRule(
                tenant_id="tenant_1",
                rule_id="rule_1",
                name="Test Discount",
                discount_type=DiscountType.PERCENTAGE,
                discount_value=Decimal("10.00"),
                max_uses=-10,  # Negative not allowed
            )

        assert "Max uses must be positive" in str(exc_info.value)


class TestDiscountRuleMethods:
    """Test DiscountRule methods - lines 107-118, 122-125, 129-138."""

    def test_is_currently_active_false_when_inactive(self):
        """Test is_currently_active returns False when is_active=False - lines 107-108."""
        rule = DiscountRule(
            tenant_id="tenant_1",
            rule_id="rule_1",
            name="Test Discount",
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal("10.00"),
            is_active=False,
        )

        assert rule.is_currently_active() is False

    def test_is_currently_active_false_before_starts_at(self):
        """Test is_currently_active returns False before starts_at - lines 112-113."""
        future_date = datetime.now(timezone.utc) + timedelta(days=7)
        rule = DiscountRule(
            tenant_id="tenant_1",
            rule_id="rule_1",
            name="Test Discount",
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal("10.00"),
            is_active=True,
            starts_at=future_date,
        )

        assert rule.is_currently_active() is False

    def test_is_currently_active_false_after_ends_at(self):
        """Test is_currently_active returns False after ends_at - lines 115-116."""
        past_date = datetime.now(timezone.utc) - timedelta(days=7)
        rule = DiscountRule(
            tenant_id="tenant_1",
            rule_id="rule_1",
            name="Test Discount",
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal("10.00"),
            is_active=True,
            ends_at=past_date,
        )

        assert rule.is_currently_active() is False

    def test_is_currently_active_true_within_time_window(self):
        """Test is_currently_active returns True within time window - line 118."""
        past_date = datetime.now(timezone.utc) - timedelta(days=7)
        future_date = datetime.now(timezone.utc) + timedelta(days=7)
        rule = DiscountRule(
            tenant_id="tenant_1",
            rule_id="rule_1",
            name="Test Discount",
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal("10.00"),
            is_active=True,
            starts_at=past_date,
            ends_at=future_date,
        )

        assert rule.is_currently_active() is True

    def test_has_usage_remaining_true_when_max_uses_none(self):
        """Test has_usage_remaining returns True when max_uses is None - lines 122-123."""
        rule = DiscountRule(
            tenant_id="tenant_1",
            rule_id="rule_1",
            name="Test Discount",
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal("10.00"),
            max_uses=None,
            current_uses=100,  # Doesn't matter
        )

        assert rule.has_usage_remaining() is True

    def test_has_usage_remaining_true_when_under_max(self):
        """Test has_usage_remaining returns True when current < max - line 125."""
        rule = DiscountRule(
            tenant_id="tenant_1",
            rule_id="rule_1",
            name="Test Discount",
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal("10.00"),
            max_uses=100,
            current_uses=50,
        )

        assert rule.has_usage_remaining() is True

    def test_has_usage_remaining_false_when_at_max(self):
        """Test has_usage_remaining returns False when current >= max - line 125."""
        rule = DiscountRule(
            tenant_id="tenant_1",
            rule_id="rule_1",
            name="Test Discount",
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal("10.00"),
            max_uses=100,
            current_uses=100,
        )

        assert rule.has_usage_remaining() is False

    def test_can_be_applied_false_when_not_active(self):
        """Test can_be_applied returns False when not active - lines 129-130."""
        rule = DiscountRule(
            tenant_id="tenant_1",
            rule_id="rule_1",
            name="Test Discount",
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal("10.00"),
            is_active=False,
        )

        assert rule.can_be_applied(quantity=1) is False

    def test_can_be_applied_false_when_no_usage_remaining(self):
        """Test can_be_applied returns False when no usage remaining - lines 132-133."""
        rule = DiscountRule(
            tenant_id="tenant_1",
            rule_id="rule_1",
            name="Test Discount",
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal("10.00"),
            is_active=True,
            max_uses=10,
            current_uses=10,
        )

        assert rule.can_be_applied(quantity=1) is False

    def test_can_be_applied_false_below_min_quantity(self):
        """Test can_be_applied returns False when quantity < min_quantity - lines 135-136."""
        rule = DiscountRule(
            tenant_id="tenant_1",
            rule_id="rule_1",
            name="Test Discount",
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal("10.00"),
            is_active=True,
            min_quantity=10,
        )

        assert rule.can_be_applied(quantity=5) is False

    def test_can_be_applied_true_when_all_conditions_met(self):
        """Test can_be_applied returns True when all conditions met - line 138."""
        rule = DiscountRule(
            tenant_id="tenant_1",
            rule_id="rule_1",
            name="Test Discount",
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal("10.00"),
            is_active=True,
            min_quantity=5,
            max_uses=100,
            current_uses=50,
        )

        assert rule.can_be_applied(quantity=10) is True


class TestPricingTierValidators:
    """Test PricingTier validators - lines 229-232."""

    def test_validate_price_per_unit_negative(self):
        """Test price_per_unit cannot be negative - lines 229-230."""
        with pytest.raises(ValidationError) as exc_info:
            PricingTier(
                tier_id="tier_1",
                min_quantity=1,
                max_quantity=10,
                price_per_unit=Decimal("-5.00"),  # Negative
            )

        assert "Price per unit cannot be negative" in str(exc_info.value)

    def test_validate_price_per_unit_zero_allowed(self):
        """Test zero price_per_unit is allowed - line 232."""
        tier = PricingTier(
            tier_id="tier_1",
            min_quantity=1,
            max_quantity=10,
            price_per_unit=Decimal("0.00"),
        )

        assert tier.price_per_unit == Decimal("0.00")


class TestPricingRuleValidators:
    """Test PricingRule validators - lines 264-266."""

    def test_validate_base_price_negative(self):
        """Test base_price cannot be negative - lines 264-265."""
        with pytest.raises(ValidationError) as exc_info:
            PricingRule(
                tenant_id="tenant_1",
                rule_id="rule_1",
                name="Test Pricing",
                product_id="prod_1",
                base_price=Decimal("-10.00"),  # Negative
                currency="USD",
            )

        assert "Base price cannot be negative" in str(exc_info.value)

    def test_validate_base_price_zero_allowed(self):
        """Test zero base_price is allowed - line 266."""
        rule = PricingRule(
            tenant_id="tenant_1",
            rule_id="rule_1",
            name="Test Pricing",
            product_id="prod_1",
            base_price=Decimal("0.00"),
            currency="USD",
        )

        assert rule.base_price == Decimal("0.00")