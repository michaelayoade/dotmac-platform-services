"""
Integration test for Redis connectivity using redis.asyncio.

Environment variables:
- DOTMAC_REDIS_URL (e.g., redis://localhost:6379/0)
"""

import os
import uuid

import pytest
import os

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(os.getenv("DOTMAC_LIVE") != "1", reason="Live integration disabled (set DOTMAC_LIVE=1)"),
]


@pytest.mark.asyncio
async def test_redis_set_get_delete() -> None:
    try:
        import redis.asyncio as redis  # type: ignore
    except Exception:
        pytest.skip("redis is not installed; install with: poetry add redis")

    url = os.getenv("DOTMAC_REDIS_URL", "redis://localhost:6379/0")
    client = redis.from_url(url, decode_responses=True)

    key = f"it:{uuid.uuid4()}"
    value = "hello"

    try:
        ok = await client.set(key, value, ex=30)
        assert ok is True

        got = await client.get(key)
        assert got == value

        deleted = await client.delete(key)
        assert deleted >= 1
    finally:
        try:
            await client.close()
        except Exception:
            pass
