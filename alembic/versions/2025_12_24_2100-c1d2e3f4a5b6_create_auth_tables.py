"""Create core auth and user tables for login functionality.

Revision ID: c1d2e3f4a5b6
Revises: b2c3d4e5f6a7
Create Date: 2025-12-24 21:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "c1d2e3f4a5b6"
down_revision: str | None = "b2c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create users, permissions, roles, and related auth tables."""

    # Check if tables already exist
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    # ===================
    # USERS TABLE
    # ===================
    if "users" not in existing_tables:
        op.create_table(
            "users",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", sa.String(36), nullable=False, index=True),
            sa.Column("username", sa.String(50), nullable=False, index=True),
            sa.Column("email", sa.String(255), nullable=False, index=True),
            sa.Column("password_hash", sa.Text(), nullable=False),
            sa.Column("full_name", sa.String(255), nullable=True),
            sa.Column("phone_number", sa.String(20), nullable=True),
            sa.Column("first_name", sa.String(100), nullable=True),
            sa.Column("last_name", sa.String(100), nullable=True),
            sa.Column("phone", sa.String(20), nullable=True),
            sa.Column("phone_verified", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("bio", sa.Text(), nullable=True),
            sa.Column("website", sa.String(255), nullable=True),
            sa.Column("location", sa.String(255), nullable=True),
            sa.Column("timezone", sa.String(50), nullable=True),
            sa.Column("language", sa.String(10), nullable=True),
            sa.Column("avatar_url", sa.String(500), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("is_platform_admin", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("roles", postgresql.JSON(), nullable=False, server_default="[]"),
            sa.Column("permissions", postgresql.JSON(), nullable=False, server_default="[]"),
            sa.Column("mfa_enabled", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("mfa_secret", sa.String(255), nullable=True),
            sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_login_ip", sa.String(45), nullable=True),
            sa.Column("failed_login_attempts", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
            sa.Column("metadata", postgresql.JSON(), nullable=False, server_default="{}"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("tenant_id", "username", name="uq_users_tenant_username"),
            sa.UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
        )

    # ===================
    # PERMISSIONS TABLE
    # ===================
    if "permissions" not in existing_tables:
        op.create_table(
            "permissions",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("name", sa.String(100), nullable=False, unique=True, index=True),
            sa.Column("display_name", sa.String(200), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("category", sa.String(50), nullable=False),
            sa.Column("parent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("permissions.id"), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("is_system", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("metadata", postgresql.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )

    # ===================
    # ROLES TABLE
    # ===================
    if "roles" not in existing_tables:
        op.create_table(
            "roles",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", sa.String(36), nullable=True, index=True),
            sa.Column("name", sa.String(100), nullable=False, index=True),
            sa.Column("display_name", sa.String(200), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("is_system", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("is_default", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("metadata", postgresql.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("tenant_id", "name", name="uq_roles_tenant_name"),
        )

    # ===================
    # USER_ROLES JUNCTION TABLE
    # ===================
    if "user_roles" not in existing_tables:
        op.create_table(
            "user_roles",
            sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
            sa.Column("role_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
            sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("granted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("metadata", postgresql.JSON(), nullable=True),
            sa.UniqueConstraint("user_id", "role_id", name="uq_user_role"),
        )
        op.create_index("ix_user_roles_user_id", "user_roles", ["user_id"])
        op.create_index("ix_user_roles_expires_at", "user_roles", ["expires_at"])

    # ===================
    # ROLE_PERMISSIONS JUNCTION TABLE
    # ===================
    if "role_permissions" not in existing_tables:
        op.create_table(
            "role_permissions",
            sa.Column("role_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
            sa.Column("permission_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
            sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
        )
        op.create_index("ix_role_permissions_role_id", "role_permissions", ["role_id"])

    # ===================
    # USER_PERMISSIONS JUNCTION TABLE
    # ===================
    if "user_permissions" not in existing_tables:
        op.create_table(
            "user_permissions",
            sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
            sa.Column("permission_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
            sa.Column("granted", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("granted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("reason", sa.Text(), nullable=True),
            sa.UniqueConstraint("user_id", "permission_id", name="uq_user_permission"),
        )
        op.create_index("ix_user_permissions_user_id", "user_permissions", ["user_id"])

    # ===================
    # API_KEYS TABLE
    # ===================
    if "api_keys" not in existing_tables:
        op.create_table(
            "api_keys",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", sa.String(36), nullable=False, index=True),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("name", sa.String(100), nullable=False),
            sa.Column("key_hash", sa.String(255), nullable=False, unique=True),
            sa.Column("key_prefix", sa.String(10), nullable=False, index=True),
            sa.Column("scopes", postgresql.JSON(), nullable=False, server_default="[]"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_used_ip", sa.String(45), nullable=True),
            sa.Column("metadata", postgresql.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )

    # ===================
    # BACKUP_CODES TABLE
    # ===================
    if "backup_codes" not in existing_tables:
        op.create_table(
            "backup_codes",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", sa.String(36), nullable=False, index=True),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
            sa.Column("code_hash", sa.String(255), nullable=False),
            sa.Column("used", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("used_ip", sa.String(45), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )

    # ===================
    # TEAMS TABLE
    # ===================
    if "teams" not in existing_tables:
        op.create_table(
            "teams",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", sa.String(36), nullable=False, index=True),
            sa.Column("name", sa.String(100), nullable=False, index=True),
            sa.Column("slug", sa.String(100), nullable=False, index=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("is_default", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("team_lead_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
            sa.Column("color", sa.String(7), nullable=True),
            sa.Column("icon", sa.String(50), nullable=True),
            sa.Column("metadata", postgresql.JSON(), nullable=False, server_default="{}"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("tenant_id", "name", name="uq_teams_tenant_name"),
            sa.UniqueConstraint("tenant_id", "slug", name="uq_teams_tenant_slug"),
        )


def downgrade() -> None:
    """Drop auth tables in reverse order."""
    op.drop_table("teams")
    op.drop_table("backup_codes")
    op.drop_table("api_keys")
    op.drop_table("user_permissions")
    op.drop_table("role_permissions")
    op.drop_table("user_roles")
    op.drop_table("roles")
    op.drop_table("permissions")
    op.drop_table("users")
