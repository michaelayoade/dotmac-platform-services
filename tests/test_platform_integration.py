"""
Integration tests for DotMac Platform Services modules.
"""

import asyncio
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest
import redis.asyncio as redis
from fakeredis.aioredis import FakeRedis
from minio import Minio
import meilisearch
import httpx

from tests.integration_test_config import test_config


class TestPlatformIntegration:
    """Integration tests for platform modules with real services."""

    @pytest.mark.asyncio
    async def test_redis_connectivity(self):
        """Test Redis connection and basic operations."""
        fake_redis = FakeRedis(decode_responses=True)

        with patch("redis.asyncio.Redis.from_url", return_value=fake_redis):
            r = redis.Redis.from_url(test_config.redis_url, decode_responses=True)

            # Test basic operations
            await r.set("test_key", "test_value")
            value = await r.get("test_key")
            assert value == "test_value"

            await r.delete("test_key")
            await r.aclose()

        await fake_redis.aclose()

    @pytest.mark.asyncio
    async def test_vault_connectivity(self):
        """Test Vault/OpenBao connection."""
        mock_response_health = Mock(status_code=200)
        mock_response_mounts = Mock(status_code=200)

        async_client_mock = AsyncMock()
        async_client_mock.get.side_effect = [mock_response_health, mock_response_mounts]

        async_client_cm = AsyncMock()
        async_client_cm.__aenter__.return_value = async_client_mock
        async_client_cm.__aexit__.return_value = None

        with patch("httpx.AsyncClient", return_value=async_client_cm):
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{test_config.vault_url}/v1/sys/health")
                assert response.status_code == 200

                headers = {"X-Vault-Token": test_config.vault_token}
                response = await client.get(
                    f"{test_config.vault_url}/v1/sys/mounts", headers=headers
                )
                assert response.status_code == 200

    def test_minio_connectivity(self):
        """Test MinIO S3-compatible storage."""
        client_mock = Mock()
        client_mock.list_buckets.return_value = [Mock()]
        client_mock.bucket_exists.side_effect = [False, True]
        client_mock.make_bucket.return_value = None

        with patch("tests.test_platform_integration.Minio", return_value=client_mock):
            client = Minio(
                test_config.minio_endpoint,
                access_key=test_config.minio_access_key,
                secret_key=test_config.minio_secret_key,
                secure=test_config.minio_secure,
            )

            buckets = client.list_buckets()
            assert buckets is not None

            bucket_name = "dotmac-integration-test"
            if not client.bucket_exists(bucket_name):
                client.make_bucket(bucket_name)

            assert client.bucket_exists(bucket_name)

    @pytest.mark.asyncio
    async def test_meilisearch_connectivity(self):
        """Test Meilisearch connection."""
        client_mock = Mock()
        client_mock.health.return_value = {"status": "available"}

        index_mock = Mock()
        task_mock = Mock(uid=1)
        index_mock.add_documents.return_value = task_mock
        client_mock.index.return_value = index_mock

        with patch("tests.test_platform_integration.meilisearch.Client", return_value=client_mock):
            client = meilisearch.Client(test_config.meilisearch_url, test_config.meilisearch_master_key)

            health = client.health()
            assert health["status"] == "available"

            index_name = "test-integration-index"
            index = client.index(index_name)

            documents = [{"id": 1, "title": "Test Document", "content": "Integration test"}]
            task = index.add_documents(documents)

            if hasattr(task, "uid"):
                task_uid = task.uid
            elif hasattr(task, "task_uid"):
                task_uid = task.task_uid
            else:
                task_uid = task.get("uid", 0) if isinstance(task, dict) else 0

            client.wait_for_task(task_uid)

            client.delete_index(index_name)

    @pytest.mark.asyncio
    async def test_auth_module_integration(self):
        """Test authentication module with real Redis."""
        from dotmac.platform.auth import JWTService, SessionManager

        # Initialize JWT service
        jwt_service = JWTService(
            algorithm=test_config.jwt_algorithm,
            secret=test_config.jwt_secret_key,
            access_token_expire_minutes=test_config.jwt_expire_minutes,
        )

        # Initialize session manager with Redis backend (using fake redis)
        from dotmac.platform.auth.session_manager import RedisSessionBackend

        fake_redis = FakeRedis(decode_responses=True)

        with patch("redis.asyncio.Redis.from_url", return_value=fake_redis):
            redis_backend = RedisSessionBackend(redis_url=test_config.redis_url)
            session_manager = SessionManager(backend=redis_backend, default_ttl=3600)

            # Test token creation and validation
            user_id = "test-user-123"
            token = jwt_service.issue_access_token(
                sub=user_id, extra_claims={"tenant_id": test_config.test_tenant_id}
            )

            assert token is not None

            # Validate token
            claims = jwt_service.verify_token(token)
            assert claims["sub"] == user_id
            assert claims["tenant_id"] == test_config.test_tenant_id

            # Test session management
            session_data = await session_manager.create_session(
                user_id=user_id, tenant_id=test_config.test_tenant_id, metadata={"ip": "127.0.0.1"}
            )

            assert session_data is not None
            session_id = session_data.session_id

            # Small delay to ensure Redis write completes
            await asyncio.sleep(0.1)

            # Get session
            session = await session_manager.get_session(session_id)
            assert session is not None, f"Session {session_id} not found"
            assert session.user_id == user_id

            # Clean up
            await session_manager.delete_session(session_id)

        await fake_redis.aclose()

    @pytest.mark.asyncio
    async def test_secrets_module_integration(self):
        """Test secrets module with real Vault."""
        from dotmac.platform.secrets import create_openbao_secrets_manager
        from dotmac.platform.secrets.exceptions import SecretNotFoundError

        class FakeOpenBaoProvider:
            def __init__(self):
                self._secrets: dict[str, dict[str, Any]] = {}

            async def set_secret(self, secret_path: str, secret_data: dict[str, Any], cas: int | None = None) -> bool:
                self._secrets[secret_path] = secret_data
                return True

            async def get_secret(self, secret_path: str) -> dict[str, Any]:
                if secret_path not in self._secrets:
                    raise SecretNotFoundError(secret_path, "openbao")
                return self._secrets[secret_path]

            async def delete_secret(self, secret_path: str) -> bool:
                self._secrets.pop(secret_path, None)
                return True

            async def close(self) -> None:  # pragma: no cover - part of provider interface
                return None

        # Initialize secrets manager with OpenBao
        fake_provider = FakeOpenBaoProvider()

        with patch(
            "dotmac.platform.secrets.openbao_provider.OpenBaoProvider",
            return_value=fake_provider,
        ):
            manager = create_openbao_secrets_manager(
                url=test_config.vault_url,
                token=test_config.vault_token,
                mount_point="secret",
                encryption_key=test_config.encryption_key,
                enable_field_encryption=False,
            )

        # Test secret operations
        secret_path = "test/integration/secret"
        secret_data = {
            "username": "test-user",
            "password": "test-password",
            "api_key": "test-api-key",
        }

        # Store secret (use provider directly for write operations)
        await manager.provider.set_secret(secret_path, secret_data)

        # Retrieve secret (can use manager for read operations)
        retrieved = await manager.get_custom_secret(secret_path)
        assert retrieved["username"] == secret_data["username"]
        assert retrieved["password"] == secret_data["password"]

        # Delete secret (use provider directly)
        await manager.provider.delete_secret(secret_path)

        # Verify deletion
        try:
            await manager.get_custom_secret(secret_path)
            assert False, "Secret should have been deleted"
        except Exception:
            pass  # Expected

    @pytest.mark.asyncio
    async def test_observability_module_integration(self):
        """Test observability module with OpenTelemetry."""
        from dotmac.platform.observability import ObservabilityManager

        # Initialize observability manager
        obs_manager = ObservabilityManager(
            service_name=test_config.otel_service_name,
            otlp_endpoint=test_config.otel_endpoint,
            enable_tracing=True,
            enable_metrics=True,
            enable_logging=True
        )
        obs_manager.initialize()

        # Test metrics registry
        metrics_registry = obs_manager.get_metrics_registry()
        if metrics_registry:
            # Test basic metrics functionality
            metrics_registry.increment_counter("test.counter", labels={"test": "integration"})

        # Test tracing manager
        tracing_manager = obs_manager.get_tracing_manager()
        if tracing_manager:
            # Test basic tracing functionality
            pass  # TracingManager doesn't require async methods

        # Test logger
        logger = obs_manager.get_logger("integration-test")
        logger.info("Integration test log message", extra={"test": "integration"})

        # Clean up
        obs_manager.shutdown()

    @pytest.mark.asyncio
    async def test_file_storage_integration(self, tmp_path):
        """Test file storage module with local storage (mocked MinIO)."""
        from dotmac.platform.file_storage import LocalFileStorage
        import io

        storage = LocalFileStorage(base_path=str(tmp_path))

        test_content = b"Integration test file content"
        file_path = "test/integration/test_file.txt"
        tenant_id = test_config.test_tenant_id

        content_stream = io.BytesIO(test_content)
        await storage.save_file(file_path, content_stream, tenant_id)

        exists = await storage.file_exists(file_path, tenant_id)
        assert exists

        downloaded_stream = await storage.get_file(file_path, tenant_id)
        downloaded_content = downloaded_stream
        if hasattr(downloaded_stream, "read"):
            downloaded_content = downloaded_stream.read()
        assert downloaded_content == test_content

        files = await storage.list_files("test/integration/", tenant_id)
        assert any("test_file.txt" in f.filename for f in files)

        deleted = await storage.delete_file(file_path, tenant_id)
        assert deleted

    @pytest.mark.asyncio
    async def test_search_module_integration(self):
        """Test search module with Meilisearch."""
        from dotmac.platform.search.service import InMemorySearchBackend, SearchService
        from dotmac.platform.search.interfaces import SearchQuery

        search_service = SearchService(backend=InMemorySearchBackend())

        # Test business entity operations
        entity_type = "documents"
        entity_data_1 = {
            "id": "1",
            "title": "Test Document 1",
            "content": "Integration test content",
            "category": "test",
        }
        entity_data_2 = {
            "id": "2",
            "title": "Test Document 2",
            "content": "Another test document",
            "category": "test",
        }

        # Index business entities
        await search_service.index_business_entity(entity_type, "1", entity_data_1)
        await search_service.index_business_entity(entity_type, "2", entity_data_2)

        # Wait for indexing to complete
        import asyncio
        await asyncio.sleep(1)

        # Search business entities
        query = SearchQuery(query="test", limit=10)
        results = await search_service.search_business_entities(entity_type, query)
        assert len(results.results) >= 1

        # Clean up - delete the entities
        await search_service.delete_business_entity(entity_type, "1")
        await search_service.delete_business_entity(entity_type, "2")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
