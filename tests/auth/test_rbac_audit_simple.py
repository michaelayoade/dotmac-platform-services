"""
Simple tests for RBAC audit logging without complex imports
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.audit.models import ActivityType
from dotmac.platform.audit.service import AuditService
from dotmac.platform.auth.rbac_audit import rbac_audit_logger


@pytest.mark.asyncio
class TestRBACAuditLogging:
    """Test RBAC audit logging functionality"""

    async def test_log_role_assigned(self, async_db_session: AsyncSession):
        """Test that role assignment creates proper audit log"""
        user_id = str(uuid4())
        role_id = str(uuid4())
        assigned_by = str(uuid4())
        tenant_id = "test_tenant"

        # Log role assignment
        await rbac_audit_logger.log_role_assigned(
            user_id=user_id,
            role_name="test_role",
            role_id=role_id,
            assigned_by=assigned_by,
            tenant_id=tenant_id,
            metadata={"test": "data"}
        )

        # Check audit log
        result = await async_db_session.execute(
            text("""
                SELECT * FROM audit_activities
                WHERE activity_type = :activity_type
                AND resource_id = :resource_id
                ORDER BY timestamp DESC
                LIMIT 1
            """),
            {"activity_type": ActivityType.ROLE_ASSIGNED, "resource_id": user_id}
        )

        audit_log = result.fetchone()
        assert audit_log is not None
        assert audit_log.action == "assign_role"
        assert "test_role" in audit_log.description

    async def test_log_role_revoked(self, async_db_session: AsyncSession):
        """Test that role revocation creates proper audit log"""
        user_id = str(uuid4())
        role_id = str(uuid4())
        revoked_by = str(uuid4())
        tenant_id = "test_tenant"

        # Log role revocation
        await rbac_audit_logger.log_role_revoked(
            user_id=user_id,
            role_name="test_role",
            role_id=role_id,
            revoked_by=revoked_by,
            tenant_id=tenant_id,
            reason="Test revocation"
        )

        # Check audit log
        result = await async_db_session.execute(
            text("""
                SELECT * FROM audit_activities
                WHERE activity_type = :activity_type
                AND resource_id = :resource_id
                ORDER BY timestamp DESC
                LIMIT 1
            """),
            {"activity_type": ActivityType.ROLE_REVOKED, "resource_id": user_id}
        )

        audit_log = result.fetchone()
        assert audit_log is not None
        assert audit_log.action == "revoke_role"

    async def test_log_permission_granted(self, async_db_session: AsyncSession):
        """Test that permission grant creates proper audit log"""
        user_id = str(uuid4())
        permission_id = str(uuid4())
        granted_by = str(uuid4())
        tenant_id = "test_tenant"

        # Log permission grant
        await rbac_audit_logger.log_permission_granted(
            user_id=user_id,
            permission_name="test.permission",
            permission_id=permission_id,
            granted_by=granted_by,
            tenant_id=tenant_id,
            reason="Testing permission grant"
        )

        # Check audit log
        result = await async_db_session.execute(
            text("""
                SELECT * FROM audit_activities
                WHERE activity_type = :activity_type
                AND resource_id = :resource_id
                ORDER BY timestamp DESC
                LIMIT 1
            """),
            {"activity_type": ActivityType.PERMISSION_GRANTED, "resource_id": user_id}
        )

        audit_log = result.fetchone()
        assert audit_log is not None
        assert audit_log.action == "grant_permission"
        assert "test.permission" in audit_log.description

    async def test_log_permission_revoked(self, async_db_session: AsyncSession):
        """Test that permission revocation creates proper audit log"""
        user_id = str(uuid4())
        permission_id = str(uuid4())
        revoked_by = str(uuid4())
        tenant_id = "test_tenant"

        # Log permission revocation
        await rbac_audit_logger.log_permission_revoked(
            user_id=user_id,
            permission_name="test.permission",
            permission_id=permission_id,
            revoked_by=revoked_by,
            tenant_id=tenant_id,
            reason="Testing permission revocation"
        )

        # Check audit log
        result = await async_db_session.execute(
            text("""
                SELECT * FROM audit_activities
                WHERE activity_type = :activity_type
                AND resource_id = :resource_id
                ORDER BY timestamp DESC
                LIMIT 1
            """),
            {"activity_type": ActivityType.PERMISSION_REVOKED, "resource_id": user_id}
        )

        audit_log = result.fetchone()
        assert audit_log is not None
        assert audit_log.action == "revoke_permission"

    async def test_audit_service_filtering(self, async_db_session: AsyncSession):
        """Test filtering RBAC audit activities"""
        audit_service = AuditService(async_db_session)
        tenant_id = "filter_test_tenant"
        user_id = str(uuid4())

        # Create various RBAC audit activities
        activities = [
            (ActivityType.ROLE_CREATED, "create_role", "Created test role"),
            (ActivityType.ROLE_ASSIGNED, "assign_role", "Assigned test role"),
            (ActivityType.PERMISSION_GRANTED, "grant_permission", "Granted permission"),
        ]

        for activity_type, action, description in activities:
            await audit_service.log_activity(
                activity_type=activity_type,
                action=action,
                description=description,
                user_id=user_id,
                tenant_id=tenant_id
            )

        # Filter activities
        from dotmac.platform.audit.models import AuditFilterParams

        filters = AuditFilterParams(
            tenant_id=tenant_id,
            user_id=user_id,
            page=1,
            per_page=10
        )

        result = await audit_service.get_activities(filters)

        # Verify we got the activities
        assert len(result.activities) >= 3

        # Verify they are all RBAC activities
        rbac_types = [
            ActivityType.ROLE_CREATED,
            ActivityType.ROLE_ASSIGNED,
            ActivityType.PERMISSION_GRANTED
        ]

        for activity in result.activities:
            if activity.activity_type in rbac_types:
                assert activity.tenant_id == tenant_id
                assert activity.user_id == user_id