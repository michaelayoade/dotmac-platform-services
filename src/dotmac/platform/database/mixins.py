"""
Database Mixins - Compatibility Module

Provides database mixins for backward compatibility.
"""

from datetime import datetime
from typing import Any, Dict, TYPE_CHECKING

from sqlalchemy import Boolean, Column, DateTime, String, Text

if TYPE_CHECKING:
    from sqlalchemy.sql.schema import Table


class ISPModelMixin:
    """Mixin for ISP models to provide common functionality."""

    if TYPE_CHECKING:
        __table__: "Table"

    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def update(self, **kwargs: Any) -> "ISPModelMixin":
        """Update model with provided kwargs."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps."""

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TenantMixin:
    """Mixin to add tenant_id for multi-tenancy."""

    tenant_id = Column(String(255), nullable=True, index=True)


class StatusMixin:
    """Mixin to add status tracking."""

    status = Column(String(50), nullable=False, default="active")
    is_active = Column(Boolean, default=True)


class DescriptionMixin:
    """Mixin to add description field."""

    description = Column(Text, nullable=True)


__all__ = ["DescriptionMixin", "ISPModelMixin", "StatusMixin", "TenantMixin", "TimestampMixin"]
