"""
Customer Management Service Layer.

Provides business logic and data operations for customer management.
"""

import secrets
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

import structlog
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

# Temporary tenant context helper
def get_current_tenant() -> str:
    """Temporary helper - returns default tenant ID."""
    return "default-tenant"


from dotmac.platform.customer_management.models import (
    ActivityType,
    Customer,
    CustomerActivity,
    CustomerNote,
    CustomerSegment,
    CustomerStatus,
    CustomerTag,
)
from dotmac.platform.customer_management.schemas import (
    CustomerActivityCreate,
    CustomerCreate,
    CustomerNoteCreate,
    CustomerSearchParams,
    CustomerSegmentCreate,
    CustomerUpdate,
)

logger = structlog.get_logger(__name__)


class CustomerService:
    """Service for managing customer operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_customer(
        self,
        data: CustomerCreate,
        created_by: Optional[str] = None,
    ) -> Customer:
        """Create a new customer."""
        # Generate customer number
        customer_number = await self._generate_customer_number()

        # Get current tenant
        tenant_id = get_current_tenant()

        customer = Customer(
            customer_number=customer_number,
            tenant_id=tenant_id,
            created_by=created_by,
            **data.model_dump(exclude={"tags", "metadata", "custom_fields"}),
        )

        # Set JSON fields
        customer.tags = data.tags
        customer.metadata = data.metadata
        customer.custom_fields = data.custom_fields

        self.session.add(customer)

        # Create initial activity
        activity = CustomerActivity(
            customer_id=customer.id,
            tenant_id=tenant_id,
            activity_type=ActivityType.CREATED,
            title="Customer created",
            description=f"Customer {customer.full_name} was created",
            metadata={"customer_number": customer_number},
        )
        self.session.add(activity)

        # Add tags if provided
        for tag_name in data.tags:
            tag = CustomerTag(
                customer_id=customer.id,
                tenant_id=tenant_id,
                tag_name=tag_name,
            )
            self.session.add(tag)

        await self.session.commit()
        await self.session.refresh(customer)

        logger.info(
            "Customer created",
            customer_id=str(customer.id),
            customer_number=customer_number,
            email=customer.email,
        )

        return customer

    async def get_customer(
        self,
        customer_id: UUID,
        include_activities: bool = False,
        include_notes: bool = False,
    ) -> Optional[Customer]:
        """Get customer by ID."""
        tenant_id = get_current_tenant()

        query = select(Customer).where(
            and_(
                Customer.id == customer_id,
                Customer.tenant_id == tenant_id,
                Customer.deleted_at.is_(None),
            )
        )

        if include_activities:
            query = query.options(selectinload(Customer.activities))
        if include_notes:
            query = query.options(selectinload(Customer.notes))

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_customer_by_number(
        self,
        customer_number: str,
    ) -> Optional[Customer]:
        """Get customer by customer number."""
        tenant_id = get_current_tenant()

        query = select(Customer).where(
            and_(
                Customer.customer_number == customer_number,
                Customer.tenant_id == tenant_id,
                Customer.deleted_at.is_(None),
            )
        )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_customer_by_email(
        self,
        email: str,
    ) -> Optional[Customer]:
        """Get customer by email."""
        tenant_id = get_current_tenant()

        query = select(Customer).where(
            and_(
                Customer.email == email.lower(),
                Customer.tenant_id == tenant_id,
                Customer.deleted_at.is_(None),
            )
        )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_customer(
        self,
        customer_id: UUID,
        data: CustomerUpdate,
        updated_by: Optional[str] = None,
    ) -> Optional[Customer]:
        """Update customer information."""
        customer = await self.get_customer(customer_id)
        if not customer:
            return None

        # Track status change
        old_status = customer.status

        # Update fields
        update_data = data.model_dump(exclude_unset=True, exclude={"tags"})
        for key, value in update_data.items():
            setattr(customer, key, value)

        customer.updated_by = updated_by
        customer.updated_at = datetime.now(timezone.utc)

        # Handle tags if provided
        if data.tags is not None:
            # Remove existing tags
            await self.session.execute(
                select(CustomerTag).where(CustomerTag.customer_id == customer_id)
            )
            # Add new tags
            for tag_name in data.tags:
                tag = CustomerTag(
                    customer_id=customer_id,
                    tenant_id=customer.tenant_id,
                    tag_name=tag_name,
                )
                self.session.add(tag)

        # Create activity for status change
        if old_status != customer.status:
            activity = CustomerActivity(
                customer_id=customer_id,
                tenant_id=customer.tenant_id,
                activity_type=ActivityType.STATUS_CHANGED,
                title="Status changed",
                description=f"Status changed from {old_status} to {customer.status}",
                metadata={
                    "old_status": old_status,
                    "new_status": customer.status,
                },
            )
            self.session.add(activity)

        await self.session.commit()
        await self.session.refresh(customer)

        logger.info(
            "Customer updated",
            customer_id=str(customer_id),
            updated_fields=list(update_data.keys()),
        )

        return customer

    async def delete_customer(
        self,
        customer_id: UUID,
        hard_delete: bool = False,
    ) -> bool:
        """Delete or soft-delete a customer."""
        customer = await self.get_customer(customer_id)
        if not customer:
            return False

        if hard_delete:
            await self.session.delete(customer)
        else:
            customer.soft_delete()

        await self.session.commit()

        logger.info(
            "Customer deleted",
            customer_id=str(customer_id),
            hard_delete=hard_delete,
        )

        return True

    async def search_customers(
        self,
        params: CustomerSearchParams,
    ) -> tuple[list[Customer], int]:
        """Search and filter customers."""
        tenant_id = get_current_tenant()

        # Base query
        query = select(Customer).where(
            and_(
                Customer.tenant_id == tenant_id,
                Customer.deleted_at.is_(None),
            )
        )

        # Apply filters
        conditions = []

        if params.query:
            search_pattern = f"%{params.query}%"
            conditions.append(
                or_(
                    Customer.first_name.ilike(search_pattern),
                    Customer.last_name.ilike(search_pattern),
                    Customer.company_name.ilike(search_pattern),
                    Customer.email.ilike(search_pattern),
                    Customer.customer_number.ilike(search_pattern),
                )
            )

        if params.status:
            conditions.append(Customer.status == params.status)

        if params.customer_type:
            conditions.append(Customer.customer_type == params.customer_type)

        if params.tier:
            conditions.append(Customer.tier == params.tier)

        if params.country:
            conditions.append(Customer.country == params.country)

        if params.assigned_to:
            conditions.append(Customer.assigned_to == params.assigned_to)

        if params.segment_id:
            conditions.append(Customer.segment_id == params.segment_id)

        if params.created_after:
            conditions.append(Customer.created_at >= params.created_after)

        if params.created_before:
            conditions.append(Customer.created_at <= params.created_before)

        if params.last_purchase_after:
            conditions.append(Customer.last_purchase_date >= params.last_purchase_after)

        if params.last_purchase_before:
            conditions.append(Customer.last_purchase_date <= params.last_purchase_before)

        if params.min_lifetime_value is not None:
            conditions.append(Customer.lifetime_value >= params.min_lifetime_value)

        if params.max_lifetime_value is not None:
            conditions.append(Customer.lifetime_value <= params.max_lifetime_value)

        # Apply tag filter
        if params.tags:
            tag_subquery = (
                select(CustomerTag.customer_id)
                .where(CustomerTag.tag_name.in_(params.tags))
                .group_by(CustomerTag.customer_id)
                .having(func.count(CustomerTag.tag_name) == len(params.tags))
                .subquery()
            )
            conditions.append(Customer.id.in_(select(tag_subquery)))

        if conditions:
            query = query.where(and_(*conditions))

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Apply sorting
        sort_field = getattr(Customer, params.sort_by, Customer.created_at)
        if params.sort_order == "desc":
            query = query.order_by(sort_field.desc())
        else:
            query = query.order_by(sort_field.asc())

        # Apply pagination
        offset = (params.page - 1) * params.page_size
        query = query.offset(offset).limit(params.page_size)

        # Execute query
        result = await self.session.execute(query)
        customers = list(result.scalars().all())

        return customers, total

    async def add_activity(
        self,
        customer_id: UUID,
        data: CustomerActivityCreate,
        performed_by: Optional[UUID] = None,
    ) -> CustomerActivity:
        """Add activity to customer timeline."""
        customer = await self.get_customer(customer_id)
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")

        activity = CustomerActivity(
            customer_id=customer_id,
            tenant_id=customer.tenant_id,
            performed_by=performed_by,
            **data.model_dump(),
        )

        self.session.add(activity)

        # Update last contact date
        customer.last_contact_date = datetime.now(timezone.utc)

        await self.session.commit()
        await self.session.refresh(activity)

        return activity

    async def get_activities(
        self,
        customer_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CustomerActivity]:
        """Get customer activities."""
        query = (
            select(CustomerActivity)
            .where(CustomerActivity.customer_id == customer_id)
            .order_by(CustomerActivity.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def add_note(
        self,
        customer_id: UUID,
        data: CustomerNoteCreate,
        created_by_id: UUID,
    ) -> CustomerNote:
        """Add note to customer."""
        customer = await self.get_customer(customer_id)
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")

        note = CustomerNote(
            customer_id=customer_id,
            tenant_id=customer.tenant_id,
            created_by_id=created_by_id,
            **data.model_dump(),
        )

        self.session.add(note)

        # Create activity
        activity = CustomerActivity(
            customer_id=customer_id,
            tenant_id=customer.tenant_id,
            activity_type=ActivityType.NOTE_ADDED,
            title="Note added",
            description=f"Note '{data.subject}' was added",
            performed_by=created_by_id,
            metadata={"note_id": str(note.id)},
        )
        self.session.add(activity)

        await self.session.commit()
        await self.session.refresh(note)

        return note

    async def get_notes(
        self,
        customer_id: UUID,
        include_internal: bool = True,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CustomerNote]:
        """Get customer notes."""
        query = select(CustomerNote).where(
            and_(
                CustomerNote.customer_id == customer_id,
                CustomerNote.deleted_at.is_(None),
            )
        )

        if not include_internal:
            query = query.where(CustomerNote.is_internal == False)

        query = query.order_by(CustomerNote.created_at.desc()).offset(offset).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_metrics(
        self,
        customer_id: UUID,
        purchase_amount: Optional[float] = None,
    ) -> None:
        """Update customer metrics after a purchase or event."""
        customer = await self.get_customer(customer_id)
        if not customer:
            return

        if purchase_amount:
            customer.lifetime_value += purchase_amount
            customer.total_purchases += 1
            customer.last_purchase_date = datetime.now(timezone.utc)

            if not customer.first_purchase_date:
                customer.first_purchase_date = datetime.now(timezone.utc)

            # Update average order value
            if customer.total_purchases > 0:
                customer.average_order_value = (
                    customer.lifetime_value / customer.total_purchases
                )

        await self.session.commit()

    async def create_segment(
        self,
        data: CustomerSegmentCreate,
    ) -> CustomerSegment:
        """Create a customer segment."""
        tenant_id = get_current_tenant()

        segment = CustomerSegment(
            tenant_id=tenant_id,
            **data.model_dump(),
        )

        self.session.add(segment)
        await self.session.commit()
        await self.session.refresh(segment)

        if segment.is_dynamic:
            await self.recalculate_segment(segment.id)

        return segment

    async def recalculate_segment(
        self,
        segment_id: UUID,
    ) -> int:
        """Recalculate dynamic segment membership."""
        segment = await self.session.get(CustomerSegment, segment_id)
        if not segment:
            return 0

        # Here you would implement the logic to evaluate segment criteria
        # and update customer assignments based on the criteria
        # This is simplified for the example

        # Update last calculated time
        segment.last_calculated = datetime.now(timezone.utc)
        await self.session.commit()

        return segment.member_count

    async def get_customer_metrics(self) -> dict[str, Any]:
        """Get aggregated customer metrics."""
        tenant_id = get_current_tenant()

        # Total customers
        total_query = select(func.count(Customer.id)).where(
            and_(
                Customer.tenant_id == tenant_id,
                Customer.deleted_at.is_(None),
            )
        )
        total_result = await self.session.execute(total_query)
        total_customers = total_result.scalar() or 0

        # Active customers
        active_query = select(func.count(Customer.id)).where(
            and_(
                Customer.tenant_id == tenant_id,
                Customer.status == CustomerStatus.ACTIVE,
                Customer.deleted_at.is_(None),
            )
        )
        active_result = await self.session.execute(active_query)
        active_customers = active_result.scalar() or 0

        # Average lifetime value
        avg_ltv_query = select(func.avg(Customer.lifetime_value)).where(
            and_(
                Customer.tenant_id == tenant_id,
                Customer.deleted_at.is_(None),
            )
        )
        avg_ltv_result = await self.session.execute(avg_ltv_query)
        avg_lifetime_value = avg_ltv_result.scalar() or 0

        # Total revenue
        total_revenue_query = select(func.sum(Customer.lifetime_value)).where(
            and_(
                Customer.tenant_id == tenant_id,
                Customer.deleted_at.is_(None),
            )
        )
        total_revenue_result = await self.session.execute(total_revenue_query)
        total_revenue = total_revenue_result.scalar() or 0

        return {
            "total_customers": total_customers,
            "active_customers": active_customers,
            "average_lifetime_value": float(avg_lifetime_value),
            "total_revenue": float(total_revenue),
            "churn_rate": self._calculate_churn_rate(total_customers, active_customers),
        }

    def _calculate_churn_rate(self, total: int, active: int) -> float:
        """Calculate customer churn rate."""
        if total == 0:
            return 0.0
        return ((total - active) / total) * 100

    async def _generate_customer_number(self) -> str:
        """Generate unique customer number."""
        prefix = "CUS"
        random_part = secrets.token_hex(4).upper()
        timestamp = datetime.now().strftime("%y%m")
        return f"{prefix}-{timestamp}-{random_part}"