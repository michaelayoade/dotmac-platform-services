"""
Tests for fixed NotImplementedError features.

This test module validates:
- DLQ listing operations
- SecureFileStorage methods
- Service mesh health monitoring
- WebSocket API key authentication
"""

import asyncio
import hashlib
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# DLQ Tests
@pytest.mark.asyncio
async def test_dlq_list_entries():
    """Test DLQ listing operations."""
    from dotmac.platform.communications.events.dlq import SimpleDLQ, DLQEntry
    from dotmac.platform.communications.events.message import Event
    from dotmac.platform.communications.events.bus import EventBus

    # Create mock event bus
    bus = MagicMock(spec=EventBus)
    events_collected = []

    async def mock_subscribe(topic, handler, subscription_id):
        # Simulate collecting some DLQ events
        for i in range(3):
            event = Event(
                topic=topic,
                payload={"index": i},
                headers={
                    "dlq_original_topic": "test-topic",
                    "dlq_error": f"Error {i}",
                    "dlq_error_type": "TestError",
                    "dlq_retry_count": str(i),
                    "dlq_first_failure_time": datetime.utcnow().isoformat(),
                    "dlq_last_failure_time": datetime.utcnow().isoformat(),
                },
                metadata={"timestamp": datetime.utcnow()}
            )
            await handler(event)
        return True

    bus.subscribe = AsyncMock(side_effect=mock_subscribe)
    bus.unsubscribe = AsyncMock(return_value=True)

    # Create DLQ instance
    dlq = SimpleDLQ(bus)

    # List entries
    entries = await dlq.list_dlq_entries("dlq.test-topic", limit=10)

    # Verify results
    assert len(entries) == 3
    assert all(isinstance(entry, DLQEntry) for entry in entries)
    assert bus.subscribe.called
    assert bus.unsubscribe.called


# SecureFileStorage Tests
@pytest.mark.asyncio
async def test_secure_file_storage_store_and_retrieve():
    """Test SecureFileStorage store and retrieve operations."""
    from dotmac.platform.file_storage.backends import SecureFileStorage

    # Create temp directory
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = SecureFileStorage(
            base_path=tmpdir,
            max_file_size=1024 * 1024,  # 1MB
            allowed_extensions=["txt", "json"],
            scan_for_malware=False
        )

        # Store a file
        content = b"Test file content"
        result = await storage.store_file("test.txt", content)

        assert result["path"] == "test.txt"
        assert result["size"] == len(content)
        assert "checksum" in result
        assert result["checksum"] == hashlib.sha256(content).hexdigest()

        # Retrieve the file
        retrieved = await storage.get_file("test.txt")
        assert retrieved == content

        # Delete the file
        deleted = await storage.delete_file("test.txt")
        assert deleted is True

        # Try to retrieve deleted file
        with pytest.raises(FileNotFoundError):
            await storage.get_file("test.txt")


@pytest.mark.asyncio
async def test_secure_file_storage_validation():
    """Test SecureFileStorage validation features."""
    from dotmac.platform.file_storage.backends import SecureFileStorage

    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = SecureFileStorage(
            base_path=tmpdir,
            max_file_size=100,  # Small limit for testing
            allowed_extensions=["txt"],
            scan_for_malware=False
        )

        # Test size validation
        large_content = b"x" * 200
        with pytest.raises(ValueError, match="exceeds maximum allowed size"):
            await storage.store_file("large.txt", large_content)

        # Test extension validation
        with pytest.raises(ValueError, match="extension.*not allowed"):
            await storage.store_file("test.exe", b"content")

        # Test path traversal prevention
        with pytest.raises(ValueError, match="potential path traversal"):
            await storage.store_file("../etc/passwd", b"content")

        # Valid file should work
        result = await storage.store_file("valid.txt", b"small content")
        assert result["path"] == "valid.txt"


# Service Mesh Health Monitoring Tests
@pytest.mark.asyncio
async def test_service_mesh_health_monitoring():
    """Test service mesh health monitoring functionality."""
    from dotmac.platform.resilience.service_mesh import (
        ServiceMesh,
        ServiceRegistry,
        ServiceEndpoint,
        ServiceStatus,
        LoadBalancer,
        ServiceMarketplace  # Now available as a stub in service_mesh
    )
    from sqlalchemy.ext.asyncio import AsyncSession

    # Create mocks
    db_session = MagicMock(spec=AsyncSession)
    marketplace = MagicMock(spec=ServiceMarketplace)
    marketplace.discover_service = AsyncMock(return_value=[])

    # Create service mesh
    mesh = ServiceMesh(
        db_session=db_session,
        tenant_id="test-tenant",
        marketplace=marketplace
    )

    # Initialize (which starts health monitoring)
    await mesh.initialize()

    # Register a test endpoint
    endpoint = ServiceEndpoint(
        service_name="test-service",
        host="localhost",
        port=8080,
        path="/api",
        protocol="http",
        weight=100,
        health_check_path="/health"
    )
    mesh.register_service_endpoint(endpoint)

    # Mock health check response
    with patch.object(mesh, '_check_endpoint_health') as mock_check:
        mock_check.return_value = True

        # Trigger health check
        await mesh._check_all_endpoints_health()

        # Verify health check was called
        mock_check.assert_called_once()

    # Get health status
    status = mesh.get_health_status()
    assert "total_endpoints" in status
    assert "healthy_endpoints" in status
    assert "health_percentage" in status

    # Cleanup
    await mesh.shutdown()


@pytest.mark.asyncio
async def test_service_mesh_health_status_tracking():
    """Test that service mesh tracks health status correctly."""
    from dotmac.platform.resilience.service_mesh import (
        ServiceRegistry,
        ServiceEndpoint,
        LoadBalancer
    )

    # Create registry and load balancer
    registry = ServiceRegistry()

    # Create test endpoint
    endpoint = ServiceEndpoint(
        service_name="test-service",
        host="localhost",
        port=8080,
        path="/api",
        weight=100
    )

    # Register endpoint
    registry.register_endpoint(endpoint)

    # Update health status
    endpoint_key = f"{endpoint.host}:{endpoint.port}"
    registry.health_status[endpoint_key] = {
        'healthy': True,
        'last_check': time.time(),
        'status_code': 200,
        'response_time_ms': 50,
        'endpoint': endpoint.service_name
    }

    # Verify health is tracked
    assert endpoint_key in registry.health_status
    assert registry.health_status[endpoint_key]['healthy'] is True

    # Create load balancer and test healthy check
    lb = LoadBalancer(registry)

    # The _is_healthy method is async in our implementation
    # We need to test it properly
    async def test_health():
        result = await lb._is_healthy(endpoint)
        return result

    # Since we cached healthy status, it should return True
    # (within 30 second cache window)
    is_healthy = await test_health()
    assert is_healthy is True


# WebSocket API Key Authentication Tests
@pytest.mark.asyncio
async def test_websocket_api_key_authentication():
    """Test WebSocket API key authentication."""
    from dotmac.platform.communications.websockets.auth.manager import AuthManager
    from dotmac.platform.communications.websockets.auth.types import AuthResult

    # Create mock config
    config = MagicMock()
    config.enabled = True
    config.require_token = True
    config.jwt_secret_key = "test-secret"
    config.jwt_algorithm = "HS256"
    config.default_tenant_id = "test-tenant"
    config.user_cache_ttl_seconds = 300
    config.api_keys = [
        {
            "key": "test-api-key-123",
            "user_id": "api-user-1",
            "username": "API User 1",
            "tenant_id": "tenant-1",
            "roles": ["api_user"],
            "permissions": ["read", "write"]
        },
        "simple-api-key-456"  # Simple string key
    ]

    # Create auth manager
    auth_manager = AuthManager(config)

    # Test valid API key (dict config)
    result = await auth_manager.authenticate_api_key("test-api-key-123")
    assert result.is_authenticated is True
    assert result.user_info.user_id == "api-user-1"
    assert result.user_info.username == "API User 1"
    assert result.user_info.tenant_id == "tenant-1"
    assert "read" in result.user_info.permissions
    assert "write" in result.user_info.permissions

    # Test valid API key (simple string)
    result = await auth_manager.authenticate_api_key("simple-api-key-456")
    assert result.is_authenticated is True
    assert result.user_info.user_id.startswith("api-")
    assert result.user_info.tenant_id == "test-tenant"

    # Test invalid API key
    result = await auth_manager.authenticate_api_key("invalid-key")
    assert result.is_authenticated is False
    assert result.error is not None  # Check error exists instead of reason

    # Test caching - second call should be cached
    result2 = await auth_manager.authenticate_api_key("test-api-key-123")
    assert result2.is_authenticated is True
    # Cache key should exist
    assert f"api:test-api-key-123" in auth_manager._token_cache


@pytest.mark.asyncio
async def test_websocket_auth_with_api_key():
    """Test WebSocket authentication flow with API key."""
    from dotmac.platform.communications.websockets.auth.manager import AuthManager

    # Create mock config
    config = MagicMock()
    config.enabled = True
    config.require_token = False  # Allow both token and API key
    config.jwt_secret_key = "test-secret"
    config.jwt_algorithm = "HS256"
    config.default_tenant_id = "default"
    config.user_cache_ttl_seconds = 300
    config.token_header = "Authorization"
    config.token_query_param = "token"
    config.api_keys = ["valid-api-key"]

    # Create auth manager
    auth_manager = AuthManager(config)

    # Mock WebSocket with API key in headers
    websocket = MagicMock()
    websocket.request_headers = MagicMock()
    websocket.request_headers.raw = [
        ("X-API-Key", "valid-api-key"),
        ("Host", "example.com")
    ]
    websocket.path = "/ws"

    # Validate WebSocket auth
    result = await auth_manager.validate_websocket_auth(websocket, "/ws")

    assert result.is_authenticated is True
    assert result.user_info.user_id.startswith("api-")
    assert result.auth_method == "api_key"

    # Test with API key in query params
    websocket2 = MagicMock()
    websocket2.request_headers = MagicMock()
    websocket2.request_headers.raw = []
    websocket2.path = "/ws?api_key=valid-api-key"

    result2 = await auth_manager.validate_websocket_auth(websocket2, websocket2.path)
    assert result2.is_authenticated is True
    assert result2.auth_method == "api_key"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])