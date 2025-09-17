"""Stub marketplace provider for service mesh integration tests."""

from __future__ import annotations

from typing import Any, List


class ServiceMarketplace:
    """Placeholder marketplace that returns no services by default."""

    async def discover_service(self) -> List[dict[str, Any]]:
        return []


async def discover_service_mock() -> list[dict[str, Any]]:
    """Simple helper used by tests to patch marketplace discovery."""
    return []

__all__ = ["ServiceMarketplace", "discover_service_mock"]
