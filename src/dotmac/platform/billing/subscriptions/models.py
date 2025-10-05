"""
Subscription models for billing system.

Simple subscription plans and customer subscriptions with clear lifecycle management.
"""

from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from dotmac.platform.billing.models import BillingBaseModel


class BillingCycle(str, Enum):
    """Subscription billing cycles."""

    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


class SubscriptionStatus(str, Enum):
    """Subscription status values."""

    INCOMPLETE = "incomplete"  # Payment method setup pending
    TRIALING = "trialing"  # In trial period
    ACTIVE = "active"  # Active subscription
    PAST_DUE = "past_due"  # Payment failed, retrying
    CANCELED = "canceled"  # Canceled, still active until period end
    ENDED = "ended"  # Fully terminated
    PAUSED = "paused"  # Temporarily suspended


class SubscriptionEventType(str, Enum):
    """Subscription lifecycle events."""

    CREATED = "subscription.created"
    ACTIVATED = "subscription.activated"
    TRIAL_STARTED = "subscription.trial_started"
    TRIAL_ENDED = "subscription.trial_ended"
    RENEWED = "subscription.renewed"
    PLAN_CHANGED = "subscription.plan_changed"
    CANCELED = "subscription.canceled"
    PAUSED = "subscription.paused"
    RESUMED = "subscription.resumed"
    ENDED = "subscription.ended"
    PAYMENT_FAILED = "subscription.payment_failed"
    PAYMENT_SUCCEEDED = "subscription.payment_succeeded"


class ProrationBehavior(str, Enum):
    """How to handle mid-cycle plan changes."""

    NONE = "none"  # No proration, change at next cycle
    CREATE_PRORATIONS = "prorate"  # Create prorated charges/credits


class SubscriptionPlan(BillingBaseModel):
    """Subscription plan definition."""

    plan_id: str = Field(description="Plan identifier")
    product_id: str = Field(description="Associated product")

    # Plan details
    name: str = Field(description="Plan name", max_length=255)
    description: str | None = Field(None, description="Plan description")

    # Billing configuration
    billing_cycle: BillingCycle = Field(description="How often to bill")
    price: Decimal = Field(description="Plan price in minor units")
    currency: str = Field(default="USD", description="Price currency", max_length=3)
    setup_fee: Decimal | None = Field(None, description="One-time setup fee")

    # Trial configuration
    trial_days: int | None = Field(None, description="Free trial period days")

    # Usage allowances for hybrid plans
    included_usage: dict[str, int] = Field(
        default_factory=dict, description="Included usage quotas (e.g., {'api_calls': 1000})"
    )
    overage_rates: dict[str, Decimal] = Field(
        default_factory=dict, description="Per-unit overage pricing (e.g., {'api_calls': '0.01'})"
    )

    # Plan status
    is_active: bool = Field(default=True, description="Plan is available for signup")

    # Flexible metadata
    metadata: dict[str, Any] = Field(default_factory=dict, description="Custom metadata")

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: str(v),
        }
    )

    @field_validator("price", "setup_fee")
    @classmethod
    def validate_prices(cls, v: Decimal | None) -> Decimal | None:
        """Ensure prices are non-negative."""
        if v is not None and v < 0:
            raise ValueError("Price cannot be negative")
        return v

    @field_validator("trial_days")
    @classmethod
    def validate_trial_days(cls, v: int | None) -> int | None:
        """Ensure trial days is reasonable."""
        if v is not None and (v < 0 or v > 365):
            raise ValueError("Trial days must be between 0 and 365")
        return v

    def has_trial(self) -> bool:
        """Check if plan includes a trial period."""
        return self.trial_days is not None and self.trial_days > 0

    def has_setup_fee(self) -> bool:
        """Check if plan has a setup fee."""
        return self.setup_fee is not None and self.setup_fee > 0

    def supports_usage_billing(self) -> bool:
        """Check if plan supports usage-based billing."""
        return bool(self.included_usage or self.overage_rates)


class Subscription(BillingBaseModel):
    """Customer subscription instance."""

    subscription_id: str = Field(description="Subscription identifier")
    customer_id: str = Field(description="Customer who owns subscription")
    plan_id: str = Field(description="Current subscription plan")

    # Current billing period
    current_period_start: datetime = Field(description="Current billing period start")
    current_period_end: datetime = Field(description="Current billing period end")

    # Subscription status and lifecycle
    status: SubscriptionStatus = Field(description="Current subscription status")

    # Trial information
    trial_end: datetime | None = Field(None, description="Trial period end")

    # Cancellation handling
    cancel_at_period_end: bool = Field(default=False, description="Cancel at current period end")
    canceled_at: datetime | None = Field(None, description="When subscription was canceled")
    ended_at: datetime | None = Field(None, description="When subscription fully ended")

    # Pricing overrides
    custom_price: Decimal | None = Field(None, description="Customer-specific pricing override")

    # Usage tracking for hybrid plans
    usage_records: dict[str, int] = Field(
        default_factory=dict, description="Current period usage tracking"
    )

    # Flexible metadata
    metadata: dict[str, Any] = Field(default_factory=dict, description="Custom metadata")

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: str(v),
        }
    )

    def is_active(self) -> bool:
        """Check if subscription is currently active."""
        return self.status in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING]

    def is_in_trial(self) -> bool:
        """Check if subscription is in trial period."""
        if not self.trial_end:
            return False
        return datetime.now(UTC) < self.trial_end

    def days_until_renewal(self) -> int:
        """Get days until next renewal."""
        if not self.is_active():
            return 0
        delta = self.current_period_end - datetime.now(UTC)
        return max(0, delta.days)

    def is_past_due(self) -> bool:
        """Check if subscription is past due."""
        return self.status == SubscriptionStatus.PAST_DUE


class SubscriptionEvent(BillingBaseModel):
    """Subscription lifecycle event for audit trail."""

    event_id: str = Field(description="Event identifier")
    subscription_id: str = Field(description="Related subscription")

    event_type: SubscriptionEventType = Field(description="Type of event")
    event_data: dict[str, Any] = Field(default_factory=dict, description="Event-specific data")

    # User who triggered event (optional for system events)
    user_id: str | None = Field(None, description="User who triggered event")

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
        }
    )


# Request/Response Models


class SubscriptionPlanCreateRequest(BaseModel):
    """Request model for creating subscription plans."""

    product_id: str = Field(description="Associated product ID")
    name: str = Field(description="Plan name", max_length=255)
    description: str | None = Field(None, description="Plan description")
    billing_cycle: BillingCycle = Field(description="Billing frequency")
    price: Decimal = Field(description="Plan price in minor units")
    currency: str = Field(default="USD", max_length=3)
    setup_fee: Decimal | None = Field(None, description="One-time setup fee")
    trial_days: int | None = Field(None, description="Trial period days")
    included_usage: dict[str, int] = Field(default_factory=dict)
    overage_rates: dict[str, Decimal] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("price", "setup_fee")
    @classmethod
    def validate_prices(cls, v: Decimal | None) -> Decimal | None:
        """Ensure prices are non-negative."""
        if v is not None and v < 0:
            raise ValueError("Price cannot be negative")
        return v


class SubscriptionCreateRequest(BaseModel):
    """Request model for creating subscriptions."""

    customer_id: str = Field(description="Customer ID")
    plan_id: str = Field(description="Subscription plan ID")
    start_date: datetime | None = Field(None, description="Subscription start date")
    custom_price: Decimal | None = Field(None, description="Customer-specific pricing")
    trial_end_override: datetime | None = Field(None, description="Override trial end date")
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("custom_price")
    @classmethod
    def validate_custom_price(cls, v: Decimal | None) -> Decimal | None:
        """Ensure custom price is non-negative."""
        if v is not None and v < 0:
            raise ValueError("Custom price cannot be negative")
        return v


class SubscriptionUpdateRequest(BaseModel):
    """Request model for updating subscriptions."""

    custom_price: Decimal | None = Field(None, description="Update custom pricing")
    metadata: dict[str, Any] | None = Field(None, description="Update metadata")

    @field_validator("custom_price")
    @classmethod
    def validate_custom_price(cls, v: Decimal | None) -> Decimal | None:
        """Ensure custom price is non-negative."""
        if v is not None and v < 0:
            raise ValueError("Custom price cannot be negative")
        return v


class SubscriptionPlanChangeRequest(BaseModel):
    """Request model for changing subscription plans."""

    new_plan_id: str = Field(description="New plan to switch to")
    proration_behavior: ProrationBehavior = Field(
        default=ProrationBehavior.CREATE_PRORATIONS, description="How to handle proration"
    )
    effective_date: datetime | None = Field(
        None, description="When to make the change (default: immediate)"
    )


class UsageRecordRequest(BaseModel):
    """Request model for recording usage."""

    subscription_id: str = Field(description="Subscription ID")
    usage_type: str = Field(description="Type of usage (api_calls, storage_gb, etc.)")
    quantity: int = Field(description="Usage quantity", ge=0)
    timestamp: datetime | None = Field(None, description="Usage timestamp (default: now)")


class SubscriptionResponse(BaseModel):
    """Response model for subscription data."""

    subscription_id: str
    tenant_id: str
    customer_id: str
    plan_id: str
    current_period_start: datetime
    current_period_end: datetime
    status: SubscriptionStatus
    trial_end: datetime | None
    cancel_at_period_end: bool
    canceled_at: datetime | None
    ended_at: datetime | None
    custom_price: Decimal | None
    usage_records: dict[str, int]
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime | None

    # Computed fields
    is_in_trial: bool
    days_until_renewal: int

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: str(v),
        }
    )


class SubscriptionPlanResponse(BaseModel):
    """Response model for subscription plan data."""

    plan_id: str
    tenant_id: str
    product_id: str
    name: str
    description: str | None
    billing_cycle: BillingCycle
    price: Decimal
    currency: str
    setup_fee: Decimal | None
    trial_days: int | None
    included_usage: dict[str, int]
    overage_rates: dict[str, Decimal]
    is_active: bool
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime | None

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: str(v),
        }
    )


class ProrationResult(BaseModel):
    """Result of proration calculation."""

    proration_amount: Decimal = Field(
        description="Proration amount (positive = charge, negative = credit)"
    )
    proration_description: str = Field(description="Human-readable description")
    old_plan_unused_amount: Decimal = Field(description="Unused amount from old plan")
    new_plan_prorated_amount: Decimal = Field(description="Prorated amount for new plan")
    days_remaining: int = Field(description="Days remaining in current period")

    model_config = ConfigDict(
        json_encoders={
            Decimal: lambda v: str(v),
        }
    )
