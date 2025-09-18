"""Compatibility layer for core exception imports.

Historically the platform exposed common exception types from a dedicated
``dotmac.platform.core.exceptions`` module. Some parts of the codebase and
older tests still import from that path, so we provide a thin shim that
re-exports the canonical exception classes defined elsewhere in the core
package. Keeping this module lightweight avoids duplicating exception
hierarchies while preserving import compatibility for tests.
"""

from __future__ import annotations

from . import (
    AuthorizationError,
    BusinessRuleError,
    ConfigurationError,
    DotMacError,
    ValidationError,
)
from .repository import DuplicateEntityError, EntityNotFoundError, RepositoryError

__all__ = [
    "DotMacError",
    "AuthorizationError",
    "BusinessRuleError",
    "ConfigurationError",
    "ValidationError",
    "RepositoryError",
    "EntityNotFoundError",
    "DuplicateEntityError",
]
