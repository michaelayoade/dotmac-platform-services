"""Add enhanced communications tables

Revision ID: 2025_09_24_1200_add_communications_tables
Revises: 9d6a492bf126
Create Date: 2024-09-24 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'add_comms_tables'
down_revision: Union[str, None] = '9d6a492bf126'  # Fixed: was None, should link to merge head
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create enhanced communications tables."""
    # Create email_templates table
    op.create_table(
        'email_templates',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),

        # Template content
        sa.Column('subject_template', sa.Text, nullable=False),
        sa.Column('html_template', sa.Text, nullable=False),
        sa.Column('text_template', sa.Text),

        # Template metadata
        sa.Column('variables', sa.JSON),
        sa.Column('category', sa.String(100)),
        sa.Column('is_active', sa.Boolean, default=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create bulk_email_jobs table
    op.create_table(
        'bulk_email_jobs',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('template_id', sa.String(50), nullable=False),

        # Job configuration
        sa.Column('recipients', sa.JSON, nullable=False),
        sa.Column('template_data', sa.JSON),

        # Job status and metrics
        sa.Column('status', sa.String(20), default='queued'),
        sa.Column('total_recipients', sa.Integer, default=0),
        sa.Column('sent_count', sa.Integer, default=0),
        sa.Column('failed_count', sa.Integer, default=0),

        # Error handling
        sa.Column('error_message', sa.Text),
        sa.Column('retry_count', sa.Integer, default=0),
        sa.Column('max_retries', sa.Integer, default=3),

        # Timestamps
        sa.Column('scheduled_at', sa.DateTime(timezone=True)),
        sa.Column('started_at', sa.DateTime(timezone=True)),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create email_deliveries table
    op.create_table(
        'email_deliveries',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('job_id', sa.String(50)),
        sa.Column('template_id', sa.String(50)),

        # Email details
        sa.Column('recipient_email', sa.String(255), nullable=False),
        sa.Column('subject', sa.Text, nullable=False),

        # Delivery tracking
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('priority', sa.String(20), default='normal'),
        sa.Column('provider_id', sa.String(100)),

        # Timestamps and attempts
        sa.Column('sent_at', sa.DateTime(timezone=True)),
        sa.Column('delivered_at', sa.DateTime(timezone=True)),
        sa.Column('failed_at', sa.DateTime(timezone=True)),
        sa.Column('attempt_count', sa.Integer, default=0),

        # Error tracking
        sa.Column('error_message', sa.Text),
        sa.Column('metadata', sa.JSON),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create indexes for performance
    op.create_index('idx_email_templates_category', 'email_templates', ['category'])
    op.create_index('idx_email_templates_active', 'email_templates', ['is_active'])
    op.create_index('idx_email_templates_created', 'email_templates', ['created_at'])

    op.create_index('idx_bulk_jobs_status', 'bulk_email_jobs', ['status'])
    op.create_index('idx_bulk_jobs_template', 'bulk_email_jobs', ['template_id'])
    op.create_index('idx_bulk_jobs_created', 'bulk_email_jobs', ['created_at'])

    op.create_index('idx_deliveries_job', 'email_deliveries', ['job_id'])
    op.create_index('idx_deliveries_status', 'email_deliveries', ['status'])
    op.create_index('idx_deliveries_recipient', 'email_deliveries', ['recipient_email'])
    op.create_index('idx_deliveries_created', 'email_deliveries', ['created_at'])


def downgrade() -> None:
    """Drop enhanced communications tables."""
    # Drop indexes
    op.drop_index('idx_deliveries_created')
    op.drop_index('idx_deliveries_recipient')
    op.drop_index('idx_deliveries_status')
    op.drop_index('idx_deliveries_job')

    op.drop_index('idx_bulk_jobs_created')
    op.drop_index('idx_bulk_jobs_template')
    op.drop_index('idx_bulk_jobs_status')

    op.drop_index('idx_email_templates_created')
    op.drop_index('idx_email_templates_active')
    op.drop_index('idx_email_templates_category')

    # Drop tables
    op.drop_table('email_deliveries')
    op.drop_table('bulk_email_jobs')
    op.drop_table('email_templates')