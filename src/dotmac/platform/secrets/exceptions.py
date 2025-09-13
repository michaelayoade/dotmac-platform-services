"""
Exception classes for secrets management.
"""

from collections.abc import Mapping
from typing import Any


class SecretsProviderError(Exception):
    """Base exception for secrets provider errors."""

    def __init__(
        self, message: str, provider: str = "unknown", details: Mapping[str, Any] | None = None
    ) -> None:
        super().__init__(message)
        self.message = message
        self.provider = provider
        self.details: dict[str, Any] = dict(details) if details is not None else {}


class SecretNotFoundError(SecretsProviderError):
    """Exception raised when a secret is not found."""

    def __init__(self, secret_path: str, provider: str = "unknown") -> None:
        message = f"Secret not found: {secret_path}"
        super().__init__(message, provider)
        self.secret_path = secret_path


class SecretValidationError(SecretsProviderError):
    """Exception raised when secret validation fails."""

    def __init__(self, message: str, validation_errors: list | None = None) -> None:
        super().__init__(message)
        self.validation_errors = validation_errors or []


class ProviderConnectionError(SecretsProviderError):
    """Exception raised when provider connection fails."""

    def __init__(self, provider: str, details: str = "") -> None:
        message = f"Failed to connect to {provider} provider: {details}"
        super().__init__(message, provider)


class ProviderAuthenticationError(SecretsProviderError):
    """Exception raised when provider authentication fails."""

    def __init__(self, provider: str, auth_method: str = "") -> None:
        message = f"Authentication failed for {provider} provider"
        if auth_method:
            message += f" using {auth_method}"
        super().__init__(message, provider)


class ProviderAuthorizationError(SecretsProviderError):
    """Exception raised when provider authorization fails."""

    def __init__(self, provider: str, resource: str = "", operation: str = "") -> None:
        message = f"Authorization failed for {provider} provider"
        if resource:
            message += f" on resource {resource}"
        if operation:
            message += f" for operation {operation}"
        super().__init__(message, provider)


class SecretExpiredError(SecretsProviderError):
    """Exception raised when a secret has expired."""

    def __init__(self, secret_path: str, expiry_time: str = "") -> None:
        message = f"Secret expired: {secret_path}"
        if expiry_time:
            message += f" at {expiry_time}"
        super().__init__(message)
        self.secret_path = secret_path
        self.expiry_time = expiry_time


class SecretsManagerError(Exception):
    """Exception raised by secrets manager."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.cause = cause


class ConfigurationError(Exception):
    """Exception raised for configuration errors."""

    def __init__(self, message: str, config_key: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.config_key = config_key
