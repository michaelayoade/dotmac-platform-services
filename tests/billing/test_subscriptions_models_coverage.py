"""Tests for subscription models to reach 90%+ coverage - focused on uncovered lines."""

import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pydantic import ValidationError

from dotmac.platform.billing.subscriptions.models import (
    BillingCycle,
    Subscription,
    SubscriptionCreateRequest,
    SubscriptionPlan,
    SubscriptionStatus,
    SubscriptionUpdateRequest,
)


class TestSubscriptionPlanValidators:
    """Test uncovered SubscriptionPlan validator lines (107-109, 115-117)."""

    def test_validate_prices_negative_price(self):
        """Test negative price validation - lines 107-108."""
        with pytest.raises(ValidationError) as exc_info:
            SubscriptionPlan(
                tenant_id="tenant_1",
                plan_id="plan_1",
                product_id="prod_1",
                name="Test Plan",
                billing_cycle=BillingCycle.MONTHLY,
                price=Decimal("-10.00"),  # Negative price
                currency="USD",
            )

        assert "Price cannot be negative" in str(exc_info.value)

    def test_validate_prices_negative_setup_fee(self):
        """Test negative setup fee validation - lines 107-108."""
        with pytest.raises(ValidationError) as exc_info:
            SubscriptionPlan(
                tenant_id="tenant_1",
                plan_id="plan_1",
                product_id="prod_1",
                name="Test Plan",
                billing_cycle=BillingCycle.MONTHLY,
                price=Decimal("10.00"),
                currency="USD",
                setup_fee=Decimal("-5.00"),  # Negative setup fee
            )

        assert "Price cannot be negative" in str(exc_info.value)

    def test_validate_trial_days_negative(self):
        """Test negative trial days validation - lines 115-116."""
        with pytest.raises(ValidationError) as exc_info:
            SubscriptionPlan(
                tenant_id="tenant_1",
                plan_id="plan_1",
                product_id="prod_1",
                name="Test Plan",
                billing_cycle=BillingCycle.MONTHLY,
                price=Decimal("10.00"),
                currency="USD",
                trial_days=-5,  # Negative trial days
            )

        assert "Trial days must be between 0 and 365" in str(exc_info.value)

    def test_validate_trial_days_too_long(self):
        """Test trial days > 365 validation - lines 115-116."""
        with pytest.raises(ValidationError) as exc_info:
            SubscriptionPlan(
                tenant_id="tenant_1",
                plan_id="plan_1",
                product_id="prod_1",
                name="Test Plan",
                billing_cycle=BillingCycle.MONTHLY,
                price=Decimal("10.00"),
                currency="USD",
                trial_days=400,  # Too long
            )

        assert "Trial days must be between 0 and 365" in str(exc_info.value)


class TestSubscriptionPlanMethods:
    """Test uncovered SubscriptionPlan method lines (121, 125, 129)."""

    def test_has_trial_with_positive_trial_days(self):
        """Test has_trial returns True - line 121."""
        plan = SubscriptionPlan(
            tenant_id="tenant_1",
            plan_id="plan_1",
            product_id="prod_1",
            name="Test Plan",
            billing_cycle=BillingCycle.MONTHLY,
            price=Decimal("10.00"),
            currency="USD",
            trial_days=14,
        )

        assert plan.has_trial() is True

    def test_has_setup_fee_with_positive_fee(self):
        """Test has_setup_fee returns True - line 125."""
        plan = SubscriptionPlan(
            tenant_id="tenant_1",
            plan_id="plan_1",
            product_id="prod_1",
            name="Test Plan",
            billing_cycle=BillingCycle.MONTHLY,
            price=Decimal("10.00"),
            currency="USD",
            setup_fee=Decimal("25.00"),
        )

        assert plan.has_setup_fee() is True

    def test_supports_usage_billing_true(self):
        """Test supports_usage_billing returns True - line 129."""
        plan = SubscriptionPlan(
            tenant_id="tenant_1",
            plan_id="plan_1",
            product_id="prod_1",
            name="Test Plan",
            billing_cycle=BillingCycle.MONTHLY,
            price=Decimal("10.00"),
            currency="USD",
            included_usage={"api_calls": 1000},
        )

        assert plan.supports_usage_billing() is True


class TestSubscriptionMethods:
    """Test uncovered Subscription method lines (178, 182-184, 188-191, 195)."""

    def test_is_active_with_trialing_status(self):
        """Test is_active returns True for TRIALING - line 178."""
        now = datetime.now(timezone.utc)
        subscription = Subscription(
            tenant_id="tenant_1",
            subscription_id="sub_1",
            customer_id="cust_1",
            plan_id="plan_1",
            status=SubscriptionStatus.TRIALING,
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
        )

        assert subscription.is_active() is True

    def test_is_in_trial_no_trial_end(self):
        """Test is_in_trial returns False when no trial_end - lines 182-183."""
        now = datetime.now(timezone.utc)
        subscription = Subscription(
            tenant_id="tenant_1",
            subscription_id="sub_1",
            customer_id="cust_1",
            plan_id="plan_1",
            status=SubscriptionStatus.ACTIVE,
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            trial_end=None,
        )

        assert subscription.is_in_trial() is False

    def test_is_in_trial_expired_trial(self):
        """Test is_in_trial returns False after trial end - line 184."""
        now = datetime.now(timezone.utc)
        subscription = Subscription(
            tenant_id="tenant_1",
            subscription_id="sub_1",
            customer_id="cust_1",
            plan_id="plan_1",
            status=SubscriptionStatus.ACTIVE,
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            trial_end=now - timedelta(days=1),  # Past date
        )

        assert subscription.is_in_trial() is False

    def test_days_until_renewal_inactive(self):
        """Test days_until_renewal returns 0 for inactive - lines 188-189."""
        now = datetime.now(timezone.utc)
        subscription = Subscription(
            tenant_id="tenant_1",
            subscription_id="sub_1",
            customer_id="cust_1",
            plan_id="plan_1",
            status=SubscriptionStatus.CANCELED,
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
        )

        assert subscription.days_until_renewal() == 0

    def test_days_until_renewal_active(self):
        """Test days_until_renewal calculation - lines 190-191."""
        now = datetime.now(timezone.utc)
        subscription = Subscription(
            tenant_id="tenant_1",
            subscription_id="sub_1",
            customer_id="cust_1",
            plan_id="plan_1",
            status=SubscriptionStatus.ACTIVE,
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
        )

        days = subscription.days_until_renewal()
        assert 29 <= days <= 30  # Allow for timing variance

    def test_is_past_due_true(self):
        """Test is_past_due returns True - line 195."""
        now = datetime.now(timezone.utc)
        subscription = Subscription(
            tenant_id="tenant_1",
            subscription_id="sub_1",
            customer_id="cust_1",
            plan_id="plan_1",
            status=SubscriptionStatus.PAST_DUE,
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
        )

        assert subscription.is_past_due() is True


class TestSubscriptionCreateRequestValidators:
    """Test uncovered SubscriptionCreateRequest validator lines (260-262)."""

    def test_validate_custom_price_negative(self):
        """Test negative custom price validation - lines 260-261."""
        with pytest.raises(ValidationError) as exc_info:
            SubscriptionCreateRequest(
                customer_id="cust_1",
                plan_id="plan_1",
                custom_price=Decimal("-10.00"),  # Negative
            )

        assert "Custom price cannot be negative" in str(exc_info.value)


class TestSubscriptionUpdateRequestValidators:
    """Test uncovered SubscriptionUpdateRequest validator lines (275-277)."""

    def test_validate_custom_price_negative(self):
        """Test negative custom price validation - lines 275-276."""
        with pytest.raises(ValidationError) as exc_info:
            SubscriptionUpdateRequest(
                custom_price=Decimal("-10.00"),  # Negative
            )

        assert "Custom price cannot be negative" in str(exc_info.value)