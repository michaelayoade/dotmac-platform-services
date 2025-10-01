#!/bin/bash

# Export environment variables for OpenBao and other services
export DOTMAC_SECRETS_BACKEND=openbao
export DOTMAC_VAULT_URL=http://localhost:8200
export DOTMAC_VAULT_TOKEN=root
export DOTMAC_VAULT_VERIFY_SSL=false
export DOTMAC_CACHE_BACKEND=redis
export DOTMAC_REDIS_URL=redis://localhost:6379

# Database configuration
export DATABASE_URL=postgresql://dotmac:dotmac@localhost:5432/dotmac_test
export TEST_DATABASE_URL=postgresql://dotmac:dotmac@localhost:5432/dotmac_test

# Service URLs
export REDIS_URL=redis://localhost:6379
export REDIS_HOST=localhost
export REDIS_PORT=6379

# MinIO/S3 configuration
export MINIO_ENDPOINT=localhost:9000
export MINIO_ACCESS_KEY=minioadmin
export MINIO_SECRET_KEY=minioadmin
export S3_ENDPOINT_URL=http://localhost:9000
export AWS_ACCESS_KEY_ID=minioadmin
export AWS_SECRET_ACCESS_KEY=minioadmin

# Meilisearch configuration
export MEILISEARCH_URL=http://localhost:7700
export MEILISEARCH_API_KEY=masterKey

# RabbitMQ/Celery configuration
export RABBITMQ_URL=amqp://guest:guest@localhost:5672/
export CELERY_BROKER_URL=amqp://guest:guest@localhost:5672/
export CELERY_RESULT_BACKEND=redis://localhost:6379/1

# OpenTelemetry configuration
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
export OTEL_EXPORTER_OTLP_INSECURE=true

# JWT Configuration
export JWT_SECRET_KEY=test-secret-key-for-testing-only
export JWT_ALGORITHM=HS256

# General test configuration
export TESTING=true
export ENVIRONMENT=test
export LOG_LEVEL=INFO
export DEBUG=false

# Run tests with specific ignores
poetry run pytest tests/ \
    --ignore=tests/test_observability.py \
    --ignore=tests/test_real_services.py \
    --ignore=tests/auth/test_mfa_service.py \
    -x \
    --tb=short \
    -v \
    "$@"