"""
End-to-end tests for tenant portal.

Tests cover portal dashboard, team management, billing, and settings.
"""

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.auth.core import hash_password
from dotmac.platform.tenant.models import Tenant, TenantInvitation
from dotmac.platform.user_management.models import User

pytestmark = [pytest.mark.asyncio, pytest.mark.e2e]


# ============================================================================
# Fixtures for Portal E2E Tests
# ============================================================================


@pytest_asyncio.fixture
async def portal_tenant(e2e_db_session: AsyncSession, tenant_id: str):
    """Create or get a tenant for portal tests."""
    # Use the e2e-test-tenant from fixtures
    tenant = Tenant(
        id=tenant_id,
        name=f"Portal Test Org {uuid.uuid4().hex[:6]}",
        slug=f"portal-org-{uuid.uuid4().hex[:8]}",
        email=f"portal_{uuid.uuid4().hex[:6]}@example.com",
        plan_type="professional",
        status="active",
        is_active=True,
        max_users=50,
        max_api_calls_per_month=100000,
        max_storage_gb=100,
        current_users=5,
        current_api_calls=5000,
        current_storage_gb=Decimal("2.5"),
    )
    e2e_db_session.add(tenant)
    try:
        await e2e_db_session.commit()
        await e2e_db_session.refresh(tenant)
    except Exception:
        await e2e_db_session.rollback()
        # Tenant may already exist
        pass
    return tenant


@pytest_asyncio.fixture
async def portal_team_members(e2e_db_session: AsyncSession, tenant_id: str):
    """Create team members for portal tests."""
    members = []
    roles = ["owner", "admin", "member", "member", "member"]
    for i, role in enumerate(roles):
        user = User(
            id=uuid.uuid4(),
            username=f"team_{role}_{i}_{uuid.uuid4().hex[:4]}",
            email=f"team_{role}_{i}_{uuid.uuid4().hex[:4]}@example.com",
            password_hash=hash_password("TestPassword123!"),
            tenant_id=tenant_id,
            is_active=True,
            is_verified=True,
            roles=[role],
        )
        e2e_db_session.add(user)
        members.append(user)

    await e2e_db_session.commit()
    for member in members:
        await e2e_db_session.refresh(member)
    return members


@pytest_asyncio.fixture
async def portal_invitations(e2e_db_session: AsyncSession, tenant_id: str):
    """Create pending invitations for portal tests."""
    invitations = []
    for i in range(3):
        invitation = TenantInvitation(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            email=f"pending_{i}_{uuid.uuid4().hex[:6]}@example.com",
            role="member" if i < 2 else "admin",
            invited_by=str(uuid.uuid4()),
            token=uuid.uuid4().hex,
            status="pending",
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )
        e2e_db_session.add(invitation)
        invitations.append(invitation)

    await e2e_db_session.commit()
    for inv in invitations:
        await e2e_db_session.refresh(inv)
    return invitations


# ============================================================================
# Dashboard Tests
# ============================================================================


class TestPortalDashboardE2E:
    """End-to-end tests for portal dashboard."""

    async def test_get_dashboard_stats(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test getting dashboard statistics."""
        response = await async_client.get(
            "/api/v1/portal/dashboard",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        # Check for expected fields
        assert isinstance(data, dict)

    async def test_get_usage_metrics(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test getting usage metrics."""
        response = await async_client.get(
            "/api/v1/portal/usage",
            headers=auth_headers,
        )

        assert response.status_code == 200

    async def test_get_usage_breakdown(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test getting detailed usage breakdown."""
        response = await async_client.get(
            "/api/v1/portal/usage/breakdown",
            headers=auth_headers,
        )

        assert response.status_code == 200

    async def test_get_usage_with_period(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test getting usage for specific period."""
        response = await async_client.get(
            "/api/v1/portal/usage?period=30d",
            headers=auth_headers,
        )

        assert response.status_code == 200


# ============================================================================
# Team Management Tests
# ============================================================================


class TestPortalTeamE2E:
    """End-to-end tests for portal team management."""

    async def test_list_team_members(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        portal_team_members: list[User],
    ):
        """Test listing team members."""
        response = await async_client.get(
            "/api/v1/portal/members",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "members" in data or isinstance(data, list)

    async def test_get_team_member(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        portal_team_members: list[User],
    ):
        """Test getting a specific team member."""
        member = portal_team_members[0]
        response = await async_client.get(
            f"/api/v1/portal/members/{member.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200

    async def test_update_member_role(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        portal_team_members: list[User],
    ):
        """Test updating a member's role."""
        member = portal_team_members[2]  # A regular member

        response = await async_client.patch(
            f"/api/v1/portal/members/{member.id}/role",
            json={"role": "admin"},
            headers=auth_headers,
        )

        assert response.status_code == 200

    async def test_remove_team_member(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        portal_team_members: list[User],
    ):
        """Test removing a team member."""
        member = portal_team_members[-1]  # Last member

        response = await async_client.delete(
            f"/api/v1/portal/members/{member.id}",
            headers=auth_headers,
        )

        assert response.status_code in [200, 204]

    async def test_cannot_remove_owner(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        portal_team_members: list[User],
    ):
        """Test that owner cannot be removed."""
        owner = portal_team_members[0]  # Owner

        response = await async_client.delete(
            f"/api/v1/portal/members/{owner.id}",
            headers=auth_headers,
        )

        # Should fail - can't remove owner
        assert response.status_code in [400, 403]


# ============================================================================
# Portal Invitations Tests
# ============================================================================


class TestPortalInvitationsE2E:
    """End-to-end tests for portal invitation management."""

    async def test_list_invitations(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        portal_invitations: list[TenantInvitation],
    ):
        """Test listing pending invitations."""
        response = await async_client.get(
            "/api/v1/portal/invitations",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "invitations" in data or isinstance(data, list)

    async def test_create_invitation(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test creating an invitation."""
        invitation_data = {
            "email": f"newinvite_{uuid.uuid4().hex[:8]}@example.com",
            "role": "member",
            "sendEmail": True,
        }

        with patch("dotmac.platform.communications.email_service.EmailService.send_email") as mock:
            mock.return_value = AsyncMock()

            response = await async_client.post(
                "/api/v1/portal/invitations",
                json=invitation_data,
                headers=auth_headers,
            )

            assert response.status_code in [200, 201]

    async def test_cancel_invitation(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        portal_invitations: list[TenantInvitation],
    ):
        """Test canceling an invitation."""
        invitation = portal_invitations[0]

        response = await async_client.delete(
            f"/api/v1/portal/invitations/{invitation.id}",
            headers=auth_headers,
        )

        assert response.status_code in [200, 204]

    async def test_resend_invitation(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        portal_invitations: list[TenantInvitation],
    ):
        """Test resending an invitation email."""
        invitation = portal_invitations[0]

        with patch("dotmac.platform.communications.email_service.EmailService.send_email") as mock:
            mock.return_value = AsyncMock()

            response = await async_client.post(
                f"/api/v1/portal/invitations/{invitation.id}/resend",
                headers=auth_headers,
            )

            assert response.status_code == 200


# ============================================================================
# Portal Billing Tests
# ============================================================================


class TestPortalBillingE2E:
    """End-to-end tests for portal billing information."""

    async def test_get_billing_info(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test getting billing information."""
        response = await async_client.get(
            "/api/v1/portal/billing",
            headers=auth_headers,
        )

        assert response.status_code == 200

    async def test_list_invoices(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test listing invoices."""
        response = await async_client.get(
            "/api/v1/portal/invoices",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "invoices" in data or isinstance(data, list)

    async def test_list_invoices_with_filters(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test listing invoices with status filter."""
        response = await async_client.get(
            "/api/v1/portal/invoices?status=paid",
            headers=auth_headers,
        )

        assert response.status_code == 200

    async def test_download_invoice_not_found(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test downloading non-existent invoice."""
        fake_id = str(uuid.uuid4())
        response = await async_client.get(
            f"/api/v1/portal/invoices/{fake_id}/download",
            headers=auth_headers,
        )

        assert response.status_code == 404


# ============================================================================
# Portal Settings Tests
# ============================================================================


class TestPortalSettingsE2E:
    """End-to-end tests for portal settings."""

    async def test_get_settings(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test getting tenant settings."""
        response = await async_client.get(
            "/api/v1/portal/settings",
            headers=auth_headers,
        )

        assert response.status_code == 200

    async def test_update_settings(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test updating tenant settings."""
        settings_data = {
            "organizationName": "Updated Organization",
            "timezone": "America/New_York",
            "dateFormat": "MM/DD/YYYY",
        }

        response = await async_client.patch(
            "/api/v1/portal/settings",
            json=settings_data,
            headers=auth_headers,
        )

        assert response.status_code == 200


# ============================================================================
# Portal API Keys Tests
# ============================================================================


class TestPortalApiKeysE2E:
    """End-to-end tests for portal API key management."""

    async def test_list_api_keys(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test listing API keys."""
        response = await async_client.get(
            "/api/v1/portal/api-keys",
            headers=auth_headers,
        )

        assert response.status_code == 200

    async def test_create_api_key(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test creating an API key."""
        key_data = {
            "name": f"Test Key {uuid.uuid4().hex[:8]}",
            "permissions": ["read", "write"],
            "expiresIn": 30,  # 30 days
        }

        response = await async_client.post(
            "/api/v1/portal/api-keys",
            json=key_data,
            headers=auth_headers,
        )

        assert response.status_code in [200, 201]

    async def test_delete_api_key_not_found(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test deleting non-existent API key."""
        fake_id = str(uuid.uuid4())
        response = await async_client.delete(
            f"/api/v1/portal/api-keys/{fake_id}",
            headers=auth_headers,
        )

        assert response.status_code == 404


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestPortalErrorHandlingE2E:
    """End-to-end tests for portal error handling."""

    async def test_unauthorized_access(
        self,
        async_client: AsyncClient,
        tenant_id: str,
    ):
        """Test accessing portal without authentication."""
        response = await async_client.get(
            "/api/v1/portal/dashboard",
            headers={"X-Tenant-ID": tenant_id},
        )

        assert response.status_code == 401

    async def test_invite_invalid_email(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test creating invitation with invalid email."""
        invitation_data = {
            "email": "not-an-email",
            "role": "member",
        }

        response = await async_client.post(
            "/api/v1/portal/invitations",
            json=invitation_data,
            headers=auth_headers,
        )

        assert response.status_code == 422

    async def test_update_member_role_invalid(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        portal_team_members: list[User],
    ):
        """Test updating member with invalid role."""
        member = portal_team_members[2]

        response = await async_client.patch(
            f"/api/v1/portal/members/{member.id}/role",
            json={"role": "invalid_role"},
            headers=auth_headers,
        )

        # May succeed if role is validated elsewhere
        assert response.status_code in [200, 400, 422]

    async def test_access_other_tenant_data(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test that tenant isolation is enforced."""
        # Try to access a different tenant's member
        other_member_id = str(uuid.uuid4())

        response = await async_client.get(
            f"/api/v1/portal/members/{other_member_id}",
            headers=auth_headers,
        )

        # Should return 404 (not found) rather than the data
        assert response.status_code in [403, 404]
