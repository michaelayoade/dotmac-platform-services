import pytest

from dotmac.platform.cache.config import CacheConfig
from dotmac.platform.cache.service import CacheService
from dotmac.platform.tasks.idempotency import idempotent


@pytest.mark.unit
@pytest.mark.asyncio
async def test_idempotent_does_not_cache_failures_then_succeeds():
    cache = CacheService(config=CacheConfig(backend="memory"))
    await cache.initialize()

    calls = {"n": 0}

    @idempotent(ttl=60)
    async def sometimes(x: int):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("fail once")
        return x + 1

    try:
        with pytest.raises(RuntimeError):
            await sometimes(10, _cache=cache)
        # Should not be cached; next call executes and succeeds
        assert await sometimes(10, _cache=cache) == 11
        # Subsequent call uses cached result
        assert await sometimes(10, _cache=cache) == 11
        assert calls["n"] == 2
    finally:
        await cache.shutdown()
