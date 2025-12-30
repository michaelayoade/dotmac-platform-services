"""
End-to-end tests for partner admin management.

Tests cover partner CRUD, user management, and account assignment.
"""

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.partner_management.models import (
    CommissionModel,
    CommissionStatus,
    Partner,
    PartnerAccount,
    PartnerCommissionEvent,
    PartnerStatus,
    PartnerTier,
    PartnerUser,
    ReferralLead,
    ReferralStatus,
)
from dotmac.platform.tenant.models import Tenant

pytestmark = [pytest.mark.asyncio, pytest.mark.e2e]


# ============================================================================
# Fixtures for Partner Admin E2E Tests
# ============================================================================


@pytest_asyncio.fixture
async def admin_partner(e2e_db_session: AsyncSession, tenant_id: str):
    """Create a partner for admin tests."""
    unique_id = uuid.uuid4().hex[:8]
    partner = Partner(
        id=uuid.uuid4(),
        company_name=f"Admin Test Partner {unique_id}",
        legal_name=f"Admin Test Partner Legal {unique_id}",
        partner_number=f"AP-{unique_id}",
        primary_email=f"primary_{unique_id}@partner.com",
        billing_email=f"admin_{unique_id}@partner.com",
        status=PartnerStatus.ACTIVE,
        tier=PartnerTier.GOLD,
        commission_model=CommissionModel.REVENUE_SHARE,
        default_commission_rate=Decimal("20.00"),
        total_customers=10,
        total_revenue_generated=Decimal("100000.00"),
        total_commissions_earned=Decimal("20000.00"),
        total_commissions_paid=Decimal("15000.00"),
        tenant_id=tenant_id,
    )
    e2e_db_session.add(partner)
    await e2e_db_session.commit()
    await e2e_db_session.refresh(partner)
    return partner


@pytest_asyncio.fixture
async def multiple_partners(e2e_db_session: AsyncSession, tenant_id: str):
    """Create multiple partners for list tests."""
    partners = []
    statuses = [
        PartnerStatus.ACTIVE,
        PartnerStatus.ACTIVE,
        PartnerStatus.SUSPENDED,
        PartnerStatus.PENDING,
    ]

    for i, status_val in enumerate(statuses):
        unique_id = uuid.uuid4().hex[:8]
        partner = Partner(
            id=uuid.uuid4(),
            company_name=f"Partner Company {unique_id}",
            partner_number=f"MP-{unique_id}",
            primary_email=f"mp_primary_{unique_id}@partner.com",
            billing_email=f"mp_{unique_id}@partner.com",
            status=status_val,
            tier=PartnerTier.BRONZE,
            commission_model=CommissionModel.FLAT_FEE,
            tenant_id=tenant_id,
        )
        e2e_db_session.add(partner)
        partners.append(partner)

    await e2e_db_session.commit()
    for p in partners:
        await e2e_db_session.refresh(p)
    return partners


@pytest_asyncio.fixture
async def admin_partner_users(
    e2e_db_session: AsyncSession,
    admin_partner: Partner,
    tenant_id: str,
):
    """Create users for the admin partner."""
    users = []
    roles = ["admin", "member", "viewer"]

    for i, role in enumerate(roles):
        unique_id = uuid.uuid4().hex[:8]
        user = PartnerUser(
            id=uuid.uuid4(),
            partner_id=admin_partner.id,
            email=f"partneruser_{unique_id}@partner.com",
            first_name=f"User{i}",
            last_name=f"Partner{i}",
            role=role,
            is_active=True,
            tenant_id=tenant_id,
        )
        e2e_db_session.add(user)
        users.append(user)

    await e2e_db_session.commit()
    for u in users:
        await e2e_db_session.refresh(u)
    return users


@pytest_asyncio.fixture
async def customer_tenant(e2e_db_session: AsyncSession):
    """Create a tenant to be assigned to a partner."""
    unique_id = uuid.uuid4().hex[:8]
    tenant = Tenant(
        id=str(uuid.uuid4()),
        name=f"Customer Tenant {unique_id}",
        slug=f"customer-tenant-{unique_id}",
        email=f"customer_{unique_id}@example.com",
        plan_type="professional",
        status="active",
        is_active=True,
    )
    e2e_db_session.add(tenant)
    await e2e_db_session.commit()
    await e2e_db_session.refresh(tenant)
    return tenant


# ============================================================================
# Partner CRUD Tests
# ============================================================================


class TestPartnerCRUDE2E:
    """End-to-end tests for partner CRUD operations."""

    async def test_create_partner(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test creating a new partner."""
        unique_id = uuid.uuid4().hex[:8]
        partner_data = {
            "company_name": f"New Partner {unique_id}",
            "legal_name": f"New Partner Legal {unique_id}",
            "billing_email": f"new_{unique_id}@partner.com",
            "tier": "bronze",
            "commission_model": "revenue_share",
            "default_commission_rate": "10.00",
        }

        response = await async_client.post(
            "/api/v1/partners",
            json=partner_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["company_name"] == partner_data["company_name"]
        assert "id" in data
        assert "partner_number" in data

    async def test_list_partners(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        multiple_partners: list[Partner],
    ):
        """Test listing all partners."""
        response = await async_client.get(
            "/api/v1/partners",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "partners" in data
        assert "total" in data

    async def test_list_partners_filter_by_status(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        multiple_partners: list[Partner],
    ):
        """Test listing partners filtered by status."""
        response = await async_client.get(
            "/api/v1/partners?status=active",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "partners" in data
        for p in data["partners"]:
            assert p["status"] == "active"

    async def test_list_partners_pagination(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        multiple_partners: list[Partner],
    ):
        """Test listing partners with pagination."""
        response = await async_client.get(
            "/api/v1/partners?page=1&page_size=2",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "page" in data
        assert len(data["partners"]) <= 2

    async def test_get_partner(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        admin_partner: Partner,
    ):
        """Test getting a specific partner."""
        response = await async_client.get(
            f"/api/v1/partners/{admin_partner.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(admin_partner.id)
        assert data["company_name"] == admin_partner.company_name

    async def test_get_partner_by_number(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        admin_partner: Partner,
    ):
        """Test getting partner by partner number."""
        response = await async_client.get(
            f"/api/v1/partners/by-number/{admin_partner.partner_number}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["partner_number"] == admin_partner.partner_number

    async def test_get_partner_not_found(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test getting non-existent partner."""
        fake_id = uuid.uuid4()
        response = await async_client.get(
            f"/api/v1/partners/{fake_id}",
            headers=auth_headers,
        )

        assert response.status_code == 404

    async def test_update_partner(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        admin_partner: Partner,
    ):
        """Test updating a partner."""
        update_data = {
            "company_name": "Updated Partner Name",
            "tier": "platinum",
        }

        response = await async_client.patch(
            f"/api/v1/partners/{admin_partner.id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["company_name"] == "Updated Partner Name"

    async def test_delete_partner(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        e2e_db_session: AsyncSession,
        tenant_id: str,
    ):
        """Test soft deleting a partner."""
        # Create a partner to delete
        unique_id = uuid.uuid4().hex[:8]
        partner = Partner(
            id=uuid.uuid4(),
            company_name=f"Delete Test {unique_id}",
            partner_number=f"DEL-{unique_id}",
            primary_email=f"delete_primary_{unique_id}@partner.com",
            billing_email=f"delete_{unique_id}@partner.com",
            status=PartnerStatus.ACTIVE,
            tier=PartnerTier.BRONZE,
            commission_model=CommissionModel.FLAT_FEE,
            tenant_id=tenant_id,
        )
        e2e_db_session.add(partner)
        await e2e_db_session.commit()

        response = await async_client.delete(
            f"/api/v1/partners/{partner.id}",
            headers=auth_headers,
        )

        assert response.status_code == 204


# ============================================================================
# Partner User Management Tests
# ============================================================================


class TestPartnerUserManagementE2E:
    """End-to-end tests for partner user management."""

    async def test_create_partner_user(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        admin_partner: Partner,
    ):
        """Test creating a partner user."""
        unique_id = uuid.uuid4().hex[:8]
        user_data = {
            "email": f"newuser_{unique_id}@partner.com",
            "first_name": "New",
            "last_name": "User",
            "role": "member",
        }

        response = await async_client.post(
            f"/api/v1/partners/{admin_partner.id}/users",
            json=user_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]

    async def test_list_partner_users(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        admin_partner: Partner,
        admin_partner_users: list[PartnerUser],
    ):
        """Test listing partner users."""
        response = await async_client.get(
            f"/api/v1/partners/{admin_partner.id}/users",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= len(admin_partner_users)

    async def test_list_partner_users_active_only(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        admin_partner: Partner,
        admin_partner_users: list[PartnerUser],
    ):
        """Test listing only active partner users."""
        response = await async_client.get(
            f"/api/v1/partners/{admin_partner.id}/users?active_only=true",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        for user in data:
            assert user["is_active"] is True

    async def test_get_partner_user(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        admin_partner: Partner,
        admin_partner_users: list[PartnerUser],
    ):
        """Test getting a specific partner user."""
        user = admin_partner_users[0]
        response = await async_client.get(
            f"/api/v1/partners/{admin_partner.id}/users/{user.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(user.id)

    async def test_update_partner_user(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        admin_partner: Partner,
        admin_partner_users: list[PartnerUser],
    ):
        """Test updating a partner user."""
        user = admin_partner_users[0]
        update_data = {
            "role": "viewer",
            "phone": "+1-555-9999",
        }

        response = await async_client.patch(
            f"/api/v1/partners/{admin_partner.id}/users/{user.id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "viewer"

    async def test_delete_partner_user(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        admin_partner: Partner,
        admin_partner_users: list[PartnerUser],
    ):
        """Test soft deleting a partner user."""
        user = admin_partner_users[-1]  # Last user

        response = await async_client.delete(
            f"/api/v1/partners/{admin_partner.id}/users/{user.id}",
            headers=auth_headers,
        )

        assert response.status_code == 204


# ============================================================================
# Partner Account Assignment Tests
# ============================================================================


class TestPartnerAccountsE2E:
    """End-to-end tests for partner account management."""

    async def test_create_partner_account(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        admin_partner: Partner,
        customer_tenant: Tenant,
    ):
        """Test assigning a customer to a partner."""
        account_data = {
            "partner_id": str(admin_partner.id),
            "customer_id": str(customer_tenant.id),
            "engagement_type": "reseller",
        }

        response = await async_client.post(
            "/api/v1/partners/accounts",
            json=account_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["partner_id"] == str(admin_partner.id)

    async def test_list_partner_accounts(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        admin_partner: Partner,
        e2e_db_session: AsyncSession,
        tenant_id: str,
    ):
        """Test listing partner accounts."""
        # Create some accounts first
        for i in range(2):
            customer_id = str(uuid.uuid4())
            tenant = Tenant(
                id=customer_id,
                name=f"Account Customer {i}",
                slug=f"account-customer-{uuid.uuid4().hex[:8]}",
                email=f"account_{i}@example.com",
                plan_type="starter",
                status="active",
                is_active=True,
            )
            e2e_db_session.add(tenant)

            account = PartnerAccount(
                id=uuid.uuid4(),
                partner_id=admin_partner.id,
                customer_id=customer_id,
                engagement_type="referral",
                start_date=datetime.now(UTC),
                is_active=True,
                tenant_id=tenant_id,
            )
            e2e_db_session.add(account)

        await e2e_db_session.commit()

        response = await async_client.get(
            f"/api/v1/partners/{admin_partner.id}/accounts",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


# ============================================================================
# Commission Events Tests
# ============================================================================


class TestPartnerCommissionsAdminE2E:
    """End-to-end tests for commission event management."""

    async def test_create_commission_event(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        admin_partner: Partner,
        customer_tenant: Tenant,
    ):
        """Test creating a commission event."""
        event_data = {
            "partner_id": str(admin_partner.id),
            "customer_id": str(customer_tenant.id),
            "base_amount": "1000.00",
            "commission_rate": "15.00",
            "commission_amount": "150.00",
            "currency": "USD",
            "event_type": "invoice_paid",
        }

        response = await async_client.post(
            "/api/v1/partners/commissions",
            json=event_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["partner_id"] == str(admin_partner.id)

    async def test_list_commission_events(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        admin_partner: Partner,
        e2e_db_session: AsyncSession,
        tenant_id: str,
    ):
        """Test listing commission events for a partner."""
        # Create some events
        for i in range(3):
            event = PartnerCommissionEvent(
                id=uuid.uuid4(),
                partner_id=admin_partner.id,
                customer_id=str(uuid.uuid4()),
                base_amount=Decimal("500.00"),
                commission_rate=Decimal("10.00"),
                commission_amount=Decimal("50.00"),
                currency="USD",
                status=CommissionStatus.PENDING,
                event_type="subscription_renewal",
                event_date=datetime.now(UTC),
                tenant_id=tenant_id,
            )
            e2e_db_session.add(event)

        await e2e_db_session.commit()

        response = await async_client.get(
            f"/api/v1/partners/{admin_partner.id}/commissions",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "events" in data
        assert "total" in data


# ============================================================================
# Referral Management Tests
# ============================================================================


class TestPartnerReferralsAdminE2E:
    """End-to-end tests for referral management via admin endpoints."""

    async def test_create_referral(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        admin_partner: Partner,
    ):
        """Test creating a referral."""
        unique_id = uuid.uuid4().hex[:8]
        referral_data = {
            "partner_id": str(admin_partner.id),
            "company_name": f"Referred Company {unique_id}",
            "contact_name": "Referral Contact",
            "contact_email": f"referral_{unique_id}@example.com",
        }

        response = await async_client.post(
            "/api/v1/partners/referrals",
            json=referral_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["company_name"] == referral_data["company_name"]

    async def test_list_referrals(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        admin_partner: Partner,
        e2e_db_session: AsyncSession,
        tenant_id: str,
    ):
        """Test listing referrals for a partner."""
        # Create some referrals
        for i in range(3):
            unique_id = uuid.uuid4().hex[:8]
            referral = ReferralLead(
                id=uuid.uuid4(),
                partner_id=admin_partner.id,
                company_name=f"Referral Co {unique_id}",
                contact_name=f"Contact {i}",
                contact_email=f"ref_{unique_id}@example.com",
                status=ReferralStatus.NEW,
                tenant_id=tenant_id,
            )
            e2e_db_session.add(referral)

        await e2e_db_session.commit()

        response = await async_client.get(
            f"/api/v1/partners/{admin_partner.id}/referrals",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "referrals" in data
        assert "total" in data

    async def test_update_referral(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        admin_partner: Partner,
        e2e_db_session: AsyncSession,
        tenant_id: str,
    ):
        """Test updating a referral."""
        unique_id = uuid.uuid4().hex[:8]
        referral = ReferralLead(
            id=uuid.uuid4(),
            partner_id=admin_partner.id,
            company_name=f"Update Test {unique_id}",
            contact_name="Contact",
            contact_email=f"update_{unique_id}@example.com",
            status=ReferralStatus.NEW,
            tenant_id=tenant_id,
        )
        e2e_db_session.add(referral)
        await e2e_db_session.commit()

        update_data = {
            "status": "qualified",
            "notes": "Qualified lead, ready for contact.",
        }

        response = await async_client.patch(
            f"/api/v1/partners/referrals/{referral.id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "qualified"


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestPartnerAdminErrorsE2E:
    """End-to-end tests for admin error handling."""

    async def test_create_partner_unauthorized(
        self,
        async_client: AsyncClient,
        tenant_id: str,
    ):
        """Test creating partner without authentication."""
        response = await async_client.post(
            "/api/v1/partners",
            json={"company_name": "Test"},
            headers={"X-Tenant-ID": tenant_id},
        )

        assert response.status_code == 401

    async def test_get_partner_users_not_found(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test listing users for non-existent partner."""
        fake_id = uuid.uuid4()
        response = await async_client.get(
            f"/api/v1/partners/{fake_id}/users",
            headers=auth_headers,
        )

        assert response.status_code == 404

    async def test_update_partner_not_found(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test updating non-existent partner."""
        fake_id = uuid.uuid4()
        response = await async_client.patch(
            f"/api/v1/partners/{fake_id}",
            json={"company_name": "Updated"},
            headers=auth_headers,
        )

        assert response.status_code == 404

    async def test_delete_partner_not_found(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test deleting non-existent partner."""
        fake_id = uuid.uuid4()
        response = await async_client.delete(
            f"/api/v1/partners/{fake_id}",
            headers=auth_headers,
        )

        assert response.status_code == 404
