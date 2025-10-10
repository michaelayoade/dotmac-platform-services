"""
Admin settings management API router.

Provides endpoints for managing platform configuration settings
with proper admin authentication and audit logging.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse

from dotmac.platform.admin.settings.models import (
    AuditLog,
    BulkSettingsUpdate,
    SettingsBackup,
    SettingsCategory,
    SettingsCategoryInfo,
    SettingsExportRequest,
    SettingsImportRequest,
    SettingsResponse,
    SettingsUpdateRequest,
    SettingsValidationResult,
)
from dotmac.platform.admin.settings.service import SettingsManagementService
from dotmac.platform.auth.core import UserInfo
from dotmac.platform.auth.rbac_dependencies import require_permission

router = APIRouter(
    tags=["Admin - Settings"],
)

# Service instance (singleton)
settings_service: SettingsManagementService = SettingsManagementService()


@router.get("/categories", response_model=list[SettingsCategoryInfo])
async def get_all_categories(
    current_admin: UserInfo = Depends(require_permission("settings.read")),
) -> list[SettingsCategoryInfo]:
    """
    Get information about all available settings categories.

    Returns a list of categories with metadata about each category
    including field counts, sensitivity, and restart requirements.
    """
    categories: list[SettingsCategoryInfo] = settings_service.get_all_categories()
    return categories


@router.get("/category/{category}", response_model=SettingsResponse)
async def get_category_settings(
    category: SettingsCategory,
    include_sensitive: bool = False,
    current_admin: UserInfo = Depends(require_permission("settings.read")),
) -> SettingsResponse:
    """
    Get settings for a specific category.

    Args:
        category: The settings category to retrieve
        include_sensitive: Whether to include sensitive field values (default: masked)
        current_admin: Current admin user (from auth)

    Returns:
        Settings for the specified category
    """
    try:
        return settings_service.get_category_settings(
            category=category,
            include_sensitive=include_sensitive,
            user_id=current_admin.user_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/category/{category}", response_model=SettingsResponse)
async def update_category_settings(
    category: SettingsCategory,
    update_request: SettingsUpdateRequest,
    request: Request,
    current_admin: UserInfo = Depends(require_permission("settings.update")),
) -> SettingsResponse | JSONResponse:
    """
    Update settings for a specific category.

    This endpoint allows admins to update configuration settings
    for a specific category. Changes are validated before being applied
    and all modifications are logged in the audit trail.

    Args:
        category: The settings category to update
        update_request: The update request with new values
        request: HTTP request (for IP and user agent)
        current_admin: Current admin user

    Returns:
        Updated settings for the category
    """
    # Extract client info for audit
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")

    try:
        # First validate the settings
        validation_result = settings_service.validate_settings(
            category=category,
            updates=update_request.updates,
        )

        if not validation_result.valid:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "detail": "Validation failed",
                    "errors": validation_result.errors,
                    "warnings": validation_result.warnings,
                },
            )

        # Get email, fallback to username, then user id to ensure we have an identifier
        user_email: str = current_admin.email or current_admin.username or current_admin.user_id

        # Apply the updates
        return settings_service.update_category_settings(
            category=category,
            update_request=update_request,
            user_id=current_admin.user_id,
            user_email=user_email,
            ip_address=client_ip,
            user_agent=user_agent,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/validate", response_model=SettingsValidationResult)
async def validate_settings(
    category: SettingsCategory,
    updates: dict,
    current_admin: UserInfo = Depends(require_permission("settings.read")),
) -> SettingsValidationResult:
    """
    Validate settings updates without applying them.

    This endpoint allows testing configuration changes before
    applying them to ensure they are valid and understand any
    potential impacts (e.g., restart requirements).

    Args:
        category: The settings category
        updates: The proposed updates to validate
        current_admin: Current admin user

    Returns:
        Validation result with any errors or warnings
    """
    try:
        return settings_service.validate_settings(
            category=category,
            updates=updates,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/bulk-update")
async def bulk_update_settings(
    bulk_update: BulkSettingsUpdate,
    request: Request,
    current_admin: UserInfo = Depends(require_permission("settings.update")),
) -> dict:
    """
    Update multiple settings categories at once.

    This endpoint allows updating settings across multiple
    categories in a single transaction. Useful for coordinated
    configuration changes.

    Args:
        bulk_update: The bulk update request
        request: HTTP request
        current_admin: Current admin user

    Returns:
        Summary of updates by category
    """
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")

    results: dict[str, str] = {}
    errors: dict[str, Any] = {}

    # Get email, fallback to username
    user_email: str = current_admin.email or current_admin.username or current_admin.user_id

    for category, updates in bulk_update.updates.items():
        try:
            # Validate first
            validation = settings_service.validate_settings(category, updates)
            if not validation.valid:
                errors[category.value] = validation.errors
                continue

            # Apply updates
            update_request = SettingsUpdateRequest(
                updates=updates,
                validate_only=bulk_update.validate_only,
                reason=bulk_update.reason,
                restart_required=False,  # Can be updated based on actual needs
            )

            settings_service.update_category_settings(
                category=category,
                update_request=update_request,
                user_id=current_admin.user_id,
                user_email=user_email,
                ip_address=client_ip,
                user_agent=user_agent,
            )
            results[category.value] = "Success"

        except Exception as e:
            errors[category.value] = str(e)

    if errors and not results:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"errors": errors})

    return {
        "results": results,
        "errors": errors,
        "summary": f"Updated {len(results)} categories, {len(errors)} failed",
    }


@router.post("/backup", response_model=SettingsBackup)
async def create_settings_backup(
    name: str,
    description: str | None = None,
    categories: list[SettingsCategory] | None = None,
    current_admin: UserInfo = Depends(require_permission("settings.backup")),
) -> SettingsBackup:
    """
    Create a backup of current settings.

    Creates a snapshot of current configuration settings
    that can be restored later if needed.

    Args:
        name: Backup name
        description: Optional backup description
        categories: Categories to backup (all if not specified)
        current_admin: Current admin user

    Returns:
        Created backup information
    """
    return settings_service.create_backup(
        name=name,
        description=description,
        categories=categories,
        user_id=current_admin.user_id,
    )


@router.post("/restore/{backup_id}")
async def restore_settings_backup(
    backup_id: str,
    current_admin: UserInfo = Depends(require_permission("settings.restore")),
) -> dict:
    """
    Restore settings from a backup.

    Restores configuration settings from a previously created backup.
    All changes are logged in the audit trail.

    Args:
        backup_id: The backup ID to restore
        current_admin: Current admin user

    Returns:
        Summary of restored settings
    """
    try:
        import uuid

        backup_uuid = uuid.UUID(backup_id)

        # Get email, fallback to username
        user_email: str = current_admin.email or current_admin.username or current_admin.user_id

        restored = settings_service.restore_backup(
            backup_id=backup_uuid,
            user_id=current_admin.user_id,
            user_email=user_email,
        )

        return {
            "message": "Settings restored successfully",
            "categories": [cat.value for cat in restored.keys()],
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/audit-logs", response_model=list[AuditLog])
async def get_audit_logs(
    category: SettingsCategory | None = None,
    user_id: str | None = None,
    limit: int = 100,
    current_admin: UserInfo = Depends(require_permission("settings.audit.read")),
) -> list[AuditLog]:
    """
    Get audit logs for settings changes.

    Retrieves the audit trail of all configuration changes
    with optional filtering by category or user.

    Args:
        category: Filter by settings category
        user_id: Filter by user who made changes
        limit: Maximum number of logs to return (default: 100)
        current_admin: Current admin user

    Returns:
        List of audit log entries
    """
    audit_logs: list[AuditLog] = settings_service.get_audit_logs(
        category=category,
        user_id=user_id,
        limit=limit,
    )
    return audit_logs


@router.post("/export")
async def export_settings(
    export_request: SettingsExportRequest,
    current_admin: UserInfo = Depends(require_permission("settings.export")),
) -> dict:
    """
    Export settings to a specific format.

    Exports configuration settings to JSON, YAML, or environment
    variable format for backup or migration purposes.

    Args:
        export_request: Export request with format and options
        current_admin: Current admin user

    Returns:
        Exported settings in requested format
    """
    try:
        exported = settings_service.export_settings(
            categories=export_request.categories,
            include_sensitive=export_request.include_sensitive,
            format=export_request.format,
        )

        return {
            "format": export_request.format,
            "data": exported,
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/import")
async def import_settings(
    import_request: SettingsImportRequest,
    request: Request,
    current_admin: UserInfo = Depends(require_permission("settings.import")),
) -> dict:
    """
    Import settings from external data.

    Imports configuration settings from JSON/YAML data.
    Settings are validated before being applied.

    Args:
        import_request: Import request with settings data
        request: HTTP request
        current_admin: Current admin user

    Returns:
        Summary of imported settings
    """
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")

    imported_categories: list[str] = []
    errors: dict[str, Any] = {}

    # Get email, fallback to username
    user_email: str = current_admin.email or current_admin.username or current_admin.user_id

    for category_str, settings_data in import_request.data.items():
        try:
            category = SettingsCategory(category_str)

            # Skip if not in allowed categories
            if import_request.categories and category not in import_request.categories:
                continue

            # Validate settings
            validation = settings_service.validate_settings(
                category=category,
                updates=settings_data,
            )

            if not validation.valid:
                errors[category_str] = validation.errors
                continue

            # Apply if not validate_only
            if not import_request.validate_only:
                update_request = SettingsUpdateRequest(
                    updates=settings_data,
                    validate_only=False,
                    reason=import_request.reason or "Imported settings",
                    restart_required=False,  # Can be updated based on actual needs
                )

                settings_service.update_category_settings(
                    category=category,
                    update_request=update_request,
                    user_id=current_admin.user_id,
                    user_email=user_email,
                    ip_address=client_ip,
                    user_agent=user_agent,
                )

                imported_categories.append(category_str)

        except Exception as e:
            errors[category_str] = str(e)

    if errors and not imported_categories:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"errors": errors})

    return {
        "imported": imported_categories,
        "errors": errors,
        "validate_only": import_request.validate_only,
    }


@router.post("/reset/{category}")
async def reset_category_to_defaults(
    category: SettingsCategory,
    request: Request,
    current_admin: UserInfo = Depends(require_permission("settings.reset")),
) -> SettingsResponse:
    """
    Reset a settings category to default values.

    Resets all settings in a category to their default values.
    This action is logged in the audit trail.

    Args:
        category: The settings category to reset
        request: HTTP request
        current_admin: Current admin user

    Returns:
        Reset settings for the category
    """
    # This would need to be implemented in the service
    # to get default values from the Pydantic model defaults

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Reset to defaults not yet implemented"
    )


@router.get("/health")
async def settings_health_check(
    current_admin: UserInfo = Depends(require_permission("settings.read")),
) -> dict:
    """
    Health check for settings management.

    Verifies that the settings management system is operational
    and returns basic statistics.

    Args:
        current_admin: Current admin user

    Returns:
        Health status and statistics
    """
    categories = settings_service.get_all_categories()

    return {
        "status": "healthy",
        "categories_available": len(categories),
        "audit_logs_count": len(settings_service._audit_logs),
        "backups_count": len(settings_service._backups),
    }
