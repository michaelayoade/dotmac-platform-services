"""
Tests for Secrets Providers - matching actual implementation.
"""

import os
import warnings
from unittest.mock import patch

import pytest

from dotmac.platform.secrets.exceptions import (
    SecretNotFoundError,
)
from dotmac.platform.secrets.interfaces import (
    SecretsProvider,
    WritableSecretsProvider,
)
from dotmac.platform.secrets.providers.env import EnvironmentProvider
from dotmac.platform.secrets.types import Environment


class TestSecretsProviderInterface:
    """Test the abstract secrets provider interface."""

    def test_secrets_provider_is_abstract(self):
        """Test that SecretsProvider is abstract and cannot be instantiated."""
        with pytest.raises(TypeError):
            SecretsProvider()

    def test_writable_secrets_provider_is_abstract(self):
        """Test that WritableSecretsProvider is abstract."""
        with pytest.raises(TypeError):
            WritableSecretsProvider()


class TestEnvironmentProvider:
    """Test environment variable secrets provider."""

    def test_provider_initialization(self):
        """Test environment provider initialization."""
        provider = EnvironmentProvider(prefix="TEST", environment=Environment.DEVELOPMENT)

        assert provider.prefix == "TEST"
        assert provider.environment == Environment.DEVELOPMENT
        assert provider.allow_production is False

    def test_production_safety_check_blocks(self):
        """Test production safety check blocks by default."""
        with pytest.raises(ValueError) as exc_info:
            EnvironmentProvider(environment=Environment.PRODUCTION)

        assert "disabled in production" in str(exc_info.value)

    def test_production_with_override(self):
        """Test production usage with environment override."""
        with patch.dict(os.environ, {"EXPLICIT_ALLOW_ENV_SECRETS": "true"}):
            with warnings.catch_warnings(record=True) as w:
                EnvironmentProvider(environment=Environment.PRODUCTION)

                # Should issue warning
                assert len(w) > 0
                assert "not recommended" in str(w[0].message)

    def test_production_with_allow_flag(self):
        """Test production usage with allow_production flag."""
        with warnings.catch_warnings(record=True) as w:
            EnvironmentProvider(environment=Environment.PRODUCTION, allow_production=True)

            # Should issue warning
            assert len(w) > 0
            assert "not recommended" in str(w[0].message)

    def test_get_env_var_with_prefix(self):
        """Test getting environment variable with prefix."""
        provider = EnvironmentProvider(prefix="MYAPP")

        with patch.dict(os.environ, {"MYAPP_SECRET_KEY": "test_value"}):
            value = provider._get_env_var("SECRET_KEY")
            assert value == "test_value"

    def test_get_env_var_without_prefix(self):
        """Test getting environment variable without prefix."""
        provider = EnvironmentProvider()

        with patch.dict(os.environ, {"SECRET_KEY": "test_value"}):
            value = provider._get_env_var("SECRET_KEY")
            assert value == "test_value"

    @pytest.mark.asyncio
    async def test_get_jwt_secret(self):
        """Test getting JWT secret from environment."""
        provider = EnvironmentProvider()

        env_vars = {
            "JWT_PRIVATE_KEY_MYAPP": "-----BEGIN PRIVATE KEY-----",
            "JWT_PUBLIC_KEY_MYAPP": "-----BEGIN PUBLIC KEY-----",
            "JWT_ALGORITHM_MYAPP": "RS256",
        }

        with patch.dict(os.environ, env_vars):
            secret = await provider.get_secret("jwt/myapp/keypair")

            assert secret["private_pem"] == "-----BEGIN PRIVATE KEY-----"
            assert secret["public_pem"] == "-----BEGIN PUBLIC KEY-----"
            assert secret["algorithm"] == "RS256"

    @pytest.mark.asyncio
    async def test_get_jwt_secret_symmetric(self):
        """Test getting symmetric JWT secret."""
        provider = EnvironmentProvider()

        env_vars = {"JWT_PRIVATE_KEY": "symmetric_secret_key", "JWT_ALGORITHM": "HS256"}

        with patch.dict(os.environ, env_vars):
            secret = await provider.get_secret("jwt/app/keypair")

            assert secret["secret"] == "symmetric_secret_key"
            assert secret["algorithm"] == "HS256"

    @pytest.mark.asyncio
    async def test_get_database_secret_from_url(self):
        """Test getting database secret from DATABASE_URL."""
        provider = EnvironmentProvider()

        db_url = "postgresql://user:pass@localhost:5432/mydb?sslmode=require"

        with patch.dict(os.environ, {"DATABASE_URL": db_url}):
            secret = await provider.get_secret("databases/mydb")

            assert secret["host"] == "localhost"
            assert secret["port"] == 5432
            assert secret["username"] == "user"
            assert secret["password"] == "pass"
            assert secret["database"] == "mydb"
            assert secret["driver"] == "postgresql"
            assert secret["ssl_mode"] == "require"

    @pytest.mark.asyncio
    async def test_get_database_secret_from_components(self):
        """Test getting database secret from individual components."""
        provider = EnvironmentProvider()

        env_vars = {
            "DATABASE_HOST": "db.example.com",
            "DATABASE_PORT": "3306",
            "DATABASE_USER": "dbuser",
            "DATABASE_PASSWORD": "dbpass",
            "DATABASE_NAME": "testdb",
            "DATABASE_DRIVER": "mysql",
        }

        with patch.dict(os.environ, env_vars):
            secret = await provider.get_secret("databases/testdb")

            assert secret["host"] == "db.example.com"
            assert secret["port"] == 3306
            assert secret["username"] == "dbuser"
            assert secret["password"] == "dbpass"

    @pytest.mark.asyncio
    async def test_get_service_signing_secret(self):
        """Test getting service signing secret."""
        provider = EnvironmentProvider()

        with patch.dict(os.environ, {"SERVICE_SIGNING_SECRET_API": "signing_key"}):
            secret = await provider.get_secret("service-signing/api")
            assert secret["secret"] == "signing_key"

    @pytest.mark.asyncio
    async def test_get_encryption_key(self):
        """Test getting encryption key."""
        provider = EnvironmentProvider()

        with patch.dict(os.environ, {"ENCRYPTION_KEY_MASTER": "encryption_key"}):
            secret = await provider.get_secret("encryption-keys/master")
            assert secret["key"] == "encryption_key"

    @pytest.mark.asyncio
    async def test_get_webhook_secret(self):
        """Test getting webhook secret."""
        provider = EnvironmentProvider()

        with patch.dict(os.environ, {"WEBHOOK_SECRET_GITHUB": "webhook_secret"}):
            secret = await provider.get_secret("webhooks/github")
            assert secret["secret"] == "webhook_secret"

    @pytest.mark.asyncio
    async def test_get_symmetric_secret(self):
        """Test getting symmetric secret."""
        provider = EnvironmentProvider()

        with patch.dict(os.environ, {"SYMMETRIC_SECRET_SESSION": "session_key"}):
            secret = await provider.get_secret("secrets/symmetric/session")
            assert secret["secret"] == "session_key"

    @pytest.mark.asyncio
    async def test_get_custom_secret(self):
        """Test getting custom secret."""
        provider = EnvironmentProvider()

        with patch.dict(os.environ, {"CUSTOM_API_KEY": "api_key_value"}):
            secret = await provider.get_secret("custom/api/key")
            assert secret["value"] == "api_key_value"

    @pytest.mark.asyncio
    async def test_secret_not_found(self):
        """Test secret not found error."""
        provider = EnvironmentProvider()

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(SecretNotFoundError):
                await provider.get_secret("jwt/app/keypair")

    @pytest.mark.asyncio
    async def test_list_secrets(self):
        """Test listing available secrets."""
        provider = EnvironmentProvider()

        env_vars = {
            "JWT_PRIVATE_KEY": "key",
            "DATABASE_URL": "postgres://...",
            "SERVICE_SIGNING_SECRET": "secret",
            "JWT_PRIVATE_KEY_MYAPP": "app_key",
        }

        with patch.dict(os.environ, env_vars):
            secrets = await provider.list_secrets()

            assert "jwt/default/keypair" in secrets
            assert "databases/default" in secrets
            assert "service-signing/default" in secrets
            assert "jwt/myapp/keypair" in secrets

    @pytest.mark.asyncio
    async def test_list_secrets_with_prefix_filter(self):
        """Test listing secrets with path prefix."""
        provider = EnvironmentProvider()

        env_vars = {
            "JWT_PRIVATE_KEY": "key",
            "DATABASE_URL": "postgres://...",
            "JWT_PRIVATE_KEY_MYAPP": "app_key",
        }

        with patch.dict(os.environ, env_vars):
            secrets = await provider.list_secrets("jwt/")

            assert "jwt/default/keypair" in secrets
            assert "jwt/myapp/keypair" in secrets
            assert "databases/default" not in secrets

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test successful health check."""
        provider = EnvironmentProvider()

        with patch.dict(os.environ, {"PATH": "/usr/bin"}):
            result = await provider.health_check()
            assert result is True
            assert provider._healthy is True

    @pytest.mark.asyncio
    async def test_health_check_minimal_environment(self):
        """Test health check in minimal environment."""
        provider = EnvironmentProvider()

        # Even with no standard env vars, should be considered healthy
        with patch.dict(os.environ, {}, clear=True):
            result = await provider.health_check()
            assert result is True

    @pytest.mark.asyncio
    async def test_health_check_exception(self):
        """Test health check with exception."""
        provider = EnvironmentProvider()

        with patch("os.getenv", side_effect=Exception("OS error")):
            result = await provider.health_check()
            assert result is False
            assert provider._healthy is False

    def test_parse_database_url(self):
        """Test parsing database URL into components."""
        provider = EnvironmentProvider()

        url = "postgresql+psycopg2://user:pass@host:5432/db"
        result = provider._parse_database_url(url)

        assert result["host"] == "host"
        assert result["port"] == 5432
        assert result["username"] == "user"
        assert result["password"] == "pass"
        assert result["database"] == "db"
        assert result["driver"] == "postgresql"

    def test_parse_database_url_invalid(self):
        """Test parsing invalid database URL."""
        provider = EnvironmentProvider()

        with pytest.raises(SecretNotFoundError):
            provider._parse_database_url("invalid://url")
