"""
Test file to validate mock fixtures work correctly.
This ensures all mock fixtures can be imported and used properly.
"""

import asyncio
import pytest

from tests.fixtures import (
    MockAsyncSession,
    MockRedis,
    MockVaultClient,
    MockTracer,
    MockHTTPSession,
    mock_session,
    mock_redis,
    mock_vault_client,
    mock_tracer,
    mock_http_session,
)


class TestMockFixtureImports:
    """Test that all mock fixtures can be imported."""

    def test_database_mocks_import(self):
        """Test database mock imports."""
        session = MockAsyncSession()
        assert session is not None
        assert hasattr(session, 'commit')
        assert hasattr(session, 'add')

    def test_redis_mocks_import(self):
        """Test Redis mock imports."""
        redis = MockRedis()
        assert redis is not None
        assert hasattr(redis, 'get')
        assert hasattr(redis, 'set')

    def test_vault_mocks_import(self):
        """Test Vault mock imports."""
        vault = MockVaultClient()
        assert vault is not None
        assert hasattr(vault, 'read_secret')
        assert hasattr(vault, 'write_secret')

    def test_otel_mocks_import(self):
        """Test OpenTelemetry mock imports."""
        tracer = MockTracer()
        assert tracer is not None
        assert hasattr(tracer, 'start_span')

    def test_http_mocks_import(self):
        """Test HTTP mock imports."""
        session = MockHTTPSession()
        assert session is not None
        assert hasattr(session, 'get')
        assert hasattr(session, 'post')


@pytest.mark.asyncio
class TestMockDatabaseFunctionality:
    """Test mock database functionality."""

    async def test_session_operations(self, mock_session):
        """Test basic session operations."""
        # Test add
        from tests.fixtures.mock_database import MockModel
        model = MockModel(name="test")
        mock_session.add(model)

        # Test commit
        await mock_session.commit()
        assert mock_session.committed is True

        # Test rollback
        await mock_session.rollback()
        assert mock_session.rolled_back is True

    async def test_session_context_manager(self):
        """Test session as context manager."""
        from tests.fixtures.mock_database import MockAsyncSession, MockModel
        session = MockAsyncSession()

        async with session:
            session.add(MockModel(name="test"))

        assert session.committed is True
        assert session.closed is True


@pytest.mark.asyncio
class TestMockRedisFunctionality:
    """Test mock Redis functionality."""

    async def test_basic_operations(self, mock_redis):
        """Test basic Redis operations."""
        # Test set/get
        await mock_redis.set("key", "value")
        value = await mock_redis.get("key")
        assert value == b"value"

        # Test exists
        exists = await mock_redis.exists("key")
        assert exists == 1

        # Test delete
        deleted = await mock_redis.delete("key")
        assert deleted == 1
        exists = await mock_redis.exists("key")
        assert exists == 0

    async def test_hash_operations(self, mock_redis):
        """Test Redis hash operations."""
        await mock_redis.hset("hash", "field", "value")
        value = await mock_redis.hget("hash", "field")
        assert value == b"value"

        all_values = await mock_redis.hgetall("hash")
        assert all_values == {b"field": b"value"}

    async def test_expiry_operations(self, mock_redis):
        """Test Redis expiry operations."""
        await mock_redis.set("expiring", "value", ex=10)
        ttl = await mock_redis.ttl("expiring")
        assert 0 < ttl <= 10


@pytest.mark.asyncio
class TestMockVaultFunctionality:
    """Test mock Vault functionality."""

    async def test_secret_operations(self, mock_vault_client):
        """Test Vault secret operations."""
        # Write secret
        await mock_vault_client.write_secret(
            "test/path",
            {"username": "test", "password": "secret"}
        )

        # Read secret
        result = await mock_vault_client.read_secret("test/path")
        assert "data" in result
        secret_data = result["data"]["data"]
        assert secret_data["username"] == "test"
        assert secret_data["password"] == "secret"

        # Delete secret
        deleted = await mock_vault_client.delete_secret("test/path")
        assert deleted is True

    async def test_encryption_operations(self, mock_vault_client):
        """Test Vault encryption operations."""
        plaintext = "sensitive data"

        # Encrypt
        ciphertext = await mock_vault_client.encrypt_data(plaintext)
        assert ciphertext.startswith("vault:v1:")

        # Decrypt
        decrypted = await mock_vault_client.decrypt_data(ciphertext)
        assert decrypted == plaintext


class TestMockOTelFunctionality:
    """Test mock OpenTelemetry functionality."""

    def test_span_operations(self, mock_tracer):
        """Test tracer span operations."""
        span = mock_tracer.start_span("test-operation")

        # Set attributes
        span.set_attribute("user.id", "123")
        assert span.attributes["user.id"] == "123"

        # Add event
        span.add_event("custom-event", {"key": "value"})
        assert len(span.events) == 1
        assert span.events[0]["name"] == "custom-event"

        # End span
        span.end()
        assert span.end_time is not None
        assert not span.is_recording

    def test_span_context_manager(self, mock_tracer):
        """Test tracer as context manager."""
        with mock_tracer.start_as_current_span("test-operation") as span:
            span.set_attribute("test", "value")
            assert mock_tracer.get_current_span() == span

        assert span.end_time is not None
        assert mock_tracer.get_current_span() is None


@pytest.mark.asyncio
class TestMockHTTPFunctionality:
    """Test mock HTTP client functionality."""

    async def test_basic_requests(self, mock_http_session):
        """Test basic HTTP requests."""
        # Add mock response
        from tests.fixtures.mock_http import MockHTTPResponse
        mock_http_session.add_response(
            "https://api.example.com/data",
            MockHTTPResponse(json_data={"result": "success"})
        )

        # Make request
        response = await mock_http_session.get("https://api.example.com/data")
        assert response.status == 200
        data = await response.json()
        assert data["result"] == "success"

        # Check call history
        assert len(mock_http_session.call_history) == 1
        assert mock_http_session.call_history[0]["method"] == "GET"

    async def test_error_responses(self, mock_http_session):
        """Test HTTP error responses."""
        from tests.fixtures.mock_http import MockHTTPResponse, MockHTTPError

        mock_http_session.add_response(
            "https://api.example.com/error",
            MockHTTPResponse(status=500, text="Server Error")
        )

        response = await mock_http_session.get("https://api.example.com/error")
        assert response.status == 500
        assert not response.ok

        with pytest.raises(MockHTTPError):
            response.raise_for_status()


def test_all_fixtures_accessible():
    """Test that all fixtures are accessible."""
    from tests.fixtures import __all__

    # Check that all exported items exist
    assert len(__all__) > 0

    # Verify some key exports
    assert "MockAsyncSession" in __all__
    assert "MockRedis" in __all__
    assert "MockVaultClient" in __all__
    assert "MockTracer" in __all__
    assert "MockHTTPSession" in __all__