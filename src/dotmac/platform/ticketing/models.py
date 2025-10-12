"""
Ticketing domain models enabling cross-organization support workflows.

Supports ticket exchanges between customers, tenant teams, partners, and platform admins.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dotmac.platform.db import AuditMixin, Base, TenantMixin, TimestampMixin


class TicketActorType(str, Enum):
    """Represents which party is acting within the ticket conversation."""

    CUSTOMER = "customer"
    TENANT = "tenant"
    PARTNER = "partner"
    PLATFORM = "platform"


class TicketStatus(str, Enum):
    """Lifecycle state of a support ticket."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING = "waiting"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, Enum):
    """Operational priority assigned to a ticket."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Ticket(Base, TimestampMixin, TenantMixin, AuditMixin):
    """
    Ticket record capturing the high-level support request.

    Key relationships:
    - tenant_id: Owning tenant for isolation
    - partner_id: Linked partner when escalation involves a partner
    - customer_id: Customer who originated the request (when applicable)
    """

    __tablename__ = "tickets"

    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    ticket_number: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False,
        index=True,
    )
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[TicketStatus] = mapped_column(
        SQLEnum(TicketStatus),
        default=TicketStatus.OPEN,
        nullable=False,
        index=True,
    )
    priority: Mapped[TicketPriority] = mapped_column(
        SQLEnum(TicketPriority),
        default=TicketPriority.NORMAL,
        nullable=False,
        index=True,
    )
    origin_type: Mapped[TicketActorType] = mapped_column(
        SQLEnum(TicketActorType),
        nullable=False,
        index=True,
    )
    target_type: Mapped[TicketActorType] = mapped_column(
        SQLEnum(TicketActorType),
        nullable=False,
        index=True,
    )
    origin_user_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        nullable=True,
        index=True,
    )
    assigned_to_user_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        nullable=True,
        index=True,
    )
    customer_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    partner_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("partners.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    last_response_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    context: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )

    messages: Mapped[list[TicketMessage]] = relationship(
        "TicketMessage",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="TicketMessage.created_at",
    )

    __table_args__ = (
        Index("ix_tickets_tenant_status", "tenant_id", "status"),
        Index("ix_tickets_partner_status", "partner_id", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<Ticket(id={self.id}, number={self.ticket_number}, subject={self.subject!r}, "
            f"status={self.status}, tenant_id={self.tenant_id})>"
        )


class TicketMessage(Base, TimestampMixin, TenantMixin, AuditMixin):
    """
    Threaded message within a ticket conversation.

    Each message captures the sender type and optional linkage to customer or partner entities.
    """

    __tablename__ = "ticket_messages"

    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    ticket_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender_type: Mapped[TicketActorType] = mapped_column(
        SQLEnum(TicketActorType),
        nullable=False,
        index=True,
    )
    sender_user_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        nullable=True,
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    attachments: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    partner_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("partners.id", ondelete="SET NULL"),
        nullable=True,
    )
    customer_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True,
    )

    ticket: Mapped[Ticket] = relationship("Ticket", back_populates="messages")

    __table_args__ = (Index("ix_ticket_messages_ticket_created", "ticket_id", "created_at"),)

    def __repr__(self) -> str:
        return (
            f"<TicketMessage(id={self.id}, ticket_id={self.ticket_id}, sender={self.sender_type}, "
            f"created_at={self.created_at})>"
        )


__all__ = [
    "Ticket",
    "TicketMessage",
    "TicketActorType",
    "TicketPriority",
    "TicketStatus",
]
