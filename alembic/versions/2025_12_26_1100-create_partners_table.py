"""create partners table

Revision ID: create_partners_table
Revises: create_tickets_tables
Create Date: 2025-12-26 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ENUM

# revision identifiers, used by Alembic.
revision = 'create_partners_table'
down_revision = 'create_tickets_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    op.execute("""
        CREATE TYPE partnerstatus AS ENUM (
            'pending', 'active', 'suspended', 'terminated', 'archived'
        )
    """)
    op.execute("""
        CREATE TYPE partnertier AS ENUM (
            'bronze', 'silver', 'gold', 'platinum', 'direct'
        )
    """)
    op.execute("""
        CREATE TYPE commissionmodel AS ENUM (
            'revenue_share', 'flat_fee', 'tiered', 'hybrid'
        )
    """)
    op.execute("""
        CREATE TYPE commissionstatus AS ENUM (
            'pending', 'approved', 'paid', 'clawback', 'cancelled'
        )
    """)
    op.execute("""
        CREATE TYPE payoutstatus AS ENUM (
            'pending', 'ready', 'processing', 'completed', 'failed', 'cancelled'
        )
    """)
    op.execute("""
        CREATE TYPE referralstatus AS ENUM (
            'new', 'contacted', 'qualified', 'converted', 'lost', 'invalid'
        )
    """)
    op.execute("""
        CREATE TYPE partnertenantaccessrole AS ENUM (
            'msp_full', 'msp_billing', 'msp_support', 'enterprise_hq', 'auditor', 'reseller', 'delegate'
        )
    """)

    # Create partners table
    op.create_table(
        'partners',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('partner_number', sa.String(50), unique=True, nullable=False, index=True),

        # Company Information
        sa.Column('company_name', sa.String(255), nullable=False, index=True),
        sa.Column('legal_name', sa.String(255), nullable=True),
        sa.Column('website', sa.String(255), nullable=True),
        sa.Column('description', sa.Text, nullable=True),

        # Status and Tier
        sa.Column('status', ENUM('pending', 'active', 'suspended', 'terminated', 'archived', name='partnerstatus', create_type=False), nullable=False, server_default='pending'),
        sa.Column('tier', ENUM('bronze', 'silver', 'gold', 'platinum', 'direct', name='partnertier', create_type=False), nullable=False, server_default='bronze'),

        # Commission Configuration
        sa.Column('commission_model', ENUM('revenue_share', 'flat_fee', 'tiered', 'hybrid', name='commissionmodel', create_type=False), nullable=False, server_default='revenue_share'),
        sa.Column('default_commission_rate', sa.Numeric(5, 4), nullable=True),

        # Contact Information
        sa.Column('primary_email', sa.String(255), nullable=False),
        sa.Column('billing_email', sa.String(255), nullable=True),
        sa.Column('support_email', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(30), nullable=True),

        # Address Information
        sa.Column('address_line1', sa.String(200), nullable=True),
        sa.Column('address_line2', sa.String(200), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('state_province', sa.String(100), nullable=True),
        sa.Column('postal_code', sa.String(20), nullable=True),
        sa.Column('country', sa.String(2), nullable=True),

        # Business & Tax Information
        sa.Column('tax_id', sa.String(50), nullable=True),
        sa.Column('vat_number', sa.String(50), nullable=True),
        sa.Column('business_registration', sa.String(100), nullable=True),

        # SLA Configuration
        sa.Column('sla_response_hours', sa.Integer, nullable=True),
        sa.Column('sla_uptime_percentage', sa.Numeric(5, 2), nullable=True),

        # Partner Dates
        sa.Column('partnership_start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('partnership_end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), nullable=True),

        # Extended attributes
        sa.Column('metadata', sa.JSON, server_default='{}', nullable=False),
        sa.Column('certifications', sa.JSON, server_default='[]', nullable=False),
        sa.Column('specializations', sa.JSON, server_default='[]', nullable=False),

        # Internal tracking
        sa.Column('account_manager_id', sa.String(255), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),

        # Timestamps (from TimestampMixin)
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),

        # Tenant (from TenantMixin)
        sa.Column('tenant_id', sa.String(255), nullable=False, index=True),

        # Soft delete (from SoftDeleteMixin)
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),

        # Audit (from AuditMixin)
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.Column('updated_by', sa.String(255), nullable=True),
    )

    # Create indexes
    op.create_index('ix_partners_status', 'partners', ['status'])
    op.create_index('ix_partners_tier', 'partners', ['tier'])

    # Create partner_users table
    op.create_table(
        'partner_users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('partner_id', UUID(as_uuid=True), sa.ForeignKey('partners.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('role', sa.String(50), nullable=False, server_default='account_manager'),
        sa.Column('is_primary', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('permissions', sa.JSON, server_default='{}', nullable=False),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('last_access_at', sa.DateTime(timezone=True), nullable=True),
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        # Tenant
        sa.Column('tenant_id', sa.String(255), nullable=False, index=True),
        # Unique constraint
        sa.UniqueConstraint('partner_id', 'user_id', name='uq_partner_user'),
    )

    # Create partner_tenant_access table
    op.create_table(
        'partner_tenant_access',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('partner_id', UUID(as_uuid=True), sa.ForeignKey('partners.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('managed_tenant_id', sa.String(255), nullable=False, index=True),
        sa.Column('role', ENUM('msp_full', 'msp_billing', 'msp_support', 'enterprise_hq', 'auditor', 'reseller', 'delegate', name='partnertenantaccessrole', create_type=False), nullable=False),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('granted_by', sa.String(255), nullable=True),
        sa.Column('granted_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('permissions', sa.JSON, server_default='{}', nullable=False),
        sa.Column('notes', sa.Text, nullable=True),
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        # Tenant
        sa.Column('tenant_id', sa.String(255), nullable=False, index=True),
        # Unique constraint
        sa.UniqueConstraint('partner_id', 'managed_tenant_id', name='uq_partner_tenant'),
    )


def downgrade() -> None:
    op.drop_table('partner_tenant_access')
    op.drop_table('partner_users')
    op.drop_table('partners')

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS partnertenantaccessrole")
    op.execute("DROP TYPE IF EXISTS referralstatus")
    op.execute("DROP TYPE IF EXISTS payoutstatus")
    op.execute("DROP TYPE IF EXISTS commissionstatus")
    op.execute("DROP TYPE IF EXISTS commissionmodel")
    op.execute("DROP TYPE IF EXISTS partnertier")
    op.execute("DROP TYPE IF EXISTS partnerstatus")
