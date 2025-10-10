#!/usr/bin/env python
"""
Seed development database with test data.
Usage: python scripts/seed_data.py [--env=development]
"""

import argparse
import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging

from sqlalchemy import text
from src.dotmac.platform.auth.password_service import PasswordService
from src.dotmac.platform.secrets.models import Secret

from src.dotmac.platform.auth.models import Permission, Role, User
from src.dotmac.platform.billing.models import Customer, Invoice, Price, Product, Subscription
from src.dotmac.platform.database import get_db_session, init_db
from src.dotmac.platform.tenant.models import Tenant

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test data
TEST_USERS = [
    {
        "username": "admin",
        "email": "admin@example.com",
        "password": "Admin123!@#",
        "first_name": "Admin",
        "last_name": "User",
        "is_active": True,
        "is_superuser": True,
        "is_platform_admin": True,  # Platform admin with cross-tenant access
        "roles": ["admin", "user"],
        "permissions": ["platform:admin"],  # Grant platform admin permission
    },
    {
        "username": "john.doe",
        "email": "john.doe@example.com",
        "password": "Test123!@#",
        "first_name": "John",
        "last_name": "Doe",
        "is_active": True,
        "is_superuser": False,
        "roles": ["user"],
    },
    {
        "username": "jane.smith",
        "email": "jane.smith@example.com",
        "password": "Test123!@#",
        "first_name": "Jane",
        "last_name": "Smith",
        "is_active": True,
        "is_superuser": False,
        "roles": ["user", "developer"],
    },
    {
        "username": "bob.wilson",
        "email": "bob.wilson@example.com",
        "password": "Test123!@#",
        "first_name": "Bob",
        "last_name": "Wilson",
        "is_active": False,  # Inactive user for testing
        "is_superuser": False,
        "roles": ["user"],
    },
]

TEST_TENANTS = [
    {
        "name": "Acme Corporation",
        "slug": "acme-corp",
        "settings": {"theme": "blue", "features": ["analytics", "reporting", "api_access"]},
    },
    {
        "name": "TechStart Inc",
        "slug": "techstart",
        "settings": {"theme": "green", "features": ["analytics"]},
    },
    {
        "name": "Global Enterprises",
        "slug": "global-ent",
        "settings": {
            "theme": "purple",
            "features": ["analytics", "reporting", "api_access", "premium_support"],
        },
    },
]

TEST_ROLES = [
    {
        "name": "admin",
        "description": "Administrator role with full access",
        "permissions": ["read:all", "write:all", "delete:all", "admin:all"],
    },
    {
        "name": "developer",
        "description": "Developer role with API access",
        "permissions": ["read:api", "write:api", "read:secrets", "write:secrets"],
    },
    {"name": "user", "description": "Standard user role", "permissions": ["read:own", "write:own"]},
    {
        "name": "viewer",
        "description": "Read-only access",
        "permissions": ["read:public", "read:shared"],
    },
]

TEST_PRODUCTS = [
    {
        "name": "Basic Plan",
        "description": "Essential features for small teams",
        "features": ["5 users", "10GB storage", "Basic support"],
        "prices": [
            {"amount": 9.99, "currency": "USD", "interval": "month"},
            {"amount": 99.99, "currency": "USD", "interval": "year"},
        ],
    },
    {
        "name": "Professional Plan",
        "description": "Advanced features for growing teams",
        "features": ["25 users", "100GB storage", "Priority support", "API access"],
        "prices": [
            {"amount": 29.99, "currency": "USD", "interval": "month"},
            {"amount": 299.99, "currency": "USD", "interval": "year"},
        ],
    },
    {
        "name": "Enterprise Plan",
        "description": "Complete solution for large organizations",
        "features": ["Unlimited users", "1TB storage", "24/7 support", "Custom integrations"],
        "prices": [
            {"amount": 99.99, "currency": "USD", "interval": "month"},
            {"amount": 999.99, "currency": "USD", "interval": "year"},
        ],
    },
]

TEST_SECRETS = [
    {
        "name": "api_key_production",
        "path": "api/keys/production",
        "value": {"key": "sk_live_test123456789", "environment": "production"},
        "metadata": {"created_by": "admin", "purpose": "Production API access"},
    },
    {
        "name": "database_credentials",
        "path": "database/postgres/main",
        "value": {
            "host": "localhost",
            "port": 5432,
            "database": "dotmac_db",
            "username": "postgres",
            "password": "encrypted_password_here",
        },
        "metadata": {"service": "postgresql", "environment": "development"},
    },
    {
        "name": "smtp_settings",
        "path": "email/smtp/default",
        "value": {
            "host": "smtp.mailtrap.io",
            "port": 587,
            "username": "test_user",
            "password": "test_password",
            "use_tls": True,
        },
        "metadata": {"provider": "mailtrap", "purpose": "Email testing"},
    },
]


class DataSeeder:
    def __init__(self):
        self.password_service = PasswordService()
        self.db = None

    async def seed_all(self, clear_existing=False):
        """Seed all test data."""
        try:
            # Initialize database connection
            await init_db()

            async with get_db_session() as db:
                self.db = db

                if clear_existing:
                    await self.clear_existing_data()

                # Seed in order of dependencies
                await self.seed_roles()
                await self.seed_permissions()
                await self.seed_tenants()
                await self.seed_users()
                await self.seed_tenant_users()
                await self.seed_products()
                await self.seed_secrets()
                await self.seed_subscriptions()

                await db.commit()
                logger.info("✅ Database seeding completed successfully!")

        except Exception as e:
            logger.error(f"❌ Seeding failed: {str(e)}")
            if self.db:
                await self.db.rollback()
            raise

    async def clear_existing_data(self):
        """Clear existing test data (be careful!)."""
        logger.info("🧹 Clearing existing data...")

        # Clear in reverse order of dependencies
        tables = [
            "invoices",
            "invoice_items",
            "subscriptions",
            "prices",
            "products",
            "customers",
            "secrets",
            "tenant_users",
            "users",
            "tenants",
            "role_permissions",
            "permissions",
            "roles",
        ]

        for table in tables:
            try:
                await self.db.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
            except Exception as e:
                logger.warning(f"Could not truncate {table}: {e}")

    async def seed_roles(self):
        """Seed role data."""
        logger.info("👥 Seeding roles...")

        for role_data in TEST_ROLES:
            # Check if role exists
            existing = await self.db.execute(
                text("SELECT id FROM roles WHERE name = :name"), {"name": role_data["name"]}
            )
            if not existing.first():
                role = Role(name=role_data["name"], description=role_data["description"])
                self.db.add(role)

        await self.db.commit()

    async def seed_permissions(self):
        """Seed permission data."""
        logger.info("🔐 Seeding permissions...")

        # Collect all unique permissions
        all_permissions = set()
        for role in TEST_ROLES:
            all_permissions.update(role["permissions"])

        for perm_name in all_permissions:
            # Check if permission exists
            existing = await self.db.execute(
                text("SELECT id FROM permissions WHERE name = :name"), {"name": perm_name}
            )
            if not existing.first():
                permission = Permission(
                    name=perm_name, description=f"Permission to {perm_name.replace(':', ' ')}"
                )
                self.db.add(permission)

        await self.db.commit()

        # Link permissions to roles
        for role_data in TEST_ROLES:
            role_result = await self.db.execute(
                text("SELECT id FROM roles WHERE name = :name"), {"name": role_data["name"]}
            )
            role_id = role_result.first()[0]

            for perm_name in role_data["permissions"]:
                perm_result = await self.db.execute(
                    text("SELECT id FROM permissions WHERE name = :name"), {"name": perm_name}
                )
                perm_id = perm_result.first()[0]

                # Check if link exists
                existing = await self.db.execute(
                    text(
                        "SELECT 1 FROM role_permissions WHERE role_id = :role_id AND permission_id = :perm_id"
                    ),
                    {"role_id": role_id, "perm_id": perm_id},
                )
                if not existing.first():
                    await self.db.execute(
                        text(
                            "INSERT INTO role_permissions (role_id, permission_id) VALUES (:role_id, :perm_id)"
                        ),
                        {"role_id": role_id, "perm_id": perm_id},
                    )

    async def seed_tenants(self):
        """Seed tenant data."""
        logger.info("🏢 Seeding tenants...")

        for tenant_data in TEST_TENANTS:
            # Check if tenant exists
            existing = await self.db.execute(
                text("SELECT id FROM tenants WHERE slug = :slug"), {"slug": tenant_data["slug"]}
            )
            if not existing.first():
                tenant = Tenant(
                    name=tenant_data["name"],
                    slug=tenant_data["slug"],
                    settings=tenant_data["settings"],
                    is_active=True,
                )
                self.db.add(tenant)

        await self.db.commit()

    async def seed_users(self):
        """Seed user data."""
        logger.info("👤 Seeding users...")

        for user_data in TEST_USERS:
            # Check if user exists
            existing = await self.db.execute(
                text("SELECT id FROM users WHERE username = :username"),
                {"username": user_data["username"]},
            )
            if not existing.first():
                # Hash password
                hashed_password = self.password_service.hash_password(user_data["password"])

                user = User(
                    username=user_data["username"],
                    email=user_data["email"],
                    password_hash=hashed_password,
                    full_name=f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip(),
                    is_active=user_data["is_active"],
                    is_superuser=user_data["is_superuser"],
                    is_platform_admin=user_data.get("is_platform_admin", False),
                    is_verified=True,
                    roles=user_data.get("roles", []),
                    permissions=user_data.get("permissions", []),
                    tenant_id=(
                        None if user_data.get("is_platform_admin") else user_data.get("tenant_id")
                    ),
                    created_at=datetime.utcnow(),
                )
                self.db.add(user)
                await self.db.commit()

        await self.db.commit()

    async def seed_tenant_users(self):
        """Link users to tenants."""
        logger.info("🔗 Linking users to tenants...")

        # Get all users and tenants
        users = await self.db.execute(text("SELECT id, username FROM users"))
        tenants = await self.db.execute(text("SELECT id, slug FROM tenants"))

        user_list = users.fetchall()
        tenant_list = tenants.fetchall()

        if user_list and tenant_list:
            # Assign admin to all tenants
            admin_user = next((u for u in user_list if u[1] == "admin"), None)
            if admin_user:
                for tenant in tenant_list:
                    await self.db.execute(
                        text(
                            "INSERT INTO tenant_users (tenant_id, user_id, role) VALUES (:tenant_id, :user_id, :role) ON CONFLICT DO NOTHING"
                        ),
                        {"tenant_id": tenant[0], "user_id": admin_user[0], "role": "owner"},
                    )

            # Assign other users to specific tenants
            assignments = [
                ("john.doe", "acme-corp", "member"),
                ("jane.smith", "techstart", "admin"),
                ("bob.wilson", "global-ent", "viewer"),
            ]

            for username, tenant_slug, role in assignments:
                user = next((u for u in user_list if u[1] == username), None)
                tenant = next((t for t in tenant_list if t[1] == tenant_slug), None)

                if user and tenant:
                    await self.db.execute(
                        text(
                            "INSERT INTO tenant_users (tenant_id, user_id, role) VALUES (:tenant_id, :user_id, :role) ON CONFLICT DO NOTHING"
                        ),
                        {"tenant_id": tenant[0], "user_id": user[0], "role": role},
                    )

        await self.db.commit()

    async def seed_products(self):
        """Seed product and pricing data."""
        logger.info("💰 Seeding products and pricing...")

        for product_data in TEST_PRODUCTS:
            # Check if product exists
            existing = await self.db.execute(
                text("SELECT id FROM products WHERE name = :name"), {"name": product_data["name"]}
            )
            if not existing.first():
                product = Product(
                    name=product_data["name"],
                    description=product_data["description"],
                    features=product_data["features"],
                    is_active=True,
                )
                self.db.add(product)
                await self.db.commit()

                # Add prices
                for price_data in product_data["prices"]:
                    price = Price(
                        product_id=product.id,
                        amount=price_data["amount"],
                        currency=price_data["currency"],
                        interval=price_data["interval"],
                        is_active=True,
                    )
                    self.db.add(price)

        await self.db.commit()

    async def seed_secrets(self):
        """Seed secret data (for development only!)."""
        logger.info("🔑 Seeding secrets...")

        # Get first tenant for secrets
        tenant_result = await self.db.execute(text("SELECT id FROM tenants LIMIT 1"))
        tenant_id = tenant_result.first()[0] if tenant_result.first() else None

        for secret_data in TEST_SECRETS:
            # Check if secret exists
            existing = await self.db.execute(
                text("SELECT id FROM secrets WHERE path = :path"), {"path": secret_data["path"]}
            )
            if not existing.first():
                secret = Secret(
                    name=secret_data["name"],
                    path=secret_data["path"],
                    encrypted_value=str(
                        secret_data["value"]
                    ),  # In real app, this would be encrypted
                    metadata=secret_data["metadata"],
                    tenant_id=tenant_id,
                    version=1,
                    is_active=True,
                )
                self.db.add(secret)

        await self.db.commit()

    async def seed_subscriptions(self):
        """Seed subscription data."""
        logger.info("📊 Seeding subscriptions...")

        # Get users and products
        users = await self.db.execute(
            text("SELECT id, username FROM users WHERE username != 'admin'")
        )
        products = await self.db.execute(text("SELECT id, name FROM products"))

        user_list = users.fetchall()
        product_list = products.fetchall()

        if user_list and product_list:
            subscription_data = [
                (user_list[0][0], product_list[0][0], "active"),  # John - Basic
                (user_list[1][0], product_list[1][0], "active"),  # Jane - Professional
                (user_list[2][0], product_list[0][0], "canceled"),  # Bob - Basic (canceled)
            ]

            for user_id, product_id, status in subscription_data:
                # Get price for product
                price_result = await self.db.execute(
                    text(
                        "SELECT id, amount FROM prices WHERE product_id = :product_id AND interval = 'month' LIMIT 1"
                    ),
                    {"product_id": product_id},
                )
                price = price_result.first()

                if price:
                    # Create customer if not exists
                    customer_result = await self.db.execute(
                        text("SELECT id FROM customers WHERE user_id = :user_id"),
                        {"user_id": user_id},
                    )
                    customer = customer_result.first()

                    if not customer:
                        new_customer = Customer(
                            user_id=user_id,
                            stripe_customer_id=f"cus_test_{user_id}",
                            payment_method_id=f"pm_test_{user_id}",
                        )
                        self.db.add(new_customer)
                        await self.db.commit()
                        customer_id = new_customer.id
                    else:
                        customer_id = customer[0]

                    # Create subscription
                    subscription = Subscription(
                        customer_id=customer_id,
                        price_id=price[0],
                        status=status,
                        current_period_start=datetime.utcnow(),
                        current_period_end=datetime.utcnow() + timedelta(days=30),
                        stripe_subscription_id=f"sub_test_{customer_id}_{product_id}",
                    )
                    self.db.add(subscription)

                    # Create invoice for active subscriptions
                    if status == "active":
                        invoice = Invoice(
                            customer_id=customer_id,
                            subscription_id=subscription.id,
                            amount_total=price[1],
                            currency="USD",
                            status="paid",
                            paid_at=datetime.utcnow(),
                            stripe_invoice_id=f"inv_test_{customer_id}_{product_id}",
                        )
                        self.db.add(invoice)

        await self.db.commit()


async def main():
    parser = argparse.ArgumentParser(description="Seed development database")
    parser.add_argument("--clear", action="store_true", help="Clear existing data before seeding")
    parser.add_argument(
        "--env", default="development", choices=["development", "test"], help="Environment to seed"
    )

    args = parser.parse_args()

    if args.env == "production":
        logger.error("❌ Cannot seed production database!")
        sys.exit(1)

    logger.info(f"🌱 Starting database seeding for {args.env} environment...")

    seeder = DataSeeder()
    await seeder.seed_all(clear_existing=args.clear)

    logger.info(
        """
    ✨ Seeding complete! Test credentials:

    Admin User:
      Username: admin
      Password: Admin123!@#

    Regular Users:
      Username: john.doe / jane.smith / bob.wilson
      Password: Test123!@#

    Tenants:
      - acme-corp (Acme Corporation)
      - techstart (TechStart Inc)
      - global-ent (Global Enterprises)
    """
    )


if __name__ == "__main__":
    asyncio.run(main())
