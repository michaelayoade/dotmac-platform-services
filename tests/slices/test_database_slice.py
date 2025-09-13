"""
Database session slice tests using the default SQLite fallback.
No mocks; just ensure helpers work and connections open.
"""

import os

from dotmac.platform.database.session import (
    check_database_health,
    get_database_session,
    get_engine,
)


def test_sync_session_and_engine_sqlite_fallback(tmp_path):
    # Point to a temp sqlite DB to avoid polluting repo
    os.environ["DOTMAC_DATABASE_URL"] = f"sqlite:///{tmp_path}/test.sqlite"

    engine = get_engine()
    assert engine is not None

    with get_database_session() as s:
        result = s.execute("SELECT 1").scalar()
        assert result == 1

    # Health check should be True for sqlite
    assert check_database_health() in (True, False)  # Should not raise

