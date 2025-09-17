"""Configuration models for the licensing subsystem."""

from __future__ import annotations

import json
import os
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, ValidationError


class LicensingMode(str, Enum):
    """Supported licensing deployment modes."""

    DISABLED = "disabled"
    STANDALONE = "standalone"
    REMOTE = "remote"


class SubscriptionConfig(BaseModel):
    """Serializable subscription definition used by the static provider."""

    app: str
    plan: str = "basic"
    features: list[str] = Field(default_factory=list)
    is_active: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class LicensingConfig(BaseModel):
    """Configuration for the licensing service."""

    mode: LicensingMode = LicensingMode.STANDALONE
    static_subscriptions: dict[str, list[SubscriptionConfig]] = Field(default_factory=dict)
    remote_base_url: str | None = None
    remote_api_key: str | None = None
    cache_ttl_seconds: int = 300
    cache_enabled: bool = True
    request_timeout: float = 10.0

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def from_env(cls) -> "LicensingConfig":
        """Create a configuration instance using environment variables."""

        mode = os.getenv("DOTMAC_LICENSING_MODE", LicensingMode.STANDALONE.value)

        static_data: dict[str, list[SubscriptionConfig]] = {}
        raw_static = os.getenv("DOTMAC_LICENSING_STATIC")
        static_file = os.getenv("DOTMAC_LICENSING_STATIC_FILE")

        if raw_static:
            try:
                parsed_static = json.loads(raw_static)
                static_data = {
                    tenant: [SubscriptionConfig(**item) for item in items]
                    for tenant, items in parsed_static.items()
                }
            except (json.JSONDecodeError, ValidationError) as exc:  # pragma: no cover - defensive
                raise ValueError("Invalid DOTMAC_LICENSING_STATIC payload") from exc
        elif static_file:
            try:
                with open(static_file, "r", encoding="utf-8") as handle:
                    parsed_static = json.load(handle)
                static_data = {
                    tenant: [SubscriptionConfig(**item) for item in items]
                    for tenant, items in parsed_static.items()
                }
            except FileNotFoundError as exc:  # pragma: no cover - configuration error
                raise ValueError(f"Static licensing file not found: {static_file}") from exc

        return cls(
            mode=LicensingMode(mode.lower()),
            static_subscriptions=static_data,
            remote_base_url=os.getenv("DOTMAC_LICENSING_REMOTE_URL"),
            remote_api_key=os.getenv("DOTMAC_LICENSING_REMOTE_API_KEY"),
            cache_ttl_seconds=int(os.getenv("DOTMAC_LICENSING_CACHE_TTL", "300")),
            cache_enabled=os.getenv("DOTMAC_LICENSING_CACHE_ENABLED", "true").lower() != "false",
            request_timeout=float(os.getenv("DOTMAC_LICENSING_TIMEOUT", "10")),
        )
