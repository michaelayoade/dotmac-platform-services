"""Drop unique tenant constraint on licensing_tenant_subscriptions.

Revision ID: drop_lic_sub_unique
Revises: fix_communications_schema
Create Date: 2025-12-27 05:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "drop_lic_sub_unique"
down_revision: str | None = "fix_communications_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _drop_unique_constraint(table_name: str, column_name: str) -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    try:
        uniques = inspector.get_unique_constraints(table_name)
    except Exception:
        uniques = []

    for unique in uniques:
        columns = unique.get("column_names") or []
        name = unique.get("name")
        if name and columns == [column_name]:
            with op.batch_alter_table(table_name) as batch_op:
                batch_op.drop_constraint(name, type_="unique")


def _ensure_unique_constraint(table_name: str, column_name: str, name: str) -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    try:
        uniques = inspector.get_unique_constraints(table_name)
    except Exception:
        uniques = []

    for unique in uniques:
        columns = unique.get("column_names") or []
        if columns == [column_name]:
            return

    with op.batch_alter_table(table_name) as batch_op:
        batch_op.create_unique_constraint(name, [column_name])


def upgrade() -> None:
    _drop_unique_constraint("licensing_tenant_subscriptions", "tenant_id")


def downgrade() -> None:
    _ensure_unique_constraint(
        "licensing_tenant_subscriptions",
        "tenant_id",
        "uq_licensing_tenant_subscriptions_tenant_id",
    )
