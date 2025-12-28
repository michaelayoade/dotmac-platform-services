"""
End-to-end tests for partner portal.

Tests cover partner dashboard, referrals, commissions, team management, and invitations.
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
from dotmac.platform.partner_management.models import (
    CommissionModel,
    CommissionStatus,
    Partner,
    PartnerAccount,
    PartnerCommissionEvent,
    PartnerInvitationStatus,
    PartnerPayout,
    PartnerStatus,
    PartnerTier,
    PartnerUser,
    PartnerUserInvitation,
    PayoutStatus,
    ReferralLead,
    ReferralStatus,
)
from dotmac.platform.tenant.models import Tenant
from dotmac.platform.user_management.models import User

pytestmark = [pytest.mark.asyncio, pytest.mark.e2e]


# ============================================================================
# Fixtures for Partner Portal E2E Tests
# ============================================================================


@pytest_asyncio.fixture
async def portal_partner(e2e_db_session: AsyncSession, tenant_id: str):
    """Create a partner for portal tests."""
    unique_id = uuid.uuid4().hex[:8]
    partner = Partner(
        id=uuid.uuid4(),
        company_name=f"Portal Partner {unique_id}",
        legal_name=f"Portal Partner Legal {unique_id}",
        partner_number=f"P-{unique_id}",
        primary_email=f"primary_{unique_id}@partner.com",
        billing_email=f"billing_{unique_id}@partner.com",
        status=PartnerStatus.ACTIVE,
        tier=PartnerTier.SILVER,
        commission_model=CommissionModel.REVENUE_SHARE,
        default_commission_rate=Decimal("15.00"),
        total_customers=5,
        total_revenue_generated=Decimal("50000.00"),
        total_commissions_earned=Decimal("7500.00"),
        total_commissions_paid=Decimal("5000.00"),
        total_referrals=10,
        converted_referrals=5,
        tenant_id=tenant_id,
    )
    e2e_db_session.add(partner)
    await e2e_db_session.commit()
    await e2e_db_session.refresh(partner)
    return partner


@pytest_asyncio.fixture
async def partner_user(
    e2e_db_session: AsyncSession,
    portal_partner: Partner,
    user_id: str,
    tenant_id: str,
):
    """Create a partner user linked to the authenticated user."""
    partner_user = PartnerUser(
        id=uuid.uuid4(),
        partner_id=portal_partner.id,
        email="partner_user@example.com",
        first_name="Partner",
        last_name="User",
        role="admin",
        is_primary_contact=True,
        is_active=True,
        user_id=uuid.UUID(user_id),
        tenant_id=tenant_id,
    )
    e2e_db_session.add(partner_user)
    await e2e_db_session.commit()
    await e2e_db_session.refresh(partner_user)
    return partner_user


@pytest_asyncio.fixture
async def partner_team_members(
    e2e_db_session: AsyncSession,
    portal_partner: Partner,
    tenant_id: str,
):
    """Create multiple team members for the partner."""
    members = []
    roles = ["admin", "member", "member", "viewer"]

    for i, role in enumerate(roles):
        unique_id = uuid.uuid4().hex[:4]
        member = PartnerUser(
            id=uuid.uuid4(),
            partner_id=portal_partner.id,
            email=f"team_{role}_{unique_id}@partner.com",
            first_name=f"Team{i}",
            last_name=f"Member{i}",
            role=role,
            is_active=True,
            tenant_id=tenant_id,
        )
        e2e_db_session.add(member)
        members.append(member)

    await e2e_db_session.commit()
    for m in members:
        await e2e_db_session.refresh(m)
    return members


@pytest_asyncio.fixture
async def partner_referrals(
    e2e_db_session: AsyncSession,
    portal_partner: Partner,
    tenant_id: str,
):
    """Create referrals for the partner."""
    referrals = []
    statuses = [
        ReferralStatus.NEW,
        ReferralStatus.CONTACTED,
        ReferralStatus.QUALIFIED,
        ReferralStatus.CONVERTED,
        ReferralStatus.LOST,
    ]

    for i, status_val in enumerate(statuses):
        unique_id = uuid.uuid4().hex[:8]
        referral = ReferralLead(
            id=uuid.uuid4(),
            partner_id=portal_partner.id,
            company_name=f"Referred Company {unique_id}",
            contact_name=f"Contact {i}",
            contact_email=f"referral_{unique_id}@example.com",
            status=status_val,
            notes=f"Referral notes {i}",
            tenant_id=tenant_id,
        )
        e2e_db_session.add(referral)
        referrals.append(referral)

    await e2e_db_session.commit()
    for r in referrals:
        await e2e_db_session.refresh(r)
    return referrals


@pytest_asyncio.fixture
async def partner_commissions(
    e2e_db_session: AsyncSession,
    portal_partner: Partner,
    tenant_id: str,
):
    """Create commission events for the partner."""
    events = []

    for i in range(5):
        event = PartnerCommissionEvent(
            id=uuid.uuid4(),
            partner_id=portal_partner.id,
            customer_id=str(uuid.uuid4()),
            base_amount=Decimal("1000.00"),
            commission_rate=Decimal("15.00"),
            commission_amount=Decimal("150.00"),
            currency="USD",
            status=CommissionStatus.PENDING if i < 2 else CommissionStatus.PAID,
            event_type="invoice_paid",
            event_date=datetime.now(UTC) - timedelta(days=i * 7),
            tenant_id=tenant_id,
        )
        e2e_db_session.add(event)
        events.append(event)

    await e2e_db_session.commit()
    for e in events:
        await e2e_db_session.refresh(e)
    return events


@pytest_asyncio.fixture
async def partner_accounts(
    e2e_db_session: AsyncSession,
    portal_partner: Partner,
    tenant_id: str,
):
    """Create tenant accounts assigned to the partner."""
    accounts = []

    for i in range(3):
        customer_id = str(uuid.uuid4())
        # Create tenant for this account
        tenant = Tenant(
            id=customer_id,
            name=f"Partner Customer {i}",
            slug=f"partner-customer-{uuid.uuid4().hex[:8]}",
            email=f"customer_{i}@example.com",
            plan_type="professional",
            status="active",
            is_active=True,
        )
        e2e_db_session.add(tenant)

        account = PartnerAccount(
            id=uuid.uuid4(),
            partner_id=portal_partner.id,
            customer_id=customer_id,
            engagement_type="reseller",
            start_date=datetime.now(UTC) - timedelta(days=30 * (i + 1)),
            is_active=True,
            tenant_id=tenant_id,
        )
        e2e_db_session.add(account)
        accounts.append(account)

    await e2e_db_session.commit()
    for a in accounts:
        await e2e_db_session.refresh(a)
    return accounts


@pytest_asyncio.fixture
async def partner_payouts(
    e2e_db_session: AsyncSession,
    portal_partner: Partner,
    tenant_id: str,
):
    """Create payout records for the partner."""
    payouts = []

    for i in range(3):
        payout = PartnerPayout(
            id=uuid.uuid4(),
            partner_id=portal_partner.id,
            total_amount=Decimal("1500.00"),
            currency="USD",
            status=PayoutStatus.PAID if i > 0 else PayoutStatus.PENDING,
            period_start=datetime.now(UTC) - timedelta(days=60 + i * 30),
            period_end=datetime.now(UTC) - timedelta(days=30 + i * 30),
            payout_date=datetime.now(UTC) - timedelta(days=25 + i * 30),
            tenant_id=tenant_id,
        )
        e2e_db_session.add(payout)
        payouts.append(payout)

    await e2e_db_session.commit()
    for p in payouts:
        await e2e_db_session.refresh(p)
    return payouts


@pytest_asyncio.fixture
async def partner_invitations(
    e2e_db_session: AsyncSession,
    portal_partner: Partner,
    tenant_id: str,
):
    """Create pending invitations for the partner."""
    invitations = []

    for i in range(2):
        unique_id = uuid.uuid4().hex[:8]
        invitation = PartnerUserInvitation(
            id=uuid.uuid4(),
            partner_id=portal_partner.id,
            email=f"invite_{unique_id}@example.com",
            role="member" if i == 0 else "admin",
            invited_by=uuid.uuid4(),  # Required: who sent the invitation
            token=uuid.uuid4().hex,
            status=PartnerInvitationStatus.PENDING,
            expires_at=datetime.now(UTC) + timedelta(days=7),
            tenant_id=tenant_id,
        )
        e2e_db_session.add(invitation)
        invitations.append(invitation)

    await e2e_db_session.commit()
    for inv in invitations:
        await e2e_db_session.refresh(inv)
    return invitations


@pytest.fixture
def mock_email_service():
    """Mock email service for invitation tests."""
    with patch("dotmac.platform.partner_management.portal_router._send_partner_invitation_email") as mock:
        mock.return_value = AsyncMock()
        yield mock


# ============================================================================
# Dashboard Tests
# ============================================================================


class TestPartnerPortalDashboardE2E:
    """End-to-end tests for partner portal dashboard."""

    async def test_get_dashboard_stats(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        portal_partner: Partner,
        partner_user: PartnerUser,
    ):
        """Test getting dashboard statistics."""
        response = await async_client.get(
            "/api/v1/partners/portal/dashboard",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_tenants" in data
        assert "total_commissions_earned" in data
        assert "pending_commissions" in data
        assert "total_referrals" in data
        assert "current_tier" in data

    async def test_get_partner_profile(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        portal_partner: Partner,
        partner_user: PartnerUser,
    ):
        """Test getting partner profile."""
        response = await async_client.get(
            "/api/v1/partners/portal/profile",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["company_name"] == portal_partner.company_name

    async def test_update_partner_profile(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        portal_partner: Partner,
        partner_user: PartnerUser,
    ):
        """Test updating partner profile."""
        update_data = {
            "company_name": "Updated Partner Name",
            "website": "https://updated-partner.com",
        }

        response = await async_client.patch(
            "/api/v1/partners/portal/profile",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["company_name"] == "Updated Partner Name"


# ============================================================================
# Referrals Tests
# ============================================================================


class TestPartnerPortalReferralsE2E:
    """End-to-end tests for partner referral management."""

    async def test_list_referrals(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        portal_partner: Partner,
        partner_user: PartnerUser,
        partner_referrals: list[ReferralLead],
    ):
        """Test listing partner referrals."""
        response = await async_client.get(
            "/api/v1/partners/portal/referrals",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= len(partner_referrals)

    async def test_submit_referral(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        portal_partner: Partner,
        partner_user: PartnerUser,
    ):
        """Test submitting a new referral."""
        unique_id = uuid.uuid4().hex[:8]
        referral_data = {
            "company_name": f"Referred Company {unique_id}",
            "contact_name": "John Referral",
            "contact_email": f"referral_{unique_id}@example.com",
            "contact_phone": "+1-555-0300",
            "notes": "Met at conference, interested in our platform.",
        }

        response = await async_client.post(
            "/api/v1/partners/portal/referrals",
            json=referral_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["company_name"] == referral_data["company_name"]
        assert data["status"] == "new"

    async def test_submit_referral_missing_email(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        portal_partner: Partner,
        partner_user: PartnerUser,
    ):
        """Test submitting referral without email."""
        referral_data = {
            "company_name": "Test Company",
            "contact_name": "Test Contact",
        }

        response = await async_client.post(
            "/api/v1/partners/portal/referrals",
            json=referral_data,
            headers=auth_headers,
        )

        # May require email or accept without
        assert response.status_code in [201, 422]


# ============================================================================
# Commissions Tests
# ============================================================================


class TestPartnerPortalCommissionsE2E:
    """End-to-end tests for partner commission viewing."""

    async def test_list_commissions(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        portal_partner: Partner,
        partner_user: PartnerUser,
        partner_commissions: list[PartnerCommissionEvent],
    ):
        """Test listing commission events."""
        response = await async_client.get(
            "/api/v1/partners/portal/commissions",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_list_statements(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        portal_partner: Partner,
        partner_user: PartnerUser,
        partner_payouts: list[PartnerPayout],
    ):
        """Test listing partner statements."""
        response = await async_client.get(
            "/api/v1/partners/portal/statements",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_list_payouts(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        portal_partner: Partner,
        partner_user: PartnerUser,
        partner_payouts: list[PartnerPayout],
    ):
        """Test listing payout history."""
        response = await async_client.get(
            "/api/v1/partners/portal/payouts",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_download_statement(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        portal_partner: Partner,
        partner_user: PartnerUser,
        partner_payouts: list[PartnerPayout],
    ):
        """Test downloading a statement."""
        payout = partner_payouts[0]
        response = await async_client.get(
            f"/api/v1/partners/portal/statements/{payout.id}/download",
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")

    async def test_download_statement_not_found(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        portal_partner: Partner,
        partner_user: PartnerUser,
    ):
        """Test downloading non-existent statement."""
        fake_id = uuid.uuid4()
        response = await async_client.get(
            f"/api/v1/partners/portal/statements/{fake_id}/download",
            headers=auth_headers,
        )

        assert response.status_code == 404


# ============================================================================
# Tenants Tests
# ============================================================================


class TestPartnerPortalTenantsE2E:
    """End-to-end tests for partner tenant viewing."""

    async def test_list_tenants(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        portal_partner: Partner,
        partner_user: PartnerUser,
        partner_accounts: list[PartnerAccount],
    ):
        """Test listing assigned tenants."""
        response = await async_client.get(
            "/api/v1/partners/portal/tenants",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


# ============================================================================
# Team Management Tests
# ============================================================================


class TestPartnerPortalTeamE2E:
    """End-to-end tests for partner team management."""

    async def test_list_team_members(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        portal_partner: Partner,
        partner_user: PartnerUser,
        partner_team_members: list[PartnerUser],
    ):
        """Test listing team members."""
        response = await async_client.get(
            "/api/v1/partners/portal/team",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_list_portal_users(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        portal_partner: Partner,
        partner_user: PartnerUser,
        partner_team_members: list[PartnerUser],
    ):
        """Test listing portal users."""
        response = await async_client.get(
            "/api/v1/partners/portal/users",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "users" in data

    async def test_update_portal_user(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        portal_partner: Partner,
        partner_user: PartnerUser,
        partner_team_members: list[PartnerUser],
    ):
        """Test updating a team member."""
        member = partner_team_members[0]
        update_data = {"role": "viewer"}

        response = await async_client.patch(
            f"/api/v1/partners/portal/users/{member.id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "viewer"

    async def test_update_portal_user_not_found(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        portal_partner: Partner,
        partner_user: PartnerUser,
    ):
        """Test updating non-existent team member."""
        fake_id = uuid.uuid4()
        response = await async_client.patch(
            f"/api/v1/partners/portal/users/{fake_id}",
            json={"role": "member"},
            headers=auth_headers,
        )

        assert response.status_code == 404

    async def test_delete_portal_user(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        portal_partner: Partner,
        partner_user: PartnerUser,
        partner_team_members: list[PartnerUser],
    ):
        """Test removing a team member."""
        member = partner_team_members[-1]  # Last member

        response = await async_client.delete(
            f"/api/v1/partners/portal/users/{member.id}",
            headers=auth_headers,
        )

        assert response.status_code == 204


# ============================================================================
# Invitations Tests
# ============================================================================


class TestPartnerPortalInvitationsE2E:
    """End-to-end tests for partner invitation management."""

    async def test_list_invitations(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        portal_partner: Partner,
        partner_user: PartnerUser,
        partner_invitations: list[PartnerUserInvitation],
    ):
        """Test listing pending invitations."""
        response = await async_client.get(
            "/api/v1/partners/portal/invitations",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "invitations" in data
        assert "total" in data

    async def test_create_invitation(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        portal_partner: Partner,
        partner_user: PartnerUser,
        mock_email_service,
    ):
        """Test creating an invitation."""
        unique_id = uuid.uuid4().hex[:8]
        invitation_data = {
            "email": f"newinvite_{unique_id}@example.com",
            "role": "member",
            "send_email": False,
        }

        response = await async_client.post(
            "/api/v1/partners/portal/invitations",
            json=invitation_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == invitation_data["email"]

    async def test_create_invitation_duplicate_email(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        portal_partner: Partner,
        partner_user: PartnerUser,
        partner_invitations: list[PartnerUserInvitation],
    ):
        """Test creating invitation with already invited email."""
        existing = partner_invitations[0]

        response = await async_client.post(
            "/api/v1/partners/portal/invitations",
            json={"email": existing.email, "role": "member"},
            headers=auth_headers,
        )

        assert response.status_code == 400

    async def test_cancel_invitation(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        portal_partner: Partner,
        partner_user: PartnerUser,
        partner_invitations: list[PartnerUserInvitation],
    ):
        """Test canceling an invitation."""
        invitation = partner_invitations[0]

        response = await async_client.delete(
            f"/api/v1/partners/portal/invitations/{invitation.id}",
            headers=auth_headers,
        )

        assert response.status_code == 204

    async def test_cancel_invitation_not_found(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        portal_partner: Partner,
        partner_user: PartnerUser,
    ):
        """Test canceling non-existent invitation."""
        fake_id = uuid.uuid4()
        response = await async_client.delete(
            f"/api/v1/partners/portal/invitations/{fake_id}",
            headers=auth_headers,
        )

        assert response.status_code == 404

    async def test_resend_invitation(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        portal_partner: Partner,
        partner_user: PartnerUser,
        partner_invitations: list[PartnerUserInvitation],
        mock_email_service,
    ):
        """Test resending an invitation."""
        invitation = partner_invitations[0]

        response = await async_client.post(
            f"/api/v1/partners/portal/invitations/{invitation.id}/resend",
            headers=auth_headers,
        )

        assert response.status_code == 200


# ============================================================================
# Public Invitation Accept Tests
# ============================================================================


class TestPartnerInvitationAcceptE2E:
    """End-to-end tests for accepting partner invitations."""

    async def test_accept_invitation(
        self,
        async_client: AsyncClient,
        tenant_id: str,
        partner_invitations: list[PartnerUserInvitation],
    ):
        """Test accepting a partner invitation."""
        invitation = partner_invitations[0]

        accept_data = {
            "token": invitation.token,
            "first_name": "New",
            "last_name": "Partner",
            "password": "SecurePassword123!",
        }

        response = await async_client.post(
            "/api/v1/partners/invitations/accept",
            json=accept_data,
            headers={"X-Tenant-ID": tenant_id},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    async def test_accept_invitation_invalid_token(
        self,
        async_client: AsyncClient,
        tenant_id: str,
    ):
        """Test accepting invitation with invalid token."""
        accept_data = {
            "token": "invalid-token-12345",
            "first_name": "Test",
            "last_name": "User",
            "password": "SecurePassword123!",
        }

        response = await async_client.post(
            "/api/v1/partners/invitations/accept",
            json=accept_data,
            headers={"X-Tenant-ID": tenant_id},
        )

        assert response.status_code == 404


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestPartnerPortalErrorsE2E:
    """End-to-end tests for portal error handling."""

    async def test_portal_unauthorized(
        self,
        async_client: AsyncClient,
        tenant_id: str,
    ):
        """Test accessing portal without authentication."""
        response = await async_client.get(
            "/api/v1/partners/portal/dashboard",
            headers={"X-Tenant-ID": tenant_id},
        )

        assert response.status_code == 401

    async def test_portal_no_partner_association(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test accessing portal without partner association."""
        # User is authenticated but not associated with a partner
        response = await async_client.get(
            "/api/v1/partners/portal/dashboard",
            headers=auth_headers,
        )

        # Should return 403 or 404 if no partner found
        assert response.status_code in [403, 404]
