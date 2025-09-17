"""
Configuration management system for DotMac Business Services.

Provides centralized configuration with environment support, validation,
and secure secrets management.
"""

from .base import (
    BaseConfig,
    CacheConfig,
    DatabaseConfig,
    LoggingConfig,
    ObservabilityConfig,
    RedisConfig,
    SecurityConfig,
)
from .environments import (
    DevelopmentConfig,
    ProductionConfig,
    StagingConfig,
    TestingConfig,
    get_config,
)
from .secure import SecureConfigManager, get_config_manager

__all__ = [
    # Base configurations
    "BaseConfig",
    "CacheConfig",
    "DatabaseConfig",
    "LoggingConfig",
    "ObservabilityConfig",
    "RedisConfig",
    "SecurityConfig",
    # Environment configurations
    "DevelopmentConfig",
    "ProductionConfig",
    "StagingConfig",
    "TestingConfig",
    "get_config",
    # Secure configuration
    "SecureConfigManager",
    "get_config_manager",
]
