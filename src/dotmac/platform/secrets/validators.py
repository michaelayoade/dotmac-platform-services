"""
Secret validators for common secret types.
"""

from typing import Any

from .exceptions import SecretValidationError
from .interfaces import SecretValidator


class JWTValidator(SecretValidator):
    """Validator for JWT keypairs."""

    def validate(self, secret_data: dict[str, Any]) -> bool:
        """Validate JWT keypair format."""
        required_keys = {"private_key", "public_key", "algorithm"}

        if not isinstance(secret_data, dict):
            raise SecretValidationError("JWT secret must be a dictionary")

        missing_keys = required_keys - set(secret_data.keys())
        if missing_keys:
            raise SecretValidationError(f"JWT secret missing keys: {missing_keys}")

        # Validate algorithm
        valid_algorithms = {
            "HS256",
            "HS384",
            "HS512",
            "RS256",
            "RS384",
            "RS512",
            "ES256",
            "ES384",
            "ES512",
        }
        if secret_data["algorithm"] not in valid_algorithms:
            raise SecretValidationError(f"Invalid algorithm: {secret_data['algorithm']}")

        return True


class DatabaseCredentialsValidator(SecretValidator):
    """Validator for database credentials."""

    def validate(self, secret_data: dict[str, Any]) -> bool:
        """Validate database credentials format."""
        required_keys = {"host", "port", "database", "username", "password"}

        if not isinstance(secret_data, dict):
            raise SecretValidationError("Database credentials must be a dictionary")

        missing_keys = required_keys - set(secret_data.keys())
        if missing_keys:
            raise SecretValidationError(f"Database credentials missing keys: {missing_keys}")

        # Validate port
        try:
            port = int(secret_data["port"])
            if not (1 <= port <= 65535):
                raise SecretValidationError("Port must be between 1 and 65535")
        except (ValueError, TypeError):
            raise SecretValidationError("Port must be a valid integer")

        return True


class PolicyValidator(SecretValidator):
    """Validator for secret policies."""

    def validate(self, secret_data: dict[str, Any]) -> bool:
        """Validate secret policy format."""
        if not isinstance(secret_data, dict):
            raise SecretValidationError("Secret policy must be a dictionary")

        # Basic policy validation
        if "rules" in secret_data and not isinstance(secret_data["rules"], list):
            raise SecretValidationError("Policy rules must be a list")

        return True


class DefaultValidator(SecretValidator):
    """Default validator that performs basic checks."""

    def validate(self, secret_data: dict[str, Any]) -> bool:
        """Perform basic validation."""
        if not isinstance(secret_data, dict):
            raise SecretValidationError("Secret data must be a dictionary")

        if not secret_data:
            raise SecretValidationError("Secret data cannot be empty")

        return True


def create_default_validator() -> SecretValidator:
    """Create default secret validator."""
    return DefaultValidator()


def create_jwt_validator() -> SecretValidator:
    """Create JWT secret validator."""
    return JWTValidator()


def create_database_validator() -> SecretValidator:
    """Create database credentials validator."""
    return DatabaseCredentialsValidator()


def create_policy_validator() -> SecretValidator:
    """Create policy validator."""
    return PolicyValidator()
