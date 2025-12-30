"""create_tickets_tables

Revision ID: create_tickets_tables
Revises: 538fcb9b9612
Create Date: 2025-12-25 16:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON, ENUM

# revision identifiers, used by Alembic.
revision = 'create_tickets_tables'
down_revision = '538fcb9b9612'
branch_labels = None
depends_on = None

# Create enums
ticket_status = ENUM('open', 'in_progress', 'waiting', 'resolved', 'closed', name='ticketstatus', create_type=False)
ticket_priority = ENUM('low', 'normal', 'high', 'urgent', 'critical', name='ticketpriority', create_type=False)
ticket_actor_type = ENUM('platform', 'partner', 'customer', 'system', 'external', name='ticketactortype', create_type=False)
ticket_type = ENUM('general', 'technical', 'billing', 'provisioning', 'installation', 'support_request', 'network_issue', 'equipment_issue', 'service_activation', 'service_cancellation', 'service_change', 'complaint', 'escalation', 'connectivity_issue', 'fault', 'outage', 'maintenance', name='tickettype', create_type=False)


def upgrade() -> None:
    # Create enums first
    op.execute("CREATE TYPE ticketstatus AS ENUM ('open', 'in_progress', 'waiting', 'resolved', 'closed')")
    op.execute("CREATE TYPE ticketpriority AS ENUM ('low', 'normal', 'high', 'urgent', 'critical')")
    op.execute("CREATE TYPE ticketactortype AS ENUM ('platform', 'partner', 'customer', 'system', 'external')")
    op.execute("CREATE TYPE tickettype AS ENUM ('general', 'technical', 'billing', 'provisioning', 'installation', 'support_request', 'network_issue', 'equipment_issue', 'service_activation', 'service_cancellation', 'service_change', 'complaint', 'escalation', 'connectivity_issue', 'fault', 'outage', 'maintenance')")

    # Create tickets table
    op.create_table(
        'tickets',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('ticket_number', sa.String(32), unique=True, nullable=False, index=True),
        sa.Column('subject', sa.String(255), nullable=False),
        sa.Column('status', ticket_status, nullable=False, server_default='open'),
        sa.Column('priority', ticket_priority, nullable=False, server_default='normal'),
        sa.Column('origin_type', ticket_actor_type, nullable=False),
        sa.Column('target_type', ticket_actor_type, nullable=False),
        sa.Column('origin_user_id', UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('assigned_to_user_id', UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('customer_id', UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('partner_id', UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('last_response_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('context', JSON, nullable=False, server_default='{}'),
        sa.Column('ticket_type', ticket_type, nullable=True, index=True),
        sa.Column('service_address', sa.String(500), nullable=True),
        sa.Column('affected_services', JSON, nullable=False, server_default='[]'),
        sa.Column('device_serial_numbers', JSON, nullable=False, server_default='[]'),
        sa.Column('sla_due_date', sa.DateTime(timezone=True), nullable=True, index=True),
        sa.Column('sla_breached', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('first_response_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolution_time_minutes', sa.Integer(), nullable=True),
        sa.Column('escalation_level', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('escalated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('escalated_to_user_id', UUID(as_uuid=True), nullable=True),
        # Timestamp/Audit columns
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('tenant_id', sa.String(255), nullable=False, index=True),
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.Column('updated_by', sa.String(255), nullable=True),
    )

    # Create indexes
    op.create_index('ix_tickets_status', 'tickets', ['status'])
    op.create_index('ix_tickets_priority', 'tickets', ['priority'])
    op.create_index('ix_tickets_origin_type', 'tickets', ['origin_type'])
    op.create_index('ix_tickets_target_type', 'tickets', ['target_type'])
    op.create_index('ix_tickets_tenant_status', 'tickets', ['tenant_id', 'status'])
    op.create_index('ix_tickets_partner_status', 'tickets', ['partner_id', 'status'])
    op.create_index('ix_tickets_tenant_type', 'tickets', ['tenant_id', 'ticket_type'])
    op.create_index('ix_tickets_sla_breach', 'tickets', ['sla_breached', 'sla_due_date'])

    # Create ticket_messages table
    op.create_table(
        'ticket_messages',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('ticket_id', UUID(as_uuid=True), sa.ForeignKey('tickets.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('sender_type', ticket_actor_type, nullable=False),
        sa.Column('sender_user_id', UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('sender_customer_id', UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('sender_partner_id', UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('is_internal', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('attachments', JSON, nullable=False, server_default='[]'),
        sa.Column('metadata', JSON, nullable=False, server_default='{}'),
        # Timestamp/Audit columns
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('tenant_id', sa.String(255), nullable=False, index=True),
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.Column('updated_by', sa.String(255), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('ticket_messages')
    op.drop_table('tickets')
    op.execute("DROP TYPE IF EXISTS tickettype")
    op.execute("DROP TYPE IF EXISTS ticketactortype")
    op.execute("DROP TYPE IF EXISTS ticketpriority")
    op.execute("DROP TYPE IF EXISTS ticketstatus")
