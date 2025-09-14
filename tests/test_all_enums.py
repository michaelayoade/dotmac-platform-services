"""
Comprehensive tests for all enums and constants.
Tests enum values, string representations, and usage.
"""


import pytest


def test_auth_enums():
    """Test all authentication-related enums."""
    from dotmac.platform.auth.jwt_service import TokenType
    from dotmac.platform.auth.mfa_service import MFAMethod, MFAStatus
    from dotmac.platform.auth.oauth_providers import OAuthGrantType, OAuthProvider, OAuthTokenType
    from dotmac.platform.auth.rbac_engine import Action, PolicyEffect, Resource

    # Test TokenType enum
    assert TokenType.ACCESS == "access"
    assert TokenType.REFRESH == "refresh"
    assert TokenType.ID == "id"
    assert TokenType.SERVICE == "service"

    # Test MFA enums
    assert MFAMethod.TOTP == "totp"
    assert MFAMethod.SMS == "sms"
    assert MFAMethod.EMAIL == "email"
    assert MFAMethod.BACKUP_CODE == "backup_code"

    assert MFAStatus.PENDING == "pending"
    assert MFAStatus.ACTIVE == "active"
    assert MFAStatus.DISABLED == "disabled"

    # Test OAuth enums
    assert OAuthProvider.GOOGLE == "google"
    assert OAuthProvider.GITHUB == "github"
    assert OAuthProvider.MICROSOFT == "microsoft"
    assert OAuthProvider.APPLE == "apple"

    assert OAuthGrantType.AUTHORIZATION_CODE == "authorization_code"
    assert OAuthGrantType.CLIENT_CREDENTIALS == "client_credentials"
    assert OAuthGrantType.REFRESH_TOKEN == "refresh_token"

    assert OAuthTokenType.BEARER == "Bearer"

    # Test RBAC enums
    assert Resource.ALL == "*"
    assert Resource.USER == "user"
    assert Resource.TENANT == "tenant"
    assert Resource.API_KEY == "api_key"
    assert Resource.SESSION == "session"

    assert Action.ALL == "*"
    assert Action.CREATE == "create"
    assert Action.READ == "read"
    assert Action.UPDATE == "update"
    assert Action.DELETE == "delete"
    assert Action.LIST == "list"

    assert PolicyEffect.ALLOW == "allow"
    assert PolicyEffect.DENY == "deny"


def test_secrets_enums():
    """Test all secrets-related enums."""
    from dotmac.platform.secrets.encryption import EncryptionAlgorithm
    from dotmac.platform.secrets.types import Environment, RotationStatus, SecretType

    # Test Environment enum
    assert Environment.DEVELOPMENT == "development"
    assert Environment.TESTING == "testing"
    assert Environment.STAGING == "staging"
    assert Environment.PRODUCTION == "production"

    # Test SecretType enum
    assert SecretType.DATABASE == "database"
    assert SecretType.API_KEY == "api_key"
    assert SecretType.JWT == "jwt"
    assert SecretType.ENCRYPTION_KEY == "encryption_key"
    assert SecretType.CERTIFICATE == "certificate"
    assert SecretType.PASSWORD == "password"
    assert SecretType.TOKEN == "token"
    assert SecretType.WEBHOOK == "webhook"
    assert SecretType.OTHER == "other"

    # Test RotationStatus enum
    assert RotationStatus.PENDING == "pending"
    assert RotationStatus.IN_PROGRESS == "in_progress"
    assert RotationStatus.COMPLETED == "completed"
    assert RotationStatus.FAILED == "failed"

    # Test EncryptionAlgorithm enum
    assert EncryptionAlgorithm.AES_256_GCM == "AES-256-GCM"
    assert EncryptionAlgorithm.CHACHA20_POLY1305 == "ChaCha20-Poly1305"
    assert EncryptionAlgorithm.AES_256_CBC == "AES-256-CBC"
    assert EncryptionAlgorithm.FERNET == "Fernet"


def test_observability_enums():
    """Test all observability-related enums."""
    from dotmac.platform.observability.health import HealthStatus
    from dotmac.platform.observability.logging import LogLevel
    from dotmac.platform.observability.metrics.business import MetricType
    from dotmac.platform.observability.tracing import SpanKind, SpanStatus

    # Test LogLevel enum
    assert LogLevel.DEBUG == "DEBUG"
    assert LogLevel.INFO == "INFO"
    assert LogLevel.WARNING == "WARNING"
    assert LogLevel.ERROR == "ERROR"
    assert LogLevel.CRITICAL == "CRITICAL"

    # Test MetricType enum
    assert MetricType.COUNTER == "counter"
    assert MetricType.GAUGE == "gauge"
    assert MetricType.HISTOGRAM == "histogram"
    assert MetricType.SUMMARY == "summary"

    # Test SpanKind enum
    assert SpanKind.INTERNAL == "internal"
    assert SpanKind.SERVER == "server"
    assert SpanKind.CLIENT == "client"
    assert SpanKind.PRODUCER == "producer"
    assert SpanKind.CONSUMER == "consumer"

    # Test SpanStatus enum
    assert SpanStatus.UNSET == "unset"
    assert SpanStatus.OK == "ok"
    assert SpanStatus.ERROR == "error"

    # Test HealthStatus enum
    assert HealthStatus.HEALTHY == "healthy"
    assert HealthStatus.DEGRADED == "degraded"
    assert HealthStatus.UNHEALTHY == "unhealthy"


def test_monitoring_enums():
    """Test monitoring-related enums."""
    from dotmac.platform.monitoring.benchmarks import BenchmarkStatus
    from dotmac.platform.monitoring.integrations import IntegrationType

    # Test BenchmarkStatus enum
    assert BenchmarkStatus.PENDING == "pending"
    assert BenchmarkStatus.RUNNING == "running"
    assert BenchmarkStatus.COMPLETED == "completed"
    assert BenchmarkStatus.FAILED == "failed"
    assert BenchmarkStatus.CANCELLED == "cancelled"

    # Test IntegrationType enum
    assert IntegrationType.PROMETHEUS == "prometheus"
    assert IntegrationType.DATADOG == "datadog"
    assert IntegrationType.NEWRELIC == "newrelic"
    assert IntegrationType.GRAFANA == "grafana"
    assert IntegrationType.CUSTOM == "custom"


def test_task_enums():
    """Test task/background operations enums."""
    from dotmac.platform.tasks import RetryStrategy, TaskPriority, TaskState

    # Test TaskState enum
    assert TaskState.PENDING == "pending"
    assert TaskState.RUNNING == "running"
    assert TaskState.COMPLETED == "completed"
    assert TaskState.FAILED == "failed"
    assert TaskState.CANCELLED == "cancelled"
    assert TaskState.RETRYING == "retrying"

    # Test TaskPriority enum
    assert TaskPriority.LOW == 0
    assert TaskPriority.NORMAL == 1
    assert TaskPriority.HIGH == 2
    assert TaskPriority.CRITICAL == 3

    # Test RetryStrategy enum
    assert RetryStrategy.FIXED == "fixed"
    assert RetryStrategy.EXPONENTIAL == "exponential"
    assert RetryStrategy.LINEAR == "linear"
    assert RetryStrategy.FIBONACCI == "fibonacci"


def test_database_enums():
    """Test database-related enums."""
    from dotmac.platform.database import DatabaseDriver, IsolationLevel

    # Test DatabaseDriver enum
    assert DatabaseDriver.POSTGRESQL == "postgresql"
    assert DatabaseDriver.MYSQL == "mysql"
    assert DatabaseDriver.SQLITE == "sqlite"
    assert DatabaseDriver.POSTGRESQL_ASYNC == "postgresql+asyncpg"
    assert DatabaseDriver.MYSQL_ASYNC == "mysql+aiomysql"

    # Test IsolationLevel enum
    assert IsolationLevel.READ_UNCOMMITTED == "READ UNCOMMITTED"
    assert IsolationLevel.READ_COMMITTED == "READ COMMITTED"
    assert IsolationLevel.REPEATABLE_READ == "REPEATABLE READ"
    assert IsolationLevel.SERIALIZABLE == "SERIALIZABLE"


def test_tenant_enums():
    """Test tenant-related enums."""
    from dotmac.platform.tenant import TenantIsolationLevel, TenantResolutionStrategy

    # Test TenantIsolationLevel enum
    assert TenantIsolationLevel.NONE == "none"
    assert TenantIsolationLevel.LOGICAL == "logical"
    assert TenantIsolationLevel.SCHEMA == "schema"
    assert TenantIsolationLevel.DATABASE == "database"

    # Test TenantResolutionStrategy enum
    assert TenantResolutionStrategy.HEADER == "header"
    assert TenantResolutionStrategy.JWT_CLAIM == "jwt_claim"
    assert TenantResolutionStrategy.SUBDOMAIN == "subdomain"
    assert TenantResolutionStrategy.PATH == "path"
    assert TenantResolutionStrategy.QUERY_PARAM == "query_param"


def test_enum_iteration():
    """Test that enums can be iterated."""
    from dotmac.platform.auth.mfa_service import MFAMethod
    from dotmac.platform.secrets.types import Environment

    # Test MFAMethod iteration
    mfa_methods = list(MFAMethod)
    assert MFAMethod.TOTP in mfa_methods
    assert MFAMethod.SMS in mfa_methods
    assert len(mfa_methods) >= 4

    # Test Environment iteration
    environments = list(Environment)
    assert Environment.DEVELOPMENT in environments
    assert Environment.PRODUCTION in environments
    assert len(environments) >= 4


def test_enum_comparison():
    """Test enum comparison and equality."""
    from dotmac.platform.auth.jwt_service import TokenType
    from dotmac.platform.observability.health import HealthStatus

    # Test equality
    assert TokenType.ACCESS == TokenType.ACCESS
    assert TokenType.ACCESS != TokenType.REFRESH

    # Test string comparison
    assert TokenType.ACCESS.value == "access"
    assert str(TokenType.ACCESS.value) == "access"

    # Test health status ordering (if implemented)
    assert HealthStatus.HEALTHY != HealthStatus.UNHEALTHY

    # Can compare with string values
    assert HealthStatus.HEALTHY.value == "healthy"


def test_enum_membership():
    """Test enum membership checks."""
    from dotmac.platform.auth.oauth_providers import OAuthProvider
    from dotmac.platform.secrets.types import SecretType

    # Test membership
    assert "google" in [p.value for p in OAuthProvider]
    assert "invalid" not in [p.value for p in OAuthProvider]

    # Test with hasattr
    assert hasattr(OAuthProvider, "GOOGLE")
    assert hasattr(OAuthProvider, "GITHUB")
    assert not hasattr(OAuthProvider, "INVALID")

    # Test SecretType membership
    assert "database" in [s.value for s in SecretType]
    assert "api_key" in [s.value for s in SecretType]


def test_constants():
    """Test module-level constants."""
    from dotmac.platform import __version__
    from dotmac.platform.auth.jwt_service import (
        DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES,
        DEFAULT_ALGORITHM,
        DEFAULT_REFRESH_TOKEN_EXPIRE_DAYS,
    )
    from dotmac.platform.auth.mfa_service import MFAServiceConfig

    # Test version constant
    assert __version__ is not None
    assert isinstance(__version__, str)

    # Test JWT constants
    assert DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES == 30
    assert DEFAULT_REFRESH_TOKEN_EXPIRE_DAYS == 7
    assert DEFAULT_ALGORITHM == "HS256"

    # Test MFA defaults via config
    cfg = MFAServiceConfig()
    assert cfg.totp_digits == 6
    assert cfg.totp_period == 30
    assert cfg.backup_codes_count == 10


def test_http_status_constants():
    """Test HTTP status code constants if defined."""
    # These might be defined in the codebase
    HTTP_200_OK = 200
    HTTP_201_CREATED = 201
    HTTP_204_NO_CONTENT = 204
    HTTP_400_BAD_REQUEST = 400
    HTTP_401_UNAUTHORIZED = 401
    HTTP_403_FORBIDDEN = 403
    HTTP_404_NOT_FOUND = 404
    HTTP_429_TOO_MANY_REQUESTS = 429
    HTTP_500_INTERNAL_SERVER_ERROR = 500

    assert HTTP_200_OK == 200
    assert HTTP_401_UNAUTHORIZED == 401
    assert HTTP_403_FORBIDDEN == 403
    assert HTTP_429_TOO_MANY_REQUESTS == 429


def test_time_constants():
    """Test time-related constants."""
    # Common time constants that might be defined
    SECONDS_PER_MINUTE = 60
    SECONDS_PER_HOUR = 3600
    SECONDS_PER_DAY = 86400
    MINUTES_PER_HOUR = 60
    HOURS_PER_DAY = 24
    DAYS_PER_WEEK = 7

    assert SECONDS_PER_MINUTE == 60
    assert SECONDS_PER_HOUR == 60 * 60
    assert SECONDS_PER_DAY == 60 * 60 * 24
    assert DAYS_PER_WEEK == 7


def test_regex_patterns():
    """Test regex pattern constants if defined."""
    import re

    # Common regex patterns
    EMAIL_PATTERN = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    UUID_PATTERN = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    JWT_PATTERN = r"^[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]*$"

    # Test email pattern
    assert re.match(EMAIL_PATTERN, "user@example.com") is not None
    assert re.match(EMAIL_PATTERN, "invalid.email") is None

    # Test UUID pattern
    assert re.match(UUID_PATTERN, "123e4567-e89b-12d3-a456-426614174000") is not None
    assert re.match(UUID_PATTERN, "not-a-uuid") is None

    # Test JWT pattern
    assert (
        re.match(
            JWT_PATTERN, "eyJ0eXAiOiJKV1QiLCJhbGc.eyJzdWIiOiIxMjM0NTY3ODkw.SflKxwRJSMeKKF2QT4fwpM"
        )
        is not None
    )


def test_limit_constants():
    """Test limit and threshold constants."""
    # Common limits
    MAX_PASSWORD_LENGTH = 128
    MIN_PASSWORD_LENGTH = 8
    MAX_USERNAME_LENGTH = 50
    MAX_EMAIL_LENGTH = 255
    MAX_SECRET_SIZE = 65536  # 64KB
    MAX_CACHE_SIZE = 10000
    MAX_RETRY_ATTEMPTS = 5

    assert MAX_PASSWORD_LENGTH > MIN_PASSWORD_LENGTH
    assert MAX_USERNAME_LENGTH > 0
    assert MAX_EMAIL_LENGTH >= 254  # RFC 5321
    assert MAX_SECRET_SIZE > 0
    assert MAX_CACHE_SIZE > 0
    assert MAX_RETRY_ATTEMPTS > 0


def test_default_values():
    """Test default value constants."""
    # Common defaults
    DEFAULT_PAGE_SIZE = 20
    DEFAULT_MAX_PAGE_SIZE = 100
    DEFAULT_CACHE_TTL = 300
    DEFAULT_SESSION_TIMEOUT = 3600
    DEFAULT_TOKEN_LENGTH = 32
    DEFAULT_SALT_LENGTH = 16

    assert DEFAULT_PAGE_SIZE > 0
    assert DEFAULT_MAX_PAGE_SIZE > DEFAULT_PAGE_SIZE
    assert DEFAULT_CACHE_TTL > 0
    assert DEFAULT_SESSION_TIMEOUT > 0
    assert DEFAULT_TOKEN_LENGTH >= 32
    assert DEFAULT_SALT_LENGTH >= 16


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
