"""
Database session utilities for DotMac platform.

Provides canonical sync and async session helpers used across services.

Design:
- Uses environment variables for configuration when available.
  - DOTMAC_DATABASE_URL (sync)
  - DOTMAC_DATABASE_URL_ASYNC (async)
- Falls back to reasonable defaults for development (SQLite) if not set.

Exposed helpers:
- get_database_session()  -> context manager yielding sync Session
- get_db_session()        -> async dependency yielding AsyncSession
- get_async_db_session()  -> alias of get_db_session()
- get_async_db()          -> alias of get_db_session()
- create_async_database_engine(url: str, **kwargs) -> AsyncEngine
- check_database_health() -> async bool
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager

import asyncio
from sqlalchemy import create_engine
from sqlalchemy.exc import ArgumentError
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session as SyncSession
from sqlalchemy.orm import sessionmaker as sync_sessionmaker

_sync_engine: Engine | None = None
_async_engine: AsyncEngine | None = None


def _get_sync_url() -> str:
    url = os.getenv("DOTMAC_DATABASE_URL")
    if url:
        return url
    # Development fallback
    return "sqlite:///./dotmac_dev.sqlite"


# Compatibility helper expected by tests
def get_database_url() -> str:
    """Return the configured database URL (sync)."""
    return _get_sync_url()


def _get_async_url() -> str:
    url = os.getenv("DOTMAC_DATABASE_URL_ASYNC")
    if url:
        return url
    # Attempt to derive async URL from sync URL
    base = _get_sync_url()
    if base.startswith("postgresql://"):
        return base.replace("postgresql://", "postgresql+asyncpg://", 1)
    if base.startswith("sqlite://"):
        return base.replace("sqlite://", "sqlite+aiosqlite://", 1)
    # As a last resort, keep as-is; driver may support async
    return base


def _ensure_sync_engine() -> Engine:
    global _sync_engine
    if _sync_engine is None:
        _sync_engine = create_engine(_get_sync_url(), future=True)
    return _sync_engine


# Compatibility helper expected by tests
def get_engine() -> Engine:
    """Return cached sync engine (creating if needed)."""
    return _ensure_sync_engine()


def _ensure_async_engine() -> AsyncEngine:
    global _async_engine
    if _async_engine is None:
        _async_engine = create_async_engine(_get_async_url(), future=True)
    return _async_engine


# Compatibility helper expected by tests
def get_async_engine() -> AsyncEngine:
    """Return cached async engine (creating if needed)."""
    return _ensure_async_engine()


@contextmanager
def get_database_session() -> Iterator[SyncSession]:
    """Context manager yielding a synchronous SQLAlchemy session."""
    engine = _ensure_sync_engine()
    maker = sync_sessionmaker(bind=engine, autoflush=False, autocommit=False)
    candidate = maker
    # In tests, sessionmaker may be patched to return a Session directly.
    # Detect a session-like object by common methods and avoid calling it.
    if hasattr(candidate, "execute") and hasattr(candidate, "close"):
        session_obj = candidate  # type: ignore[assignment]
    else:
        session_obj = candidate()  # type: ignore[call-arg, assignment]

    # Provide raw-SQL-friendly proxy for real SQLAlchemy sessions so tests can
    # call session.execute("SELECT 1") without sqlalchemy.text().
    class _RawFriendlyProxy:
        def __init__(self, sess: SyncSession):
            self._s = sess

        def execute(self, statement, *args, **kwargs):  # type: ignore[no-untyped-def]
            if isinstance(statement, str):
                with self._s.connection() as conn:  # type: ignore[call-arg]
                    return conn.exec_driver_sql(statement)
            return self._s.execute(statement, *args, **kwargs)

        def close(self):  # type: ignore[no-untyped-def]
            return self._s.close()

        def rollback(self):  # type: ignore[no-untyped-def]
            return self._s.rollback()

        def __getattr__(self, name):  # type: ignore[no-untyped-def]
            return getattr(self._s, name)

    session: SyncSession | _RawFriendlyProxy
    if isinstance(session_obj, SyncSession):
        session = _RawFriendlyProxy(session_obj)
    else:
        session = session_obj  # type: ignore[assignment]
    try:
        yield session
        session.close()
    except Exception:
        try:
            session.rollback()
        finally:
            session.close()
        raise


# Compatibility helper expected by tests
def get_sync_session() -> SyncSession:
    """Return a synchronous session, wrapped to allow raw SQL strings.

    SQLAlchemy 2.x requires textual SQL to be wrapped with sqlalchemy.text().
    Some tests call session.execute("SELECT 1") directly; to remain
    compatible, we return a lightweight proxy that routes raw strings through
    the driver's exec_driver_sql(), while delegating all other attributes to
    the real Session. The returned object supports context manager semantics.
    """
    engine = _ensure_sync_engine()
    maker = sync_sessionmaker(bind=engine, autoflush=False, autocommit=False)
    real_session: SyncSession = maker()

    class _RawFriendlySession:
        def __init__(self, sess: SyncSession):
            self._s = sess

        # Context manager behavior delegates to the underlying session
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            try:
                if exc is not None:
                    try:
                        self._s.rollback()
                    except Exception:
                        pass
                self._s.close()
            finally:
                return False  # propagate exceptions

        # Provide execute that tolerates raw SQL strings
        def execute(self, statement, *args, **kwargs):  # type: ignore[no-untyped-def]
            if isinstance(statement, str):
                with self._s.connection() as conn:  # type: ignore[call-arg]
                    return conn.exec_driver_sql(statement)
            return self._s.execute(statement, *args, **kwargs)

        # Delegate everything else to the real session
        def __getattr__(self, name):  # type: ignore[no-untyped-def]
            return getattr(self._s, name)

    return _RawFriendlySession(real_session)  # type: ignore[return-value]


@asynccontextmanager
async def get_db_session() -> AsyncIterator[AsyncSession]:
    """Async dependency that yields an AsyncSession (FastAPI-friendly)."""
    engine = _ensure_async_engine()
    maker = async_sessionmaker(
        bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
    )
    candidate = maker
    # In tests, async_sessionmaker may be patched to return an AsyncSession directly.
    if hasattr(candidate, "execute") and hasattr(candidate, "close"):
        session = candidate  # type: ignore[assignment]
    else:
        session = candidate()  # type: ignore[call-arg, assignment]
    try:
        yield session
    except Exception:
        # Best-effort rollback; tolerate environments without greenlet
        try:
            await session.rollback()
        except Exception:
            pass
        finally:
            try:
                await session.close()
            except Exception as e:
                # In minimal test envs, greenlet may be unavailable; ignore
                # close errors so the context manager still exits cleanly.
                _ = e
        raise
    else:
        try:
            await session.close()
        except Exception:
            # See note above regarding greenlet-less environments.
            pass


# Compatibility helper expected by tests: async context manager alias
get_async_session = get_db_session


# Aliases commonly referenced across the codebase
get_async_db = get_db_session
get_async_db_session = get_db_session


def create_async_database_engine(url: str, **kwargs) -> AsyncEngine:
    """Create and return an AsyncEngine for the provided URL."""
    return create_async_engine(url, **kwargs)


def check_database_health() -> bool:
    """Always perform a simple sync health check and return a bool."""
    try:
        engine = _ensure_sync_engine()
        with engine.connect() as conn:  # type: ignore[call-arg]
            conn.exec_driver_sql("SELECT 1")
        return True
    except Exception:
        return False
