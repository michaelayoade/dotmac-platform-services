#!/usr/bin/env python3
"""
Assign admin role to a user.

Usage:
    python scripts/assign_admin_role.py --username newuser
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from dotmac.platform.auth.rbac_service import RBACService
from dotmac.platform.user_management.service import UserService


async def assign_admin_role(username: str) -> None:
    """Assign admin role to the specified user."""
    # Create async engine
    engine = create_async_engine(
        "postgresql+asyncpg://dotmac_user:change-me-in-production@localhost:5432/dotmac"
    )
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Get user
        user_service = UserService(session)
        user = await user_service.get_user_by_username(username)

        if not user:
            print(f"❌ User '{username}' not found")
            return

        print(f"✅ Found user: {user.username} (ID: {user.id})")

        # Get RBAC service
        rbac_service = RBACService(session)

        # Check if user already has admin role
        user_roles = await rbac_service.get_user_roles(user.id)
        if any(r.name == "admin" for r in user_roles):
            print("✅ User already has admin role")
        else:
            # Assign admin role to user (will create role if doesn't exist)
            try:
                await rbac_service.assign_role_to_user(
                    user_id=str(user.id),
                    role_name="admin",
                    granted_by=str(user.id),  # Self-assignment
                )
                print(f"✅ Assigned admin role to {username}")
            except Exception as e:
                print(f"❌ Failed to assign admin role: {e}")
                # Try creating the role first
                print("📋 Creating admin role...")
                await rbac_service.create_role(
                    name="admin",
                    description="Administrator role with full access",
                    created_by=str(user.id),
                )
                # Retry assignment
                await rbac_service.assign_role_to_user(
                    user_id=str(user.id),
                    role_name="admin",
                    granted_by=str(user.id),
                )
                print(f"✅ Assigned admin role to {username}")

        # Get user permissions
        permissions = await rbac_service.get_user_permissions(str(user.id))
        print(f"📋 User permissions: {list(permissions) if permissions else '(none)'}")

    await engine.dispose()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Assign admin role to a user")
    parser.add_argument("--username", required=True, help="Username to assign admin role to")
    args = parser.parse_args()

    asyncio.run(assign_admin_role(args.username))
