"""create partner user invitations table

Revision ID: create_partner_invitations
Revises: create_tickets_tables
Create Date: 2025-12-26 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ENUM

# revision identifiers, used by Alembic.
revision = 'create_partner_invitations'
down_revision = 'create_partners_table'
branch_labels = None
depends_on = None

# Create enum
partner_invitation_status = ENUM(
    'pending', 'accepted', 'expired', 'revoked',
    name='partnerinvitationstatus',
    create_type=False
)


def upgrade() -> None:
    # Create enum first
    op.execute("CREATE TYPE partnerinvitationstatus AS ENUM ('pending', 'accepted', 'expired', 'revoked')")

    # Create partner_user_invitations table
    op.create_table(
        'partner_user_invitations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('partner_id', UUID(as_uuid=True), sa.ForeignKey('partners.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('email', sa.String(255), nullable=False, index=True),
        sa.Column('role', sa.String(50), nullable=False, server_default='account_manager'),
        sa.Column('invited_by', UUID(as_uuid=True), nullable=False),
        sa.Column('status', partner_invitation_status, nullable=False, server_default='pending'),
        sa.Column('token', sa.String(500), unique=True, nullable=False, index=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
        # Timestamp columns
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        # Tenant column (from TenantMixin)
        sa.Column('tenant_id', sa.String(255), nullable=False, index=True),
    )

    # Create composite indexes
    op.create_index('ix_partner_invitation_partner_status', 'partner_user_invitations', ['partner_id', 'status'])


def downgrade() -> None:
    op.drop_table('partner_user_invitations')
    op.execute("DROP TYPE IF EXISTS partnerinvitationstatus")
