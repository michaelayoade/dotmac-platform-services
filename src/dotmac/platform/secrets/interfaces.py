"""
Interface definitions for secrets providers.
"""

from abc import ABC, abstractmethod
from typing import Any


class SecretsProvider(ABC):
    """Base interface for secrets providers."""

    @abstractmethod
    async def get_secret(self, secret_path: str, **kwargs: Any) -> dict[str, Any]:
        """
        Retrieve a secret by path.

        Args:
            secret_path: Path to the secret
            **kwargs: Provider-specific options

        Returns:
            Dictionary containing secret data

        Raises:
            Exception: If secret doesn't exist or retrieval fails
        """

    @abstractmethod
    async def list_secrets(self, secret_path: str = "") -> list[str]:
        """
        List secrets at given path.

        Args:
            secret_path: Path to list (root if empty)

        Returns:
            List of secret names/paths

        Raises:
            Exception: If listing fails
        """

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """
        Check provider health status.

        Returns:
            Dictionary with health information
        """


class WritableSecretsProvider(SecretsProvider):
    """Interface for providers that support writing secrets."""

    @abstractmethod
    async def set_secret(
        self, secret_path: str, secret_data: dict[str, Any], **kwargs: Any
    ) -> bool:
        """
        Store a secret at the given path.

        Args:
            secret_path: Path to store the secret
            secret_data: Secret data to store
            **kwargs: Provider-specific options

        Returns:
            True if successful

        Raises:
            Exception: If storage fails
        """

    @abstractmethod
    async def delete_secret(self, secret_path: str, **kwargs: Any) -> bool:
        """
        Delete a secret at the given path.

        Args:
            secret_path: Path to the secret
            **kwargs: Provider-specific options

        Returns:
            True if successful

        Raises:
            Exception: If deletion fails
        """


class SecretValidator(ABC):
    """Interface for secret validation."""

    @abstractmethod
    def validate(self, secret_data: dict[str, Any]) -> bool:
        """
        Validate secret data.

        Args:
            secret_data: Secret data to validate

        Returns:
            True if valid

        Raises:
            Exception: If validation fails
        """


class SecretCache(ABC):
    """Interface for secret caching."""

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """Get cached value."""

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Set cached value with optional TTL."""

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete cached value."""

    @abstractmethod
    async def clear(self) -> int:
        """Clear all cached values. Returns count of cleared items."""


class KeyRotationPolicy(ABC):
    """Interface for key rotation policies."""

    @abstractmethod
    def should_rotate(self, secret_metadata: dict[str, Any]) -> bool:
        """
        Determine if secret should be rotated.

        Args:
            secret_metadata: Metadata about the secret

        Returns:
            True if rotation is needed
        """

    @abstractmethod
    async def rotate(self, secret_path: str, current_secret: dict[str, Any]) -> dict[str, Any]:
        """
        Perform secret rotation.

        Args:
            secret_path: Path to the secret
            current_secret: Current secret data

        Returns:
            New secret data
        """


class ObservabilityHook(ABC):
    """Interface for observability hooks."""

    @abstractmethod
    async def on_secret_accessed(
        self, secret_path: str, operation: str, success: bool, duration_ms: float, **metadata: Any
    ) -> None:
        """Called when a secret is accessed."""

    @abstractmethod
    async def on_secret_modified(
        self, secret_path: str, operation: str, success: bool, **metadata: Any
    ) -> None:
        """Called when a secret is modified."""

    @abstractmethod
    async def on_error(
        self, error: Exception, secret_path: str | None = None, **metadata: Any
    ) -> None:
        """Called when an error occurs."""
