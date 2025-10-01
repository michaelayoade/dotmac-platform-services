"""
Test audit trail integration for admin settings service.
"""

import json
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import BaseModel

from dotmac.platform.admin.settings.models import (
    AuditLog,
    SettingsBackup,
    SettingsCategory,
    SettingsCategoryInfo,
    SettingsResponse,
    SettingsUpdateRequest,
    SettingsValidationResult,
    SettingField,
)
from dotmac.platform.admin.settings.service import SettingsManagementService


class TestSettingsAuditIntegration:
    """Test that settings service properly tracks audit information."""

    @pytest.fixture
    def service(self):
        """Create a settings management service instance."""
        return SettingsManagementService()

    def test_get_category_settings_without_updates(self, service):
        """Test that get_category_settings returns None for last_updated when no updates exist."""
        # Get settings for a category that hasn't been updated
        response = service.get_category_settings(SettingsCategory.DATABASE)

        assert response.category == SettingsCategory.DATABASE
        assert response.last_updated is None
        assert response.updated_by is None

    def test_get_category_settings_with_updates(self, service):
        """Test that get_category_settings returns audit info after updates."""
        # First make an update to create an audit log
        update_request = SettingsUpdateRequest(
            updates={"pool_size": 20},
            reason="Testing audit trail",
        )

        service.update_category_settings(
            category=SettingsCategory.DATABASE,
            update_request=update_request,
            user_id="test_user_123",
            user_email="test@example.com",
            ip_address="192.168.1.1",
            user_agent="TestAgent/1.0",
        )

        # Now get the settings and check audit info
        response = service.get_category_settings(SettingsCategory.DATABASE)

        assert response.category == SettingsCategory.DATABASE
        assert response.last_updated is not None
        assert response.updated_by == "test@example.com"

    def test_multiple_updates_returns_most_recent(self, service):
        """Test that multiple updates return the most recent audit info."""
        # Make first update
        update_request1 = SettingsUpdateRequest(
            updates={"pool_size": 100},
            reason="First update",
        )

        service.update_category_settings(
            category=SettingsCategory.DATABASE,
            update_request=update_request1,
            user_id="user1",
            user_email="user1@example.com",
        )

        # Make second update
        update_request2 = SettingsUpdateRequest(
            updates={"pool_size": 200},
            reason="Second update",
        )

        service.update_category_settings(
            category=SettingsCategory.DATABASE,
            update_request=update_request2,
            user_id="user2",
            user_email="user2@example.com",
        )

        # Get settings - should show most recent update
        response = service.get_category_settings(SettingsCategory.DATABASE)

        assert response.updated_by == "user2@example.com"
        # The second update should have a later timestamp
        audit_logs = service.get_audit_logs(category=SettingsCategory.DATABASE)
        assert len(audit_logs) == 2
        assert audit_logs[0].user_email == "user2@example.com"  # Most recent first
        assert audit_logs[1].user_email == "user1@example.com"

    def test_different_categories_have_independent_audit_info(self, service):
        """Test that different categories track their own audit information."""
        # Update DATABASE category
        db_update = SettingsUpdateRequest(
            updates={"pool_size": 100},
            reason="Update database",
        )

        service.update_category_settings(
            category=SettingsCategory.DATABASE,
            update_request=db_update,
            user_id="db_user",
            user_email="db_user@example.com",
        )

        # Update JWT category
        jwt_update = SettingsUpdateRequest(
            updates={"access_token_expire_minutes": 60},
            reason="Update JWT",
        )

        service.update_category_settings(
            category=SettingsCategory.JWT,
            update_request=jwt_update,
            user_id="jwt_user",
            user_email="jwt_user@example.com",
        )

        # Check DATABASE category
        db_response = service.get_category_settings(SettingsCategory.DATABASE)
        assert db_response.updated_by == "db_user@example.com"

        # Check JWT category
        jwt_response = service.get_category_settings(SettingsCategory.JWT)
        assert jwt_response.updated_by == "jwt_user@example.com"

        # Check a category that wasn't updated
        redis_response = service.get_category_settings(SettingsCategory.REDIS)
        assert redis_response.last_updated is None
        assert redis_response.updated_by is None

    def test_validate_only_updates_do_not_affect_audit(self, service):
        """Test that validation-only updates don't create audit logs."""
        # Make a real update first
        real_update = SettingsUpdateRequest(
            updates={"pool_size": 100},
            validate_only=False,
            reason="Real update",
        )

        service.update_category_settings(
            category=SettingsCategory.DATABASE,
            update_request=real_update,
            user_id="real_user",
            user_email="real@example.com",
        )

        # Now do a validation-only update
        validate_update = SettingsUpdateRequest(
            updates={"pool_size": 200},
            validate_only=True,
            reason="Validation only",
        )

        service.update_category_settings(
            category=SettingsCategory.DATABASE,
            update_request=validate_update,
            user_id="validate_user",
            user_email="validate@example.com",
        )

        # Check that audit info still shows the real update
        response = service.get_category_settings(SettingsCategory.DATABASE)
        assert response.updated_by == "real@example.com"  # Not validate@example.com

        # Verify only one audit log exists
        logs = service.get_audit_logs(category=SettingsCategory.DATABASE)
        assert len(logs) == 1
        assert logs[0].user_email == "real@example.com"

    def test_restore_backup_creates_audit_log(self, service):
        """Test that restoring from backup creates proper audit logs."""
        # First create a backup
        backup = service.create_backup(
            name="Test Backup",
            description="Testing backup restore audit",
            categories=[SettingsCategory.DATABASE],
            user_id="backup_creator",
        )

        # Restore the backup
        restored = service.restore_backup(
            backup_id=backup.id,
            user_id="restore_user",
            user_email="restore@example.com",
        )

        # Check that restore created an audit log
        response = service.get_category_settings(SettingsCategory.DATABASE)
        assert response.updated_by == "restore@example.com"

        # Verify audit log shows restore action
        logs = service.get_audit_logs(category=SettingsCategory.DATABASE)
        assert len(logs) >= 1
        latest_log = logs[0]
        assert latest_log.action == "restore"
        assert latest_log.user_email == "restore@example.com"
        assert "Restored from backup" in latest_log.reason

    def test_get_all_categories_includes_last_updated(self, service):
        """Test that get_all_categories includes last update time."""
        # Update a couple of categories
        service.update_category_settings(
            category=SettingsCategory.DATABASE,
            update_request=SettingsUpdateRequest(
                updates={"pool_size": 10},
                reason="Update DB",
            ),
            user_id="user1",
            user_email="user1@example.com",
        )

        service.update_category_settings(
            category=SettingsCategory.JWT,
            update_request=SettingsUpdateRequest(
                updates={"access_token_expire_minutes": 30},
                reason="Update JWT",
            ),
            user_id="user2",
            user_email="user2@example.com",
        )

        # Get all categories
        categories = service.get_all_categories()

        # Find the updated categories
        db_info = next(c for c in categories if c.category == SettingsCategory.DATABASE)
        jwt_info = next(c for c in categories if c.category == SettingsCategory.JWT)
        redis_info = next(c for c in categories if c.category == SettingsCategory.REDIS)

        # Check that updated categories have timestamps
        assert db_info.last_updated is not None
        assert jwt_info.last_updated is not None

        # Check that non-updated category has no timestamp
        assert redis_info.last_updated is None

    def test_audit_log_contains_all_required_fields(self, service):
        """Test that audit logs contain all required information."""
        update_request = SettingsUpdateRequest(
            updates={"pool_size": 15},
            reason="Testing complete audit log",
        )

        before_update = datetime.now(timezone.utc)

        service.update_category_settings(
            category=SettingsCategory.DATABASE,
            update_request=update_request,
            user_id="test_user_456",
            user_email="complete@example.com",
            ip_address="10.0.0.1",
            user_agent="Mozilla/5.0 TestBrowser",
        )

        after_update = datetime.now(timezone.utc)

        # Get the audit log
        logs = service.get_audit_logs(category=SettingsCategory.DATABASE, limit=1)
        assert len(logs) == 1

        log = logs[0]

        # Verify all fields are present
        assert log.id is not None
        assert before_update <= log.timestamp <= after_update
        assert log.user_id == "test_user_456"
        assert log.user_email == "complete@example.com"
        assert log.category == SettingsCategory.DATABASE
        assert log.action == "update"
        assert log.reason == "Testing complete audit log"
        assert log.ip_address == "10.0.0.1"
        assert log.user_agent == "Mozilla/5.0 TestBrowser"

        # Verify changes are tracked
        assert "pool_size" in log.changes
        assert "old" in log.changes["pool_size"]
        assert "new" in log.changes["pool_size"]
        assert log.changes["pool_size"]["new"] == 15

    def test_get_audit_logs_filtering(self, service):
        """Test that audit logs can be filtered properly."""
        # Create updates for different categories and users
        service.update_category_settings(
            category=SettingsCategory.DATABASE,
            update_request=SettingsUpdateRequest(updates={"pool_size": 100}),
            user_id="user1",
            user_email="user1@example.com",
        )

        service.update_category_settings(
            category=SettingsCategory.JWT,
            update_request=SettingsUpdateRequest(updates={"access_token_expire_minutes": 30}),
            user_id="user1",
            user_email="user1@example.com",
        )

        service.update_category_settings(
            category=SettingsCategory.DATABASE,
            update_request=SettingsUpdateRequest(updates={"pool_size": 200}),
            user_id="user2",
            user_email="user2@example.com",
        )

        # Test filtering by category
        db_logs = service.get_audit_logs(category=SettingsCategory.DATABASE)
        assert len(db_logs) == 2
        for log in db_logs:
            assert log.category == SettingsCategory.DATABASE

        # Test filtering by user
        user1_logs = service.get_audit_logs(user_id="user1")
        assert len(user1_logs) == 2
        for log in user1_logs:
            assert log.user_id == "user1"

        # Test filtering by both
        user1_db_logs = service.get_audit_logs(
            category=SettingsCategory.DATABASE,
            user_id="user1"
        )
        assert len(user1_db_logs) == 1
        assert user1_db_logs[0].user_id == "user1"
        assert user1_db_logs[0].category == SettingsCategory.DATABASE

    def test_export_includes_last_update_metadata(self, service):
        """Test that exported settings include update metadata."""
        # Make an update
        service.update_category_settings(
            category=SettingsCategory.DATABASE,
            update_request=SettingsUpdateRequest(
                updates={"pool_size": 10},
                reason="Pre-export update"
            ),
            user_id="exporter",
            user_email="export@example.com",
        )

        # Export settings as JSON
        exported = service.export_settings(
            categories=[SettingsCategory.DATABASE],
            include_sensitive=False,
            format="json"
        )

        # Parse the export
        data = json.loads(exported)
        assert "database" in data

        # Get category info to verify last_updated is tracked
        response = service.get_category_settings(SettingsCategory.DATABASE)
        assert response.last_updated is not None
        assert response.updated_by == "export@example.com"