"""Add is_platform_admin field to users table

Revision ID: 133b0030fe4e
Revises: 1275a5851a69
Create Date: 2025-10-04 08:19:42.436784

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "133b0030fe4e"
down_revision = "1275a5851a69"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_platform_admin column to users table
    op.add_column(
        "users",
        sa.Column("is_platform_admin", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    # Remove is_platform_admin column from users table
    op.drop_column("users", "is_platform_admin")
