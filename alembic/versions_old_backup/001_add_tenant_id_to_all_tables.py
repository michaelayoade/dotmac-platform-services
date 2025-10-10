"""Add tenant_id to all tables

Revision ID: 001_add_tenant_id
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001_add_tenant_id"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add tenant_id column to all existing tables."""

    # Get all table names from the database
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    tables = inspector.get_table_names()

    # Add tenant_id to each table that doesn't have it
    for table_name in tables:
        # Skip alembic version table
        if table_name == "alembic_version":
            continue

        # Get existing columns
        columns = [col["name"] for col in inspector.get_columns(table_name)]

        # Add tenant_id if it doesn't exist
        if "tenant_id" not in columns:
            op.add_column(
                table_name, sa.Column("tenant_id", sa.String(255), nullable=True, index=True)
            )

            # Create index for tenant_id
            op.create_index(f"ix_{table_name}_tenant_id", table_name, ["tenant_id"], unique=False)


def downgrade() -> None:
    """Remove tenant_id column from all tables."""

    # Get all table names from the database
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    tables = inspector.get_table_names()

    # Remove tenant_id from each table
    for table_name in tables:
        # Skip alembic version table
        if table_name == "alembic_version":
            continue

        # Get existing columns
        columns = [col["name"] for col in inspector.get_columns(table_name)]

        # Remove tenant_id if it exists
        if "tenant_id" in columns:
            # Drop index first
            op.drop_index(f"ix_{table_name}_tenant_id", table_name)

            # Drop column
            op.drop_column(table_name, "tenant_id")
