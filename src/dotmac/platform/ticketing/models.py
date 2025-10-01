"""
Ticketing System Database Models
"""
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID, uuid4
from enum import Enum

from sqlalchemy import (
    Column, String, Boolean, DateTime, ForeignKey, Table, Text,
    UniqueConstraint, Index, JSON, Integer, Float, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, ARRAY
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy.ext.hybrid import hybrid_property

from dotmac.platform.database import Base
from dotmac.platform.core.models import TimestampMixin, SoftDeleteMixin


# Association tables
ticket_watchers = Table(
    'ticket_watchers',
    Base.metadata,
    Column('ticket_id', PGUUID(as_uuid=True), ForeignKey('tickets.id', ondelete='CASCADE'), primary_key=True),
    Column('user_id', PGUUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('added_at', DateTime(timezone=True), server_default=func.now()),
    UniqueConstraint('ticket_id', 'user_id', name='uq_ticket_watcher'),
)

ticket_tags = Table(
    'ticket_tags',
    Base.metadata,
    Column('ticket_id', PGUUID(as_uuid=True), ForeignKey('tickets.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', PGUUID(as_uuid=True), ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True),
    UniqueConstraint('ticket_id', 'tag_id', name='uq_ticket_tag'),
)


class TicketStatus(str, Enum):
    """Ticket workflow states"""
    NEW = "new"
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING_CUSTOMER = "pending_customer"
    PENDING_INTERNAL = "pending_internal"
    RESOLVED = "resolved"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class TicketPriority(str, Enum):
    """Ticket priority levels"""
    CRITICAL = "critical"  # P0 - Production down
    HIGH = "high"         # P1 - Major impact
    MEDIUM = "medium"     # P2 - Moderate impact
    LOW = "low"          # P3 - Minor impact
    NONE = "none"        # P4 - No immediate impact


class TicketType(str, Enum):
    """Types of tickets"""
    INCIDENT = "incident"          # Break/fix
    SERVICE_REQUEST = "service"    # New request
    QUESTION = "question"          # Information request
    PROBLEM = "problem"            # Root cause analysis
    TASK = "task"                  # Internal task
    BUG = "bug"                    # Software bug
    FEATURE = "feature"            # Feature request


class TicketSource(str, Enum):
    """How the ticket was created"""
    WEB = "web"
    EMAIL = "email"
    API = "api"
    PHONE = "phone"
    CHAT = "chat"
    INTERNAL = "internal"
    AUTOMATION = "automation"


class Ticket(Base, TimestampMixin, SoftDeleteMixin):
    """Main ticket entity"""
    __tablename__ = 'tickets'

    # Primary fields
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    ticket_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Classification
    status: Mapped[TicketStatus] = mapped_column(String(50), default=TicketStatus.NEW, nullable=False, index=True)
    priority: Mapped[TicketPriority] = mapped_column(String(20), default=TicketPriority.MEDIUM, nullable=False, index=True)
    type: Mapped[TicketType] = mapped_column(String(50), default=TicketType.SERVICE_REQUEST, nullable=False)
    source: Mapped[TicketSource] = mapped_column(String(20), default=TicketSource.WEB, nullable=False)

    # Assignment
    created_by_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    assigned_to_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey('users.id'), nullable=True, index=True)
    assigned_team_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey('teams.id'), nullable=True)
    escalated_to_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey('users.id'), nullable=True)

    # Organization
    customer_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey('customers.id'), nullable=True, index=True)
    organization_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey('organizations.id'), nullable=True)
    category_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey('ticket_categories.id'), nullable=True)

    # Parent/Child relationships
    parent_ticket_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey('tickets.id'), nullable=True)
    merged_into_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey('tickets.id'), nullable=True)

    # SLA tracking
    sla_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey('sla_policies.id'), nullable=True)
    first_response_due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    first_responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Metrics
    response_time_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    resolution_time_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reopen_count: Mapped[int] = mapped_column(Integer, default=0)
    satisfaction_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5 scale

    # Additional fields
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)  # Visible to customer
    is_spam: Mapped[bool] = mapped_column(Boolean, default=False)
    tags: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    custom_fields: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    created_by = relationship("User", foreign_keys=[created_by_id], backref="created_tickets")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id], backref="assigned_tickets")
    customer = relationship("Customer", backref="tickets")
    comments = relationship("TicketComment", back_populates="ticket", cascade="all, delete-orphan", order_by="TicketComment.created_at")
    attachments = relationship("TicketAttachment", back_populates="ticket", cascade="all, delete-orphan")
    activities = relationship("TicketActivity", back_populates="ticket", cascade="all, delete-orphan", order_by="desc(TicketActivity.created_at)")
    watchers = relationship("User", secondary=ticket_watchers, backref="watched_tickets")
    child_tickets = relationship("Ticket", backref="parent_ticket", remote_side=[id], foreign_keys=[parent_ticket_id])

    @hybrid_property
    def is_overdue(self) -> bool:
        """Check if ticket is overdue based on SLA"""
        if self.status in [TicketStatus.RESOLVED, TicketStatus.CLOSED, TicketStatus.CANCELLED]:
            return False
        if self.resolution_due_at:
            return datetime.utcnow() > self.resolution_due_at
        return False

    def __repr__(self) -> str:
        return f"<Ticket(number='{self.ticket_number}', status='{self.status}', priority='{self.priority}')>"


class TicketComment(Base, TimestampMixin):
    """Comments on tickets"""
    __tablename__ = 'ticket_comments'

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    ticket_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey('tickets.id', ondelete='CASCADE'), nullable=False)
    author_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey('users.id'), nullable=False)

    body: Mapped[str] = mapped_column(Text, nullable=False)
    body_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Rendered HTML version

    is_public: Mapped[bool] = mapped_column(Boolean, default=True)  # Visible to customer
    is_internal_note: Mapped[bool] = mapped_column(Boolean, default=False)
    is_resolution: Mapped[bool] = mapped_column(Boolean, default=False)  # Marks as resolution

    # For email integration
    email_message_id: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    in_reply_to: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    ticket = relationship("Ticket", back_populates="comments")
    author = relationship("User", backref="ticket_comments")
    attachments = relationship("TicketAttachment", back_populates="comment", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_ticket_comments_ticket_id', 'ticket_id'),
        Index('ix_ticket_comments_created_at', 'created_at'),
    )


class TicketAttachment(Base, TimestampMixin):
    """File attachments for tickets and comments"""
    __tablename__ = 'ticket_attachments'

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    ticket_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey('tickets.id', ondelete='CASCADE'), nullable=False)
    comment_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey('ticket_comments.id', ondelete='CASCADE'), nullable=True)
    uploaded_by_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey('users.id'), nullable=False)

    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)

    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    ticket = relationship("Ticket", back_populates="attachments")
    comment = relationship("TicketComment", back_populates="attachments")
    uploaded_by = relationship("User", backref="ticket_attachments")


class TicketActivity(Base, TimestampMixin):
    """Audit trail of ticket changes"""
    __tablename__ = 'ticket_activities'

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    ticket_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey('tickets.id', ondelete='CASCADE'), nullable=False)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey('users.id'), nullable=False)

    activity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # created, updated, assigned, resolved, etc.
    field_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    old_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    new_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    ticket = relationship("Ticket", back_populates="activities")
    user = relationship("User", backref="ticket_activities")

    __table_args__ = (
        Index('ix_ticket_activities_ticket_id', 'ticket_id'),
        Index('ix_ticket_activities_created_at', 'created_at'),
    )


class TicketCategory(Base):
    """Categories for organizing tickets"""
    __tablename__ = 'ticket_categories'

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    parent_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey('ticket_categories.id'), nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)  # Hex color

    default_priority: Mapped[Optional[TicketPriority]] = mapped_column(String(20), nullable=True)
    default_assignee_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    default_team_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey('teams.id'), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class SLAPolicy(Base):
    """Service Level Agreement policies"""
    __tablename__ = 'sla_policies'

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Response times in minutes
    first_response_time: Mapped[int] = mapped_column(Integer, nullable=False)  # Minutes
    resolution_time: Mapped[int] = mapped_column(Integer, nullable=False)  # Minutes

    # Conditions for applying this SLA
    priority: Mapped[Optional[TicketPriority]] = mapped_column(String(20), nullable=True)
    customer_tier: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    category_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey('ticket_categories.id'), nullable=True)

    # Business hours consideration
    business_hours_only: Mapped[bool] = mapped_column(Boolean, default=True)
    escalation_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint('first_response_time > 0', name='check_positive_response_time'),
        CheckConstraint('resolution_time > 0', name='check_positive_resolution_time'),
    )


class TicketTemplate(Base):
    """Templates for common ticket types"""
    __tablename__ = 'ticket_templates'

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    title_template: Mapped[str] = mapped_column(String(500), nullable=False)
    body_template: Mapped[str] = mapped_column(Text, nullable=False)

    default_type: Mapped[TicketType] = mapped_column(String(50), nullable=False)
    default_priority: Mapped[TicketPriority] = mapped_column(String(20), nullable=False)
    default_category_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey('ticket_categories.id'), nullable=True)

    available_to_customers: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())