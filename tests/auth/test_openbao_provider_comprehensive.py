"""
Comprehensive OpenBao Provider Testing
Implementation of comprehensive OpenBao provider testing to achieve 85% coverage.
"""

import json
from unittest.mock import AsyncMock, Mock, patch

import pytest

from dotmac.platform.secrets.exceptions import (
    ConfigurationError,
    ProviderAuthenticationError,
    ProviderAuthorizationError,
    SecretNotFoundError,
    SecretsProviderError,
)
from dotmac.platform.secrets.openbao_provider import (
    OpenBaoProvider,
    create_openbao_provider,
    create_vault_provider,
)


class MockResponse:
    """Mock aiohttp response"""

    def __init__(self, status=200, json_data=None, text_data="", exc_on_json=False):
        self.status = status
        self._json_data = json_data or {}
        self._text_data = text_data
        self._exc_on_json = exc_on_json

    async def json(self):
        if self._exc_on_json:
            raise json.JSONDecodeError("Invalid JSON", "", 0)
        return self._json_data

    async def text(self):
        return self._text_data


class MockSession:
    """Mock aiohttp session"""

    def __init__(self, responses=None, connection_errors=None):
        self.responses = responses or {}
        self.connection_errors = connection_errors or []
        self.requests = []
        self.closed = False
        self.headers = {}

    def request(self, method, url, **kwargs):
        return MockContextManager(self._get_response(method, url, **kwargs))

    def _get_response(self, method, url, **kwargs):
        self.requests.append((method, url, kwargs))

        # Simulate connection errors
        if self.connection_errors:
            error = self.connection_errors.pop(0)
            raise error

        # Return configured response
        key = f"{method} {url}"
        if key in self.responses:
            return self.responses[key]

        # Default responses
        if "sys/health" in url:
            return MockResponse(200, {"sealed": False, "standby": False})
        elif "secret/data/" in url:
            return MockResponse(200, {"data": {"data": {"test": "value"}}})
        else:
            return MockResponse(404, {}, "Not found")

    async def close(self):
        self.closed = True


class MockContextManager:
    """Mock context manager for aiohttp requests"""

    def __init__(self, response):
        self.response = response

    async def __aenter__(self):
        return self.response

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class TestOpenBaoProviderComprehensive:
    """Comprehensive OpenBao provider testing"""

    # Initialization Tests

    def test_openbao_provider_initialization_success(self):
        """Test successful OpenBao provider initialization"""
        provider = OpenBaoProvider(url="https://vault.example.com", token="test-token")

        assert provider.url == "https://vault.example.com"
        assert provider.token == "test-token"
        assert provider.mount_point == "secret"
        assert provider.kv_version == 2
        assert provider.timeout == 30
        assert provider.max_retries == 3
        assert provider.verify_ssl is True

    def test_openbao_provider_initialization_full_config(self):
        """Test OpenBao provider with full configuration"""
        provider = OpenBaoProvider(
            url="https://vault.example.com/",  # Test URL trimming
            token="test-token",
            mount_point="kv",
            kv_version=1,
            namespace="test-namespace",
            tenant_id="tenant-123",
            timeout=60,
            max_retries=5,
            retry_delay=2.0,
            verify_ssl=False,
        )

        assert provider.url == "https://vault.example.com"  # Trimmed
        assert provider.mount_point == "kv"
        assert provider.kv_version == 1
        assert provider.namespace == "test-namespace"
        assert provider.tenant_id == "tenant-123"
        assert provider.timeout == 60
        assert provider.max_retries == 5
        assert provider.retry_delay == 2.0
        assert provider.verify_ssl is False

    def test_openbao_provider_initialization_errors(self):
        """Test initialization validation errors"""
        # Missing URL
        with pytest.raises(ConfigurationError, match="OpenBao URL is required"):
            OpenBaoProvider(url="", token="test-token")

        # Missing token
        with pytest.raises(ConfigurationError, match="OpenBao token is required"):
            OpenBaoProvider(url="https://vault.example.com", token="")

        # Invalid KV version
        with pytest.raises(ConfigurationError, match="KV version must be 1 or 2"):
            OpenBaoProvider(url="https://vault.example.com", token="test-token", kv_version=3)

    # Path Building Tests

    def test_build_path_kv_v2(self):
        """Test path building for KV v2"""
        provider = OpenBaoProvider(
            url="https://vault.example.com", token="test-token", kv_version=2
        )

        # Basic path
        path = provider._build_path("myapp/config")  # type: ignore[reportPrivateUsage]
        assert path == "v1/secret/data/myapp/config"

        # Path with leading slash
        path = provider._build_path("/myapp/config")  # type: ignore[reportPrivateUsage]
        assert path == "v1/secret/data/myapp/config"

    def test_build_path_kv_v1(self):
        """Test path building for KV v1"""
        provider = OpenBaoProvider(
            url="https://vault.example.com", token="test-token", kv_version=1
        )

        path = provider._build_path("myapp/config")  # type: ignore[reportPrivateUsage]
        assert path == "v1/secret/myapp/config"

    def test_build_path_with_tenant(self):
        """Test path building with tenant isolation"""
        provider = OpenBaoProvider(
            url="https://vault.example.com", token="test-token", tenant_id="tenant-123"
        )

        path = provider._build_path("myapp/config")  # type: ignore[reportPrivateUsage]
        assert path == "v1/secret/data/tenant/tenant-123/myapp/config"

    def test_build_metadata_path(self):
        """Test metadata path building for KV v2"""
        provider = OpenBaoProvider(
            url="https://vault.example.com", token="test-token", kv_version=2
        )

        path = provider._build_metadata_path("myapp/config")
        assert path == "v1/secret/metadata/myapp/config"

    def test_build_metadata_path_with_tenant(self):
        """Test metadata path with tenant"""
        provider = OpenBaoProvider(
            url="https://vault.example.com",
            token="test-token",
            tenant_id="tenant-123",
            kv_version=2,
        )

        path = provider._build_metadata_path("myapp/config")
        assert path == "v1/secret/metadata/tenant/tenant-123/myapp/config"

    def test_build_metadata_path_kv_v1_error(self):
        """Test metadata path error for KV v1"""
        provider = OpenBaoProvider(
            url="https://vault.example.com", token="test-token", kv_version=1
        )

        with pytest.raises(ValueError, match="Metadata path only available for KV v2"):
            provider._build_metadata_path("myapp/config")

    # Session Management Tests

    @pytest.mark.asyncio
    async def test_ensure_session_creation(self):
        """Test session creation"""
        fake_session = Mock()
        fake_session.closed = False
        provider = OpenBaoProvider(
            url="https://vault.example.com",
            token="test-token",
            verify_ssl=False,
            http_client=fake_session,
        )

        await provider._ensure_session()
        assert provider._session is fake_session

    @pytest.mark.asyncio
    async def test_ensure_session_with_namespace(self):
        """Test session creation with namespace header"""
        fake_session = Mock()
        fake_session.headers = {}
        fake_session.closed = False
        provider = OpenBaoProvider(
            url="https://vault.example.com",
            token="test-token",
            namespace="test-namespace",
            http_client=fake_session,
        )

        await provider._ensure_session()
        assert provider._session.headers["X-Vault-Namespace"] == "test-namespace"

    @pytest.mark.asyncio
    async def test_close_session(self):
        """Test session closing"""
        provider = OpenBaoProvider(url="https://vault.example.com", token="test-token")

        # Mock session
        mock_session = AsyncMock()
        mock_session.closed = False
        provider._session = mock_session

        await provider.close()

        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_no_session(self):
        """Test closing when no session exists"""
        provider = OpenBaoProvider(url="https://vault.example.com", token="test-token")

        # Should not raise any errors
        await provider.close()

    # Context Manager Tests

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager"""
        provider = OpenBaoProvider(url="https://vault.example.com", token="test-token")

        with patch.object(provider, "_ensure_session") as mock_ensure:
            with patch.object(provider, "close") as mock_close:
                async with provider as p:
                    assert p == provider
                    mock_ensure.assert_called_once()

                mock_close.assert_called_once()

    # Request Tests

    @pytest.mark.asyncio
    async def test_request_success_200(self):
        """Test successful request with 200 status"""
        provider = OpenBaoProvider(url="https://vault.example.com", token="test-token")

        mock_response = MockResponse(200, {"data": {"test": "value"}})
        mock_session = MockSession({"GET https://vault.example.com/v1/test": mock_response})

        provider._session = mock_session

        result = await provider._request("GET", "v1/test")
        assert result == {"data": {"test": "value"}}

    @pytest.mark.asyncio
    async def test_request_success_204(self):
        """Test successful request with 204 status"""
        provider = OpenBaoProvider(url="https://vault.example.com", token="test-token")

        mock_response = MockResponse(204)
        mock_session = MockSession({"DELETE https://vault.example.com/v1/test": mock_response})

        provider._session = mock_session

        result = await provider._request("DELETE", "v1/test")
        assert result == {"success": True}

    @pytest.mark.asyncio
    async def test_request_json_decode_error(self):
        """Test request with JSON decode error"""
        provider = OpenBaoProvider(url="https://vault.example.com", token="test-token")

        mock_response = MockResponse(200, {}, "plain text response", exc_on_json=True)
        mock_session = MockSession({"GET https://vault.example.com/v1/test": mock_response})

        provider._session = mock_session

        result = await provider._request("GET", "v1/test")
        assert result == {"data": "plain text response"}

    @pytest.mark.asyncio
    async def test_request_404_error(self):
        """Test 404 error handling"""
        provider = OpenBaoProvider(url="https://vault.example.com", token="test-token")

        mock_response = MockResponse(404)
        mock_session = MockSession({"GET https://vault.example.com/v1/test": mock_response})

        provider._session = mock_session

        with pytest.raises(SecretNotFoundError):
            await provider._request("GET", "v1/test")

    @pytest.mark.asyncio
    async def test_request_403_error(self):
        """Test 403 authorization error handling"""
        provider = OpenBaoProvider(url="https://vault.example.com", token="test-token")

        mock_response = MockResponse(403)
        mock_session = MockSession({"GET https://vault.example.com/v1/test": mock_response})

        provider._session = mock_session

        with pytest.raises(ProviderAuthorizationError):
            await provider._request("GET", "v1/test")

    @pytest.mark.asyncio
    async def test_request_401_error(self):
        """Test 401 authentication error handling"""
        provider = OpenBaoProvider(url="https://vault.example.com", token="test-token")

        mock_response = MockResponse(401)
        mock_session = MockSession({"GET https://vault.example.com/v1/test": mock_response})

        provider._session = mock_session

        with pytest.raises(ProviderAuthenticationError):
            await provider._request("GET", "v1/test")

    @pytest.mark.asyncio
    async def test_request_retry_logic(self):
        """Test retry logic on server errors"""
        provider = OpenBaoProvider(
            url="https://vault.example.com",
            token="test-token",
            max_retries=2,
            retry_delay=0.01,  # Fast retry for testing
        )

        # First request fails with 500, second succeeds
        responses = {}
        call_count = 0

        def get_response(method, url, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return MockResponse(500, {}, "Internal server error")
            return MockResponse(200, {"data": "success"})

        mock_session = MockSession()
        mock_session._get_response = get_response
        provider._session = mock_session

        result = await provider._request("GET", "v1/test")
        assert result == {"data": "success"}
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_request_max_retries_exceeded(self):
        """Test max retries exceeded"""
        provider = OpenBaoProvider(
            url="https://vault.example.com", token="test-token", max_retries=1, retry_delay=0.01
        )

        mock_response = MockResponse(500, {}, "Server error")
        mock_session = MockSession({"GET https://vault.example.com/v1/test": mock_response})

        provider._session = mock_session

        with pytest.raises(SecretsProviderError, match="HTTP 500"):
            await provider._request("GET", "v1/test")

    @pytest.mark.asyncio
    async def test_request_with_data(self):
        """Test request with JSON data"""
        provider = OpenBaoProvider(url="https://vault.example.com", token="test-token")

        mock_response = MockResponse(200, {"success": True})
        mock_session = MockSession({"POST https://vault.example.com/v1/test": mock_response})

        provider._session = mock_session

        result = await provider._request("POST", "v1/test", {"key": "value"})
        assert result == {"success": True}

        # Verify data was passed correctly
        assert len(mock_session.requests) == 1
        method, url, kwargs = mock_session.requests[0]
        assert method == "POST"
        assert kwargs["json"] == {"key": "value"}

    # Get Secret Tests

    @pytest.mark.asyncio
    async def test_get_secret_kv_v2_success(self):
        """Test getting secret from KV v2"""
        provider = OpenBaoProvider(
            url="https://vault.example.com", token="test-token", kv_version=2
        )

        mock_response = MockResponse(
            200,
            {
                "data": {
                    "data": {"username": "admin", "password": "secret123"},
                    "metadata": {"version": 1},
                }
            },
        )

        provider._session = MockSession(
            {"GET https://vault.example.com/v1/secret/data/myapp/config": mock_response}
        )

        result = await provider.get_secret("myapp/config")
        assert result == {"username": "admin", "password": "secret123"}

    @pytest.mark.asyncio
    async def test_get_secret_kv_v1_success(self):
        """Test getting secret from KV v1"""
        provider = OpenBaoProvider(
            url="https://vault.example.com", token="test-token", kv_version=1
        )

        mock_response = MockResponse(200, {"data": {"username": "admin", "password": "secret123"}})

        provider._session = MockSession(
            {"GET https://vault.example.com/v1/secret/myapp/config": mock_response}
        )

        result = await provider.get_secret("myapp/config")
        assert result == {"username": "admin", "password": "secret123"}

    @pytest.mark.asyncio
    async def test_get_secret_with_version(self):
        """Test getting specific version of secret"""
        provider = OpenBaoProvider(
            url="https://vault.example.com", token="test-token", kv_version=2
        )

        mock_response = MockResponse(
            200,
            {
                "data": {
                    "data": {"username": "admin", "password": "old_password"},
                    "metadata": {"version": 5},
                }
            },
        )

        provider._session = MockSession(
            {"GET https://vault.example.com/v1/secret/data/myapp/config?version=5": mock_response}
        )

        result = await provider.get_secret("myapp/config", version=5)
        assert result == {"username": "admin", "password": "old_password"}

    @pytest.mark.asyncio
    async def test_get_secret_not_found(self):
        """Test secret not found error"""
        provider = OpenBaoProvider(url="https://vault.example.com", token="test-token")

        provider._session = MockSession(
            {"GET https://vault.example.com/v1/secret/data/nonexistent": MockResponse(404)}
        )

        with pytest.raises(SecretNotFoundError):
            await provider.get_secret("nonexistent")

    @pytest.mark.asyncio
    async def test_get_secret_kv_v2_malformed_response(self):
        """Test KV v2 with malformed response"""
        provider = OpenBaoProvider(
            url="https://vault.example.com", token="test-token", kv_version=2
        )

        # Missing nested data structure
        mock_response = MockResponse(200, {"data": {"metadata": {"version": 1}}})

        provider._session = MockSession(
            {"GET https://vault.example.com/v1/secret/data/myapp/config": mock_response}
        )

        with pytest.raises(SecretNotFoundError):
            await provider.get_secret("myapp/config")

    @pytest.mark.asyncio
    async def test_get_secret_kv_v1_malformed_response(self):
        """Test KV v1 with malformed response"""
        provider = OpenBaoProvider(
            url="https://vault.example.com", token="test-token", kv_version=1
        )

        # Missing data key
        mock_response = MockResponse(200, {"metadata": {"version": 1}})

        provider._session = MockSession(
            {"GET https://vault.example.com/v1/secret/myapp/config": mock_response}
        )

        with pytest.raises(SecretNotFoundError):
            await provider.get_secret("myapp/config")

    @pytest.mark.asyncio
    async def test_get_secret_unexpected_error(self):
        """Test unexpected error handling"""
        provider = OpenBaoProvider(url="https://vault.example.com", token="test-token")

        # Mock request to raise unexpected error
        with patch.object(provider, "_request", side_effect=ValueError("Unexpected error")):
            with pytest.raises(SecretsProviderError, match="Failed to get secret"):
                await provider.get_secret("myapp/config")

    # Set Secret Tests

    @pytest.mark.asyncio
    async def test_set_secret_kv_v2_success(self):
        """Test setting secret in KV v2"""
        provider = OpenBaoProvider(
            url="https://vault.example.com", token="test-token", kv_version=2
        )

        mock_response = MockResponse(200, {"success": True})
        mock_session = MockSession(
            {"POST https://vault.example.com/v1/secret/data/myapp/config": mock_response}
        )

        provider._session = mock_session

        result = await provider.set_secret(
            "myapp/config", {"username": "admin", "password": "secret123"}
        )
        assert result is True

        # Verify data structure for KV v2
        method, url, kwargs = mock_session.requests[0]
        expected_data = {"data": {"username": "admin", "password": "secret123"}}
        assert kwargs["json"] == expected_data

    @pytest.mark.asyncio
    async def test_set_secret_kv_v2_with_cas(self):
        """Test setting secret with check-and-set"""
        provider = OpenBaoProvider(
            url="https://vault.example.com", token="test-token", kv_version=2
        )

        mock_response = MockResponse(200, {"success": True})
        mock_session = MockSession(
            {"POST https://vault.example.com/v1/secret/data/myapp/config": mock_response}
        )

        provider._session = mock_session

        result = await provider.set_secret("myapp/config", {"username": "admin"}, cas=5)
        assert result is True

        # Verify CAS option was included
        method, url, kwargs = mock_session.requests[0]
        expected_data = {"data": {"username": "admin"}, "options": {"cas": 5}}
        assert kwargs["json"] == expected_data

    @pytest.mark.asyncio
    async def test_set_secret_kv_v1_success(self):
        """Test setting secret in KV v1"""
        provider = OpenBaoProvider(
            url="https://vault.example.com", token="test-token", kv_version=1
        )

        mock_response = MockResponse(200, {"success": True})
        mock_session = MockSession(
            {"POST https://vault.example.com/v1/secret/myapp/config": mock_response}
        )

        provider._session = mock_session

        result = await provider.set_secret(
            "myapp/config", {"username": "admin", "password": "secret123"}
        )
        assert result is True

        # Verify data is passed directly for KV v1
        method, url, kwargs = mock_session.requests[0]
        assert kwargs["json"] == {"username": "admin", "password": "secret123"}

    @pytest.mark.asyncio
    async def test_set_secret_error(self):
        """Test set secret error handling"""
        provider = OpenBaoProvider(url="https://vault.example.com", token="test-token")

        with patch.object(provider, "_request", side_effect=ValueError("Request failed")):
            with pytest.raises(SecretsProviderError, match="Failed to set secret"):
                await provider.set_secret("myapp/config", {"test": "value"})

    # Delete Secret Tests

    @pytest.mark.asyncio
    async def test_delete_secret_kv_v2_latest(self):
        """Test deleting latest version in KV v2"""
        provider = OpenBaoProvider(
            url="https://vault.example.com", token="test-token", kv_version=2
        )

        mock_response = MockResponse(204)
        mock_session = MockSession(
            {"DELETE https://vault.example.com/v1/secret/data/myapp/config": mock_response}
        )

        provider._session = mock_session

        result = await provider.delete_secret("myapp/config")
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_secret_kv_v2_specific_versions(self):
        """Test deleting specific versions in KV v2"""
        provider = OpenBaoProvider(
            url="https://vault.example.com", token="test-token", kv_version=2
        )

        mock_response = MockResponse(200, {"success": True})
        mock_session = MockSession(
            {"POST https://vault.example.com/v1/secret/delete/myapp/config": mock_response}
        )

        provider._session = mock_session

        result = await provider.delete_secret("myapp/config", versions=[1, 2, 3])
        assert result is True

        # Verify versions were included in request
        method, url, kwargs = mock_session.requests[0]
        assert kwargs["json"] == {"versions": [1, 2, 3]}

    @pytest.mark.asyncio
    async def test_delete_secret_kv_v1(self):
        """Test deleting secret in KV v1"""
        provider = OpenBaoProvider(
            url="https://vault.example.com", token="test-token", kv_version=1
        )

        mock_response = MockResponse(204)
        mock_session = MockSession(
            {"DELETE https://vault.example.com/v1/secret/myapp/config": mock_response}
        )

        provider._session = mock_session

        result = await provider.delete_secret("myapp/config")
        assert result is True

    # List Secrets Tests

    @pytest.mark.asyncio
    async def test_list_secrets_kv_v2_success(self):
        """Test listing secrets in KV v2"""
        provider = OpenBaoProvider(
            url="https://vault.example.com", token="test-token", kv_version=2
        )

        mock_response = MockResponse(200, {"data": {"keys": ["config1", "config2", "subdir/"]}})

        mock_session = MockSession()
        mock_session.responses = {
            "GET https://vault.example.com/v1/secret/metadata/myapp?list=true": mock_response
        }
        provider._session = mock_session

        result = await provider.list_secrets("myapp")
        assert result == ["config1", "config2", "subdir/"]

    @pytest.mark.asyncio
    async def test_list_secrets_kv_v2_root(self):
        """Test listing secrets at root in KV v2"""
        provider = OpenBaoProvider(
            url="https://vault.example.com", token="test-token", kv_version=2
        )

        mock_response = MockResponse(200, {"data": {"keys": ["app1/", "app2/", "shared"]}})

        mock_session = MockSession()
        mock_session.responses = {
            "GET https://vault.example.com/v1/secret/metadata/?list=true": mock_response
        }
        provider._session = mock_session

        result = await provider.list_secrets("")
        assert result == ["app1/", "app2/", "shared"]

    @pytest.mark.asyncio
    async def test_list_secrets_kv_v1_success(self):
        """Test listing secrets in KV v1"""
        provider = OpenBaoProvider(
            url="https://vault.example.com", token="test-token", kv_version=1
        )

        mock_response = MockResponse(200, {"data": {"keys": ["config1", "config2"]}})

        provider._session = MockSession(
            {"GET https://vault.example.com/v1/secret/myapp?list=true": mock_response}
        )

        result = await provider.list_secrets("myapp")
        assert result == ["config1", "config2"]

    @pytest.mark.asyncio
    async def test_list_secrets_empty_result(self):
        """Test listing secrets with empty result"""
        provider = OpenBaoProvider(url="https://vault.example.com", token="test-token")

        mock_response = MockResponse(200, {"data": {}})
        mock_session = MockSession()
        mock_session.responses = {
            "GET https://vault.example.com/v1/secret/metadata/myapp?list=true": mock_response
        }
        provider._session = mock_session

        result = await provider.list_secrets("myapp")
        assert result == []

    @pytest.mark.asyncio
    async def test_list_secrets_not_found(self):
        """Test listing secrets when path doesn't exist"""
        provider = OpenBaoProvider(url="https://vault.example.com", token="test-token")

        mock_session = MockSession()
        mock_session.responses = {
            "GET https://vault.example.com/v1/secret/metadata/nonexistent?list=true": MockResponse(
                404
            )
        }
        provider._session = mock_session

        result = await provider.list_secrets("nonexistent")
        assert result == []

    @pytest.mark.asyncio
    async def test_list_secrets_error(self):
        """Test list secrets error handling"""
        provider = OpenBaoProvider(url="https://vault.example.com", token="test-token")

        with patch.object(provider, "_request", side_effect=ValueError("Request failed")):
            with pytest.raises(SecretsProviderError, match="Failed to list secrets"):
                await provider.list_secrets("myapp")

    # Metadata Tests

    @pytest.mark.asyncio
    async def test_get_secret_metadata_success(self):
        """Test getting secret metadata"""
        provider = OpenBaoProvider(
            url="https://vault.example.com", token="test-token", kv_version=2
        )

        mock_response = MockResponse(
            200,
            {
                "data": {
                    "created_time": "2023-01-01T00:00:00Z",
                    "current_version": 3,
                    "versions": {"1": {}, "2": {}, "3": {}},
                }
            },
        )

        provider._session = MockSession(
            {"GET https://vault.example.com/v1/secret/metadata/myapp/config": mock_response}
        )

        result = await provider.get_secret_metadata("myapp/config")
        assert result["current_version"] == 3
        assert "versions" in result

    @pytest.mark.asyncio
    async def test_get_secret_metadata_kv_v1_error(self):
        """Test metadata error for KV v1"""
        provider = OpenBaoProvider(
            url="https://vault.example.com", token="test-token", kv_version=1
        )

        with pytest.raises(ValueError, match="Metadata only available for KV v2"):
            await provider.get_secret_metadata("myapp/config")

    @pytest.mark.asyncio
    async def test_get_secret_metadata_not_found(self):
        """Test metadata not found"""
        provider = OpenBaoProvider(
            url="https://vault.example.com", token="test-token", kv_version=2
        )

        mock_response = MockResponse(404)  # Not found
        mock_session = MockSession()
        mock_session.responses = {
            "GET https://vault.example.com/v1/secret/metadata/nonexistent": mock_response
        }
        provider._session = mock_session

        with pytest.raises(SecretsProviderError):
            await provider.get_secret_metadata("nonexistent")

    @pytest.mark.asyncio
    async def test_get_secret_metadata_error(self):
        """Test metadata error handling"""
        provider = OpenBaoProvider(
            url="https://vault.example.com", token="test-token", kv_version=2
        )

        with patch.object(provider, "_request", side_effect=ValueError("Request failed")):
            with pytest.raises(SecretsProviderError, match="Failed to get metadata"):
                await provider.get_secret_metadata("myapp/config")

    # Health Check Tests

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test successful health check"""
        provider = OpenBaoProvider(url="https://vault.example.com", token="test-token")

        mock_response = MockResponse(
            200, {"sealed": False, "standby": False, "server_time_utc": 1234567890}
        )

        provider._session = MockSession(
            {"GET https://vault.example.com/v1/sys/health": mock_response}
        )

        result = await provider.health_check()
        assert result["status"] == "healthy"
        assert result["provider"] == "openbao"
        assert "details" in result
        assert result["details"]["sealed"] is False

    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test health check failure"""
        provider = OpenBaoProvider(url="https://vault.example.com", token="test-token")

        with patch.object(provider, "_request", side_effect=ConnectionError("Connection failed")):
            result = await provider.health_check()
            assert result["status"] == "unhealthy"
            assert result["provider"] == "openbao"
            assert "error" in result

    # Token Renewal Tests

    @pytest.mark.asyncio
    async def test_renew_token_success(self):
        """Test successful token renewal"""
        provider = OpenBaoProvider(url="https://vault.example.com", token="test-token")

        mock_response = MockResponse(
            200, {"auth": {"lease_duration": 3600, "renewable": True, "client_token": "new-token"}}
        )

        provider._session = MockSession(
            {"POST https://vault.example.com/v1/auth/token/renew-self": mock_response}
        )

        result = await provider.renew_token()
        assert result is True
        assert provider.token_lease_duration == 3600
        assert provider.token_renewable is True
        assert provider.token_created_at > 0

    @pytest.mark.asyncio
    async def test_renew_token_no_auth(self):
        """Test token renewal with missing auth info"""
        provider = OpenBaoProvider(url="https://vault.example.com", token="test-token")

        mock_response = MockResponse(200, {"data": "success"})  # Missing auth key
        provider._session = MockSession(
            {"POST https://vault.example.com/v1/auth/token/renew-self": mock_response}
        )

        result = await provider.renew_token()
        assert result is False

    @pytest.mark.asyncio
    async def test_renew_token_failure(self):
        """Test token renewal failure"""
        provider = OpenBaoProvider(url="https://vault.example.com", token="test-token")

        with patch.object(provider, "_request", side_effect=Exception("Renewal failed")):
            result = await provider.renew_token()
            assert result is False

    # String Representation Test

    def test_repr(self):
        """Test string representation"""
        provider = OpenBaoProvider(
            url="https://vault.example.com", token="test-token", mount_point="kv", kv_version=1
        )

        repr_str = repr(provider)
        assert "OpenBaoProvider" in repr_str
        assert "https://vault.example.com" in repr_str
        assert "mount_point=kv" in repr_str
        assert "kv_version=1" in repr_str

    # Factory Function Tests

    def test_create_openbao_provider(self):
        """Test OpenBao provider factory function"""
        provider = create_openbao_provider(
            "https://vault.example.com", "test-token", mount_point="kv", kv_version=1
        )

        assert isinstance(provider, OpenBaoProvider)
        assert provider.url == "https://vault.example.com"
        assert provider.token == "test-token"
        assert provider.mount_point == "kv"
        assert provider.kv_version == 1

    def test_create_vault_provider(self):
        """Test Vault provider factory function (alias)"""
        provider = create_vault_provider("https://vault.example.com", "test-token")

        assert isinstance(provider, OpenBaoProvider)
        assert provider.url == "https://vault.example.com"
        assert provider.token == "test-token"

    # Integration-style Tests

    @pytest.mark.asyncio
    async def test_full_workflow_kv_v2(self):
        """Test complete workflow with KV v2"""
        provider = OpenBaoProvider(
            url="https://vault.example.com", token="test-token", kv_version=2
        )

        responses = {
            # Set secret
            "POST https://vault.example.com/v1/secret/data/myapp/config": MockResponse(
                200, {"success": True}
            ),
            # Get secret
            "GET https://vault.example.com/v1/secret/data/myapp/config": MockResponse(
                200, {"data": {"data": {"username": "admin"}}}
            ),
            # List secrets
            "GET https://vault.example.com/v1/secret/metadata/myapp?list=true": MockResponse(
                200, {"data": {"keys": ["config"]}}
            ),
            # Get metadata
            "GET https://vault.example.com/v1/secret/metadata/myapp/config": MockResponse(
                200, {"data": {"current_version": 1}}
            ),
            # Delete secret
            "DELETE https://vault.example.com/v1/secret/data/myapp/config": MockResponse(204),
        }

        mock_session = MockSession()
        mock_session.responses = responses
        provider._session = mock_session

        # Set secret
        await provider.set_secret("myapp/config", {"username": "admin"})

        # Get secret
        result = await provider.get_secret("myapp/config")
        assert result == {"username": "admin"}

        # List secrets
        secrets = await provider.list_secrets("myapp")
        assert "config" in secrets

        # Get metadata
        metadata = await provider.get_secret_metadata("myapp/config")
        assert metadata["current_version"] == 1

        # Delete secret
        await provider.delete_secret("myapp/config")

    @pytest.mark.asyncio
    async def test_tenant_isolation(self):
        """Test tenant path isolation"""
        provider = OpenBaoProvider(
            url="https://vault.example.com", token="test-token", tenant_id="tenant-123"
        )

        mock_response = MockResponse(200, {"data": {"data": {"test": "value"}}})

        # Verify tenant path is used
        provider._session = MockSession(
            {
                "GET https://vault.example.com/v1/secret/data/tenant/tenant-123/myapp/config": mock_response
            }
        )

        result = await provider.get_secret("myapp/config")
        assert result == {"test": "value"}

    @pytest.mark.asyncio
    async def test_error_logging(self):
        """Test error logging integration"""
        provider = OpenBaoProvider(url="https://vault.example.com", token="test-token")

        with patch("dotmac.platform.secrets.openbao_provider.logger") as mock_logger:
            with patch.object(provider, "_request", side_effect=ValueError("Test error")):
                with pytest.raises(SecretsProviderError):
                    await provider.get_secret("test/path")

                # Verify error was logged
                mock_logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_success_logging(self):
        """Test success logging integration"""
        provider = OpenBaoProvider(url="https://vault.example.com", token="test-token")

        mock_response = MockResponse(200, {"success": True})
        provider._session = MockSession(
            {"POST https://vault.example.com/v1/secret/data/test": mock_response}
        )

        with patch("dotmac.platform.secrets.openbao_provider.logger") as mock_logger:
            await provider.set_secret("test", {"key": "value"})

            # Verify success was logged
            mock_logger.info.assert_called_with("Secret stored successfully", secret_path="test")

    @pytest.mark.asyncio
    async def test_retry_logging(self):
        """Test retry attempt logging"""
        provider = OpenBaoProvider(
            url="https://vault.example.com", token="test-token", max_retries=1, retry_delay=0.01
        )

        call_count = 0

        def get_response(method, url, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return MockResponse(500, {}, "Server error")
            return MockResponse(200, {"data": "success"})

        mock_session = MockSession()
        mock_session._get_response = get_response
        provider._session = mock_session

        with patch("dotmac.platform.secrets.openbao_provider.logger") as mock_logger:
            await provider._request("GET", "v1/test")

            # Verify retry was logged
            mock_logger.warning.assert_called()
