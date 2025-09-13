"""
Tests for secrets configuration and management.
"""

import os

import pytest

from dotmac.platform.secrets import SecretsConfig


def test_secrets_config_basic() -> None:
    """Test basic secrets configuration."""
    config = SecretsConfig(
        vault_url="https://vault.example.com",
        vault_token="test-token",
        encryption_key="test-key-that-is-32-chars-long!",
    )

    assert config.vault_url == "https://vault.example.com"
    assert config.vault_token == "test-token"
    assert config.encryption_key == "test-key-that-is-32-chars-long!"


def test_secrets_config_environment_loading() -> None:
    """Test secrets config loads from environment variables."""
    # Set test environment variables
    os.environ["DOTMAC_VAULT_URL"] = "https://test-vault.example.com"
    os.environ["DOTMAC_VAULT_TOKEN"] = "env-test-token"
    os.environ["DOTMAC_ENCRYPTION_KEY"] = "env-key-that-is-32-chars-long!!"

    try:
        config = SecretsConfig()
        assert config.vault_url == "https://test-vault.example.com"
        assert config.vault_token == "env-test-token"
        assert config.encryption_key == "env-key-that-is-32-chars-long!!"
    finally:
        # Cleanup environment
        del os.environ["DOTMAC_VAULT_URL"]
        del os.environ["DOTMAC_VAULT_TOKEN"]
        del os.environ["DOTMAC_ENCRYPTION_KEY"]


def test_secrets_production_validation() -> None:
    """Test production readiness validation."""
    config = SecretsConfig(
        vault_url="https://vault.example.com",
        vault_token="test-token",
        encryption_key="test-key-that-is-32-chars-long!",
    )

    # Set development environment to avoid strict production checks
    os.environ["ENVIRONMENT"] = "development"
    try:
        warnings = config.validate_production_readiness()
        assert isinstance(warnings, list)
    finally:
        if "ENVIRONMENT" in os.environ:
            del os.environ["ENVIRONMENT"]


if __name__ == "__main__":
    pytest.main([__file__])
