"""
Unit tests for SessionManager with MemorySessionBackend.
"""


import pytest

from dotmac.platform.auth.session_manager import (
    MemorySessionBackend,
    SessionManager,
    SessionStatus,
)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_get_extend_invalidate_delete_session():
    backend = MemorySessionBackend()
    mgr = SessionManager(backend, default_ttl=2)  # short TTL for test

    session = await mgr.create_session(user_id="u1", tenant_id="t1", metadata={"k": "v"})
    assert session.user_id == "u1"
    assert session.is_active()

    # get_session updates last_accessed
    before = session.last_accessed
    got = await mgr.get_session(session.session_id)
    assert got is not None
    assert got.last_accessed >= before

    # extend session
    ok = await mgr.extend_session(session.session_id, additional_ttl=5)
    assert ok is True

    # invalidate
    invalidated = await mgr.invalidate_session(session.session_id)
    assert invalidated is True
    got2 = await mgr.get_session(session.session_id)
    assert got2 is not None and got2.status == SessionStatus.INVALIDATED

    # delete
    deleted = await mgr.delete_session(session.session_id)
    assert deleted is True
    assert await backend.get_session(session.session_id) is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_enforce_session_limit():
    backend = MemorySessionBackend()
    mgr = SessionManager(backend, default_ttl=100, max_sessions_per_user=3)

    sids = []
    for _ in range(4):
        s = await mgr.create_session(user_id="user", tenant_id=None)
        sids.append(s.session_id)

    # After enforcing limit, there should be at most 3 active sessions
    sessions = await mgr.get_user_sessions("user")
    assert len(sessions) <= 3
