"""Create communication_templates table.

Revision ID: 7c6d5e4f3a2b
Revises: a1b2c3d4e5f6
Create Date: 2025-12-24 11:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "7c6d5e4f3a2b"
down_revision: str | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create communication_templates table."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "communication_templates" in inspector.get_table_names():
        return

    communication_type_enum = postgresql.ENUM(
        "email",
        "webhook",
        "sms",
        "push",
        name="communicationtype",
        create_type=False,
    )
    communication_type_enum.create(bind, checkfirst=True)

    op.create_table(
        "communication_templates",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("tenant_id", sa.String(255), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("type", communication_type_enum, nullable=False, server_default="email"),
        sa.Column("subject_template", sa.Text(), nullable=True),
        sa.Column("text_template", sa.Text(), nullable=True),
        sa.Column("html_template", sa.Text(), nullable=True),
        sa.Column("variables", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("required_variables", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("usage_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint("name", name="communication_templates_name_key"),
    )

    op.create_index(
        "ix_communication_templates_name",
        "communication_templates",
        ["name"],
    )
    op.create_index(
        "ix_communication_templates_tenant_id",
        "communication_templates",
        ["tenant_id"],
    )


def downgrade() -> None:
    """Drop communication_templates table."""
    try:
        op.drop_index("ix_communication_templates_tenant_id", table_name="communication_templates")
    except Exception:
        pass
    try:
        op.drop_index("ix_communication_templates_name", table_name="communication_templates")
    except Exception:
        pass
    op.drop_table("communication_templates")

    bind = op.get_bind()
    postgresql.ENUM(name="communicationtype").drop(bind, checkfirst=True)
