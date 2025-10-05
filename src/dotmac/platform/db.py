"""
SQLAlchemy 2.0 Database Configuration

Simple, standard SQLAlchemy setup replacing the custom database module.
"""

import inspect
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock
from urllib.parse import quote_plus
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

from dotmac.platform.settings import settings

# ==========================================
# Database URLs from settings
# ==========================================


def get_database_url() -> str:
    """Get the sync database URL from settings."""
    if settings.database.url:
        return str(settings.database.url)

    # In development, use SQLite if PostgreSQL is not configured
    if settings.is_development and not settings.database.password:
        return "sqlite:///./dotmac_dev.sqlite"

    # Build PostgreSQL URL from components with proper encoding
    # URL-encode password to handle special characters safely
    username = quote_plus(settings.database.username)
    password = quote_plus(settings.database.password) if settings.database.password else ""
    host = settings.database.host
    port = settings.database.port
    database = settings.database.database

    return f"postgresql://{username}:{password}" f"@{host}:{port}/{database}"


def get_async_database_url() -> str:
    """Get the async database URL from settings."""
    sync_url = get_database_url()
    # Convert to async driver
    if "postgresql://" in sync_url:
        return sync_url.replace("postgresql://", "postgresql+asyncpg://")
    elif "sqlite://" in sync_url:
        return sync_url.replace("sqlite://", "sqlite+aiosqlite://")
    return sync_url


# ==========================================
# SQLAlchemy 2.0 Declarative Base
# ==========================================


class Base(DeclarativeBase):
    """Base class for all database models using SQLAlchemy 2.0 declarative mapping."""

    pass


# ==========================================
# Common Mixins (Optional, can be used by models)
# ==========================================
#
# IMPORTANT: Tenant Isolation Guidelines
# - Use StrictTenantMixin for user data, billing, secrets, etc.
# - Use TenantMixin only for system/shared resources
# - Always filter by tenant_id in queries for tenant-isolated models
# ==========================================


class TimestampMixin:
    """Adds created_at and updated_at timestamps to models."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class TenantMixin:
    """Adds tenant_id for multi-tenancy support (optional tenant)."""

    tenant_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)


class StrictTenantMixin:
    """Adds tenant_id for strict multi-tenancy (required tenant).

    Use this mixin for models that MUST have tenant isolation.
    Records without a tenant_id will be rejected.
    """

    tenant_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)


class SoftDeleteMixin:
    """Adds soft delete support."""

    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    @property
    def is_deleted(self) -> bool:
        """Check if the record is soft deleted."""
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        """Mark this record as soft deleted."""
        self.deleted_at = datetime.now(UTC)
        # Note: is_active is typically a computed property, don't set it here

    def restore(self) -> None:
        """Restore this record from soft deletion."""
        self.deleted_at = None
        # Note: is_active is typically a computed property, don't set it here


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

    # Tenant isolation - critical for multi-tenant SaaS
    tenant_id = Column(String(255), nullable=True, index=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True)
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
            get_database_url(),
            echo=settings.database.echo,
            pool_size=settings.database.pool_size,
            max_overflow=settings.database.max_overflow,
            pool_timeout=settings.database.pool_timeout,
            pool_recycle=settings.database.pool_recycle,
            pool_pre_ping=settings.database.pool_pre_ping,
        )
    return _sync_engine


def get_async_engine():
    """Get or create the asynchronous engine."""
    global _async_engine
    if _async_engine is None:
        _async_engine = create_async_engine(
            get_async_database_url(),
            echo=settings.database.echo,
            pool_size=settings.database.pool_size,
            max_overflow=settings.database.max_overflow,
            pool_timeout=settings.database.pool_timeout,
            pool_recycle=settings.database.pool_recycle,
            pool_pre_ping=settings.database.pool_pre_ping,
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

# Global variable to hold the session maker (can be overridden for testing)
_async_session_maker = AsyncSessionLocal


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


async def get_async_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency for getting an async database session."""
    async with _async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_session_dependency() -> AsyncIterator[AsyncSession]:
    """Compatibility wrapper that yields a session and remains easy to patch in tests."""

    session_source = get_async_session()

    if isinstance(session_source, AsyncMock):
        try:
            session = await session_source
        except TypeError:
            session = session_source
        yield session
        return

    if inspect.isasyncgen(session_source):
        async for session in session_source:
            yield session
        return

    if hasattr(session_source, "__aenter__") and hasattr(session_source, "__aexit__"):
        async with session_source as session:
            yield session
        return

    if hasattr(session_source, "__await__"):
        session = await session_source  # type: ignore[func-returns-value]
    else:
        session = session_source

    yield session


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
    from sqlalchemy import text

    try:
        async with get_async_db() as session:
            await session.execute(text("SELECT 1"))
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
    "get_async_session",  # FastAPI dependency
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
