"""Add email verification and profile change history tables

Revision ID: add_email_verification
Revises: fix_user_profile
Create Date: 2025-10-04 18:40:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = "add_email_verification"
down_revision = "fix_user_profile"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add email verification and profile change history tables."""
    from sqlalchemy import inspect
    from alembic import context

    conn = context.get_bind()
    inspector = inspect(conn)
    existing_tables = inspector.get_table_names()

    # Create email_verification_tokens table if it doesn't exist
    if "email_verification_tokens" not in existing_tables:
        op.create_table(
            "email_verification_tokens",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("user_id", UUID(as_uuid=True), nullable=False),
            sa.Column("token_hash", sa.String(255), nullable=False, unique=True),
            sa.Column("email", sa.String(255), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("used", sa.Boolean(), default=False, nullable=False, server_default="false"),
            sa.Column("used_at", sa.DateTime(), nullable=True),
            sa.Column("used_ip", sa.String(45), nullable=True),
            sa.Column("tenant_id", sa.String(255), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("now()"),
                onupdate=sa.text("now()"),
            ),
        )

        # Create indexes for email_verification_tokens
        op.create_index(
            "ix_email_verification_tokens_user_id",
            "email_verification_tokens",
            ["user_id"],
            unique=False,
        )
        op.create_index(
            "ix_email_verification_tokens_token_hash",
            "email_verification_tokens",
            ["token_hash"],
            unique=True,
        )
        op.create_index(
            "ix_email_verification_tokens_tenant_id",
            "email_verification_tokens",
            ["tenant_id"],
            unique=False,
        )

    # Create profile_change_history table if it doesn't exist
    if "profile_change_history" not in existing_tables:
        op.create_table(
            "profile_change_history",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("user_id", UUID(as_uuid=True), nullable=False),
            sa.Column("changed_by_user_id", UUID(as_uuid=True), nullable=False),
            sa.Column("field_name", sa.String(100), nullable=False),
            sa.Column("old_value", sa.Text(), nullable=True),
            sa.Column("new_value", sa.Text(), nullable=True),
            sa.Column("change_reason", sa.String(255), nullable=True),
            sa.Column("ip_address", sa.String(45), nullable=True),
            sa.Column("user_agent", sa.Text(), nullable=True),
            sa.Column("tenant_id", sa.String(255), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("now()"),
                onupdate=sa.text("now()"),
            ),
        )

        # Create indexes for profile_change_history
        op.create_index(
            "ix_profile_change_history_user_id", "profile_change_history", ["user_id"], unique=False
        )
        op.create_index(
            "ix_profile_change_history_field_name",
            "profile_change_history",
            ["field_name"],
            unique=False,
        )
        op.create_index(
            "ix_profile_change_history_tenant_id",
            "profile_change_history",
            ["tenant_id"],
            unique=False,
        )


def downgrade() -> None:
    """Drop email verification and profile change history tables."""
    # Drop profile_change_history indexes and table
    op.drop_index("ix_profile_change_history_tenant_id", table_name="profile_change_history")
    op.drop_index("ix_profile_change_history_field_name", table_name="profile_change_history")
    op.drop_index("ix_profile_change_history_user_id", table_name="profile_change_history")
    op.drop_table("profile_change_history")

    # Drop email_verification_tokens indexes and table
    op.drop_index("ix_email_verification_tokens_tenant_id", table_name="email_verification_tokens")
    op.drop_index("ix_email_verification_tokens_token_hash", table_name="email_verification_tokens")
    op.drop_index("ix_email_verification_tokens_user_id", table_name="email_verification_tokens")
    op.drop_table("email_verification_tokens")
