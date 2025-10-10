"""Merge rbac and contact migrations

Revision ID: e24194971426
Revises: rbac_20250127, add_contact_system_tables
Create Date: 2025-09-28 20:31:54.570870

"""

# revision identifiers, used by Alembic.
revision = "e24194971426"
down_revision = ("rbac_20250127", "add_contact_system_tables")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
