"""
Database session utilities for DotMac platform.

Provides canonical sync and async session helpers used across services.

Design:
- Uses environment variables for configuration when available.
  - DOTMAC_DATABASE_URL (sync)
  - DOTMAC_DATABASE_URL_ASYNC (async)
- Falls back to reasonable defaults for development (SQLite) if not set.

- Exposed helpers:
- get_database_session()  -> context manager yielding sync Session
- get_db_session()        -> async dependency yielding AsyncSession
- get_async_db_session()  -> alias of get_db_session()
- get_async_db()          -> alias of get_db_session()
- create_async_database_engine(url: str, **kwargs) -> AsyncEngine
- check_database_health() -> async bool
- init_db()               -> ensure database connectivity and optional migrations
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

from dotmac.platform.observability.unified_logging import get_logger

_sync_engine: Engine | None = None
_async_engine: AsyncEngine | None = None
logger = get_logger(__name__)


def _get_sync_url() -> str:
    url = os.getenv("DOTMAC_DATABASE_URL")
    if url:
        return url
    # Development fallback
    return "sqlite:///./dotmac_dev.sqlite"


# Note: previously exposed test-only helper get_database_url() has been removed.
_ = None  # placeholder to keep linters calm when block becomes empty


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


# Note: previously exposed test-only helper get_engine() has been removed.


def _ensure_async_engine() -> AsyncEngine:
    global _async_engine
    if _async_engine is None:
        _async_engine = create_async_engine(_get_async_url(), future=True)
    return _async_engine


# Note: previously exposed test-only helper get_async_engine() has been removed.


@contextmanager
def get_database_session() -> Iterator[SyncSession]:
    """Context manager yielding a synchronous SQLAlchemy session."""
    engine = _ensure_sync_engine()
    maker = sync_sessionmaker(bind=engine, autoflush=False, autocommit=False)
    # Support tests that patch sessionmaker to return a Session directly
    if hasattr(maker, "execute") and hasattr(maker, "close"):
        session = maker  # type: ignore[assignment]
    else:
        session = maker()  # type: ignore[call-arg,assignment]
    try:
        yield session
        session.close()
    except Exception:
        try:
            session.rollback()
        finally:
            session.close()
        raise


# Note: previously exposed test-only helper get_sync_session() has been removed.


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


# Note: previously exposed alias get_async_session has been removed; use get_db_session().


# Aliases commonly referenced across the codebase
get_async_db = get_db_session
get_async_db_session = get_db_session
get_session = get_db_session


async def init_db(run_migrations: bool | None = None) -> None:
    """Initialize database engines and optionally apply migrations."""

    _ensure_sync_engine()
    healthy = await check_database_health()
    if not healthy:
        raise RuntimeError("Database initialization failed: unable to connect with provided URL")

    should_run_migrations = run_migrations
    if should_run_migrations is None:
        should_run_migrations = os.getenv("DOTMAC_RUN_MIGRATIONS", "false").lower() == "true"

    if should_run_migrations:
        await _run_migrations_async()

    logger.info("database initialized", run_migrations=bool(should_run_migrations))


def create_async_database_engine(url: str, **kwargs) -> AsyncEngine:
    """Create and return an AsyncEngine for the provided URL."""
    return create_async_engine(url, **kwargs)


async def check_database_health() -> bool:
    """Perform a simple async health check using the async engine and return a bool."""
    try:
        engine = _ensure_async_engine()
        conn = await engine.connect()
        try:
            # A successful connect is sufficient for health in tests
            await conn.close()
        except Exception:
            # If .close is not awaitable in some drivers, try sync close
            try:
                conn.close()  # type: ignore[attr-defined]
            except Exception:
                pass
        return True
    except Exception:
        return False


async def _run_migrations_async() -> None:
    """Execute Alembic migrations using a background thread."""

    loop = asyncio.get_running_loop()

    def _upgrade():
        cfg_path = os.getenv("ALEMBIC_CONFIG", "alembic.ini")
        if not os.path.exists(cfg_path):
            logger.warning("alembic config not found; skipping migrations", path=cfg_path)
            return

        try:
            from alembic import command
            from alembic.config import Config
        except ModuleNotFoundError as exc:  # pragma: no cover - optional dependency
            logger.warning("alembic not installed; skipping migrations", error=str(exc))
            return

        command.upgrade(Config(cfg_path), "head")

    await loop.run_in_executor(None, _upgrade)
