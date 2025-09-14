import pytest

from dotmac.platform.auth.session_manager import (
    SessionStatus,
    create_memory_session_manager,
)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_session_lifecycle_and_stats_memory_backend():
    sm = create_memory_session_manager(default_ttl=60, max_sessions_per_user=2)

    # Create and validate
    s1 = await sm.create_session_async(user_id="u1", metadata={"k": "v"})
    assert s1.user_id == "u1" and s1.status == SessionStatus.ACTIVE
    assert await sm.validate_session(s1.session_id) is not None

    # Extend
    old_exp = s1.expires_at
    assert await sm.extend_session(s1.session_id, additional_ttl=5) is True
    s1b = await sm.get_session_async(s1.session_id)
    assert s1b and s1b.expires_at > old_exp

    # Get user sessions
    sessions = await sm.get_user_sessions("u1")
    ids = {x.session_id for x in sessions}
    assert s1.session_id in ids

    # Invalidate
    assert await sm.invalidate_session(s1.session_id) is True
    assert await sm.validate_session(s1.session_id) is None

    # Stats
    stats = await sm.get_session_stats()
    assert stats["backend_type"] == "MemorySessionBackend"
    assert stats["default_ttl"] == 60 and stats["max_sessions_per_user"] == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_session_limit_enforced_removes_oldest():
    sm = create_memory_session_manager(default_ttl=60, max_sessions_per_user=2)

    s1 = await sm.create_session_async(user_id="u2")
    s2 = await sm.create_session_async(user_id="u2")
    # Third should trigger removal of oldest when next is stored
    s3 = await sm.create_session_async(user_id="u2")

    active_ids = {s.session_id for s in await sm.get_user_sessions("u2")}
    # We should have at most 2 active; oldest likely evicted
    assert len(active_ids) <= 2
    assert s3.session_id in active_ids

