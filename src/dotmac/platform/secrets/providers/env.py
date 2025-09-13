"""
Environment variable provider for secrets
Includes production safeguards and validation
"""

from __future__ import annotations

import logging
import os
import warnings
from urllib.parse import parse_qs, urlparse

from ..exceptions import SecretNotFoundError
from ..types import Environment, SecretData
from .base import BaseProvider

logger = logging.getLogger(__name__)


class EnvironmentProvider(BaseProvider):
    """
    Provider that reads secrets from environment variables
    Includes safety checks for production environments
    """

    def __init__(
        self,
        prefix: str = "",
        allow_production: bool = False,
        environment: Environment = Environment.DEVELOPMENT,
        **kwargs: any,
    ) -> None:
        super().__init__(**kwargs)
        self.prefix = prefix
        self.environment = environment
        self.allow_production = allow_production

        # Production safety check
        self._check_production_safety()

        # Issue warnings for production usage
        if environment == Environment.PRODUCTION:
            warnings.warn(
                "Using EnvironmentProvider in production is not recommended. "
                "Consider using OpenBaoProvider for production deployments.",
                UserWarning,
                stacklevel=2,
            )
            logger.warning(
                "EnvironmentProvider is being used in production environment. "
                "This is not recommended for security reasons."
            )

    def _check_production_safety(self) -> None:
        """Check if environment provider usage is safe in production"""
        if self.environment == Environment.PRODUCTION and not self.allow_production:
            # Check for explicit override
            env_override = os.getenv("EXPLICIT_ALLOW_ENV_SECRETS", "").lower()
            if env_override not in {"true", "1", "yes"}:
                raise ValueError(
                    "EnvironmentProvider is disabled in production for security. "
                    "Set EXPLICIT_ALLOW_ENV_SECRETS=true to override, or use "
                    "allow_production=True in configuration."
                )

    def _get_env_var(self, key: str) -> str | None:
        """Get environment variable with optional prefix"""
        if self.prefix:
            prefixed_key = f"{self.prefix}_{key}"
            value = os.getenv(prefixed_key)
            if value is not None:
                return value

        return os.getenv(key)

    async def get_secret(self, path: str) -> SecretData:
        """
        Retrieve secret from environment variables

        Args:
            path: Secret path (used to determine env var names)

        Returns:
            Secret data dictionary

        Raises:
            SecretNotFoundError: If required environment variables not found
        """
        normalized_path = self._normalize_path(path)

        # Handle different secret types based on path patterns
        if normalized_path.startswith("jwt/"):
            return await self._get_jwt_secret(normalized_path)
        if normalized_path.startswith("databases/"):
            return await self._get_database_secret(normalized_path)
        if normalized_path.startswith("service-signing/"):
            return await self._get_service_signing_secret(normalized_path)
        if normalized_path.startswith("encryption-keys/"):
            return await self._get_encryption_key_secret(normalized_path)
        if normalized_path.startswith("webhooks/"):
            return await self._get_webhook_secret(normalized_path)
        if normalized_path.startswith("secrets/symmetric/"):
            return await self._get_symmetric_secret(normalized_path)
        return await self._get_custom_secret(normalized_path)

    def _normalize_path(self, path: str) -> str:
        """Normalize secret path by stripping leading/trailing slashes and collapsing duplicates."""
        parts = [p for p in str(path).split("/") if p]
        return "/".join(parts)

    async def _get_jwt_secret(self, path: str) -> SecretData:
        """Get JWT keypair from environment"""
        # Extract app name from path: jwt/{app}/keypair[/{kid}]
        path_parts = path.split("/")
        if len(path_parts) < 3:
            raise SecretNotFoundError(f"Invalid JWT path format: {path}")

        app = path_parts[1]
        kid = path_parts[3] if len(path_parts) > 3 else "default"

        # Try app-specific variables first
        private_key = (
            self._get_env_var(f"JWT_PRIVATE_KEY_{app.upper()}")
            or self._get_env_var(f"JWT_PRIVATE_KEY_{app.upper()}_{kid.upper()}")
            or self._get_env_var("JWT_PRIVATE_KEY")
        )

        public_key = (
            self._get_env_var(f"JWT_PUBLIC_KEY_{app.upper()}")
            or self._get_env_var(f"JWT_PUBLIC_KEY_{app.upper()}_{kid.upper()}")
            or self._get_env_var("JWT_PUBLIC_KEY")
        )

        algorithm = (
            self._get_env_var(f"JWT_ALGORITHM_{app.upper()}")
            or self._get_env_var("JWT_ALGORITHM")
            or "RS256"
        )

        if not private_key:
            raise SecretNotFoundError(f"JWT private key not found for path: {path}")

        # For symmetric algorithms, use private_key as the secret
        if algorithm.startswith(("HS", "A")):
            return {
                "secret": private_key,
                "algorithm": algorithm,
                "kid": kid,
            }

        if not public_key:
            raise SecretNotFoundError(f"JWT public key not found for path: {path}")

        return {
            "private_pem": private_key,
            "public_pem": public_key,
            "algorithm": algorithm,
            "kid": kid,
        }

    async def _get_database_secret(self, path: str) -> SecretData:
        """Get database credentials from environment"""
        # Extract db name from path: databases/{name}
        path_parts = path.split("/")
        if len(path_parts) < 2:
            raise SecretNotFoundError(f"Invalid database path format: {path}")

        db_name = path_parts[1]

        # Try full DATABASE_URL first
        database_url = self._get_env_var(f"DATABASE_URL_{db_name.upper()}") or self._get_env_var(
            "DATABASE_URL"
        )

        if database_url:
            return self._parse_database_url(database_url)

        # Try individual components
        host = self._get_env_var(f"DATABASE_HOST_{db_name.upper()}") or self._get_env_var(
            "DATABASE_HOST"
        )
        port_str = self._get_env_var(f"DATABASE_PORT_{db_name.upper()}") or self._get_env_var(
            "DATABASE_PORT"
        )
        username = self._get_env_var(f"DATABASE_USER_{db_name.upper()}") or self._get_env_var(
            "DATABASE_USER"
        )
        password = self._get_env_var(f"DATABASE_PASSWORD_{db_name.upper()}") or self._get_env_var(
            "DATABASE_PASSWORD"
        )
        database = (
            self._get_env_var(f"DATABASE_NAME_{db_name.upper()}")
            or self._get_env_var("DATABASE_NAME")
            or db_name
        )
        driver = (
            self._get_env_var(f"DATABASE_DRIVER_{db_name.upper()}")
            or self._get_env_var("DATABASE_DRIVER")
            or "postgresql"
        )

        if not all([host, username, password]):
            raise SecretNotFoundError(f"Database credentials incomplete for: {path}")

        try:
            port = int(port_str) if port_str else (5432 if driver == "postgresql" else 3306)
        except ValueError:
            port = 5432 if driver == "postgresql" else 3306

        return {
            "host": host,
            "port": port,
            "username": username,
            "password": password,
            "database": database,
            "driver": driver,
        }

    def _parse_database_url(self, url: str) -> SecretData:
        """Parse database URL into components"""
        parsed = urlparse(url)

        if not parsed.hostname or not parsed.username:
            raise SecretNotFoundError("Invalid database URL format")

        # Extract driver from scheme
        driver = parsed.scheme
        if "+" in driver:
            driver = driver.split("+")[0]

        # Parse query parameters for additional options
        query_params = parse_qs(parsed.query)
        ssl_mode = query_params.get("sslmode", ["require"])[0]

        return {
            "host": parsed.hostname,
            "port": parsed.port or (5432 if driver == "postgresql" else 3306),
            "username": parsed.username,
            "password": parsed.password or "",
            "database": parsed.path.lstrip("/") if parsed.path else "",
            "driver": driver,
            "ssl_mode": ssl_mode,
        }

    async def _get_service_signing_secret(self, path: str) -> SecretData:
        """Get service signing secret from environment"""
        # Extract service name from path: service-signing/{service}
        path_parts = path.split("/")
        if len(path_parts) < 2:
            raise SecretNotFoundError(f"Invalid service signing path format: {path}")

        service = path_parts[1]

        secret = self._get_env_var(
            f"SERVICE_SIGNING_SECRET_{service.upper()}"
        ) or self._get_env_var("SERVICE_SIGNING_SECRET")

        if not secret:
            raise SecretNotFoundError(f"Service signing secret not found for: {path}")

        return {"secret": secret}

    async def _get_encryption_key_secret(self, path: str) -> SecretData:
        """Get encryption key from environment"""
        # Extract key name from path: encryption-keys/{name}
        path_parts = path.split("/")
        if len(path_parts) < 2:
            raise SecretNotFoundError(f"Invalid encryption key path format: {path}")

        key_name = path_parts[1]

        key = self._get_env_var(f"ENCRYPTION_KEY_{key_name.upper()}") or self._get_env_var(
            "ENCRYPTION_KEY"
        )

        if not key:
            raise SecretNotFoundError(f"Encryption key not found for: {path}")

        return {"key": key}

    async def _get_webhook_secret(self, path: str) -> SecretData:
        """Get webhook secret from environment"""
        # Extract webhook ID from path: webhooks/{id}
        path_parts = path.split("/")
        if len(path_parts) < 2:
            raise SecretNotFoundError(f"Invalid webhook path format: {path}")

        webhook_id = path_parts[1]

        secret = self._get_env_var(f"WEBHOOK_SECRET_{webhook_id.upper()}") or self._get_env_var(
            "WEBHOOK_SECRET"
        )

        if not secret:
            raise SecretNotFoundError(f"Webhook secret not found for: {path}")

        return {"secret": secret}

    async def _get_symmetric_secret(self, path: str) -> SecretData:
        """Get symmetric secret from environment"""
        # Extract secret name from path: secrets/symmetric/{name}
        path_parts = path.split("/")
        if len(path_parts) < 3:
            raise SecretNotFoundError(f"Invalid symmetric secret path format: {path}")

        secret_name = path_parts[2]

        secret = self._get_env_var(f"SYMMETRIC_SECRET_{secret_name.upper()}") or self._get_env_var(
            f"SECRET_{secret_name.upper()}"
        )

        if not secret:
            raise SecretNotFoundError(f"Symmetric secret not found for: {path}")

        return {"secret": secret}

    async def _get_custom_secret(self, path: str) -> SecretData:
        """Get custom secret from environment"""
        # Convert path to environment variable name
        # Replace slashes and dashes with underscores, convert to uppercase
        env_key = path.replace("/", "_").replace("-", "_").upper()

        secret = self._get_env_var(env_key)
        if not secret:
            raise SecretNotFoundError(f"Custom secret not found for: {path}")

        return {"value": secret}

    async def list_secrets(self, path_prefix: str = "") -> list[str]:
        """List available secrets based on environment variables"""
        secrets = []

        # Define known secret patterns
        patterns = [
            ("JWT_PRIVATE_KEY", "jwt/default/keypair"),
            ("DATABASE_URL", "databases/default"),
            ("SERVICE_SIGNING_SECRET", "service-signing/default"),
            ("ENCRYPTION_KEY", "encryption-keys/default"),
            ("WEBHOOK_SECRET", "webhooks/default"),
        ]

        for env_var, secret_path in patterns:
            if self._get_env_var(env_var):
                if not path_prefix or secret_path.startswith(path_prefix):
                    secrets.append(secret_path)

        # Look for app-specific JWT keys
        for key, value in os.environ.items():
            if key.startswith("JWT_PRIVATE_KEY_") and value:
                app = key.replace("JWT_PRIVATE_KEY_", "").lower()
                secret_path = f"jwt/{app}/keypair"
                if not path_prefix or secret_path.startswith(path_prefix):
                    secrets.append(secret_path)

        return sorted(set(secrets))

    async def health_check(self) -> bool:
        """Check if provider has access to environment variables"""
        try:
            # Check if we can read any environment variable
            test_vars = ["PATH", "HOME", "USER", "USERNAME"]
            for var in test_vars:
                if os.getenv(var):
                    self._healthy = True
                    return True

            # If no standard env vars found, still consider healthy
            # as it might be a minimal container environment
            self._healthy = True
            return True

        except Exception as e:
            logger.error(f"Environment provider health check failed: {e}")
            self._healthy = False
            return False
