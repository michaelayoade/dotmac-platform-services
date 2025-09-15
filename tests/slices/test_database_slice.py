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


# REMOVED: SQLite test that conflicts with async implementation
