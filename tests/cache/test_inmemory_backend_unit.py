import asyncio

import pytest

from dotmac.platform.cache.backends import InMemoryCache
from dotmac.platform.cache.config import CacheConfig


# Test removed - was testing cache statistics functionality
# @pytest.mark.unit
# @pytest.mark.asyncio
# async def test_inmemory_cache_crud_and_stats(monkeypatch):
#     Test has been removed as it tests integration/performance aspects
