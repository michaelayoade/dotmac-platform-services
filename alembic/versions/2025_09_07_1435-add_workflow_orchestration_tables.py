"""Add workflow orchestration tables

Revision ID: add_workflow_orchestration_tables
Revises: add_user_management
Create Date: 2025-09-07 14:35:00.000000

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers
revision = 'add_workflow_orchestration_tables'
down_revision = 'add_user_management'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create workflow orchestration tables for sagas and idempotent operations."""
    
    # Create enum types for workflow orchestration
    op.execute("CREATE TYPE saga_status_enum AS ENUM ('pending', 'running', 'completed', 'failed', 'compensating', 'compensated')")
    op.execute("CREATE TYPE step_status_enum AS ENUM ('pending', 'running', 'completed', 'failed', 'compensating', 'compensated', 'skipped')")
    op.execute("CREATE TYPE operation_status_enum AS ENUM ('pending', 'running', 'completed', 'failed')")
    
    # === Saga Executions Table ===
    op.create_table('saga_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('saga_name', sa.String(length=100), nullable=False, index=True),
        sa.Column('tenant_id', sa.String(length=100), nullable=False, index=True),
        sa.Column('user_id', sa.String(length=100), nullable=True),
        sa.Column('correlation_id', sa.String(length=100), nullable=False, index=True),
        
        # Execution tracking
        sa.Column('status', sa.Enum('pending', 'running', 'completed', 'failed', 'compensating', 'compensated', name='saga_status_enum'), nullable=False, default='pending', index=True),
        sa.Column('current_step', sa.String(length=100), nullable=True),
        sa.Column('current_step_index', sa.Integer(), nullable=False, default=0),
        sa.Column('total_steps', sa.Integer(), nullable=False, default=0),
        
        # Data and timing
        sa.Column('input_data', sa.JSON(), nullable=True),
        sa.Column('output_data', sa.JSON(), nullable=True),
        sa.Column('error_data', sa.JSON(), nullable=True),
        sa.Column('context_data', sa.JSON(), nullable=True),
        sa.Column('saga_metadata', sa.JSON(), nullable=False, default={}),
        
        # Timing
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        
        # Indexes for performance
        sa.Index('idx_saga_executions_tenant_status', 'tenant_id', 'status'),
        sa.Index('idx_saga_executions_correlation_id', 'correlation_id'),
        sa.Index('idx_saga_executions_created_at', 'created_at'),
    )
    
    # === Saga Step Executions Table ===
    op.create_table('saga_step_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('saga_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('step_name', sa.String(length=100), nullable=False),
        sa.Column('step_index', sa.Integer(), nullable=False),
        
        # Execution tracking
        sa.Column('status', sa.Enum('pending', 'running', 'completed', 'failed', 'compensating', 'compensated', 'skipped', name='step_status_enum'), nullable=False, default='pending'),
        sa.Column('attempt_count', sa.Integer(), nullable=False, default=0),
        sa.Column('max_attempts', sa.Integer(), nullable=False, default=3),
        
        # Results and errors
        sa.Column('input_data', sa.JSON(), nullable=True),
        sa.Column('output_data', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_data', sa.JSON(), nullable=True),
        
        # Compensation
        sa.Column('compensation_data', sa.JSON(), nullable=True),
        sa.Column('compensation_attempts', sa.Integer(), nullable=False, default=0),
        sa.Column('max_compensation_attempts', sa.Integer(), nullable=False, default=3),
        
        # Timing
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        
        # Foreign key constraint
        sa.ForeignKeyConstraint(['saga_id'], ['saga_executions.id'], ondelete='CASCADE'),
        
        # Indexes for performance
        sa.Index('idx_saga_step_executions_saga_id', 'saga_id'),
        sa.Index('idx_saga_step_executions_step_index', 'saga_id', 'step_index'),
        sa.Index('idx_saga_step_executions_status', 'status'),
    )
    
    # === Idempotent Operations Table ===
    op.create_table('idempotent_operations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('idempotency_key', sa.String(length=255), nullable=False, unique=True, index=True),
        sa.Column('operation_type', sa.String(length=100), nullable=False, index=True),
        sa.Column('tenant_id', sa.String(length=100), nullable=False, index=True),
        sa.Column('user_id', sa.String(length=100), nullable=True),
        sa.Column('correlation_id', sa.String(length=100), nullable=False, index=True),
        
        # Operation tracking
        sa.Column('status', sa.Enum('pending', 'running', 'completed', 'failed', name='operation_status_enum'), nullable=False, default='pending', index=True),
        sa.Column('attempt_count', sa.Integer(), nullable=False, default=0),
        sa.Column('max_attempts', sa.Integer(), nullable=False, default=3),
        
        # Data and timing
        sa.Column('input_data', sa.JSON(), nullable=True),
        sa.Column('output_data', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_data', sa.JSON(), nullable=True),
        
        # Timing and metadata
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),  # For cleanup
        sa.Column('operation_metadata', sa.JSON(), nullable=False, default={}),
        
        # Indexes for performance
        sa.Index('idx_idempotent_operations_tenant_type', 'tenant_id', 'operation_type'),
        sa.Index('idx_idempotent_operations_status', 'status'),
        sa.Index('idx_idempotent_operations_expires_at', 'expires_at'),
        sa.Index('idx_idempotent_operations_created_at', 'created_at'),
    )
    
    # === Create update timestamp triggers ===
    # Function to update the updated_at column
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    # Triggers for auto-updating timestamps
    op.execute("""
        CREATE TRIGGER update_saga_executions_updated_at
            BEFORE UPDATE ON saga_executions
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)
    
    op.execute("""
        CREATE TRIGGER update_saga_step_executions_updated_at
            BEFORE UPDATE ON saga_step_executions
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)
    
    op.execute("""
        CREATE TRIGGER update_idempotent_operations_updated_at
            BEFORE UPDATE ON idempotent_operations
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    """Drop workflow orchestration tables."""
    
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS update_idempotent_operations_updated_at ON idempotent_operations")
    op.execute("DROP TRIGGER IF EXISTS update_saga_step_executions_updated_at ON saga_step_executions")
    op.execute("DROP TRIGGER IF EXISTS update_saga_executions_updated_at ON saga_executions")
    
    # Drop function
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")
    
    # Drop tables
    op.drop_table('idempotent_operations')
    op.drop_table('saga_step_executions')
    op.drop_table('saga_executions')
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS operation_status_enum")
    op.execute("DROP TYPE IF EXISTS step_status_enum")
    op.execute("DROP TYPE IF EXISTS saga_status_enum")