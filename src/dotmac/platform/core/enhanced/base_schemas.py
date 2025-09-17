"""
Common base schemas for DotMac Platform Services.
Provides consistent Pydantic models across all modules.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Generic, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        str_strip_whitespace=True,
        use_enum_values=True,
        arbitrary_types_allowed=True,
    )


class TimestampMixin(BaseSchema):
    """Mixin for entities with timestamp fields."""

    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    deleted_at: Optional[datetime] = Field(None, description="Deletion timestamp")


class AuditMixin(BaseSchema):
    """Mixin for entities with audit fields."""

    created_by: Optional[str] = Field(None, description="User who created the entity")
    updated_by: Optional[str] = Field(None, description="User who last updated the entity")


class TenantMixin(BaseSchema):
    """Mixin for tenant-aware entities."""

    tenant_id: Optional[str] = Field(None, description="Tenant identifier")


class SoftDeleteMixin(BaseSchema):
    """Mixin for entities supporting soft delete."""

    is_deleted: bool = Field(False, description="Soft delete flag")
    deleted_at: Optional[datetime] = Field(None, description="Deletion timestamp")


class EmailMixin(BaseSchema):
    """Mixin that adds normalized e-mail fields."""

    email: str = Field(..., description="Primary email address")
    secondary_email: Optional[str] = Field(None, description="Secondary email address")

    @field_validator("email", "secondary_email")
    @classmethod
    def _normalize_email(cls, value: Optional[str]) -> Optional[str]:
        if not value:
            return value
        normalized = value.strip().lower()
        if "@" not in normalized:
            raise ValueError("Email address must contain '@'")
        return normalized


class PhoneMixin(BaseSchema):
    """Mixin that provides normalized phone number fields."""

    phone: Optional[str] = Field(None, description="Primary phone number")
    phone_country_code: Optional[str] = Field(
        None, description="ISO country code for the phone number"
    )

    @field_validator("phone")
    @classmethod
    def _validate_phone(cls, value: Optional[str]) -> Optional[str]:
        if not value:
            return value
        digits = [c for c in value if c.isdigit()]
        if len(digits) < 7:
            raise ValueError("Phone number must contain at least 7 digits")
        return value.strip()


class StatusMixin(BaseSchema):
    """Mixin for common active/status fields."""

    is_active: bool = Field(True, description="Whether the entity is active")
    status: Optional[str] = Field(None, description="Application-defined status value")


class BaseCreateSchema(BaseSchema):
    """Base schema for entity creation requests."""

    pass


class BaseUpdateSchema(BaseSchema):
    """Base schema for entity update requests."""

    pass


class BaseResponseSchema(BaseSchema):
    """Base schema for entity responses with common fields."""

    id: UUID = Field(..., description="Entity unique identifier")

    # Include timestamp fields in responses
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")


class BaseCreateWithAuditSchema(BaseCreateSchema, AuditMixin, TimestampMixin):
    """Base creation schema with audit fields."""

    pass


class BaseUpdateWithAuditSchema(BaseUpdateSchema, AuditMixin):
    """Base update schema with audit fields."""

    pass


class BaseResponseWithAuditSchema(BaseResponseSchema, AuditMixin, SoftDeleteMixin):
    """Base response schema with audit and soft delete fields."""

    pass


class BaseTenantCreateSchema(BaseCreateSchema, TenantMixin):
    """Base creation schema for tenant-aware entities."""

    pass


class BaseTenantUpdateSchema(BaseUpdateSchema):
    """Base update schema for tenant-aware entities."""

    pass


class BaseTenantResponseSchema(BaseResponseSchema, TenantMixin, AuditMixin, SoftDeleteMixin):
    """Base response schema for tenant-aware entities with full audit trail."""

    pass


# Generic type variables for pagination
T = TypeVar("T")


class PaginationParams(BaseSchema):
    """Schema for pagination parameters."""

    page: int = Field(1, ge=1, description="Page number (1-based)")
    size: int = Field(20, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        """Calculate offset from page and size."""
        return (self.page - 1) * self.size


class SortParams(BaseSchema):
    """Schema for sorting parameters."""

    sort_by: Optional[str] = Field(None, description="Field to sort by")
    sort_order: str = Field("asc", pattern=r"^(asc|desc)$", description="Sort order")


class FilterParams(BaseSchema):
    """Schema for common filter parameters."""

    search: Optional[str] = Field(None, description="Search term")
    status: Optional[str] = Field(None, description="Status filter")
    date_from: Optional[datetime] = Field(None, description="Filter from date")
    date_to: Optional[datetime] = Field(None, description="Filter to date")

    @field_validator("search")
    @classmethod
    def validate_search(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v.strip()) < 2:
            raise ValueError("Search term must be at least 2 characters")
        return v.strip() if v else None


class PaginatedResponseSchema(BaseSchema, Generic[T]):
    """Generic schema for paginated responses."""

    items: list[T] = Field(..., description="List of items")
    total: int = Field(..., ge=0, description="Total number of items")
    page: int = Field(..., ge=1, description="Current page number")
    size: int = Field(..., ge=1, description="Items per page")
    pages: Optional[int] = Field(None, description="Total number of pages")

    def model_post_init(self, __context: Any) -> None:
        """Calculate total pages after initialization."""
        if self.total and self.size:
            self.pages = (self.total + self.size - 1) // self.size
        else:
            self.pages = 0


class ErrorResponseSchema(BaseSchema):
    """Schema for error responses."""

    error: bool = Field(True, description="Error flag")
    message: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    details: Optional[dict[str, Any]] = Field(None, description="Additional error details")
    field_errors: Optional[dict[str, str]] = Field(None, description="Field validation errors")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request identifier")


class SuccessResponseSchema(BaseSchema):
    """Schema for success responses."""

    success: bool = Field(True, description="Success flag")
    message: str = Field(..., description="Success message")
    data: Optional[Any] = Field(None, description="Response data")


class SearchSchema(BaseSchema):
    """Base schema for search endpoints with pagination and sorting."""

    query: Optional[str] = Field(None, description="Free-text search query")
    page: int = Field(1, ge=1, description="Page number (1-based)")
    size: int = Field(20, ge=1, le=100, description="Items per page")
    sort_by: Optional[str] = Field(None, description="Field to sort by")
    sort_order: str = Field("asc", pattern=r"^(asc|desc)$", description="Sort order")
    include_inactive: bool = Field(False, description="Include inactive records")

    @field_validator("query")
    @classmethod
    def _normalize_query(cls, value: Optional[str]) -> Optional[str]:
        if value:
            value = value.strip()
            if len(value) < 2:
                raise ValueError("Query must be at least 2 characters long")
        return value or None


class BulkOperationSchema(BaseSchema):
    """Schema for bulk operation requests."""

    items: list[Any] = Field(..., min_length=1, max_length=1000, description="Items to process")
    dry_run: bool = Field(False, description="Preview operation without executing")
    force: bool = Field(False, description="Force operation even with warnings")


class BulkOperationResponseSchema(BaseSchema):
    """Schema for bulk operation responses."""

    total_items: int = Field(..., description="Total items processed")
    successful: int = Field(..., description="Successfully processed items")
    failed: int = Field(..., description="Failed items")
    errors: list[dict[str, Any]] = Field(default_factory=list, description="Error details")
    warnings: list[str] = Field(default_factory=list, description="Warning messages")


# Common field validators
class CommonValidators:
    """Common field validators for reuse across schemas."""

    @staticmethod
    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        if not v or "@" not in v:
            raise ValueError("Invalid email format")
        return v.lower().strip()

    @staticmethod
    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format."""
        if not v:
            return None
        # Remove non-digits
        digits_only = "".join(filter(str.isdigit, v))
        if len(digits_only) < 10 or len(digits_only) > 15:
            raise ValueError("Phone number must be between 10-15 digits")
        return digits_only

    @staticmethod
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name fields."""
        if not v or len(v.strip()) < 2:
            raise ValueError("Name must be at least 2 characters")
        if len(v.strip()) > 100:
            raise ValueError("Name must be less than 100 characters")
        return v.strip().title()


# Status enums commonly used across modules
class EntityStatus(str, Enum):
    """Common entity status values."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class OperationStatus(str, Enum):
    """Common operation status values."""

    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    CANCELLED = "cancelled"
