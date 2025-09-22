"""Domain-specific models and exceptions for DotMac Platform.

This module contains only the essential domain models that are specific
to the DotMac platform. All utility functions have been replaced with
standard libraries.
"""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel as PydanticBaseModel, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict


# Domain-specific exceptions
class DotMacError(Exception):
    """Base exception for DotMac Framework."""


class ValidationError(DotMacError):
    """Validation error."""


class AuthorizationError(DotMacError):
    """Authorization error."""


class ConfigurationError(DotMacError):
    """Configuration error."""


class BusinessRuleError(DotMacError):
    """Business rule violation."""


# Repository exceptions (if still needed)
class RepositoryError(DotMacError):
    """Base repository error."""


class EntityNotFoundError(RepositoryError):
    """Entity not found in repository."""


class DuplicateEntityError(RepositoryError):
    """Duplicate entity in repository."""


# Base model for all domain entities
class BaseModel(PydanticBaseModel):
    """Base model for DotMac Framework entities."""

    model_config = ConfigDict(from_attributes=True, validate_assignment=True)


# Domain models
class TenantContext(BaseModel):
    """Tenant context information."""

    tenant_id: str
    tenant_name: str | None = None
    domain: str | None = None
    is_active: bool = True
    metadata: dict[str, Any] = {}

    @classmethod
    def create_default(cls) -> "TenantContext":
        """Create a default tenant context for testing."""
        return cls(
            tenant_id=str(uuid4()),
            tenant_name="Test Tenant",
            domain="test.example.com",
            is_active=True,
        )


# Application configuration using pydantic-settings
class Config(BaseSettings):
    """Main application configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application settings
    name: str = "dotmac-platform"
    version: str = "1.0.0"
    debug: bool = False
    testing: bool = False

    # Server settings
    host: str = "0.0.0.0"  # nosec B104
    port: int = 8000
    workers: int = 4
    reload: bool = False

    # CORS settings
    cors_enabled: bool = True
    cors_origins: list[str] = ["*"]
    cors_methods: list[str] = ["*"]
    cors_headers: list[str] = ["*"]

    # Security settings
    secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 30


# Use standard libraries directly:
# - datetime.now(timezone.utc) instead of utcnow()
# - str(uuid4()) instead of generate_id()
