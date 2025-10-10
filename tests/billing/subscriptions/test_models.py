"""
Tests for billing subscription models.

Covers Pydantic model validation, enums, and business logic.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from pydantic import ValidationError

from dotmac.platform.billing.subscriptions.models import (
    BillingCycle,
    ProrationBehavior,
    ProrationResult,
    Subscription,
    SubscriptionCreateRequest,
    SubscriptionEvent,
    SubscriptionEventType,
    SubscriptionPlan,
    SubscriptionPlanChangeRequest,
    SubscriptionPlanCreateRequest,
    SubscriptionPlanResponse,
    SubscriptionResponse,
    SubscriptionStatus,
    SubscriptionUpdateRequest,
    UsageRecordRequest,
)


class TestBillingCycle:
    """Test BillingCycle enum."""

    def test_billing_cycle_values(self):
        """Test BillingCycle enum values."""
        assert BillingCycle.MONTHLY == "monthly"
        assert BillingCycle.QUARTERLY == "quarterly"
        assert BillingCycle.ANNUAL == "annual"

    def test_billing_cycle_enum_members(self):
        """Test BillingCycle enum has all expected members."""
        expected_cycles = {"MONTHLY", "QUARTERLY", "ANNUAL"}
        actual_cycles = set(BillingCycle.__members__.keys())
        assert actual_cycles == expected_cycles


class TestSubscriptionStatus:
    """Test SubscriptionStatus enum."""

    def test_subscription_status_values(self):
        """Test SubscriptionStatus enum values."""
        assert SubscriptionStatus.INCOMPLETE == "incomplete"
        assert SubscriptionStatus.TRIALING == "trialing"
        assert SubscriptionStatus.ACTIVE == "active"
        assert SubscriptionStatus.PAST_DUE == "past_due"
        assert SubscriptionStatus.CANCELED == "canceled"
        assert SubscriptionStatus.ENDED == "ended"
        assert SubscriptionStatus.PAUSED == "paused"

    def test_subscription_status_enum_members(self):
        """Test SubscriptionStatus enum has all expected members."""
        expected_statuses = {
            "INCOMPLETE",
            "TRIALING",
            "ACTIVE",
            "PAST_DUE",
            "CANCELED",
            "ENDED",
            "PAUSED",
        }
        actual_statuses = set(SubscriptionStatus.__members__.keys())
        assert actual_statuses == expected_statuses


class TestSubscriptionEventType:
    """Test SubscriptionEventType enum."""

    def test_subscription_event_type_values(self):
        """Test SubscriptionEventType enum values."""
        assert SubscriptionEventType.CREATED == "subscription.created"
        assert SubscriptionEventType.ACTIVATED == "subscription.activated"
        assert SubscriptionEventType.CANCELED == "subscription.canceled"
        assert SubscriptionEventType.ENDED == "subscription.ended"

    def test_subscription_event_type_enum_members(self):
        """Test SubscriptionEventType enum has all expected members."""
        expected_events = {
            "CREATED",
            "ACTIVATED",
            "TRIAL_STARTED",
            "TRIAL_ENDED",
            "RENEWED",
            "PLAN_CHANGED",
            "CANCELED",
            "PAUSED",
            "RESUMED",
            "ENDED",
            "PAYMENT_FAILED",
            "PAYMENT_SUCCEEDED",
        }
        actual_events = set(SubscriptionEventType.__members__.keys())
        assert actual_events == expected_events


class TestProrationBehavior:
    """Test ProrationBehavior enum."""

    def test_proration_behavior_values(self):
        """Test ProrationBehavior enum values."""
        assert ProrationBehavior.NONE == "none"
        assert ProrationBehavior.CREATE_PRORATIONS == "prorate"

    def test_proration_behavior_enum_members(self):
        """Test ProrationBehavior enum has all expected members."""
        expected_behaviors = {"NONE", "CREATE_PRORATIONS"}
        actual_behaviors = set(ProrationBehavior.__members__.keys())
        assert actual_behaviors == expected_behaviors


class TestSubscriptionPlan:
    """Test SubscriptionPlan model."""

    def test_valid_subscription_plan_creation(self, sample_subscription_plan):
        """Test creating a valid subscription plan."""
        plan = sample_subscription_plan
        assert plan.plan_id == "plan_123"
        assert plan.product_id == "prod_123"
        assert plan.billing_cycle == BillingCycle.MONTHLY
        assert plan.price == Decimal("99.99")
        assert plan.setup_fee == Decimal("19.99")
        assert plan.trial_days == 14

    def test_subscription_plan_validation_negative_price(self):
        """Test subscription plan validation fails with negative price."""
        with pytest.raises(ValidationError) as exc_info:
            SubscriptionPlan(
                plan_id="plan_123",
                tenant_id="test-tenant",
                product_id="prod_123",
                name="Test Plan",
                billing_cycle=BillingCycle.MONTHLY,
                price=Decimal("-10.00"),  # Negative price
                currency="USD",
                is_active=True,
                created_at=datetime.now(UTC),
            )

        errors = exc_info.value.errors()
        assert any("price" in str(error) for error in errors)

    def test_subscription_plan_validation_negative_setup_fee(self):
        """Test subscription plan validation fails with negative setup fee."""
        with pytest.raises(ValidationError) as exc_info:
            SubscriptionPlan(
                plan_id="plan_123",
                tenant_id="test-tenant",
                product_id="prod_123",
                name="Test Plan",
                billing_cycle=BillingCycle.MONTHLY,
                price=Decimal("10.00"),
                currency="USD",
                setup_fee=Decimal("-5.00"),  # Negative setup fee
                is_active=True,
                created_at=datetime.now(UTC),
            )

        errors = exc_info.value.errors()
        assert any("setup_fee" in str(error) for error in errors)

    def test_subscription_plan_validation_invalid_trial_days(self):
        """Test subscription plan validation with invalid trial days."""
        # Test negative trial days
        with pytest.raises(ValidationError):
            SubscriptionPlan(
                plan_id="plan_123",
                tenant_id="test-tenant",
                product_id="prod_123",
                name="Test Plan",
                billing_cycle=BillingCycle.MONTHLY,
                price=Decimal("10.00"),
                currency="USD",
                trial_days=-1,  # Negative trial days
                is_active=True,
                created_at=datetime.now(UTC),
            )

        # Test excessive trial days
        with pytest.raises(ValidationError):
            SubscriptionPlan(
                plan_id="plan_123",
                tenant_id="test-tenant",
                product_id="prod_123",
                name="Test Plan",
                billing_cycle=BillingCycle.MONTHLY,
                price=Decimal("10.00"),
                currency="USD",
                trial_days=400,  # Too many trial days
                is_active=True,
                created_at=datetime.now(UTC),
            )

    def test_subscription_plan_business_methods(self, sample_subscription_plan):
        """Test subscription plan business logic methods."""
        plan = sample_subscription_plan

        # Test has_trial
        assert plan.has_trial() is True

        # Test has_setup_fee
        assert plan.has_setup_fee() is True

        # Test supports_usage_billing
        assert plan.supports_usage_billing() is True

        # Test plan without trial
        plan_no_trial = SubscriptionPlan(
            plan_id="plan_no_trial",
            tenant_id="test-tenant",
            product_id="prod_123",
            name="No Trial Plan",
            billing_cycle=BillingCycle.MONTHLY,
            price=Decimal("10.00"),
            currency="USD",
            trial_days=0,  # No trial
            is_active=True,
            created_at=datetime.now(UTC),
        )
        assert plan_no_trial.has_trial() is False

    def test_subscription_plan_defaults(self):
        """Test subscription plan model defaults."""
        plan = SubscriptionPlan(
            plan_id="plan_123",
            tenant_id="test-tenant",
            product_id="prod_123",
            name="Test Plan",
            billing_cycle=BillingCycle.MONTHLY,
            price=Decimal("10.00"),
            created_at=datetime.now(UTC),
        )

        assert plan.description is None
        assert plan.currency == "USD"
        assert plan.setup_fee is None
        assert plan.trial_days is None
        assert plan.included_usage == {}
        assert plan.overage_rates == {}
        assert plan.is_active is True
        assert plan.metadata == {}

    def test_subscription_plan_json_encoders(self, sample_subscription_plan):
        """Test subscription plan JSON serialization."""
        plan_dict = sample_subscription_plan.model_dump()

        # Decimal should be converted to string
        assert isinstance(plan_dict["price"], str)
        assert isinstance(plan_dict["setup_fee"], str)

        # DateTime should be converted to ISO format
        assert isinstance(plan_dict["created_at"], str)


class TestSubscription:
    """Test Subscription model."""

    def test_valid_subscription_creation(self, sample_subscription):
        """Test creating a valid subscription."""
        subscription = sample_subscription
        assert subscription.subscription_id == "sub_123"
        assert subscription.customer_id == "customer-456"
        assert subscription.plan_id == "plan_123"
        assert subscription.status == SubscriptionStatus.ACTIVE
        assert subscription.usage_records == {"api_calls": 5000, "storage_gb": 50}

    def test_subscription_business_methods(self, sample_subscription):
        """Test subscription business logic methods."""
        subscription = sample_subscription

        # Test is_active
        assert subscription.is_active() is True

        # Test is_in_trial
        assert subscription.is_in_trial() is True

        # Test days_until_renewal
        days = subscription.days_until_renewal()
        assert days > 0

        # Test is_past_due
        assert subscription.is_past_due() is False

        # Test with past due subscription
        past_due_subscription = Subscription(
            subscription_id="sub_past_due",
            tenant_id="test-tenant",
            customer_id="customer-456",
            plan_id="plan_123",
            current_period_start=datetime.now(UTC),
            current_period_end=datetime.now(UTC) + timedelta(days=30),
            status=SubscriptionStatus.PAST_DUE,
            created_at=datetime.now(UTC),
        )
        assert past_due_subscription.is_past_due() is True
        assert past_due_subscription.is_active() is False

    def test_subscription_trial_logic(self):
        """Test subscription trial period logic."""
        now = datetime.now(UTC)

        # Subscription in trial
        trial_subscription = Subscription(
            subscription_id="sub_trial",
            tenant_id="test-tenant",
            customer_id="customer-456",
            plan_id="plan_123",
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            status=SubscriptionStatus.TRIALING,
            trial_end=now + timedelta(days=7),  # 7 days left in trial
            created_at=now,
        )
        assert trial_subscription.is_in_trial() is True

        # Subscription with expired trial
        expired_trial_subscription = Subscription(
            subscription_id="sub_expired_trial",
            tenant_id="test-tenant",
            customer_id="customer-456",
            plan_id="plan_123",
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            status=SubscriptionStatus.ACTIVE,
            trial_end=now - timedelta(days=1),  # Trial ended yesterday
            created_at=now,
        )
        assert expired_trial_subscription.is_in_trial() is False

    def test_subscription_defaults(self):
        """Test subscription model defaults."""
        now = datetime.now(UTC)
        subscription = Subscription(
            subscription_id="sub_123",
            tenant_id="test-tenant",
            customer_id="customer-456",
            plan_id="plan_123",
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            status=SubscriptionStatus.ACTIVE,
            created_at=now,
        )

        assert subscription.trial_end is None
        assert subscription.cancel_at_period_end is False
        assert subscription.canceled_at is None
        assert subscription.ended_at is None
        assert subscription.custom_price is None
        assert subscription.usage_records == {}
        assert subscription.metadata == {}

    def test_subscription_json_encoders(self, sample_subscription):
        """Test subscription JSON serialization."""
        subscription_dict = sample_subscription.model_dump()

        # DateTime should be converted to ISO format
        assert isinstance(subscription_dict["current_period_start"], str)
        assert isinstance(subscription_dict["current_period_end"], str)
        assert isinstance(subscription_dict["created_at"], str)


class TestSubscriptionEvent:
    """Test SubscriptionEvent model."""

    def test_valid_subscription_event_creation(self):
        """Test creating a valid subscription event."""
        event = SubscriptionEvent(
            event_id="event_123",
            tenant_id="test-tenant",
            subscription_id="sub_123",
            event_type=SubscriptionEventType.CREATED,
            event_data={"plan_id": "plan_123"},
            user_id="user_123",
            created_at=datetime.now(UTC),
        )

        assert event.event_id == "event_123"
        assert event.subscription_id == "sub_123"
        assert event.event_type == SubscriptionEventType.CREATED
        assert event.event_data == {"plan_id": "plan_123"}
        assert event.user_id == "user_123"

    def test_subscription_event_defaults(self):
        """Test subscription event model defaults."""
        event = SubscriptionEvent(
            event_id="event_123",
            tenant_id="test-tenant",
            subscription_id="sub_123",
            event_type=SubscriptionEventType.CREATED,
            created_at=datetime.now(UTC),
        )

        assert event.event_data == {}
        assert event.user_id is None

    def test_subscription_event_json_encoders(self):
        """Test subscription event JSON serialization."""
        event = SubscriptionEvent(
            event_id="event_123",
            tenant_id="test-tenant",
            subscription_id="sub_123",
            event_type=SubscriptionEventType.CREATED,
            event_data={"timestamp": datetime.now(UTC)},
            created_at=datetime.now(UTC),
        )

        event_dict = event.model_dump()
        assert isinstance(event_dict["created_at"], str)


class TestSubscriptionPlanCreateRequest:
    """Test SubscriptionPlanCreateRequest model."""

    def test_valid_plan_create_request(self, plan_create_request):
        """Test valid subscription plan creation request."""
        request = plan_create_request
        assert request.product_id == "prod_123"
        assert request.name == "Test Plan"
        assert request.billing_cycle == BillingCycle.MONTHLY
        assert request.price == Decimal("29.99")

    def test_plan_create_request_validation(self):
        """Test subscription plan creation request validation."""
        # Test invalid price
        with pytest.raises(ValidationError):
            SubscriptionPlanCreateRequest(
                product_id="prod_123",
                name="Test Plan",
                billing_cycle=BillingCycle.MONTHLY,
                price=Decimal("-10"),  # Invalid negative price
            )

        # Test invalid setup fee
        with pytest.raises(ValidationError):
            SubscriptionPlanCreateRequest(
                product_id="prod_123",
                name="Test Plan",
                billing_cycle=BillingCycle.MONTHLY,
                price=Decimal("10"),
                setup_fee=Decimal("-5"),  # Invalid negative setup fee
            )

    def test_plan_create_request_defaults(self):
        """Test subscription plan creation request defaults."""
        request = SubscriptionPlanCreateRequest(
            product_id="prod_123",
            name="Test Plan",
            billing_cycle=BillingCycle.MONTHLY,
            price=Decimal("29.99"),
        )

        assert request.description is None
        assert request.currency == "USD"
        assert request.setup_fee is None
        assert request.trial_days is None
        assert request.included_usage == {}
        assert request.overage_rates == {}
        assert request.metadata == {}


class TestSubscriptionCreateRequest:
    """Test SubscriptionCreateRequest model."""

    def test_valid_subscription_create_request(self, subscription_create_request):
        """Test valid subscription creation request."""
        request = subscription_create_request
        assert request.customer_id == "customer-456"
        assert request.plan_id == "plan_123"
        assert request.metadata == {"source": "api"}

    def test_subscription_create_request_validation(self):
        """Test subscription creation request validation."""
        # Test invalid custom price
        with pytest.raises(ValidationError):
            SubscriptionCreateRequest(
                customer_id="customer-456",
                plan_id="plan_123",
                custom_price=Decimal("-10"),  # Invalid negative price
            )

    def test_subscription_create_request_defaults(self):
        """Test subscription creation request defaults."""
        request = SubscriptionCreateRequest(
            customer_id="customer-456",
            plan_id="plan_123",
        )

        assert request.start_date is None
        assert request.custom_price is None
        assert request.trial_end_override is None
        assert request.metadata == {}


class TestSubscriptionUpdateRequest:
    """Test SubscriptionUpdateRequest model."""

    def test_valid_subscription_update_request(self):
        """Test valid subscription update request."""
        request = SubscriptionUpdateRequest(
            custom_price=Decimal("49.99"),
            metadata={"updated": True},
        )

        assert request.custom_price == Decimal("49.99")
        assert request.metadata == {"updated": True}

    def test_subscription_update_request_validation(self):
        """Test subscription update request validation."""
        # Test invalid custom price
        with pytest.raises(ValidationError):
            SubscriptionUpdateRequest(
                custom_price=Decimal("-10"),  # Invalid negative price
            )

    def test_subscription_update_request_defaults(self):
        """Test subscription update request defaults."""
        request = SubscriptionUpdateRequest()

        assert request.custom_price is None
        assert request.metadata is None


class TestSubscriptionPlanChangeRequest:
    """Test SubscriptionPlanChangeRequest model."""

    def test_valid_plan_change_request(self):
        """Test valid subscription plan change request."""
        request = SubscriptionPlanChangeRequest(
            new_plan_id="plan_new",
            proration_behavior=ProrationBehavior.CREATE_PRORATIONS,
            effective_date=datetime.now(UTC),
        )

        assert request.new_plan_id == "plan_new"
        assert request.proration_behavior == ProrationBehavior.CREATE_PRORATIONS

    def test_plan_change_request_defaults(self):
        """Test subscription plan change request defaults."""
        request = SubscriptionPlanChangeRequest(new_plan_id="plan_new")

        assert request.proration_behavior == ProrationBehavior.CREATE_PRORATIONS
        assert request.effective_date is None


class TestUsageRecordRequest:
    """Test UsageRecordRequest model."""

    def test_valid_usage_record_request(self):
        """Test valid usage record request."""
        request = UsageRecordRequest(
            subscription_id="sub_123",
            usage_type="api_calls",
            quantity=1000,
            timestamp=datetime.now(UTC),
        )

        assert request.subscription_id == "sub_123"
        assert request.usage_type == "api_calls"
        assert request.quantity == 1000

    def test_usage_record_request_validation(self):
        """Test usage record request validation."""
        # Test negative quantity
        with pytest.raises(ValidationError):
            UsageRecordRequest(
                subscription_id="sub_123",
                usage_type="api_calls",
                quantity=-10,  # Invalid negative quantity
            )

    def test_usage_record_request_defaults(self):
        """Test usage record request defaults."""
        request = UsageRecordRequest(
            subscription_id="sub_123",
            usage_type="api_calls",
            quantity=1000,
        )

        assert request.timestamp is None


class TestProrationResult:
    """Test ProrationResult model."""

    def test_valid_proration_result(self):
        """Test valid proration result."""
        result = ProrationResult(
            proration_amount=Decimal("15.50"),
            proration_description="Prorated charge for plan change",
            old_plan_unused_amount=Decimal("20.00"),
            new_plan_prorated_amount=Decimal("35.50"),
            days_remaining=15,
        )

        assert result.proration_amount == Decimal("15.50")
        assert result.days_remaining == 15

    def test_proration_result_json_encoders(self):
        """Test proration result JSON serialization."""
        result = ProrationResult(
            proration_amount=Decimal("15.50"),
            proration_description="Test proration",
            old_plan_unused_amount=Decimal("20.00"),
            new_plan_prorated_amount=Decimal("35.50"),
            days_remaining=15,
        )

        result_dict = result.model_dump()

        # Decimal should be converted to string
        assert isinstance(result_dict["proration_amount"], str)
        assert isinstance(result_dict["old_plan_unused_amount"], str)
        assert isinstance(result_dict["new_plan_prorated_amount"], str)


class TestSubscriptionResponse:
    """Test SubscriptionResponse model."""

    def test_subscription_response_creation(self):
        """Test subscription response model creation."""
        now = datetime.now(UTC)
        response = SubscriptionResponse(
            subscription_id="sub_123",
            tenant_id="test-tenant",
            customer_id="customer-456",
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
            is_in_trial=True,
            days_until_renewal=30,
        )

        assert response.subscription_id == "sub_123"
        assert response.status == SubscriptionStatus.ACTIVE
        assert response.is_in_trial is True
        assert response.days_until_renewal == 30

    def test_subscription_response_json_encoders(self):
        """Test subscription response JSON serialization."""
        now = datetime.now(UTC)
        response = SubscriptionResponse(
            subscription_id="sub_123",
            tenant_id="test-tenant",
            customer_id="customer-456",
            plan_id="plan_123",
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            status=SubscriptionStatus.ACTIVE,
            trial_end=None,
            cancel_at_period_end=False,
            canceled_at=None,
            ended_at=None,
            custom_price=Decimal("99.99"),
            usage_records={},
            metadata={},
            created_at=now,
            updated_at=None,
            is_in_trial=False,
            days_until_renewal=30,
        )

        response_dict = response.model_dump()

        # Check JSON encoding
        assert isinstance(response_dict["current_period_start"], str)
        assert isinstance(response_dict["created_at"], str)
        assert isinstance(response_dict["custom_price"], str)


class TestSubscriptionPlanResponse:
    """Test SubscriptionPlanResponse model."""

    def test_subscription_plan_response_creation(self):
        """Test subscription plan response model creation."""
        now = datetime.now(UTC)
        response = SubscriptionPlanResponse(
            plan_id="plan_123",
            tenant_id="test-tenant",
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
            metadata={"tier": "professional"},
            created_at=now,
            updated_at=None,
        )

        assert response.plan_id == "plan_123"
        assert response.billing_cycle == BillingCycle.MONTHLY
        assert response.price == Decimal("99.99")

    def test_subscription_plan_response_json_encoders(self):
        """Test subscription plan response JSON serialization."""
        now = datetime.now(UTC)
        response = SubscriptionPlanResponse(
            plan_id="plan_123",
            tenant_id="test-tenant",
            product_id="prod_123",
            name="Pro Plan",
            description="Professional plan",
            billing_cycle=BillingCycle.MONTHLY,
            price=Decimal("99.99"),
            currency="USD",
            setup_fee=None,
            trial_days=None,
            included_usage={},
            overage_rates={"api_calls": Decimal("0.001")},
            is_active=True,
            metadata={},
            created_at=now,
            updated_at=None,
        )

        response_dict = response.model_dump()

        # Check JSON encoding
        assert isinstance(response_dict["price"], str)
        assert isinstance(response_dict["created_at"], str)
        assert isinstance(response_dict["overage_rates"]["api_calls"], str)
