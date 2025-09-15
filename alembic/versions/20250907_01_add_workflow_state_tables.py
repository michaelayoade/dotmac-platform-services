"""add workflow state tables

Revision ID: 20250907_01
Revises: 
Create Date: 2025-09-07 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20250907_01"
down_revision = "add_workflow_orchestration_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Incident Response
    op.create_table(
        "bl_incidents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(length=255), index=True),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False, index=True),
        sa.Column("status", sa.String(length=30), nullable=False, index=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("opened_at", sa.DateTime(), nullable=False),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "bl_incident_escalations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("assignee", sa.String(length=255), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("escalated_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "bl_incident_timeline",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("details", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
    )

    # Payment Processing
    op.create_table(
        "bl_payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(length=255), index=True),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, index=True),
        sa.Column("provider", sa.String(length=50), nullable=True),
        sa.Column("provider_ref", sa.String(length=255), nullable=True, index=True),
        sa.Column("metadata", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("initiated_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "bl_payment_fraud_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("payment_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("model_version", sa.String(length=50), nullable=True),
        sa.Column("factors", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("evaluated_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "bl_payment_settlements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("payment_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("batch_id", sa.String(length=100), nullable=True, index=True),
        sa.Column("settled_at", sa.DateTime(), nullable=True),
    )

    # Service Provisioning
    op.create_table(
        "bl_provisioning_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(length=255), index=True),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("service_type", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, index=True),
        sa.Column("requested_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("details", postgresql.JSON(astext_type=sa.Text()), nullable=True),
    )
    op.create_table(
        "bl_provisioning_validations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("check_name", sa.String(length=100), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("info", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("validated_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "bl_provisioning_steps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("step_name", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("logs", sa.Text(), nullable=True),
        sa.Column("executed_at", sa.DateTime(), nullable=False),
    )

    # Workflow state and metrics
    op.create_table(
        "bl_workflow_state",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workflow_name", sa.String(length=100), nullable=False, index=True),
        sa.Column("correlation_id", sa.String(length=100), nullable=True, index=True),
        sa.Column("status", sa.String(length=30), nullable=False, index=True),
        sa.Column("state", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "bl_workflow_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workflow_name", sa.String(length=100), nullable=False, index=True),
        sa.Column("correlation_id", sa.String(length=100), nullable=True, index=True),
        sa.Column("event", sa.String(length=100), nullable=False),
        sa.Column("payload", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "bl_workflow_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workflow_name", sa.String(length=100), nullable=False, index=True),
        sa.Column("metric_name", sa.String(length=100), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("labels", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("observed_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("bl_workflow_metrics")
    op.drop_table("bl_workflow_history")
    op.drop_table("bl_workflow_state")
    op.drop_table("bl_provisioning_steps")
    op.drop_table("bl_provisioning_validations")
    op.drop_table("bl_provisioning_requests")
    op.drop_table("bl_payment_settlements")
    op.drop_table("bl_payment_fraud_scores")
    op.drop_table("bl_payments")
    op.drop_table("bl_incident_timeline")
    op.drop_table("bl_incident_escalations")
    op.drop_table("bl_incidents")
