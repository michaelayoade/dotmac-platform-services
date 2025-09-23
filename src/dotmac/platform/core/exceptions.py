"""Domain-specific exceptions for DotMac Platform."""


class DotMacError(Exception):
    """Base exception for DotMac Framework."""


class ValidationError(DotMacError):
    """Validation error for invalid data."""


class AuthorizationError(DotMacError):
    """Authorization error for insufficient permissions."""


class ConfigurationError(DotMacError):
    """Configuration error for invalid settings."""


class BusinessRuleError(DotMacError):
    """Business rule violation error."""


class RepositoryError(DotMacError):
    """Base repository error."""


class EntityNotFoundError(RepositoryError):
    """Entity not found in repository."""


class DuplicateEntityError(RepositoryError):
    """Duplicate entity in repository."""
