"""Add template_key column and tenant-unique constraint.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2025-12-24 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: str | None = "7c6d5e4f3a2b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add template_key column and change unique constraint for tenant overrides."""
    # Add template_key column for standardized template lookup
    op.add_column(
        "communication_templates",
        sa.Column("template_key", sa.String(255), nullable=True),
    )

    # Create index on template_key for faster lookups
    op.create_index(
        "ix_communication_templates_template_key",
        "communication_templates",
        ["template_key"],
    )

    # Drop the existing unique constraint on name (global unique)
    # Note: The constraint name may vary, this is the standard naming
    try:
        op.drop_constraint(
            "communication_templates_name_key",
            "communication_templates",
            type_="unique",
        )
    except Exception:
        # Constraint might have a different name
        try:
            op.drop_index(
                "ix_communication_templates_name",
                table_name="communication_templates",
            )
        except Exception:
            pass

    # Create new composite unique constraint for tenant + name
    # This allows the same template name for different tenants
    op.create_unique_constraint(
        "uq_communication_templates_tenant_name",
        "communication_templates",
        ["tenant_id", "name"],
    )

    # Add index on tenant_id + template_key for optimized lookups
    op.create_index(
        "ix_communication_templates_tenant_template_key",
        "communication_templates",
        ["tenant_id", "template_key"],
    )


def downgrade() -> None:
    """Remove template_key column and revert to global unique name."""
    # Drop the new indexes
    op.drop_index(
        "ix_communication_templates_tenant_template_key",
        table_name="communication_templates",
    )

    # Drop the composite unique constraint
    op.drop_constraint(
        "uq_communication_templates_tenant_name",
        "communication_templates",
        type_="unique",
    )

    # Restore the original unique constraint on name
    op.create_unique_constraint(
        "communication_templates_name_key",
        "communication_templates",
        ["name"],
    )

    # Drop the template_key index and column
    op.drop_index(
        "ix_communication_templates_template_key",
        table_name="communication_templates",
    )
    op.drop_column("communication_templates", "template_key")
