"""
Push Notification Models
Database models for push notification subscriptions
"""

from datetime import datetime
from uuid import UUID as UUIDType
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from dotmac.platform.db import Base


class PushSubscription(Base):
    """Push notification subscription"""

    __tablename__ = "push_subscriptions"

    id: Mapped[UUIDType] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUIDType] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    tenant_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Subscription details
    endpoint: Mapped[str] = mapped_column(Text, nullable=False)
    p256dh_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    auth_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    device_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    device_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    browser: Mapped[str | None] = mapped_column(String(100), nullable=True)
    expiration_time: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        Index("idx_push_subscriptions_user_active", "user_id", "is_active"),
        Index("idx_push_subscriptions_tenant_active", "tenant_id", "is_active"),
        Index("idx_push_subscriptions_endpoint", "endpoint"),
    )

    def __repr__(self) -> str:
        return f"<PushSubscription(user_id={self.user_id}, active={self.is_active})>"
