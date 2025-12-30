"""Fix communications schema - bulk jobs table and status enum.

Revision ID: fix_communications_schema
Revises: fix_licensing_columns
Create Date: 2025-12-27 04:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision: str = "fix_communications_schema"
down_revision: str | None = "fix_licensing_columns"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def table_exists(table_name: str) -> bool:
    """Check if a table exists."""
    bind = op.get_bind()
    result = bind.execute(
        sa.text(
            """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = :table
            )
            """
        ),
        {"table": table_name},
    )
    return result.scalar()


def column_type_is_varchar(table_name: str, column_name: str) -> bool:
    """Check if a column is VARCHAR type."""
    bind = op.get_bind()
    result = bind.execute(
        sa.text(
            """
            SELECT data_type FROM information_schema.columns
            WHERE table_name = :table AND column_name = :column
            """
        ),
        {"table": table_name, "column": column_name},
    )
    data_type = result.scalar()
    return data_type == "character varying" if data_type else False


def upgrade() -> None:
    """Fix communications schema."""

    # 1. Create communication_bulk_jobs table if it doesn't exist
    if not table_exists("communication_bulk_jobs"):
        op.create_table(
            "communication_bulk_jobs",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", sa.String(255), nullable=True, index=True),
            sa.Column("job_id", sa.String(255), nullable=False, unique=True, index=True),
            sa.Column("task_id", sa.String(255), nullable=True, index=True),
            sa.Column("template_id", sa.String(255), nullable=True),
            sa.Column("recipient_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("status", sa.String(50), nullable=False, server_default="queued"),
            sa.Column("metadata", sa.JSON(), nullable=False, server_default="{}"),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        )

    # 2. Fix communication_logs.status column - convert from VARCHAR to enum
    if column_type_is_varchar("communication_logs", "status"):
        # First, update any status values to match enum values (lowercase)
        op.execute(
            sa.text(
                """
                UPDATE communication_logs
                SET status = LOWER(status)
                WHERE status != LOWER(status)
                """
            )
        )

        # Drop the default before altering the column type
        op.execute(
            sa.text(
                """
                ALTER TABLE communication_logs
                ALTER COLUMN status DROP DEFAULT
                """
            )
        )

        # Alter the column to use the enum type
        op.execute(
            sa.text(
                """
                ALTER TABLE communication_logs
                ALTER COLUMN status TYPE communicationstatus
                USING status::communicationstatus
                """
            )
        )

        # Set the new default using the enum type
        op.execute(
            sa.text(
                """
                ALTER TABLE communication_logs
                ALTER COLUMN status SET DEFAULT 'pending'::communicationstatus
                """
            )
        )


def downgrade() -> None:
    """Revert changes."""
    pass
