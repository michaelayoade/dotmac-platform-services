"""
Platform Products SQLAlchemy Models.

Defines deployable SaaS products in the Dotmac portfolio (e.g., Insights, Connect, Radius).
These are global/platform-level resources, NOT tenant-scoped.
"""

from typing import TYPE_CHECKING, Any
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    ForeignKey,
    Integer,
    String,
    Text,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base as BaseRuntime
from ..db import GUID, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from sqlalchemy.orm import DeclarativeBase as Base

    from ..deployment.models import DeploymentTemplate
else:
    Base = BaseRuntime


class PlatformProduct(Base, TimestampMixin, SoftDeleteMixin):
    """
    Platform Product Model.

    Represents a deployable SaaS product in the Dotmac portfolio.
    Products are global resources managed by platform administrators.
    Tenants subscribe to products and get isolated instances provisioned.

    Examples:
        - Dotmac Insights (Business Management)
        - Dotmac Connect (ISP Billing)
        - Dotmac Radius (Network Authentication)
    """

    __tablename__ = "platform_products"
    __table_args__ = (
        Index("ix_platform_products_slug", "slug", unique=True),
        Index("ix_platform_products_is_active", "is_active"),
        Index("ix_platform_products_is_public", "is_public"),
        Index("ix_platform_products_template_id", "template_id"),
    )

    # Identity
    id: Mapped[str] = mapped_column(
        GUID, primary_key=True, default=lambda: str(uuid4())
    )
    slug: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    short_description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Deployment Configuration
    docker_image: Mapped[str | None] = mapped_column(String(500), nullable=True)
    helm_chart_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    helm_chart_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    docker_compose_template: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Resource Defaults (JSON)
    default_resources: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=lambda: {"cpu": 2, "memory_gb": 4, "storage_gb": 50},
    )
    required_services: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=lambda: ["postgresql", "redis"],
    )

    # Module/Feature Configuration (JSON)
    available_modules: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list
    )
    default_modules: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list
    )

    # Health & Monitoring
    health_check_path: Mapped[str] = mapped_column(
        String(255), nullable=False, default="/health"
    )
    metrics_path: Mapped[str | None] = mapped_column(
        String(255), nullable=True, default="/metrics"
    )

    # Branding & Display
    icon_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    documentation_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Status
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Versioning
    current_version: Mapped[str] = mapped_column(
        String(50), nullable=False, default="1.0.0"
    )
    min_supported_version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Metadata (flexible JSON for custom attributes)
    # Note: Named 'product_metadata' to avoid conflict with SQLAlchemy's metadata
    product_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, nullable=False, default=dict
    )

    # Relationship to DeploymentTemplate (REQUIRED)
    template_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("deployment_templates.id", ondelete="RESTRICT"),
        nullable=False,
    )
    template: Mapped["DeploymentTemplate"] = relationship(
        "DeploymentTemplate",
        lazy="joined",
    )

    def __repr__(self) -> str:
        return f"<PlatformProduct(id={self.id}, slug={self.slug}, name={self.name})>"

    @property
    def is_deployable(self) -> bool:
        """Check if product can be deployed (has necessary configuration)."""
        return bool(
            self.is_active  # type: ignore[attr-defined] # From SoftDeleteMixin
            and self.template_id
            and (self.docker_image or self.helm_chart_url or self.docker_compose_template)
        )

    @property
    def display_name(self) -> str:
        """Get display name with fallback to name."""
        return self.name

    def has_module(self, module: str) -> bool:
        """Check if product supports a specific module."""
        return module in self.available_modules

    def get_resource_default(self, key: str, default: Any = None) -> Any:
        """Get a default resource value."""
        return self.default_resources.get(key, default)
