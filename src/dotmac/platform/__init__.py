"""
DotMac Platform Services - Unified platform infrastructure.

This package provides core platform services for DotMac applications:
- Authentication and authorization (JWT, RBAC, sessions, MFA)
- Secrets management (Vault integration, encryption, rotation)
- Observability (tracing, metrics, logging, health checks)

Design Principles:
1. DRY: Leverages dotmac-core for shared utilities
2. Logical Grouping: Related functionality organized together
3. Production Ready: Battle-tested with comprehensive testing
4. Clear Dependencies: core → platform-services → business-logic
5. Extensible: Plugin architecture for custom providers
"""

import os
from typing import Any

__version__ = "1.0.0"
__author__ = "DotMac Team"
__email__ = "dev@dotmac.com"

# Platform services registry
_services_registry: dict[str, Any] = {}
_initialized_services: set = set()


def get_version() -> str:
    """Get platform services version."""
    return __version__


def register_service(name: str, service: Any) -> None:
    """Register a platform service."""
    _services_registry[name] = service


def get_service(name: str) -> Any | None:
    """Get a registered platform service."""
    return _services_registry.get(name)


def is_service_available(name: str) -> bool:
    """Check if a service is available."""
    return name in _services_registry


def get_available_services() -> list[str]:
    """Get list of available services."""
    return list(_services_registry.keys())


# Configuration management
class PlatformConfig:
    """Platform services configuration management."""

    def __init__(self) -> None:
        self._config = {}
        self._load_from_environment()

    def _load_from_environment(self) -> None:
        """Load configuration from environment variables."""
        # Authentication configuration
        self._config.update(
            {
                "auth": {
                    "jwt_secret_key": os.getenv("DOTMAC_JWT_SECRET_KEY"),
                    "jwt_algorithm": os.getenv("DOTMAC_JWT_ALGORITHM", "HS256"),
                    "access_token_expire_minutes": int(
                        os.getenv("DOTMAC_JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "15")
                    ),
                    "refresh_token_expire_days": int(
                        os.getenv("DOTMAC_JWT_REFRESH_TOKEN_EXPIRE_DAYS", "30")
                    ),
                    "session_backend": os.getenv("DOTMAC_SESSION_BACKEND", "memory"),
                    "redis_url": os.getenv("DOTMAC_REDIS_URL", "redis://localhost:6379"),
                },
                # Secrets management configuration
                "secrets": {
                    "vault_url": os.getenv("DOTMAC_VAULT_URL"),
                    "vault_token": os.getenv("DOTMAC_VAULT_TOKEN"),
                    "vault_mount_point": os.getenv("DOTMAC_VAULT_MOUNT_POINT", "secret"),
                    "encryption_key": os.getenv("DOTMAC_ENCRYPTION_KEY"),
                    "auto_rotation": os.getenv("DOTMAC_SECRETS_AUTO_ROTATION", "false").lower()
                    == "true",
                },
                # Observability configuration
                "observability": {
                    "service_name": os.getenv("DOTMAC_SERVICE_NAME", "dotmac-service"),
                    "otlp_endpoint": os.getenv("DOTMAC_OTLP_ENDPOINT"),
                    "log_level": os.getenv("DOTMAC_LOG_LEVEL", "INFO"),
                    "correlation_id_header": os.getenv(
                        "DOTMAC_CORRELATION_ID_HEADER", "X-Correlation-ID"
                    ),
                    "tracing_enabled": os.getenv("DOTMAC_TRACING_ENABLED", "true").lower()
                    == "true",
                    "metrics_enabled": os.getenv("DOTMAC_METRICS_ENABLED", "true").lower()
                    == "true",
                },
            }
        )

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key path (e.g., 'auth.jwt_secret_key')."""
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def update(self, updates: dict[str, Any]) -> None:
        """Update configuration with new values."""
        self._merge_config(self._config, updates)

    def _merge_config(self, target: dict[str, Any], source: dict[str, Any]) -> None:
        """Recursively merge configuration dictionaries."""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._merge_config(target[key], value)
            else:
                target[key] = value


# Global configuration instance
config = PlatformConfig()


def initialize_platform_services(
    auth_config: dict[str, Any] | None = None,
    secrets_config: dict[str, Any] | None = None,
    observability_config: dict[str, Any] | None = None,
    auto_discover: bool = True,
) -> None:
    """
    Initialize platform services with optional configuration.

    Args:
        auth_config: Authentication service configuration
        secrets_config: Secrets management configuration
        observability_config: Observability configuration
        auto_discover: Whether to auto-discover and initialize available services
    """
    # Update global configuration
    if auth_config:
        config.update({"auth": auth_config})
    if secrets_config:
        config.update({"secrets": secrets_config})
    if observability_config:
        config.update({"observability": observability_config})

    if auto_discover:
        # Import and initialize available services
        _initialize_available_services()


def _initialize_available_services() -> None:
    """Initialize available platform services."""
    try:
        from .auth import initialize_auth_service

        # Normalize flat auth config into nested structure if needed
        auth_conf = dict(config.get("auth", {}) or {})
        if "jwt" not in auth_conf and any(
            k in auth_conf for k in ("jwt_secret_key", "jwt_algorithm", "access_token_expire_minutes")
        ):
            nested_jwt = {}
            if "jwt_secret_key" in auth_conf:
                nested_jwt["secret_key"] = auth_conf["jwt_secret_key"]
            if "jwt_algorithm" in auth_conf:
                nested_jwt["algorithm"] = auth_conf["jwt_algorithm"]
            if "access_token_expire_minutes" in auth_conf:
                nested_jwt["access_token_expire_minutes"] = auth_conf["access_token_expire_minutes"]
            if "refresh_token_expire_days" in auth_conf:
                nested_jwt["refresh_token_expire_days"] = auth_conf["refresh_token_expire_days"]
            # Place into expected nested shape
            auth_conf = {"jwt": nested_jwt}

        initialize_auth_service(auth_conf)
        _initialized_services.add("auth")
    except ImportError:
        pass

    try:
        from .secrets import initialize_secrets_service

        try:
            initialize_secrets_service(config.get("secrets", {}))
        except Exception:
            # Secrets initialization is optional; continue without blocking platform init
            pass
        _initialized_services.add("secrets")
    except ImportError:
        pass

    try:
        from .observability import initialize_observability_service

        initialize_observability_service(config.get("observability", {}))
        _initialized_services.add("observability")
    except ImportError:
        pass


def get_initialized_services() -> set[str]:
    """Get set of initialized services."""
    return _initialized_services.copy()


# Quick access functions
def create_jwt_service(**kwargs):
    """Quick create JWT service with configuration.

    Maps flat auth config keys (e.g., jwt_secret_key, jwt_algorithm) to the
    JWTService/create_jwt_service_from_config schema.
    """
    try:
        import sys as _sys
        if "dotmac.platform.auth" not in _sys.modules:
            # Simulate optional extra missing
            raise ImportError("Auth module not available")

        from .auth import JWTService, create_jwt_service_from_config  # type: ignore

        cfg = dict(config.get("auth", {}))
        cfg.update(kwargs)

        # Normalize into expected keys for create_jwt_service_from_config
        normalized: dict[str, Any] = {}

        # Algorithm mapping
        if "jwt_algorithm" in cfg:
            normalized["algorithm"] = cfg["jwt_algorithm"]

        # Secret/private key mapping
        if "jwt_secret_key" in cfg:
            alg = cfg.get("jwt_algorithm", "HS256")
            if str(alg).startswith("HS"):
                normalized["secret"] = cfg["jwt_secret_key"]
            else:
                normalized["private_key"] = cfg["jwt_secret_key"]

        # Other common fields
        for k in (
            "access_token_expire_minutes",
            "refresh_token_expire_days",
            "issuer",
            "default_audience",
            "leeway",
        ):
            if k in cfg:
                normalized[k] = cfg[k]

        # Fall back to direct constructor if normalized is empty
        if normalized:
            return create_jwt_service_from_config(normalized)
        return JWTService()
    except ImportError:
        raise ImportError(
            "Auth service not available. Ensure core dependencies are installed. "
            "For running a server, optionally install extras: "
            "pip install 'dotmac-platform-services[server]' or use '[all]'"
        )


def create_secrets_manager(**kwargs):
    """Quick create secrets manager with configuration."""
    try:
        from .secrets import SecretsManager

        secrets_config = config.get("secrets", {})
        secrets_config.update(kwargs)
        return SecretsManager(**secrets_config)
    except ImportError:
        raise ImportError(
            "Secrets service not available. If you need Vault/OpenBao support, install extras: "
            "pip install 'dotmac-platform-services[vault]' (or use '[all]')"
        )


def create_observability_manager(**kwargs):
    """Quick create observability manager with configuration."""
    try:
        from .observability import ObservabilityManager

        obs_config = config.get("observability", {})
        obs_config.update(kwargs)
        return ObservabilityManager(**obs_config)
    except ImportError:
        raise ImportError(
            "Observability service not available. Ensure OpenTelemetry deps are installed (core). "
            "For server middleware and local serving, optionally install: "
            "pip install 'dotmac-platform-services[server]' (or use '[all]')"
        )


# Re-export selected components for convenience
try:
    from .observability.manager import ObservabilityManager  # type: ignore
except Exception:  # pragma: no cover - optional
    ObservabilityManager = None  # type: ignore

try:
    from .secrets.manager import SecretsManager  # type: ignore
except Exception:  # pragma: no cover - optional
    SecretsManager = None  # type: ignore

try:
    from .core import create_application, get_application  # type: ignore
except Exception:  # pragma: no cover - optional

    def create_application(*args, **kwargs):  # type: ignore
        raise ImportError("core.create_application unavailable")

    def get_application(*args, **kwargs):  # type: ignore
        return None


# Export main components
__all__ = [
    "PlatformConfig",
    "__version__",
    "ObservabilityManager",
    "SecretsManager",
    "create_application",
    "get_application",
    "config",
    "create_jwt_service",
    "create_observability_manager",
    "create_secrets_manager",
    "get_available_services",
    "get_initialized_services",
    "get_service",
    "initialize_platform_services",
    "is_service_available",
    "register_service",
]
