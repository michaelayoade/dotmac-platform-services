"""
Database Module - Compatibility Module

Provides database base classes for backward compatibility.
"""

from uuid import uuid4

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import declarative_base, Mapped, mapped_column

from .config import DatabaseConfig

Base = declarative_base()


class BaseModel(Base):
    """Base model for all database entities."""

    __abstract__ = True

    # Primary key for all ORM entities using this base
    id: Mapped[str] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    def __init__(self, **kwargs) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_dict(self):
        """Convert model to dictionary."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}({self.__dict__})>"


__all__ = ["Base", "BaseModel", "DatabaseConfig"]

# Enums expected by tests
from enum import Enum


class DatabaseDriver(str, Enum):
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    POSTGRESQL_ASYNC = "postgresql+asyncpg"
    MYSQL_ASYNC = "mysql+aiomysql"


class IsolationLevel(str, Enum):
    READ_UNCOMMITTED = "READ UNCOMMITTED"
    READ_COMMITTED = "READ COMMITTED"
    REPEATABLE_READ = "REPEATABLE READ"
    SERIALIZABLE = "SERIALIZABLE"


__all__ += ["DatabaseDriver", "IsolationLevel"]
