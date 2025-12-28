"""Create notifications tables.

Revision ID: create_notifications_tables
Revises: create_licensing_tables
Create Date: 2025-12-26 20:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "create_notifications_tables"
down_revision: str | None = "create_licensing_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    # Create ENUM types if they don't exist
    notificationtype_enum = postgresql.ENUM(
        'service_activated', 'service_failed', 'service_outage', 'service_restored',
        'bandwidth_limit_reached', 'connection_quality_degraded', 'alarm',
        'invoice_generated', 'invoice_due', 'invoice_overdue',
        'payment_received', 'payment_failed', 'subscription_renewed', 'subscription_cancelled',
        'dunning_reminder', 'dunning_suspension_warning', 'dunning_final_notice',
        'ticket_created', 'ticket_assigned', 'ticket_updated', 'ticket_resolved',
        'ticket_closed', 'ticket_reopened',
        'password_reset', 'account_locked', 'two_factor_enabled', 'api_key_expiring', 'system_alert',
        'system_announcement', 'custom',
        name='notificationtype',
        create_type=False
    )

    notificationpriority_enum = postgresql.ENUM(
        'low', 'medium', 'high', 'urgent',
        name='notificationpriority',
        create_type=False
    )

    # Create ENUMs if they don't exist
    result = bind.execute(sa.text("SELECT 1 FROM pg_type WHERE typname = 'notificationtype'"))
    if not result.fetchone():
        notificationtype_enum.create(bind, checkfirst=True)

    result = bind.execute(sa.text("SELECT 1 FROM pg_type WHERE typname = 'notificationpriority'"))
    if not result.fetchone():
        notificationpriority_enum.create(bind, checkfirst=True)

    # notifications
    if "notifications" not in existing_tables:
        op.create_table(
            "notifications",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", sa.String(50), nullable=False, index=True),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
            sa.Column("type", postgresql.ENUM(
                'service_activated', 'service_failed', 'service_outage', 'service_restored',
                'bandwidth_limit_reached', 'connection_quality_degraded', 'alarm',
                'invoice_generated', 'invoice_due', 'invoice_overdue',
                'payment_received', 'payment_failed', 'subscription_renewed', 'subscription_cancelled',
                'dunning_reminder', 'dunning_suspension_warning', 'dunning_final_notice',
                'ticket_created', 'ticket_assigned', 'ticket_updated', 'ticket_resolved',
                'ticket_closed', 'ticket_reopened',
                'password_reset', 'account_locked', 'two_factor_enabled', 'api_key_expiring', 'system_alert',
                'system_announcement', 'custom',
                name='notificationtype', create_type=False
            ), nullable=False, index=True),
            sa.Column("priority", postgresql.ENUM(
                'low', 'medium', 'high', 'urgent',
                name='notificationpriority', create_type=False
            ), nullable=False, server_default='medium', index=True),
            sa.Column("title", sa.String(500), nullable=False),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("action_url", sa.String(1000), nullable=True),
            sa.Column("action_label", sa.String(100), nullable=True),
            sa.Column("related_entity_type", sa.String(100), nullable=True, index=True),
            sa.Column("related_entity_id", sa.String(255), nullable=True, index=True),
            sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false", index=True),
            sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_archived", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("channels", postgresql.JSON(), nullable=False, server_default="[]"),
            sa.Column("email_sent", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("email_sent_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("sms_sent", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("sms_sent_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("push_sent", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("push_sent_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("metadata", postgresql.JSON(), nullable=False, server_default="{}"),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )

    # notification_preferences
    if "notification_preferences" not in existing_tables:
        op.create_table(
            "notification_preferences",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", sa.String(50), nullable=False, index=True),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("email_enabled", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("sms_enabled", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("push_enabled", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("quiet_hours_enabled", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("quiet_hours_start", sa.String(5), nullable=True),
            sa.Column("quiet_hours_end", sa.String(5), nullable=True),
            sa.Column("quiet_hours_timezone", sa.String(50), nullable=True),
            sa.Column("type_preferences", postgresql.JSON(), nullable=False, server_default="{}"),
            sa.Column("minimum_priority", postgresql.ENUM(
                'low', 'medium', 'high', 'urgent',
                name='notificationpriority', create_type=False
            ), nullable=False, server_default='low'),
            sa.Column("email_digest_enabled", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("email_digest_frequency", sa.String(20), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.UniqueConstraint("tenant_id", "user_id", name="uq_notification_pref_tenant_user"),
        )

    # notification_templates
    if "notification_templates" not in existing_tables:
        op.create_table(
            "notification_templates",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", sa.String(50), nullable=False, index=True),
            sa.Column("type", postgresql.ENUM(
                'service_activated', 'service_failed', 'service_outage', 'service_restored',
                'bandwidth_limit_reached', 'connection_quality_degraded', 'alarm',
                'invoice_generated', 'invoice_due', 'invoice_overdue',
                'payment_received', 'payment_failed', 'subscription_renewed', 'subscription_cancelled',
                'dunning_reminder', 'dunning_suspension_warning', 'dunning_final_notice',
                'ticket_created', 'ticket_assigned', 'ticket_updated', 'ticket_resolved',
                'ticket_closed', 'ticket_reopened',
                'password_reset', 'account_locked', 'two_factor_enabled', 'api_key_expiring', 'system_alert',
                'system_announcement', 'custom',
                name='notificationtype', create_type=False
            ), nullable=False, unique=True, index=True),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("title_template", sa.String(500), nullable=False),
            sa.Column("message_template", sa.Text(), nullable=False),
            sa.Column("action_url_template", sa.String(1000), nullable=True),
            sa.Column("action_label", sa.String(100), nullable=True),
            sa.Column("email_template_name", sa.String(255), nullable=True),
            sa.Column("sms_template", sa.String(160), nullable=True),
            sa.Column("push_title_template", sa.String(100), nullable=True),
            sa.Column("push_body_template", sa.String(200), nullable=True),
            sa.Column("default_priority", postgresql.ENUM(
                'low', 'medium', 'high', 'urgent',
                name='notificationpriority', create_type=False
            ), nullable=False, server_default='medium'),
            sa.Column("default_channels", postgresql.JSON(), nullable=False, server_default="[]"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("required_variables", postgresql.JSON(), nullable=False, server_default="[]"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )

    # push_subscriptions
    if "push_subscriptions" not in existing_tables:
        op.create_table(
            "push_subscriptions",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", sa.String(50), nullable=False, index=True),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
            sa.Column("endpoint", sa.Text(), nullable=False),
            sa.Column("p256dh_key", sa.Text(), nullable=True),
            sa.Column("auth_key", sa.Text(), nullable=True),
            sa.Column("device_type", sa.String(50), nullable=True),
            sa.Column("device_name", sa.String(255), nullable=True),
            sa.Column("browser", sa.String(100), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )


def downgrade() -> None:
    tables = [
        "push_subscriptions",
        "notification_templates",
        "notification_preferences",
        "notifications",
    ]
    for table in tables:
        op.drop_table(table)

    # Drop ENUMs
    op.execute("DROP TYPE IF EXISTS notificationtype")
    op.execute("DROP TYPE IF EXISTS notificationpriority")
