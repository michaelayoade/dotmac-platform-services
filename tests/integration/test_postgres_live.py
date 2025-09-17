"""
Integration test for PostgreSQL connectivity.

Requires a running PostgreSQL and either of:
- asyncpg installed (preferred)

Environment variables:
- DOTMAC_DATABASE_URL (e.g., postgresql://user:pass@localhost:5432/db)
"""

import os

import pytest

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("DOTMAC_LIVE") != "1", reason="Live integration disabled (set DOTMAC_LIVE=1)"
    ),
]


@pytest.mark.asyncio
async def test_postgres_connect_select_1() -> None:
    try:
        import asyncpg  # type: ignore
    except Exception:
        pytest.skip("asyncpg is not installed; install with: poetry add asyncpg")

    dsn = os.getenv("DOTMAC_DATABASE_URL")
    if not dsn or not dsn.startswith("postgresql://"):
        pytest.skip("DOTMAC_DATABASE_URL must be set to a postgresql:// DSN for live test")

    conn = await asyncpg.connect(dsn=dsn)
    try:
        val = await conn.fetchval("SELECT 1")
        assert val == 1
    finally:
        await conn.close()
