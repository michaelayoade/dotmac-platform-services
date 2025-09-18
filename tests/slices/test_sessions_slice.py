"""
Session slice tests using the async in-memory backend (no mocks).
"""

from datetime import datetime, timedelta, UTC

import pytest
from dotmac.platform.auth.session_manager import MemorySessionBackend, SessionData, SessionStatus


@pytest.mark.asyncio
async def test_memory_session_backend_store_get_delete():
    backend = MemorySessionBackend()

    s = SessionData(
        session_id="s1",
        user_id="u1",
        tenant_id=None,
        created_at=datetime.now(UTC),
        last_accessed=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
        status=SessionStatus.ACTIVE,
        metadata={"k": "v"},
    )

    assert await backend.store_session(s) is True

    got = await backend.get_session("s1")
    assert got is not None
    assert got.session_id == "s1"
    assert got.user_id == "u1"
    assert got.is_active() is True

    assert await backend.delete_session("s1") is True
    assert await backend.get_session("s1") is None
