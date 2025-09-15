import pytest

from dotmac.platform.cache.config import CacheConfig
from dotmac.platform.cache.service import CacheService
from dotmac.platform.tasks.idempotency import IdempotencyManager, idempotent


@pytest.mark.unit
@pytest.mark.asyncio
async def test_idempotent_decorator_caches_and_skips():
    cache = CacheService(config=CacheConfig(backend="memory"))
    await cache.initialize()

    calls = {"n": 0}

    @idempotent(ttl=60)
    async def op(x: int):
        calls["n"] += 1
        return x * 2

    try:
        # First call executes, second returns cached result
        assert await op(5, _cache=cache) == 10
        assert await op(5, _cache=cache) == 10
        assert calls["n"] == 1
    finally:
        await cache.shutdown()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_idempotent_decorator_marker_only():
    cache = CacheService(config=CacheConfig(backend="memory"))
    await cache.initialize()

    calls = {"n": 0}

    @idempotent(ttl=60, include_result=False)
    async def op2(x: int):
        calls["n"] += 1
        return x

    try:
        first = await op2(7, _cache=cache)
        second = await op2(7, _cache=cache)
        assert first == 7 and second is None
        assert calls["n"] == 1
    finally:
        await cache.shutdown()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_idempotency_manager_flow():
    cache = CacheService(config=CacheConfig(backend="memory"))
    await cache.initialize()
    try:
        async with IdempotencyManager(cache, "k1", ttl=60) as mgr:
            assert mgr.already_performed is False
            await mgr.set_result({"v": 1})

        # Second time should be marked as performed and load result
        async with IdempotencyManager(cache, "k1", ttl=60) as mgr2:
            assert mgr2.already_performed is True
            assert mgr2.cached_result == {"v": 1}
    finally:
        await cache.shutdown()
