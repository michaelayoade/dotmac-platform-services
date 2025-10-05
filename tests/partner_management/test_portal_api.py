"""Tests for Partner Portal API endpoints."""

import pytest
from decimal import Decimal
from uuid import uuid4

from dotmac.platform.partner_management.models import (
    PartnerStatus,
    PartnerTier,
    CommissionModel,
    ReferralStatus,
)
from dotmac.platform.partner_management.schemas import (
    PartnerCreate,
    PartnerAccountCreate,
    PartnerCommissionEventCreate,
    ReferralLeadCreate,
)

pytestmark = pytest.mark.asyncio


@pytest.mark.asyncio
class TestPortalDashboard:
    """Test partner portal dashboard endpoint."""

    async def test_get_dashboard_stats(self, async_db_session, test_tenant_id):
        """Test retrieving dashboard statistics."""
        from dotmac.platform.partner_management.service import PartnerService

        service = PartnerService(async_db_session)

        # Create partner with data
        partner = await service.create_partner(
            PartnerCreate(
                company_name="Test Partner",
                primary_email="test@partner.com",
                tier=PartnerTier.GOLD,
                commission_model=CommissionModel.REVENUE_SHARE,
                default_commission_rate=Decimal("0.20"),
            ),
        )

        # Create some data
        customer_id = uuid4()
        await service.create_partner_account(
            PartnerAccountCreate(
                partner_id=partner.id,
                customer_id=customer_id,
                engagement_type="direct",
            ),
        )

        base_amount = Decimal("1000.00")
        rate = Decimal("0.20")
        await service.create_commission_event(
            PartnerCommissionEventCreate(
                partner_id=partner.id,
                customer_id=customer_id,
                event_type="revenue_share",
                commission_amount=base_amount * rate,
                base_amount=base_amount,
                commission_rate=rate,
            ),
        )

        await service.create_referral(
            ReferralLeadCreate(
                partner_id=partner.id,
                contact_name="Test Lead",
                contact_email="lead@example.com",
            ),
        )

        # Get dashboard stats
        from dotmac.platform.partner_management.portal_router import get_dashboard_stats

        stats = await get_dashboard_stats(partner=partner, db=async_db_session)

        assert stats.total_customers == 1
        assert stats.total_revenue_generated == Decimal("1000.00")
        assert stats.total_commissions_earned == Decimal("200.00")
        assert stats.pending_commissions == Decimal("200.00")
        assert stats.total_referrals == 1
        assert stats.current_tier == "gold"
        assert stats.commission_model == "revenue_share"
        assert stats.default_commission_rate == Decimal("0.20")


@pytest.mark.asyncio
class TestPortalProfile:
    """Test partner profile endpoints."""

    async def test_get_profile(self, async_db_session, test_tenant_id):
        """Test retrieving partner profile."""
        from dotmac.platform.partner_management.service import PartnerService

        service = PartnerService(async_db_session)

        partner = await service.create_partner(
            PartnerCreate(
                company_name="Test Partner",
                primary_email="test@partner.com",
                website="https://test.com",
            ),
        )

        # Profile should match partner data
        from dotmac.platform.partner_management.portal_router import get_partner_profile

        profile = await get_partner_profile(partner=partner)

        assert profile.company_name == "Test Partner"
        assert profile.primary_email == "test@partner.com"
        assert profile.website == "https://test.com"

    async def test_update_profile(self, async_db_session, test_tenant_id):
        """Test updating partner profile."""
        from dotmac.platform.partner_management.service import PartnerService
        from dotmac.platform.partner_management.schemas import PartnerUpdate

        service = PartnerService(async_db_session)

        partner = await service.create_partner(
            PartnerCreate(
                company_name="Old Name",
                primary_email="test@partner.com",
            ),
        )

        # Update through portal
        from dotmac.platform.partner_management.portal_router import update_partner_profile

        update_data = PartnerUpdate(
            company_name="New Name",
            website="https://newsite.com",
            phone="+1234567890",
        )

        updated = await update_partner_profile(
            data=update_data,
            partner=partner,
            db=async_db_session,
        )

        assert updated.company_name == "New Name"
        assert updated.website == "https://newsite.com"
        assert updated.phone == "+1234567890"


@pytest.mark.asyncio
class TestPortalReferrals:
    """Test partner referral management."""

    async def test_list_referrals(self, async_db_session, test_tenant_id):
        """Test listing partner referrals."""
        from dotmac.platform.partner_management.service import PartnerService

        service = PartnerService(async_db_session)

        partner = await service.create_partner(
            PartnerCreate(company_name="Test Partner", primary_email="test@partner.com"),
        )

        # Create referrals
        for i in range(3):
            await service.create_referral(
                ReferralLeadCreate(
                    partner_id=partner.id,
                    contact_name=f"Lead {i}",
                    contact_email=f"lead{i}@example.com",
                ),
            )

        # List referrals
        from dotmac.platform.partner_management.portal_router import list_partner_referrals

        referrals = await list_partner_referrals(partner=partner, db=async_db_session)

        assert len(referrals) == 3
        assert all(r.partner_id == partner.id for r in referrals)

    async def test_submit_referral(self, async_db_session, test_tenant_id):
        """Test submitting new referral."""
        from dotmac.platform.partner_management.service import PartnerService
        from dotmac.platform.partner_management.schemas import ReferralLeadCreate

        service = PartnerService(async_db_session)

        partner = await service.create_partner(
            PartnerCreate(company_name="Test Partner", primary_email="test@partner.com"),
        )

        # Submit referral
        from dotmac.platform.partner_management.portal_router import submit_referral

        referral_data = ReferralLeadCreate(
            partner_id=partner.id,
            contact_name="New Lead",
            contact_email="new@example.com",
            estimated_value=Decimal("5000.00"),
        )

        referral = await submit_referral(
            data=referral_data,
            partner=partner,
            db=async_db_session,
        )

        assert referral.contact_name == "New Lead"
        assert referral.estimated_value == Decimal("5000.00")
        assert referral.status == ReferralStatus.NEW

        # Verify partner count updated
        await async_db_session.refresh(partner)
        assert partner.total_referrals == 1


@pytest.mark.asyncio
class TestPortalCommissions:
    """Test partner commission tracking."""

    async def test_list_commissions(self, async_db_session, test_tenant_id):
        """Test listing partner commissions."""
        from dotmac.platform.partner_management.service import PartnerService

        service = PartnerService(async_db_session)

        partner = await service.create_partner(
            PartnerCreate(
                company_name="Test Partner",
                primary_email="test@partner.com",
                default_commission_rate=Decimal("0.15"),
            ),
        )

        # Create commission events
        for amount in [Decimal("1000"), Decimal("2000")]:
            rate = Decimal("0.15")
            await service.create_commission_event(
                PartnerCommissionEventCreate(
                    partner_id=partner.id,
                    customer_id=uuid4(),
                    event_type="revenue_share",
                    commission_amount=amount * rate,
                    base_amount=amount,
                    commission_rate=rate,
                ),
            )

        # List commissions
        from dotmac.platform.partner_management.portal_router import list_partner_commissions

        commissions = await list_partner_commissions(partner=partner, db=async_db_session)

        assert len(commissions) == 2
        assert sum(c.commission_amount for c in commissions) == Decimal("450.00")


@pytest.mark.asyncio
class TestPortalCustomers:
    """Test partner customer listing."""

    async def test_list_customers(self, async_db_session, test_tenant_id):
        """Test listing partner customers."""
        from dotmac.platform.partner_management.service import PartnerService

        service = PartnerService(async_db_session)

        partner = await service.create_partner(
            PartnerCreate(company_name="Test Partner", primary_email="test@partner.com"),
        )

        # Create customer accounts
        for i in range(2):
            await service.create_partner_account(
                PartnerAccountCreate(
                    partner_id=partner.id,
                    customer_id=uuid4(),
                    engagement_type="direct" if i == 0 else "referral",
                ),
            )

        # List customers
        from dotmac.platform.partner_management.portal_router import list_partner_customers

        customers = await list_partner_customers(partner=partner, db=async_db_session)

        assert len(customers) == 2
        assert all(c.is_active for c in customers)
        assert customers[0].engagement_type in ["direct", "referral"]
