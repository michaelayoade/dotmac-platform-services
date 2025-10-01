"""
Regression test for CustomerContactLink ORM relationship.

This test file ensures the Customer ↔ Contact many-to-many relationship
works correctly with proper foreign keys and relationship mappings.

This would have caught the NoForeignKeysError that occurred when contact_id
was missing a ForeignKey constraint.
"""

import pytest
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from dotmac.platform.customer_management.models import (
    ContactRole,
    Customer,
    CustomerContactLink,
    CustomerStatus,
    CustomerTier,
    CustomerType,
)
from dotmac.platform.contacts.models import Contact


@pytest.mark.asyncio
class TestCustomerContactRelationship:
    """Test CustomerContactLink ORM relationship integrity."""

    async def test_customer_contact_link_creation(self, db_session):
        """Test basic creation of customer-contact link."""
        # Create customer
        customer = Customer(
            customer_number="TEST001",
            tenant_id="test-tenant",
            first_name="John",
            last_name="Doe",
            email=f"john.doe.{uuid4()}@example.com",
            status=CustomerStatus.ACTIVE,
            customer_type=CustomerType.INDIVIDUAL,
            tier=CustomerTier.FREE,
        )
        db_session.add(customer)
        await db_session.flush()

        # Create contact
        contact = Contact(
            tenant_id="test-tenant",
            first_name="Jane",
            last_name="Smith",
            email=f"jane.smith.{uuid4()}@example.com",
        )
        db_session.add(contact)
        await db_session.flush()

        # Create link
        link = CustomerContactLink(
            customer_id=customer.id,
            contact_id=contact.id,
            tenant_id="test-tenant",
            role=ContactRole.PRIMARY,
            is_primary_for_role=True,
        )
        db_session.add(link)
        await db_session.flush()

        # Verify link was created
        result = await db_session.execute(
            select(CustomerContactLink).where(
                CustomerContactLink.customer_id == customer.id
            )
        )
        loaded_link = result.scalar_one()
        assert loaded_link.contact_id == contact.id
        assert loaded_link.role == ContactRole.PRIMARY

    async def test_foreign_key_constraint_enforced(self, db_session):
        """Test that foreign key constraints are enforced."""
        # Create customer
        customer = Customer(
            customer_number="TEST002",
            tenant_id="test-tenant",
            first_name="John",
            last_name="Doe",
            email=f"john.{uuid4()}@example.com",
            status=CustomerStatus.ACTIVE,
            customer_type=CustomerType.INDIVIDUAL,
            tier=CustomerTier.FREE,
        )
        db_session.add(customer)
        await db_session.flush()

        # Try to create link with non-existent contact_id
        invalid_contact_id = uuid4()
        link = CustomerContactLink(
            customer_id=customer.id,
            contact_id=invalid_contact_id,  # Non-existent
            tenant_id="test-tenant",
            role=ContactRole.PRIMARY,
        )
        db_session.add(link)

        # Should raise IntegrityError
        with pytest.raises(IntegrityError):
            await db_session.flush()

    async def test_cascade_delete_behavior(self, db_session):
        """Test CASCADE delete when customer is deleted."""
        # Create customer and contact
        customer = Customer(
            customer_number="TEST003",
            tenant_id="test-tenant",
            first_name="John",
            last_name="Doe",
            email=f"john.{uuid4()}@example.com",
            status=CustomerStatus.ACTIVE,
            customer_type=CustomerType.INDIVIDUAL,
            tier=CustomerTier.FREE,
        )
        contact = Contact(
            tenant_id="test-tenant",
            first_name="Jane",
            last_name="Smith",
            email=f"jane.{uuid4()}@example.com",
        )
        db_session.add(customer)
        db_session.add(contact)
        await db_session.flush()

        # Create link
        link = CustomerContactLink(
            customer_id=customer.id,
            contact_id=contact.id,
            tenant_id="test-tenant",
            role=ContactRole.PRIMARY,
        )
        db_session.add(link)
        await db_session.flush()
        link_id = link.id

        # Delete customer
        await db_session.delete(customer)
        await db_session.flush()

        # Link should be cascaded and deleted
        result = await db_session.execute(
            select(CustomerContactLink).where(CustomerContactLink.id == link_id)
        )
        assert result.scalar_one_or_none() is None

    async def test_multiple_roles_for_single_contact(self, db_session):
        """Test that a contact can have multiple roles with same customer."""
        # Create customer and contact
        customer = Customer(
            customer_number="TEST004",
            tenant_id="test-tenant",
            first_name="John",
            last_name="Doe",
            email=f"john.{uuid4()}@example.com",
            status=CustomerStatus.ACTIVE,
            customer_type=CustomerType.INDIVIDUAL,
            tier=CustomerTier.FREE,
        )
        contact = Contact(
            tenant_id="test-tenant",
            first_name="Jane",
            last_name="Smith",
            email=f"jane.{uuid4()}@example.com",
        )
        db_session.add(customer)
        db_session.add(contact)
        await db_session.flush()

        # Add contact with multiple roles
        link1 = CustomerContactLink(
            customer_id=customer.id,
            contact_id=contact.id,
            tenant_id="test-tenant",
            role=ContactRole.PRIMARY,
            is_primary_for_role=True,
        )
        link2 = CustomerContactLink(
            customer_id=customer.id,
            contact_id=contact.id,
            tenant_id="test-tenant",
            role=ContactRole.TECHNICAL,
            is_primary_for_role=True,
        )
        db_session.add(link1)
        db_session.add(link2)
        await db_session.flush()

        # Verify both roles exist
        result = await db_session.execute(
            select(CustomerContactLink)
            .where(CustomerContactLink.customer_id == customer.id)
            .order_by(CustomerContactLink.role)
        )
        links = result.scalars().all()
        assert len(links) == 2
        assert links[0].role == ContactRole.PRIMARY
        assert links[1].role == ContactRole.TECHNICAL
