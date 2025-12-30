"""Add platform_products table

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2025-12-17 10:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "9f8e7d6c5b4a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create platform_products table."""
    op.create_table(
        "platform_products",
        # Identity
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("slug", sa.String(100), unique=True, nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("short_description", sa.String(500), nullable=True),
        # Deployment Configuration
        sa.Column("docker_image", sa.String(500), nullable=True),
        sa.Column("helm_chart_url", sa.String(500), nullable=True),
        sa.Column("helm_chart_version", sa.String(50), nullable=True),
        sa.Column("docker_compose_template", sa.String(500), nullable=True),
        # Resource Defaults (JSON)
        sa.Column(
            "default_resources",
            sa.JSON(),
            nullable=False,
            server_default='{"cpu": 2, "memory_gb": 4, "storage_gb": 50}',
        ),
        sa.Column(
            "required_services",
            sa.JSON(),
            nullable=False,
            server_default='["postgresql", "redis"]',
        ),
        # Module/Feature Configuration (JSON)
        sa.Column(
            "available_modules",
            sa.JSON(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "default_modules",
            sa.JSON(),
            nullable=False,
            server_default="[]",
        ),
        # Health & Monitoring
        sa.Column(
            "health_check_path",
            sa.String(255),
            nullable=False,
            server_default="/health",
        ),
        sa.Column(
            "metrics_path",
            sa.String(255),
            nullable=True,
            server_default="/metrics",
        ),
        # Branding & Display
        sa.Column("icon_url", sa.String(500), nullable=True),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("documentation_url", sa.String(500), nullable=True),
        # Status
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default="false"),
        # Versioning
        sa.Column(
            "current_version",
            sa.String(50),
            nullable=False,
            server_default="1.0.0",
        ),
        sa.Column("min_supported_version", sa.String(50), nullable=True),
        # Metadata
        sa.Column(
            "metadata",
            sa.JSON(),
            nullable=False,
            server_default="{}",
        ),
        # Foreign Key to deployment_templates
        sa.Column("template_id", sa.Integer(), nullable=False),
        # Timestamps (from TimestampMixin)
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
        # Soft delete (from SoftDeleteMixin)
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        # Foreign key constraint
        sa.ForeignKeyConstraint(
            ["template_id"],
            ["deployment_templates.id"],
            ondelete="RESTRICT",
        ),
    )

    # Create indexes (skip if they already exist)
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_indexes = {
        index["name"] for index in inspector.get_indexes("platform_products")
    }

    if "ix_platform_products_is_active" not in existing_indexes:
        op.create_index(
            "ix_platform_products_is_active",
            "platform_products",
            ["is_active"],
        )
    if "ix_platform_products_is_public" not in existing_indexes:
        op.create_index(
            "ix_platform_products_is_public",
            "platform_products",
            ["is_public"],
        )
    if "ix_platform_products_template_id" not in existing_indexes:
        op.create_index(
            "ix_platform_products_template_id",
            "platform_products",
            ["template_id"],
        )


def downgrade() -> None:
    """Drop platform_products table."""
    try:
        op.drop_index("ix_platform_products_template_id", table_name="platform_products")
    except Exception:
        pass
    try:
        op.drop_index("ix_platform_products_is_public", table_name="platform_products")
    except Exception:
        pass
    try:
        op.drop_index("ix_platform_products_is_active", table_name="platform_products")
    except Exception:
        pass
    try:
        op.drop_index("ix_platform_products_slug", table_name="platform_products")
    except Exception:
        pass
    op.drop_table("platform_products")
