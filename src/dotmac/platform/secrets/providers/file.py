"""
File-based secrets provider.
"""

import json
import os
from typing import Any

from ..exceptions import ConfigurationError, SecretNotFoundError, SecretsProviderError
from ..interfaces import WritableSecretsProvider


class FileProvider(WritableSecretsProvider):
    """
    File-based secrets provider for development and testing.
    """

    def __init__(self, file_path: str = "secrets.json") -> None:
        """
        Initialize file provider.

        Args:
            file_path: Path to the secrets file
        """
        self.file_path = file_path
        self._secrets_cache: dict[str, Any] | None = None

    def _load_secrets(self) -> dict[str, Any]:
        """Load secrets from file.

        Behavior:
        - Cached value is returned when available
        - If file does not exist, return empty dict and cache it
        - Invalid JSON raises ConfigurationError
        - Permission and other IO errors raise SecretsProviderError
        """
        if self._secrets_cache is not None:
            return self._secrets_cache

        try:
            with open(self.file_path, encoding="utf-8") as f:
                self._secrets_cache = json.load(f)
                return self._secrets_cache
        except FileNotFoundError:
            self._secrets_cache = {}
            return self._secrets_cache
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in secrets file: {e}") from e
        except Exception as e:
            raise SecretsProviderError(f"Failed to load secrets file: {e}", "file") from e

    def _save_secrets(self, secrets: dict[str, Any]) -> None:
        """Save secrets to file."""
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(secrets, f, indent=2, ensure_ascii=False)
                self._secrets_cache = secrets
        except Exception as e:
            raise SecretsProviderError(f"Failed to save secrets file: {e}", "file") from e

    def _get_nested_value(self, secrets: dict[str, Any], path: str) -> Any:
        """Get nested value from secrets using dot notation path."""
        parts = path.split("/")
        current = secrets

        for part in parts:
            if not part:  # Skip empty parts from leading/trailing slashes
                continue
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                raise SecretNotFoundError(path, "file")

        return current

    def _set_nested_value(self, secrets: dict[str, Any], path: str, value: Any) -> None:
        """Set nested value in secrets using dot notation path."""
        parts = [p for p in path.split("/") if p]  # Remove empty parts
        current = secrets

        # Navigate to the parent of the target key
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            elif not isinstance(current[part], dict):
                raise SecretsProviderError(f"Cannot set nested value: {part} is not a dict", "file")
            current = current[part]

        # Set the final value
        if parts:
            current[parts[-1]] = value

    async def get_secret(self, secret_path: str, **kwargs: Any) -> dict[str, Any]:
        """
        Get secret from file.

        Args:
            secret_path: Path to the secret
            **kwargs: Ignored for file provider

        Returns:
            Dictionary containing secret data
        """
        try:
            secrets = self._load_secrets()
            value = self._get_nested_value(secrets, secret_path)

            if isinstance(value, dict):
                return value
            return {"value": value}
        except SecretNotFoundError:
            raise
        except Exception as e:
            raise SecretsProviderError(f"Failed to get secret: {e}", "file") from e

    async def set_secret(
        self, secret_path: str, secret_data: dict[str, Any], **kwargs: Any
    ) -> bool:
        """
        Set secret in file.

        Args:
            secret_path: Path to the secret
            secret_data: Secret data to store
            **kwargs: Ignored for file provider

        Returns:
            True if successful
        """
        secrets = self._load_secrets()

        try:
            self._set_nested_value(secrets, secret_path, secret_data)
            self._save_secrets(secrets)
            return True
        except Exception as e:
            raise SecretsProviderError(f"Failed to set secret: {e}", "file") from e

    async def delete_secret(self, secret_path: str, **kwargs: Any) -> bool:
        """
        Delete secret from file.

        Args:
            secret_path: Path to the secret
            **kwargs: Ignored for file provider

        Returns:
            True if successful
        """
        secrets = self._load_secrets()

        try:
            parts = [p for p in secret_path.split("/") if p]
            current = secrets

            # Navigate to the parent of the target key
            for part in parts[:-1]:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    raise SecretNotFoundError(secret_path, "file")

            # Delete the final key
            if parts and isinstance(current, dict) and parts[-1] in current:
                del current[parts[-1]]
                self._save_secrets(secrets)
                return True
            raise SecretNotFoundError(secret_path, "file")

        except SecretNotFoundError:
            raise
        except Exception as e:
            raise SecretsProviderError(f"Failed to delete secret: {e}", "file") from e

    async def list_secrets(self, secret_path: str = "") -> list[str]:
        """
        List secrets in file.

        Args:
            secret_path: Path prefix to filter

        Returns:
            List of secret names/paths
        """
        secrets = self._load_secrets()

        def _collect_paths(obj: Any, prefix: str = "") -> list[str]:
            paths = []
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{prefix}/{key}" if prefix else key
                    if isinstance(value, dict):
                        # Add dict path and recurse
                        paths.append(current_path)
                        paths.extend(_collect_paths(value, current_path))
                    else:
                        # Leaf value
                        paths.append(current_path)
            return paths

        all_paths = _collect_paths(secrets)

        # Filter by prefix if provided
        if secret_path:
            prefix = secret_path.strip("/")
            # Include only paths under the prefix, excluding the prefix itself
            filtered_paths = [
                path for path in all_paths if path.startswith(prefix) and path != prefix
            ]
            return sorted(filtered_paths)

        return sorted(all_paths)

    async def health_check(self) -> dict[str, Any]:
        """
        Check file provider health.

        Returns:
            Health status dictionary
        """
        try:
            self._load_secrets()
            return {
                "status": "healthy",
                "provider": "file",
                "details": {
                    "file_path": self.file_path,
                    "file_exists": os.path.exists(self.file_path),
                    "secret_count": len(await self.list_secrets()),
                },
            }
        except Exception as e:
            return {"status": "unhealthy", "provider": "file", "error": str(e)}
