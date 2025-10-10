"""Merge migration heads

Revision ID: 9d6a492bf126
Revises: 001_add_tenant_id, 20250907_04
Create Date: 2025-09-24 09:45:01.572156

"""

# revision identifiers, used by Alembic.
revision = "9d6a492bf126"
down_revision = ("001_add_tenant_id", "20250907_04")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
