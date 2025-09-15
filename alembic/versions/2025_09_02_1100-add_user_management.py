"""Add comprehensive user management tables

Revision ID: add_user_management
Revises: 952b95951dab
Create Date: 2025-09-02 11:00:00.000000

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers
revision = 'add_user_management'
down_revision = 'field_ops_2025_01_16_1200'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create comprehensive user management v2 tables."""
    
    # Create enum types
    op.execute("CREATE TYPE user_type_enum AS ENUM ('customer', 'technician', 'isp_admin', 'isp_support', 'super_admin', 'platform_admin', 'tenant_admin', 'tenant_user', 'platform_support', 'api_user', 'readonly', 'reseller', 'partner')")
    op.execute("CREATE TYPE user_status_enum AS ENUM ('pending', 'active', 'inactive', 'suspended', 'locked', 'expired', 'deleted', 'archived')")
    op.execute("CREATE TYPE session_type_enum AS ENUM ('web', 'mobile', 'api', 'cli', 'system')")
    op.execute("CREATE TYPE auth_provider_enum AS ENUM ('local', 'oauth_google', 'oauth_microsoft', 'saml', 'ldap', 'api_key')")
    
    # === Core Users Table ===
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        
        # Core Identity
        sa.Column('username', sa.String(50), nullable=False, unique=True, index=True, comment='Unique username for login'),
        sa.Column('email', sa.String(255), nullable=False, unique=True, index=True, comment='Primary email address'),
        
        # Personal Information
        sa.Column('first_name', sa.String(100), nullable=False, comment="User's first name"),
        sa.Column('last_name', sa.String(100), nullable=False, comment="User's last name"),
        sa.Column('middle_name', sa.String(100), nullable=True, comment="User's middle name"),
        sa.Column('preferred_name', sa.String(100), nullable=True, comment='Preferred display name'),
        
        # Classification
        sa.Column('user_type', sa.Enum(name='user_type_enum'), nullable=False, index=True, comment='Type of user account'),
        sa.Column('status', sa.Enum(name='user_status_enum'), nullable=False, default='pending', index=True, comment='Current account status'),
        
        # Verification Status
        sa.Column('is_verified', sa.Boolean(), nullable=False, default=False, comment='Email verification status'),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, default=False, comment='Superuser privileges flag'),
        sa.Column('email_verified', sa.Boolean(), nullable=False, default=False, comment='Email verification flag'),
        sa.Column('phone_verified', sa.Boolean(), nullable=False, default=False, comment='Phone verification flag'),
        sa.Column('email_verified_at', sa.DateTime(), nullable=True, comment='Email verification timestamp'),
        sa.Column('phone_verified_at', sa.DateTime(), nullable=True, comment='Phone verification timestamp'),
        
        # Professional Information
        sa.Column('job_title', sa.String(200), nullable=True, comment='Job title'),
        sa.Column('department', sa.String(200), nullable=True, comment='Department'),
        sa.Column('company', sa.String(200), nullable=True, comment='Company name'),
        
        # Contact Information
        sa.Column('phone', sa.String(20), nullable=True, comment='Primary phone number'),
        sa.Column('mobile', sa.String(20), nullable=True, comment='Mobile phone number'),
        
        # Settings
        sa.Column('timezone', sa.String(50), nullable=False, default='UTC', comment='User timezone'),
        sa.Column('language', sa.String(10), nullable=False, default='en', comment='Preferred language'),
        
        # Security Information
        sa.Column('password_changed_at', sa.DateTime(), nullable=True, comment='Last password change timestamp'),
        sa.Column('mfa_enabled', sa.Boolean(), nullable=False, default=False, comment='Multi-factor authentication enabled'),
        sa.Column('mfa_methods', sa.JSON(), nullable=True, comment='Enabled MFA methods'),
        
        # Activity Tracking
        sa.Column('last_login', sa.DateTime(), nullable=True, comment='Last successful login'),
        sa.Column('login_count', sa.Integer(), nullable=False, default=0, comment='Total login count'),
        sa.Column('failed_login_count', sa.Integer(), nullable=False, default=0, comment='Failed login attempts'),
        sa.Column('locked_until', sa.DateTime(), nullable=True, comment='Account locked until timestamp'),
        
        # Profile Information
        sa.Column('avatar_url', sa.String(500), nullable=True, comment='Avatar image URL'),
        
        # Multi-tenant Support
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('customer_tenants.id'), nullable=True, index=True, comment='Tenant association'),
        
        # Platform-specific Data
        sa.Column('platform_metadata', sa.JSON(), nullable=True, comment='Platform-specific metadata'),
        
        # Legal Compliance
        sa.Column('terms_accepted', sa.Boolean(), nullable=False, default=False, comment='Terms of service accepted'),
        sa.Column('privacy_accepted', sa.Boolean(), nullable=False, default=False, comment='Privacy policy accepted'),
        sa.Column('marketing_consent', sa.Boolean(), nullable=False, default=False, comment='Marketing communications consent'),
        sa.Column('terms_accepted_at', sa.DateTime(), nullable=True, comment='Terms acceptance timestamp'),
        sa.Column('privacy_accepted_at', sa.DateTime(), nullable=True, comment='Privacy acceptance timestamp'),
        
        comment='Core user management table with comprehensive features'
    )
    
    # === User Profiles Table ===
    op.create_table('user_profiles_v2',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.text('CURRENT_TIMESTAMP')),
        
        # Foreign Key
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False, unique=True, comment='Reference to user'),
        
        # Personal Details
        sa.Column('title', sa.String(20), nullable=True, comment='Title (Mr., Ms., Dr., etc.)'),
        sa.Column('date_of_birth', sa.DateTime(), nullable=True, comment='Date of birth'),
        sa.Column('gender', sa.String(20), nullable=True, comment='Gender'),
        
        # Additional Contact
        sa.Column('website', sa.String(500), nullable=True, comment='Personal or professional website'),
        sa.Column('linkedin_url', sa.String(500), nullable=True, comment='LinkedIn profile URL'),
        
        # Bio Information
        sa.Column('bio', sa.Text(), nullable=True, comment='User biography or description'),
        sa.Column('skills', sa.JSON(), nullable=True, comment='User skills list'),
        sa.Column('interests', sa.JSON(), nullable=True, comment='User interests list'),
        
        # Emergency Contact
        sa.Column('emergency_contact_name', sa.String(200), nullable=True, comment='Emergency contact name'),
        sa.Column('emergency_contact_phone', sa.String(20), nullable=True, comment='Emergency contact phone'),
        sa.Column('emergency_contact_relationship', sa.String(100), nullable=True, comment='Emergency contact relationship'),
        
        # Custom Fields
        sa.Column('custom_fields', sa.JSON(), nullable=True, comment='Custom profile fields'),
        
        comment='Extended user profile information'
    )
    
    # === User Contact Info Table ===
    op.create_table('user_contact_info_v2',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.text('CURRENT_TIMESTAMP')),
        
        # Foreign Key
        sa.Column('profile_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user_profiles_v2.id'), nullable=False, unique=True, comment='Reference to user profile'),
        
        # Primary Address
        sa.Column('address_line1', sa.String(200), nullable=True, comment='Address line 1'),
        sa.Column('address_line2', sa.String(200), nullable=True, comment='Address line 2'),
        sa.Column('city', sa.String(100), nullable=True, comment='City'),
        sa.Column('state', sa.String(100), nullable=True, comment='State or province'),
        sa.Column('postal_code', sa.String(20), nullable=True, comment='Postal/ZIP code'),
        sa.Column('country', sa.String(100), nullable=True, comment='Country'),
        
        # Billing Address
        sa.Column('billing_address_line1', sa.String(200), nullable=True, comment='Billing address line 1'),
        sa.Column('billing_address_line2', sa.String(200), nullable=True, comment='Billing address line 2'),
        sa.Column('billing_city', sa.String(100), nullable=True, comment='Billing city'),
        sa.Column('billing_state', sa.String(100), nullable=True, comment='Billing state or province'),
        sa.Column('billing_postal_code', sa.String(20), nullable=True, comment='Billing postal/ZIP code'),
        sa.Column('billing_country', sa.String(100), nullable=True, comment='Billing country'),
        
        # Geographic Information
        sa.Column('latitude', sa.String(50), nullable=True, comment='Geographic latitude'),
        sa.Column('longitude', sa.String(50), nullable=True, comment='Geographic longitude'),
        
        comment='User contact and address information'
    )
    
    # === User Preferences Table ===
    op.create_table('user_preferences_v2',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.text('CURRENT_TIMESTAMP')),
        
        # Foreign Key
        sa.Column('profile_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user_profiles_v2.id'), nullable=False, unique=True, comment='Reference to user profile'),
        
        # UI Preferences
        sa.Column('theme', sa.String(20), nullable=False, default='light', comment='UI theme preference'),
        sa.Column('date_format', sa.String(20), nullable=False, default='YYYY-MM-DD', comment='Preferred date format'),
        sa.Column('time_format', sa.String(10), nullable=False, default='24h', comment='Preferred time format'),
        sa.Column('number_format', sa.String(20), nullable=False, default='1,234.56', comment='Preferred number format'),
        
        # Notification Preferences
        sa.Column('email_notifications', sa.Boolean(), nullable=False, default=True, comment='Email notifications enabled'),
        sa.Column('sms_notifications', sa.Boolean(), nullable=False, default=False, comment='SMS notifications enabled'),
        sa.Column('push_notifications', sa.Boolean(), nullable=False, default=True, comment='Push notifications enabled'),
        sa.Column('in_app_notifications', sa.Boolean(), nullable=False, default=True, comment='In-app notifications enabled'),
        
        # Notification Types
        sa.Column('security_alerts', sa.Boolean(), nullable=False, default=True, comment='Security alert notifications'),
        sa.Column('account_updates', sa.Boolean(), nullable=False, default=True, comment='Account update notifications'),
        sa.Column('system_maintenance', sa.Boolean(), nullable=False, default=False, comment='System maintenance notifications'),
        sa.Column('marketing_emails', sa.Boolean(), nullable=False, default=False, comment='Marketing email notifications'),
        
        # Privacy Settings
        sa.Column('profile_visibility', sa.String(20), nullable=False, default='private', comment='Profile visibility setting'),
        sa.Column('activity_visibility', sa.String(20), nullable=False, default='private', comment='Activity visibility setting'),
        
        # Custom Preferences
        sa.Column('dashboard_layout', sa.JSON(), nullable=True, comment='Dashboard layout preferences'),
        sa.Column('custom_preferences', sa.JSON(), nullable=True, comment='Custom user preferences'),
        
        comment='User preferences and settings'
    )
    
    # === User Passwords Table ===
    op.create_table('user_passwords_v2',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.text('CURRENT_TIMESTAMP')),
        
        # Foreign Key
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False, unique=True, comment='Reference to user'),
        
        # Password Information
        sa.Column('password_hash', sa.String(255), nullable=False, comment='Hashed password'),
        sa.Column('salt', sa.String(255), nullable=True, comment='Password salt for additional security'),
        sa.Column('algorithm', sa.String(50), nullable=False, default='bcrypt', comment='Hashing algorithm used'),
        
        # Security Metadata
        sa.Column('password_strength_score', sa.Integer(), nullable=True, comment='Password strength score (0-100)'),
        sa.Column('is_temporary', sa.Boolean(), nullable=False, default=False, comment='Is this a temporary password'),
        sa.Column('must_change', sa.Boolean(), nullable=False, default=False, comment='User must change password on next login'),
        
        # Expiry Management
        sa.Column('expires_at', sa.DateTime(), nullable=True, comment='Password expiry timestamp'),
        
        # Password Reset
        sa.Column('reset_token', sa.String(255), nullable=True, unique=True, comment='Password reset token'),
        sa.Column('reset_token_expires', sa.DateTime(), nullable=True, comment='Reset token expiry'),
        sa.Column('reset_attempts', sa.Integer(), nullable=False, default=0, comment='Number of reset attempts'),
        
        comment='User password management with security features'
    )
    
    # === Password History Table ===
    op.create_table('password_history_v2',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.text('CURRENT_TIMESTAMP')),
        
        # Foreign Keys
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False, comment='Reference to user'),
        sa.Column('password_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user_passwords_v2.id'), nullable=False, comment='Reference to current password record'),
        
        # Password Information
        sa.Column('password_hash', sa.String(255), nullable=False, comment='Historical password hash'),
        sa.Column('algorithm', sa.String(50), nullable=False, comment='Hashing algorithm used'),
        
        # Metadata
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True, comment='User who created this password'),
        sa.Column('change_reason', sa.String(100), nullable=True, comment='Reason for password change'),
        
        comment='Password history for preventing reuse'
    )
    
    # === User Sessions Table ===
    op.create_table('user_sessions_v2',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.text('CURRENT_TIMESTAMP')),
        
        # Foreign Key
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False, index=True, comment='Reference to user'),
        
        # Session Identity
        sa.Column('session_token', sa.String(255), nullable=False, unique=True, index=True, comment='Session token'),
        sa.Column('refresh_token', sa.String(255), nullable=True, unique=True, index=True, comment='Refresh token'),
        
        # Session Type and Provider
        sa.Column('session_type', sa.Enum(name='session_type_enum'), nullable=False, default='web', comment='Type of session'),
        sa.Column('auth_provider', sa.Enum(name='auth_provider_enum'), nullable=False, default='local', comment='Authentication provider used'),
        
        # Client Information
        sa.Column('client_ip', sa.String(45), nullable=True, comment='Client IP address'),  # IPv6 support
        sa.Column('user_agent', sa.Text(), nullable=True, comment='Client user agent string'),
        sa.Column('device_fingerprint', sa.String(255), nullable=True, comment='Device fingerprint hash'),
        
        # Geographic Information
        sa.Column('country', sa.String(100), nullable=True, comment='Login country from IP'),
        sa.Column('city', sa.String(100), nullable=True, comment='Login city from IP'),
        
        # Session Status
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True, index=True, comment='Session active status'),
        sa.Column('expires_at', sa.DateTime(), nullable=False, index=True, comment='Session expiry timestamp'),
        sa.Column('last_activity', sa.DateTime(), nullable=False, default=sa.text('CURRENT_TIMESTAMP'), comment='Last activity timestamp'),
        
        # Security Flags
        sa.Column('is_suspicious', sa.Boolean(), nullable=False, default=False, comment='Marked as suspicious activity'),
        sa.Column('mfa_verified', sa.Boolean(), nullable=False, default=False, comment='MFA verification completed'),
        sa.Column('remember_device', sa.Boolean(), nullable=False, default=False, comment='Device marked as trusted'),
        
        # Termination Information
        sa.Column('terminated_at', sa.DateTime(), nullable=True, comment='Session termination timestamp'),
        sa.Column('termination_reason', sa.String(100), nullable=True, comment='Reason for session termination'),
        
        # Session Metadata
        sa.Column('session_metadata', sa.JSON(), nullable=True, comment='Additional session metadata'),
        
        comment='User session management with comprehensive tracking'
    )
    
    # === Create Indexes ===
    
    # Users table indexes
    op.create_index('idx_users_email_status', 'users', ['email', 'status'])
    op.create_index('idx_users_username_status', 'users', ['username', 'status'])
    op.create_index('idx_users_type_tenant', 'users', ['user_type', 'tenant_id'])
    op.create_index('idx_users_status_active', 'users', ['status', 'is_active'])
    op.create_index('idx_users_created_tenant', 'users', ['created_at', 'tenant_id'])
    op.create_index('idx_users_last_login', 'users', ['last_login'])
    
    # Profile table indexes
    op.create_index('idx_user_profiles_v2_user_id', 'user_profiles_v2', ['user_id'])
    op.create_index('idx_user_contact_info_v2_profile_id', 'user_contact_info_v2', ['profile_id'])
    op.create_index('idx_user_preferences_v2_profile_id', 'user_preferences_v2', ['profile_id'])
    
    # Password table indexes
    op.create_index('idx_user_passwords_v2_user_id', 'user_passwords_v2', ['user_id'])
    op.create_index('idx_user_passwords_v2_reset_token', 'user_passwords_v2', ['reset_token'])
    op.create_index('idx_user_passwords_v2_expires_at', 'user_passwords_v2', ['expires_at'])
    op.create_index('idx_password_history_v2_user_id', 'password_history_v2', ['user_id'])
    op.create_index('idx_password_history_v2_created_at', 'password_history_v2', ['created_at'])
    
    # Session table indexes
    op.create_index('idx_user_sessions_v2_user_active', 'user_sessions_v2', ['user_id', 'is_active'])
    op.create_index('idx_user_sessions_v2_expires_at', 'user_sessions_v2', ['expires_at'])
    op.create_index('idx_user_sessions_v2_last_activity', 'user_sessions_v2', ['last_activity'])
    op.create_index('idx_user_sessions_v2_client_ip', 'user_sessions_v2', ['client_ip'])


def downgrade() -> None:
    """Drop user management v2 tables."""
    
    # Drop tables in reverse order
    op.drop_table('user_sessions_v2')
    op.drop_table('password_history_v2')
    op.drop_table('user_passwords_v2')
    op.drop_table('user_preferences_v2')
    op.drop_table('user_contact_info_v2')
    op.drop_table('user_profiles_v2')
    op.drop_table('users')
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS auth_provider_enum")
    op.execute("DROP TYPE IF EXISTS session_type_enum")
    op.execute("DROP TYPE IF EXISTS user_status_enum")
    op.execute("DROP TYPE IF EXISTS user_type_enum")