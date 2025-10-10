"""Add invoice_id and payout_id foreign keys to partner_commission_events

Revision ID: 364eab9b9915
Revises: 51aa0da58b97
Create Date: 2025-10-09 05:11:35.200239

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "364eab9b9915"
down_revision = "51aa0da58b97"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create PayoutStatus enum if it doesn't exist
    op.execute(
        "CREATE TYPE IF NOT EXISTS payoutstatus AS ENUM ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'CANCELLED')"
    )

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
            sa.Enum(
                "PENDING", "PROCESSING", "COMPLETED", "FAILED", "CANCELLED", name="payoutstatus"
            ),
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
    op.drop_index("ix_partner_payouts_tenant_id", "partner_payouts")
    op.drop_index("ix_partner_payouts_period", "partner_payouts")
    op.drop_index("ix_partner_payouts_partner_id", "partner_payouts")
    op.drop_table("partner_payouts")

    # Drop PayoutStatus enum
    op.execute("DROP TYPE IF EXISTS payoutstatus")
