#!/usr/bin/env python
"""
Create or update a user to be a platform administrator.

Usage:
    python scripts/create_platform_admin.py --email admin@example.com
    python scripts/create_platform_admin.py --email admin@example.com --password NewPassword123!
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from src.dotmac.platform.database import get_db_session, init_db
from src.dotmac.platform.auth.password_service import PasswordService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_or_update_platform_admin(email: str, password: str | None = None):
    """Create or update a user to be a platform administrator."""
    try:
        await init_db()

        async with get_db_session() as db:
            # Check if user exists
            result = await db.execute(
                text("SELECT id, username, is_platform_admin FROM users WHERE email = :email"),
                {"email": email},
            )
            user = result.first()

            if not user:
                logger.error(f"❌ User with email {email} not found!")
                logger.info("💡 Available users:")
                users_result = await db.execute(
                    text("SELECT email, username, is_platform_admin FROM users LIMIT 10")
                )
                for u in users_result:
                    admin_status = "✅ Platform Admin" if u[2] else ""
                    logger.info(f"   - {u[0]} ({u[1]}) {admin_status}")
                return False

            user_id, username, is_already_admin = user

            # Update user to be platform admin
            update_query = text(
                """
                UPDATE users
                SET is_platform_admin = true,
                    tenant_id = NULL,
                    permissions = CASE
                        WHEN permissions IS NULL THEN '["platform:admin"]'::jsonb
                        WHEN NOT permissions @> '["platform:admin"]'::jsonb
                        THEN permissions || '["platform:admin"]'::jsonb
                        ELSE permissions
                    END,
                    updated_at = NOW()
                WHERE id = :user_id
            """
            )
            await db.execute(update_query, {"user_id": user_id})

            # Update password if provided
            if password:
                password_service = PasswordService()
                hashed_password = password_service.hash_password(password)
                await db.execute(
                    text("UPDATE users SET password_hash = :password WHERE id = :user_id"),
                    {"user_id": user_id, "password": hashed_password},
                )
                logger.info(f"✅ Password updated for {email}")

            await db.commit()

            if is_already_admin:
                logger.info(f"✅ User {email} ({username}) was already a platform admin")
            else:
                logger.info(f"✅ User {email} ({username}) is now a platform admin!")

            logger.info(
                """
Platform Admin Capabilities:
  - Cross-tenant access to all data
  - Can impersonate any tenant via X-Target-Tenant-ID header
  - Full access to platform administration endpoints
  - All platform admin actions are audit logged

API Endpoints:
  - GET /api/v1/admin/platform/health
  - GET /api/v1/admin/platform/tenants
  - GET /api/v1/admin/platform/stats
  - POST /api/v1/admin/platform/search
  - POST /api/v1/admin/platform/tenants/{id}/impersonate
  - POST /api/v1/admin/platform/system/cache/clear
  - GET /api/v1/admin/platform/system/config
"""
            )

            return True

    except Exception as e:
        logger.error(f"❌ Failed to create platform admin: {str(e)}")
        raise


async def main():
    parser = argparse.ArgumentParser(
        description="Create or update a user to be a platform administrator"
    )
    parser.add_argument("--email", required=True, help="Email of the user to make platform admin")
    parser.add_argument(
        "--password",
        help="New password for the user (optional, only if changing password)",
    )

    args = parser.parse_args()

    logger.info(f"🔧 Setting up platform admin for: {args.email}")

    success = await create_or_update_platform_admin(args.email, args.password)

    if success:
        logger.info("✨ Platform admin setup complete!")
        if args.password:
            logger.info(
                f"\n📝 Credentials:\n   Email: {args.email}\n   Password: {args.password}\n"
            )
        else:
            logger.info(f"\n📝 Email: {args.email}\n   (password unchanged)\n")
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
