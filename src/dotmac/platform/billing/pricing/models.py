"""
Pricing engine models.

Simple pricing rules with clear application logic.
"""

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, ConfigDict

from dotmac.platform.billing.models import BillingBaseModel


class DiscountType(str, Enum):
    """Types of discounts that can be applied."""

    PERCENTAGE = "percentage"         # 10% off
    FIXED_AMOUNT = "fixed_amount"    # $10 off
    FIXED_PRICE = "fixed_price"      # Set price to $50


class PricingRule(BillingBaseModel):
    """Simple pricing rule with clear conditions."""

    rule_id: str = Field(description="Rule identifier")
    name: str = Field(description="Rule name", max_length=255)
    description: Optional[str] = Field(None, description="Rule description")

    # What does this rule apply to?
    applies_to_product_ids: List[str] = Field(
        default_factory=list,
        description="Specific products this rule applies to"
    )
    applies_to_categories: List[str] = Field(
        default_factory=list,
        description="Product categories this rule applies to"
    )
    applies_to_all: bool = Field(default=False, description="Apply to all products")

    # Simple conditions
    min_quantity: Optional[int] = Field(None, description="Minimum quantity required")
    customer_segments: List[str] = Field(
        default_factory=list,
        description="Customer types/segments this applies to"
    )

    # Discount configuration
    discount_type: DiscountType = Field(description="How to apply discount")
    discount_value: Decimal = Field(description="Discount amount or percentage")

    # Time constraints
    starts_at: Optional[datetime] = Field(None, description="Rule starts at this time")
    ends_at: Optional[datetime] = Field(None, description="Rule ends at this time")

    # Usage limits
    max_uses: Optional[int] = Field(None, description="Maximum times rule can be used")
    current_uses: int = Field(default=0, description="Current usage count")

    # Rule priority (higher number = higher priority)
    priority: int = Field(default=0, description="Rule priority for conflict resolution")

    # Status
    is_active: bool = Field(default=True, description="Rule is active")

    # Flexible metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata")

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: str(v),
        }
    )

    @field_validator("discount_value")
    @classmethod
    def validate_discount_value(cls, v: Decimal, info) -> Decimal:
        """Validate discount value based on discount type."""
        if v < 0:
            raise ValueError("Discount value cannot be negative")

        # Additional validation based on discount type would need the discount_type field
        # For now, just ensure it's non-negative
        return v

    @field_validator("min_quantity")
    @classmethod
    def validate_min_quantity(cls, v: Optional[int]) -> Optional[int]:
        """Ensure minimum quantity is positive."""
        if v is not None and v <= 0:
            raise ValueError("Minimum quantity must be positive")
        return v

    @field_validator("max_uses")
    @classmethod
    def validate_max_uses(cls, v: Optional[int]) -> Optional[int]:
        """Ensure max uses is positive."""
        if v is not None and v <= 0:
            raise ValueError("Max uses must be positive")
        return v

    def is_currently_active(self) -> bool:
        """Check if rule is active and within time constraints."""
        if not self.is_active:
            return False

        now = datetime.now(timezone.utc)

        if self.starts_at and now < self.starts_at:
            return False

        if self.ends_at and now > self.ends_at:
            return False

        return True

    def has_usage_remaining(self) -> bool:
        """Check if rule has usage remaining."""
        if self.max_uses is None:
            return True

        return self.current_uses < self.max_uses

    def can_be_applied(self, quantity: int = 1) -> bool:
        """Check if rule can be applied given quantity and usage constraints."""
        if not self.is_currently_active():
            return False

        if not self.has_usage_remaining():
            return False

        if self.min_quantity and quantity < self.min_quantity:
            return False

        return True


class PriceCalculationContext(BaseModel):
    """Context for price calculations."""

    product_id: str = Field(description="Product being priced")
    quantity: int = Field(description="Quantity being purchased", ge=1)
    customer_id: str = Field(description="Customer making purchase")
    customer_segments: List[str] = Field(
        default_factory=list,
        description="Customer segments/types"
    )

    # Product context
    product_category: Optional[str] = Field(None, description="Product category")
    base_price: Decimal = Field(description="Product base price")

    # Additional context
    calculation_date: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When calculation is performed"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context data"
    )

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: str(v),
        }
    )


class PriceAdjustment(BaseModel):
    """Result of applying a pricing rule."""

    rule_id: str = Field(description="Rule that was applied")
    rule_name: str = Field(description="Rule name")
    discount_type: DiscountType = Field(description="Type of discount applied")
    discount_value: Decimal = Field(description="Original discount value from rule")

    # Calculation results
    original_price: Decimal = Field(description="Price before this rule")
    discount_amount: Decimal = Field(description="Actual discount amount")
    adjusted_price: Decimal = Field(description="Price after this rule")

    model_config = ConfigDict(
        json_encoders={
            Decimal: lambda v: str(v),
        }
    )


class PriceCalculationResult(BaseModel):
    """Complete result of price calculation."""

    # Input context
    product_id: str
    quantity: int
    customer_id: str

    # Price breakdown
    base_price: Decimal = Field(description="Base price per unit")
    subtotal: Decimal = Field(description="Base price * quantity")
    total_discount_amount: Decimal = Field(description="Total discount applied")
    final_price: Decimal = Field(description="Final price after all discounts")

    # Applied adjustments (in order)
    applied_adjustments: List[PriceAdjustment] = Field(
        default_factory=list,
        description="Price adjustments applied"
    )

    # Calculation metadata
    calculation_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When calculation was performed"
    )

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: str(v),
        }
    )

    def get_savings_percentage(self) -> Decimal:
        """Calculate percentage savings."""
        if self.subtotal == 0:
            return Decimal("0")

        return (self.total_discount_amount / self.subtotal) * 100


# Request/Response Models

class PricingRuleCreateRequest(BaseModel):
    """Request model for creating pricing rules."""

    name: str = Field(description="Rule name", max_length=255)
    description: Optional[str] = Field(None, description="Rule description")

    applies_to_product_ids: List[str] = Field(default_factory=list)
    applies_to_categories: List[str] = Field(default_factory=list)
    applies_to_all: bool = Field(default=False)

    min_quantity: Optional[int] = Field(None, ge=1)
    customer_segments: List[str] = Field(default_factory=list)

    discount_type: DiscountType
    discount_value: Decimal = Field(ge=0)

    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    max_uses: Optional[int] = Field(None, ge=1)
    priority: int = Field(default=0)

    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("ends_at")
    @classmethod
    def validate_end_date(cls, v: Optional[datetime], info) -> Optional[datetime]:
        """Ensure end date is after start date."""
        if v and info.data.get("starts_at") and v <= info.data["starts_at"]:
            raise ValueError("End date must be after start date")
        return v


class PricingRuleUpdateRequest(BaseModel):
    """Request model for updating pricing rules."""

    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    discount_value: Optional[Decimal] = Field(None, ge=0)
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    max_uses: Optional[int] = Field(None, ge=1)
    priority: Optional[int] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class PriceCalculationRequest(BaseModel):
    """Request model for price calculations."""

    product_id: str = Field(description="Product to calculate price for")
    quantity: int = Field(description="Quantity", ge=1)
    customer_id: str = Field(description="Customer ID")
    customer_segments: List[str] = Field(
        default_factory=list,
        description="Customer segments for rule matching"
    )

    # Optional context
    calculation_date: Optional[datetime] = Field(
        None,
        description="Date to calculate price for (default: now)"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PricingRuleResponse(BaseModel):
    """Response model for pricing rule data."""

    rule_id: str
    tenant_id: str
    name: str
    description: Optional[str]
    applies_to_product_ids: List[str]
    applies_to_categories: List[str]
    applies_to_all: bool
    min_quantity: Optional[int]
    customer_segments: List[str]
    discount_type: DiscountType
    discount_value: Decimal
    starts_at: Optional[datetime]
    ends_at: Optional[datetime]
    max_uses: Optional[int]
    current_uses: int
    priority: int
    is_active: bool
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: str(v),
        }
    )