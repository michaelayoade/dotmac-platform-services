"""
Customer Management Database Models.

Provides comprehensive customer data models with full audit trail,
multi-tenant support, and rich metadata capabilities.
"""

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dotmac.platform.db import (
    AuditMixin,
    Base,
    SoftDeleteMixin,
    TenantMixin,
    TimestampMixin,
)


class CustomerStatus(str, Enum):
    """Customer account status."""

    PROSPECT = "prospect"
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    CHURNED = "churned"
    ARCHIVED = "archived"


class CustomerType(str, Enum):
    """Type of customer account."""

    INDIVIDUAL = "individual"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"
    PARTNER = "partner"
    VENDOR = "vendor"


class CustomerTier(str, Enum):
    """Customer tier/level for service differentiation."""

    FREE = "free"
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class CommunicationChannel(str, Enum):
    """Preferred communication channels."""

    EMAIL = "email"
    SMS = "sms"
    PHONE = "phone"
    IN_APP = "in_app"
    PUSH = "push"
    MAIL = "mail"


class ActivityType(str, Enum):
    """Types of customer activities."""

    CREATED = "created"
    UPDATED = "updated"
    STATUS_CHANGED = "status_changed"
    NOTE_ADDED = "note_added"
    TAG_ADDED = "tag_added"
    TAG_REMOVED = "tag_removed"
    CONTACT_MADE = "contact_made"
    PURCHASE = "purchase"
    SUPPORT_TICKET = "support_ticket"
    LOGIN = "login"
    EXPORT = "export"
    IMPORT = "import"


class Customer(Base, TimestampMixin, TenantMixin, SoftDeleteMixin, AuditMixin):
    """
    Core customer model with comprehensive profile information.
    """

    __tablename__ = "customers"

    # Primary identifier
    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
    )

    # Customer identification
    customer_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique customer identifier for business operations",
    )

    # Basic Information
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    middle_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    company_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Account Information
    status: Mapped[CustomerStatus] = mapped_column(
        SQLEnum(CustomerStatus),
        default=CustomerStatus.PROSPECT,
        nullable=False,
        index=True,
    )
    customer_type: Mapped[CustomerType] = mapped_column(
        SQLEnum(CustomerType),
        default=CustomerType.INDIVIDUAL,
        nullable=False,
        index=True,
    )
    tier: Mapped[CustomerTier] = mapped_column(
        SQLEnum(CustomerTier),
        default=CustomerTier.FREE,
        nullable=False,
        index=True,
    )

    # Contact Information
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mobile: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    # Address Information
    address_line1: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state_province: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)  # ISO 3166-1 alpha-2

    # Business Information
    tax_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    vat_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    employee_count: Mapped[Optional[int]] = mapped_column(nullable=True)
    annual_revenue: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2), nullable=True
    )

    # Communication Preferences
    preferred_channel: Mapped[CommunicationChannel] = mapped_column(
        SQLEnum(CommunicationChannel),
        default=CommunicationChannel.EMAIL,
        nullable=False,
    )
    preferred_language: Mapped[str] = mapped_column(
        String(10), default="en", nullable=False
    )
    timezone: Mapped[str] = mapped_column(
        String(50), default="UTC", nullable=False
    )
    opt_in_marketing: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    opt_in_updates: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    user_id: Mapped[Optional[UUID]] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="Link to auth user account",
    )

    assigned_to: Mapped[Optional[UUID]] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="Assigned account manager or support agent",
    )

    segment_id: Mapped[Optional[UUID]] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("customer_segments.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Metrics
    lifetime_value: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), default=Decimal("0.00"), nullable=False
    )
    total_purchases: Mapped[int] = mapped_column(default=0, nullable=False)
    last_purchase_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    first_purchase_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    average_order_value: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), default=Decimal("0.00"), nullable=False
    )

    # Scoring and Risk
    credit_score: Mapped[Optional[int]] = mapped_column(nullable=True)
    risk_score: Mapped[int] = mapped_column(default=0, nullable=False)
    satisfaction_score: Mapped[Optional[int]] = mapped_column(nullable=True)
    net_promoter_score: Mapped[Optional[int]] = mapped_column(nullable=True)

    # Dates
    acquisition_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    last_contact_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    birthday: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Custom Fields (JSON for flexibility)
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, default=dict, nullable=False
    )
    custom_fields: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )
    tags: Mapped[list[str]] = mapped_column(
        JSON, default=list, nullable=False
    )

    # External System References
    external_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True
    )
    source_system: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Relationships
    activities = relationship("CustomerActivity", back_populates="customer", lazy="dynamic")
    notes = relationship("CustomerNote", back_populates="customer", lazy="dynamic")
    customer_tags = relationship("CustomerTag", back_populates="customer", lazy="dynamic")
    segment = relationship("CustomerSegment", back_populates="customers")
    # Contact relationships via join table
    contact_links = relationship("CustomerContactLink", back_populates="customer", lazy="dynamic")

    # Indexes and constraints
    __table_args__ = (
        UniqueConstraint("tenant_id", "customer_number", name="uq_tenant_customer_number"),
        UniqueConstraint("tenant_id", "email", name="uq_tenant_email"),
        Index("ix_customer_status_tier", "status", "tier"),
        Index("ix_customer_search", "first_name", "last_name", "company_name"),
        Index("ix_customer_location", "country", "state_province", "city"),
    )

    @property
    def full_name(self) -> str:
        """Get customer's full name."""
        parts = [self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        parts.append(self.last_name)
        return " ".join(parts)

    @property
    def display_label(self) -> str:
        """Get display label for customer."""
        if self.display_name:
            return self.display_name
        if self.company_name:
            return f"{self.full_name} ({self.company_name})"
        return self.full_name


class CustomerSegment(Base, TimestampMixin, TenantMixin, SoftDeleteMixin):
    """Customer segmentation for targeted operations."""

    __tablename__ = "customer_segments"

    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    criteria: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False, comment="Segmentation criteria/rules"
    )
    is_dynamic: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="Auto-update membership"
    )
    priority: Mapped[int] = mapped_column(default=0, nullable=False)

    # Metrics
    member_count: Mapped[int] = mapped_column(default=0, nullable=False)
    last_calculated: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    customers = relationship("Customer", back_populates="segment")

    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_tenant_segment_name"),
    )


class CustomerActivity(Base, TimestampMixin, TenantMixin):
    """Track all customer activities and interactions."""

    __tablename__ = "customer_activities"

    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    customer_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
    )

    activity_type: Mapped[ActivityType] = mapped_column(
        SQLEnum(ActivityType),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Activity details
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, default=dict, nullable=False
    )

    # User who performed the activity
    performed_by: Mapped[Optional[UUID]] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relationships
    customer = relationship("Customer", back_populates="activities")

    __table_args__ = (
        Index("ix_activity_customer_time", "customer_id", "created_at"),
    )


class CustomerNote(Base, TimestampMixin, TenantMixin, SoftDeleteMixin):
    """Notes and comments about customers."""

    __tablename__ = "customer_notes"

    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    customer_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
    )

    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    is_internal: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="Internal note vs customer visible"
    )

    def __init__(self, **kwargs):
        """Initialize with defaults."""
        # Set is_internal default if not provided
        if 'is_internal' not in kwargs:
            kwargs['is_internal'] = True
        super().__init__(**kwargs)

    # Author
    created_by_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    customer = relationship("Customer", back_populates="notes")

    __table_args__ = (
        Index("ix_note_customer_created", "customer_id", "created_at"),
    )


class CustomerTag(Base, TimestampMixin, TenantMixin):
    """Many-to-many relationship for customer tags."""

    __tablename__ = "customer_tags_association"

    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    customer_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
    )

    tag_name: Mapped[str] = mapped_column(String(50), nullable=False)
    tag_category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Relationships
    customer = relationship("Customer", back_populates="customer_tags")

    __table_args__ = (
        UniqueConstraint("customer_id", "tag_name", name="uq_customer_tag"),
        Index("ix_tag_name_category", "tag_name", "tag_category"),
    )


class ContactRole(str, Enum):
    """Roles a contact can have for a customer."""

    PRIMARY = "primary"
    BILLING = "billing"
    TECHNICAL = "technical"
    ADMIN = "admin"
    SUPPORT = "support"
    EMERGENCY = "emergency"
    OTHER = "other"


class CustomerContactLink(Base, TimestampMixin, TenantMixin):
    """
    Join table linking customers to contacts with roles.

    Normalizes the many-to-many relationship between customers and contacts,
    allowing a contact to be associated with multiple customers with different roles.
    """

    __tablename__ = "customer_contacts"

    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    customer_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Contact reference
    contact_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("contacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="FK to contacts.id"
    )

    # Role this contact has for this customer
    role: Mapped[ContactRole] = mapped_column(
        SQLEnum(ContactRole),
        default=ContactRole.OTHER,
        nullable=False,
    )

    # Is this the primary contact for this role?
    is_primary_for_role: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Primary contact for this specific role",
    )

    # Additional metadata
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    customer = relationship("Customer", back_populates="contact_links")
    contact = relationship("Contact", back_populates="customer_links")

    __table_args__ = (
        UniqueConstraint("customer_id", "contact_id", "role", name="uq_customer_contact_role"),
        Index("ix_customer_contact_customer", "customer_id", "role"),
        Index("ix_customer_contact_contact", "contact_id", "role"),
    )