"""add concurrent indexes for workflow/state tables (RDS-safe)

Revision ID: 20250907_02
Revises: 20250907_01
Create Date: 2025-09-07 00:15:00.000000

"""

from alembic import op
from typing import Sequence

# revision identifiers, used by Alembic.
revision: str = "20250907_02"
down_revision: str | None = "20250907_01"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def _create_index(name: str, table: str, columns: list[str]) -> None:
    ctx = op.get_context()
    if ctx.dialect.name == "postgresql":
        cols = ", ".join(columns)
        sql = f"CREATE INDEX CONCURRENTLY IF NOT EXISTS {name} ON {table} ({cols})"
        with ctx.autocommit_block():
            op.execute(sql)
    else:
        op.create_index(name, table, columns)


def _drop_index(name: str, table: str) -> None:
    ctx = op.get_context()
    if ctx.dialect.name == "postgresql":
        with ctx.autocommit_block():
            op.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {name}")
    else:
        op.drop_index(name, table_name=table, if_exists=True)


def upgrade() -> None:
    # bl_incidents
    _create_index("ix_bl_incidents_tenant_status", "bl_incidents", ["tenant_id", "status"])
    _create_index("ix_bl_incidents_severity", "bl_incidents", ["severity"])
    _create_index("ix_bl_incidents_opened_at", "bl_incidents", ["opened_at"])

    # bl_incident_escalations
    _create_index("ix_bl_incident_escalations_incident_id", "bl_incident_escalations", ["incident_id"])
    _create_index("ix_bl_incident_escalations_level", "bl_incident_escalations", ["level"])

    # bl_incident_timeline
    _create_index("ix_bl_incident_timeline_incident_id", "bl_incident_timeline", ["incident_id"])
    _create_index("ix_bl_incident_timeline_occurred_at", "bl_incident_timeline", ["occurred_at"])

    # bl_payments
    _create_index("ix_bl_payments_tenant_status", "bl_payments", ["tenant_id", "status"])
    _create_index("ix_bl_payments_provider_ref", "bl_payments", ["provider_ref"])
    _create_index("ix_bl_payments_initiated_at", "bl_payments", ["initiated_at"])

    # bl_payment_fraud_scores
    _create_index("ix_bl_payment_fraud_scores_payment_id", "bl_payment_fraud_scores", ["payment_id"])

    # bl_payment_settlements
    _create_index("ix_bl_payment_settlements_payment_id", "bl_payment_settlements", ["payment_id"])
    _create_index("ix_bl_payment_settlements_batch_id", "bl_payment_settlements", ["batch_id"])

    # bl_provisioning_requests
    _create_index("ix_bl_provisioning_requests_tenant_status", "bl_provisioning_requests", ["tenant_id", "status"])
    _create_index("ix_bl_provisioning_requests_customer_id", "bl_provisioning_requests", ["customer_id"])
    _create_index("ix_bl_provisioning_requests_requested_at", "bl_provisioning_requests", ["requested_at"])

    # bl_provisioning_validations
    _create_index("ix_bl_provisioning_validations_request_id", "bl_provisioning_validations", ["request_id"])
    _create_index("ix_bl_provisioning_validations_check_name", "bl_provisioning_validations", ["check_name"])

    # bl_provisioning_steps
    _create_index("ix_bl_provisioning_steps_request_id", "bl_provisioning_steps", ["request_id"])
    _create_index("ix_bl_provisioning_steps_step_name", "bl_provisioning_steps", ["step_name"])

    # bl_workflow_state
    _create_index("ix_bl_workflow_state_name_status", "bl_workflow_state", ["workflow_name", "status"])
    _create_index("ix_bl_workflow_state_correlation_id", "bl_workflow_state", ["correlation_id"])
    _create_index("ix_bl_workflow_state_updated_at", "bl_workflow_state", ["updated_at"])

    # bl_workflow_history
    _create_index("ix_bl_workflow_history_name_corr", "bl_workflow_history", ["workflow_name", "correlation_id"])
    _create_index("ix_bl_workflow_history_occurred_at", "bl_workflow_history", ["occurred_at"])

    # bl_workflow_metrics
    _create_index("ix_bl_workflow_metrics_name_metric", "bl_workflow_metrics", ["workflow_name", "metric_name"])
    _create_index("ix_bl_workflow_metrics_observed_at", "bl_workflow_metrics", ["observed_at"])


def downgrade() -> None:
    _drop_index("ix_bl_workflow_metrics_observed_at", "bl_workflow_metrics")
    _drop_index("ix_bl_workflow_metrics_name_metric", "bl_workflow_metrics")
    _drop_index("ix_bl_workflow_history_occurred_at", "bl_workflow_history")
    _drop_index("ix_bl_workflow_history_name_corr", "bl_workflow_history")
    _drop_index("ix_bl_workflow_state_updated_at", "bl_workflow_state")
    _drop_index("ix_bl_workflow_state_correlation_id", "bl_workflow_state")
    _drop_index("ix_bl_workflow_state_name_status", "bl_workflow_state")
    _drop_index("ix_bl_provisioning_steps_step_name", "bl_provisioning_steps")
    _drop_index("ix_bl_provisioning_steps_request_id", "bl_provisioning_steps")
    _drop_index("ix_bl_provisioning_validations_check_name", "bl_provisioning_validations")
    _drop_index("ix_bl_provisioning_validations_request_id", "bl_provisioning_validations")
    _drop_index("ix_bl_provisioning_requests_requested_at", "bl_provisioning_requests")
    _drop_index("ix_bl_provisioning_requests_customer_id", "bl_provisioning_requests")
    _drop_index("ix_bl_provisioning_requests_tenant_status", "bl_provisioning_requests")
    _drop_index("ix_bl_payment_settlements_batch_id", "bl_payment_settlements")
    _drop_index("ix_bl_payment_settlements_payment_id", "bl_payment_settlements")
    _drop_index("ix_bl_payment_fraud_scores_payment_id", "bl_payment_fraud_scores")
    _drop_index("ix_bl_payments_initiated_at", "bl_payments")
    _drop_index("ix_bl_payments_provider_ref", "bl_payments")
    _drop_index("ix_bl_payments_tenant_status", "bl_payments")
    _drop_index("ix_bl_incident_timeline_occurred_at", "bl_incident_timeline")
    _drop_index("ix_bl_incident_timeline_incident_id", "bl_incident_timeline")
    _drop_index("ix_bl_incident_escalations_level", "bl_incident_escalations")
    _drop_index("ix_bl_incident_escalations_incident_id", "bl_incident_escalations")
    _drop_index("ix_bl_incidents_opened_at", "bl_incidents")
    _drop_index("ix_bl_incidents_severity", "bl_incidents")
    _drop_index("ix_bl_incidents_tenant_status", "bl_incidents")

