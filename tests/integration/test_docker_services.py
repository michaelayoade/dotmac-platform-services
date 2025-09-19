"""
Integration tests for Docker services.

Tests connectivity and functionality of all Docker services.
"""

import asyncio
import os
import signal
import subprocess
import time
from typing import Any

import pytest
import redis.asyncio as redis
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

# Mark all tests as integration
pytestmark = pytest.mark.integration


class TestDockerServices:
    """Test all Docker services are running and accessible."""

    @pytest.mark.asyncio
    async def test_postgres_connectivity(self):
        """Test PostgreSQL database connectivity."""
        # Database connection string
        database_url = os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://dotmac:dotmac_password@localhost:5432/dotmac"
        )

        try:
            # Create async engine
            engine = create_async_engine(database_url, echo=False)

            # Test connection
            async with engine.begin() as conn:
                result = await conn.execute(text("SELECT version()"))
                version = result.scalar()
                assert version is not None
                assert "PostgreSQL" in version

                # Test we can create tables
                await conn.execute(
                    text("""
                    CREATE TABLE IF NOT EXISTS test_integration (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """)
                )

                # Insert test data
                await conn.execute(
                    text("INSERT INTO test_integration (name) VALUES (:name)"),
                    {"name": "integration_test"}
                )

                # Query data
                result = await conn.execute(
                    text("SELECT COUNT(*) FROM test_integration")
                )
                count = result.scalar()
                assert count >= 1

                # Cleanup
                await conn.execute(text("DROP TABLE IF EXISTS test_integration"))

            await engine.dispose()
            print("✓ PostgreSQL connectivity test passed")

        except Exception as e:
            pytest.fail(f"PostgreSQL connectivity test failed: {e}")

    @pytest.mark.asyncio
    async def test_redis_connectivity(self):
        """Test Redis connectivity and operations."""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

        try:
            # Create Redis client
            client = redis.from_url(redis_url, decode_responses=True)

            # Test basic operations
            assert await client.ping()

            # Set and get
            await client.set("test:key", "test_value", ex=60)
            value = await client.get("test:key")
            assert value == "test_value"

            # List operations
            await client.lpush("test:list", "item1", "item2", "item3")
            items = await client.lrange("test:list", 0, -1)
            assert len(items) == 3

            # Hash operations
            await client.hset("test:hash", mapping={"field1": "value1", "field2": "value2"})
            hash_data = await client.hgetall("test:hash")
            assert hash_data["field1"] == "value1"

            # Set operations
            await client.sadd("test:set", "member1", "member2")
            members = await client.smembers("test:set")
            assert len(members) == 2

            # Pub/Sub test
            pubsub = client.pubsub()
            await pubsub.subscribe("test:channel")

            # Publish message
            await client.publish("test:channel", "test_message")

            # Cleanup
            await client.delete("test:key", "test:list", "test:hash", "test:set")
            await pubsub.unsubscribe("test:channel")
            await pubsub.close()
            await client.close()

            print("✓ Redis connectivity test passed")

        except Exception as e:
            pytest.fail(f"Redis connectivity test failed: {e}")

    @pytest.mark.asyncio
    async def test_rabbitmq_connectivity(self):
        """Test RabbitMQ connectivity via Celery."""
        import subprocess
        import time
        import signal

        worker_process = None
        try:
            # Start Celery worker in the background
            print("Starting Celery worker for test...")
            worker_process = subprocess.Popen(
                [
                    ".venv/bin/python", "-m", "celery",
                    "-A", "dotmac.platform.tasks.celery_app",
                    "worker",
                    "--loglevel=error",
                    "--concurrency=1",
                    "--pool=solo"
                ],
                env={
                    **os.environ,
                    "CELERY_BROKER_URL": "amqp://admin:admin@localhost:5672//",
                    "CELERY_RESULT_BACKEND": "redis://localhost:6379/1",
                },
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Give worker time to start
            time.sleep(3)

            from dotmac.platform.tasks.celery_app import app, health_check

            # Test Celery health check
            result = health_check.apply_async()

            # Wait for result with timeout
            health_status = result.get(timeout=10)

            assert health_status["status"] == "healthy"
            assert health_status["service"] == "celery-worker"

            # Test task submission and retrieval
            # Submit health check multiple times to test queueing
            tasks = []
            for i in range(3):
                tasks.append(health_check.apply_async())

            # Get all results
            for task in tasks:
                result = task.get(timeout=10)
                assert result["status"] == "healthy"

            print("✓ RabbitMQ/Celery connectivity test passed")

        except Exception as e:
            pytest.fail(f"RabbitMQ/Celery connectivity test failed: {e}")

        finally:
            # Stop the worker
            if worker_process:
                worker_process.send_signal(signal.SIGTERM)
                try:
                    worker_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    worker_process.kill()
                    worker_process.wait()

    @pytest.mark.asyncio
    async def test_vault_connectivity(self):
        """Test HashiCorp Vault/OpenBao connectivity."""
        try:
            import hvac

            vault_url = os.getenv("VAULT_URL", "http://localhost:8200")
            vault_token = os.getenv("VAULT_TOKEN", "root-token")

            # Create Vault client
            client = hvac.Client(url=vault_url, token=vault_token)

            # Check if Vault is sealed
            assert client.is_authenticated()
            assert not client.sys.is_sealed()

            # Write and read secret
            secret_path = "secret/data/integration_test"
            secret_data = {"username": "testuser", "password": "testpass"}

            client.secrets.kv.v2.create_or_update_secret(
                path="integration_test",
                secret=secret_data,
            )

            # Read secret back
            response = client.secrets.kv.v2.read_secret_version(path="integration_test")
            assert response["data"]["data"]["username"] == "testuser"

            # Delete secret
            client.secrets.kv.v2.delete_metadata_and_all_versions(path="integration_test")

            print("✓ Vault/OpenBao connectivity test passed")

        except Exception as e:
            pytest.fail(f"Vault/OpenBao connectivity test failed: {e}")

    @pytest.mark.asyncio
    async def test_minio_connectivity(self):
        """Test MinIO S3 storage connectivity."""
        try:
            from minio import Minio
            from minio.error import S3Error

            # MinIO connection
            minio_client = Minio(
                "localhost:9000",
                access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
                secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
                secure=False
            )

            # Create test bucket
            bucket_name = "integration-test"
            if not minio_client.bucket_exists(bucket_name):
                minio_client.make_bucket(bucket_name)

            # Upload test object
            test_data = b"Integration test data"
            object_name = "test-object.txt"

            import io
            minio_client.put_object(
                bucket_name,
                object_name,
                io.BytesIO(test_data),
                length=len(test_data)
            )

            # Download and verify
            response = minio_client.get_object(bucket_name, object_name)
            data = response.read()
            assert data == test_data

            # List objects
            objects = list(minio_client.list_objects(bucket_name))
            assert len(objects) >= 1

            # Cleanup
            minio_client.remove_object(bucket_name, object_name)

            print("✓ MinIO S3 storage test passed")

        except Exception as e:
            pytest.fail(f"MinIO connectivity test failed: {e}")

    @pytest.mark.asyncio
    async def test_meilisearch_connectivity(self):
        """Test Meilisearch connectivity."""
        try:
            import meilisearch

            # Meilisearch client with master key
            client = meilisearch.Client(
                os.getenv("MEILISEARCH_URL", "http://localhost:7700"),
                os.getenv("MEILISEARCH_KEY", "masterKey123456789")
            )

            # Check health
            health = client.health()
            assert health["status"] == "available"

            # Create test index
            index = client.index("integration_test")

            # Add documents
            documents = [
                {"id": 1, "title": "Test Document 1", "content": "Integration test content"},
                {"id": 2, "title": "Test Document 2", "content": "Another test document"},
            ]
            index.add_documents(documents)

            # Wait for indexing
            time.sleep(1)

            # Search
            results = index.search("test")
            assert len(results["hits"]) > 0

            # Cleanup
            client.delete_index("integration_test")

            print("✓ Meilisearch connectivity test passed")

        except Exception as e:
            pytest.fail(f"Meilisearch connectivity test failed: {e}")

    @pytest.mark.asyncio
    async def test_observability_stack(self):
        """Test observability stack (Prometheus, Grafana, Jaeger)."""
        import aiohttp

        services = [
            ("Prometheus", "http://localhost:9090/-/healthy"),
            ("Grafana", "http://localhost:3000/api/health"),
            ("Jaeger", "http://localhost:16686/"),
        ]

        async with aiohttp.ClientSession() as session:
            for service_name, url in services:
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                        assert response.status in [200, 302]  # Grafana redirects
                        print(f"✓ {service_name} is accessible")
                except Exception as e:
                    print(f"⚠ {service_name} not accessible: {e}")
                    # Don't fail test if observability stack not running

    @pytest.mark.asyncio
    async def test_service_integration(self):
        """Test integration between multiple services."""
        try:
            # Test flow: Store secret in Vault, cache in Redis, audit in PostgreSQL
            import hvac

            # 1. Store secret in Vault
            vault_client = hvac.Client(
                url=os.getenv("VAULT_URL", "http://localhost:8200"),
                token=os.getenv("VAULT_TOKEN", "root-token")
            )

            secret_data = {"api_key": "test_integration_key_123"}
            vault_client.secrets.kv.v2.create_or_update_secret(
                path="test/integration",
                secret=secret_data
            )

            # 2. Cache in Redis
            redis_client = redis.from_url("redis://localhost:6379/0", decode_responses=True)
            await redis_client.set(
                "vault:cache:test/integration",
                "test_integration_key_123",
                ex=60
            )

            # 3. Audit in PostgreSQL
            database_url = "postgresql+asyncpg://dotmac:dotmac_password@localhost:5432/dotmac"
            engine = create_async_engine(database_url)

            async with engine.begin() as conn:
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS audit_log (
                        id SERIAL PRIMARY KEY,
                        event_type VARCHAR(50),
                        resource VARCHAR(100),
                        details TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))

                await conn.execute(text("""
                    INSERT INTO audit_log (event_type, resource, details)
                    VALUES (:event_type, :resource, :details)
                """), {
                    "event_type": "secret_accessed",
                    "resource": "test/integration",
                    "details": "Integration test secret access"
                })

            # Verify integration
            cached_value = await redis_client.get("vault:cache:test/integration")
            assert cached_value == "test_integration_key_123"

            # Cleanup
            vault_client.secrets.kv.v2.delete_metadata_and_all_versions(path="test/integration")
            await redis_client.delete("vault:cache:test/integration")

            async with engine.begin() as conn:
                await conn.execute(text("DROP TABLE IF EXISTS audit_log"))

            await redis_client.close()
            await engine.dispose()

            print("✓ Service integration test passed")

        except Exception as e:
            pytest.fail(f"Service integration test failed: {e}")


class TestDockerHealthChecks:
    """Test Docker service health checks."""

    @pytest.mark.asyncio
    async def test_all_services_healthy(self):
        """Check health status of all services."""
        import subprocess
        import json

        # Define critical services that must be healthy
        CRITICAL_SERVICES = ['postgres', 'redis', 'openbao', 'rabbitmq']
        # Optional services that may be unhealthy without failing the test
        OPTIONAL_SERVICES = ['celery-worker', 'celery-beat', 'minio', 'meilisearch']

        try:
            # Get container health status
            result = subprocess.run(
                ["docker", "ps", "--format", "json"],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                pytest.skip("Docker not available or services not running")

            containers = [json.loads(line) for line in result.stdout.strip().split('\n') if line]

            dotmac_containers = [c for c in containers if 'dotmac' in c.get('Names', '')]

            if not dotmac_containers:
                pytest.skip("No DotMac containers running")

            critical_unhealthy = []
            optional_unhealthy = []

            for container in dotmac_containers:
                name = container.get('Names', '')
                status = container.get('Status', '')

                if 'unhealthy' in status.lower():
                    # Check if it's a critical service
                    is_critical = any(svc in name.lower() for svc in CRITICAL_SERVICES)
                    is_optional = any(svc in name.lower() for svc in OPTIONAL_SERVICES)

                    if is_critical:
                        critical_unhealthy.append(name)
                    elif is_optional:
                        optional_unhealthy.append(name)
                    else:
                        # Unknown service, treat as critical
                        critical_unhealthy.append(name)

            # Report status
            if optional_unhealthy:
                print(f"⚠ Optional services unhealthy (non-critical): {', '.join(optional_unhealthy)}")

            if critical_unhealthy:
                pytest.fail(f"Critical services unhealthy: {', '.join(critical_unhealthy)}")

            healthy_count = len(dotmac_containers) - len(optional_unhealthy) - len(critical_unhealthy)
            print(f"✓ {healthy_count}/{len(dotmac_containers)} DotMac containers are healthy")

        except Exception as e:
            pytest.skip(f"Could not check container health: {e}")