"""
SecretsManager - Main interface for secrets management
Provides unified access to secrets with caching, validation, and observability
"""

from __future__ import annotations

import logging
import time
from typing import Any

from .cache import InMemoryCache
from .exceptions import (
    SecretNotFoundError,
    SecretValidationError,
)
from .interfaces import (
    ObservabilityHook,
    SecretCache,
    SecretsProvider,
    SecretValidator,
)
from .types import (
    DatabaseCredentials,
    JWTKeypair,
    SecretData,
    SecretKind,
    SecretMetadata,
    SecretPaths,
    SecretValue,
)
from .validators import create_default_validator

logger = logging.getLogger(__name__)


class SecretsManager:
    """
    Main secrets manager providing unified interface to secrets

    Features:
    - Multiple provider support with fallback
    - Caching with TTL and negative caching
    - Secret validation and policy enforcement
    - Observability hooks for metrics and monitoring
    - Type-specific convenience methods
    """

    def __init__(
        self,
        provider: SecretsProvider,
        cache: SecretCache | None = None,
        validator: SecretValidator | None = None,
        observability_hook: ObservabilityHook | None = None,
        default_ttl: int = 300,
        negative_cache_ttl: int = 30,
        enable_negative_caching: bool = True,
        validate_secrets: bool = True,
    ) -> None:
        """
        Initialize SecretsManager

        Args:
            provider: Primary secrets provider
            cache: Optional cache implementation
            validator: Optional secret validator
            observability_hook: Optional observability hook
            default_ttl: Default TTL for cached secrets (seconds)
            negative_cache_ttl: TTL for negative cache entries (seconds)
            enable_negative_caching: Whether to cache failed lookups
            validate_secrets: Whether to validate retrieved secrets
        """
        self.provider = provider
        self.cache = cache or InMemoryCache(default_ttl=default_ttl)
        self.validator = validator or (create_default_validator() if validate_secrets else None)
        self.observability_hook = observability_hook
        self.default_ttl = default_ttl
        self.negative_cache_ttl = negative_cache_ttl
        self.enable_negative_caching = enable_negative_caching
        self.validate_secrets = validate_secrets

        # Statistics
        self._stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "provider_calls": 0,
            "validation_failures": 0,
            "errors": 0,
        }

    async def _get_secret_with_cache(
        self, path: str, kind: SecretKind, ttl: int | None = None
    ) -> SecretData:
        """
        Get secret with caching logic

        Args:
            path: Secret path
            kind: Secret kind for validation
            ttl: Optional TTL override

        Returns:
            Secret data

        Raises:
            SecretNotFoundError: If secret not found
            SecretValidationError: If secret validation fails
            SecretsProviderError: If provider error occurs
        """
        cache_key = f"{kind.value}:{path}"
        start_time = time.time()

        try:
            # Check cache first
            if self.cache:
                cached_value = await self.cache.get(cache_key)
                if cached_value is not None:
                    self._stats["cache_hits"] += 1
                    if self.observability_hook:
                        self.observability_hook.record_cache_hit(path)

                    # Check if it's a negative cache entry
                    if isinstance(cached_value.value, dict) and cached_value.value.get(
                        "__negative_cache"
                    ):
                        raise SecretNotFoundError(f"Secret not found (cached): {path}")

                    return cached_value.value
                self._stats["cache_misses"] += 1
                if self.observability_hook:
                    self.observability_hook.record_cache_miss(path)

            # Fetch from provider
            self._stats["provider_calls"] += 1
            secret_data = await self.provider.get_secret(path)

            # Validate secret if validator is configured
            if self.validator and self.validate_secrets:
                try:
                    if not self.validator.validate(secret_data, kind):
                        errors = self.validator.get_validation_errors(secret_data, kind)
                        error_msg = f"Secret validation failed for {path}: {'; '.join(errors)}"

                        self._stats["validation_failures"] += 1
                        if self.observability_hook:
                            self.observability_hook.record_validation_failure(kind, error_msg, path)

                        raise SecretValidationError(error_msg)

                except SecretValidationError:
                    raise
                except Exception as e:
                    logger.warning(f"Secret validation error for {path}: {e}")
                    if self.observability_hook:
                        self.observability_hook.record_validation_failure(kind, str(e), path)

            # Cache the secret
            if self.cache:
                metadata = SecretMetadata(path=path, kind=kind)
                secret_value = SecretValue(value=secret_data, metadata=metadata)
                cache_ttl = ttl or self.default_ttl
                await self.cache.set(cache_key, secret_value, cache_ttl)

            # Record success metrics
            latency_ms = (time.time() - start_time) * 1000
            if self.observability_hook:
                self.observability_hook.record_secret_fetch(
                    kind, "provider", True, latency_ms, path
                )

            return secret_data

        except SecretNotFoundError:
            # Cache negative result if enabled
            if self.enable_negative_caching and self.cache:
                negative_entry = {"__negative_cache": True, "timestamp": time.time()}
                metadata = SecretMetadata(path=path, kind=kind)
                secret_value = SecretValue(value=negative_entry, metadata=metadata)
                await self.cache.set(cache_key, secret_value, self.negative_cache_ttl)

            # Record failure metrics
            latency_ms = (time.time() - start_time) * 1000
            if self.observability_hook:
                self.observability_hook.record_secret_fetch(
                    kind, "provider", False, latency_ms, path
                )

            raise

        except Exception as e:
            self._stats["errors"] += 1

            # Record error metrics
            latency_ms = (time.time() - start_time) * 1000
            if self.observability_hook:
                self.observability_hook.record_secret_fetch(
                    kind, "provider", False, latency_ms, path
                )
                self.observability_hook.record_provider_error(
                    type(self.provider).__name__, type(e).__name__, path
                )

            raise

    async def get_jwt_keypair(self, app: str = "default", kid: str | None = None) -> JWTKeypair:
        """
        Get JWT keypair for application

        Args:
            app: Application name (e.g., "management", "isp")
            kid: Optional key ID for key rotation

        Returns:
            JWT keypair with metadata

        Raises:
            SecretNotFoundError: If keypair not found
            SecretValidationError: If keypair validation fails
        """
        path = SecretPaths.jwt_keypair(app, kid)
        secret_data = await self._get_secret_with_cache(path, SecretKind.JWT_KEYPAIR)

        # Convert to JWTKeypair object
        algorithm = secret_data.get("algorithm", "RS256")
        key_id = secret_data.get("kid", kid or "default")

        if algorithm.startswith(("HS", "A")):
            # Symmetric algorithm
            return JWTKeypair(
                private_pem=secret_data["secret"],
                public_pem="",  # Not applicable for symmetric
                algorithm=algorithm,
                kid=key_id,
                created_at=secret_data.get("created_at"),
                expires_at=secret_data.get("expires_at"),
            )
        # Asymmetric algorithm
        return JWTKeypair(
            private_pem=secret_data["private_pem"],
            public_pem=secret_data["public_pem"],
            algorithm=algorithm,
            kid=key_id,
            created_at=secret_data.get("created_at"),
            expires_at=secret_data.get("expires_at"),
        )

    async def get_symmetric_secret(self, name: str, min_length: int = 32) -> str:
        """
        Get symmetric secret

        Args:
            name: Secret name
            min_length: Minimum required length

        Returns:
            Secret string

        Raises:
            SecretNotFoundError: If secret not found
            SecretValidationError: If secret too short
        """
        path = SecretPaths.symmetric_secret(name)
        secret_data = await self._get_secret_with_cache(path, SecretKind.SYMMETRIC_SECRET)

        secret = secret_data.get("secret", "")
        if len(secret) < min_length:
            raise SecretValidationError(
                f"Symmetric secret '{name}' too short: {len(secret)} < {min_length}"
            )

        return secret

    async def get_service_signing_secret(self, service: str) -> str:
        """
        Get service signing secret

        Args:
            service: Service name

        Returns:
            Signing secret string
        """
        path = SecretPaths.service_signing_secret(service)
        secret_data = await self._get_secret_with_cache(path, SecretKind.SERVICE_SIGNING_SECRET)

        return secret_data["secret"]

    async def get_database_credentials(self, db_name: str) -> DatabaseCredentials:
        """
        Get database credentials

        Args:
            db_name: Database name

        Returns:
            Database credentials object
        """
        path = SecretPaths.database_credentials(db_name)
        secret_data = await self._get_secret_with_cache(path, SecretKind.DATABASE_CREDENTIALS)

        return DatabaseCredentials(
            host=secret_data["host"],
            port=secret_data.get("port", 5432),
            username=secret_data["username"],
            password=secret_data["password"],
            database=secret_data["database"],
            driver=secret_data.get("driver", "postgresql"),
            ssl_mode=secret_data.get("ssl_mode", "require"),
            pool_size=secret_data.get("pool_size", 10),
            max_overflow=secret_data.get("max_overflow", 20),
        )

    async def get_encryption_key(self, key_name: str, min_length: int = 32) -> str | bytes:
        """
        Get encryption key

        Args:
            key_name: Encryption key name
            min_length: Minimum required length in bytes

        Returns:
            Encryption key as string or bytes
        """
        path = SecretPaths.encryption_key(key_name)
        secret_data = await self._get_secret_with_cache(path, SecretKind.ENCRYPTION_KEY)

        key = secret_data["key"]

        # Validate length for binary data
        if isinstance(key, bytes):
            if len(key) < min_length:
                raise SecretValidationError(
                    f"Encryption key '{key_name}' too short: {len(key)} < {min_length} bytes"
                )
        elif isinstance(key, str):
            # Try to detect encoding and validate length
            key_bytes = len(key.encode("utf-8"))

            # Check if it's base64 or hex encoded
            if self._is_base64(key):
                import base64

                key_bytes = len(base64.b64decode(key))
            elif self._is_hex(key):
                key_bytes = len(key) // 2

            if key_bytes < min_length:
                raise SecretValidationError(
                    f"Encryption key '{key_name}' too short: {key_bytes} < {min_length} bytes"
                )

        return key

    async def get_webhook_signing_secret(self, webhook_id: str) -> str:
        """
        Get webhook signing secret

        Args:
            webhook_id: Webhook identifier

        Returns:
            Webhook signing secret
        """
        path = SecretPaths.webhook_secret(webhook_id)
        secret_data = await self._get_secret_with_cache(path, SecretKind.WEBHOOK_SECRET)

        return secret_data["secret"]

    async def get_custom_secret(self, path: str) -> dict[str, Any]:
        """
        Get custom secret data

        Args:
            path: Custom secret path

        Returns:
            Secret data dictionary
        """
        return await self._get_secret_with_cache(path, SecretKind.CUSTOM_SECRET)

    async def invalidate_cache(self, path: str | None = None) -> bool:
        """
        Invalidate cached secrets

        Args:
            path: Optional specific path to invalidate, or None to clear all

        Returns:
            True if successful
        """
        if not self.cache:
            return True

        if path:
            # Invalidate all cache keys for this path
            for kind in SecretKind:
                cache_key = f"{kind.value}:{path}"
                await self.cache.delete(cache_key)
        else:
            await self.cache.clear()

        return True

    async def health_check(self) -> dict[str, Any]:
        """
        Perform health check on all components

        Returns:
            Health status dictionary
        """
        health_status = {
            "manager": "healthy",
            "provider": "unknown",
            "cache": "unknown",
            "timestamp": time.time(),
        }

        # Check provider health
        try:
            provider_healthy = await self.provider.health_check()
            health_status["provider"] = "healthy" if provider_healthy else "unhealthy"
        except Exception as e:
            health_status["provider"] = f"error: {e}"

        # Check cache health
        try:
            if self.cache:
                await self.cache.exists("health_check")
                health_status["cache"] = "healthy"
            else:
                health_status["cache"] = "disabled"
        except Exception as e:
            health_status["cache"] = f"error: {e}"

        return health_status

    async def get_stats(self) -> dict[str, Any]:
        """
        Get manager statistics

        Returns:
            Statistics dictionary
        """
        stats = self._stats.copy()

        # Add cache stats if available
        if self.cache:
            try:
                cache_stats = await self.cache.get_stats()
                stats["cache"] = cache_stats
            except Exception:
                stats["cache"] = {"error": "unable to get cache stats"}

        return stats

    def _is_base64(self, s: str) -> bool:
        """Check if string looks like base64"""
        try:
            import base64

            if len(s) % 4 != 0:
                return False
            base64.b64decode(s, validate=True)
            return True
        except Exception:
            return False

    def _is_hex(self, s: str) -> bool:
        """Check if string looks like hex"""
        try:
            int(s, 16)
            return len(s) % 2 == 0
        except ValueError:
            return False

    async def close(self) -> None:
        """Close manager and cleanup resources"""
        if self.cache:
            await self.cache.close()

        if hasattr(self.provider, "close"):
            await self.provider.close()

    async def __aenter__(self) -> SecretsManager:
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit"""
        await self.close()

    def __repr__(self) -> str:
        """String representation of manager"""
        provider_name = type(self.provider).__name__
        cache_name = type(self.cache).__name__ if self.cache else "None"
        return f"SecretsManager(provider={provider_name}, cache={cache_name})"
