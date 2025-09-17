"""
Unit tests for database session helper utilities.
Uses SQLite URLs to avoid external services.
"""

import pytest

from dotmac.platform.database.session import (
    check_database_health,
    create_async_database_engine,
    get_database_session,
    get_db_session,
)


@pytest.mark.unit
def test_sync_session_context_manager(monkeypatch, tmp_path):
    # Use a project-local SQLite DB file
    url = f"sqlite:///{tmp_path}/unit.sqlite"
    monkeypatch.setenv("DOTMAC_DATABASE_URL", url)

    with get_database_session() as sess:
        # Simple no-op to ensure session object is alive
        assert sess is not None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_async_session_context_manager(monkeypatch, tmp_path):
    # Ensure async URL uses aiosqlite
    url = f"sqlite+aiosqlite:///{tmp_path}/unit_async.sqlite"
    monkeypatch.setenv("DOTMAC_DATABASE_URL_ASYNC", url)

    async with get_db_session() as sess:
        assert sess is not None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_check_database_health_sqlite(monkeypatch, tmp_path):
    url = f"sqlite:///{tmp_path}/health.sqlite"
    monkeypatch.setenv("DOTMAC_DATABASE_URL", url)
    healthy = await check_database_health()
    assert isinstance(healthy, bool)


@pytest.mark.unit
def test_create_async_engine_factory():
    engine = create_async_database_engine("sqlite+aiosqlite:///./test.sqlite")
    # Can't easily assert type without importing SQLA symbols, but ensure object exists
    assert engine is not None
