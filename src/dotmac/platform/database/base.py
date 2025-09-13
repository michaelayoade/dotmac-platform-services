"""
Database Base Module - Compatibility Module

Provides database base classes for backward compatibility.
"""

from datetime import datetime
from typing import Any, Dict
from uuid import uuid4

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm import declarative_base

Base: DeclarativeMeta = declarative_base()


class BaseModel(Base):
    """Base model for all database entities."""

    __abstract__ = True

    # Primary key for all ORM entities using this base
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    def __init__(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}({self.__dict__})>"


class AuditableMixin:
    """Mixin for auditable models."""

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)


__all__ = ["AuditableMixin", "Base", "BaseModel"]
