"""
Base service class with DRY patterns.
Provides common functionality for all user management services.
"""


from abc import ABC
from typing import Any, Optional, TypeVar
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.core import AuthorizationError
from dotmac.platform.core.enhanced.exceptions import (

    EntityNotFoundError,
    ValidationError,
)
from dotmac.platform.observability.unified_logging import get_logger


logger = get_logger(__name__)

ServiceType = TypeVar("ServiceType")

class BaseUserService(ABC):
    """
    Abstract base service with common functionality.
    Enforces DRY patterns and provides standard operations.
    """

    def __init__(self, db_session: AsyncSession, tenant_id: Optional[UUID] = None):
        """Initialize service with database session and tenant context."""
        self.db = db_session
        self.db_session = db_session  # Backwards compatibility attribute
        self.tenant_id = tenant_id
        self._logger = get_logger(f"{__name__}.{self.__class__.__name__}")

    # === Validation Helpers ===

    def _validate_tenant_access(
        self, entity_tenant_id: Optional[UUID], operation: str = "access"
    ) -> None:
        """Validate user has access to entity's tenant."""
        if not self.tenant_id:
            # Super admin or system service
            return

        if entity_tenant_id and entity_tenant_id != self.tenant_id:
            raise AuthorizationError(f"Cannot {operation} entity from different tenant")

    def _validate_required_fields(self, data: dict[str, Any], required_fields: list[str]) -> None:
        """Validate required fields are present."""
        missing_fields = []

        for field in required_fields:
            if field not in data or data[field] is None:
                missing_fields.append(field)

        if missing_fields:
            raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")

    def _validate_field_formats(
        self, data: dict[str, Any], format_validators: dict[str, callable]
    ) -> None:
        """Validate field formats using provided validators."""
        validation_errors = []

        for field, validator in format_validators.items():
            if field in data and data[field] is not None:
                try:
                    validator(data[field])
                except ValueError as e:
                    validation_errors.append(f"{field}: {str(e)}")

        if validation_errors:
            raise ValidationError(f"Field validation errors: {'; '.join(validation_errors)}")

    def _validate_business_rules(self, operation: str, **context) -> None:
        """Validate business rules for specific operations."""
        # Override in subclasses for specific business rule validation
        pass

    # === Authorization Helpers ===

    def _check_permission(self, user_id: UUID, permission: str) -> None:
        """Check if user has required permission."""
        # This would typically integrate with a permission service
        # For now, we'll implement basic checks
        pass

    def _check_user_can_modify(self, acting_user_id: UUID, target_user_id: UUID) -> None:
        """Check if acting user can modify target user."""
        # Business rule: users can modify their own account or admins can modify others
        if acting_user_id != target_user_id:
            # Would check if acting user is admin
            # self._check_permission(acting_user_id, "users:modify")
            pass

    def _check_admin_permissions(self, user_id: UUID, operation: str) -> None:
        """Check if user has admin permissions for operation."""
        # Would integrate with role/permission system
        # For now, basic implementation
        pass

    # === Audit Helpers ===

    def _log_user_action(
        self,
        user_id: UUID,
        action: str,
        target_id: Optional[UUID] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """Log user action for audit trail."""
        audit_data = {
            "user_id": user_id,
            "action": action,
            "target_id": target_id,
            "tenant_id": self.tenant_id,
            "metadata": metadata or {},
        }

        self._logger.info(f"User action logged: {action}", extra=audit_data)

    def _log_security_event(
        self,
        event_type: str,
        user_id: Optional[UUID] = None,
        severity: str = "info",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """Log security-related events."""
        security_data = {
            "event_type": event_type,
            "user_id": user_id,
            "tenant_id": self.tenant_id,
            "severity": severity,
            "details": details or {},
        }

        if severity == "critical":
            self._logger.critical(f"Security event: {event_type}", extra=security_data)
        elif severity == "warning":
            self._logger.warning(f"Security event: {event_type}", extra=security_data)
        else:
            self._logger.info(f"Security event: {event_type}", extra=security_data)

    # === Data Transformation Helpers ===

    def _sanitize_user_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Sanitize user input data."""
        sanitized = data.copy()

        # Remove None values
        sanitized = {k: v for k, v in sanitized.items() if v is not None}

        # Normalize string fields
        string_fields = ["username", "email", "first_name", "last_name"]
        for field in string_fields:
            if field in sanitized and isinstance(sanitized[field], str):
                sanitized[field] = sanitized[field].strip()

                # Lowercase for username and email
                if field in ["username", "email"]:
                    sanitized[field] = sanitized[field].lower()

        return sanitized

    def _mask_sensitive_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Mask sensitive data in response."""
        masked = data.copy()

        sensitive_fields = [
            "password",
            "password_hash",
            "secret",
            "token",
            "api_key",
            "private_key",
            "reset_token",
        ]

        for field in sensitive_fields:
            if field in masked:
                masked[field] = "***MASKED***"

        return masked

    # === Error Handling Helpers ===

    def _handle_database_error(self, error: Exception, operation: str) -> None:
        """Handle database errors with appropriate exceptions."""
        error_msg = str(error).lower()

        if "unique constraint" in error_msg or "already exists" in error_msg:
            if "email" in error_msg:
                raise ValidationError("Email address is already in use")
            elif "username" in error_msg:
                raise ValidationError("Username is already taken")
            else:
                raise ValidationError("Duplicate entry detected")

        elif "foreign key constraint" in error_msg:
            raise ValidationError("Referenced entity does not exist")

        elif "not null constraint" in error_msg:
            raise ValidationError("Required field is missing")

        else:
            self._logger.error(f"Database error during {operation}: {error}")
            raise RuntimeError(f"Database operation failed: {operation}")

    def _validate_entity_exists(
        self, entity: Optional[Any], entity_type: str, entity_id: UUID
    ) -> Any:
        """Validate entity exists or raise appropriate error."""
        if not entity:
            raise EntityNotFoundError(f"{entity_type} not found with ID: {entity_id}")
        return entity

    # === Rate Limiting Helpers ===

    async def _check_rate_limit(self, user_id: UUID, operation: str) -> None:
        """Check rate limiting for user operations."""
        # Implementation would integrate with Redis or similar
        # For now, basic placeholder
        pass

    # === Notification Helpers ===

    async def _send_notification(
        self, user_id: UUID, notification_type: str, template: str, data: dict[str, Any]
    ) -> None:
        """Send notification to user."""
        # Integration point for notification service
        notification_data = {
            "user_id": user_id,
            "type": notification_type,
            "template": template,
            "data": data,
            "tenant_id": self.tenant_id,
        }

        self._logger.debug(f"Notification queued: {notification_type}", extra=notification_data)

    # === Configuration Helpers ===

    def _get_tenant_config(self, config_key: str, default_value: Any = None) -> Any:
        """Get tenant-specific configuration."""
        # Would integrate with configuration service
        return default_value

    def _get_security_config(self) -> dict[str, Any]:
        """Get security configuration for tenant."""
        return {
            "password_policy": {
                "min_length": 8,
                "require_uppercase": True,
                "require_lowercase": True,
                "require_numbers": True,
                "require_symbols": True,
                "max_age_days": 90,
                "history_count": 5,
            },
            "login_policy": {
                "max_failed_attempts": 5,
                "lockout_duration_minutes": 30,
                "session_timeout_minutes": 480,
                "require_mfa_for_admin": True,
            },
            "account_policy": {
                "require_email_verification": True,
                "auto_deactivate_unused_days": 365,
                "require_terms_acceptance": True,
            },
        }

    # === Utility Methods ===

    def _generate_correlation_id(self) -> str:
        """Generate correlation ID for tracking operations."""
        import uuid

        return str(uuid.uuid4())

    def _get_current_user_context(self) -> dict[str, Any]:
        """Get current user context for operations."""
        # Would typically come from request context
        return {
            "tenant_id": self.tenant_id,
            "timestamp": "datetime.now(timezone.utc)",
            # "user_id": current_user.id,
            # "session_id": current_session.id,
        }

    # === Service Interface Helpers ===

    async def health_check(self) -> dict[str, Any]:
        """Check service health."""
        try:
            # Test database connection
            await self.db.execute("SELECT 1")

            return {
                "status": "healthy",
                "service": self.__class__.__name__,
                "tenant_id": str(self.tenant_id) if self.tenant_id else None,
                "checks": {
                    "database": "connected",
                },
            }
        except (SQLAlchemyError, TimeoutError, ConnectionError) as e:
            return {
                "status": "unhealthy",
                "service": self.__class__.__name__,
                "error": str(e),
                "checks": {
                    "database": "disconnected",
                },
            }

class BaseService(BaseUserService):
    """Backward-compatible alias for legacy imports."""

__all__ = ["BaseUserService", "BaseService"]
