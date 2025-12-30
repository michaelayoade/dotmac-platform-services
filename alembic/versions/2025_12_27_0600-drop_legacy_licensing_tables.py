"""Drop legacy licensing tables.

Revision ID: drop_legacy_lic
Revises: drop_lic_sub_unique
Create Date: 2025-12-27 06:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "drop_legacy_lic"
down_revision: str | None = "drop_lic_sub_unique"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    try:
        tables = inspector.get_table_names()
    except Exception:
        return False
    return table_name in tables


def _drop_table_if_exists(table_name: str) -> None:
    if _table_exists(table_name):
        op.drop_table(table_name)


def upgrade() -> None:
    # Drop legacy/v2 licensing tables in dependency order.
    _drop_table_if_exists("license_activations")
    _drop_table_if_exists("license_orders")
    _drop_table_if_exists("license_templates")
    _drop_table_if_exists("licenses")

    _drop_table_if_exists("plan_features")
    _drop_table_if_exists("plan_quotas")
    _drop_table_if_exists("tenant_quota_usage")
    _drop_table_if_exists("tenant_subscriptions")
    _drop_table_if_exists("subscription_plans")


def downgrade() -> None:
    # Irreversible migration; legacy tables intentionally removed.
    pass
