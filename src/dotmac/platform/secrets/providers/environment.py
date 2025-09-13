"""
Environment variable secrets provider.
"""

import json
import os
from typing import Any

from ..exceptions import SecretNotFoundError
from ..interfaces import SecretsProvider


class EnvironmentProvider(SecretsProvider):
    """
    Secrets provider that reads from environment variables.
    """

    def __init__(self, prefix: str = "DOTMAC_SECRET_") -> None:
        """
        Initialize environment provider.

        Args:
            prefix: Prefix for environment variable names
        """
        self.prefix = prefix

    def _get_env_key(self, secret_path: str) -> str:
        """Convert secret path to environment variable key."""
        # Replace path separators with underscores
        clean_path = secret_path.replace("/", "_").replace("-", "_").upper()
        return f"{self.prefix}{clean_path}"

    async def get_secret(self, secret_path: str, **kwargs) -> dict[str, Any]:
        """
        Get secret from environment variable.

        Args:
            secret_path: Path to the secret
            **kwargs: Ignored for environment provider

        Returns:
            Dictionary containing secret data
        """
        env_key = self._get_env_key(secret_path)
        value = os.getenv(env_key)

        if value is None:
            raise SecretNotFoundError(secret_path, "environment")

        # Try to parse as JSON, fallback to string
        try:
            parsed_value = json.loads(value)
            if isinstance(parsed_value, dict):
                return parsed_value
            return {"value": parsed_value}
        except json.JSONDecodeError:
            return {"value": value}

    async def list_secrets(self, secret_path: str = "") -> list[str]:
        """
        List available secrets from environment variables.

        Args:
            secret_path: Path prefix to filter (ignored for environment)

        Returns:
            List of secret names
        """
        secrets = []
        prefix_len = len(self.prefix)

        for key in os.environ:
            if key.startswith(self.prefix):
                # Convert back to secret path format
                secret_name = key[prefix_len:].lower().replace("_", "/")
                secrets.append(secret_name)

        return sorted(secrets)

    async def health_check(self) -> dict[str, Any]:
        """
        Check environment provider health.

        Returns:
            Health status dictionary
        """
        return {
            "status": "healthy",
            "provider": "environment",
            "details": {"prefix": self.prefix, "available_secrets": len(await self.list_secrets())},
        }
