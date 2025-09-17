import pytest

from dotmac.platform.cache.backends import InMemoryCache
from dotmac.platform.cache.config import CacheConfig


@pytest.mark.unit
@pytest.mark.asyncio
async def test_inmemory_cache_lru_eviction():
    cfg = CacheConfig(backend="memory", max_size=1)
    backend = InMemoryCache(cfg)
    await backend.connect()
    try:
        assert await backend.set("k1", 1) is True
        # Second set should evict first due to max_size=1
        assert await backend.set("k2", 2) is True
        assert await backend.get("k1") is None
        assert await backend.get("k2") == 2
    finally:
        await backend.disconnect()
