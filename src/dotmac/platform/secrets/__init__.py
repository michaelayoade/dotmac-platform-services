"""
DotMac Platform Secrets Management

Comprehensive secrets management services including:
- HashiCorp Vault / OpenBao integration
- Field-level encryption/decryption
- Secrets rotation automation
- Multi-tenant secrets isolation
- Environment-based configuration
- Audit logging for secret access
- Cache management for performance
- Production-ready validation

Design Principles:
- Security-first approach with encryption at rest
- Multi-tenant isolation with path-based separation
- Performance optimization with intelligent caching
- Production-ready with comprehensive validation
- Extensible provider architecture
- DRY leveraging dotmac-core utilities
"""

import os
import warnings
from typing import Any

try:
    from .config import (
        SecretsConfig,
        SecretsBackend,
        create_default_config,
        create_openbao_config,
        create_production_config,
    )
    from .manager import SecretsManager

    _manager_available = True
except ImportError as e:
    warnings.warn(f"Secrets manager not available: {e}", stacklevel=2)
    SecretsManager = SecretsConfig = None
    create_default_config = create_openbao_config = create_production_config = None
    _manager_available = False

# Provider interfaces and implementations
try:
    from .interfaces import SecretsProvider, WritableSecretsProvider
    from .openbao_provider import OpenBaoProvider, create_openbao_provider

    # Alias for backward compatibility
    VaultProvider = OpenBaoProvider
    create_vault_provider = create_openbao_provider
    _providers_available = True
except ImportError as e:
    warnings.warn(f"Secrets providers not available: {e}", stacklevel=2)
    SecretsProvider = WritableSecretsProvider = None
    OpenBaoProvider = VaultProvider = None
    create_openbao_provider = create_vault_provider = None
    _providers_available = False

# Environment and file providers (lightweight)
try:
    from .providers.environment import EnvironmentProvider
    from .providers.file import FileProvider

    _basic_providers_available = True
except ImportError as e:
    warnings.warn(f"Basic providers not available: {e}", stacklevel=2)
    EnvironmentProvider = FileProvider = None
    _basic_providers_available = False

# Field encryption
try:
    from .encryption import (
        DataClassification,
        EncryptedField,
        FieldEncryption,
        SymmetricEncryptionService,
    )

    _encryption_available = True
except ImportError as e:
    warnings.warn(f"Field encryption not available: {e}", stacklevel=2)
    FieldEncryption = EncryptedField = DataClassification = None
    _encryption_available = False

# Secret rotation
try:
    from .rotation import (
        DefaultRotationPolicy,
        JWTRotationPolicy,
        RotationResult,
        RotationRule,
        RotationScheduler,
        RotationStatus,
    )

    _rotation_available = True
except ImportError as e:
    warnings.warn(f"Secrets rotation not available: {e}", stacklevel=2)
    RotationScheduler = RotationRule = RotationResult = None
    RotationStatus = DefaultRotationPolicy = JWTRotationPolicy = None
    _rotation_available = False

# Caching
try:
    from .cache import InMemoryCache, NullCache, RedisCache, SecretCache

    _cache_available = True
except ImportError as e:
    warnings.warn(f"Secrets caching not available: {e}", stacklevel=2)
    SecretCache = InMemoryCache = RedisCache = NullCache = None
    _cache_available = False

# Validation
try:
    from .validators import (
        DatabaseCredentialsValidator,
        JWTValidator,
        PolicyValidator,
        SecretValidator,
    )

    _validators_available = True
except ImportError as e:
    warnings.warn(f"Secret validators not available: {e}", stacklevel=2)
    SecretValidator = JWTValidator = DatabaseCredentialsValidator = None
    PolicyValidator = None
    _validators_available = False

# Types and exceptions
try:
    from .exceptions import (
        ConfigurationError,
        ProviderAuthenticationError,
        ProviderAuthorizationError,
        ProviderConnectionError,
        SecretExpiredError,
        SecretNotFoundError,
        SecretsManagerError,
        SecretsProviderError,
        SecretValidationError,
    )
    from .types import (
        DatabaseCredentials,
        Environment,
        JWTKeypair,
        SecretKind,
        SecretMetadata,
        SecretPolicy,
        SecretValue,
    )

    _types_available = True
except ImportError as e:
    warnings.warn(f"Secrets types/exceptions not available: {e}", stacklevel=2)
    SecretKind = Environment = JWTKeypair = DatabaseCredentials = None
    SecretPolicy = SecretMetadata = SecretValue = None
    SecretsProviderError = SecretNotFoundError = SecretValidationError = None
    ProviderConnectionError = ProviderAuthenticationError = None
    ProviderAuthorizationError = SecretExpiredError = None
    SecretsManagerError = ConfigurationError = None
    _types_available = False

# Service initialization and management
_secrets_service_registry: dict[str, Any] = {}


def initialize_secrets_service(config: dict[str, Any]) -> None:
    """Initialize secrets management services with configuration."""
    if not _manager_available:
        warnings.warn("Secrets manager not available, skipping initialization", stacklevel=2)
        return

    # If no meaningful config provided, skip initialization gracefully
    minimal_keys = {
        k
        for k in ("vault_url", "vault_token", "backend", "file_path", "encryption_key")
        if k in config
    }
    if not minimal_keys:
        return

    # Create a config appropriate to provided settings
    try:
        backend = (config.get("backend") or "").lower()
        if backend == "environment":
            manager_config = SecretsConfig(backend=SecretsBackend.ENVIRONMENT)
        elif backend == "file":
            manager_config = SecretsConfig(backend=SecretsBackend.FILE)
            if "file_path" in config:
                manager_config.provider_config["file_path"] = config["file_path"]
        else:
            manager_config = SecretsConfig(
                vault_url=config.get("vault_url"),
                vault_token=config.get("vault_token"),
                vault_mount_point=config.get("vault_mount_point", "secret"),
                environment=config.get("environment", "development"),
            )

        if "cache_ttl" in config:
            manager_config.cache_ttl = int(config["cache_ttl"])  # type: ignore[attr-defined]

        manager = create_secrets_manager(config=manager_config)
        _secrets_service_registry["manager"] = manager
    except Exception:
        # Skip secrets manager initialization on invalid/missing config
        return

    # Initialize field encryption if available
    if _encryption_available and config.get("encryption_key"):
        encryption_service = SymmetricEncryptionService(config["encryption_key"])
        _secrets_service_registry["encryption"] = encryption_service

    # Initialize rotation scheduler if available
    if _rotation_available:
        scheduler = RotationScheduler()
        _secrets_service_registry["rotation"] = scheduler


def get_secrets_service(name: str) -> Any | None:
    """Get an initialized secrets service."""
    return _secrets_service_registry.get(name)


def is_secrets_service_available(name: str) -> bool:
    """Check if secrets service is available."""
    return name in _secrets_service_registry


# Factory functions for creating services
def create_secrets_manager(
    config: SecretsConfig | None = None,
    vault_url: str | None = None,
    vault_token: str | None = None,
    **kwargs,
) -> Any | None:
    """Create a secrets manager with configuration."""
    if not _manager_available:
        raise ImportError("Secrets manager not available")

    if config is None:
        # Create config from parameters
        if vault_url and vault_token:
            config = create_openbao_config(vault_url, vault_token, **kwargs)
        else:
            config = create_default_config(**kwargs)

    # Create provider based on config
    provider = None
    if config.backend in ("openbao", "vault"):
        if not _providers_available:
            raise ImportError("OpenBao provider not available")
        provider = create_openbao_provider(**config.get_provider_config())
    elif config.backend == "environment":
        if not _basic_providers_available:
            raise ImportError("Environment provider not available")
        provider = EnvironmentProvider()
    elif config.backend == "file":
        if not _basic_providers_available:
            raise ImportError("File provider not available")
        file_path = config.provider_config.get("file_path", "secrets.json")
        provider = FileProvider(file_path)
    else:
        raise ValueError(f"Unknown backend: {config.backend}")

    return SecretsManager(provider=provider)


def create_production_secrets_manager() -> Any | None:
    """Create production-ready secrets manager from environment."""
    if not _manager_available:
        raise ImportError("Secrets manager not available")

    config = create_production_config()
    return create_secrets_manager(config=config)


def create_openbao_secrets_manager(
    url: str, token: str, mount_point: str = "secret", **kwargs
) -> Any | None:
    """Create secrets manager with OpenBao provider."""
    config = create_openbao_config(
        vault_url=url, vault_token=token, vault_mount_point=mount_point, **kwargs
    )
    return create_secrets_manager(config=config)


# Backward compatibility alias
create_vault_secrets_manager = create_openbao_secrets_manager


def create_field_encryption(encryption_key: str) -> Any | None:
    """Create field encryption service."""
    if not _encryption_available:
        raise ImportError("Field encryption not available")

    return FieldEncryption(encryption_key=encryption_key)


def create_rotation_scheduler(policies: list | None = None) -> Any | None:
    """Create secrets rotation scheduler."""
    if not _rotation_available:
        raise ImportError("Secrets rotation not available")

    scheduler = RotationScheduler()

    if policies:
        for policy in policies:
            scheduler.add_policy(policy)

    return scheduler


def create_secret_cache(cache_type: str = "memory", **kwargs) -> Any | None:
    """Create secret cache."""
    if not _cache_available:
        raise ImportError("Secret caching not available")

    if cache_type.lower() == "redis":
        redis_url = kwargs.get("redis_url", os.getenv("REDIS_URL", "redis://localhost:6379"))
        return RedisCache(redis_url=redis_url, **kwargs)
    if cache_type.lower() == "memory":
        return InMemoryCache(**kwargs)
    if cache_type.lower() == "null":
        return NullCache()
    raise ValueError(f"Unknown cache type: {cache_type}")


# Utility functions
def get_current_environment() -> str:
    """Get current environment from configuration."""
    return os.getenv("ENVIRONMENT", "development").lower()


def is_production_environment() -> bool:
    """Check if running in production environment."""
    return get_current_environment() == "production"


def validate_production_config() -> list[str]:
    """Validate configuration for production use."""
    warnings_list = []

    if is_production_environment():
        # Check required environment variables
        required_vars = ["DOTMAC_VAULT_URL", "DOTMAC_VAULT_TOKEN", "DOTMAC_ENCRYPTION_KEY"]

        for var in required_vars:
            if not os.getenv(var):
                warnings_list.append(f"Missing required environment variable: {var}")

        # Check for development defaults
        vault_url = os.getenv("DOTMAC_VAULT_URL", "")
        if "localhost" in vault_url or "127.0.0.1" in vault_url:
            warnings_list.append("Vault URL appears to be localhost in production")

        encryption_key = os.getenv("DOTMAC_ENCRYPTION_KEY", "")
        if len(encryption_key) < 32:
            warnings_list.append("Encryption key is too short for production use")

    return warnings_list


# Version and metadata
__version__ = "1.0.0"
__author__ = "DotMac Team"
__email__ = "dev@dotmac.com"

# Export everything that's available
__all__ = [
    # Version
    "__version__",
    "create_field_encryption",
    "create_rotation_scheduler",
    "create_secret_cache",
    # Factory functions
    "create_secrets_manager",
    "create_vault_provider",
    # Utilities
    "get_current_environment",
    "get_secrets_service",
    # Service management
    "initialize_secrets_service",
    "is_production_environment",
    "is_secrets_service_available",
    "validate_production_config",
]

# Add available components to exports
if _manager_available:
    __all__.extend(
        [
            "SecretsConfig",
            "SecretsManager",
        ]
    )

if _providers_available:
    __all__.extend(
        [
            "EnvironmentProvider",
            "FileProvider",
            "SecretsProvider",
            "VaultProvider",
            "WritableSecretsProvider",
        ]
    )

if _encryption_available:
    __all__.extend(
        [
            "DataClassification",
            "EncryptedField",
            "FieldEncryption",
        ]
    )

if _rotation_available:
    __all__.extend(
        [
            "DefaultRotationPolicy",
            "JWTRotationPolicy",
            "RotationResult",
            "RotationRule",
            "RotationScheduler",
            "RotationStatus",
        ]
    )

if _cache_available:
    __all__.extend(
        [
            "InMemoryCache",
            "NullCache",
            "RedisCache",
            "SecretCache",
        ]
    )

if _validators_available:
    __all__.extend(
        [
            "DatabaseCredentialsValidator",
            "JWTValidator",
            "PolicyValidator",
            "SecretValidator",
        ]
    )

if _types_available:
    __all__.extend(
        [
            "ConfigurationError",
            "DatabaseCredentials",
            "Environment",
            "JWTKeypair",
            "ProviderAuthenticationError",
            "ProviderAuthorizationError",
            "ProviderConnectionError",
            "SecretExpiredError",
            "SecretKind",
            "SecretMetadata",
            "SecretNotFoundError",
            "SecretPolicy",
            "SecretValidationError",
            "SecretValue",
            "SecretsManagerError",
            "SecretsProviderError",
        ]
    )


# Production configuration check
def _check_production_config() -> None:
    """Check configuration on module import for production."""
    try:
        if is_production_environment():
            config_warnings = validate_production_config()
            for warning in config_warnings:
                warnings.warn(warning, UserWarning, stacklevel=2)
    except Exception:
        # Don't fail on import if validation fails
        pass


# Only run production check if not in testing
if not os.getenv("PYTEST_CURRENT_TEST"):
    _check_production_config()
