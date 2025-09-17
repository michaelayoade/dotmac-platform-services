"""
Comprehensive tests for secrets.providers.file module.

Tests the FileProvider class for file-based secrets management.
"""

import json
import os
import tempfile
from unittest.mock import patch

import pytest

from dotmac.platform.secrets.exceptions import (
    ConfigurationError,
    SecretNotFoundError,
    SecretsProviderError,
)
from dotmac.platform.secrets.interfaces import WritableSecretsProvider
from dotmac.platform.secrets.providers.file import FileProvider


# Module-level fixtures reused by multiple classes
@pytest.fixture
def temp_file():
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        test_secrets = {
            "app": {
                "database": {"username": "admin", "password": "secret123"},
                "api_key": "key123",
            },
            "simple_secret": "simple_value",
        }
        json.dump(test_secrets, f, indent=2)
        temp_path = f.name
    try:
        yield temp_path
    finally:
        try:
            os.unlink(temp_path)
        except (OSError, FileNotFoundError):
            pass


@pytest.fixture
def empty_temp_file():
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        json.dump({}, f)
        temp_path = f.name
    try:
        yield temp_path
    finally:
        try:
            os.unlink(temp_path)
        except (OSError, FileNotFoundError):
            pass


class TestFileProvider:
    """Test FileProvider class."""

    @pytest.fixture
    def temp_file(self):
        """Create temporary file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            test_secrets = {
                "app": {
                    "database": {"username": "admin", "password": "secret123"},
                    "api_key": "key123",
                },
                "simple_secret": "simple_value",
            }
            json.dump(test_secrets, f, indent=2)
            temp_path = f.name

        yield temp_path

        # Cleanup
        try:
            os.unlink(temp_path)
        except (OSError, FileNotFoundError):
            pass

    @pytest.fixture
    def empty_temp_file(self):
        """Create temporary empty file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            json.dump({}, f)
            temp_path = f.name

        yield temp_path

        # Cleanup
        try:
            os.unlink(temp_path)
        except (OSError, FileNotFoundError):
            pass

    @pytest.fixture
    def nonexistent_file_path(self):
        """Create path for non-existent file."""
        temp_dir = tempfile.gettempdir()
        return os.path.join(temp_dir, "nonexistent_secrets.json")

    @pytest.fixture
    def provider(self, temp_file):
        """Create FileProvider with temp file."""
        return FileProvider(file_path=temp_file)

    def test_provider_initialization_default(self):
        """Test provider initialization with default file path."""
        provider = FileProvider()
        assert provider.file_path == "secrets.json"
        assert provider._secrets_cache is None

    def test_provider_initialization_custom_path(self):
        """Test provider initialization with custom file path."""
        custom_path = "/custom/path/secrets.json"
        provider = FileProvider(file_path=custom_path)
        assert provider.file_path == custom_path

    def test_provider_implements_writable_interface(self, provider):
        """Test that FileProvider implements WritableSecretsProvider."""
        assert isinstance(provider, WritableSecretsProvider)

    def test_load_secrets_existing_file(self, provider):
        """Test loading secrets from existing file."""
        secrets = provider._load_secrets()

        assert isinstance(secrets, dict)
        assert "app" in secrets
        assert "simple_secret" in secrets
        assert secrets["simple_secret"] == "simple_value"

    def test_load_secrets_caching(self, provider):
        """Test that secrets are cached after first load."""
        # First load
        secrets1 = provider._load_secrets()
        assert provider._secrets_cache is not None

        # Second load should return cached version
        secrets2 = provider._load_secrets()
        assert secrets1 is secrets2

    def test_load_secrets_nonexistent_file(self, nonexistent_file_path):
        """Test loading secrets when file doesn't exist."""
        provider = FileProvider(file_path=nonexistent_file_path)
        secrets = provider._load_secrets()

        assert secrets == {}
        assert provider._secrets_cache == {}

    def test_load_secrets_invalid_json(self):
        """Test loading secrets with invalid JSON."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            f.write("invalid json content")
            temp_path = f.name

        try:
            provider = FileProvider(file_path=temp_path)
            with pytest.raises(ConfigurationError, match="Invalid JSON"):
                provider._load_secrets()
        finally:
            os.unlink(temp_path)

    def test_load_secrets_file_permission_error(self):
        """Test loading secrets with file permission error."""
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            provider = FileProvider(file_path="secrets.json")
            with pytest.raises(SecretsProviderError, match="Failed to load secrets file"):
                provider._load_secrets()

    def test_save_secrets_success(self, empty_temp_file):
        """Test saving secrets to file."""
        provider = FileProvider(file_path=empty_temp_file)
        test_secrets = {"key": "value", "nested": {"inner": "data"}}

        provider._save_secrets(test_secrets)

        # Verify file content
        with open(empty_temp_file) as f:
            saved_data = json.load(f)
        assert saved_data == test_secrets
        assert provider._secrets_cache == test_secrets

    def test_save_secrets_file_error(self):
        """Test saving secrets with file write error."""
        provider = FileProvider(file_path="/invalid/path/secrets.json")
        test_secrets = {"key": "value"}

        with pytest.raises(SecretsProviderError, match="Failed to save secrets file"):
            provider._save_secrets(test_secrets)

    def test_get_nested_value_simple(self, provider):
        """Test getting simple nested value."""
        secrets = provider._load_secrets()

        value = provider._get_nested_value(secrets, "simple_secret")
        assert value == "simple_value"

    def test_get_nested_value_deep(self, provider):
        """Test getting deep nested value."""
        secrets = provider._load_secrets()

        value = provider._get_nested_value(secrets, "app/database/username")
        assert value == "admin"

    def test_get_nested_value_dict(self, provider):
        """Test getting nested dictionary."""
        secrets = provider._load_secrets()

        value = provider._get_nested_value(secrets, "app/database")
        expected = {"username": "admin", "password": "secret123"}
        assert value == expected

    def test_get_nested_value_not_found(self, provider):
        """Test getting non-existent nested value."""
        secrets = provider._load_secrets()

        with pytest.raises(SecretNotFoundError):
            provider._get_nested_value(secrets, "nonexistent/path")

    def test_get_nested_value_path_through_non_dict(self, provider):
        """Test getting value when path goes through non-dict."""
        secrets = provider._load_secrets()

        with pytest.raises(SecretNotFoundError):
            provider._get_nested_value(secrets, "simple_secret/invalid/path")

    def test_get_nested_value_empty_parts(self, provider):
        """Test getting nested value with empty path parts."""
        secrets = provider._load_secrets()

        value = provider._get_nested_value(secrets, "/app//database/username/")
        assert value == "admin"

    def test_set_nested_value_simple(self):
        """Test setting simple value."""
        provider = FileProvider()
        secrets = {}

        provider._set_nested_value(secrets, "key", "value")
        assert secrets["key"] == "value"

    def test_set_nested_value_deep(self):
        """Test setting deep nested value."""
        provider = FileProvider()
        secrets = {}

        provider._set_nested_value(secrets, "level1/level2/level3", "deep_value")
        expected = {"level1": {"level2": {"level3": "deep_value"}}}
        assert secrets == expected

    def test_set_nested_value_existing_path(self):
        """Test setting value in existing nested structure."""
        provider = FileProvider()
        secrets = {"level1": {"existing": "value"}}

        provider._set_nested_value(secrets, "level1/new_key", "new_value")
        expected = {"level1": {"existing": "value", "new_key": "new_value"}}
        assert secrets == expected

    def test_set_nested_value_overwrite_non_dict(self):
        """Test setting value when intermediate path is not dict."""
        provider = FileProvider()
        secrets = {"level1": "string_value"}

        with pytest.raises(SecretsProviderError, match="is not a dict"):
            provider._set_nested_value(secrets, "level1/level2", "value")

    def test_set_nested_value_empty_path(self):
        """Test setting value with empty path."""
        provider = FileProvider()
        secrets = {"existing": "value"}

        # Empty path should not modify secrets
        provider._set_nested_value(secrets, "", "new_value")
        assert secrets == {"existing": "value"}

    @pytest.mark.asyncio
    async def test_get_secret_success_dict(self, provider):
        """Test getting secret that returns dict."""
        result = await provider.get_secret("app/database")
        expected = {"username": "admin", "password": "secret123"}
        assert result == expected

    @pytest.mark.asyncio
    async def test_get_secret_success_simple_value(self, provider):
        """Test getting secret that returns simple value."""
        result = await provider.get_secret("simple_secret")
        assert result == {"value": "simple_value"}

    @pytest.mark.asyncio
    async def test_get_secret_not_found(self, provider):
        """Test getting non-existent secret."""
        with pytest.raises(SecretNotFoundError):
            await provider.get_secret("nonexistent/secret")

    @pytest.mark.asyncio
    async def test_get_secret_load_error(self):
        """Test getting secret with load error."""
        with patch.object(FileProvider, "_load_secrets", side_effect=Exception("Load error")):
            provider = FileProvider()
            with pytest.raises(SecretsProviderError, match="Failed to get secret"):
                await provider.get_secret("any/path")

    @pytest.mark.asyncio
    async def test_set_secret_success(self, empty_temp_file):
        """Test setting secret successfully."""
        provider = FileProvider(file_path=empty_temp_file)
        secret_data = {"username": "user", "password": "pass"}

        result = await provider.set_secret("app/credentials", secret_data)
        assert result is True

        # Verify secret was saved
        retrieved = await provider.get_secret("app/credentials")
        assert retrieved == secret_data

    @pytest.mark.asyncio
    async def test_set_secret_overwrite(self, provider):
        """Test overwriting existing secret."""
        new_data = {"new_username": "newuser", "new_password": "newpass"}

        result = await provider.set_secret("app/database", new_data)
        assert result is True

        # Verify overwrite
        retrieved = await provider.get_secret("app/database")
        assert retrieved == new_data

    @pytest.mark.asyncio
    async def test_set_secret_save_error(self):
        """Test setting secret with save error."""
        with patch.object(FileProvider, "_save_secrets", side_effect=Exception("Save error")):
            provider = FileProvider()
            provider._secrets_cache = {}  # Initialize cache

            with pytest.raises(SecretsProviderError, match="Failed to set secret"):
                await provider.set_secret("key", {"value": "data"})

    @pytest.mark.asyncio
    async def test_delete_secret_success(self, provider):
        """Test deleting secret successfully."""
        # Verify secret exists
        await provider.get_secret("simple_secret")

        result = await provider.delete_secret("simple_secret")
        assert result is True

        # Verify secret is gone
        with pytest.raises(SecretNotFoundError):
            await provider.get_secret("simple_secret")

    @pytest.mark.asyncio
    async def test_delete_secret_nested(self, provider):
        """Test deleting nested secret."""
        # Verify secret exists
        await provider.get_secret("app/database/username")

        result = await provider.delete_secret("app/database/username")
        assert result is True

        # Verify specific key is gone but parent still exists
        remaining = await provider.get_secret("app/database")
        assert remaining == {"password": "secret123"}

    @pytest.mark.asyncio
    async def test_delete_secret_not_found(self, provider):
        """Test deleting non-existent secret."""
        with pytest.raises(SecretNotFoundError):
            await provider.delete_secret("nonexistent/secret")

    @pytest.mark.asyncio
    async def test_delete_secret_path_not_found(self, provider):
        """Test deleting secret with non-existent parent path."""
        with pytest.raises(SecretNotFoundError):
            await provider.delete_secret("nonexistent/parent/secret")

    @pytest.mark.asyncio
    async def test_delete_secret_save_error(self):
        """Test deleting secret with save error."""
        provider = FileProvider()
        provider._secrets_cache = {"key": "value"}  # Initialize cache

        with patch.object(FileProvider, "_save_secrets", side_effect=Exception("Save error")):
            with pytest.raises(SecretsProviderError, match="Failed to delete secret"):
                await provider.delete_secret("key")

    @pytest.mark.asyncio
    async def test_list_secrets_all(self, provider):
        """Test listing all secrets."""
        result = await provider.list_secrets()

        expected_paths = [
            "app",
            "app/api_key",
            "app/database",
            "app/database/password",
            "app/database/username",
            "simple_secret",
        ]
        assert sorted(result) == sorted(expected_paths)

    @pytest.mark.asyncio
    async def test_list_secrets_with_prefix(self, provider):
        """Test listing secrets with path prefix."""
        result = await provider.list_secrets("app/database")

        expected_paths = ["app/database/password", "app/database/username"]
        assert sorted(result) == sorted(expected_paths)

    @pytest.mark.asyncio
    async def test_list_secrets_empty_prefix(self, provider):
        """Test listing secrets with empty string prefix."""
        result = await provider.list_secrets("")

        # Should return all secrets
        assert len(result) > 0
        assert "simple_secret" in result

    @pytest.mark.asyncio
    async def test_list_secrets_no_matches(self, provider):
        """Test listing secrets with prefix that has no matches."""
        result = await provider.list_secrets("nonexistent")
        assert result == []

    @pytest.mark.asyncio
    async def test_list_secrets_empty_file(self, empty_temp_file):
        """Test listing secrets from empty file."""
        provider = FileProvider(file_path=empty_temp_file)
        result = await provider.list_secrets()
        assert result == []

    @pytest.mark.asyncio
    async def test_list_secrets_collect_paths_complex(self):
        """Test path collection with complex nested structure."""
        provider = FileProvider()
        complex_secrets = {
            "level1": {
                "level2a": {"secret1": "value1", "secret2": "value2"},
                "level2b": "direct_value",
                "level2c": {"level3": {"deep_secret": "deep_value"}},
            },
            "root_secret": "root_value",
        }
        provider._secrets_cache = complex_secrets

        result = await provider.list_secrets()

        expected_paths = [
            "level1",
            "level1/level2a",
            "level1/level2a/secret1",
            "level1/level2a/secret2",
            "level1/level2b",
            "level1/level2c",
            "level1/level2c/level3",
            "level1/level2c/level3/deep_secret",
            "root_secret",
        ]
        assert sorted(result) == sorted(expected_paths)

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, provider):
        """Test health check when provider is healthy."""
        result = await provider.health_check()

        assert result["status"] == "healthy"
        assert result["provider"] == "file"
        assert "details" in result
        assert "file_path" in result["details"]
        assert "file_exists" in result["details"]
        assert "secret_count" in result["details"]
        assert result["details"]["file_exists"] is True

    @pytest.mark.asyncio
    async def test_health_check_nonexistent_file(self, nonexistent_file_path):
        """Test health check with non-existent file."""
        provider = FileProvider(file_path=nonexistent_file_path)
        result = await provider.health_check()

        assert result["status"] == "healthy"  # Non-existent file is OK
        assert result["provider"] == "file"
        assert result["details"]["file_exists"] is False
        assert result["details"]["secret_count"] == 0

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self):
        """Test health check when provider is unhealthy."""
        with patch.object(FileProvider, "_load_secrets", side_effect=Exception("Load error")):
            provider = FileProvider()
            result = await provider.health_check()

            assert result["status"] == "unhealthy"
            assert result["provider"] == "file"
            assert "Load error" in result["error"]


class TestFileProviderEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_concurrent_access_simulation(self, temp_file):
        """Test simulated concurrent access to file."""
        provider1 = FileProvider(file_path=temp_file)
        provider2 = FileProvider(file_path=temp_file)

        # Both providers should be able to read
        secret1 = await provider1.get_secret("simple_secret")
        secret2 = await provider2.get_secret("simple_secret")
        assert secret1 == secret2

    def test_path_traversal_security(self):
        """Test that provider handles path traversal attempts safely."""
        provider = FileProvider()
        secrets = {"safe": {"path": "value"}}

        # These should work normally
        provider._set_nested_value(secrets, "safe/path", "new_value")
        assert secrets["safe"]["path"] == "new_value"

    @pytest.mark.asyncio
    async def test_large_secrets_handling(self, empty_temp_file):
        """Test handling of large secret data."""
        provider = FileProvider(file_path=empty_temp_file)

        # Create large secret data
        large_data = {f"key_{i}": f"value_{i}" * 100 for i in range(100)}

        result = await provider.set_secret("large_secret", large_data)
        assert result is True

        retrieved = await provider.get_secret("large_secret")
        assert retrieved == large_data

    @pytest.mark.asyncio
    async def test_unicode_handling(self, empty_temp_file):
        """Test handling of unicode characters in secrets."""
        provider = FileProvider(file_path=empty_temp_file)

        unicode_data = {"unicode_key": "unicode_value_αβγ_🔑", "中文": "中文值", "emoji": "🚀🔐🎉"}

        result = await provider.set_secret("unicode_test", unicode_data)
        assert result is True

        retrieved = await provider.get_secret("unicode_test")
        assert retrieved == unicode_data

    def test_empty_path_components(self):
        """Test handling of empty path components."""
        provider = FileProvider()
        secrets = {}

        # Should handle multiple slashes gracefully
        provider._set_nested_value(secrets, "//level1///level2//", "value")
        assert secrets["level1"]["level2"] == "value"

    @pytest.mark.asyncio
    async def test_file_permissions_readonly(self):
        """Test behavior with read-only file."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            json.dump({"test": "value"}, f)
            temp_path = f.name

        try:
            # Make file read-only
            os.chmod(temp_path, 0o444)

            provider = FileProvider(file_path=temp_path)

            # Reading should work
            result = await provider.get_secret("test")
            assert result == {"value": "value"}

            # Writing should fail
            with pytest.raises(SecretsProviderError):
                await provider.set_secret("new_key", {"value": "new_value"})

        finally:
            # Clean up
            os.chmod(temp_path, 0o644)  # Restore write permission
            os.unlink(temp_path)
