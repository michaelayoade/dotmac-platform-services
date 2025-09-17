"""
Database Mixins - Compatibility Module

Provides database mixins for backward compatibility.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, TYPE_CHECKING

from sqlalchemy import Boolean, Column, DateTime, String, Text, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import CHAR, String as SQLString

if TYPE_CHECKING:
    from sqlalchemy.sql.schema import Table


class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Uses PostgreSQL's UUID type, otherwise uses CHAR(32), storing as stringified hex values.
    """

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % uuid.UUID(value).int
            else:
                # hexstring
                return "%.32x" % value.int

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
            else:
                return value


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


__all__ = ["GUID", "DescriptionMixin", "ISPModelMixin", "StatusMixin", "TenantMixin", "TimestampMixin"]
