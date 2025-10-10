"""Merge multiple migration heads

Revision ID: c6c1a94cd6c0
Revises: 22bd27837bd6, billing_001, add_comms_tables
Create Date: 2025-09-25 09:00:36.889042

"""

# revision identifiers, used by Alembic.
revision = "c6c1a94cd6c0"
down_revision = ("22bd27837bd6", "billing_001", "add_comms_tables")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
