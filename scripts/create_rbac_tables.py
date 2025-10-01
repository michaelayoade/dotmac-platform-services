#!/usr/bin/env python
"""
Create RBAC tables directly and seed data
"""
import sys
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from dotmac.platform.db import get_sync_engine
from dotmac.platform.settings import settings


def create_rbac_tables():
    """Create RBAC tables using raw SQL"""
    engine = get_sync_engine()

    with engine.begin() as conn:
        print("Creating RBAC tables...")

        # Create permissions table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS permissions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(100) UNIQUE NOT NULL,
                display_name VARCHAR(200) NOT NULL,
                description TEXT,
                category VARCHAR(50) NOT NULL,
                parent_id UUID REFERENCES permissions(id),
                is_active BOOLEAN DEFAULT true NOT NULL,
                is_system BOOLEAN DEFAULT false NOT NULL,
                metadata JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
            )
        """))
        print("  ✓ Created permissions table")

        # Create indexes for permissions
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_permissions_name ON permissions(name)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_permissions_category ON permissions(category)"))

        # Create roles table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS roles (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(100) UNIQUE NOT NULL,
                display_name VARCHAR(200) NOT NULL,
                description TEXT,
                parent_id UUID REFERENCES roles(id),
                priority INTEGER DEFAULT 0 NOT NULL,
                is_active BOOLEAN DEFAULT true NOT NULL,
                is_system BOOLEAN DEFAULT false NOT NULL,
                is_default BOOLEAN DEFAULT false NOT NULL,
                max_users INTEGER,
                metadata JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
            )
        """))
        print("  ✓ Created roles table")

        # Create indexes for roles
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_roles_name ON roles(name)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_roles_priority ON roles(priority)"))

        # Create role_permissions junction table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS role_permissions (
                role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
                permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
                granted_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
                PRIMARY KEY (role_id, permission_id)
            )
        """))
        print("  ✓ Created role_permissions table")

        # Create indexes for role_permissions
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_role_permissions_role_id ON role_permissions(role_id)"))

        # Create user_roles junction table (if users table exists)
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS user_roles (
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
                    granted_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
                    granted_by UUID REFERENCES users(id),
                    expires_at TIMESTAMP WITH TIME ZONE,
                    metadata JSONB,
                    PRIMARY KEY (user_id, role_id)
                )
            """))
            print("  ✓ Created user_roles table")

            # Create indexes for user_roles
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_user_roles_user_id ON user_roles(user_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_user_roles_expires_at ON user_roles(expires_at)"))
        except Exception as e:
            print(f"  - Skipped user_roles table (users table may not exist): {e}")

        print("All RBAC tables created successfully!\n")


def seed_rbac_data():
    """Seed RBAC data using raw SQL"""
    engine = get_sync_engine()

    permissions_data = [
        # User Management
        ("users.read", "View Users", "users", "View user accounts and profiles"),
        ("users.create", "Create Users", "users", "Create new user accounts"),
        ("users.update", "Update Users", "users", "Modify user accounts and profiles"),
        ("users.delete", "Delete Users", "users", "Remove user accounts"),
        ("users.manage", "Manage Users", "users", "Full user management capabilities"),

        # Customer Management
        ("customers.read", "View Customers", "customers", "View customer details and lists"),
        ("customers.create", "Create Customers", "customers", "Create new customer accounts"),
        ("customers.update", "Update Customers", "customers", "Edit customer information"),
        ("customers.delete", "Delete Customers", "customers", "Remove customer accounts"),
        ("customers.manage", "Manage Customers", "customers", "Full customer management capabilities"),

        # Billing & Payments
        ("billing.read", "View Billing", "billing", "View billing information and invoices"),
        ("billing.create", "Create Billing", "billing", "Create invoices and billing records"),
        ("billing.update", "Update Billing", "billing", "Modify invoices and billing settings"),
        ("billing.delete", "Delete Billing", "billing", "Remove billing records and invoices"),
        ("billing.manage", "Manage Billing", "billing", "Full billing system management"),
        ("billing.execute", "Process Payments", "billing", "Process payments and refunds"),

        # Analytics & Reporting
        ("analytics.read", "View Analytics", "analytics", "Access dashboards and reports"),
        ("analytics.create", "Create Reports", "analytics", "Generate custom reports"),
        ("analytics.update", "Update Analytics", "analytics", "Modify analytics configurations"),
        ("analytics.delete", "Delete Analytics", "analytics", "Remove analytics data"),
        ("analytics.manage", "Manage Analytics", "analytics", "Full analytics system management"),

        # Communications
        ("communications.read", "View Communications", "communications", "View communication logs and templates"),
        ("communications.create", "Create Communications", "communications", "Send emails and notifications"),
        ("communications.update", "Update Communications", "communications", "Modify communication templates"),
        ("communications.delete", "Delete Communications", "communications", "Remove communication records"),
        ("communications.manage", "Manage Communications", "communications", "Full communication system management"),
        ("communications.execute", "Send Communications", "communications", "Execute communication campaigns"),

        # Infrastructure
        ("infrastructure.read", "View Infrastructure", "infrastructure", "View system configuration and status"),
        ("infrastructure.create", "Create Infrastructure", "infrastructure", "Create infrastructure resources"),
        ("infrastructure.update", "Update Infrastructure", "infrastructure", "Modify infrastructure settings"),
        ("infrastructure.delete", "Delete Infrastructure", "infrastructure", "Remove infrastructure resources"),
        ("infrastructure.manage", "Manage Infrastructure", "infrastructure", "Full infrastructure management"),
        ("infrastructure.execute", "Execute Infrastructure", "infrastructure", "Deploy and operate infrastructure"),

        # Secrets Management
        ("secrets.read", "Read Secrets", "secrets", "Access secret values"),
        ("secrets.create", "Create Secrets", "secrets", "Create new secrets"),
        ("secrets.update", "Update Secrets", "secrets", "Modify existing secrets"),
        ("secrets.delete", "Delete Secrets", "secrets", "Remove secrets"),
        ("secrets.manage", "Manage Secrets", "secrets", "Full secrets management"),
        ("secrets.execute", "Rotate Secrets", "secrets", "Execute secret rotation"),

        # Settings
        ("settings.read", "View Settings", "settings", "View system and user settings"),
        ("settings.create", "Create Settings", "settings", "Create new configuration settings"),
        ("settings.update", "Update Settings", "settings", "Modify system settings"),
        ("settings.delete", "Delete Settings", "settings", "Remove configuration settings"),
        ("settings.manage", "Manage Settings", "settings", "Full settings management"),

        # System Administration
        ("system.read", "View System", "system", "View system status and logs"),
        ("system.create", "Create System Resources", "system", "Create system-level resources"),
        ("system.update", "Update System", "system", "Modify system configuration"),
        ("system.delete", "Delete System Resources", "system", "Remove system resources"),
        ("system.manage", "Manage System", "system", "Full system administration"),
        ("system.execute", "Execute System Operations", "system", "Perform system operations"),
    ]

    roles_data = [
        # Basic user role
        ("user", "User", "Basic read permissions for standard users", 1, True, False, [
            "settings.read", "analytics.read"
        ]),

        # Analyst role
        ("analyst", "Analyst", "Read-only access for analytics and reporting", 10, False, False, [
            "analytics.read", "analytics.create", "billing.read", "customers.read",
            "communications.read", "settings.read"
        ]),

        # Developer role
        ("developer", "Developer", "Infrastructure and API access for developers", 15, False, False, [
            "infrastructure.read", "infrastructure.create", "infrastructure.update", "infrastructure.execute",
            "secrets.read", "secrets.create", "secrets.update", "analytics.read",
            "settings.read", "settings.update"
        ]),

        # Manager role
        ("manager", "Manager", "Read/write access for business operations", 20, False, False, [
            "users.read", "users.create", "users.update", "customers.read", "customers.create",
            "customers.update", "customers.manage", "billing.read", "billing.create",
            "billing.update", "billing.execute", "analytics.read", "analytics.create",
            "communications.read", "communications.create", "communications.update",
            "communications.execute", "settings.read", "settings.update"
        ]),

        # Admin role
        ("admin", "Administrator", "Full management permissions except system-level operations", 50, False, True, [
            "users.read", "users.create", "users.update", "users.delete", "users.manage",
            "customers.read", "customers.create", "customers.update", "customers.delete", "customers.manage",
            "billing.read", "billing.create", "billing.update", "billing.delete", "billing.manage", "billing.execute",
            "analytics.read", "analytics.create", "analytics.update", "analytics.delete", "analytics.manage",
            "communications.read", "communications.create", "communications.update", "communications.delete",
            "communications.manage", "communications.execute", "infrastructure.read", "infrastructure.create",
            "infrastructure.update", "infrastructure.execute", "secrets.read", "secrets.create",
            "secrets.update", "secrets.execute", "settings.read", "settings.create",
            "settings.update", "settings.delete", "settings.manage"
        ]),

        # Superuser role
        ("superuser", "Super User", "All permissions including system-level operations", 100, False, True, ["*"])
    ]

    with engine.begin() as conn:
        print("Seeding permissions...")
        permission_ids = {}

        # Insert permissions
        for name, display_name, category, description in permissions_data:
            # Check if permission exists
            result = conn.execute(text(
                "SELECT id FROM permissions WHERE name = :name"
            ), {"name": name})

            existing = result.fetchone()
            if existing:
                permission_ids[name] = existing[0]
                print(f"  - Permission exists: {name}")
            else:
                permission_id = str(uuid4())
                permission_ids[name] = permission_id

                conn.execute(text("""
                    INSERT INTO permissions (id, name, display_name, description, category, is_active, is_system, created_at, updated_at)
                    VALUES (:id, :name, :display_name, :description, :category, :is_active, :is_system, :created_at, :updated_at)
                """), {
                    "id": permission_id,
                    "name": name,
                    "display_name": display_name,
                    "description": description,
                    "category": category,
                    "is_active": True,
                    "is_system": True,
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                })
                print(f"  ✓ Created permission: {name}")

        print(f"Total permissions: {len(permission_ids)}\n")

        print("Seeding roles...")
        role_ids = {}

        # Insert roles
        for name, display_name, description, priority, is_default, is_system, permissions in roles_data:
            # Check if role exists
            result = conn.execute(text(
                "SELECT id FROM roles WHERE name = :name"
            ), {"name": name})

            existing = result.fetchone()
            if existing:
                role_ids[name] = existing[0]
                print(f"  - Role exists: {name}")
            else:
                role_id = str(uuid4())
                role_ids[name] = role_id

                conn.execute(text("""
                    INSERT INTO roles (id, name, display_name, description, priority, is_active, is_system, is_default, created_at, updated_at)
                    VALUES (:id, :name, :display_name, :description, :priority, :is_active, :is_system, :is_default, :created_at, :updated_at)
                """), {
                    "id": role_id,
                    "name": name,
                    "display_name": display_name,
                    "description": description,
                    "priority": priority,
                    "is_active": True,
                    "is_system": is_system,
                    "is_default": is_default,
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                })

                # Add role permissions
                for perm_name in permissions:
                    if perm_name == "*":
                        # Add all permissions for wildcard roles
                        for perm_name_all in permission_ids.keys():
                            # Check if role-permission already exists
                            check_result = conn.execute(text(
                                "SELECT 1 FROM role_permissions WHERE role_id = :role_id AND permission_id = :permission_id"
                            ), {"role_id": role_id, "permission_id": permission_ids[perm_name_all]})

                            if not check_result.fetchone():
                                conn.execute(text("""
                                    INSERT INTO role_permissions (role_id, permission_id, granted_at)
                                    VALUES (:role_id, :permission_id, :granted_at)
                                """), {
                                    "role_id": role_id,
                                    "permission_id": permission_ids[perm_name_all],
                                    "granted_at": datetime.now(timezone.utc)
                                })
                    elif perm_name in permission_ids:
                        # Check if role-permission already exists
                        check_result = conn.execute(text(
                            "SELECT 1 FROM role_permissions WHERE role_id = :role_id AND permission_id = :permission_id"
                        ), {"role_id": role_id, "permission_id": permission_ids[perm_name]})

                        if not check_result.fetchone():
                            conn.execute(text("""
                                INSERT INTO role_permissions (role_id, permission_id, granted_at)
                                VALUES (:role_id, :permission_id, :granted_at)
                            """), {
                                "role_id": role_id,
                                "permission_id": permission_ids[perm_name],
                                "granted_at": datetime.now(timezone.utc)
                            })
                    else:
                        print(f"    Warning: Permission '{perm_name}' not found")

                print(f"  ✓ Created role: {name} (priority: {priority})")

        print(f"Total roles: {len(role_ids)}\n")

        print("Role Assignment Information:")
        print("="*40)
        print("Default role assignments:")
        print("  - New users automatically get 'user' role")
        print("  - Role assignments should be done through the admin interface")
        print("  - Available roles:")

        for name, display_name, description, priority, is_default, is_system, _ in roles_data:
            print(f"    • {display_name} ({name}) - Priority: {priority}")

        print("\nTo assign roles to users:")
        print("  1. Use the web admin interface")
        print("  2. Use the RBAC API endpoints")
        print("  3. Use the CLI management commands")
        print()


def main():
    """Main entry point"""
    try:
        print("="*60)
        print("RBAC Tables Creation and Seeding")
        print("="*60 + "\n")

        print("Connecting to database...")
        engine = get_sync_engine()

        # Test connection
        with engine.connect() as conn:
            print("Database connection successful!")

        create_rbac_tables()
        seed_rbac_data()

        print("="*60)
        print("✅ RBAC setup completed successfully!")
        print("="*60)

    except Exception as e:
        print(f"\nError during RBAC setup: {e}")
        print("\nPlease ensure:")
        print("1. The database server is running")
        print("2. The database URL is correct in your settings")
        print("3. You have the necessary permissions")
        print("4. Required environment variables are set")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()