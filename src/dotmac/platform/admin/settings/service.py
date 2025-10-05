"""
Settings management service for admin operations.
"""

import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import structlog
from pydantic import BaseModel, ValidationError

from dotmac.platform import settings as platform_settings
from dotmac.platform.admin.settings.models import (
    AuditLog,
    SettingField,
    SettingsBackup,
    SettingsCategory,
    SettingsCategoryInfo,
    SettingsResponse,
    SettingsUpdateRequest,
    SettingsValidationResult,
)

logger = structlog.get_logger(__name__)


class SettingsManagementService:
    """Service for managing platform settings."""

    # Map categories to settings attributes
    CATEGORY_MAPPING = {
        SettingsCategory.DATABASE: "database",
        SettingsCategory.JWT: "jwt",
        SettingsCategory.REDIS: "redis",
        SettingsCategory.VAULT: "vault",
        SettingsCategory.STORAGE: "storage",
        SettingsCategory.EMAIL: "email",
        SettingsCategory.TENANT: "tenant",
        SettingsCategory.CORS: "cors",
        SettingsCategory.RATE_LIMIT: "rate_limit",
        SettingsCategory.OBSERVABILITY: "observability",
        SettingsCategory.CELERY: "celery",
        SettingsCategory.FEATURES: "features",
        SettingsCategory.BILLING: "billing",
    }

    # Fields that should be masked in responses
    SENSITIVE_FIELDS = {
        "password",
        "secret",
        "token",
        "key",
        "api_key",
        "secret_key",
        "private_key",
        "smtp_password",
        "redis_password",
        "database_password",
    }

    # Settings that require service restart
    RESTART_REQUIRED_SETTINGS = {
        SettingsCategory.DATABASE: ["host", "port", "database", "pool_size"],
        SettingsCategory.REDIS: ["host", "port", "max_connections"],
        SettingsCategory.CELERY: ["broker_url", "result_backend"],
    }

    def __init__(self):
        """Initialize settings management service."""
        self.settings = platform_settings.settings
        self._audit_logs: list[AuditLog] = []
        self._backups: dict[UUID, SettingsBackup] = {}

    def get_category_settings(
        self,
        category: SettingsCategory,
        include_sensitive: bool = False,
        user_id: str | None = None,
    ) -> SettingsResponse:
        """
        Get settings for a specific category.

        Args:
            category: Settings category to retrieve
            include_sensitive: Whether to include sensitive field values
            user_id: ID of requesting user (for audit)

        Returns:
            SettingsResponse with category settings
        """
        attr_name = self.CATEGORY_MAPPING.get(category)
        if not attr_name or not hasattr(self.settings, attr_name):
            raise ValueError(f"Invalid settings category: {category}")

        settings_obj = getattr(self.settings, attr_name)
        fields = self._extract_fields(settings_obj, include_sensitive=include_sensitive)

        # Get last update info from audit logs
        last_update_info = self._get_last_update_info(category)

        return SettingsResponse(
            category=category,
            display_name=SettingsCategory.get_display_name(category),
            fields=fields,
            last_updated=last_update_info.get("timestamp"),
            updated_by=last_update_info.get("user_email"),
        )

    def update_category_settings(
        self,
        category: SettingsCategory,
        update_request: SettingsUpdateRequest,
        user_id: str,
        user_email: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> SettingsResponse:
        """
        Update settings for a specific category.

        Args:
            category: Settings category to update
            update_request: Update request with new values
            user_id: ID of user making changes
            user_email: Email of user making changes
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Updated settings response
        """
        # Validate category
        attr_name = self.CATEGORY_MAPPING.get(category)
        if not attr_name or not hasattr(self.settings, attr_name):
            raise ValueError(f"Invalid settings category: {category}")

        # Get current settings
        settings_obj = getattr(self.settings, attr_name)
        old_values = {}
        changes = {}

        # Validate and apply updates
        for field_name, new_value in update_request.updates.items():
            if not hasattr(settings_obj, field_name):
                raise ValueError(f"Invalid field '{field_name}' for category {category}")

            old_value = getattr(settings_obj, field_name)
            old_values[field_name] = old_value

            # Apply the update
            if not update_request.validate_only:
                setattr(settings_obj, field_name, new_value)
                changes[field_name] = {"old": old_value, "new": new_value}

        # Create audit log entry
        if not update_request.validate_only and changes:
            audit_entry = AuditLog(
                id=uuid4(),
                timestamp=datetime.now(UTC),
                user_id=user_id,
                user_email=user_email,
                category=category,
                action="update",
                changes=changes,
                reason=update_request.reason,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            self._audit_logs.append(audit_entry)

            logger.info(
                "Settings updated",
                category=category.value,
                user=user_email,
                changes=list(changes.keys()),
            )

        # Return updated settings
        return self.get_category_settings(category, include_sensitive=False)

    def validate_settings(
        self,
        category: SettingsCategory,
        updates: dict[str, Any],
    ) -> SettingsValidationResult:
        """
        Validate settings updates without applying them.

        Args:
            category: Settings category
            updates: Proposed updates

        Returns:
            Validation result with any errors or warnings
        """
        result = SettingsValidationResult(
            valid=True,
            errors={},
            warnings={},
            restart_required=False,
        )

        attr_name = self.CATEGORY_MAPPING.get(category)
        if not attr_name or not hasattr(self.settings, attr_name):
            result.valid = False
            result.errors["category"] = f"Invalid category: {category}"
            return result

        settings_class = type(getattr(self.settings, attr_name))

        # Check if any fields require restart
        restart_fields = self.RESTART_REQUIRED_SETTINGS.get(category, [])
        for field_name in updates.keys():
            if field_name in restart_fields:
                result.restart_required = True
                result.warnings[field_name] = "This change requires service restart"

        # Validate using Pydantic model
        try:
            # Get current values
            current_data = getattr(self.settings, attr_name).model_dump()
            # Apply updates
            current_data.update(updates)
            # Validate complete model
            settings_class(**current_data)
        except ValidationError as e:
            result.valid = False
            for error in e.errors():
                field = ".".join(str(loc) for loc in error["loc"])
                result.errors[field] = error["msg"]
        except Exception as e:
            result.valid = False
            result.errors["validation"] = str(e)

        return result

    def get_all_categories(self) -> list[SettingsCategoryInfo]:
        """
        Get information about all available settings categories.

        Returns:
            List of category information
        """
        categories = []

        for category in SettingsCategory:
            attr_name = self.CATEGORY_MAPPING.get(category)
            if not attr_name or not hasattr(self.settings, attr_name):
                continue

            settings_obj = getattr(self.settings, attr_name)
            fields = self._extract_fields(settings_obj)

            has_sensitive = any(self._is_sensitive_field(field.name) for field in fields)

            restart_required = category in self.RESTART_REQUIRED_SETTINGS

            categories.append(
                SettingsCategoryInfo(
                    category=category,
                    display_name=SettingsCategory.get_display_name(category),
                    description=self._get_category_description(category),
                    fields_count=len(fields),
                    has_sensitive_fields=has_sensitive,
                    restart_required=restart_required,
                    last_updated=self._get_last_update_time(category),
                )
            )

        return categories

    def create_backup(
        self,
        name: str,
        description: str | None,
        categories: list[SettingsCategory] | None,
        user_id: str,
    ) -> SettingsBackup:
        """
        Create a backup of current settings.

        Args:
            name: Backup name
            description: Backup description
            categories: Categories to backup (all if None)
            user_id: User creating backup

        Returns:
            Created backup
        """
        if categories is None:
            categories = list(SettingsCategory)

        backup_data = {}
        for category in categories:
            attr_name = self.CATEGORY_MAPPING.get(category)
            if attr_name and hasattr(self.settings, attr_name):
                settings_obj = getattr(self.settings, attr_name)
                backup_data[category.value] = settings_obj.model_dump()

        backup = SettingsBackup(
            id=uuid4(),
            created_at=datetime.now(UTC),
            created_by=user_id,
            name=name,
            description=description,
            categories=categories,
            settings_data=backup_data,
        )

        self._backups[backup.id] = backup

        logger.info(
            "Settings backup created",
            backup_id=str(backup.id),
            name=name,
            categories=[c.value for c in categories],
        )

        return backup

    def restore_backup(
        self,
        backup_id: UUID,
        user_id: str,
        user_email: str,
    ) -> dict[SettingsCategory, SettingsResponse]:
        """
        Restore settings from a backup.

        Args:
            backup_id: Backup ID to restore
            user_id: User performing restore
            user_email: User email

        Returns:
            Restored settings by category
        """
        backup = self._backups.get(backup_id)
        if not backup:
            raise ValueError(f"Backup not found: {backup_id}")

        restored = {}

        for category_str, data in backup.settings_data.items():
            category = SettingsCategory(category_str)
            attr_name = self.CATEGORY_MAPPING.get(category)

            if attr_name and hasattr(self.settings, attr_name):
                settings_obj = getattr(self.settings, attr_name)

                # Track changes for audit
                changes = {}
                for field_name, new_value in data.items():
                    if hasattr(settings_obj, field_name):
                        old_value = getattr(settings_obj, field_name)
                        setattr(settings_obj, field_name, new_value)
                        changes[field_name] = {"old": old_value, "new": new_value}

                # Audit log
                if changes:
                    audit_entry = AuditLog(
                        id=uuid4(),
                        timestamp=datetime.now(UTC),
                        user_id=user_id,
                        user_email=user_email,
                        category=category,
                        action="restore",
                        changes=changes,
                        reason=f"Restored from backup: {backup.name}",
                    )
                    self._audit_logs.append(audit_entry)

                restored[category] = self.get_category_settings(category)

        logger.info(
            "Settings restored from backup",
            backup_id=str(backup_id),
            categories=list(restored.keys()),
            user=user_email,
        )

        return restored

    def get_audit_logs(
        self,
        category: SettingsCategory | None = None,
        user_id: str | None = None,
        limit: int = 100,
    ) -> list[AuditLog]:
        """
        Get audit logs for settings changes.

        Args:
            category: Filter by category
            user_id: Filter by user
            limit: Maximum number of logs to return

        Returns:
            List of audit logs
        """
        logs = self._audit_logs

        if category:
            logs = [log for log in logs if log.category == category]

        if user_id:
            logs = [log for log in logs if log.user_id == user_id]

        # Sort by timestamp descending
        logs.sort(key=lambda x: x.timestamp, reverse=True)

        return logs[:limit]

    def export_settings(
        self,
        categories: list[SettingsCategory] | None = None,
        include_sensitive: bool = False,
        format: str = "json",
    ) -> str:
        """
        Export settings to string format.

        Args:
            categories: Categories to export (all if None)
            include_sensitive: Include sensitive fields
            format: Export format (json, yaml, env)

        Returns:
            Exported settings string
        """
        if categories is None:
            categories = list(SettingsCategory)

        export_data = {}
        for category in categories:
            attr_name = self.CATEGORY_MAPPING.get(category)
            if attr_name and hasattr(self.settings, attr_name):
                settings_obj = getattr(self.settings, attr_name)
                data = settings_obj.model_dump()

                # Mask sensitive fields if needed
                if not include_sensitive:
                    data = self._mask_sensitive_data(data)

                export_data[category.value] = data

        if format == "json":
            return json.dumps(export_data, indent=2, default=str)
        elif format == "env":
            return self._to_env_format(export_data)
        elif format == "yaml":
            # Would need to import yaml library
            return json.dumps(export_data, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    # Helper methods

    def _extract_fields(
        self,
        settings_obj: BaseModel,
        include_sensitive: bool = False,
    ) -> list[SettingField]:
        """Extract fields from a settings object."""
        fields = []

        # Access model_fields from the class, not the instance (Pydantic v2.11+)
        model_class = type(settings_obj)
        for field_name, field_info in model_class.model_fields.items():
            value = getattr(settings_obj, field_name)
            is_sensitive = self._is_sensitive_field(field_name)

            # Mask sensitive values if needed
            if is_sensitive and not include_sensitive:
                if value:
                    value = "***MASKED***"

            fields.append(
                SettingField(
                    name=field_name,
                    value=value,
                    type=str(field_info.annotation),
                    description=field_info.description,
                    default=field_info.default,
                    required=field_info.is_required(),
                    sensitive=is_sensitive,
                )
            )

        return fields

    def _is_sensitive_field(self, field_name: str) -> bool:
        """Check if a field is sensitive."""
        field_lower = field_name.lower()
        return any(sensitive in field_lower for sensitive in self.SENSITIVE_FIELDS)

    def _get_category_description(self, category: SettingsCategory) -> str:
        """Get description for a settings category."""
        descriptions = {
            SettingsCategory.DATABASE: "Database connection and pooling configuration",
            SettingsCategory.JWT: "JWT token generation and validation settings",
            SettingsCategory.REDIS: "Redis cache and session storage configuration",
            SettingsCategory.VAULT: "HashiCorp Vault integration settings",
            SettingsCategory.STORAGE: "Object storage (MinIO/S3) configuration",
            SettingsCategory.EMAIL: "Email and SMTP server settings",
            SettingsCategory.TENANT: "Multi-tenant configuration and isolation",
            SettingsCategory.CORS: "Cross-Origin Resource Sharing settings",
            SettingsCategory.RATE_LIMIT: "API rate limiting configuration",
            SettingsCategory.OBSERVABILITY: "Logging, tracing, and monitoring settings",
            SettingsCategory.CELERY: "Background task processing configuration",
            SettingsCategory.FEATURES: "Feature flags and toggles",
            SettingsCategory.BILLING: "Billing system configuration and subscription settings",
        }
        return descriptions.get(category, "")

    def _get_last_update_time(self, category: SettingsCategory) -> datetime | None:
        """Get last update time for a category from audit logs."""
        for log in self._audit_logs:
            if log.category == category:
                return log.timestamp
        return None

    def _get_last_update_info(self, category: SettingsCategory) -> dict[str, Any]:
        """Get last update information for a category from audit logs."""
        # Sort logs by timestamp descending to get the most recent
        sorted_logs = sorted(self._audit_logs, key=lambda x: x.timestamp, reverse=True)

        for log in sorted_logs:
            if log.category == category:
                return {
                    "timestamp": log.timestamp,
                    "user_email": log.user_email,
                    "user_id": log.user_id,
                }

        return {}

    def _mask_sensitive_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Mask sensitive values in data dictionary."""
        masked = {}
        for key, value in data.items():
            if self._is_sensitive_field(key):
                # Always mask sensitive fields, even if empty
                masked[key] = "***MASKED***" if value else "***MASKED***"
            elif isinstance(value, dict):
                masked[key] = self._mask_sensitive_data(value)
            else:
                masked[key] = value
        return masked

    def _to_env_format(self, data: dict[str, Any], prefix: str = "") -> str:
        """Convert settings data to environment variable format."""
        lines = []

        def process_dict(d: dict[str, Any], current_prefix: str):
            for key, value in d.items():
                env_key = f"{current_prefix}{key}".upper()

                if isinstance(value, dict):
                    process_dict(value, f"{env_key}__")
                elif isinstance(value, bool):
                    lines.append(f"{env_key}={str(value).lower()}")
                elif isinstance(value, (list, tuple)):
                    lines.append(f"{env_key}={','.join(str(v) for v in value)}")
                else:
                    lines.append(f"{env_key}={value}")

        for category, settings_data in data.items():
            process_dict(settings_data, f"{category.upper()}__")

        return "\n".join(lines)
