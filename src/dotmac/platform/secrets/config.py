"""
Production-ready configuration for secrets management.
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .exceptions import ConfigurationError


class SecretsBackend(str, Enum):
    """Supported secrets backends."""

    OPENBAO = "openbao"
    VAULT = "vault"  # Alias for openbao
    ENVIRONMENT = "environment"
    FILE = "file"
    MEMORY = "memory"


class CacheBackend(str, Enum):
    """Supported cache backends."""

    MEMORY = "memory"
    REDIS = "redis"
    NULL = "null"


@dataclass
class SecretsConfig:
    """
    Production-ready secrets configuration.

    Supports configuration from environment variables with validation.
    """

    # Provider configuration
    backend: SecretsBackend = SecretsBackend.OPENBAO
    vault_url: str | None = None
    vault_token: str | None = None
    vault_mount_point: str = "secret"
    vault_kv_version: int = 2
    vault_namespace: str | None = None
    vault_verify_ssl: bool = True

    # Multi-tenancy
    tenant_id: str | None = None
    tenant_path_prefix: str = "tenant"

    # Caching
    cache_backend: CacheBackend = CacheBackend.MEMORY
    cache_ttl: int = 300  # 5 minutes
    cache_max_size: int = 1000
    redis_url: str | None = None

    # Security
    encryption_key: str | None = None
    enable_field_encryption: bool = True

    # Performance
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    connection_pool_size: int = 20

    # Observability
    enable_metrics: bool = True
    enable_audit_logging: bool = True
    log_secret_access: bool = False  # Security sensitive

    # Validation
    enable_validation: bool = True
    validation_strict: bool = False

    # Environment
    environment: str = "development"

    # Additional provider-specific config
    provider_config: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate and normalize configuration."""
        self._load_from_environment()
        self._validate_config()
        self._normalize_config()

    def _load_from_environment(self) -> None:
        """Load configuration from environment variables."""
        # Backend selection
        if env_backend := os.getenv("DOTMAC_SECRETS_BACKEND"):
            try:
                self.backend = SecretsBackend(env_backend.lower())
            except ValueError:
                raise ConfigurationError(f"Invalid secrets backend: {env_backend}")

        # OpenBao/Vault configuration
        self.vault_url = os.getenv("DOTMAC_VAULT_URL") or self.vault_url
        self.vault_token = os.getenv("DOTMAC_VAULT_TOKEN") or self.vault_token
        self.vault_mount_point = os.getenv("DOTMAC_VAULT_MOUNT_POINT", self.vault_mount_point)
        self.vault_namespace = os.getenv("DOTMAC_VAULT_NAMESPACE") or self.vault_namespace

        if env_kv_version := os.getenv("DOTMAC_VAULT_KV_VERSION"):
            try:
                self.vault_kv_version = int(env_kv_version)
            except ValueError:
                raise ConfigurationError(f"Invalid KV version: {env_kv_version}")

        if env_verify_ssl := os.getenv("DOTMAC_VAULT_VERIFY_SSL"):
            self.vault_verify_ssl = env_verify_ssl.lower() in ("true", "1", "yes", "on")

        # Multi-tenancy
        self.tenant_id = os.getenv("DOTMAC_TENANT_ID") or self.tenant_id
        self.tenant_path_prefix = os.getenv("DOTMAC_TENANT_PATH_PREFIX", self.tenant_path_prefix)

        # Caching
        if env_cache_backend := os.getenv("DOTMAC_CACHE_BACKEND"):
            try:
                self.cache_backend = CacheBackend(env_cache_backend.lower())
            except ValueError:
                raise ConfigurationError(f"Invalid cache backend: {env_cache_backend}")

        if env_cache_ttl := os.getenv("DOTMAC_CACHE_TTL"):
            try:
                self.cache_ttl = int(env_cache_ttl)
            except ValueError:
                raise ConfigurationError(f"Invalid cache TTL: {env_cache_ttl}")

        self.redis_url = os.getenv("DOTMAC_REDIS_URL") or self.redis_url

        # Security
        self.encryption_key = os.getenv("DOTMAC_ENCRYPTION_KEY") or self.encryption_key

        if env_field_encryption := os.getenv("DOTMAC_ENABLE_FIELD_ENCRYPTION"):
            self.enable_field_encryption = env_field_encryption.lower() in (
                "true",
                "1",
                "yes",
                "on",
            )

        # Performance
        if env_timeout := os.getenv("DOTMAC_SECRETS_TIMEOUT"):
            try:
                self.timeout = int(env_timeout)
            except ValueError:
                raise ConfigurationError(f"Invalid timeout: {env_timeout}")

        if env_max_retries := os.getenv("DOTMAC_SECRETS_MAX_RETRIES"):
            try:
                self.max_retries = int(env_max_retries)
            except ValueError:
                raise ConfigurationError(f"Invalid max retries: {env_max_retries}")

        # Environment
        self.environment = os.getenv("ENVIRONMENT", "development").lower()

    def _validate_config(self) -> None:
        """Validate configuration for consistency and security."""
        validation_errors = []

        # Backend-specific validation
        if self.backend in (SecretsBackend.OPENBAO, SecretsBackend.VAULT):
            if not self.vault_url:
                validation_errors.append("vault_url is required for OpenBao/Vault backend")
            if not self.vault_token:
                validation_errors.append("vault_token is required for OpenBao/Vault backend")
            if self.vault_kv_version not in (1, 2):
                validation_errors.append("vault_kv_version must be 1 or 2")

        # Cache backend validation
        if self.cache_backend == CacheBackend.REDIS and not self.redis_url:
            validation_errors.append("redis_url is required for Redis cache backend")

        # Security validation
        if self.enable_field_encryption and not self.encryption_key:
            validation_errors.append("encryption_key is required when field encryption is enabled")

        # Production environment validation
        if self.environment == "production":
            if self.backend == SecretsBackend.MEMORY:
                validation_errors.append("Memory backend not recommended for production")
            if self.cache_backend == CacheBackend.MEMORY:
                validation_errors.append("Memory cache not recommended for production")
            if self.vault_url and "localhost" in self.vault_url:
                validation_errors.append("Localhost Vault URL detected in production")
            if not self.vault_verify_ssl and self.backend in (
                SecretsBackend.OPENBAO,
                SecretsBackend.VAULT,
            ):
                validation_errors.append("SSL verification disabled in production")

        # Performance validation
        if self.timeout <= 0:
            validation_errors.append("timeout must be positive")
        if self.max_retries < 0:
            validation_errors.append("max_retries must be non-negative")
        if self.cache_ttl <= 0:
            validation_errors.append("cache_ttl must be positive")

        if validation_errors:
            raise ConfigurationError(
                f"Configuration validation failed: {'; '.join(validation_errors)}"
            )

    def _normalize_config(self) -> None:
        """Normalize configuration values."""
        # Normalize URLs
        if self.vault_url:
            self.vault_url = self.vault_url.rstrip("/")

        if self.redis_url:
            self.redis_url = self.redis_url.rstrip("/")

        # Normalize paths
        self.vault_mount_point = self.vault_mount_point.strip("/")
        self.tenant_path_prefix = self.tenant_path_prefix.strip("/")

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "backend": self.backend.value,
            "vault_url": self.vault_url,
            "vault_mount_point": self.vault_mount_point,
            "vault_kv_version": self.vault_kv_version,
            "vault_namespace": self.vault_namespace,
            "vault_verify_ssl": self.vault_verify_ssl,
            "tenant_id": self.tenant_id,
            "tenant_path_prefix": self.tenant_path_prefix,
            "cache_backend": self.cache_backend.value,
            "cache_ttl": self.cache_ttl,
            "cache_max_size": self.cache_max_size,
            "redis_url": self.redis_url,
            "enable_field_encryption": self.enable_field_encryption,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "connection_pool_size": self.connection_pool_size,
            "enable_metrics": self.enable_metrics,
            "enable_audit_logging": self.enable_audit_logging,
            "enable_validation": self.enable_validation,
            "validation_strict": self.validation_strict,
            "environment": self.environment,
        }

    def get_provider_config(self) -> dict[str, Any]:
        """Get provider-specific configuration."""
        if self.backend in (SecretsBackend.OPENBAO, SecretsBackend.VAULT):
            return {
                "url": self.vault_url,
                "token": self.vault_token,
                "mount_point": self.vault_mount_point,
                "kv_version": self.vault_kv_version,
                "namespace": self.vault_namespace,
                "tenant_id": self.tenant_id,
                "verify_ssl": self.vault_verify_ssl,
                "timeout": self.timeout,
                "max_retries": self.max_retries,
                "retry_delay": self.retry_delay,
                **self.provider_config,
            }
        return self.provider_config.copy()

    def get_cache_config(self) -> dict[str, Any]:
        """Get cache-specific configuration."""
        config = {
            "backend": self.cache_backend.value,
            "ttl": self.cache_ttl,
            "max_size": self.cache_max_size,
        }

        if self.cache_backend == CacheBackend.REDIS:
            config["redis_url"] = self.redis_url

        return config

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    def validate_production_readiness(self) -> list[str]:
        """Validate production readiness and return warnings."""
        warnings = []

        if not self.is_production():
            return warnings

        # Security checks
        if not self.vault_verify_ssl:
            warnings.append("SSL verification is disabled")

        if self.vault_url and ("localhost" in self.vault_url or "127.0.0.1" in self.vault_url):
            warnings.append("Vault URL appears to be localhost")

        if self.encryption_key and len(self.encryption_key) < 32:
            warnings.append("Encryption key is shorter than recommended 32 characters")

        # Performance checks
        if self.cache_backend == CacheBackend.MEMORY:
            warnings.append("Using memory cache in production")

        if self.timeout < 30:
            warnings.append("Timeout is less than recommended 30 seconds for production")

        # Monitoring checks
        if not self.enable_metrics:
            warnings.append("Metrics are disabled")

        if not self.enable_audit_logging:
            warnings.append("Audit logging is disabled")

        return warnings


def create_default_config(**overrides) -> SecretsConfig:
    """Create default secrets configuration with optional overrides."""
    return SecretsConfig(**overrides)


def create_openbao_config(vault_url: str, vault_token: str, **kwargs) -> SecretsConfig:
    """Create OpenBao-specific configuration."""
    return SecretsConfig(
        backend=SecretsBackend.OPENBAO, vault_url=vault_url, vault_token=vault_token, **kwargs
    )


def create_development_config() -> SecretsConfig:
    """Create development configuration."""
    return SecretsConfig(
        backend=SecretsBackend.ENVIRONMENT,
        cache_backend=CacheBackend.MEMORY,
        enable_field_encryption=False,
        enable_validation=False,
        environment="development",
    )


def create_production_config() -> SecretsConfig:
    """Create production configuration from environment."""
    config = SecretsConfig(environment="production")

    # Validate production readiness
    warnings = config.validate_production_readiness()
    if warnings:
        import logging

        logger = logging.getLogger(__name__)
        for warning in warnings:
            logger.warning(f"Production configuration warning: {warning}")

    return config
