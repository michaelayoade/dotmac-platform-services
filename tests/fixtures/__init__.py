"""Test fixtures and utilities for DotMac Platform Services."""

from tests.fixtures.async_db import (
    MockAsyncSessionFactory,
    create_mock_async_result,
    create_mock_async_session,
    create_mock_scalar_result,
)
from tests.fixtures.cache_bypass import (
    apply_cache_bypass,
    cache_bypass_fixture,
    mock_cached_result,
)

__all__ = [
    # Async DB fixtures
    "create_mock_async_result",
    "create_mock_async_session",
    "create_mock_scalar_result",
    "MockAsyncSessionFactory",
    # Cache bypass fixtures
    "apply_cache_bypass",
    "cache_bypass_fixture",
    "mock_cached_result",
]
