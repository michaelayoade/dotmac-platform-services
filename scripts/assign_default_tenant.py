#!/usr/bin/env python
"""
Assign default tenant to admin user.
Usage: python scripts/assign_default_tenant.py
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging

from sqlalchemy import select

from src.dotmac.platform.db import AsyncSessionLocal
from src.dotmac.platform.tenant.models import Tenant
from src.dotmac.platform.user_management.models import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def assign_default_tenant():
    """Assign a default tenant to the admin user."""
    async with AsyncSessionLocal() as session:
        # Check if admin user exists
        result = await session.execute(select(User).where(User.username == "admin"))
        admin_user = result.scalar_one_or_none()

        if not admin_user:
            logger.error("Admin user not found")
            return

        logger.info(f"Found admin user: {admin_user.id} ({admin_user.email})")

        # Check if a default tenant exists
        result = await session.execute(select(Tenant).where(Tenant.slug == "default-org"))
        tenant = result.scalar_one_or_none()

        if not tenant:
            # Create default tenant
            tenant = Tenant(
                name="Default Organization",
                slug="default-org",
                settings={"theme": "blue", "features": ["analytics", "reporting", "api_access"]},
                is_active=True,
            )
            session.add(tenant)
            await session.flush()
            logger.info(f"Created default tenant: {tenant.id} ({tenant.name})")
        else:
            logger.info(f"Found existing tenant: {tenant.id} ({tenant.name})")

        # Assign tenant to admin user
        admin_user.tenant_id = str(tenant.id)
        await session.commit()

        logger.info(f"✅ Assigned tenant {tenant.id} to user {admin_user.username}")
        logger.info(f"   User ID: {admin_user.id}")
        logger.info(f"   Tenant ID: {tenant.id}")
        logger.info(f"   Tenant Name: {tenant.name}")


if __name__ == "__main__":
    asyncio.run(assign_default_tenant())
