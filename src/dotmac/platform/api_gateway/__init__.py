"""API Gateway Service - Request routing, rate limiting, and versioning.

Provider-agnostic API management without vendor lock-in.
"""

from typing import Any, Mapping, Optional

from fastapi import FastAPI

from dotmac.platform.observability.unified_logging import get_logger

logger = get_logger(__name__)

from .interfaces import RateLimiter, VersionStrategy, RateLimitConfig  # lightweight
from .config import GatewayConfig, GatewayMode  # unified config
from .validation import RequestValidator, ValidationMiddleware, ValidationLevel

# ObservabilityManager removed - replaced with unified analytics
from .factory import create_gateway, setup_gateway_app
from .analytics_integration import APIGatewayAnalyticsAdapter, get_gateway_analytics

# Optional imports guarded to avoid hard dependency at package import time
try:
    from .gateway import APIGateway
except Exception as e:  # pragma: no cover - optional
    APIGateway = None
    logger.debug(f"APIGateway not available: {e}")

try:
    from .rate_limiting import (
        TokenBucketLimiter,
        SlidingWindowLimiter,
        FixedWindowLimiter,
    )
except Exception as e:  # pragma: no cover - optional
    TokenBucketLimiter = SlidingWindowLimiter = FixedWindowLimiter = None  # type: ignore
    logger.debug(f"Rate limiting implementations not available: {e}")

try:
    from .versioning import HeaderVersioning, PathVersioning, QueryVersioning
except Exception as e:  # pragma: no cover - optional
    HeaderVersioning = PathVersioning = QueryVersioning = None  # type: ignore
    logger.debug(f"Versioning strategies not available: {e}")

__all__ = [
    "RateLimiter",
    "VersionStrategy",
    "RateLimitConfig",
    "GatewayConfig",
    "GatewayMode",
    "RequestValidator",
    "ValidationMiddleware",
    "ValidationLevel",
    "APIGatewayAnalyticsAdapter",
    "get_gateway_analytics",
    "create_gateway",
    "setup_gateway_app",
    "create_api_gateway",
]
if APIGateway is not None:
    __all__.append("APIGateway")

# Add rate limiting classes if available
if TokenBucketLimiter is not None:
    __all__.extend(["TokenBucketLimiter", "SlidingWindowLimiter", "FixedWindowLimiter"])

# Add versioning classes if available
if HeaderVersioning is not None:
    __all__.extend(["HeaderVersioning", "PathVersioning", "QueryVersioning"])


def _resolve_gateway_mode(environment: Optional[str]) -> GatewayMode:
    env = (environment or "development").lower()
    if env in {"production", "prod"}:
        return GatewayMode.PRODUCTION
    if env in {"staging", "stage"}:
        return GatewayMode.STAGING
    return GatewayMode.DEVELOPMENT


def _extract_mapping(candidate: Any) -> Optional[Mapping[str, Any]]:
    if candidate is None:
        return None
    if isinstance(candidate, Mapping):
        return candidate
    model_dump = getattr(candidate, "model_dump", None)
    if callable(model_dump):
        try:
            data = model_dump()
        except Exception:  # pragma: no cover - defensive
            return None
        if isinstance(data, Mapping):
            return data
    return None


def _coerce_gateway_config(config: Any) -> GatewayConfig:
    if isinstance(config, GatewayConfig):
        return config

    environment = getattr(config, "environment", None) if config is not None else None
    mode = _resolve_gateway_mode(environment)

    if mode is GatewayMode.PRODUCTION:
        gateway_config = GatewayConfig.for_production()
    elif mode is GatewayMode.STAGING:
        gateway_config = GatewayConfig(mode=GatewayMode.STAGING)
    else:
        gateway_config = GatewayConfig.for_development()

    gateway_config.mode = mode

    if config is not None:
        name = getattr(config, "app_name", None)
        if isinstance(name, str) and name:
            gateway_config.name = name

        version = getattr(config, "app_version", None)
        if isinstance(version, str) and version:
            gateway_config.version = version

    api_mapping = _extract_mapping(getattr(config, "api_gateway", None)) if config is not None else None
    if api_mapping:
        if "rate_limit_enabled" in api_mapping:
            gateway_config.rate_limit.enabled = bool(api_mapping["rate_limit_enabled"])
        if api_mapping.get("rate_limit_requests") is not None:
            gateway_config.rate_limit.default_limit = int(api_mapping["rate_limit_requests"])
        if api_mapping.get("rate_limit_window") is not None:
            gateway_config.rate_limit.window_seconds = int(api_mapping["rate_limit_window"])

        if "circuit_breaker_enabled" in api_mapping:
            gateway_config.circuit_breaker.enabled = bool(api_mapping["circuit_breaker_enabled"])
        if api_mapping.get("circuit_breaker_failure_threshold") is not None:
            gateway_config.circuit_breaker.failure_threshold = int(
                api_mapping["circuit_breaker_failure_threshold"]
            )
        if api_mapping.get("circuit_breaker_recovery_timeout") is not None:
            gateway_config.circuit_breaker.recovery_timeout = int(
                api_mapping["circuit_breaker_recovery_timeout"]
            )

        if "versioning_enabled" in api_mapping:
            gateway_config.features["api_versioning"] = bool(api_mapping["versioning_enabled"])

        supported_versions = api_mapping.get("supported_versions")
        default_version = api_mapping.get("default_version")
        if (
            HeaderVersioning is not None
            and (supported_versions or default_version)
        ):
            versions = list(supported_versions or [])
            if not versions and isinstance(default_version, str):
                versions = [default_version]
            if not versions:
                versions = ["v1"]
            current_version = str(default_version) if default_version else versions[0]
            gateway_config.version_strategy = HeaderVersioning(
                supported_versions=versions,
                current_version=current_version,
                min_version=versions[0],
            )

    return gateway_config


def create_api_gateway(config: Any | None = None) -> FastAPI:
    """Create a FastAPI application configured as the DotMac API gateway."""

    gateway_config = _coerce_gateway_config(config)
    docs_enabled = gateway_config.mode is not GatewayMode.PRODUCTION

    app = FastAPI(
        title=gateway_config.name,
        version=gateway_config.version,
        docs_url="/docs" if docs_enabled else None,
        redoc_url="/redoc" if docs_enabled else None,
    )

    logger.info(
        "creating api gateway", mode=gateway_config.mode.value, name=gateway_config.name
    )

    gateway = setup_gateway_app(
        app,
        mode=gateway_config.mode.value,
        config=gateway_config,
    )

    app.state.gateway = gateway
    app.state.gateway_config = gateway_config

    return app
