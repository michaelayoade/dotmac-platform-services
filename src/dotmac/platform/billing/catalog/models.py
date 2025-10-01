"""
Product catalog models for billing system.

Simple, flat product structure with categories and usage-based billing support.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, field_validator, ConfigDict

from dotmac.platform.billing.models import BillingBaseModel


class ProductType(str, Enum):
    """Product type determines billing behavior."""

    ONE_TIME = "one_time"           # Single purchase
    SUBSCRIPTION = "subscription"    # Recurring billing
    USAGE_BASED = "usage_based"     # Metered usage only
    HYBRID = "hybrid"               # Subscription + usage


class UsageType(str, Enum):
    """Types of usage that can be measured."""

    API_CALLS = "api_calls"
    STORAGE_GB = "storage_gb"
    BANDWIDTH_GB = "bandwidth_gb"
    USERS = "users"
    TRANSACTIONS = "transactions"
    COMPUTE_HOURS = "compute_hours"
    CUSTOM = "custom"


class TaxClass(str, Enum):
    """Tax classification for products."""

    STANDARD = "standard"              # Standard tax rate
    REDUCED = "reduced"                # Reduced tax rate
    EXEMPT = "exempt"                  # Tax exempt
    ZERO_RATED = "zero_rated"         # Zero tax rate
    DIGITAL_SERVICES = "digital_services"  # Digital services tax


class ProductCategory(BillingBaseModel):
    """Simple flat product categories."""

    category_id: str = Field(description="Category identifier")
    name: str = Field(description="Category name", max_length=100)
    description: Optional[str] = Field(None, description="Category description")

    # Tax defaults for category
    default_tax_class: TaxClass = Field(
        default=TaxClass.STANDARD,
        description="Default tax class for products in this category"
    )

    # Display order
    sort_order: int = Field(default=0, description="Display sort order")

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
        }
    )


class Product(BillingBaseModel):
    """Core product model - simple and flexible."""

    product_id: str = Field(description="Unique product identifier")
    sku: str = Field(description="Stock keeping unit", max_length=100)
    name: str = Field(description="Product name", max_length=255)
    description: Optional[str] = Field(None, description="Product description")

    # Categorization - simple flat structure
    category: str = Field(description="Product category name", max_length=100)

    # Product type determines billing behavior
    product_type: ProductType = Field(description="How this product is billed")

    # Pricing - single base price
    base_price: Decimal = Field(description="Base price in minor units (e.g., cents)")
    currency: str = Field(default="USD", description="Price currency", max_length=3)

    # Tax handling
    tax_class: TaxClass = Field(default=TaxClass.STANDARD, description="Tax classification")

    # Usage-based billing configuration
    usage_type: Optional[UsageType] = Field(
        None,
        description="Type of usage measured (for usage-based products)"
    )
    usage_unit_name: Optional[str] = Field(
        None,
        description="Display name for usage unit (e.g., 'API Calls', 'GB Storage')",
        max_length=50
    )

    # Product status
    is_active: bool = Field(default=True, description="Product is available for sale")

    # Flexible metadata for custom attributes
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Custom metadata for product-specific attributes"
    )

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: str(v),
        }
    )

    @field_validator("base_price")
    @classmethod
    def validate_base_price(cls, v: Decimal) -> Decimal:
        """Ensure base price is non-negative."""
        if v < 0:
            raise ValueError("Base price cannot be negative")
        return v

    @field_validator("sku")
    @classmethod
    def validate_sku(cls, v: str) -> str:
        """Ensure SKU is not empty and properly formatted."""
        if not v or not v.strip():
            raise ValueError("SKU cannot be empty")
        # Convert to uppercase and remove extra whitespace
        return v.strip().upper()

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Ensure currency is a valid 3-letter code."""
        if len(v) != 3:
            raise ValueError("Currency must be a 3-letter code")
        return v.upper()

    def is_usage_based(self) -> bool:
        """Check if product supports usage-based billing."""
        return self.product_type in [ProductType.USAGE_BASED, ProductType.HYBRID]

    def requires_usage_tracking(self) -> bool:
        """Check if product requires usage tracking."""
        return self.is_usage_based() and self.usage_type is not None


# Request/Response Models

class ProductCategoryCreateRequest(BaseModel):
    """Request model for creating product categories."""

    name: str = Field(description="Category name", max_length=100)
    description: Optional[str] = Field(None, description="Category description")
    default_tax_class: TaxClass = Field(default=TaxClass.STANDARD)
    sort_order: int = Field(default=0)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensure category name is not empty."""
        if not v or not v.strip():
            raise ValueError("Category name cannot be empty")
        return v.strip()


class ProductCreateRequest(BaseModel):
    """Request model for creating products."""

    sku: str = Field(description="Stock keeping unit", max_length=100)
    name: str = Field(description="Product name", max_length=255)
    description: Optional[str] = Field(None, description="Product description")
    category: str = Field(description="Product category", max_length=100)
    product_type: ProductType = Field(description="Product type")
    base_price: Decimal = Field(description="Base price in minor units")
    currency: str = Field(default="USD", max_length=3)
    tax_class: TaxClass = Field(default=TaxClass.STANDARD)
    usage_type: Optional[UsageType] = Field(None)
    usage_unit_name: Optional[str] = Field(None, max_length=50)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("base_price")
    @classmethod
    def validate_base_price(cls, v: Decimal) -> Decimal:
        """Ensure base price is non-negative."""
        if v < 0:
            raise ValueError("Base price cannot be negative")
        return v


class ProductUpdateRequest(BaseModel):
    """Request model for updating products."""

    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    base_price: Optional[Decimal] = None
    tax_class: Optional[TaxClass] = None
    usage_unit_name: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None

    @field_validator("base_price")
    @classmethod
    def validate_base_price(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Ensure base price is non-negative if provided."""
        if v is not None and v < 0:
            raise ValueError("Base price cannot be negative")
        return v


class ProductFilters(BaseModel):
    """Filter options for product listings."""

    category: Optional[str] = Field(None, description="Filter by category")
    product_type: Optional[ProductType] = Field(None, description="Filter by product type")
    is_active: bool = Field(default=True, description="Filter by active status")
    usage_type: Optional[UsageType] = Field(None, description="Filter by usage type")
    search: Optional[str] = Field(None, description="Search in name and description")


class ProductResponse(BaseModel):
    """Response model for product data."""

    product_id: str
    tenant_id: str
    sku: str
    name: str
    description: Optional[str]
    category: str
    product_type: ProductType
    base_price: Decimal
    currency: str
    tax_class: TaxClass
    usage_type: Optional[UsageType]
    usage_unit_name: Optional[str]
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


class ProductCategoryResponse(BaseModel):
    """Response model for product category data."""

    category_id: str
    tenant_id: str
    name: str
    description: Optional[str]
    default_tax_class: TaxClass
    sort_order: int
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
        }
    )