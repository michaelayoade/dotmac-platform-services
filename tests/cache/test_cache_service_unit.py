import asyncio
from typing import Any

import pytest

from dotmac.platform.cache.config import CacheConfig
from dotmac.platform.cache.service import CacheService, cached, create_cache_service


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cache_service_key_and_generate_key():
    cfg = CacheConfig(backend="memory")
    cache = CacheService(config=cfg, tenant_aware=True)
    await cache.initialize()

    try:
        # _make_key with tenant isolation
        assert cache._make_key("k", "t1") == "tenant:t1:k"

        # generate_key determinism and mixed args
        k1 = cache.generate_key({"a": 1}, x=2)
        k2 = cache.generate_key({"a": 1}, x=2)
        assert k1 == k2 and len(k1) == 64  # sha256 hex

        class Obj:
            def __repr__(self) -> str:  # non-JSON-serializable path
                return "<OBJ>"

        _ = cache.generate_key(Obj())  # should not raise
    finally:
        await cache.shutdown()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cached_decorator_with_memory_backend_and_tenant_isolation():
    cache = CacheService(config=CacheConfig(backend="memory"), tenant_aware=True)
    await cache.initialize()

    calls: dict[str, int] = {"count": 0}

    @cached(ttl=60, key_prefix="demo", tenant_aware=True)
    async def compute(x: int) -> int:
        calls["count"] += 1
        return x * 2

    try:
        # First call -> miss, second -> hit (same tenant)
        assert await compute(2, _cache_service=cache, _tenant_id="t1") == 4
        assert await compute(2, _cache_service=cache, _tenant_id="t1") == 4
        # Different tenant -> separate cache entry
        assert await compute(2, _cache_service=cache, _tenant_id="t2") == 4

        assert calls["count"] == 2  # one per tenant
    finally:
        await cache.shutdown()


@pytest.mark.unit
def test_cached_decorator_rejects_sync_functions():
    with pytest.raises(ValueError):
        @cached(ttl=10)
        def nope() -> int:  # noqa: D401 - intentionally sync
            return 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_cache_service_factory_variants():
    mem = create_cache_service()
    assert isinstance(mem, CacheService)
    await mem.initialize()
    try:
        stats = await mem.get_stats()
        assert stats["tenant_aware"] is False
        assert stats["backend"] == "memory"
    finally:
        await mem.shutdown()

    null = create_cache_service(backend="null")
    await null.initialize()
    try:
        stats = await null.get_stats()
        assert stats["backend"] == "null"
    finally:
        await null.shutdown()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cache_service_exists_delete_and_tenant_clear_branch():
    cache = CacheService(config=CacheConfig(backend="memory"), tenant_aware=True)
    await cache.initialize()
    try:
        assert await cache.set("k1", 7) is True
        assert await cache.exists("k1") is True
        assert await cache.delete("k1") is True
        assert await cache.exists("k1") is False

        # Exercise tenant-aware clear branch without touching backend
        assert await cache.clear(tenant_id="tenant-A") is True
    finally:
        await cache.shutdown()
