"""
Unit tests for RedisSessionBackend using fakeredis.aioredis to avoid real Redis.
"""

import pytest

# Skip these tests when fakeredis is not available in the environment
pytest.importorskip("fakeredis", reason="fakeredis is required for Redis backend unit tests")
import fakeredis

from dotmac.platform.auth.session_manager import (
    RedisSessionBackend,
    SessionManager,
)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_redis_backend_store_get_delete_user_sessions():
    # Create backend and inject fake redis client
    backend = RedisSessionBackend("redis://localhost:6379/0")
    backend._redis = fakeredis.aioredis.FakeRedis(decode_responses=True)

    mgr = SessionManager(backend, default_ttl=60)

    # Create a session (uses backend.store_session under the hood)
    session = await mgr.create_session(user_id="user-1", tenant_id="t1")
    assert session is not None

    # Retrieve session
    got = await backend.get_session(session.session_id)
    assert got is not None and got.user_id == "user-1"

    # User sessions set
    user_sessions = await backend.get_user_sessions("user-1")
    assert session.session_id in user_sessions

    # Delete session
    deleted = await backend.delete_session(session.session_id)
    assert deleted is True
    assert await backend.get_session(session.session_id) is None
