"""
End-to-end tests for tenant management.

Tests cover tenant CRUD operations, settings, invitations, and bulk operations.
"""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.auth.core import hash_password
from dotmac.platform.tenant.models import Tenant, TenantInvitation, TenantSetting
from dotmac.platform.user_management.models import User

pytestmark = [pytest.mark.asyncio, pytest.mark.e2e]


# ============================================================================
# Fixtures for Tenant E2E Tests
# ============================================================================


@pytest_asyncio.fixture
async def test_tenant(e2e_db_session: AsyncSession):
    """Create a test tenant in the database."""
    tenant = Tenant(
        id=str(uuid.uuid4()),
        name=f"Test Org {uuid.uuid4().hex[:6]}",
        slug=f"test-org-{uuid.uuid4().hex[:8]}",
        email=f"contact_{uuid.uuid4().hex[:6]}@example.com",
        plan_type="professional",
        status="active",
        is_active=True,
        max_users=50,
        max_api_calls_per_month=100000,
        max_storage_gb=100,
    )
    e2e_db_session.add(tenant)
    await e2e_db_session.commit()
    await e2e_db_session.refresh(tenant)
    return tenant


@pytest_asyncio.fixture
async def multiple_tenants(e2e_db_session: AsyncSession):
    """Create multiple tenants for listing and bulk tests."""
    tenants = []
    statuses = ["active", "trial", "suspended", "active", "trial"]
    for i, status in enumerate(statuses):
        tenant = Tenant(
            id=str(uuid.uuid4()),
            name=f"Org {i} {uuid.uuid4().hex[:4]}",
            slug=f"org-{i}-{uuid.uuid4().hex[:8]}",
            email=f"org{i}_{uuid.uuid4().hex[:4]}@example.com",
            plan_type="starter" if i < 2 else "professional",
            status=status,
            is_active=status != "suspended",
            max_users=10 + (i * 10),
            max_api_calls_per_month=10000 * (i + 1),
        )
        e2e_db_session.add(tenant)
        tenants.append(tenant)

    await e2e_db_session.commit()
    for tenant in tenants:
        await e2e_db_session.refresh(tenant)
    return tenants


@pytest_asyncio.fixture
async def tenant_with_settings(e2e_db_session: AsyncSession, test_tenant: Tenant):
    """Create a tenant with settings."""
    settings = [
        TenantSetting(
            tenant_id=test_tenant.id,
            key="feature_flag_1",
            value="enabled",
            value_type="string",
        ),
        TenantSetting(
            tenant_id=test_tenant.id,
            key="max_upload_size",
            value="100",
            value_type="int",
        ),
    ]
    for setting in settings:
        e2e_db_session.add(setting)
    await e2e_db_session.commit()
    for setting in settings:
        await e2e_db_session.refresh(setting)
    return test_tenant, settings


@pytest_asyncio.fixture
async def tenant_invitation(e2e_db_session: AsyncSession, test_tenant: Tenant):
    """Create a pending tenant invitation."""
    invitation = TenantInvitation(
        id=str(uuid.uuid4()),
        tenant_id=test_tenant.id,
        email=f"invited_{uuid.uuid4().hex[:8]}@example.com",
        role="member",
        invited_by=str(uuid.uuid4()),
        token=uuid.uuid4().hex,
        status="pending",
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    e2e_db_session.add(invitation)
    await e2e_db_session.commit()
    await e2e_db_session.refresh(invitation)
    return invitation


# ============================================================================
# Tenant CRUD Tests
# ============================================================================


class TestTenantCRUDE2E:
    """End-to-end tests for tenant CRUD operations."""

    async def test_create_tenant_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test creating a tenant with valid data."""
        unique_id = uuid.uuid4().hex[:8]
        tenant_data = {
            "name": f"New Organization {unique_id}",
            "slug": f"new-org-{unique_id}",
            "email": f"contact_{unique_id}@example.com",
            "plan_type": "professional",
        }

        response = await async_client.post(
            "/api/v1/tenants",
            json=tenant_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == tenant_data["name"]
        assert data["slug"] == tenant_data["slug"]
        assert "id" in data

    async def test_create_tenant_duplicate_slug(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_tenant: Tenant,
    ):
        """Test creating a tenant with duplicate slug."""
        tenant_data = {
            "name": "Different Name",
            "slug": test_tenant.slug,
            "email": f"different_{uuid.uuid4().hex[:8]}@example.com",
            "plan_type": "starter",
        }

        response = await async_client.post(
            "/api/v1/tenants",
            json=tenant_data,
            headers=auth_headers,
        )

        assert response.status_code in [400, 409]

    async def test_list_tenants(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        multiple_tenants: list[Tenant],
    ):
        """Test listing all tenants."""
        response = await async_client.get(
            "/api/v1/tenants",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "tenants" in data
        assert "total" in data
        assert isinstance(data["tenants"], list)

    async def test_list_tenants_with_pagination(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        multiple_tenants: list[Tenant],
    ):
        """Test listing tenants with pagination."""
        response = await async_client.get(
            "/api/v1/tenants?skip=0&limit=2",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["tenants"]) <= 2

    async def test_get_current_tenant(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test getting current user's tenant."""
        response = await async_client.get(
            "/api/v1/tenants/current",
            headers=auth_headers,
        )

        # May return null if no tenant associated
        assert response.status_code == 200

    async def test_get_tenant_by_id(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_tenant: Tenant,
    ):
        """Test getting a tenant by ID."""
        response = await async_client.get(
            f"/api/v1/tenants/{test_tenant.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_tenant.id
        assert data["name"] == test_tenant.name

    async def test_get_tenant_not_found(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test getting a non-existent tenant."""
        fake_id = str(uuid.uuid4())
        response = await async_client.get(
            f"/api/v1/tenants/{fake_id}",
            headers=auth_headers,
        )

        assert response.status_code == 404

    async def test_get_tenant_by_slug(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_tenant: Tenant,
    ):
        """Test getting a tenant by slug."""
        response = await async_client.get(
            f"/api/v1/tenants/slug/{test_tenant.slug}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["slug"] == test_tenant.slug

    async def test_update_tenant_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_tenant: Tenant,
    ):
        """Test updating a tenant."""
        update_data = {
            "name": "Updated Organization Name",
        }

        response = await async_client.patch(
            f"/api/v1/tenants/{test_tenant.id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Organization Name"

    async def test_delete_tenant_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_tenant: Tenant,
    ):
        """Test deleting a tenant (soft delete)."""
        response = await async_client.delete(
            f"/api/v1/tenants/{test_tenant.id}",
            headers=auth_headers,
        )

        assert response.status_code == 204

    async def test_restore_tenant(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        e2e_db_session: AsyncSession,
    ):
        """Test restoring a deleted tenant."""
        # Create a soft-deleted tenant
        tenant = Tenant(
            id=str(uuid.uuid4()),
            name=f"Deleted Org {uuid.uuid4().hex[:6]}",
            slug=f"deleted-org-{uuid.uuid4().hex[:8]}",
            email=f"deleted_{uuid.uuid4().hex[:6]}@example.com",
            plan_type="starter",
            status="cancelled",
            is_active=False,
            deleted_at=datetime.now(UTC),
        )
        e2e_db_session.add(tenant)
        await e2e_db_session.commit()
        await e2e_db_session.refresh(tenant)

        response = await async_client.post(
            f"/api/v1/tenants/{tenant.id}/restore",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is True


# ============================================================================
# Tenant Settings Tests
# ============================================================================


class TestTenantSettingsE2E:
    """End-to-end tests for tenant settings management."""

    async def test_list_tenant_settings(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        tenant_with_settings: tuple,
    ):
        """Test listing all tenant settings."""
        tenant, settings = tenant_with_settings

        response = await async_client.get(
            f"/api/v1/tenants/{tenant.id}/settings",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_get_specific_setting(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        tenant_with_settings: tuple,
    ):
        """Test getting a specific setting by key."""
        tenant, settings = tenant_with_settings

        response = await async_client.get(
            f"/api/v1/tenants/{tenant.id}/settings/feature_flag_1",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["key"] == "feature_flag_1"

    async def test_get_nonexistent_setting(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_tenant: Tenant,
    ):
        """Test getting a non-existent setting."""
        response = await async_client.get(
            f"/api/v1/tenants/{test_tenant.id}/settings/nonexistent_key",
            headers=auth_headers,
        )

        assert response.status_code == 404

    async def test_create_setting(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_tenant: Tenant,
    ):
        """Test creating a new tenant setting."""
        setting_data = {
            "key": f"new_setting_{uuid.uuid4().hex[:8]}",
            "value": "test_value",
            "value_type": "string",
        }

        response = await async_client.post(
            f"/api/v1/tenants/{test_tenant.id}/settings",
            json=setting_data,
            headers=auth_headers,
        )

        assert response.status_code in [200, 201]
        data = response.json()
        assert data["key"] == setting_data["key"]

    async def test_update_setting(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        tenant_with_settings: tuple,
    ):
        """Test updating an existing setting."""
        tenant, settings = tenant_with_settings

        setting_data = {
            "key": "feature_flag_1",
            "value": "disabled",
            "value_type": "string",
        }

        response = await async_client.post(
            f"/api/v1/tenants/{tenant.id}/settings",
            json=setting_data,
            headers=auth_headers,
        )

        assert response.status_code in [200, 201]
        data = response.json()
        assert data["value"] == "disabled"

    async def test_delete_setting(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        tenant_with_settings: tuple,
    ):
        """Test deleting a tenant setting."""
        tenant, settings = tenant_with_settings

        response = await async_client.delete(
            f"/api/v1/tenants/{tenant.id}/settings/feature_flag_1",
            headers=auth_headers,
        )

        assert response.status_code == 204


# ============================================================================
# Tenant Invitations Tests
# ============================================================================


class TestTenantInvitationsE2E:
    """End-to-end tests for tenant invitation management."""

    async def test_create_invitation(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_tenant: Tenant,
    ):
        """Test creating a tenant invitation."""
        invitation_data = {
            "email": f"invitee_{uuid.uuid4().hex[:8]}@example.com",
            "role": "member",
        }

        response = await async_client.post(
            f"/api/v1/tenants/{test_tenant.id}/invitations",
            json=invitation_data,
            headers=auth_headers,
        )

        assert response.status_code in [200, 201]
        data = response.json()
        assert data["email"] == invitation_data["email"]

    async def test_list_invitations(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_tenant: Tenant,
        tenant_invitation: TenantInvitation,
    ):
        """Test listing tenant invitations."""
        response = await async_client.get(
            f"/api/v1/tenants/{test_tenant.id}/invitations",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_list_invitations_filter_by_status(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_tenant: Tenant,
        tenant_invitation: TenantInvitation,
    ):
        """Test listing invitations filtered by status."""
        response = await async_client.get(
            f"/api/v1/tenants/{test_tenant.id}/invitations?status=pending",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_accept_invitation_invalid_token(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test accepting an invitation with invalid token."""
        response = await async_client.post(
            "/api/v1/tenants/invitations/accept",
            json={"token": "invalid-token"},
            headers=auth_headers,
        )

        assert response.status_code in [400, 404]

    async def test_revoke_invitation(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_tenant: Tenant,
        tenant_invitation: TenantInvitation,
    ):
        """Test revoking a tenant invitation."""
        response = await async_client.post(
            f"/api/v1/tenants/{test_tenant.id}/invitations/{tenant_invitation.id}/revoke",
            headers=auth_headers,
        )

        assert response.status_code == 200


# ============================================================================
# Tenant Usage Tests
# ============================================================================


class TestTenantUsageE2E:
    """End-to-end tests for tenant usage tracking."""

    async def test_record_usage(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_tenant: Tenant,
    ):
        """Test recording tenant usage."""
        usage_data = {
            "api_calls": 100,
            "storage_bytes": 1024000,
            "users_active": 5,
        }

        response = await async_client.post(
            f"/api/v1/tenants/{test_tenant.id}/usage",
            json=usage_data,
            headers=auth_headers,
        )

        assert response.status_code in [200, 201]

    async def test_get_usage_history(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_tenant: Tenant,
    ):
        """Test getting tenant usage history."""
        response = await async_client.get(
            f"/api/v1/tenants/{test_tenant.id}/usage",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_get_tenant_stats(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_tenant: Tenant,
    ):
        """Test getting tenant statistics."""
        response = await async_client.get(
            f"/api/v1/tenants/{test_tenant.id}/stats",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data or "api_calls" in data or isinstance(data, dict)


# ============================================================================
# Tenant Bulk Operations Tests
# ============================================================================


class TestTenantBulkOperationsE2E:
    """End-to-end tests for bulk tenant operations."""

    async def test_bulk_status_update(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        multiple_tenants: list[Tenant],
    ):
        """Test bulk updating tenant status."""
        tenant_ids = [t.id for t in multiple_tenants[:2]]

        response = await async_client.post(
            "/api/v1/tenants/bulk/status",
            json={
                "tenant_ids": tenant_ids,
                "status": "suspended",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "success_count" in data or "updated" in data

    async def test_bulk_delete(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        multiple_tenants: list[Tenant],
    ):
        """Test bulk deleting tenants."""
        tenant_ids = [t.id for t in multiple_tenants[:2]]

        response = await async_client.post(
            "/api/v1/tenants/bulk/delete",
            json={
                "tenant_ids": tenant_ids,
                "permanent": False,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "success_count" in data or "deleted" in data


# ============================================================================
# Tenant Features/Metadata Tests
# ============================================================================


class TestTenantFeaturesMetadataE2E:
    """End-to-end tests for tenant features and metadata."""

    async def test_update_features(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_tenant: Tenant,
    ):
        """Test updating tenant features."""
        features_data = {
            "features": {
                "advanced_analytics": True,
                "api_access": True,
                "custom_branding": False,
            },
        }

        response = await async_client.patch(
            f"/api/v1/tenants/{test_tenant.id}/features",
            json=features_data,
            headers=auth_headers,
        )

        assert response.status_code == 200

    async def test_update_metadata(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_tenant: Tenant,
    ):
        """Test updating tenant metadata."""
        metadata_data = {
            "metadata": {
                "industry": "Technology",
                "company_size": "50-100",
                "referral_source": "google",
            },
        }

        response = await async_client.patch(
            f"/api/v1/tenants/{test_tenant.id}/metadata",
            json=metadata_data,
            headers=auth_headers,
        )

        assert response.status_code == 200


# ============================================================================
# Tenant Members Tests
# ============================================================================


class TestTenantMembersE2E:
    """End-to-end tests for tenant member listing."""

    async def test_list_tenant_members(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_tenant: Tenant,
        e2e_db_session: AsyncSession,
    ):
        """Test listing members of a tenant."""
        # Create some users for this tenant
        for i in range(3):
            user = User(
                id=uuid.uuid4(),
                username=f"member_{i}_{uuid.uuid4().hex[:6]}",
                email=f"member_{i}_{uuid.uuid4().hex[:6]}@example.com",
                password_hash=hash_password("TestPassword123!"),
                tenant_id=test_tenant.id,
                is_active=True,
                is_verified=True,
                roles=["member"],
            )
            e2e_db_session.add(user)
        await e2e_db_session.commit()

        response = await async_client.get(
            f"/api/v1/tenants/{test_tenant.id}/members",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "members" in data or "users" in data or isinstance(data, list)


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestTenantErrorHandlingE2E:
    """End-to-end tests for error handling."""

    async def test_create_tenant_missing_required_fields(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test creating tenant with missing required fields."""
        response = await async_client.post(
            "/api/v1/tenants",
            json={"name": "Test"},  # Missing slug and email
            headers=auth_headers,
        )

        assert response.status_code == 422

    async def test_update_nonexistent_tenant(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test updating a non-existent tenant."""
        fake_id = str(uuid.uuid4())
        response = await async_client.patch(
            f"/api/v1/tenants/{fake_id}",
            json={"name": "Updated"},
            headers=auth_headers,
        )

        assert response.status_code == 404

    async def test_unauthorized_access(
        self,
        async_client: AsyncClient,
        tenant_id: str,
    ):
        """Test accessing tenants without authentication."""
        response = await async_client.get(
            "/api/v1/tenants",
            headers={"X-Tenant-ID": tenant_id},
        )

        assert response.status_code == 401
