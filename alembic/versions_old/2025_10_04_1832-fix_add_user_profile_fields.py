"""Add user profile fields only

Revision ID: fix_user_profile
Revises: 133b0030fe4e
Create Date: 2025-10-04 18:32:00.000000

This migration ONLY adds the missing user profile fields without touching other tables.
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "fix_user_profile"
down_revision = "133b0030fe4e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add user profile fields."""
    # Add new user profile columns
    op.add_column("users", sa.Column("first_name", sa.String(length=100), nullable=True))
    op.add_column("users", sa.Column("last_name", sa.String(length=100), nullable=True))
    op.add_column("users", sa.Column("phone", sa.String(length=20), nullable=True))
    op.add_column(
        "users", sa.Column("phone_verified", sa.Boolean(), nullable=False, server_default="false")
    )
    op.add_column("users", sa.Column("bio", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("website", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("location", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("timezone", sa.String(length=50), nullable=True))
    op.add_column("users", sa.Column("language", sa.String(length=10), nullable=True))
    op.add_column("users", sa.Column("avatar_url", sa.String(length=500), nullable=True))


def downgrade() -> None:
    """Remove user profile fields."""
    op.drop_column("users", "avatar_url")
    op.drop_column("users", "language")
    op.drop_column("users", "timezone")
    op.drop_column("users", "location")
    op.drop_column("users", "website")
    op.drop_column("users", "bio")
    op.drop_column("users", "phone_verified")
    op.drop_column("users", "phone")
    op.drop_column("users", "last_name")
    op.drop_column("users", "first_name")
