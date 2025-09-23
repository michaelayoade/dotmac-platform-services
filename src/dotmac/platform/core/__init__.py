"""Core domain models and exceptions for DotMac Platform.

This module contains the essential domain models and exceptions that are
used throughout the DotMac platform.
"""

from .exceptions import (
    AuthorizationError,
    BusinessRuleError,
    ConfigurationError,
    DotMacError,
    DuplicateEntityError,
    EntityNotFoundError,
    RepositoryError,
    ValidationError,
)
from .models import BaseModel, TenantContext

__all__ = [
    # Exceptions
    "DotMacError",
    "ValidationError",
    "AuthorizationError",
    "ConfigurationError",
    "BusinessRuleError",
    "RepositoryError",
    "EntityNotFoundError",
    "DuplicateEntityError",
    # Models
    "BaseModel",
    "TenantContext",
]
