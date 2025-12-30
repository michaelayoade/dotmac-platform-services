"""Create tenant tables.

Revision ID: create_tenants_table
Revises: create_partner_applications
Create Date: 2025-12-26 15:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "create_tenants_table"
down_revision: str | None = "create_partner_applications"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create tenants and related tables."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    # Create enum types
    tenantstatus = postgresql.ENUM(
        "trial",
        "active",
        "suspended",
        "cancelled",
        "pending",
        "provisioned",
        "deprovisioned",
        name="tenantstatus",
        create_type=False,
    )
    tenantplantype = postgresql.ENUM(
        "free", "starter", "professional", "enterprise", "custom",
        name="tenantplantype",
        create_type=False,
    )
    billingcycle = postgresql.ENUM(
        "monthly", "yearly", "quarterly",
        name="billingcycle",
        create_type=False,
    )
    invitationstatus = postgresql.ENUM(
        "pending", "accepted", "expired", "revoked",
        name="tenantinvitationstatus",
        create_type=False,
    )
    provisioningstatus = postgresql.ENUM(
        "queued", "in_progress", "succeeded", "failed", "cancelled", "timed_out",
        name="tenantprovisioningstatus",
        create_type=False,
    )

    # Create enum types in database
    tenantstatus.create(bind, checkfirst=True)
    tenantplantype.create(bind, checkfirst=True)
    billingcycle.create(bind, checkfirst=True)
    invitationstatus.create(bind, checkfirst=True)
    provisioningstatus.create(bind, checkfirst=True)

    # Create tenants table
    if "tenants" not in existing_tables:
        op.create_table(
            "tenants",
            sa.Column("id", sa.String(255), primary_key=True),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("slug", sa.String(255), nullable=False, unique=True, index=True),
            sa.Column("domain", sa.String(255), nullable=True, unique=True),
            sa.Column(
                "status",
                tenantstatus,
                nullable=False,
                server_default="trial",
            ),
            sa.Column(
                "plan_type",
                tenantplantype,
                nullable=False,
                server_default="free",
            ),
            sa.Column("email", sa.String(255), nullable=True),
            sa.Column("phone", sa.String(50), nullable=True),
            sa.Column("billing_email", sa.String(255), nullable=True),
            sa.Column(
                "billing_cycle",
                billingcycle,
                nullable=False,
                server_default="monthly",
            ),
            sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("subscription_starts_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("subscription_ends_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("max_users", sa.Integer(), nullable=False, server_default="5"),
            sa.Column("max_api_calls_per_month", sa.Integer(), nullable=False, server_default="10000"),
            sa.Column("max_storage_gb", sa.Integer(), nullable=False, server_default="10"),
            sa.Column("current_users", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("current_api_calls", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("current_storage_gb", sa.Numeric(10, 2), nullable=False, server_default="0"),
            sa.Column("features", postgresql.JSON(), nullable=False, server_default="{}"),
            sa.Column("settings", postgresql.JSON(), nullable=False, server_default="{}"),
            sa.Column("custom_metadata", postgresql.JSON(), nullable=False, server_default="{}"),
            sa.Column("company_size", sa.String(50), nullable=True),
            sa.Column("industry", sa.String(100), nullable=True),
            sa.Column("country", sa.String(100), nullable=True),
            sa.Column("timezone", sa.String(50), nullable=False, server_default="UTC"),
            sa.Column("logo_url", sa.String(500), nullable=True),
            sa.Column("primary_color", sa.String(20), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("created_by", sa.String(255), nullable=True),
            sa.Column("updated_by", sa.String(255), nullable=True),
        )
        op.create_index("ix_tenants_status", "tenants", ["status"])

    # Create tenant_settings table
    if "tenant_settings" not in existing_tables:
        op.create_table(
            "tenant_settings",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("tenant_id", sa.String(255), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("key", sa.String(255), nullable=False, index=True),
            sa.Column("value", sa.Text(), nullable=False),
            sa.Column("value_type", sa.String(50), nullable=False, server_default="string"),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("is_encrypted", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("tenant_id", "key", name="uq_tenant_setting_key"),
        )

    # Create tenant_usage table
    if "tenant_usage" not in existing_tables:
        op.create_table(
            "tenant_usage",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("tenant_id", sa.String(255), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
            sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
            sa.Column("api_calls", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("storage_gb", sa.Numeric(10, 2), nullable=False, server_default="0"),
            sa.Column("active_users", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("bandwidth_gb", sa.Numeric(10, 2), nullable=False, server_default="0"),
            sa.Column("metrics", postgresql.JSON(), nullable=False, server_default="{}"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )
        op.create_index("ix_tenant_usage_period", "tenant_usage", ["tenant_id", "period_start", "period_end"])

    # Create tenant_invitations table
    if "tenant_invitations" not in existing_tables:
        op.create_table(
            "tenant_invitations",
            sa.Column("id", sa.String(255), primary_key=True),
            sa.Column("tenant_id", sa.String(255), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("email", sa.String(255), nullable=False, index=True),
            sa.Column("role", sa.String(100), nullable=False, server_default="member"),
            sa.Column("token", sa.String(500), nullable=False, unique=True, index=True),
            sa.Column(
                "status",
                invitationstatus,
                nullable=False,
                server_default="pending",
            ),
            sa.Column("invited_by", sa.String(255), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )

    # Create tenant_provisioning_jobs table
    # Create deployment_mode enum
    deploymentmode = postgresql.ENUM(
        "shared", "dedicated", "hybrid",
        name="tenantdeploymentmode",
        create_type=False,
    )
    deploymentmode.create(bind, checkfirst=True)

    if "tenant_provisioning_jobs" not in existing_tables:
        op.create_table(
            "tenant_provisioning_jobs",
            sa.Column("id", sa.String(255), primary_key=True),
            sa.Column("tenant_id", sa.String(255), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column(
                "status",
                provisioningstatus,
                nullable=False,
                server_default="queued",
                index=True,
            ),
            sa.Column("deployment_mode", deploymentmode, nullable=False),
            sa.Column("awx_template_id", sa.Integer(), nullable=True),
            sa.Column("awx_job_id", sa.Integer(), nullable=True, index=True),
            sa.Column("requested_by", sa.String(255), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("extra_vars", postgresql.JSON(), nullable=True),
            sa.Column("connection_profile", postgresql.JSON(), nullable=True),
            sa.Column("last_acknowledged_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("created_by", sa.String(255), nullable=True),
            sa.Column("updated_by", sa.String(255), nullable=True),
        )

    # Insert platform tenant
    op.execute("""
        INSERT INTO tenants (id, name, slug, status, plan_type, email)
        VALUES ('platform', 'Platform', 'platform', 'active', 'enterprise', 'platform@dotmac.com')
        ON CONFLICT (id) DO NOTHING;
    """)


def downgrade() -> None:
    """Drop tenant tables."""
    op.drop_table("tenant_provisioning_jobs")
    op.drop_table("tenant_invitations")
    op.drop_table("tenant_usage")
    op.drop_table("tenant_settings")
    op.drop_table("tenants")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS tenantprovisioningstatus")
    op.execute("DROP TYPE IF EXISTS tenantinvitationstatus")
    op.execute("DROP TYPE IF EXISTS billingcycle")
    op.execute("DROP TYPE IF EXISTS tenantplantype")
    op.execute("DROP TYPE IF EXISTS tenantstatus")
