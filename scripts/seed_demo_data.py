#!/usr/bin/env python3
"""
Demo Data Seeding Script

Seeds the staging database with realistic demo data for:
- Demo tenant
- User accounts (various roles)
- Sample invoices
- Network infrastructure
"""

import asyncio
import logging
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.auth.core import hash_password
from dotmac.platform.db import AsyncSessionLocal
from dotmac.platform.tenant.models import Tenant, TenantStatus
from dotmac.platform.user_management.models import User, UserRole, UserStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEMO_TENANT_ID = "demo-tenant"

# Demo user accounts
DEMO_USERS = [
    {
        "email": "admin@dotmac.com",
        "username": "admin",
        "first_name": "Platform",
        "last_name": "Administrator",
        "password": "Admin123!",
        "role": UserRole.PLATFORM_ADMIN,
        "is_platform_admin": True,
    },
    {
        "email": "ops-admin@demo.com",
        "username": "ops-admin",
        "first_name": "Operations",
        "last_name": "Administrator",
        "password": "OpsAdmin123!",
        "role": UserRole.ADMIN,
        "is_platform_admin": False,
    },
    {
        "email": "billing@demo.com",
        "username": "billing-manager",
        "first_name": "Billing",
        "last_name": "Manager",
        "password": "Billing123!",
        "role": UserRole.BILLING_MANAGER,
        "is_platform_admin": False,
    },
    {
        "email": "support@demo.com",
        "username": "support-agent",
        "first_name": "Support",
        "last_name": "Agent",
        "password": "Support123!",
        "role": UserRole.SUPPORT,
        "is_platform_admin": False,
    },
    {
        "email": "customer@demo.com",
        "username": "demo-customer",
        "first_name": "Demo",
        "last_name": "Customer",
        "password": "Customer123!",
        "role": UserRole.USER,
        "is_platform_admin": False,
    },
]


async def create_demo_tenant(db: AsyncSession) -> Tenant:
    """Create or get demo tenant."""
    stmt = select(Tenant).where(Tenant.id == DEMO_TENANT_ID)
    result = await db.execute(stmt)
    tenant = result.scalar_one_or_none()

    if tenant:
        logger.info(f"Demo tenant already exists: {DEMO_TENANT_ID}")
        return tenant

    tenant = Tenant(
        id=DEMO_TENANT_ID,
        name="Demo Company",
        slug="demo-company",
        status=TenantStatus.ACTIVE,
        company_name="Demo Company Inc.",
        contact_email="contact@demo-company.com",
        contact_phone="+1-555-DEMO-123",
        address="123 Demo Street",
        city="Demo City",
        state="NY",
        postal_code="10001",
        country="US",
        timezone="America/New_York",
        settings={
            "billing_enabled": True,
            "crm_enabled": True,
            "max_users": 1000,
            "features": {
                "analytics": True,
                "dunning": True,
                "ticketing": True,
            },
        },
    )

    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)

    logger.info(f"Created demo tenant: {tenant.name} ({tenant.id})")
    return tenant


async def create_demo_users(db: AsyncSession) -> list[User]:
    """Create demo user accounts."""
    users = []

    for user_data in DEMO_USERS:
        # Check if user already exists
        stmt = select(User).where(User.email == user_data["email"])
        result = await db.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            logger.info(f"User already exists: {user_data['email']}")
            users.append(existing_user)
            continue

        # Create new user
        user = User(
            id=uuid4(),
            tenant_id=None if user_data["is_platform_admin"] else DEMO_TENANT_ID,
            email=user_data["email"],
            username=user_data["username"],
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            password_hash=hash_password(user_data["password"]),
            role=user_data["role"],
            is_active=True,
            is_verified=True,
            status=UserStatus.ACTIVE,
            is_platform_admin=user_data["is_platform_admin"],
            preferences={
                "theme": "light",
                "notifications_enabled": True,
            },
        )

        db.add(user)
        users.append(user)
        logger.info(
            f"Created user: {user.email} ({user.role.value}) - "
            f"Platform Admin: {user.is_platform_admin}"
        )

    await db.commit()
    return users


async def main():
    """Main seeding function."""
    logger.info("=" * 60)
    logger.info("Starting Demo Data Seeding")
    logger.info("=" * 60)

    async with AsyncSessionLocal() as db:
        try:
            # Create demo tenant
            logger.info("\n1. Creating demo tenant...")
            tenant = await create_demo_tenant(db)

            # Create demo users
            logger.info("\n2. Creating demo users...")
            users = await create_demo_users(db)

            subscriptions: list[object] = []

            logger.info("\n" + "=" * 60)
            logger.info("Demo Data Seeding Complete!")
            logger.info("=" * 60)
            logger.info(f"\nTenant: {tenant.name}")
            logger.info(f"Users: {len(users)}")
            logger.info(f"Subscriptions: {len(subscriptions)}")

            logger.info("\n📝 Demo Accounts:")
            logger.info("-" * 60)
            for user_data in DEMO_USERS:
                logger.info(
                    f"Email: {user_data['email']:<30} Password: {user_data['password']}"
                )
            logger.info("-" * 60)

        except Exception as e:
            logger.error(f"Error seeding demo data: {e}", exc_info=True)
            raise


if __name__ == "__main__":
    asyncio.run(main())
