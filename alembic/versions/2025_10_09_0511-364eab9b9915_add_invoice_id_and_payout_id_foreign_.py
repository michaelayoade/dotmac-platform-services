"""Add partner management tables and foreign keys

Revision ID: 364eab9b9915
Revises: 51aa0da58b97
Create Date: 2025-10-09 05:11:35.200239

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "364eab9b9915"
down_revision = "51aa0da58b97"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create partner_status enum
    partner_status = postgresql.ENUM(
        "pending", "active", "suspended", "terminated", "archived",
        name="partner_status", create_type=False
    )
    partner_status.create(op.get_bind(), checkfirst=True)

    # Create partner_tier enum
    partner_tier = postgresql.ENUM(
        "bronze", "silver", "gold", "platinum",
        name="partner_tier", create_type=False
    )
    partner_tier.create(op.get_bind(), checkfirst=True)

    # Create commission_model enum
    commission_model = postgresql.ENUM(
        "revenue_share", "flat_fee", "tiered", "custom",
        name="commission_model", create_type=False
    )
    commission_model.create(op.get_bind(), checkfirst=True)

    # Create partners table first (required by partner_payouts FK)
    op.create_table(
        "partners",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("partner_number", sa.String(length=50), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("legal_name", sa.String(length=255), nullable=True),
        sa.Column("website", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", partner_status, nullable=False),
        sa.Column("tier", partner_tier, nullable=False),
        sa.Column("commission_model", commission_model, nullable=False),
        sa.Column("default_commission_rate", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("primary_email", sa.String(length=255), nullable=False),
        sa.Column("billing_email", sa.String(length=255), nullable=True),
        sa.Column("support_email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column("address_line1", sa.String(length=200), nullable=True),
        sa.Column("address_line2", sa.String(length=200), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("state_province", sa.String(length=100), nullable=True),
        sa.Column("postal_code", sa.String(length=20), nullable=True),
        sa.Column("country", sa.String(length=2), nullable=True),
        sa.Column("tax_id", sa.String(length=50), nullable=True),
        sa.Column("vat_number", sa.String(length=50), nullable=True),
        sa.Column("business_registration", sa.String(length=100), nullable=True),
        sa.Column("sla_response_hours", sa.Integer(), nullable=True),
        sa.Column("sla_uptime_percentage", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("partnership_start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("partnership_end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_review_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_review_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_customers", sa.Integer(), nullable=False),
        sa.Column("total_revenue_generated", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("total_commissions_earned", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("total_commissions_paid", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("total_referrals", sa.Integer(), nullable=False),
        sa.Column("converted_referrals", sa.Integer(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("custom_fields", sa.JSON(), nullable=False),
        sa.Column("external_id", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tenant_id", sa.String(length=255), nullable=False),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column("modified_by", sa.UUID(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("partner_number"),
        sa.UniqueConstraint("tenant_id", "partner_number", name="uq_tenant_partner_number"),
        sa.UniqueConstraint("tenant_id", "company_name", name="uq_tenant_company_name"),
    )
    op.create_index("ix_partners_company_name", "partners", ["company_name"])
    op.create_index("ix_partners_external_id", "partners", ["external_id"])
    op.create_index("ix_partners_partner_number", "partners", ["partner_number"])
    op.create_index("ix_partners_status", "partners", ["status"])
    op.create_index("ix_partners_tenant_id", "partners", ["tenant_id"])
    op.create_index("ix_partners_tier", "partners", ["tier"])
    op.create_index("ix_partner_status_tier", "partners", ["status", "tier"])
    op.create_index("ix_partner_dates", "partners", ["partnership_start_date", "partnership_end_date"])

    # Create partner_payouts table
    op.create_table(
        "partner_payouts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("partner_id", sa.UUID(), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("total_amount", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),  # Use String instead of Enum to avoid type creation issues
            nullable=False,
        ),
        sa.Column("payout_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payment_method", sa.String(length=50), nullable=True),
        sa.Column("payment_reference", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tenant_id", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(["partner_id"], ["partners.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_partner_payouts_partner_id", "partner_payouts", ["partner_id"])
    op.create_index("ix_partner_payouts_period", "partner_payouts", ["period_start", "period_end"])
    op.create_index("ix_partner_payouts_tenant_id", "partner_payouts", ["tenant_id"])

    # Add check constraint for status values
    op.create_check_constraint(
        "ck_partner_payouts_status",
        "partner_payouts",
        "status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'CANCELLED')",
    )

    # Add foreign key constraint for invoice_id
    op.create_foreign_key(
        "partner_commission_events_invoice_id_fkey",
        "partner_commission_events",
        "invoices",
        ["invoice_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Add foreign key constraint for payout_id
    op.create_foreign_key(
        "partner_commission_events_payout_id_fkey",
        "partner_commission_events",
        "partner_payouts",
        ["payout_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    # Drop foreign key constraints
    op.drop_constraint(
        "partner_commission_events_payout_id_fkey",
        "partner_commission_events",
        type_="foreignkey",
    )
    op.drop_constraint(
        "partner_commission_events_invoice_id_fkey",
        "partner_commission_events",
        type_="foreignkey",
    )

    # Drop partner_payouts table
    op.drop_constraint("ck_partner_payouts_status", "partner_payouts", type_="check")
    op.drop_index("ix_partner_payouts_tenant_id", "partner_payouts")
    op.drop_index("ix_partner_payouts_period", "partner_payouts")
    op.drop_index("ix_partner_payouts_partner_id", "partner_payouts")
    op.drop_table("partner_payouts")

    # Drop partners table
    op.drop_index("ix_partner_dates", "partners")
    op.drop_index("ix_partner_status_tier", "partners")
    op.drop_index("ix_partners_tier", "partners")
    op.drop_index("ix_partners_tenant_id", "partners")
    op.drop_index("ix_partners_status", "partners")
    op.drop_index("ix_partners_partner_number", "partners")
    op.drop_index("ix_partners_external_id", "partners")
    op.drop_index("ix_partners_company_name", "partners")
    op.drop_table("partners")

    # Drop enums
    postgresql.ENUM(name="commission_model").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="partner_tier").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="partner_status").drop(op.get_bind(), checkfirst=True)
