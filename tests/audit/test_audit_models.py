"""
Tests for audit models and database operations.
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from dotmac.platform.audit.models import (
    AuditActivity,
    AuditActivityCreate,
    AuditActivityResponse,
    ActivityType,
    ActivitySeverity,
)
from dotmac.platform.db import Base


class TestAuditModels:
    """Test audit model definitions and validation."""

    def test_audit_activity_model_creation(self):
        """Test creating an AuditActivity model instance."""
        activity = AuditActivity(
            id=uuid4(),
            activity_type=ActivityType.USER_LOGIN,
            severity=ActivitySeverity.LOW,
            user_id="user123",
            tenant_id="tenant456",
            action="login",
            description="User logged in",
            timestamp=datetime.now(timezone.utc),
        )

        assert activity.activity_type == ActivityType.USER_LOGIN
        assert activity.severity == ActivitySeverity.LOW
        assert activity.user_id == "user123"
        assert activity.tenant_id == "tenant456"

    def test_audit_activity_create_validation(self):
        """Test AuditActivityCreate Pydantic model validation."""
        # Valid data
        valid_data = AuditActivityCreate(
            activity_type=ActivityType.SECRET_CREATED,
            severity=ActivitySeverity.MEDIUM,
            user_id="user123",
            tenant_id="tenant456",
            action="create_secret",
            description="Created new secret",
            resource_type="secret",
            resource_id="secret/path/key",
        )

        assert valid_data.activity_type == ActivityType.SECRET_CREATED
        assert valid_data.severity == ActivitySeverity.MEDIUM

        # Test default severity
        default_severity = AuditActivityCreate(
            activity_type=ActivityType.API_REQUEST,
            action="api_call",
            description="API request",
        )
        assert default_severity.severity == ActivitySeverity.LOW

    def test_audit_activity_response_model(self):
        """Test AuditActivityResponse model serialization."""
        activity = AuditActivity(
            id=uuid4(),
            activity_type=ActivityType.FILE_UPLOADED,
            severity=ActivitySeverity.LOW,
            user_id="user123",
            tenant_id="tenant456",
            action="upload",
            description="File uploaded",
            timestamp=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        response = AuditActivityResponse.model_validate(activity)
        assert response.activity_type == ActivityType.FILE_UPLOADED
        assert response.user_id == "user123"

    def test_activity_type_enum_values(self):
        """Test ActivityType enum contains expected values."""
        expected_types = [
            "user.login",
            "user.logout",
            "user.created",
            "secret.created",
            "secret.accessed",
            "file.uploaded",
            "api.request",
        ]

        for expected in expected_types:
            assert expected in [t.value for t in ActivityType]

    def test_severity_enum_values(self):
        """Test ActivitySeverity enum values."""
        assert ActivitySeverity.LOW == "low"
        assert ActivitySeverity.MEDIUM == "medium"
        assert ActivitySeverity.HIGH == "high"
        assert ActivitySeverity.CRITICAL == "critical"

    @pytest.mark.asyncio
    async def test_audit_activity_database_constraints(self, async_db_session):
        """Test database constraints on audit_activities table."""
        # Test required fields
        with pytest.raises(Exception):  # Should fail without required fields
            activity = AuditActivity(
                id=uuid4(),
                activity_type=ActivityType.USER_LOGIN,
                # Missing required tenant_id, action, description
            )
            async_db_session.add(activity)
            await async_db_session.commit()

        await async_db_session.rollback()

        # Test with all required fields
        activity = AuditActivity(
            id=uuid4(),
            activity_type=ActivityType.USER_LOGIN,
            severity=ActivitySeverity.LOW,
            tenant_id="tenant123",  # Required by StrictTenantMixin
            action="login",
            description="User login",
            timestamp=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        async_db_session.add(activity)
        await async_db_session.commit()

        assert activity.id is not None