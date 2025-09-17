"""Licensing service implementations."""

from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Any, Iterable

import httpx

from .config import LicensingConfig, LicensingMode, SubscriptionConfig


class LicensingError(RuntimeError):
    """Raised when licensing information cannot be obtained."""


class BaseLicensingService(ABC):
    """Abstract licensing service interface."""

    @abstractmethod
    async def get_tenant_subscriptions(self, tenant_id: str) -> list[SubscriptionConfig]:
        """Return all subscriptions for a tenant."""

    async def aclose(self) -> None:  # pragma: no cover - optional cleanup
        """Release any resources held by the service."""


class NoopLicensingService(BaseLicensingService):
    """Licensing service used when licensing is disabled."""

    async def get_tenant_subscriptions(self, tenant_id: str) -> list[SubscriptionConfig]:
        return []


class StaticLicensingService(BaseLicensingService):
    """In-memory licensing service configured via static definitions."""

    def __init__(self, subscriptions: dict[str, list[SubscriptionConfig]]):
        self._subscriptions = subscriptions

    async def get_tenant_subscriptions(self, tenant_id: str) -> list[SubscriptionConfig]:
        return list(self._subscriptions.get(tenant_id, []))


class RemoteLicensingService(BaseLicensingService):
    """Licensing client that queries a remote management service."""

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        timeout: float = 10.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if not base_url:
            raise ValueError("Remote licensing service requires a base URL")

        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._client = client or httpx.AsyncClient(timeout=timeout)
        self._owns_client = client is None

    async def get_tenant_subscriptions(self, tenant_id: str) -> list[SubscriptionConfig]:
        url = f"{self.base_url}/tenants/{tenant_id}/subscriptions"
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            response = await self._client.get(url, headers=headers)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:  # pragma: no cover - network error handling
            raise LicensingError(
                f"Licensing server returned {exc.response.status_code}: {exc.response.text}"
            ) from exc
        except httpx.HTTPError as exc:  # pragma: no cover - network error handling
            raise LicensingError(f"Failed to contact licensing server: {exc}") from exc

        data = response.json()
        if not isinstance(data, Iterable):  # pragma: no cover - defensive
            raise LicensingError("Licensing server response must be iterable")

        subscriptions: list[SubscriptionConfig] = []
        for item in data:
            try:
                subscriptions.append(SubscriptionConfig(**item))
            except Exception as exc:  # pragma: no cover - defensive parsing
                raise LicensingError(f"Invalid subscription payload: {item!r}") from exc

        return subscriptions

    async def aclose(self) -> None:  # pragma: no cover - cleanup path
        if self._owns_client:
            await self._client.aclose()


class CachingLicensingService(BaseLicensingService):
    """Caching wrapper for licensing services."""

    def __init__(self, backend: BaseLicensingService, ttl_seconds: int = 300):
        self._backend = backend
        self._ttl = ttl_seconds
        self._cache: dict[str, tuple[float, list[SubscriptionConfig]]] = {}
        self._lock = asyncio.Lock()

    async def get_tenant_subscriptions(self, tenant_id: str) -> list[SubscriptionConfig]:
        async with self._lock:
            cached = self._cache.get(tenant_id)
            now = time.time()
            if cached and cached[0] > now:
                return list(cached[1])

            subscriptions = await self._backend.get_tenant_subscriptions(tenant_id)
            self._cache[tenant_id] = (now + self._ttl, list(subscriptions))
            return list(subscriptions)

    async def aclose(self) -> None:  # pragma: no cover - cleanup path
        await self._backend.aclose()


def create_licensing_service(config: LicensingConfig) -> BaseLicensingService:
    """Factory that creates a licensing service based on the supplied configuration."""

    if config.mode == LicensingMode.DISABLED:
        base_service: BaseLicensingService = NoopLicensingService()
    elif config.mode == LicensingMode.STANDALONE:
        base_service = StaticLicensingService(config.static_subscriptions)
    elif config.mode == LicensingMode.REMOTE:
        base_service = RemoteLicensingService(
            base_url=config.remote_base_url or "",
            api_key=config.remote_api_key,
            timeout=config.request_timeout,
        )
    else:  # pragma: no cover - exhaustive guard
        raise ValueError(f"Unsupported licensing mode: {config.mode}")

    if config.cache_enabled and not isinstance(base_service, NoopLicensingService):
        return CachingLicensingService(base_service, ttl_seconds=config.cache_ttl_seconds)

    return base_service
