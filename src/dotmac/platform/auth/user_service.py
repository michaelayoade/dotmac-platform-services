"""Lightweight user service helpers consolidated under the auth package.

These utilities preserve backwards-compatible behaviour from the legacy
user-management module so existing tests and call-sites can rely on the
same sanitisation, validation, and health-check semantics while the
platform converges on a single authentication stack.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Iterable

from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError

from dotmac.platform.domain import (
    AuthorizationError,
    EntityNotFoundError,
    ValidationError,
)
from dotmac.platform.logging import get_logger

logger = get_logger(__name__)

_MASKED_VALUE = "***MASKED***"
_SENSITIVE_KEYS: Iterable[str] = (
    "password",
    "password_hash",
    "token",
    "access_token",
    "refresh_token",
    "secret",
)


class UserType(str, Enum):
    """Supported user classifications (preserved for compatibility)."""

    TENANT_USER = "tenant_user"
    CUSTOMER = "customer"
    PLATFORM_ADMIN = "platform_admin"


class UserCreateSchema(BaseModel):
    """Minimal schema used by registration helpers."""

    username: str
    email: str
    first_name: str
    last_name: str | None = None
    user_type: UserType = Field(default=UserType.CUSTOMER)
    password: str
    terms_accepted: bool = Field(default=False)
    privacy_accepted: bool = Field(default=False)
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    platform_metadata: dict[str, Any] = Field(default_factory=dict)
    timezone: str | None = None
    language: str | None = None
    tenant_id: str | None = None


class BaseUserService:
    """Shared helper methods used by higher-level user-facing services."""

    def __init__(self, db_session: Any, tenant_id: str | None = None):
        self.db_session = db_session
        self.tenant_id = tenant_id

    # ------------------------------------------------------------------
    # Data sanitisation helpers
    # ------------------------------------------------------------------
    def _sanitize_user_data(self, payload: dict[str, Any]) -> dict[str, Any]:
        sanitized: dict[str, Any] = {}
        for key, value in payload.items():
            if value is None:
                continue

            if isinstance(value, str):
                trimmed = value.strip()
                if not trimmed:
                    continue

                if key in {"username", "email"}:
                    sanitized[key] = trimmed.lower()
                elif key == "first_name":
                    sanitized[key] = trimmed.capitalize()
                else:
                    sanitized[key] = trimmed
            else:
                sanitized[key] = value

        return sanitized

    def _mask_sensitive_data(self, payload: dict[str, Any]) -> dict[str, Any]:
        masked = dict(payload)
        for key in _SENSITIVE_KEYS:
            if key in masked:
                masked[key] = _MASKED_VALUE
        return masked

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------
    def _validate_tenant_access(self, tenant_id: str | None, action: str) -> None:
        if self.tenant_id is not None and tenant_id != self.tenant_id:
            raise AuthorizationError(
                f"Tenant mismatch for action '{action}': {tenant_id} != {self.tenant_id}"
            )

    def _validate_entity_exists(
        self, entity: Any, entity_name: str, entity_id: Any
    ) -> None:
        if entity is None:
            raise EntityNotFoundError(
                f"{entity_name} with identifier '{entity_id}' was not found"
            )

    def _validate_required_fields(
        self, payload: dict[str, Any], required_fields: Iterable[str]
    ) -> None:
        missing = [field for field in required_fields if not payload.get(field)]
        if missing:
            raise ValidationError(f"Missing required fields: {', '.join(sorted(missing))}")

    def _handle_database_error(self, error: Exception, operation: str) -> None:
        message = str(error)
        if "UNIQUE constraint failed" in message or "duplicate key value" in message:
            raise ValidationError("Email address is already in use") from error
        if isinstance(error, SQLAlchemyError):
            raise ValidationError(f"Database error during {operation}: {message}") from error
        raise RuntimeError(message) from error

    # ------------------------------------------------------------------
    # Operational helpers
    # ------------------------------------------------------------------
    async def health_check(self) -> dict[str, Any]:
        checks: dict[str, Any] = {}
        status = "healthy"
        try:
            await self.db_session.execute("SELECT 1")
            checks["database"] = "connected"
        except Exception as exc:  # pragma: no cover - defensive guard
            status = "unhealthy"
            checks["database"] = "disconnected"
            logger.error("User service health check failed", error=str(exc))

        return {"status": status, "checks": checks}


class UserService(BaseUserService):
    """Minimal asynchronous user orchestration service."""

    def __init__(
        self,
        db_session: Any,
        tenant_id: str | None = None,
        user_repo: Any | None = None,
    ) -> None:
        super().__init__(db_session=db_session, tenant_id=tenant_id)
        self.user_repo = user_repo

    async def register_user(
        self, user_data: UserCreateSchema, *, auto_activate: bool = False
    ) -> Any:
        if not user_data.terms_accepted or not user_data.privacy_accepted:
            raise ValidationError("User must accept terms of service and privacy policy")

        if user_data.user_type == UserType.PLATFORM_ADMIN:
            user_data.user_type = UserType.CUSTOMER

        return await self.create_user(user_data, auto_activate=auto_activate)

    async def create_user(
        self, user_data: UserCreateSchema, *, auto_activate: bool = False
    ) -> Any:
        if not self.user_repo:
            raise RuntimeError("User repository is not configured")

        username_available = await self.user_repo.check_username_available(
            user_data.username
        )
        if not username_available:
            raise ValidationError("Username is already taken")

        email_available = await self.user_repo.check_email_available(user_data.email)
        if not email_available:
            raise ValidationError("Email address is already in use")

        return await self.user_repo.create_user(user_data, auto_activate=auto_activate)


__all__ = [
    "BaseUserService",
    "UserService",
    "UserType",
    "UserCreateSchema",
]
