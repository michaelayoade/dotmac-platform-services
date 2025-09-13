"""
Session slice tests using the synchronous in-memory backend (no mocks).
"""

from datetime import datetime, timedelta

from dotmac.platform.auth.session_manager import (
    MemorySessionBackendSync,
    Session,
)


def test_memory_session_backend_sync_store_get_delete():
    backend = MemorySessionBackendSync()

    s = Session(
        id="s1",
        user_id="u1",
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(minutes=5),
        data={"k": "v"},
    )

    assert backend.store_session(s) is True

    got = backend.get_session("s1")
    assert got is not None
    assert got.id == "s1"
    assert got.user_id == "u1"
    assert got.is_valid is True

    assert backend.delete_session("s1") is True
    assert backend.get_session("s1") is None

