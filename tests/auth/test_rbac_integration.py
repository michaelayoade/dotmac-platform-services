"""
Integration tests for RBAC system including audit logging
"""

import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.auth.models import (
    Role, Permission, PermissionCategory,
    user_roles, role_permissions, user_permissions
)
from dotmac.platform.user_management.models import User
from dotmac.platform.auth.rbac_service import RBACService
from dotmac.platform.auth.rbac_audit import rbac_audit_logger
from dotmac.platform.audit.models import AuditActivity, ActivityType
from dotmac.platform.audit.service import AuditService


@pytest.mark.asyncio
class TestRBACIntegration:
    """Integration tests for RBAC system"""

    async def test_role_assignment_with_audit(self, async_session: AsyncSession):
        """Test role assignment creates audit log"""
        # Create test user
        user = User(
            id=uuid4(),
            username="test_user",
            email="test@example.com",
            is_active=True
        )
        async_session.add(user)

        # Create test role with permissions
        role = Role(
            id=uuid4(),
            name="test_role",
            display_name="Test Role",
            description="Test role for integration test",
            priority=10,
            is_active=True
        )
        async_session.add(role)

        # Create test permission
        permission = Permission(
            id=uuid4(),
            name="test.read",
            display_name="Test Read",
            description="Test read permission",
            category=PermissionCategory.SYSTEM,
            is_active=True
        )
        async_session.add(permission)
        await async_session.commit()

        # Add permission to role
        await async_session.execute(
            role_permissions.insert().values(
                role_id=role.id,
                permission_id=permission.id,
                granted_at=datetime.now(timezone.utc)
            )
        )
        await async_session.commit()

        # Create RBAC service
        rbac_service = RBACService(async_session)
        audit_service = AuditService(async_session)

        # Assign role to user
        granted_by = uuid4()
        await rbac_service.assign_role_to_user(
            user_id=user.id,
            role_name="test_role",
            granted_by=granted_by,
            metadata={"test": "data"}
        )

        # Verify role assignment
        result = await async_session.execute(
            select(user_roles).where(
                user_roles.c.user_id == user.id,
                user_roles.c.role_id == role.id
            )
        )
        assignment = result.first()
        assert assignment is not None
        assert assignment.granted_by == granted_by

        # Verify user permissions
        user_perms = await rbac_service.get_user_permissions(user.id)
        assert "test.read" in user_perms

        # Verify audit log was created
        result = await async_session.execute(
            select(AuditActivity).where(
                AuditActivity.activity_type == ActivityType.ROLE_ASSIGNED,
                AuditActivity.resource_id == str(user.id)
            )
        )
        audit_log = result.scalar_one_or_none()
        assert audit_log is not None
        assert audit_log.action == "assign_role"
        assert "test_role" in audit_log.description
        assert audit_log.details["role_name"] == "test_role"
        assert audit_log.details["metadata"] == {"test": "data"}

    async def test_role_revocation_with_audit(self, async_session: AsyncSession):
        """Test role revocation creates audit log"""
        # Create test user
        user = User(
            id=uuid4(),
            username="revoke_user",
            email="revoke@example.com",
            is_active=True
        )
        async_session.add(user)

        # Create test role
        role = Role(
            id=uuid4(),
            name="revoke_role",
            display_name="Revoke Role",
            description="Role to be revoked",
            priority=10,
            is_active=True
        )
        async_session.add(role)
        await async_session.commit()

        # Assign role first
        await async_session.execute(
            user_roles.insert().values(
                user_id=user.id,
                role_id=role.id,
                granted_by=uuid4(),
                granted_at=datetime.now(timezone.utc)
            )
        )
        await async_session.commit()

        # Create RBAC service
        rbac_service = RBACService(async_session)

        # Revoke role
        revoked_by = uuid4()
        await rbac_service.revoke_role_from_user(
            user_id=user.id,
            role_name="revoke_role",
            revoked_by=revoked_by,
            reason="Test revocation"
        )

        # Verify role was revoked
        result = await async_session.execute(
            select(user_roles).where(
                user_roles.c.user_id == user.id,
                user_roles.c.role_id == role.id
            )
        )
        assignment = result.first()
        assert assignment is None

        # Verify audit log was created
        result = await async_session.execute(
            select(AuditActivity).where(
                AuditActivity.activity_type == ActivityType.ROLE_REVOKED,
                AuditActivity.resource_id == str(user.id)
            ).order_by(AuditActivity.timestamp.desc())
        )
        audit_log = result.scalar_one_or_none()
        assert audit_log is not None
        assert audit_log.action == "revoke_role"
        assert "revoke_role" in audit_log.description
        assert audit_log.details["reason"] == "Test revocation"

    async def test_permission_grant_with_audit(self, async_session: AsyncSession):
        """Test direct permission grant creates audit log"""
        # Create test user
        user = User(
            id=uuid4(),
            username="perm_user",
            email="perm@example.com",
            is_active=True
        )
        async_session.add(user)

        # Create test permission
        permission = Permission(
            id=uuid4(),
            name="special.permission",
            display_name="Special Permission",
            description="Special direct permission",
            category=PermissionCategory.SYSTEM,
            is_active=True
        )
        async_session.add(permission)
        await async_session.commit()

        # Create RBAC service
        rbac_service = RBACService(async_session)

        # Grant permission directly
        granted_by = uuid4()
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        await rbac_service.grant_permission_to_user(
            user_id=user.id,
            permission_name="special.permission",
            granted_by=granted_by,
            expires_at=expires_at,
            reason="Temporary elevated access"
        )

        # Verify permission grant
        result = await async_session.execute(
            select(user_permissions).where(
                user_permissions.c.user_id == user.id,
                user_permissions.c.permission_id == permission.id
            )
        )
        grant = result.first()
        assert grant is not None
        assert grant.granted == True
        assert grant.reason == "Temporary elevated access"

        # Verify user has permission
        user_perms = await rbac_service.get_user_permissions(user.id)
        assert "special.permission" in user_perms

        # Verify audit log was created
        result = await async_session.execute(
            select(AuditActivity).where(
                AuditActivity.activity_type == ActivityType.PERMISSION_GRANTED,
                AuditActivity.resource_id == str(user.id)
            ).order_by(AuditActivity.timestamp.desc())
        )
        audit_log = result.scalar_one_or_none()
        assert audit_log is not None
        assert audit_log.action == "grant_permission"
        assert "special.permission" in audit_log.description
        assert audit_log.details["reason"] == "Temporary elevated access"
        assert audit_log.details["expires_at"] == expires_at.isoformat()

    async def test_permission_inheritance(self, async_session: AsyncSession):
        """Test permission inheritance through role hierarchy"""
        # Create parent role
        parent_role = Role(
            id=uuid4(),
            name="parent_role",
            display_name="Parent Role",
            description="Parent role with permissions",
            priority=20,
            is_active=True
        )
        async_session.add(parent_role)

        # Create child role
        child_role = Role(
            id=uuid4(),
            name="child_role",
            display_name="Child Role",
            description="Child role inheriting permissions",
            priority=10,
            parent_id=parent_role.id,
            is_active=True
        )
        async_session.add(child_role)

        # Create permissions
        parent_perm = Permission(
            id=uuid4(),
            name="parent.permission",
            display_name="Parent Permission",
            category=PermissionCategory.SYSTEM,
            is_active=True
        )
        child_perm = Permission(
            id=uuid4(),
            name="child.permission",
            display_name="Child Permission",
            category=PermissionCategory.SYSTEM,
            is_active=True
        )
        async_session.add(parent_perm)
        async_session.add(child_perm)
        await async_session.commit()

        # Add permissions to roles
        await async_session.execute(
            role_permissions.insert().values([
                {
                    "role_id": parent_role.id,
                    "permission_id": parent_perm.id,
                    "granted_at": datetime.now(timezone.utc)
                },
                {
                    "role_id": child_role.id,
                    "permission_id": child_perm.id,
                    "granted_at": datetime.now(timezone.utc)
                }
            ])
        )

        # Create user and assign child role
        user = User(
            id=uuid4(),
            username="inherit_user",
            email="inherit@example.com",
            is_active=True
        )
        async_session.add(user)
        await async_session.commit()

        # Create RBAC service
        rbac_service = RBACService(async_session)

        # Assign child role to user
        await rbac_service.assign_role_to_user(
            user_id=user.id,
            role_name="child_role",
            granted_by=uuid4()
        )

        # Verify user has both parent and child permissions
        user_perms = await rbac_service.get_user_permissions(user.id)
        assert "parent.permission" in user_perms  # Inherited from parent
        assert "child.permission" in user_perms  # Direct from child role

    async def test_wildcard_permissions(self, async_session: AsyncSession):
        """Test wildcard permission matching"""
        # Create role with wildcard permission
        admin_role = Role(
            id=uuid4(),
            name="wildcard_admin",
            display_name="Wildcard Admin",
            description="Admin with wildcard permissions",
            priority=100,
            is_active=True
        )
        async_session.add(admin_role)

        # Create various permissions
        permissions = [
            Permission(
                id=uuid4(),
                name="users.read",
                display_name="Read Users",
                category=PermissionCategory.USERS,
                is_active=True
            ),
            Permission(
                id=uuid4(),
                name="users.write",
                display_name="Write Users",
                category=PermissionCategory.USERS,
                is_active=True
            ),
            Permission(
                id=uuid4(),
                name="billing.read",
                display_name="Read Billing",
                category=PermissionCategory.BILLING,
                is_active=True
            )
        ]
        for perm in permissions:
            async_session.add(perm)
        await async_session.commit()

        # Create RBAC service
        rbac_service = RBACService(async_session)

        # Create user and verify wildcard matching
        user = User(
            id=uuid4(),
            username="wildcard_user",
            email="wildcard@example.com",
            is_active=True
        )
        async_session.add(user)
        await async_session.commit()

        # Test category wildcard (users.*)
        assert await rbac_service.check_permission_wildcard("users.*", "users.read")
        assert await rbac_service.check_permission_wildcard("users.*", "users.write")
        assert not await rbac_service.check_permission_wildcard("users.*", "billing.read")

        # Test global wildcard (*)
        assert await rbac_service.check_permission_wildcard("*", "users.read")
        assert await rbac_service.check_permission_wildcard("*", "billing.read")
        assert await rbac_service.check_permission_wildcard("*", "any.permission")

    async def test_permission_expiration(self, async_session: AsyncSession):
        """Test expired permissions are not included"""
        # Create user
        user = User(
            id=uuid4(),
            username="expire_user",
            email="expire@example.com",
            is_active=True
        )
        async_session.add(user)

        # Create permission
        permission = Permission(
            id=uuid4(),
            name="temp.permission",
            display_name="Temporary Permission",
            category=PermissionCategory.SYSTEM,
            is_active=True
        )
        async_session.add(permission)
        await async_session.commit()

        # Grant permission with past expiration
        past_time = datetime.now(timezone.utc) - timedelta(days=1)
        await async_session.execute(
            user_permissions.insert().values(
                user_id=user.id,
                permission_id=permission.id,
                granted=True,
                granted_by=uuid4(),
                expires_at=past_time,
                granted_at=datetime.now(timezone.utc) - timedelta(days=2)
            )
        )
        await async_session.commit()

        # Create RBAC service
        rbac_service = RBACService(async_session)

        # Verify expired permission is not included
        user_perms = await rbac_service.get_user_permissions(user.id, include_expired=False)
        assert "temp.permission" not in user_perms

        # Verify expired permission IS included when requested
        user_perms = await rbac_service.get_user_permissions(user.id, include_expired=True)
        assert "temp.permission" in user_perms

    async def test_audit_activity_filtering(self, async_session: AsyncSession):
        """Test filtering audit activities by RBAC activity types"""
        audit_service = AuditService(async_session)

        # Create multiple RBAC audit activities
        activities = [
            ActivityType.ROLE_CREATED,
            ActivityType.ROLE_ASSIGNED,
            ActivityType.PERMISSION_GRANTED,
            ActivityType.ROLE_REVOKED,
            ActivityType.PERMISSION_REVOKED
        ]

        user_id = str(uuid4())
        tenant_id = "test_tenant"

        for activity_type in activities:
            await audit_service.log_activity(
                activity_type=activity_type,
                action=f"test_{activity_type}",
                description=f"Test {activity_type}",
                user_id=user_id,
                tenant_id=tenant_id
            )

        # Filter by RBAC activity types
        from dotmac.platform.audit.models import AuditFilterParams

        filters = AuditFilterParams(
            tenant_id=tenant_id,
            page=1,
            per_page=10
        )

        result = await audit_service.get_activities(filters)

        # Verify we got all RBAC activities
        rbac_activities = [a for a in result.activities
                          if a.activity_type in [
                              ActivityType.ROLE_CREATED,
                              ActivityType.ROLE_ASSIGNED,
                              ActivityType.PERMISSION_GRANTED,
                              ActivityType.ROLE_REVOKED,
                              ActivityType.PERMISSION_REVOKED
                          ]]

        assert len(rbac_activities) >= 5  # At least our 5 activities