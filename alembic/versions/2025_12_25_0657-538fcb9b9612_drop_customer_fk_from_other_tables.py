"""drop_customer_fk_from_other_tables

Revision ID: 538fcb9b9612
Revises: e4940deabe90
Create Date: 2025-12-25 06:57:49.679513

Remove foreign key references to customers table from various models
after customer_management module removal.
"""

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = "538fcb9b9612"
down_revision = "e4940deabe90"
branch_labels = None
depends_on = None


# FK constraints to drop (table_name, constraint_name)
FK_CONSTRAINTS = [
    # Licensing models
    ("licenses", "licenses_customer_id_fkey"),
    ("license_orders", "license_orders_customer_id_fkey"),
    ("compliance_audits", "compliance_audits_customer_id_fkey"),
    # AI models
    ("ai_chat_sessions", "ai_chat_sessions_customer_id_fkey"),
    # Partner management models
    ("partner_customer_assignments", "partner_customer_assignments_customer_id_fkey"),
    ("commission_events", "commission_events_customer_id_fkey"),
    ("referral_leads", "referral_leads_converted_customer_id_fkey"),
    # Ticketing models
    ("tickets", "tickets_customer_id_fkey"),
    ("ticket_messages", "ticket_messages_customer_id_fkey"),
]


def upgrade() -> None:
    """Drop FK constraints to customers table using IF EXISTS for safety."""
    conn = op.get_bind()

    for table_name, constraint_name in FK_CONSTRAINTS:
        # Use raw SQL with IF EXISTS to avoid errors if constraint doesn't exist
        conn.execute(text(
            f"ALTER TABLE IF EXISTS {table_name} "
            f"DROP CONSTRAINT IF EXISTS {constraint_name}"
        ))


def downgrade() -> None:
    """Re-add FK constraints to customers table (if customers table exists)."""
    # Note: Downgrade requires customers table to exist
    # These are not implemented since the customers table was removed
    pass
