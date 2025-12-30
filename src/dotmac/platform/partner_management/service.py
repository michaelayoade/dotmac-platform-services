"""
Core Partner Management Service.

Provides CRUD operations for partner management following project patterns.
"""

import os
import secrets
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from dotmac.platform.partner_management.models import (
    Partner,
    PartnerAccount,
    PartnerApplication,
    PartnerApplicationStatus,
    PartnerCommissionEvent,
    PartnerStatus,
    PartnerUser,
    ReferralLead,
    ReferralStatus,
)
from dotmac.platform.partner_management.schemas import (
    PartnerAccountCreate,
    PartnerApplicationCreate,
    PartnerCommissionEventCreate,
    PartnerCreate,
    PartnerUpdate,
    PartnerUserCreate,
    PartnerUserUpdate,
    ReferralLeadCreate,
    ReferralLeadUpdate,
)
from dotmac.platform.tenant import get_current_tenant_id

logger = structlog.get_logger(__name__)


def validate_uuid(value: str | UUID, field_name: str = "id") -> UUID:
    """Validate and convert string to UUID."""
    if value is None:
        raise ValueError(f"Invalid UUID for {field_name}: {value}")
    try:
        return UUID(str(value)) if not isinstance(value, UUID) else value
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Invalid UUID for {field_name}: {value}") from e


class PartnerService:
    """Core partner management service."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _resolve_tenant_id(self) -> str:
        """Resolve the current tenant ID from context or use default."""
        tenant_id_value = get_current_tenant_id()
        testing_mode = os.getenv("TESTING") == "1"
        if tenant_id_value:
            tenant_id = (
                tenant_id_value if isinstance(tenant_id_value, str) else str(tenant_id_value)
            )
            if testing_mode and tenant_id in {"default", "default-tenant"}:
                tenant_id_value = None  # Treat framework default as missing during tests
            else:
                return tenant_id

        # Testing environments frequently rely on implicit tenant context; generate a
        # session-scoped fallback to avoid cross-test collisions when isolation relies
        # on transaction rollbacks (particularly with SQLite).
        if os.getenv("TESTING") == "1":
            cached_tenant = self.session.info.get("_test_tenant_id")
            if not cached_tenant:
                cached_tenant = f"test-tenant-{id(self.session):x}"
                self.session.info["_test_tenant_id"] = cached_tenant
            logger.debug(
                "No tenant context found (testing); using session fallback", tenant_id=cached_tenant
            )
            return cached_tenant

        tenant_id = "default-tenant"
        logger.debug("No tenant context found, using default tenant", tenant_id=tenant_id)

        return tenant_id

    def _validate_and_get_tenant(self, partner_id: UUID | str) -> tuple[UUID, str]:
        """Validate partner ID and get current tenant."""
        validated_id = validate_uuid(partner_id, "partner_id")
        tenant_id = self._resolve_tenant_id()
        return validated_id, tenant_id

    def _build_partner_filters(
        self, tenant_id: str, status: PartnerStatus | None = None
    ) -> list[Any]:
        """Build reusable partner query filters."""
        filters: list[Any] = [
            Partner.tenant_id == tenant_id,
            Partner.deleted_at.is_(None),
        ]

        if status:
            filters.append(Partner.status == status)

        return filters

    def _get_base_partner_query(self, tenant_id: str) -> Select[tuple[Partner]]:
        """Get base partner query with tenant filtering."""
        filters = self._build_partner_filters(tenant_id)
        return select(Partner).where(*filters)

    async def _generate_partner_number(self) -> str:
        """Generate unique partner number."""
        tenant_id = self._resolve_tenant_id()

        # Get current max number for tenant
        result = await self.session.execute(
            select(func.count(Partner.id)).where(Partner.tenant_id == tenant_id)
        )
        count = result.scalar() or 0

        # Generate number with prefix
        partner_number = f"PTR-{count + 1:06d}"

        # Ensure uniqueness
        result = await self.session.execute(
            select(Partner.id).where(Partner.partner_number == partner_number)
        )
        if result.scalar_one_or_none():
            # Fallback to random if collision
            partner_number = f"PTR-{secrets.token_hex(4).upper()}"

        return partner_number

    # ========================================================================
    # Partner CRUD Operations
    # ========================================================================

    async def create_partner(
        self,
        data: PartnerCreate,
        created_by: str | None = None,
    ) -> Partner:
        """Create a new partner."""
        partner_number = await self._generate_partner_number()
        tenant_id = self._resolve_tenant_id()

        if not data.primary_email:
            if data.billing_email:
                data = data.model_copy(update={"primary_email": data.billing_email})
            else:
                raise ValueError("primary_email or billing_email is required")

        partner = Partner(
            partner_number=partner_number,
            tenant_id=tenant_id,
            created_by=created_by,
            **data.model_dump(exclude={"metadata", "custom_fields"}),
        )

        # Set JSON fields
        partner.metadata_ = data.metadata or {}
        partner.custom_fields = data.custom_fields or {}

        # Set default metrics
        partner.total_customers = 0
        partner.total_revenue_generated = Decimal("0.00")
        partner.total_commissions_earned = Decimal("0.00")
        partner.total_commissions_paid = Decimal("0.00")
        partner.total_referrals = 0
        partner.converted_referrals = 0

        self.session.add(partner)
        await self.session.commit()
        await self.session.refresh(partner)

        logger.info(
            "Partner created",
            partner_id=str(partner.id),
            partner_number=partner_number,
            company_name=partner.company_name,
        )

        return partner

    async def get_partner(self, partner_id: UUID | str) -> Partner | None:
        """Get partner by ID."""
        partner_id, tenant_id = self._validate_and_get_tenant(partner_id)

        query = self._get_base_partner_query(tenant_id).where(Partner.id == partner_id)

        result = await self.session.execute(query)
        partner: Partner | None = result.scalar_one_or_none()
        return partner

    async def get_partner_by_number(self, partner_number: str) -> Partner | None:
        """Get partner by partner number."""
        tenant_id = self._resolve_tenant_id()

        query = self._get_base_partner_query(tenant_id).where(
            Partner.partner_number == partner_number
        )

        result = await self.session.execute(query)
        partner: Partner | None = result.scalar_one_or_none()
        return partner

    async def list_partners(
        self,
        status: PartnerStatus | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[Partner], int]:
        """List partners with optional filtering and total count."""
        tenant_id = self._resolve_tenant_id()

        filters = self._build_partner_filters(tenant_id, status)

        list_query = (
            select(Partner)
            .where(*filters)
            .order_by(Partner.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(list_query)
        partners = list(result.scalars().all())

        count_query = select(func.count(Partner.id)).where(*filters)
        total_result = await self.session.execute(count_query)
        total_count = total_result.scalar_one()

        return partners, total_count

    async def update_partner(
        self,
        partner_id: UUID | str,
        data: PartnerUpdate,
        updated_by: str | None = None,
    ) -> Partner | None:
        """Update partner information."""
        partner_id, tenant_id = self._validate_and_get_tenant(partner_id)

        partner = await self.get_partner(partner_id)
        if not partner:
            return None

        # Update fields
        update_data = data.model_dump(exclude_unset=True, exclude={"metadata", "custom_fields"})
        for key, value in update_data.items():
            setattr(partner, key, value)

        # Update JSON fields if provided
        if data.metadata is not None:
            partner.metadata_ = data.metadata
        if data.custom_fields is not None:
            partner.custom_fields = data.custom_fields

        partner.updated_by = updated_by
        partner.updated_at = datetime.now(UTC)

        await self.session.commit()
        await self.session.refresh(partner)

        logger.info("Partner updated", partner_id=str(partner.id))

        return partner

    async def delete_partner(
        self,
        partner_id: UUID | str,
        deleted_by: str | None = None,
    ) -> bool:
        """Soft delete a partner."""
        partner_id, tenant_id = self._validate_and_get_tenant(partner_id)

        partner = await self.get_partner(partner_id)
        if not partner:
            return False

        partner.deleted_at = datetime.now(UTC)
        partner.updated_by = deleted_by

        await self.session.commit()

        logger.info("Partner deleted", partner_id=str(partner.id))

        return True

    # ========================================================================
    # Partner User Operations
    # ========================================================================

    async def create_partner_user(
        self,
        data: PartnerUserCreate,
    ) -> PartnerUser:
        """Create a partner user."""
        tenant_id = self._resolve_tenant_id()

        user = PartnerUser(
            tenant_id=tenant_id,
            **data.model_dump(),
        )

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

        logger.info(
            "Partner user created",
            user_id=str(user.id),
            partner_id=str(user.partner_id),
            email=user.email,
        )

        return user

    async def list_partner_users(
        self,
        partner_id: UUID | str,
        active_only: bool = True,
    ) -> list[PartnerUser]:
        """List users for a partner."""
        partner_id, tenant_id = self._validate_and_get_tenant(partner_id)

        query = select(PartnerUser).where(
            and_(
                PartnerUser.tenant_id == tenant_id,
                PartnerUser.partner_id == partner_id,
                PartnerUser.deleted_at.is_(None),
            )
        )

        if active_only:
            query = query.where(PartnerUser.is_active)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_partner_user(
        self,
        partner_id: UUID | str,
        user_id: UUID | str,
    ) -> PartnerUser | None:
        """Get a single partner user by ID."""
        partner_id, tenant_id = self._validate_and_get_tenant(partner_id)
        user_id = validate_uuid(user_id, "user_id")

        query = select(PartnerUser).where(
            and_(
                PartnerUser.tenant_id == tenant_id,
                PartnerUser.partner_id == partner_id,
                PartnerUser.id == user_id,
                PartnerUser.deleted_at.is_(None),
            )
        )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_partner_user(
        self,
        partner_id: UUID | str,
        user_id: UUID | str,
        data: PartnerUserUpdate,
    ) -> PartnerUser | None:
        """Update a partner user."""
        user = await self.get_partner_user(partner_id, user_id)
        if not user:
            return None

        # Apply updates
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        await self.session.commit()
        await self.session.refresh(user)

        logger.info(
            "Partner user updated",
            user_id=str(user.id),
            partner_id=str(user.partner_id),
            updates=list(update_data.keys()),
        )

        return user

    async def delete_partner_user(
        self,
        partner_id: UUID | str,
        user_id: UUID | str,
    ) -> bool:
        """Soft delete a partner user (set is_active=False)."""
        user = await self.get_partner_user(partner_id, user_id)
        if not user:
            return False

        user.is_active = False
        user.deleted_at = datetime.now(UTC)

        await self.session.commit()

        logger.info(
            "Partner user deleted",
            user_id=str(user.id),
            partner_id=str(user.partner_id),
        )

        return True

    # ========================================================================
    # Partner Application Operations
    # ========================================================================

    async def create_partner_application(
        self,
        data: PartnerApplicationCreate,
        tenant_id: str,
    ) -> PartnerApplication:
        """Create a new partner application (public endpoint)."""
        application = PartnerApplication(
            tenant_id=tenant_id,
            **data.model_dump(),
        )

        self.session.add(application)
        await self.session.commit()
        await self.session.refresh(application)

        logger.info(
            "Partner application submitted",
            application_id=str(application.id),
            company_name=application.company_name,
            contact_email=application.contact_email,
        )

        return application

    async def list_partner_applications(
        self,
        status: PartnerApplicationStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[PartnerApplication], int]:
        """List partner applications with optional status filter."""
        tenant_id = self._resolve_tenant_id()

        query = select(PartnerApplication).where(
            PartnerApplication.tenant_id == tenant_id,
        )

        if status:
            query = query.where(PartnerApplication.status == status)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination and ordering
        query = query.order_by(PartnerApplication.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.session.execute(query)
        applications = list(result.scalars().all())

        return applications, total

    async def get_partner_application(
        self,
        application_id: UUID | str,
    ) -> PartnerApplication | None:
        """Get a single partner application by ID."""
        tenant_id = self._resolve_tenant_id()
        application_id = validate_uuid(application_id, "application_id")

        query = select(PartnerApplication).where(
            and_(
                PartnerApplication.tenant_id == tenant_id,
                PartnerApplication.id == application_id,
            )
        )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def approve_partner_application(
        self,
        application_id: UUID | str,
        reviewer_id: UUID | str,
    ) -> tuple[PartnerApplication, Partner, PartnerUser]:
        """
        Approve a partner application.

        Creates a Partner record and initial PartnerUser from the application data.
        """
        application = await self.get_partner_application(application_id)
        if not application:
            raise ValueError("Application not found")

        if application.status != PartnerApplicationStatus.PENDING:
            raise ValueError("Application is not pending")

        # Create the Partner
        partner_data = PartnerCreate(
            company_name=application.company_name,
            primary_email=application.contact_email,
            phone=application.phone,
            website=application.website,
            description=application.business_description,
        )
        partner = await self.create_partner(partner_data)

        # Create the primary PartnerUser
        contact_parts = application.contact_name.split() if application.contact_name else []
        first_name = contact_parts[0] if contact_parts else "Partner"
        last_name = " ".join(contact_parts[1:]) if len(contact_parts) > 1 else "Owner"
        user_data = PartnerUserCreate(
            partner_id=partner.id,
            first_name=first_name,
            last_name=last_name,
            email=application.contact_email,
            phone=application.phone,
            role="partner_owner",
            is_primary_contact=True,
        )
        user = await self.create_partner_user(user_data)

        # Update application status
        application.status = PartnerApplicationStatus.APPROVED
        application.reviewed_by = validate_uuid(reviewer_id, "reviewer_id")
        application.reviewed_at = datetime.now(UTC)
        application.partner_id = partner.id

        await self.session.commit()
        await self.session.refresh(application)

        logger.info(
            "Partner application approved",
            application_id=str(application.id),
            partner_id=str(partner.id),
            reviewer_id=str(reviewer_id),
        )

        return application, partner, user

    async def reject_partner_application(
        self,
        application_id: UUID | str,
        reviewer_id: UUID | str,
        rejection_reason: str,
    ) -> PartnerApplication:
        """Reject a partner application with a reason."""
        application = await self.get_partner_application(application_id)
        if not application:
            raise ValueError("Application not found")

        if application.status != PartnerApplicationStatus.PENDING:
            raise ValueError("Application is not pending")

        application.status = PartnerApplicationStatus.REJECTED
        application.reviewed_by = validate_uuid(reviewer_id, "reviewer_id")
        application.reviewed_at = datetime.now(UTC)
        application.rejection_reason = rejection_reason

        await self.session.commit()
        await self.session.refresh(application)

        logger.info(
            "Partner application rejected",
            application_id=str(application.id),
            reviewer_id=str(reviewer_id),
            rejection_reason=rejection_reason,
        )

        return application

    # ========================================================================
    # Partner Account Operations
    # ========================================================================

    async def create_partner_account(
        self,
        data: PartnerAccountCreate,
    ) -> PartnerAccount:
        """Create partner-tenant account assignment."""
        tenant_id = self._resolve_tenant_id()

        payload = data.model_dump(exclude={"metadata"})
        tenant_account_id = payload.pop("tenant_id")

        account = PartnerAccount(
            tenant_id=tenant_id,
            is_active=True,
            customer_id=tenant_account_id,
            **payload,
        )

        account.metadata_ = data.metadata or {}

        self.session.add(account)

        # Update partner's total_customers count
        result = await self.session.execute(select(Partner).where(Partner.id == data.partner_id))
        partner = result.scalar_one_or_none()
        if partner:
            partner.total_customers += 1

        await self.session.commit()
        await self.session.refresh(account)

        logger.info(
            "Partner account created",
            account_id=str(account.id),
            partner_id=str(account.partner_id),
            tenant_id=str(account.customer_id),
        )

        return account

    async def list_partner_accounts(
        self,
        partner_id: UUID | str,
        active_only: bool = True,
    ) -> list[PartnerAccount]:
        """List accounts assigned to a partner."""
        partner_id, tenant_id = self._validate_and_get_tenant(partner_id)

        query = select(PartnerAccount).where(
            and_(
                PartnerAccount.tenant_id == tenant_id,
                PartnerAccount.partner_id == partner_id,
            )
        )

        if active_only:
            query = query.where(PartnerAccount.is_active)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    # ========================================================================
    # Commission Event Operations
    # ========================================================================

    async def create_commission_event(
        self,
        data: PartnerCommissionEventCreate,
    ) -> PartnerCommissionEvent:
        """Create a commission event."""
        tenant_id = self._resolve_tenant_id()

        payload = data.model_dump(exclude={"metadata_"})
        commission_tenant_id = payload.pop("tenant_id", None)

        event = PartnerCommissionEvent(
            tenant_id=tenant_id,
            event_date=datetime.now(UTC),
            customer_id=commission_tenant_id,
            **payload,
        )

        event.metadata_ = data.metadata_ or {}

        self.session.add(event)

        # Update partner's commission totals
        result = await self.session.execute(select(Partner).where(Partner.id == data.partner_id))
        partner = result.scalar_one_or_none()
        if partner:
            partner.total_commissions_earned += data.commission_amount
            if data.base_amount:
                partner.total_revenue_generated += data.base_amount

        await self.session.commit()
        await self.session.refresh(event)

        logger.info(
            "Commission event created",
            event_id=str(event.id),
            partner_id=str(event.partner_id),
            amount=str(event.commission_amount),
        )

        return event

    async def list_commission_events(
        self,
        partner_id: UUID | str,
        offset: int = 0,
        limit: int = 100,
    ) -> list[PartnerCommissionEvent]:
        """List commission events for a partner."""
        partner_id, tenant_id = self._validate_and_get_tenant(partner_id)

        query = (
            select(PartnerCommissionEvent)
            .where(
                and_(
                    PartnerCommissionEvent.tenant_id == tenant_id,
                    PartnerCommissionEvent.partner_id == partner_id,
                )
            )
            .offset(offset)
            .limit(limit)
            .order_by(PartnerCommissionEvent.event_date.desc())
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    # ========================================================================
    # Referral Lead Operations
    # ========================================================================

    async def create_referral(
        self,
        data: ReferralLeadCreate,
    ) -> ReferralLead:
        """Create a referral lead."""
        tenant_id = self._resolve_tenant_id()

        referral = ReferralLead(
            tenant_id=tenant_id,
            submitted_date=datetime.now(UTC),
            **data.model_dump(exclude={"metadata"}),
        )

        referral.metadata_ = data.metadata or {}

        self.session.add(referral)

        # Update partner's referral count
        result = await self.session.execute(select(Partner).where(Partner.id == data.partner_id))
        partner = result.scalar_one_or_none()
        if partner:
            partner.total_referrals += 1

        await self.session.commit()
        await self.session.refresh(referral)

        logger.info(
            "Referral created",
            referral_id=str(referral.id),
            partner_id=str(referral.partner_id),
            contact_email=referral.contact_email,
        )

        return referral

    async def list_referrals(
        self,
        partner_id: UUID | str,
        offset: int = 0,
        limit: int = 100,
    ) -> list[ReferralLead]:
        """List referral leads for a partner."""
        partner_id, tenant_id = self._validate_and_get_tenant(partner_id)

        query = (
            select(ReferralLead)
            .where(
                and_(
                    ReferralLead.tenant_id == tenant_id,
                    ReferralLead.partner_id == partner_id,
                    ReferralLead.deleted_at.is_(None),
                )
            )
            .offset(offset)
            .limit(limit)
            .order_by(ReferralLead.submitted_date.desc())
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_referral(
        self,
        referral_id: UUID | str,
        data: ReferralLeadUpdate | dict[str, Any],
    ) -> ReferralLead | None:
        """Update referral lead."""
        referral_id = validate_uuid(referral_id, "referral_id")
        tenant_id = self._resolve_tenant_id()

        result = await self.session.execute(
            select(ReferralLead).where(
                and_(
                    ReferralLead.id == referral_id,
                    ReferralLead.tenant_id == tenant_id,
                    ReferralLead.deleted_at.is_(None),
                )
            )
        )
        referral = result.scalar_one_or_none()
        if not referral:
            return None

        # Handle both dict and Pydantic model
        if isinstance(data, dict):
            update_data = {k: v for k, v in data.items() if k != "metadata"}
            metadata = data.get("metadata")
        else:
            update_data = data.model_dump(exclude_unset=True, exclude={"metadata"})
            metadata = data.metadata

        # Track status change for conversion tracking
        old_status = referral.status
        new_status = update_data.get("status")

        # Update fields
        for key, value in update_data.items():
            setattr(referral, key, value)

        if metadata is not None:
            referral.metadata_ = metadata

        # Handle conversion tracking
        if new_status == ReferralStatus.CONVERTED and old_status != ReferralStatus.CONVERTED:
            # Set converted_at timestamp
            referral.converted_at = datetime.now(UTC)

            # Update partner's converted referrals count
            partner_result = await self.session.execute(
                select(Partner).where(Partner.id == referral.partner_id)
            )
            partner_obj = partner_result.scalar_one_or_none()
            if partner_obj:
                partner_obj.converted_referrals += 1

        await self.session.commit()
        await self.session.refresh(referral)

        logger.info("Referral updated", referral_id=str(referral.id))

        return referral
