"""
Enhanced repository exceptions for better error handling.
"""


class RepositoryError(Exception):
    """Base exception for repository operations."""

    pass


class EntityNotFoundError(RepositoryError):
    """Raised when an entity is not found."""

    pass


class DuplicateEntityError(RepositoryError):
    """Raised when attempting to create a duplicate entity."""

    pass


class ValidationError(RepositoryError):
    """Raised when validation fails."""

    pass


__all__ = [
    "RepositoryError",
    "EntityNotFoundError",
    "DuplicateEntityError",
    "ValidationError",
]