"""
Integration test configuration for DotMac Platform Services.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class IntegrationTestConfig:
    """Configuration for integration tests with Docker services."""

    # Database
    postgres_url: str = "postgresql+asyncpg://dotmac:dotmac_password@localhost:5432/dotmac"
    postgres_sync_url: str = "postgresql://dotmac:dotmac_password@localhost:5432/dotmac"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Vault/OpenBao
    vault_url: str = "http://localhost:8200"
    vault_token: str = "root-token"

    # RabbitMQ
    rabbitmq_url: str = "amqp://admin:admin@localhost:5672//"

    # MinIO (S3 compatible)
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False
    minio_bucket: str = "dotmac-test"

    # Meilisearch
    meilisearch_url: str = "http://localhost:7700"
    meilisearch_master_key: str = "masterKey123456789"

    # OpenTelemetry
    otel_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "dotmac-integration-tests"

    # JWT Settings for auth tests
    jwt_secret_key: str = "test-secret-key-for-integration-tests"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30

    # Test tenant ID
    test_tenant_id: str = "test-tenant-001"

    # Encryption key for secrets
    encryption_key: str = "test-encryption-key-32-char-long-key"

    @classmethod
    def from_env(cls) -> "IntegrationTestConfig":
        """Load configuration from environment variables."""
        return cls(
            postgres_url=os.getenv("DATABASE_URL", cls.postgres_url),
            redis_url=os.getenv("REDIS_URL", cls.redis_url),
            vault_url=os.getenv("VAULT_URL", cls.vault_url),
            vault_token=os.getenv("VAULT_TOKEN", cls.vault_token),
            minio_endpoint=os.getenv("MINIO_ENDPOINT", cls.minio_endpoint),
            minio_access_key=os.getenv("MINIO_ACCESS_KEY", cls.minio_access_key),
            minio_secret_key=os.getenv("MINIO_SECRET_KEY", cls.minio_secret_key),
            meilisearch_url=os.getenv("MEILISEARCH_URL", cls.meilisearch_url),
            meilisearch_master_key=os.getenv("MEILISEARCH_MASTER_KEY", cls.meilisearch_master_key),
        )


# Global instance
test_config = IntegrationTestConfig()
