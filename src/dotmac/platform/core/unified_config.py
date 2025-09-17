"""
Unified configuration system for DotMac Platform Services.

This module provides a centralized configuration system that aggregates
all service configurations and provides environment-based defaults.
"""

import os
from typing import Optional
from pydantic import BaseModel, Field

# Import all service configurations
from ..auth.configs import AuthConfig, JWTConfig, MFAConfig, SessionConfig
from ..cache.config import CacheConfig
from ..database.config import DatabaseConfig
from ..observability.config import ObservabilityConfig
from ..secrets.config import SecretsConfig
from ..tenant.config import TenantConfig
from ..tasks.config import TasksConfig

# Import new service configurations
from ..service_registry.config import ServiceRegistryConfig, ServiceHealthConfig
from ..audit_trail.config import AuditTrailConfig, AuditEventConfig
from ..distributed_locks.config import DistributedLockConfig, LockSecurityConfig

# Import module-specific configurations
from ..api_gateway.config import APIGatewayConfig
from ..communications.config import CommunicationsConfig
from ..licensing.config import LicensingConfig
from ..monitoring.config import MonitoringConfig


class PlatformConfig(BaseModel):
    """
    Unified configuration for the entire DotMac Platform.

    This configuration aggregates all service-specific configurations
    and provides a single point of configuration management.
    """

    # Core application settings
    app_name: str = Field("dotmac-platform", description="Application name")
    app_version: str = Field("1.0.0", description="Application version")
    environment: str = Field("development", description="Environment (development, staging, production)")
    debug: bool = Field(False, description="Enable debug mode")

    # Core service configurations
    auth: AuthConfig = Field(default_factory=AuthConfig, description="Authentication configuration")
    jwt: JWTConfig = Field(default_factory=JWTConfig, description="JWT configuration")
    mfa: MFAConfig = Field(default_factory=MFAConfig, description="MFA configuration")
    session: SessionConfig = Field(default_factory=SessionConfig, description="Session configuration")

    cache: CacheConfig = Field(default_factory=CacheConfig, description="Cache configuration")
    database: DatabaseConfig = Field(default_factory=DatabaseConfig, description="Database configuration")
    observability: ObservabilityConfig = Field(default_factory=ObservabilityConfig, description="Observability configuration")
    secrets: SecretsConfig = Field(default_factory=SecretsConfig, description="Secrets management configuration")
    tenant: TenantConfig = Field(default_factory=TenantConfig, description="Multi-tenant configuration")
    tasks: TasksConfig = Field(default_factory=TasksConfig, description="Background tasks configuration")

    # New infrastructure services
    service_registry: ServiceRegistryConfig = Field(default_factory=ServiceRegistryConfig, description="Service registry configuration")
    service_health: ServiceHealthConfig = Field(default_factory=ServiceHealthConfig, description="Service health monitoring configuration")
    audit_trail: AuditTrailConfig = Field(default_factory=AuditTrailConfig, description="Audit trail configuration")
    audit_events: AuditEventConfig = Field(default_factory=AuditEventConfig, description="Audit event configuration")
    distributed_locks: DistributedLockConfig = Field(default_factory=DistributedLockConfig, description="Distributed locks configuration")
    lock_security: LockSecurityConfig = Field(default_factory=LockSecurityConfig, description="Lock security configuration")

    # Platform modules
    api_gateway: APIGatewayConfig = Field(default_factory=APIGatewayConfig, description="API Gateway configuration")
    communications: CommunicationsConfig = Field(default_factory=CommunicationsConfig, description="Communications configuration")
    licensing: LicensingConfig = Field(default_factory=LicensingConfig, description="Licensing configuration")
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig, description="Monitoring configuration")

    # Global settings
    timezone: str = Field("UTC", description="Default timezone")
    locale: str = Field("en_US", description="Default locale")

    @classmethod
    def from_environment(cls) -> "PlatformConfig":
        """
        Create configuration from environment variables.

        This method provides a convenient way to configure the platform
        using environment variables with sensible defaults.
        """
        config_data = {
            "app_name": os.getenv("APP_NAME", "dotmac-platform"),
            "app_version": os.getenv("APP_VERSION", "1.0.0"),
            "environment": os.getenv("ENVIRONMENT", "development"),
            "debug": os.getenv("DEBUG", "false").lower() == "true",
            "timezone": os.getenv("TIMEZONE", "UTC"),
            "locale": os.getenv("LOCALE", "en_US"),
        }

        # Create base config
        return cls(**config_data)

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() in ("development", "dev", "local")

    def is_testing(self) -> bool:
        """Check if running in test environment."""
        return self.environment.lower() in ("test", "testing")

    def get_redis_url(self) -> str:
        """Get the primary Redis URL (uses cache config as default)."""
        return self.cache.redis_url

    def get_database_url(self) -> str:
        """Get the primary database URL."""
        return self.database.database_url

    def get_service_name(self) -> str:
        """Get the service name for observability."""
        return f"{self.app_name}-{self.environment}"


class ConfigManager:
    """
    Configuration manager for the DotMac Platform.

    Provides centralized access to configuration with caching
    and environment-specific overrides.
    """

    _instance: Optional["ConfigManager"] = None
    _config: Optional[PlatformConfig] = None

    def __new__(cls) -> "ConfigManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_config(self) -> PlatformConfig:
        """Get the platform configuration (cached)."""
        if self._config is None:
            self._config = PlatformConfig.from_environment()
        return self._config

    def reload_config(self) -> PlatformConfig:
        """Reload configuration from environment."""
        self._config = PlatformConfig.from_environment()
        return self._config

    def get_auth_config(self) -> AuthConfig:
        """Get authentication configuration."""
        return self.get_config().auth

    def get_database_config(self) -> DatabaseConfig:
        """Get database configuration."""
        return self.get_config().database

    def get_cache_config(self) -> CacheConfig:
        """Get cache configuration."""
        return self.get_config().cache

    def get_service_registry_config(self) -> ServiceRegistryConfig:
        """Get service registry configuration."""
        return self.get_config().service_registry

    def get_audit_trail_config(self) -> AuditTrailConfig:
        """Get audit trail configuration."""
        return self.get_config().audit_trail

    def get_distributed_locks_config(self) -> DistributedLockConfig:
        """Get distributed locks configuration."""
        return self.get_config().distributed_locks


# Global configuration manager instance
config_manager = ConfigManager()


def get_config() -> PlatformConfig:
    """Get the global platform configuration."""
    return config_manager.get_config()


def get_auth_config() -> AuthConfig:
    """Get authentication configuration."""
    return config_manager.get_auth_config()


def get_database_config() -> DatabaseConfig:
    """Get database configuration."""
    return config_manager.get_database_config()


def get_service_registry_config() -> ServiceRegistryConfig:
    """Get service registry configuration."""
    return config_manager.get_service_registry_config()


def get_audit_trail_config() -> AuditTrailConfig:
    """Get audit trail configuration."""
    return config_manager.get_audit_trail_config()


def get_distributed_locks_config() -> DistributedLockConfig:
    """Get distributed locks configuration."""
    return config_manager.get_distributed_locks_config()


__all__ = [
    "PlatformConfig",
    "ConfigManager",
    "config_manager",
    "get_config",
    "get_auth_config",
    "get_database_config",
    "get_service_registry_config",
    "get_audit_trail_config",
    "get_distributed_locks_config",
]