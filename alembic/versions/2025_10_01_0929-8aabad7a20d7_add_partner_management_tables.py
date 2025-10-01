"""add_partner_management_tables

Revision ID: 8aabad7a20d7
Revises: f1c6e454da91
Create Date: 2025-10-01 09:29:24.115679

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "8aabad7a20d7"
down_revision = "f1c6e454da91"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create partner status enum
    op.execute(
        """
        CREATE TYPE partnerstatus AS ENUM (
            'pending', 'active', 'suspended', 'terminated', 'archived'
        )
        """
    )

    # Create partner tier enum
    op.execute(
        """
        CREATE TYPE partnertier AS ENUM (
            'bronze', 'silver', 'gold', 'platinum', 'direct'
        )
        """
    )

    # Create commission model enum
    op.execute(
        """
        CREATE TYPE commissionmodel AS ENUM (
            'revenue_share', 'flat_fee', 'tiered', 'hybrid'
        )
        """
    )

    # Create commission status enum
    op.execute(
        """
        CREATE TYPE commissionstatus AS ENUM (
            'pending', 'approved', 'paid', 'clawback', 'cancelled'
        )
        """
    )

    # Create referral status enum
    op.execute(
        """
        CREATE TYPE referralstatus AS ENUM (
            'new', 'contacted', 'qualified', 'converted', 'lost', 'invalid'
        )
        """
    )

    # Create partners table
    op.create_table(
        "partners",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("partner_number", sa.String(length=50), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("legal_name", sa.String(length=255), nullable=True),
        sa.Column("website", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "active",
                "suspended",
                "terminated",
                "archived",
                name="partnerstatus",
            ),
            nullable=False,
        ),
        sa.Column(
            "tier",
            sa.Enum("bronze", "silver", "gold", "platinum", "direct", name="partnertier"),
            nullable=False,
        ),
        sa.Column(
            "commission_model",
            sa.Enum(
                "revenue_share", "flat_fee", "tiered", "hybrid", name="commissionmodel"
            ),
            nullable=False,
        ),
        sa.Column("default_commission_rate", sa.Numeric(5, 4), nullable=True),
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
        sa.Column("sla_uptime_percentage", sa.Numeric(5, 2), nullable=True),
        sa.Column("partnership_start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("partnership_end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_review_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_review_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_customers", sa.Integer(), nullable=False),
        sa.Column("total_revenue_generated", sa.Numeric(15, 2), nullable=False),
        sa.Column("total_commissions_earned", sa.Numeric(15, 2), nullable=False),
        sa.Column("total_commissions_paid", sa.Numeric(15, 2), nullable=False),
        sa.Column("total_referrals", sa.Integer(), nullable=False),
        sa.Column("converted_referrals", sa.Integer(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("custom_fields", sa.JSON(), nullable=False),
        sa.Column("external_id", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tenant_id", sa.String(length=255), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.Column("updated_by", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("partner_number", name=op.f("uq_partners_partner_number")),
    )
    op.create_index("ix_partner_dates", "partners", ["partnership_start_date", "partnership_end_date"], unique=False)
    op.create_index("ix_partner_status_tier", "partners", ["status", "tier"], unique=False)
    op.create_index(op.f("ix_partners_external_id"), "partners", ["external_id"], unique=False)
    op.create_index(op.f("ix_partners_partner_number"), "partners", ["partner_number"], unique=False)
    op.create_index(op.f("ix_partners_tenant_id"), "partners", ["tenant_id"], unique=False)
    op.create_index("uq_tenant_company_name", "partners", ["tenant_id", "company_name"], unique=True)
    op.create_index("uq_tenant_partner_number", "partners", ["tenant_id", "partner_number"], unique=True)

    # Create partner_users table
    op.create_table(
        "partner_users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("partner_id", sa.UUID(), nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("is_primary_contact", sa.Boolean(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tenant_id", sa.String(length=255), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["partner_id"], ["partners.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_partner_user_partner", "partner_users", ["partner_id", "is_active"], unique=False)
    op.create_index(op.f("ix_partner_users_email"), "partner_users", ["email"], unique=False)
    op.create_index(op.f("ix_partner_users_partner_id"), "partner_users", ["partner_id"], unique=False)
    op.create_index(op.f("ix_partner_users_tenant_id"), "partner_users", ["tenant_id"], unique=False)
    op.create_index("uq_partner_user_email", "partner_users", ["partner_id", "email"], unique=True)

    # Create partner_accounts table
    op.create_table(
        "partner_accounts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("partner_id", sa.UUID(), nullable=False),
        sa.Column("customer_id", sa.UUID(), nullable=False),
        sa.Column("engagement_type", sa.String(length=50), nullable=False),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("custom_commission_rate", sa.Numeric(5, 4), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tenant_id", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["partner_id"], ["partners.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_partner_account_active", "partner_accounts", ["partner_id", "is_active"], unique=False)
    op.create_index("ix_partner_account_dates", "partner_accounts", ["partner_id", "start_date", "end_date"], unique=False)
    op.create_index(op.f("ix_partner_accounts_customer_id"), "partner_accounts", ["customer_id"], unique=False)
    op.create_index(op.f("ix_partner_accounts_is_active"), "partner_accounts", ["is_active"], unique=False)
    op.create_index(op.f("ix_partner_accounts_partner_id"), "partner_accounts", ["partner_id"], unique=False)
    op.create_index(op.f("ix_partner_accounts_tenant_id"), "partner_accounts", ["tenant_id"], unique=False)
    op.create_index("uq_partner_customer", "partner_accounts", ["partner_id", "customer_id"], unique=True)

    # Create partner_commission_rules table
    op.create_table(
        "partner_commission_rules",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("partner_id", sa.UUID(), nullable=False),
        sa.Column("rule_name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "commission_type",
            sa.Enum(
                "revenue_share", "flat_fee", "tiered", "hybrid", name="commissionmodel"
            ),
            nullable=False,
        ),
        sa.Column("commission_rate", sa.Numeric(5, 4), nullable=True),
        sa.Column("flat_fee_amount", sa.Numeric(15, 2), nullable=True),
        sa.Column("tier_config", sa.JSON(), nullable=False),
        sa.Column("applies_to_products", sa.JSON(), nullable=True),
        sa.Column("applies_to_customers", sa.JSON(), nullable=True),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tenant_id", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["partner_id"], ["partners.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_commission_rule_dates", "partner_commission_rules", ["effective_from", "effective_to"], unique=False)
    op.create_index("ix_commission_rule_partner_active", "partner_commission_rules", ["partner_id", "is_active"], unique=False)
    op.create_index(op.f("ix_partner_commission_rules_partner_id"), "partner_commission_rules", ["partner_id"], unique=False)
    op.create_index(op.f("ix_partner_commission_rules_tenant_id"), "partner_commission_rules", ["tenant_id"], unique=False)

    # Create partner_commission_events table
    op.create_table(
        "partner_commission_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("partner_id", sa.UUID(), nullable=False),
        sa.Column("invoice_id", sa.UUID(), nullable=True),
        sa.Column("customer_id", sa.UUID(), nullable=True),
        sa.Column("commission_amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("base_amount", sa.Numeric(15, 2), nullable=True),
        sa.Column("commission_rate", sa.Numeric(5, 4), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "pending", "approved", "paid", "clawback", "cancelled", name="commissionstatus"
            ),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("event_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payout_id", sa.UUID(), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tenant_id", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["partner_id"], ["partners.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_commission_event_dates", "partner_commission_events", ["event_date", "paid_at"], unique=False)
    op.create_index("ix_commission_event_partner_status", "partner_commission_events", ["partner_id", "status"], unique=False)
    op.create_index("ix_commission_event_payout", "partner_commission_events", ["payout_id", "status"], unique=False)
    op.create_index(op.f("ix_partner_commission_events_invoice_id"), "partner_commission_events", ["invoice_id"], unique=False)
    op.create_index(op.f("ix_partner_commission_events_partner_id"), "partner_commission_events", ["partner_id"], unique=False)
    op.create_index(op.f("ix_partner_commission_events_payout_id"), "partner_commission_events", ["payout_id"], unique=False)
    op.create_index(op.f("ix_partner_commission_events_status"), "partner_commission_events", ["status"], unique=False)
    op.create_index(op.f("ix_partner_commission_events_tenant_id"), "partner_commission_events", ["tenant_id"], unique=False)

    # Create partner_referrals table
    op.create_table(
        "partner_referrals",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("partner_id", sa.UUID(), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=True),
        sa.Column("contact_name", sa.String(length=255), nullable=False),
        sa.Column("contact_email", sa.String(length=255), nullable=False),
        sa.Column("contact_phone", sa.String(length=30), nullable=True),
        sa.Column("estimated_value", sa.Numeric(15, 2), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "new", "contacted", "qualified", "converted", "lost", "invalid", name="referralstatus"
            ),
            nullable=False,
        ),
        sa.Column("converted_customer_id", sa.UUID(), nullable=True),
        sa.Column("conversion_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_value", sa.Numeric(15, 2), nullable=True),
        sa.Column("submitted_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("first_contact_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("qualified_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source", sa.String(length=100), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tenant_id", sa.String(length=255), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["converted_customer_id"], ["customers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["partner_id"], ["partners.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_referral_dates", "partner_referrals", ["submitted_date", "conversion_date"], unique=False)
    op.create_index("ix_referral_email", "partner_referrals", ["contact_email"], unique=False)
    op.create_index("ix_referral_partner_status", "partner_referrals", ["partner_id", "status"], unique=False)
    op.create_index(op.f("ix_partner_referrals_contact_email"), "partner_referrals", ["contact_email"], unique=False)
    op.create_index(op.f("ix_partner_referrals_partner_id"), "partner_referrals", ["partner_id"], unique=False)
    op.create_index(op.f("ix_partner_referrals_status"), "partner_referrals", ["status"], unique=False)
    op.create_index(op.f("ix_partner_referrals_tenant_id"), "partner_referrals", ["tenant_id"], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table("partner_referrals")
    op.drop_table("partner_commission_events")
    op.drop_table("partner_commission_rules")
    op.drop_table("partner_accounts")
    op.drop_table("partner_users")
    op.drop_table("partners")

    # Drop enums
    op.execute("DROP TYPE referralstatus")
    op.execute("DROP TYPE commissionstatus")
    op.execute("DROP TYPE commissionmodel")
    op.execute("DROP TYPE partnertier")
    op.execute("DROP TYPE partnerstatus")
