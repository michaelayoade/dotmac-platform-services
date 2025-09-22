"""Public API for the licensing subsystem."""

from __future__ import annotations

from typing import Optional

from dotmac.platform.settings import settings, LicensingMode, SubscriptionConfig
from .services import (
    BaseLicensingService,
    CachingLicensingService,
    NoopLicensingService,
    create_licensing_service,
)

_LICENSING_SERVICE: Optional[BaseLicensingService] = None


def configure_licensing(config: LicensingConfig) -> BaseLicensingService:
    """Configure and return a global licensing service instance."""

    global _LICENSING_SERVICE
    _LICENSING_SERVICE = create_licensing_service(config)
    return _LICENSING_SERVICE


def get_licensing_service() -> BaseLicensingService:
    """Return the singleton licensing service, creating it on first use."""

    global _LICENSING_SERVICE
    if _LICENSING_SERVICE is None:
        config = LicensingConfig.from_env()
        _LICENSING_SERVICE = create_licensing_service(config)
    return _LICENSING_SERVICE


__all__ = [
    "BaseLicensingService",
    "CachingLicensingService",
    "LicensingConfig",
    "LicensingMode",
    "NoopLicensingService",
    "SubscriptionConfig",
    "configure_licensing",
    "create_licensing_service",
    "get_licensing_service",
]
