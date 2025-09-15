"""add foreign keys with NOT VALID and session timeouts (RDS-safe)

Revision ID: 20250907_03
Revises: 20250907_02
Create Date: 2025-09-07 00:25:00.000000

"""

from alembic import op
from typing import Sequence

# revision identifiers, used by Alembic.
revision: str = "20250907_03"
down_revision: str | None = "20250907_02"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def _set_timeouts() -> None:
    ctx = op.get_context()
    if ctx.dialect.name == "postgresql":
        # Session-level timeouts to reduce risk of long locks on RDS/Aurora
        op.execute("SET lock_timeout = '5s'")
        op.execute("SET statement_timeout = '60s'")


def upgrade() -> None:
    _set_timeouts()

    ctx = op.get_context()
    pg = ctx.dialect.name == "postgresql"

    def add_fk_not_valid(table: str, cname: str, col: str, ref_table: str, ref_col: str, ondelete: str | None = None):
        clause = f"ALTER TABLE {table} ADD CONSTRAINT {cname} FOREIGN KEY ({col}) REFERENCES {ref_table}({ref_col})"
        if ondelete:
            clause += f" ON DELETE {ondelete}"
        if pg:
            clause += " NOT VALID"
        op.execute(clause)
        if pg:
            op.execute(f"ALTER TABLE {table} VALIDATE CONSTRAINT {cname}")

    # bl_incident_escalations.incident_id -> bl_incidents.id (cascade on delete)
    add_fk_not_valid(
        table="bl_incident_escalations",
        cname="fk_bl_incident_escalations_incident",
        col="incident_id",
        ref_table="bl_incidents",
        ref_col="id",
        ondelete="CASCADE",
    )

    # bl_incident_timeline.incident_id -> bl_incidents.id (cascade on delete)
    add_fk_not_valid(
        table="bl_incident_timeline",
        cname="fk_bl_incident_timeline_incident",
        col="incident_id",
        ref_table="bl_incidents",
        ref_col="id",
        ondelete="CASCADE",
    )

    # bl_payment_fraud_scores.payment_id -> bl_payments.id (cascade)
    add_fk_not_valid(
        table="bl_payment_fraud_scores",
        cname="fk_bl_payment_fraud_scores_payment",
        col="payment_id",
        ref_table="bl_payments",
        ref_col="id",
        ondelete="CASCADE",
    )

    # bl_payment_settlements.payment_id -> bl_payments.id (cascade)
    add_fk_not_valid(
        table="bl_payment_settlements",
        cname="fk_bl_payment_settlements_payment",
        col="payment_id",
        ref_table="bl_payments",
        ref_col="id",
        ondelete="CASCADE",
    )

    # bl_provisioning_validations.request_id -> bl_provisioning_requests.id (cascade)
    add_fk_not_valid(
        table="bl_provisioning_validations",
        cname="fk_bl_provisioning_validations_request",
        col="request_id",
        ref_table="bl_provisioning_requests",
        ref_col="id",
        ondelete="CASCADE",
    )

    # bl_provisioning_steps.request_id -> bl_provisioning_requests.id (cascade)
    add_fk_not_valid(
        table="bl_provisioning_steps",
        cname="fk_bl_provisioning_steps_request",
        col="request_id",
        ref_table="bl_provisioning_requests",
        ref_col="id",
        ondelete="CASCADE",
    )

    # Optional: link provisioning_requests.customer_id -> customers.id (SET NULL)
    # Only add if customers table exists in the same schema; if not, this will fail.
    # Wrap in TRY..EXCEPTION for Postgres via DO block.
    if pg:
        op.execute(
            """
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = 'customers'
                ) THEN
                    ALTER TABLE bl_provisioning_requests
                    ADD CONSTRAINT fk_bl_provisioning_requests_customer
                    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL NOT VALID;
                    ALTER TABLE bl_provisioning_requests VALIDATE CONSTRAINT fk_bl_provisioning_requests_customer;
                END IF;
            EXCEPTION WHEN others THEN
                RAISE NOTICE 'Skipping FK fk_bl_provisioning_requests_customer: %', SQLERRM;
            END$$;
            """
        )


def downgrade() -> None:
    ctx = op.get_context()
    pg = ctx.dialect.name == "postgresql"

    def drop_fk(table: str, cname: str):
        op.execute(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {cname}")

    drop_fk("bl_provisioning_steps", "fk_bl_provisioning_steps_request")
    drop_fk("bl_provisioning_validations", "fk_bl_provisioning_validations_request")
    drop_fk("bl_payment_settlements", "fk_bl_payment_settlements_payment")
    drop_fk("bl_payment_fraud_scores", "fk_bl_payment_fraud_scores_payment")
    drop_fk("bl_incident_timeline", "fk_bl_incident_timeline_incident")
    drop_fk("bl_incident_escalations", "fk_bl_incident_escalations_incident")
    # Optional customer FK
    drop_fk("bl_provisioning_requests", "fk_bl_provisioning_requests_customer")

