"""Create deployment_templates table.

Revision ID: 9f8e7d6c5b4a
Revises:
Create Date: 2025-12-16 09:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "9f8e7d6c5b4a"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create deployment_templates table."""
    deployment_backend_enum = postgresql.ENUM(
        "kubernetes",
        "awx_ansible",
        "docker_compose",
        "terraform",
        "manual",
        name="deploymentbackend",
        create_type=False,
    )
    deployment_type_enum = postgresql.ENUM(
        "cloud_shared",
        "cloud_dedicated",
        "on_prem",
        "hybrid",
        "edge",
        name="deploymenttype",
        create_type=False,
    )

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "deployment_templates" in inspector.get_table_names():
        return

    deployment_backend_enum.create(bind, checkfirst=True)
    deployment_type_enum.create(bind, checkfirst=True)

    op.create_table(
        "deployment_templates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("backend", deployment_backend_enum, nullable=False),
        sa.Column("deployment_type", deployment_type_enum, nullable=False),
        sa.Column("version", sa.String(50), nullable=False),
        sa.Column("cpu_cores", sa.Integer(), nullable=True),
        sa.Column("memory_gb", sa.Integer(), nullable=True),
        sa.Column("storage_gb", sa.Integer(), nullable=True),
        sa.Column("max_users", sa.Integer(), nullable=True),
        sa.Column("config_schema", sa.JSON(), nullable=True),
        sa.Column("default_config", sa.JSON(), nullable=True),
        sa.Column("required_secrets", sa.JSON(), nullable=True),
        sa.Column("feature_flags", sa.JSON(), nullable=True),
        sa.Column("helm_chart_url", sa.String(500), nullable=True),
        sa.Column("helm_chart_version", sa.String(50), nullable=True),
        sa.Column("ansible_playbook_path", sa.String(500), nullable=True),
        sa.Column("terraform_module_path", sa.String(500), nullable=True),
        sa.Column("docker_compose_path", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("requires_approval", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("estimated_provision_time_minutes", sa.Integer(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
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
        sa.UniqueConstraint("name", name="uq_deployment_templates_name"),
    )

    op.create_index(
        "ix_deployment_templates_name",
        "deployment_templates",
        ["name"],
        unique=True,
    )


def downgrade() -> None:
    """Drop deployment_templates table."""
    op.drop_index("ix_deployment_templates_name", table_name="deployment_templates")
    op.drop_table("deployment_templates")

    bind = op.get_bind()
    sa.Enum(name="deploymentbackend").drop(bind, checkfirst=True)
    sa.Enum(name="deploymenttype").drop(bind, checkfirst=True)
