"""
Base billing models and database tables.

Provides foundation for all billing system components.
"""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import JSON, Boolean, Column, DateTime, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from dotmac.platform.db import BaseModel as SQLBaseModel


class BillingBaseModel(BaseModel):
    """Base model for all billing entities with common fields."""

    tenant_id: str = Field(description="Tenant identifier for multi-tenancy")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Creation timestamp"
    )
    updated_at: datetime | None = Field(None, description="Last update timestamp")

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
        }
    )


class BillingSQLModel(SQLBaseModel):
    """Base SQLAlchemy model for billing tables."""

    __abstract__ = True

    tenant_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, onupdate=lambda: datetime.now(UTC)
    )
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, nullable=False, default=dict
    )


class BillingProductTable(BillingSQLModel):
    """SQLAlchemy table for billing products."""

    __tablename__ = "billing_products"

    # Primary key
    product_id = Column(String(50), primary_key=True)

    # Product identification
    sku = Column(String(100), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Categorization
    category = Column(String(100), nullable=False)

    # Product type and pricing
    product_type = Column(String(20), nullable=False)  # one_time, subscription, usage_based, hybrid
    base_price = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")

    # Tax classification
    tax_class = Column(String(20), nullable=False, default="standard")

    # Usage-based configuration
    usage_type = Column(String(50), nullable=True)
    usage_unit_name = Column(String(50), nullable=True)

    # Status
    is_active = Column(Boolean, nullable=False, default=True)

    # Indexes for performance
    __table_args__ = (
        Index("ix_billing_products_tenant_sku", "tenant_id", "sku", unique=True),
        Index("ix_billing_products_tenant_category", "tenant_id", "category"),
        Index("ix_billing_products_tenant_type", "tenant_id", "product_type"),
        Index("ix_billing_products_tenant_active", "tenant_id", "is_active"),
        {"extend_existing": True},
    )


class BillingProductCategoryTable(BillingSQLModel):
    """SQLAlchemy table for product categories."""

    __tablename__ = "billing_product_categories"

    # Primary key
    category_id = Column(String(50), primary_key=True)

    # Category details
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    # Tax defaults
    default_tax_class = Column(String(20), nullable=False, default="standard")

    # Display order
    sort_order = Column(Numeric(10, 0), nullable=False, default=0)

    # Indexes
    __table_args__ = (
        Index("ix_billing_categories_tenant_name", "tenant_id", "name", unique=True),
        Index("ix_billing_categories_sort", "tenant_id", "sort_order"),
        {"extend_existing": True},
    )


class BillingSubscriptionPlanTable(BillingSQLModel):
    """SQLAlchemy table for subscription plans."""

    __tablename__ = "billing_subscription_plans"

    # Primary key
    plan_id = Column(String(50), primary_key=True)

    # Associated product
    product_id = Column(String(50), nullable=False)

    # Plan details
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Billing configuration
    billing_cycle = Column(String(20), nullable=False)  # monthly, quarterly, annual
    price = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    setup_fee = Column(Numeric(15, 2), nullable=True)

    # Trial configuration
    trial_days = Column(Numeric(10, 0), nullable=True)

    # Usage allowances (JSON)
    included_usage = Column(JSON, nullable=False, default=dict)
    overage_rates = Column(JSON, nullable=False, default=dict)

    # Status
    is_active = Column(Boolean, nullable=False, default=True)

    # Indexes
    __table_args__ = (
        Index("ix_billing_plans_tenant_product", "tenant_id", "product_id"),
        Index("ix_billing_plans_tenant_active", "tenant_id", "is_active"),
        {"extend_existing": True},
    )


class BillingSubscriptionTable(BillingSQLModel):
    """SQLAlchemy table for customer subscriptions."""

    __tablename__ = "billing_subscriptions"

    # Primary key
    subscription_id = Column(String(50), primary_key=True)

    # Customer and plan references
    customer_id = Column(String(50), nullable=False)
    plan_id = Column(String(50), nullable=False)

    # Current billing period
    current_period_start = Column(DateTime(timezone=True), nullable=False)
    current_period_end = Column(DateTime(timezone=True), nullable=False)

    # Status
    status = Column(String(20), nullable=False)  # trial, active, past_due, canceled, ended

    # Trial information
    trial_end = Column(DateTime(timezone=True), nullable=True)

    # Cancellation
    cancel_at_period_end = Column(Boolean, nullable=False, default=False)
    canceled_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)

    # Pricing overrides
    custom_price = Column(Numeric(15, 2), nullable=True)

    # Usage tracking (JSON)
    usage_records = Column(JSON, nullable=False, default=dict)

    # Indexes
    __table_args__ = (
        Index("ix_billing_subscriptions_tenant_customer", "tenant_id", "customer_id"),
        Index("ix_billing_subscriptions_tenant_plan", "tenant_id", "plan_id"),
        Index("ix_billing_subscriptions_tenant_status", "tenant_id", "status"),
        Index("ix_billing_subscriptions_period_end", "current_period_end"),
        {"extend_existing": True},
    )


class BillingSubscriptionEventTable(BillingSQLModel):
    """SQLAlchemy table for subscription events (audit trail)."""

    __tablename__ = "billing_subscription_events"

    # Primary key
    event_id = Column(String(50), primary_key=True)

    # Related subscription
    subscription_id = Column(String(50), nullable=False)

    # Event details
    event_type = Column(String(50), nullable=False)
    event_data = Column(JSON, nullable=False, default=dict)

    # User who triggered event
    user_id = Column(String(50), nullable=True)

    # Indexes
    __table_args__ = (
        Index("ix_billing_events_tenant_subscription", "tenant_id", "subscription_id"),
        Index("ix_billing_events_tenant_type", "tenant_id", "event_type"),
        Index("ix_billing_events_created", "created_at"),
        {"extend_existing": True},
    )


class BillingPricingRuleTable(BillingSQLModel):
    """SQLAlchemy table for pricing rules."""

    __tablename__ = "billing_pricing_rules"

    # Primary key
    rule_id = Column(String(50), primary_key=True)

    # Rule details
    name = Column(String(255), nullable=False)

    # Rule targeting (JSON arrays)
    applies_to_product_ids = Column(JSON, nullable=False, default=list)
    applies_to_categories = Column(JSON, nullable=False, default=list)
    applies_to_all = Column(Boolean, nullable=False, default=False)

    # Simple conditions
    min_quantity = Column(Numeric(10, 0), nullable=True)
    customer_segments = Column(JSON, nullable=False, default=list)

    # Discount configuration
    discount_type = Column(String(20), nullable=False)  # percentage, fixed_amount, fixed_price
    discount_value = Column(Numeric(15, 2), nullable=False)

    # Time constraints
    starts_at = Column(DateTime(timezone=True), nullable=True)
    ends_at = Column(DateTime(timezone=True), nullable=True)

    # Usage limits
    max_uses = Column(Numeric(10, 0), nullable=True)
    current_uses = Column(Numeric(10, 0), nullable=False, default=0)

    # Status
    is_active = Column(Boolean, nullable=False, default=True)

    # Indexes
    __table_args__ = (
        Index("ix_billing_rules_tenant_active", "tenant_id", "is_active"),
        Index("ix_billing_rules_starts_ends", "starts_at", "ends_at"),
        {"extend_existing": True},
    )


class BillingRuleUsageTable(BillingSQLModel):
    """SQLAlchemy table for tracking pricing rule usage."""

    __tablename__ = "billing_rule_usage"

    # Primary key
    usage_id = Column(String(50), primary_key=True)

    # References
    rule_id = Column(String(50), nullable=False)
    customer_id = Column(String(50), nullable=False)
    invoice_id = Column(String(50), nullable=True)  # Links to existing invoice system

    # Usage timestamp
    used_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

    # Indexes
    __table_args__ = (
        Index("ix_billing_rule_usage_tenant_rule", "tenant_id", "rule_id"),
        Index("ix_billing_rule_usage_tenant_customer", "tenant_id", "customer_id"),
        Index("ix_billing_rule_usage_used_at", "used_at"),
        {"extend_existing": True},
    )


# Export all tables for Alembic migrations
# Import core billing models for backward compatibility
from dotmac.platform.billing.core.models import (
    Customer,
    Invoice,
    InvoiceItem,
    InvoiceLineItem,
    Payment,
    Price,
    Product,
    Subscription,
)

__all__ = [
    "BillingBaseModel",
    "BillingSQLModel",
    "BillingProductTable",
    "BillingProductCategoryTable",
    "BillingSubscriptionPlanTable",
    "BillingSubscriptionTable",
    "BillingSubscriptionEventTable",
    "BillingPricingRuleTable",
    "BillingRuleUsageTable",
    # Core models
    "Invoice",
    "InvoiceLineItem",
    "Payment",
    "Customer",
    "Subscription",
    "Product",
    "Price",
    "InvoiceItem",
]
