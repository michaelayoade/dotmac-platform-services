"""create api_keys table for persistent API key storage

Revision ID: create_api_keys_table
Revises: create_tenants_table
Create Date: 2025-12-26 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'create_api_keys_table'
down_revision: Union[str, None] = 'create_tenants_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    if 'api_keys' in existing_tables:
        # Add prefix column if it doesn't exist
        columns = [c['name'] for c in inspector.get_columns('api_keys')]
        if 'prefix' not in columns:
            op.add_column('api_keys', sa.Column('prefix', sa.String(16), nullable=True))
        return

    op.create_table(
        'api_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tenant_id', sa.String(255), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('prefix', sa.String(16), nullable=False),
        sa.Column('key_hash', sa.String(255), nullable=False),
        sa.Column('scopes', postgresql.JSON(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', postgresql.JSON(), nullable=True),
        sa.UniqueConstraint('tenant_id', 'name', name='uq_api_keys_tenant_name'),
    )

    # Indexes for common queries
    op.create_index('ix_api_keys_tenant_id', 'api_keys', ['tenant_id', 'is_active'])
    op.create_index('ix_api_keys_user_id', 'api_keys', ['user_id'])
    op.create_index('ix_api_keys_key_hash', 'api_keys', ['key_hash'], unique=True)
    op.create_index('ix_api_keys_prefix', 'api_keys', ['prefix'])


def downgrade() -> None:
    op.drop_index('ix_api_keys_prefix')
    op.drop_index('ix_api_keys_key_hash')
    op.drop_index('ix_api_keys_user_id')
    op.drop_index('ix_api_keys_tenant_id')
    op.drop_table('api_keys')
