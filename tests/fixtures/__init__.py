"""
Mock Fixtures for Testing
Centralized export of all mock fixtures for easy importing in tests.
"""

# Database mocks
from .mock_database import (
    MockAsyncSession,
    MockDatabaseModule,
    MockModel,
    MockQuery,
    MockRepository,
    MockResult,
    MockScalars,
    MockSessionMaker,
    MockTransaction,
    create_mock_entity,
    mock_db_module,
    mock_repository,
    mock_session,
    mock_session_maker,
)

# HTTP mocks
from .mock_http import (
    MockAsyncHTTPClient,
    MockHTTPError,
    MockHTTPResponse,
    MockHTTPSession,
    MockOAuth2Client,
    MockWebSocket,
    mock_async_http_client,
    mock_http_response,
    mock_http_session,
    mock_http_session_with_responses,
    mock_oauth2_client,
    mock_websocket,
)

# OpenTelemetry mocks
from .mock_otel import (
    MockBaggage,
    MockCounter,
    MockGauge,
    MockHistogram,
    MockLogger,
    MockLoggerProvider,
    MockMeter,
    MockMeterProvider,
    MockOTLPExporter,
    MockSpan,
    MockSpanContext,
    MockTracer,
    MockTracerProvider,
    MockUpDownCounter,
    mock_logger,
    mock_meter,
    mock_meter_provider,
    mock_otel_exporter,
    mock_otel_setup,
    mock_tracer,
    mock_tracer_provider,
)

# Redis mocks
from .mock_redis import (
    MockRedis,
    MockRedisLock,
    MockRedisPipeline,
    MockRedisPubSub,
    mock_redis,
    mock_redis_lock,
    mock_redis_pipeline,
    mock_redis_with_data,
)

# Vault mocks
from .mock_vault import (
    MockVaultClient,
    MockVaultProvider,
    MockVaultTransitBackend,
    mock_vault_client,
    mock_vault_provider,
    mock_vault_transit,
    mock_vault_with_secrets,
)

__all__ = [
    # Database
    "MockAsyncSession",
    "MockDatabaseModule",
    "MockModel",
    "MockQuery",
    "MockRepository",
    "MockResult",
    "MockScalars",
    "MockSessionMaker",
    "MockTransaction",
    "create_mock_entity",
    "mock_db_module",
    "mock_repository",
    "mock_session",
    "mock_session_maker",
    # Redis
    "MockRedis",
    "MockRedisLock",
    "MockRedisPipeline",
    "MockRedisPubSub",
    "mock_redis",
    "mock_redis_lock",
    "mock_redis_pipeline",
    "mock_redis_with_data",
    # Vault
    "MockVaultClient",
    "MockVaultProvider",
    "MockVaultTransitBackend",
    "mock_vault_client",
    "mock_vault_provider",
    "mock_vault_transit",
    "mock_vault_with_secrets",
    # OpenTelemetry
    "MockBaggage",
    "MockCounter",
    "MockGauge",
    "MockHistogram",
    "MockLogger",
    "MockLoggerProvider",
    "MockMeter",
    "MockMeterProvider",
    "MockOTLPExporter",
    "MockSpan",
    "MockSpanContext",
    "MockTracer",
    "MockTracerProvider",
    "MockUpDownCounter",
    "mock_logger",
    "mock_meter",
    "mock_meter_provider",
    "mock_otel_exporter",
    "mock_otel_setup",
    "mock_tracer",
    "mock_tracer_provider",
    # HTTP
    "MockAsyncHTTPClient",
    "MockHTTPError",
    "MockHTTPResponse",
    "MockHTTPSession",
    "MockOAuth2Client",
    "MockWebSocket",
    "mock_async_http_client",
    "mock_http_response",
    "mock_http_session",
    "mock_http_session_with_responses",
    "mock_oauth2_client",
    "mock_websocket",
]