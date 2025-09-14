import asyncio

import pytest

from dotmac.platform.cache.backends import InMemoryCache
from dotmac.platform.cache.config import CacheConfig


@pytest.mark.unit
@pytest.mark.asyncio
async def test_inmemory_cache_crud_and_stats(monkeypatch):
    cfg = CacheConfig(backend="memory", default_ttl=5, max_size=10)
    backend = InMemoryCache(cfg)

    # connect is idempotent
    assert await backend.connect() is True
    assert await backend.connect() is True
    assert backend.is_connected() is True

    # set/get/exists
    assert await backend.set("a", {"x": 1}, ttl=2) is True
    assert await backend.exists("a") is True
    assert await backend.get("a") == {"x": 1}

    # delete
    assert await backend.delete("a") is True
    assert await backend.get("a") is None

    # set again and clear
    assert await backend.set("b", 123) is True
    assert await backend.clear() is True
    assert await backend.get("b") is None

    # stats
    stats = await backend.get_stats()
    assert stats["backend"] == "memory"
    assert set(["connected", "size", "max_size", "default_ttl"]).issubset(stats.keys())

    # expiry behavior via time travel
    assert await backend.set("c", 1, ttl=1) is True
    import dotmac.platform.cache.backends as backends_mod

    base = backends_mod.time.time()
    monkeypatch.setattr(backends_mod.time, "time", lambda: base + 120)
    # expired -> get returns None and removes entry
    assert await backend.get("c") is None
    assert await backend.exists("c") is False

    # disconnect
    assert await backend.disconnect() is True
    assert backend.is_connected() is False

