"""Agent availability tracking models."""

from __future__ import annotations

import enum
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from dotmac.platform.database import Base


class AgentStatus(str, enum.Enum):
    """Agent availability status."""

    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"
    AWAY = "away"


class AgentAvailability(Base):
    """Track real-time availability status for support agents."""

    __tablename__ = "agent_availability"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    agent_id: Mapped[UUID] = mapped_column(index=True)  # Required by DB schema
    user_id: Mapped[UUID | None] = mapped_column(index=True, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="available", nullable=False
    )
    status_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    capacity: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    current_load: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    skills: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    last_activity_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<AgentAvailability(user_id={self.user_id}, status={self.status})>"


__all__ = ["AgentAvailability", "AgentStatus"]
