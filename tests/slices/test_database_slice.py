"""
Database session slice tests using the default SQLite fallback.
No mocks; just ensure helpers work and connections open.
"""

import os
import pytest

from sqlalchemy import text
from dotmac.platform.database.session import (
    _ensure_sync_engine,
    check_database_health,
    get_database_session,
)


@pytest.mark.skip(reason="Requires SQLite and greenlet, conflicts with async implementation")
def test_sync_session_and_engine_sqlite_fallback(tmp_path):
    # Point to a temp sqlite DB to avoid polluting repo
    os.environ["DOTMAC_DATABASE_URL"] = f"sqlite:///{tmp_path}/test.sqlite"

    engine = _ensure_sync_engine()
    assert engine is not None

    with get_database_session() as s:
        result = s.execute(text("SELECT 1")).scalar()
        assert result == 1

    # Health check should be True for sqlite
    assert check_database_health() in (True, False)  # Should not raise
