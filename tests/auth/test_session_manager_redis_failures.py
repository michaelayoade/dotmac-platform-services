"""
Failure-path tests for RedisSessionBackend using monkeypatched pipeline exceptions.
"""

import json

import pytest

pytest.importorskip("fakeredis", reason="fakeredis is required for Redis backend unit tests")
from datetime import datetime, timedelta, UTC

import fakeredis

from dotmac.platform.auth.session_manager import (
    RedisSessionBackend,
    SessionData,
    SessionStatus,
)


class BoomPipeline:
    def __init__(self, *a, **kw):
        self.calls = []

    def setex(self, *a, **kw):
        self.calls.append(("setex", a, kw))
        return self

    def sadd(self, *a, **kw):
        self.calls.append(("sadd", a, kw))
        return self

    def expire(self, *a, **kw):
        self.calls.append(("expire", a, kw))
        return self

    async def execute(self):
        raise RuntimeError("boom")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_store_session_pipeline_failure(monkeypatch):
    backend = RedisSessionBackend("redis://localhost:6379/0")
    backend._redis = fakeredis.aioredis.FakeRedis(decode_responses=True)

    # Monkeypatch pipeline to one that raises
    monkeypatch.setattr(backend._redis, "pipeline", lambda: BoomPipeline())

    # Prepare a session
    s = SessionData(
        session_id="s1",
        user_id="u1",
        tenant_id=None,
        created_at=datetime.now(UTC),
        last_accessed=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(seconds=60),
        status=SessionStatus.ACTIVE,
        metadata={},
    )

    ok = await backend.store_session(s)
    assert ok is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_session_pipeline_failure(monkeypatch):
    backend = RedisSessionBackend("redis://localhost:6379/0")
    backend._redis = fakeredis.aioredis.FakeRedis(decode_responses=True)

    # Save a session first – but we will override pipeline used during delete
    await backend.redis.set(
        backend._session_key("s1"),
        json.dumps(
            {
                "session_id": "s1",
                "user_id": "u1",
                "tenant_id": None,
                "created_at": datetime.now(UTC).isoformat(),
                "last_accessed": datetime.now(UTC).isoformat(),
                "expires_at": (datetime.now(UTC) + timedelta(seconds=60)).isoformat(),
                "status": SessionStatus.ACTIVE,
                "metadata": {},
            }
        ),
    )

    monkeypatch.setattr(backend._redis, "pipeline", lambda: BoomPipeline())

    ok = await backend.delete_session("s1")
    assert ok is False
