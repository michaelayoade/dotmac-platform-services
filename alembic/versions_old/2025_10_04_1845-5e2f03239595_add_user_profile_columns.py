"""add_user_profile_columns

Revision ID: 5e2f03239595
Revises: add_email_verification
Create Date: 2025-10-04 18:45:34.627393

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "5e2f03239595"
down_revision = "add_email_verification"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add user profile columns to users table."""
    from sqlalchemy import inspect

    from alembic import context

    conn = context.get_bind()
    inspector = inspect(conn)
    existing_columns = [col["name"] for col in inspector.get_columns("users")]

    # Only add columns that don't already exist
    if "first_name" not in existing_columns:
        op.add_column("users", sa.Column("first_name", sa.String(length=100), nullable=True))
    if "last_name" not in existing_columns:
        op.add_column("users", sa.Column("last_name", sa.String(length=100), nullable=True))
    if "phone" not in existing_columns:
        op.add_column("users", sa.Column("phone", sa.String(length=20), nullable=True))
    if "phone_verified" not in existing_columns:
        op.add_column(
            "users",
            sa.Column("phone_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        )
    if "bio" not in existing_columns:
        op.add_column("users", sa.Column("bio", sa.Text(), nullable=True))
    if "website" not in existing_columns:
        op.add_column("users", sa.Column("website", sa.String(length=255), nullable=True))
    if "location" not in existing_columns:
        op.add_column("users", sa.Column("location", sa.String(length=255), nullable=True))
    if "timezone" not in existing_columns:
        op.add_column("users", sa.Column("timezone", sa.String(length=50), nullable=True))
    if "language" not in existing_columns:
        op.add_column("users", sa.Column("language", sa.String(length=10), nullable=True))
    if "avatar_url" not in existing_columns:
        op.add_column("users", sa.Column("avatar_url", sa.String(length=500), nullable=True))


def downgrade() -> None:
    """Remove user profile columns from users table."""
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
