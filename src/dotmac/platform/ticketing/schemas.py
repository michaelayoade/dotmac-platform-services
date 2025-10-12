"""
Pydantic schemas for ticketing API endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .models import TicketActorType, TicketPriority, TicketStatus


class TicketCreate(BaseModel):
    """Payload for opening a new ticket."""

    subject: str = Field(..., min_length=3, max_length=255)
    message: str = Field(..., min_length=1)
    target_type: TicketActorType = Field(
        ...,
        description="Audience the ticket is targeting (tenant, partner, platform).",
    )
    priority: TicketPriority = Field(
        default=TicketPriority.NORMAL,
        description="Operational priority for the ticket.",
    )
    partner_id: UUID | None = Field(
        default=None,
        description="Partner identifier when escalating to a partner.",
    )
    tenant_id: str | None = Field(
        default=None,
        description="Tenant context override (required for platform admins creating tickets).",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary structured data associated with the ticket.",
    )
    attachments: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Optional attachment metadata bundled with the initial message.",
    )


class TicketMessageCreate(BaseModel):
    """Payload for appending a message to an existing ticket."""

    message: str = Field(..., min_length=1)
    attachments: list[dict[str, Any]] = Field(default_factory=list)
    new_status: TicketStatus | None = Field(
        default=None,
        description="Optional status transition to apply after posting the message.",
    )


class TicketUpdate(BaseModel):
    """Partial update payload for ticket metadata."""

    status: TicketStatus | None = None
    priority: TicketPriority | None = None
    assigned_to_user_id: UUID | None = None
    metadata: dict[str, Any] | None = None


class TicketMessageRead(BaseModel):
    """Serialized ticket message."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ticket_id: UUID
    sender_type: TicketActorType
    sender_user_id: UUID | None
    body: str
    attachments: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class TicketSummary(BaseModel):
    """Lightweight representation of a ticket for list views."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ticket_number: str
    subject: str
    status: TicketStatus
    priority: TicketPriority
    origin_type: TicketActorType
    target_type: TicketActorType
    tenant_id: str | None
    customer_id: UUID | None
    partner_id: UUID | None
    assigned_to_user_id: UUID | None
    last_response_at: datetime | None
    context: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class TicketDetail(TicketSummary):
    """Detailed ticket representation with threaded messages."""

    messages: list[TicketMessageRead] = Field(default_factory=list)


__all__ = [
    "TicketCreate",
    "TicketMessageCreate",
    "TicketUpdate",
    "TicketSummary",
    "TicketDetail",
    "TicketMessageRead",
]
