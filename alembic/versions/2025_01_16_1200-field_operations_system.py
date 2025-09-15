"""
Field Operations System Database Migration

Creates all tables and indexes for comprehensive field operations management:
- Technician management with skills and scheduling
- Work order lifecycle with status tracking
- Performance analytics and reporting
- Dispatch optimization and route planning
- Equipment and time tracking

Revision ID: field_ops_2025_01_16_1200
Revises: 2025_01_15_1200_support_system_tables
Create Date: 2025-01-16 12:00:00.000000
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers
revision = 'field_ops_2025_01_16_1200'
down_revision = '2025_01_15_1200_support_system_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create field operations system tables."""
    
    # Create ENUM types
    op.execute("""
        CREATE TYPE technician_status_enum AS ENUM (
            'available', 'on_job', 'break', 'lunch', 'traveling', 
            'sick', 'vacation', 'off_duty', 'emergency'
        )
    """)
    
    op.execute("""
        CREATE TYPE work_order_status_enum AS ENUM (
            'draft', 'scheduled', 'dispatched', 'accepted', 'en_route',
            'on_site', 'in_progress', 'waiting_parts', 'waiting_customer',
            'completed', 'cancelled', 'requires_followup', 'escalated'
        )
    """)
    
    op.execute("""
        CREATE TYPE work_order_priority_enum AS ENUM (
            'low', 'normal', 'high', 'urgent', 'emergency'
        )
    """)
    
    op.execute("""
        CREATE TYPE work_order_type_enum AS ENUM (
            'installation', 'maintenance', 'repair', 'upgrade', 'inspection',
            'disconnect', 'reconnect', 'troubleshooting', 'emergency_repair'
        )
    """)
    
    op.execute("""
        CREATE TYPE skill_level_enum AS ENUM (
            'trainee', 'junior', 'intermediate', 'senior', 'expert', 'specialist'
        )
    """)
    
    op.execute("""
        CREATE TYPE equipment_status_enum AS ENUM (
            'required', 'assigned', 'installed', 'tested', 'returned', 'missing', 'damaged'
        )
    """)
    
    # Create field_technicians table
    op.create_table(
        'field_technicians',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.String(255), nullable=False),
        sa.Column('employee_id', sa.String(100), nullable=False, unique=True),
        sa.Column('user_id', sa.String(255), nullable=True),
        
        # Personal information
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('phone', sa.String(20), nullable=False),
        sa.Column('mobile_phone', sa.String(20), nullable=True),
        
        # Employment details
        sa.Column('hire_date', sa.Date, nullable=False),
        sa.Column('employment_status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('job_title', sa.String(100), nullable=True),
        sa.Column('department', sa.String(100), nullable=True),
        sa.Column('supervisor_id', postgresql.UUID(as_uuid=True), 
                 sa.ForeignKey('field_technicians.id'), nullable=True),
        
        # Skills and certifications
        sa.Column('skill_level', sa.Enum('trainee', 'junior', 'intermediate', 'senior', 'expert', 'specialist', name='skill_level_enum'), 
                 nullable=False, server_default='junior'),
        sa.Column('skills', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('certifications', sa.JSON, nullable=True),
        sa.Column('specializations', postgresql.ARRAY(sa.String), nullable=True),
        
        # Work capacity and scheduling
        sa.Column('max_jobs_per_day', sa.Integer, nullable=False, server_default='8'),
        sa.Column('work_hours_start', sa.Time, nullable=True),
        sa.Column('work_hours_end', sa.Time, nullable=True),
        sa.Column('overtime_approved', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('weekend_availability', sa.Boolean, nullable=False, server_default='false'),
        
        # Current status and location
        sa.Column('current_status', sa.Enum('available', 'on_job', 'break', 'lunch', 'traveling', 'sick', 'vacation', 'off_duty', 'emergency', name='technician_status_enum'), 
                 nullable=False, server_default='off_duty'),
        sa.Column('current_location', sa.JSON, nullable=True),
        sa.Column('last_location_update', sa.DateTime, nullable=True),
        
        # Performance metrics
        sa.Column('jobs_completed_today', sa.Integer, nullable=False, server_default='0'),
        sa.Column('jobs_completed_week', sa.Integer, nullable=False, server_default='0'),
        sa.Column('jobs_completed_month', sa.Integer, nullable=False, server_default='0'),
        sa.Column('average_job_rating', sa.Float, nullable=True),
        sa.Column('completion_rate', sa.Float, nullable=False, server_default='0.0'),
        
        # Equipment and vehicle
        sa.Column('assigned_vehicle', sa.String(100), nullable=True),
        sa.Column('vehicle_location', sa.JSON, nullable=True),
        sa.Column('equipment_assigned', sa.JSON, nullable=True),
        
        # Preferences and settings
        sa.Column('preferred_work_types', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('notification_preferences', sa.JSON, nullable=True),
        sa.Column('language_preference', sa.String(10), nullable=False, server_default='en'),
        
        # Audit fields
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_active', sa.DateTime, nullable=True)
    )
    
    # Create field_work_orders table
    op.create_table(
        'field_work_orders',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.String(255), nullable=False),
        sa.Column('work_order_number', sa.String(100), nullable=False, unique=True),
        
        # Link to existing project management
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('project_phase_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        # Work order details
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('work_order_type', sa.Enum('installation', 'maintenance', 'repair', 'upgrade', 'inspection', 'disconnect', 'reconnect', 'troubleshooting', 'emergency_repair', name='work_order_type_enum'), nullable=False),
        sa.Column('priority', sa.Enum('low', 'normal', 'high', 'urgent', 'emergency', name='work_order_priority_enum'), nullable=False, server_default='normal'),
        
        # Customer and location
        sa.Column('customer_id', sa.String(255), nullable=True),
        sa.Column('customer_name', sa.String(200), nullable=True),
        sa.Column('customer_phone', sa.String(20), nullable=True),
        sa.Column('customer_email', sa.String(255), nullable=True),
        
        # Service location details
        sa.Column('service_address', sa.Text, nullable=False),
        sa.Column('service_coordinates', sa.JSON, nullable=True),
        sa.Column('access_instructions', sa.Text, nullable=True),
        sa.Column('site_contact', sa.String(200), nullable=True),
        sa.Column('site_contact_phone', sa.String(20), nullable=True),
        
        # Scheduling
        sa.Column('requested_date', sa.Date, nullable=True),
        sa.Column('scheduled_date', sa.Date, nullable=True),
        sa.Column('scheduled_time_start', sa.Time, nullable=True),
        sa.Column('scheduled_time_end', sa.Time, nullable=True),
        sa.Column('estimated_duration', sa.Integer, nullable=True),
        
        # Assignment
        sa.Column('technician_id', postgresql.UUID(as_uuid=True), 
                 sa.ForeignKey('field_technicians.id'), nullable=True),
        sa.Column('assigned_at', sa.DateTime, nullable=True),
        sa.Column('assigned_by', sa.String(200), nullable=True),
        sa.Column('backup_technician_id', postgresql.UUID(as_uuid=True), 
                 sa.ForeignKey('field_technicians.id'), nullable=True),
        
        # Status and progress
        sa.Column('status', sa.Enum('draft', 'scheduled', 'dispatched', 'accepted', 'en_route', 'on_site', 'in_progress', 'waiting_parts', 'waiting_customer', 'completed', 'cancelled', 'requires_followup', 'escalated', name='work_order_status_enum'), nullable=False, server_default='draft'),
        sa.Column('progress_percentage', sa.Integer, nullable=False, server_default='0'),
        
        # Work tracking
        sa.Column('actual_start_time', sa.DateTime, nullable=True),
        sa.Column('actual_end_time', sa.DateTime, nullable=True),
        sa.Column('on_site_arrival_time', sa.DateTime, nullable=True),
        sa.Column('customer_signature_time', sa.DateTime, nullable=True),
        
        # Equipment and materials
        sa.Column('required_equipment', sa.JSON, nullable=True),
        sa.Column('required_materials', sa.JSON, nullable=True),
        sa.Column('equipment_used', sa.JSON, nullable=True),
        sa.Column('materials_used', sa.JSON, nullable=True),
        
        # Work details
        sa.Column('work_performed', sa.Text, nullable=True),
        sa.Column('checklist_items', sa.JSON, nullable=True),
        sa.Column('photos', sa.JSON, nullable=True),
        sa.Column('documents', sa.JSON, nullable=True),
        sa.Column('customer_signature', sa.Text, nullable=True),
        
        # Quality and completion
        sa.Column('quality_check_passed', sa.Boolean, nullable=True),
        sa.Column('customer_satisfaction_rating', sa.Integer, nullable=True),
        sa.Column('completion_notes', sa.Text, nullable=True),
        sa.Column('followup_required', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('followup_reason', sa.String(500), nullable=True),
        
        # Cost tracking
        sa.Column('estimated_cost', sa.Numeric(10, 2), nullable=True),
        sa.Column('actual_cost', sa.Numeric(10, 2), nullable=True),
        sa.Column('billable_hours', sa.Float, nullable=True),
        sa.Column('overtime_hours', sa.Float, nullable=True),
        
        # Notifications and communication
        sa.Column('customer_notified', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('last_customer_contact', sa.DateTime, nullable=True),
        sa.Column('automated_updates_sent', sa.JSON, nullable=True),
        
        # SLA and performance
        sa.Column('sla_target_completion', sa.DateTime, nullable=True),
        sa.Column('sla_met', sa.Boolean, nullable=True),
        sa.Column('response_time_minutes', sa.Integer, nullable=True),
        sa.Column('resolution_time_minutes', sa.Integer, nullable=True),
        
        # Sync and mobile
        sa.Column('last_sync', sa.DateTime, nullable=True),
        sa.Column('offline_changes', sa.JSON, nullable=True),
        
        # Audit
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.String(200), nullable=True),
        sa.Column('updated_by', sa.String(200), nullable=True)
    )
    
    # Create work_order_status_history table
    op.create_table(
        'work_order_status_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.String(255), nullable=False),
        sa.Column('work_order_id', postgresql.UUID(as_uuid=True), 
                 sa.ForeignKey('field_work_orders.id'), nullable=False),
        
        # Status change details
        sa.Column('from_status', sa.Enum('draft', 'scheduled', 'dispatched', 'accepted', 'en_route', 'on_site', 'in_progress', 'waiting_parts', 'waiting_customer', 'completed', 'cancelled', 'requires_followup', 'escalated', name='work_order_status_enum'), nullable=True),
        sa.Column('to_status', sa.Enum('draft', 'scheduled', 'dispatched', 'accepted', 'en_route', 'on_site', 'in_progress', 'waiting_parts', 'waiting_customer', 'completed', 'cancelled', 'requires_followup', 'escalated', name='work_order_status_enum'), nullable=False),
        sa.Column('change_reason', sa.String(500), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        
        # Change tracking
        sa.Column('changed_by', sa.String(200), nullable=False),
        sa.Column('changed_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('location', sa.JSON, nullable=True)
    )
    
    # Create work_order_equipment table
    op.create_table(
        'work_order_equipment',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.String(255), nullable=False),
        sa.Column('work_order_id', postgresql.UUID(as_uuid=True), 
                 sa.ForeignKey('field_work_orders.id'), nullable=False),
        
        # Equipment details
        sa.Column('equipment_type', sa.String(100), nullable=False),
        sa.Column('equipment_model', sa.String(100), nullable=True),
        sa.Column('serial_number', sa.String(100), nullable=True),
        sa.Column('barcode', sa.String(100), nullable=True),
        
        # Status tracking
        sa.Column('status', sa.Enum('required', 'assigned', 'installed', 'tested', 'returned', 'missing', 'damaged', name='equipment_status_enum'), nullable=False, server_default='required'),
        sa.Column('quantity_required', sa.Integer, nullable=False, server_default='1'),
        sa.Column('quantity_used', sa.Integer, nullable=False, server_default='0'),
        
        # Installation details
        sa.Column('installation_location', sa.String(200), nullable=True),
        sa.Column('installation_notes', sa.Text, nullable=True),
        sa.Column('test_results', sa.JSON, nullable=True),
        
        # Tracking
        sa.Column('assigned_at', sa.DateTime, nullable=True),
        sa.Column('installed_at', sa.DateTime, nullable=True),
        sa.Column('tested_at', sa.DateTime, nullable=True),
        sa.Column('returned_at', sa.DateTime, nullable=True),
        
        # Audit
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    
    # Create technician_time_entries table
    op.create_table(
        'technician_time_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.String(255), nullable=False),
        sa.Column('technician_id', postgresql.UUID(as_uuid=True), 
                 sa.ForeignKey('field_technicians.id'), nullable=False),
        sa.Column('work_order_id', postgresql.UUID(as_uuid=True), 
                 sa.ForeignKey('field_work_orders.id'), nullable=True),
        
        # Time tracking
        sa.Column('start_time', sa.DateTime, nullable=False),
        sa.Column('end_time', sa.DateTime, nullable=True),
        sa.Column('duration_minutes', sa.Integer, nullable=True),
        
        # Activity details
        sa.Column('activity_type', sa.String(100), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('location_start', sa.JSON, nullable=True),
        sa.Column('location_end', sa.JSON, nullable=True),
        
        # Business tracking
        sa.Column('billable', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('overtime', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('break_time', sa.Boolean, nullable=False, server_default='false'),
        
        # Audit
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    
    # Create work_order_time_entries table
    op.create_table(
        'work_order_time_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.String(255), nullable=False),
        sa.Column('work_order_id', postgresql.UUID(as_uuid=True), 
                 sa.ForeignKey('field_work_orders.id'), nullable=False),
        sa.Column('technician_id', postgresql.UUID(as_uuid=True), 
                 sa.ForeignKey('field_technicians.id'), nullable=False),
        
        # Time details
        sa.Column('start_time', sa.DateTime, nullable=False),
        sa.Column('end_time', sa.DateTime, nullable=True),
        sa.Column('duration_minutes', sa.Integer, nullable=True),
        
        # Work details
        sa.Column('activity_type', sa.String(100), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        
        # Audit
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    
    # Create technician_performance table
    op.create_table(
        'technician_performance',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.String(255), nullable=False),
        sa.Column('technician_id', postgresql.UUID(as_uuid=True), 
                 sa.ForeignKey('field_technicians.id'), nullable=False),
        
        # Performance period
        sa.Column('period_start', sa.Date, nullable=False),
        sa.Column('period_end', sa.Date, nullable=False),
        sa.Column('period_type', sa.String(20), nullable=False),
        
        # Job metrics
        sa.Column('jobs_assigned', sa.Integer, nullable=False, server_default='0'),
        sa.Column('jobs_completed', sa.Integer, nullable=False, server_default='0'),
        sa.Column('jobs_cancelled', sa.Integer, nullable=False, server_default='0'),
        sa.Column('completion_rate', sa.Float, nullable=False, server_default='0.0'),
        
        # Time metrics
        sa.Column('total_work_hours', sa.Float, nullable=False, server_default='0.0'),
        sa.Column('billable_hours', sa.Float, nullable=False, server_default='0.0'),
        sa.Column('overtime_hours', sa.Float, nullable=False, server_default='0.0'),
        sa.Column('average_job_duration', sa.Float, nullable=True),
        
        # Quality metrics
        sa.Column('average_customer_rating', sa.Float, nullable=True),
        sa.Column('quality_checks_passed', sa.Integer, nullable=False, server_default='0'),
        sa.Column('quality_checks_failed', sa.Integer, nullable=False, server_default='0'),
        sa.Column('callbacks', sa.Integer, nullable=False, server_default='0'),
        
        # SLA metrics
        sa.Column('sla_met_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('sla_missed_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('average_response_time', sa.Integer, nullable=True),
        sa.Column('average_resolution_time', sa.Integer, nullable=True),
        
        # Revenue metrics
        sa.Column('revenue_generated', sa.Numeric(12, 2), nullable=True),
        sa.Column('cost_of_materials', sa.Numeric(12, 2), nullable=True),
        sa.Column('profit_margin', sa.Float, nullable=True),
        
        # Additional metrics
        sa.Column('miles_traveled', sa.Float, nullable=True),
        sa.Column('fuel_costs', sa.Numeric(8, 2), nullable=True),
        sa.Column('safety_incidents', sa.Integer, nullable=False, server_default='0'),
        
        # Calculated scores (0-100 scale)
        sa.Column('productivity_score', sa.Integer, nullable=True),
        sa.Column('quality_score', sa.Integer, nullable=True),
        sa.Column('customer_service_score', sa.Integer, nullable=True),
        sa.Column('overall_performance_score', sa.Integer, nullable=True),
        
        # Audit
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    
    # Create dispatch_zones table
    op.create_table(
        'dispatch_zones',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.String(255), nullable=False),
        
        # Zone definition
        sa.Column('zone_name', sa.String(200), nullable=False),
        sa.Column('zone_code', sa.String(20), nullable=False, unique=True),
        sa.Column('description', sa.Text, nullable=True),
        
        # Geographic boundaries
        sa.Column('boundary_coordinates', sa.JSON, nullable=False),
        sa.Column('center_coordinates', sa.JSON, nullable=False),
        sa.Column('coverage_radius', sa.Float, nullable=True),
        
        # Zone properties
        sa.Column('service_types', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('priority_level', sa.Integer, nullable=False, server_default='1'),
        sa.Column('max_concurrent_jobs', sa.Integer, nullable=False, server_default='10'),
        
        # Technician assignment
        sa.Column('primary_technicians', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('backup_technicians', postgresql.ARRAY(sa.String), nullable=True),
        
        # Schedule settings
        sa.Column('operating_hours_start', sa.Time, nullable=True),
        sa.Column('operating_hours_end', sa.Time, nullable=True),
        sa.Column('weekend_coverage', sa.Boolean, nullable=False, server_default='false'),
        
        # Performance tracking
        sa.Column('average_response_time', sa.Integer, nullable=True),
        sa.Column('jobs_completed_month', sa.Integer, nullable=False, server_default='0'),
        sa.Column('customer_satisfaction_avg', sa.Float, nullable=True),
        
        # Status
        sa.Column('active', sa.Boolean, nullable=False, server_default='true'),
        
        # Audit
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    
    # Create indexes for performance
    op.create_index('idx_technicians_tenant_status', 'field_technicians', ['tenant_id', 'current_status'])
    op.create_index('idx_technicians_skills', 'field_technicians', ['tenant_id', 'skill_level'])
    op.create_index('idx_technicians_location_update', 'field_technicians', ['last_location_update'])
    
    op.create_index('idx_workorders_tenant_status', 'field_work_orders', ['tenant_id', 'status'])
    op.create_index('idx_workorders_status_date', 'field_work_orders', ['status', 'scheduled_date'])
    op.create_index('idx_workorders_technician_status', 'field_work_orders', ['technician_id', 'status'])
    op.create_index('idx_workorders_customer_priority', 'field_work_orders', ['customer_id', 'priority'])
    op.create_index('idx_workorders_scheduled_date', 'field_work_orders', ['scheduled_date'])
    op.create_index('idx_workorders_created_at', 'field_work_orders', ['created_at'])
    
    op.create_index('idx_status_history_work_order', 'work_order_status_history', ['work_order_id'])
    op.create_index('idx_status_history_changed_at', 'work_order_status_history', ['changed_at'])
    
    op.create_index('idx_equipment_work_order', 'work_order_equipment', ['work_order_id'])
    op.create_index('idx_equipment_serial_barcode', 'work_order_equipment', ['serial_number', 'barcode'])
    
    op.create_index('idx_time_entries_technician_date', 'technician_time_entries', ['technician_id', 'start_time'])
    op.create_index('idx_time_entries_work_order', 'technician_time_entries', ['work_order_id'])
    
    op.create_index('idx_wo_time_entries_work_order', 'work_order_time_entries', ['work_order_id'])
    op.create_index('idx_wo_time_entries_technician', 'work_order_time_entries', ['technician_id'])
    
    op.create_index('idx_performance_technician_period', 'technician_performance', ['technician_id', 'period_start'])
    op.create_index('idx_performance_overall_score', 'technician_performance', ['overall_performance_score'])
    
    op.create_index('idx_dispatch_zones_tenant', 'dispatch_zones', ['tenant_id'])
    op.create_index('idx_dispatch_zones_active', 'dispatch_zones', ['active'])
    
    # Create triggers for updated_at timestamps
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    # Add triggers to relevant tables
    tables_with_updated_at = [
        'field_technicians',
        'field_work_orders', 
        'work_order_equipment',
        'technician_time_entries',
        'technician_performance',
        'dispatch_zones'
    ]
    
    for table in tables_with_updated_at:
        op.execute(f"""
            CREATE TRIGGER update_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """)
    
    # Create views for common queries
    op.execute("""
        CREATE VIEW technician_availability_view AS
        SELECT 
            t.id,
            t.tenant_id,
            t.full_name,
            t.employee_id,
            t.skill_level,
            t.current_status,
            t.is_available,
            t.current_workload,
            t.jobs_completed_today,
            t.average_job_rating,
            t.current_location,
            COUNT(wo.id) as active_jobs
        FROM field_technicians t
        LEFT JOIN field_work_orders wo ON t.id = wo.technician_id 
            AND wo.status IN ('scheduled', 'dispatched', 'en_route', 'on_site', 'in_progress')
        GROUP BY t.id, t.tenant_id, t.full_name, t.employee_id, t.skill_level, 
                 t.current_status, t.is_available, t.current_workload, 
                 t.jobs_completed_today, t.average_job_rating, t.current_location;
    """)
    
    op.execute("""
        CREATE VIEW work_order_summary_view AS
        SELECT 
            wo.id,
            wo.tenant_id,
            wo.work_order_number,
            wo.title,
            wo.work_order_type,
            wo.status,
            wo.priority,
            wo.customer_name,
            wo.service_address,
            wo.scheduled_date,
            wo.progress_percentage,
            wo.is_overdue,
            t.full_name as technician_name,
            t.phone as technician_phone,
            wo.created_at,
            wo.updated_at,
            CASE 
                WHEN wo.scheduled_date < CURRENT_DATE AND wo.status NOT IN ('completed', 'cancelled') 
                THEN true 
                ELSE false 
            END as is_overdue_calculated
        FROM field_work_orders wo
        LEFT JOIN field_technicians t ON wo.technician_id = t.id;
    """)
    
    # Create function for work order number generation
    op.execute("""
        CREATE OR REPLACE FUNCTION generate_work_order_number(tenant_id_param text)
        RETURNS text AS $$
        DECLARE
            date_prefix text;
            sequence_num integer;
            work_order_number text;
        BEGIN
            date_prefix := to_char(CURRENT_DATE, 'YYYYMMDD');
            
            SELECT COALESCE(
                MAX(
                    CAST(
                        SUBSTRING(work_order_number FROM LENGTH(date_prefix) + 2) 
                        AS INTEGER
                    )
                ), 0
            ) + 1
            INTO sequence_num
            FROM field_work_orders
            WHERE tenant_id = tenant_id_param 
            AND work_order_number LIKE date_prefix || '-%';
            
            work_order_number := date_prefix || '-' || LPAD(sequence_num::text, 4, '0');
            
            RETURN work_order_number;
        END;
        $$ LANGUAGE plpgsql;
    """)


def downgrade() -> None:
    """Remove field operations system tables."""
    
    # Drop views
    op.execute("DROP VIEW IF EXISTS work_order_summary_view")
    op.execute("DROP VIEW IF EXISTS technician_availability_view")
    
    # Drop function
    op.execute("DROP FUNCTION IF EXISTS generate_work_order_number(text)")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")
    
    # Drop indexes (automatically dropped with tables)
    
    # Drop tables in reverse order of creation
    op.drop_table('dispatch_zones')
    op.drop_table('technician_performance')  
    op.drop_table('work_order_time_entries')
    op.drop_table('technician_time_entries')
    op.drop_table('work_order_equipment')
    op.drop_table('work_order_status_history')
    op.drop_table('field_work_orders')
    op.drop_table('field_technicians')
    
    # Drop ENUM types
    op.execute("DROP TYPE IF EXISTS equipment_status_enum")
    op.execute("DROP TYPE IF EXISTS skill_level_enum")
    op.execute("DROP TYPE IF EXISTS work_order_type_enum")
    op.execute("DROP TYPE IF EXISTS work_order_priority_enum")
    op.execute("DROP TYPE IF EXISTS work_order_status_enum")
    op.execute("DROP TYPE IF EXISTS technician_status_enum")