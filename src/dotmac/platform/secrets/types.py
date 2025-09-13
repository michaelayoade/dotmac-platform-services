"""
Core types and data structures for secrets management
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal

from pydantic import (
    BaseModel,
    Field,
    field_validator,
)


class SecretKind(str, Enum):
    """Types of secrets managed by the system"""

    JWT_KEYPAIR = "jwt_keypair"
    SYMMETRIC_SECRET = "symmetric_secret"
    SERVICE_SIGNING_SECRET = "service_signing_secret"
    DATABASE_CREDENTIALS = "database_credentials"
    ENCRYPTION_KEY = "encryption_key"
    WEBHOOK_SECRET = "webhook_secret"
    CUSTOM_SECRET = "custom_secret"


# Backward-compat enum alias expected by tests
class SecretType(str, Enum):
    """Generic secret categories expected by tests."""

    DATABASE = "database"
    API_KEY = "api_key"
    JWT = "jwt"
    ENCRYPTION_KEY = "encryption_key"
    CERTIFICATE = "certificate"
    PASSWORD = "password"
    TOKEN = "token"
    WEBHOOK = "webhook"
    OTHER = "other"


class Environment(str, Enum):
    """Deployment environments"""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class RotationStatus(str, Enum):
    """Secret rotation status states"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class JWTKeypair:
    """JWT signing keypair with metadata"""

    private_pem: str
    public_pem: str
    algorithm: str
    kid: str
    created_at: str | None = None
    expires_at: str | None = None

    def __post_init__(self) -> None:
        # Validate algorithm
        if self.algorithm not in {"RS256", "RS384", "RS512", "ES256", "ES384", "ES512"}:
            raise ValueError(f"Unsupported JWT algorithm: {self.algorithm}")


@dataclass(frozen=True)
class DatabaseCredentials:
    """Database connection credentials"""

    host: str
    port: int
    username: str
    password: str
    database: str
    driver: str = "postgresql"
    ssl_mode: str = "require"
    pool_size: int = 10
    max_overflow: int = 20

    @property
    def connection_url(self) -> str:
        """Generate database connection URL"""
        if self.driver == "postgresql":
            return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        if self.driver == "mysql":
            return (
                f"mysql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
            )
        if self.driver == "sqlite":
            return f"sqlite:///{self.database}"
        raise ValueError(f"Unsupported database driver: {self.driver}")

    @property
    def connection_params(self) -> dict[str, Any]:
        """Generate connection parameters dict"""
        params = {
            "host": self.host,
            "port": self.port,
            "user": self.username,
            "password": self.password,
            "database": self.database,
            "sslmode": self.ssl_mode,
        }

        if self.driver == "postgresql":
            params["driver"] = "postgresql+asyncpg"
        elif self.driver == "mysql":
            params["driver"] = "mysql+aiomysql"

        return params


class SecretPolicy(BaseModel):
    """Policy for secret validation and rotation"""

    min_length: int = Field(default=32, ge=8)
    max_age_days: int | None = Field(default=None, ge=1)
    require_special_chars: bool = Field(default=False)
    forbidden_patterns: list[str] = Field(default_factory=list)
    allowed_algorithms: list[str] = Field(default_factory=list)
    rotation_warning_days: int = Field(default=7, ge=1)

    @field_validator("forbidden_patterns")
    def validate_patterns(cls, v: list[str]) -> list[str]:
        """Validate forbidden patterns are not empty"""
        return [p for p in v if p.strip()]


class SecretMetadata(BaseModel):
    """Metadata about a secret"""

    path: str
    kind: SecretKind
    created_at: str | None = None
    updated_at: str | None = None
    expires_at: str | None = None
    version: str | None = None
    tags: list[str] = Field(default_factory=list)
    policy: SecretPolicy | None = None

    @field_validator("path")
    def validate_path(cls, v: str) -> str:
        """Validate secret path format"""
        if not v or not v.strip():
            raise ValueError("Secret path cannot be empty")

        # Normalize path separators
        normalized = v.strip().replace("\\", "/")

        # Remove leading/trailing slashes
        return normalized.strip("/")


@dataclass(frozen=True)
class SecretValue:
    """A secret value with its metadata"""

    value: str | bytes | dict[str, Any]
    metadata: SecretMetadata

    def as_str(self) -> str:
        """Get secret as string"""
        if isinstance(self.value, str):
            return self.value
        if isinstance(self.value, bytes):
            return self.value.decode("utf-8")
        raise TypeError(f"Cannot convert {type(self.value)} to string")

    def as_bytes(self) -> bytes:
        """Get secret as bytes"""
        if isinstance(self.value, bytes):
            return self.value
        if isinstance(self.value, str):
            return self.value.encode("utf-8")
        raise TypeError(f"Cannot convert {type(self.value)} to bytes")

    def as_dict(self) -> dict[str, Any]:
        """Get secret as dictionary"""
        if isinstance(self.value, dict):
            return self.value
        raise TypeError(f"Cannot convert {type(self.value)} to dict")


class ProviderConfig(BaseModel):
    """Base configuration for secret providers"""

    provider_type: str
    timeout: int = Field(default=30, ge=1, le=300)
    retry_attempts: int = Field(default=3, ge=0, le=10)
    retry_backoff_factor: float = Field(default=2.0, ge=1.0, le=10.0)
    environment: Environment = Field(default=Environment.DEVELOPMENT)


class OpenBaoConfig(ProviderConfig):
    """Configuration for OpenBao/Vault provider"""

    provider_type: Literal["openbao"] = "openbao"
    url: str
    token: str
    mount_path: str = Field(default="kv")
    api_version: str = Field(default="v2")
    verify_ssl: bool = Field(default=True)
    ca_cert_path: str | None = None
    namespace: str | None = None

    @field_validator("url")
    def validate_url(cls, v: str) -> str:
        """Validate OpenBao URL format"""
        if not v.startswith(("http://", "https://")):
            raise ValueError("OpenBao URL must start with http:// or https://")
        return v.rstrip("/")

    @field_validator("token")
    def validate_token(cls, v: str) -> str:
        """Validate token is not empty"""
        if not v or not v.strip():
            raise ValueError("OpenBao token cannot be empty")
        return v.strip()


class EnvConfig(ProviderConfig):
    """Configuration for environment variable provider"""

    provider_type: Literal["env"] = "env"
    prefix: str = Field(default="")
    allow_production: bool = Field(default=False)

    def model_post_init(self, __context: Any) -> None:
        """Post-initialization validation"""
        if self.environment == Environment.PRODUCTION and not self.allow_production:
            env_override = os.getenv("EXPLICIT_ALLOW_ENV_SECRETS", "").lower()
            if env_override not in {"true", "1", "yes"}:
                raise ValueError(
                    "Environment provider is disabled in production. "
                    "Set EXPLICIT_ALLOW_ENV_SECRETS=true to override."
                )


class FileConfig(ProviderConfig):
    """Configuration for file-based provider"""

    provider_type: Literal["file"] = "file"
    base_path: str
    file_format: str = Field(default="json")  # json, yaml, toml

    @field_validator("base_path")
    def validate_base_path(cls, v: str) -> str:
        """Validate base path exists"""
        if not os.path.exists(v):
            raise ValueError(f"Base path does not exist: {v}")
        if not os.path.isdir(v):
            raise ValueError(f"Base path is not a directory: {v}")
        return v

    @field_validator("file_format")
    def validate_format(cls, v: str) -> str:
        """Validate supported file format"""
        if v not in {"json", "yaml", "toml"}:
            raise ValueError(f"Unsupported file format: {v}")
        return v


# Common secret path patterns
class SecretPaths:
    """Standard secret path patterns"""

    @staticmethod
    def jwt_keypair(app: str, kid: str | None = None) -> str:
        """Generate JWT keypair path"""
        if kid:
            return f"jwt/{app}/keypair/{kid}"
        return f"jwt/{app}/keypair"

    @staticmethod
    def database_credentials(db_name: str) -> str:
        """Generate database credentials path"""
        return f"databases/{db_name}"

    @staticmethod
    def service_signing_secret(service: str) -> str:
        """Generate service signing secret path"""
        return f"service-signing/{service}"

    @staticmethod
    def encryption_key(key_name: str) -> str:
        """Generate encryption key path"""
        return f"encryption-keys/{key_name}"

    @staticmethod
    def webhook_secret(webhook_id: str) -> str:
        """Generate webhook secret path"""
        return f"webhooks/{webhook_id}"

    @staticmethod
    def symmetric_secret(name: str) -> str:
        """Generate symmetric secret path"""
        return f"secrets/symmetric/{name}"


# Type aliases for convenience
SecretData = dict[str, Any]
SecretResult = str | bytes | dict[str, Any] | JWTKeypair | DatabaseCredentials
