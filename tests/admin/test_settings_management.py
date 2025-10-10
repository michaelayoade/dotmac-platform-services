"""
Tests for admin settings management functionality.
"""

import pytest

from dotmac.platform.admin.settings.models import (
    SettingsCategory,
    SettingsCategoryInfo,
    SettingsResponse,
    SettingsUpdateRequest,
    SettingsValidationResult,
)
from dotmac.platform.admin.settings.service import SettingsManagementService


class TestSettingsManagementService:
    """Test the settings management service."""

    @pytest.fixture
    def service(self):
        """Create a settings management service instance."""
        return SettingsManagementService()

    def test_get_all_categories(self, service):
        """Test getting all available settings categories."""
        categories = service.get_all_categories()

        assert len(categories) > 0
        assert all(isinstance(cat, SettingsCategoryInfo) for cat in categories)

        # Check specific categories exist
        category_names = [cat.category for cat in categories]
        assert SettingsCategory.DATABASE in category_names
        assert SettingsCategory.JWT in category_names
        assert SettingsCategory.EMAIL in category_names
        assert SettingsCategory.TENANT in category_names

    def test_get_category_settings(self, service):
        """Test getting settings for a specific category."""
        # Test EMAIL settings (newly added)
        response = service.get_category_settings(SettingsCategory.EMAIL, include_sensitive=False)

        assert isinstance(response, SettingsResponse)
        assert response.category == SettingsCategory.EMAIL
        assert response.display_name == "Email & SMTP"
        assert len(response.fields) > 0

        # Check sensitive fields are masked
        smtp_password_field = next((f for f in response.fields if f.name == "smtp_password"), None)
        assert smtp_password_field is not None
        assert smtp_password_field.sensitive is True
        assert smtp_password_field.value != "actual_password"  # Should be masked

    def test_get_category_settings_with_sensitive(self, service):
        """Test getting settings with sensitive fields included."""
        response = service.get_category_settings(SettingsCategory.EMAIL, include_sensitive=True)

        # Sensitive fields should show actual values
        smtp_password_field = next((f for f in response.fields if f.name == "smtp_password"), None)
        assert smtp_password_field is not None
        # Value should be the actual configured value (empty string by default)
        assert smtp_password_field.value == ""

    def test_validate_settings_valid(self, service):
        """Test validating valid settings updates."""
        result = service.validate_settings(
            SettingsCategory.EMAIL,
            {
                "smtp_host": "mail.example.com",
                "smtp_port": 587,
                "use_tls": True,
            },
        )

        assert isinstance(result, SettingsValidationResult)
        assert result.valid is True
        assert len(result.errors) == 0

    def test_validate_settings_invalid(self, service):
        """Test validating invalid settings updates."""
        result = service.validate_settings(
            SettingsCategory.EMAIL,
            {
                "smtp_port": "not_a_number",  # Invalid type
            },
        )

        assert result.valid is False
        assert len(result.errors) > 0

    def test_validate_settings_restart_required(self, service):
        """Test detecting when settings changes require restart."""
        result = service.validate_settings(
            SettingsCategory.DATABASE,
            {
                "host": "new-db-host.com",  # This requires restart
            },
        )

        assert result.restart_required is True
        assert "host" in result.warnings

    def test_update_category_settings(self, service):
        """Test updating settings for a category."""
        update_request = SettingsUpdateRequest(
            updates={
                "smtp_host": "mail.example.com",
                "smtp_port": 465,
            },
            validate_only=False,
            reason="Testing settings update",
        )

        response = service.update_category_settings(
            SettingsCategory.EMAIL,
            update_request,
            user_id="test-admin",
            user_email="admin@example.com",
            ip_address="127.0.0.1",
            user_agent="pytest",
        )

        assert isinstance(response, SettingsResponse)

        # Check the values were updated
        smtp_host_field = next((f for f in response.fields if f.name == "smtp_host"), None)
        assert smtp_host_field.value == "mail.example.com"

        # Check audit log was created
        assert len(service._audit_logs) > 0
        audit_log = service._audit_logs[-1]
        assert audit_log.user_id == "test-admin"
        assert audit_log.category == SettingsCategory.EMAIL
        assert "smtp_host" in audit_log.changes

    def test_update_category_settings_validate_only(self, service):
        """Test updating settings in validate-only mode."""
        initial_audit_count = len(service._audit_logs)

        update_request = SettingsUpdateRequest(
            updates={"smtp_host": "mail.example.com"},
            validate_only=True,
        )

        response = service.update_category_settings(
            SettingsCategory.EMAIL,
            update_request,
            user_id="test-admin",
            user_email="admin@example.com",
        )

        # No audit log should be created in validate-only mode
        assert len(service._audit_logs) == initial_audit_count

    def test_create_and_restore_backup(self, service):
        """Test creating and restoring a settings backup."""
        # First, modify some settings
        update_request = SettingsUpdateRequest(
            updates={"smtp_host": "backup-test.example.com"},
            validate_only=False,
        )
        service.update_category_settings(
            SettingsCategory.EMAIL,
            update_request,
            user_id="test-admin",
            user_email="admin@example.com",
        )

        # Create a backup
        backup = service.create_backup(
            name="Test Backup",
            description="Testing backup functionality",
            categories=[SettingsCategory.EMAIL],
            user_id="test-admin",
        )

        assert backup.name == "Test Backup"
        assert SettingsCategory.EMAIL in backup.categories
        assert SettingsCategory.EMAIL.value in backup.settings_data

        # Modify settings again
        update_request2 = SettingsUpdateRequest(
            updates={"smtp_host": "different-host.example.com"},
            validate_only=False,
        )
        service.update_category_settings(
            SettingsCategory.EMAIL,
            update_request2,
            user_id="test-admin",
            user_email="admin@example.com",
        )

        # Restore from backup
        restored = service.restore_backup(
            backup.id, user_id="test-admin", user_email="admin@example.com"
        )

        assert SettingsCategory.EMAIL in restored

        # Check the value was restored
        email_settings = service.get_category_settings(SettingsCategory.EMAIL)
        smtp_host_field = next((f for f in email_settings.fields if f.name == "smtp_host"), None)
        assert smtp_host_field.value == "backup-test.example.com"

    def test_get_audit_logs(self, service):
        """Test retrieving audit logs."""
        # Create some audit activity
        for i in range(5):
            update_request = SettingsUpdateRequest(
                updates={"smtp_host": f"host-{i}.example.com"},
                validate_only=False,
            )
            service.update_category_settings(
                SettingsCategory.EMAIL,
                update_request,
                user_id=f"admin-{i}",
                user_email=f"admin-{i}@example.com",
            )

        # Get all audit logs
        logs = service.get_audit_logs()
        assert len(logs) >= 5

        # Filter by category
        email_logs = service.get_audit_logs(category=SettingsCategory.EMAIL)
        assert all(log.category == SettingsCategory.EMAIL for log in email_logs)

        # Filter by user
        user_logs = service.get_audit_logs(user_id="admin-0")
        assert all(log.user_id == "admin-0" for log in user_logs)

    def test_export_settings_json(self, service):
        """Test exporting settings to JSON format."""
        exported = service.export_settings(
            categories=[SettingsCategory.EMAIL, SettingsCategory.TENANT],
            include_sensitive=False,
            format="json",
        )

        assert isinstance(exported, str)

        import json

        data = json.loads(exported)
        assert "email" in data
        assert "tenant" in data

        # Check sensitive fields are masked
        assert "***MASKED***" in str(data["email"].get("smtp_password", ""))

    def test_export_settings_env(self, service):
        """Test exporting settings to environment variable format."""
        exported = service.export_settings(
            categories=[SettingsCategory.EMAIL], include_sensitive=True, format="env"
        )

        assert isinstance(exported, str)
        assert "EMAIL__SMTP_HOST=" in exported
        assert "EMAIL__SMTP_PORT=" in exported
        assert "EMAIL__USE_TLS=" in exported

    def test_sensitive_field_detection(self, service):
        """Test that sensitive fields are properly detected."""
        # Test various sensitive field patterns
        assert service._is_sensitive_field("password") is True
        assert service._is_sensitive_field("smtp_password") is True
        assert service._is_sensitive_field("secret_key") is True
        assert service._is_sensitive_field("api_key") is True
        assert service._is_sensitive_field("database_password") is True
        assert service._is_sensitive_field("token") is True

        # Non-sensitive fields
        assert service._is_sensitive_field("host") is False
        assert service._is_sensitive_field("port") is False
        assert service._is_sensitive_field("enabled") is False

    def test_tenant_settings_available(self, service):
        """Test that new tenant settings are available."""
        response = service.get_category_settings(SettingsCategory.TENANT)

        assert response.category == SettingsCategory.TENANT
        assert response.display_name == "Multi-tenancy"

        # Check expected fields exist
        field_names = [f.name for f in response.fields]
        assert "mode" in field_names
        assert "default_tenant_id" in field_names
        assert "require_tenant_header" in field_names
        assert "tenant_header_name" in field_names
        assert "strict_isolation" in field_names
        assert "max_users_per_tenant" in field_names

    def test_invalid_category_error(self, service):
        """Test error handling for invalid category."""
        with pytest.raises(ValueError) as exc_info:
            service.get_category_settings("invalid_category")

        assert "Invalid settings category" in str(exc_info.value)

    def test_invalid_field_update_error(self, service):
        """Test error handling for invalid field in update."""
        update_request = SettingsUpdateRequest(
            updates={"non_existent_field": "value"},
            validate_only=False,
        )

        with pytest.raises(ValueError) as exc_info:
            service.update_category_settings(
                SettingsCategory.EMAIL,
                update_request,
                user_id="test-admin",
                user_email="admin@example.com",
            )

        assert "Invalid field" in str(exc_info.value)
