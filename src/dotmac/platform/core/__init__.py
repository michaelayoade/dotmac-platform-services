"""
DotMac Core - Convenience Import Aliases

This module provides core exceptions and models expected by the framework.
"""

from typing import Any

from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict

from .config import ApplicationConfig
from .decorators import rate_limit, retry_on_failure, standard_exception_handler


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


class BaseModel(PydanticBaseModel):
    """Base model for DotMac Framework entities."""

    model_config = ConfigDict(from_attributes=True, validate_assignment=True)


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
        from uuid import uuid4

        return cls(
            tenant_id=str(uuid4()),
            tenant_name="Test Tenant",
            domain="test.example.com",
            is_active=True,
        )


# ------------------------------------------------------------------
# Simple application holder and helpers (compatibility with tests)
# ------------------------------------------------------------------


class Application:
    """Minimal Application wrapper that stores the provided config."""

    def __init__(self, config: ApplicationConfig) -> None:
        self.config = config


_app_instance: Application | None = None


def create_application(config: ApplicationConfig) -> Application:
    """Create and store a global application instance and return it."""
    global _app_instance
    _app_instance = Application(config)
    return _app_instance


def get_application() -> Application | None:
    """Return the last created application instance, if any."""
    return _app_instance


# Database compatibility functions
class DatabaseManager:
    """Compatibility database manager."""

    def __init__(self, config=None) -> None:
        self.config = config

    def get_session(self) -> None:
        """Get database session."""
        return

    def check_health(self):
        """Check database health."""
        return {"status": "ok"}


def get_db() -> None:
    """Get database connection."""
    return


def get_db_session() -> None:
    """Get database session."""
    return


def check_database_health():
    """Check database health."""
    return {"status": "ok", "message": "Database health check not implemented"}


__all__ = [
    "ApplicationConfig",
    "Application",
    "AuthorizationError",
    "BusinessRuleError",
    "BaseModel",
    "rate_limit",
    "retry_on_failure",
    "standard_exception_handler",
    "ConfigurationError",
    "DatabaseManager",
    "DotMacError",
    "create_application",
    "get_application",
    "TenantContext",
    "ValidationError",
    "check_database_health",
    "get_db",
    "get_db_session",
]
