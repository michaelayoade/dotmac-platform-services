"""Type stubs for dotmac.platform.db module."""

from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import Request
from sqlalchemy import TypeDecorator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, sessionmaker

# Cross-Database UUID Type
class GUID(TypeDecorator[UUID]): ...

# Base classes
class Base(DeclarativeBase): ...

class BaseModel(Base):
    id: Mapped[UUID]
    tenant_id: Mapped[str | None]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    deleted_at: Mapped[datetime | None]
    is_active: Mapped[bool]
    def to_dict(self) -> dict[str, Any]: ...

# Mixins
class TimestampMixin:
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]

class TenantMixin:
    tenant_id: Mapped[str | None]

class StrictTenantMixin:
    tenant_id: Mapped[str]

class SoftDeleteMixin:
    deleted_at: Mapped[datetime | None]
    is_active: Mapped[bool]
    is_deleted: Mapped[bool]

class AuditMixin:
    created_by: Mapped[str | None]
    updated_by: Mapped[str | None]

# Database URLs
def get_database_url() -> str: ...
def get_async_database_url() -> str: ...

# Engines
def get_sync_engine() -> Any: ...
def get_async_engine() -> Any: ...

# Session factories
SyncSessionLocal: sessionmaker[Any]
AsyncSessionLocal: sessionmaker[Any]
async_session_maker: sessionmaker[Any]

# Session management
def set_session_rls_context(
    session: Any,
    tenant_id: str | None,
    is_superuser: bool = False,
    bypass_rls: bool = False,
) -> None: ...

def get_db(request: Request | None = None) -> Iterator[Session]: ...
def get_async_db(request: Request | None = None) -> AsyncIterator[AsyncSession]: ...
async def get_async_session_context(
    request: Request | None = None,
) -> AsyncIterator[AsyncSession]: ...
async def get_async_session(
    request: Request | None = None,
) -> AsyncIterator[AsyncSession]: ...
async def get_rls_session(
    request: Request | None = None,
) -> AsyncIterator[AsyncSession]: ...
async def get_session_dependency(
    request: Request | None = None,
) -> AsyncIterator[AsyncSession]: ...

def get_database_session(request: Request | None = None) -> Iterator[Session]: ...
def get_db_session(request: Request | None = None) -> AsyncIterator[AsyncSession]: ...
def get_async_db_session(request: Request | None = None) -> AsyncIterator[AsyncSession]: ...
def get_session(request: Request | None = None) -> AsyncIterator[AsyncSession]: ...

# Database state
@dataclass(frozen=True)
class DatabaseState:
    sync_engine: Any
    async_engine: Any
    sync_session_factory: sessionmaker[Any]
    async_session_factory: sessionmaker[Any]
    async_session_maker: sessionmaker[Any]

def snapshot_database_state() -> DatabaseState: ...
def restore_database_state(state: DatabaseState) -> None: ...
def configure_database_for_testing(
    *,
    sync_engine: Any | None = None,
    async_engine: Any | None = None,
    sync_session_factory: sessionmaker[Any] | None = None,
    async_session_factory: sessionmaker[Any] | None = None,
) -> None: ...

# Database operations
def create_all_tables() -> None: ...
async def create_all_tables_async() -> None: ...
def drop_all_tables() -> None: ...
async def drop_all_tables_async() -> None: ...
async def check_database_health() -> bool: ...
def init_db() -> None: ...
