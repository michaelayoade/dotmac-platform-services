"""link workflows to core entities (FKs) and add timeouts globally

Revision ID: 20250907_04
Revises: 20250907_03
Create Date: 2025-09-07 00:35:00.000000

"""

from alembic import op
import sqlalchemy as sa
from typing import Sequence

# revision identifiers, used by Alembic.
revision: str = "20250907_04"
down_revision: str | None = "20250907_03"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def _set_timeouts() -> None:
    ctx = op.get_context()
    if ctx.dialect.name == "postgresql":
        op.execute("SET lock_timeout = '5s'")
        op.execute("SET statement_timeout = '60s'")


def upgrade() -> None:
    _set_timeouts()

    ctx = op.get_context()
    pg = ctx.dialect.name == "postgresql"

    # Add columns if not exist (for Postgres) then create FKs NOT VALID
    if pg:
        # reporter_user_id on bl_incidents
        op.execute(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='bl_incidents' AND column_name='reporter_user_id'
                ) THEN
                    ALTER TABLE bl_incidents ADD COLUMN reporter_user_id uuid NULL;
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_bl_incidents_reporter_user_id ON bl_incidents(reporter_user_id);
                END IF;
            END$$;
            """
        )
        # subscription_id on bl_payments
        op.execute(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='bl_payments' AND column_name='subscription_id'
                ) THEN
                    ALTER TABLE bl_payments ADD COLUMN subscription_id uuid NULL;
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_bl_payments_subscription_id ON bl_payments(subscription_id);
                END IF;
            END$$;
            """
        )
    else:
        # Generic engines: attempt to add columns normally
        with op.batch_alter_table("bl_incidents") as batch:
            batch.add_column(sa.Column("reporter_user_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
        with op.batch_alter_table("bl_payments") as batch:
            batch.add_column(sa.Column("subscription_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))

    # FKs (NOT VALID then VALIDATE for Postgres)
    def add_fk_not_valid(table: str, cname: str, col: str, ref_table: str, ref_col: str, ondelete: str | None = None):
        clause = f"ALTER TABLE {table} ADD CONSTRAINT {cname} FOREIGN KEY ({col}) REFERENCES {ref_table}({ref_col})"
        if ondelete:
            clause += f" ON DELETE {ondelete}"
        if pg:
            clause += " NOT VALID"
        op.execute(clause)
        if pg:
            op.execute(f"ALTER TABLE {table} VALIDATE CONSTRAINT {cname}")

    # bl_incidents.reporter_user_id -> users.id SET NULL
    add_fk_not_valid(
        table="bl_incidents",
        cname="fk_bl_incidents_reporter_user",
        col="reporter_user_id",
        ref_table="users",
        ref_col="id",
        ondelete="SET NULL",
    )

    # bl_incidents.tenant_id (string) -> customer_tenants.tenant_id (unique) SET NULL
    # Only if the unique column exists; protect with DO block in Postgres
    if pg:
        op.execute(
            """
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'customer_tenants' AND column_name = 'tenant_id'
                ) THEN
                    ALTER TABLE bl_incidents
                    ADD CONSTRAINT fk_bl_incidents_tenant_str
                    FOREIGN KEY (tenant_id) REFERENCES customer_tenants(tenant_id) ON DELETE SET NULL NOT VALID;
                    ALTER TABLE bl_incidents VALIDATE CONSTRAINT fk_bl_incidents_tenant_str;
                END IF;
            EXCEPTION WHEN others THEN
                RAISE NOTICE 'Skipping FK fk_bl_incidents_tenant_str: %', SQLERRM;
            END$$;
            """
        )

    # bl_payments.subscription_id -> subscriptions.id SET NULL
    add_fk_not_valid(
        table="bl_payments",
        cname="fk_bl_payments_subscription",
        col="subscription_id",
        ref_table="subscriptions",
        ref_col="id",
        ondelete="SET NULL",
    )


def downgrade() -> None:
    def drop_fk(table: str, cname: str):
        op.execute(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {cname}")

    drop_fk("bl_payments", "fk_bl_payments_subscription")
    drop_fk("bl_incidents", "fk_bl_incidents_tenant_str")
    drop_fk("bl_incidents", "fk_bl_incidents_reporter_user")

    # Drop columns (safe if empty)
    with op.batch_alter_table("bl_payments") as batch:
        batch.drop_column("subscription_id")
    with op.batch_alter_table("bl_incidents") as batch:
        batch.drop_column("reporter_user_id")

