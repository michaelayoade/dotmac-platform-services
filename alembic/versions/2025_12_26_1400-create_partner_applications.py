"""Create partner applications table.

Revision ID: create_partner_applications
Revises: create_partner_invitations
Create Date: 2025-12-26 14:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "create_partner_applications"
down_revision: str | None = "create_partner_invitations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create partner_applications table
    op.create_table(
        "partner_applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("contact_name", sa.String(255), nullable=False),
        sa.Column("contact_email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("website", sa.String(255), nullable=True),
        sa.Column("business_description", sa.Text(), nullable=True),
        sa.Column("expected_referrals_monthly", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(20), server_default="pending", nullable=False),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("partner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("tenant_id", sa.String(255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["reviewed_by"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["partner_id"],
            ["partners.id"],
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint(
            "contact_email", "tenant_id", name="uq_partner_application_email_tenant"
        ),
    )

    # Create indexes
    op.create_index(
        "ix_partner_application_status",
        "partner_applications",
        ["status"],
    )
    op.create_index(
        "ix_partner_application_email",
        "partner_applications",
        ["contact_email"],
    )
    op.create_index(
        "ix_partner_applications_tenant_id",
        "partner_applications",
        ["tenant_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_partner_applications_tenant_id", table_name="partner_applications")
    op.drop_index("ix_partner_application_email", table_name="partner_applications")
    op.drop_index("ix_partner_application_status", table_name="partner_applications")
    op.drop_table("partner_applications")
