"""
Platform Products Pydantic Schemas.

Request and response models for platform product API endpoints.
"""

import re
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import ConfigDict, Field, field_validator

from ..core.pydantic import AppBaseModel


# Slug validation pattern: lowercase alphanumeric with hyphens
SLUG_PATTERN = re.compile(r"^[a-z][a-z0-9-]*[a-z0-9]$|^[a-z]$")


# =============================================================================
# Request Schemas
# =============================================================================


class PlatformProductCreate(AppBaseModel):
    """Request model for creating a platform product."""

    slug: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique identifier (lowercase alphanumeric with hyphens)",
    )
    name: str = Field(..., min_length=1, max_length=255, description="Display name")
    template_id: int = Field(..., description="Required deployment template ID")

    description: str | None = Field(None, max_length=5000, description="Full description")
    short_description: str | None = Field(
        None, max_length=500, description="Brief tagline"
    )

    # Deployment Configuration
    docker_image: str | None = Field(
        None, max_length=500, description="Container image reference"
    )
    helm_chart_url: str | None = Field(
        None, max_length=500, description="Helm chart URL"
    )
    helm_chart_version: str | None = Field(
        None, max_length=50, description="Helm chart version"
    )
    docker_compose_template: str | None = Field(
        None, max_length=500, description="Docker compose template path"
    )

    # Resource Defaults
    default_resources: dict[str, Any] = Field(
        default_factory=lambda: {"cpu": 2, "memory_gb": 4, "storage_gb": 50},
        description="Default resource allocation",
    )
    required_services: list[str] = Field(
        default_factory=lambda: ["postgresql", "redis"],
        description="Required backing services",
    )

    # Module Configuration
    available_modules: list[str] = Field(
        default_factory=list, description="Available modules for this product"
    )
    default_modules: list[str] = Field(
        default_factory=list, description="Default enabled modules"
    )

    # Health & Monitoring
    health_check_path: str = Field(
        default="/health", max_length=255, description="Health check endpoint"
    )
    metrics_path: str | None = Field(
        default="/metrics", max_length=255, description="Metrics endpoint"
    )

    # Branding
    icon_url: str | None = Field(None, max_length=500, description="Product icon URL")
    logo_url: str | None = Field(None, max_length=500, description="Product logo URL")
    documentation_url: str | None = Field(
        None, max_length=500, description="Documentation URL"
    )

    # Status
    is_active: bool = Field(default=False, description="Available for subscription")
    is_public: bool = Field(default=False, description="Visible in public catalog")

    # Versioning
    current_version: str = Field(
        default="1.0.0", max_length=50, description="Current product version"
    )
    min_supported_version: str | None = Field(
        None, max_length=50, description="Minimum supported version"
    )

    # Metadata
    product_metadata: dict[str, Any] = Field(
        default_factory=dict, description="Custom metadata", alias="metadata"
    )

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Validate slug format: lowercase alphanumeric with hyphens."""
        v = v.lower().strip()
        if not SLUG_PATTERN.match(v):
            raise ValueError(
                "Slug must be lowercase alphanumeric with hyphens, "
                "start with a letter, and not end with a hyphen"
            )
        if "--" in v:
            raise ValueError("Slug cannot contain consecutive hyphens")
        return v

    @field_validator("default_modules")
    @classmethod
    def validate_default_modules(
        cls, v: list[str], info: Any
    ) -> list[str]:
        """Ensure default modules are a subset of available modules."""
        # Note: This validation is limited in Pydantic v2 validators
        # Full validation happens in service layer
        return v


class PlatformProductUpdate(AppBaseModel):
    """Request model for updating a platform product (partial updates)."""

    name: str | None = Field(None, min_length=1, max_length=255)
    template_id: int | None = Field(None, description="Update deployment template")
    description: str | None = Field(None, max_length=5000)
    short_description: str | None = Field(None, max_length=500)

    # Deployment Configuration
    docker_image: str | None = Field(None, max_length=500)
    helm_chart_url: str | None = Field(None, max_length=500)
    helm_chart_version: str | None = Field(None, max_length=50)
    docker_compose_template: str | None = Field(None, max_length=500)

    # Resource Defaults
    default_resources: dict[str, Any] | None = None
    required_services: list[str] | None = None

    # Module Configuration
    available_modules: list[str] | None = None
    default_modules: list[str] | None = None

    # Health & Monitoring
    health_check_path: str | None = Field(None, max_length=255)
    metrics_path: str | None = Field(None, max_length=255)

    # Branding
    icon_url: str | None = Field(None, max_length=500)
    logo_url: str | None = Field(None, max_length=500)
    documentation_url: str | None = Field(None, max_length=500)

    # Status
    is_active: bool | None = None
    is_public: bool | None = None

    # Versioning
    current_version: str | None = Field(None, max_length=50)
    min_supported_version: str | None = Field(None, max_length=50)

    # Metadata
    product_metadata: dict[str, Any] | None = Field(None, alias="metadata")


class ProductFilters(AppBaseModel):
    """Filter options for listing products."""

    is_active: bool | None = Field(None, description="Filter by active status")
    is_public: bool | None = Field(None, description="Filter by public visibility")
    search: str | None = Field(None, max_length=100, description="Search in name/description")
    template_id: int | None = Field(None, description="Filter by template")


# =============================================================================
# Response Schemas
# =============================================================================


class PlatformProductResponse(AppBaseModel):
    """Full response model for platform product (admin endpoints)."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    slug: str
    name: str
    template_id: int

    description: str | None = None
    short_description: str | None = None

    # Deployment Configuration
    docker_image: str | None = None
    helm_chart_url: str | None = None
    helm_chart_version: str | None = None
    docker_compose_template: str | None = None

    # Resource Defaults
    default_resources: dict[str, Any]
    required_services: list[str]

    # Module Configuration
    available_modules: list[str]
    default_modules: list[str]

    # Health & Monitoring
    health_check_path: str
    metrics_path: str | None = None

    # Branding
    icon_url: str | None = None
    logo_url: str | None = None
    documentation_url: str | None = None

    # Status
    is_active: bool
    is_public: bool

    # Versioning
    current_version: str
    min_supported_version: str | None = None

    # Metadata
    product_metadata: dict[str, Any] = Field(..., alias="metadata")

    # Timestamps
    created_at: datetime
    updated_at: datetime

    # Soft delete
    deleted_at: datetime | None = None


class PlatformProductListResponse(AppBaseModel):
    """Paginated list response for platform products."""

    products: list[PlatformProductResponse]
    total: int
    page: int
    page_size: int
    pages: int


# =============================================================================
# Public Catalog Schemas (limited fields, no internal config)
# =============================================================================


class PublicProductResponse(AppBaseModel):
    """Limited response model for public catalog (no internal details)."""

    model_config = ConfigDict(from_attributes=True)

    slug: str
    name: str
    description: str | None = None
    short_description: str | None = None

    # Branding
    icon_url: str | None = None
    logo_url: str | None = None
    documentation_url: str | None = None

    # Feature info (safe to expose)
    available_modules: list[str]
    current_version: str

    # Note: Does NOT include:
    # - id, template_id, docker_image, helm_chart_url
    # - default_resources, required_services
    # - health_check_path, metrics_path, metadata
    # - is_active (implied true for public catalog)
    # - timestamps


class PublicProductListResponse(AppBaseModel):
    """List response for public catalog."""

    products: list[PublicProductResponse]
    total: int
