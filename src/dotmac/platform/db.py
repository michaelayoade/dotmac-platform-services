"""
SQLAlchemy 2.0 Database Configuration

Simple, standard SQLAlchemy setup replacing the custom database module.
"""

import os
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime
from typing import Any, AsyncIterator, Iterator
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    String,
    create_engine,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    sessionmaker,
)

# ==========================================
# Database URLs from environment
# ==========================================

DATABASE_URL = os.getenv("DOTMAC_DATABASE_URL", "sqlite:///./dotmac_dev.sqlite")
DATABASE_URL_ASYNC = os.getenv(
    "DOTMAC_DATABASE_URL_ASYNC",
    DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    if "postgresql://" in DATABASE_URL
    else DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")
    if "sqlite://" in DATABASE_URL
    else DATABASE_URL
)

# ==========================================
# SQLAlchemy 2.0 Declarative Base
# ==========================================

class Base(DeclarativeBase):
    """Base class for all database models using SQLAlchemy 2.0 declarative mapping."""
    pass


# ==========================================
# Common Mixins (Optional, can be used by models)
# ==========================================

class TimestampMixin:
    """Adds created_at and updated_at timestamps to models."""
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class TenantMixin:
    """Adds tenant_id for multi-tenancy support."""
    tenant_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)


class SoftDeleteMixin:
    """Adds soft delete support."""
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class AuditMixin:
    """Adds audit trail fields."""
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_by: Mapped[str | None] = mapped_column(String(255), nullable=True)


# ==========================================
# Legacy Compatibility BaseModel
# ==========================================

class BaseModel(Base):
    """
    Legacy compatibility model for existing code.
    New models should inherit directly from Base and use mixins as needed.
    """
    __abstract__ = True

    # Primary key for all ORM entities
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}({self.__dict__})>"


# ==========================================
# Engine and Session Management
# ==========================================

# Create engines (lazy initialization)
_sync_engine = None
_async_engine = None


def get_sync_engine():
    """Get or create the synchronous engine."""
    global _sync_engine
    if _sync_engine is None:
        _sync_engine = create_engine(
            DATABASE_URL,
            echo=os.getenv("SQLALCHEMY_ECHO", "false").lower() == "true",
            future=True  # Use SQLAlchemy 2.0 style
        )
    return _sync_engine


def get_async_engine():
    """Get or create the asynchronous engine."""
    global _async_engine
    if _async_engine is None:
        _async_engine = create_async_engine(
            DATABASE_URL_ASYNC,
            echo=os.getenv("SQLALCHEMY_ECHO", "false").lower() == "true",
            future=True  # Use SQLAlchemy 2.0 style
        )
    return _async_engine


# Session factories
SyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=get_sync_engine(),
    class_=Session,
)

AsyncSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=get_async_engine(),
    class_=AsyncSession,
    expire_on_commit=False,
)


# ==========================================
# Session Context Managers
# ==========================================

@contextmanager
def get_db() -> Iterator[Session]:
    """Get a synchronous database session."""
    session = SyncSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@asynccontextmanager
async def get_async_db() -> AsyncIterator[AsyncSession]:
    """Get an asynchronous database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ==========================================
# Aliases for compatibility
# ==========================================

# Legacy function names that might be used in the codebase
get_database_session = get_db
get_db_session = get_async_db
get_async_db_session = get_async_db
get_session = get_async_db


# ==========================================
# Database Initialization
# ==========================================

def create_all_tables():
    """Create all tables in the database."""
    Base.metadata.create_all(bind=get_sync_engine())


async def create_all_tables_async():
    """Create all tables in the database asynchronously."""
    engine = get_async_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def drop_all_tables():
    """Drop all tables from the database. Use with caution!"""
    Base.metadata.drop_all(bind=get_sync_engine())


async def drop_all_tables_async():
    """Drop all tables from the database asynchronously. Use with caution!"""
    engine = get_async_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ==========================================
# Health Check
# ==========================================

async def check_database_health() -> bool:
    """Check if the database is accessible."""
    try:
        async with get_async_db() as session:
            await session.execute("SELECT 1")
        return True
    except Exception:
        return False


def init_db():
    """Initialize the database (create tables if needed)."""
    create_all_tables()


# ==========================================
# Exports
# ==========================================

__all__ = [
    # Base classes
    "Base",
    "BaseModel",  # For legacy compatibility

    # Mixins
    "TimestampMixin",
    "TenantMixin",
    "SoftDeleteMixin",
    "AuditMixin",

    # Session management
    "get_db",
    "get_async_db",
    "get_database_session",  # Legacy alias
    "get_db_session",  # Legacy alias
    "get_async_db_session",  # Legacy alias
    "get_session",  # Legacy alias

    # Engines
    "get_sync_engine",
    "get_async_engine",

    # Session factories
    "SyncSessionLocal",
    "AsyncSessionLocal",

    # Database operations
    "create_all_tables",
    "create_all_tables_async",
    "drop_all_tables",
    "drop_all_tables_async",
    "check_database_health",
    "init_db",
]