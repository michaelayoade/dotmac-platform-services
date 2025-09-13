-- DotMac Platform Services - Database Initialization
-- =====================================================

-- Note: Database creation is handled by Docker environment variables
-- This script runs within the created database

-- Create schemas
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS secrets;
CREATE SCHEMA IF NOT EXISTS tenant;

-- Set search path
SET search_path TO public, auth, secrets, tenant;

-- =====================================================
-- Auth Schema Tables
-- =====================================================

-- Users table
CREATE TABLE IF NOT EXISTS auth.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    is_admin BOOLEAN DEFAULT false,
    tenant_id UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    email_verified BOOLEAN DEFAULT false,
    phone VARCHAR(20),
    phone_verified BOOLEAN DEFAULT false,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- API Keys table
CREATE TABLE IF NOT EXISTS auth.api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    tenant_id UUID,
    scopes TEXT[],
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    last_used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Sessions table
CREATE TABLE IF NOT EXISTS auth.sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_token VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    tenant_id UUID,
    ip_address INET,
    user_agent TEXT,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- MFA Secrets table
CREATE TABLE IF NOT EXISTS auth.mfa_secrets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
    secret VARCHAR(255) NOT NULL,
    backup_codes TEXT[],
    is_enabled BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- OAuth Providers table
CREATE TABLE IF NOT EXISTS auth.oauth_providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,
    provider_user_id VARCHAR(255) NOT NULL,
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(provider, provider_user_id)
);

-- Roles table
CREATE TABLE IF NOT EXISTS auth.roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    permissions TEXT[],
    tenant_id UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User Roles junction table
CREATE TABLE IF NOT EXISTS auth.user_roles (
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    role_id UUID REFERENCES auth.roles(id) ON DELETE CASCADE,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    granted_by UUID REFERENCES auth.users(id),
    PRIMARY KEY (user_id, role_id)
);

-- =====================================================
-- Tenant Schema Tables
-- =====================================================

-- Tenants table
CREATE TABLE IF NOT EXISTS tenant.tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    domain VARCHAR(255) UNIQUE,
    is_active BOOLEAN DEFAULT true,
    tier VARCHAR(50) DEFAULT 'free',
    max_users INTEGER DEFAULT 10,
    max_api_keys INTEGER DEFAULT 5,
    settings JSONB DEFAULT '{}'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tenant Invitations table
CREATE TABLE IF NOT EXISTS tenant.invitations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenant.tenants(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'member',
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    accepted_at TIMESTAMP,
    created_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- Secrets Schema Tables
-- =====================================================

-- Secret Stores table
CREATE TABLE IF NOT EXISTS secrets.stores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    tenant_id UUID,
    provider VARCHAR(50) NOT NULL, -- 'vault', 'env', 'file'
    config JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, name)
);

-- Secret Metadata table (tracks secrets without storing values)
CREATE TABLE IF NOT EXISTS secrets.metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID REFERENCES secrets.stores(id) ON DELETE CASCADE,
    path VARCHAR(500) NOT NULL,
    version INTEGER DEFAULT 1,
    rotated_at TIMESTAMP,
    rotation_interval INTERVAL,
    tags TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(store_id, path)
);

-- Audit Log table
CREATE TABLE IF NOT EXISTS secrets.audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID,
    user_id UUID REFERENCES auth.users(id),
    action VARCHAR(50) NOT NULL, -- 'read', 'write', 'delete', 'rotate'
    secret_path VARCHAR(500),
    ip_address INET,
    success BOOLEAN,
    error_message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- Indexes for Performance
-- =====================================================

-- Auth indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON auth.users(email);
CREATE INDEX IF NOT EXISTS idx_users_tenant ON auth.users(tenant_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_user ON auth.api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_tenant ON auth.api_keys(tenant_id);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON auth.sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON auth.sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_oauth_provider_user ON auth.oauth_providers(provider, provider_user_id);

-- Tenant indexes
CREATE INDEX IF NOT EXISTS idx_tenants_domain ON tenant.tenants(domain);
CREATE INDEX IF NOT EXISTS idx_invitations_token ON tenant.invitations(token);
CREATE INDEX IF NOT EXISTS idx_invitations_tenant ON tenant.invitations(tenant_id);

-- Secrets indexes
CREATE INDEX IF NOT EXISTS idx_stores_tenant ON secrets.stores(tenant_id);
CREATE INDEX IF NOT EXISTS idx_metadata_store ON secrets.metadata(store_id);
CREATE INDEX IF NOT EXISTS idx_audit_tenant ON secrets.audit_log(tenant_id);
CREATE INDEX IF NOT EXISTS idx_audit_user ON secrets.audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_created ON secrets.audit_log(created_at);

-- =====================================================
-- Seed Data for Testing
-- =====================================================

-- Insert default tenant
INSERT INTO tenant.tenants (id, name, domain, tier, max_users, max_api_keys)
VALUES 
    ('11111111-1111-1111-1111-111111111111', 'Test Tenant', 'test.localhost', 'premium', 100, 50),
    ('22222222-2222-2222-2222-222222222222', 'Demo Tenant', 'demo.localhost', 'free', 10, 5)
ON CONFLICT DO NOTHING;

-- Insert default roles
INSERT INTO auth.roles (id, name, description, permissions)
VALUES
    ('33333333-3333-3333-3333-333333333333', 'admin', 'Administrator role', ARRAY['*']),
    ('44444444-4444-4444-4444-444444444444', 'user', 'Regular user role', ARRAY['read:profile', 'write:profile']),
    ('55555555-5555-5555-5555-555555555555', 'viewer', 'Read-only role', ARRAY['read:*'])
ON CONFLICT DO NOTHING;

-- Insert test users (password is 'password123' hashed with bcrypt)
INSERT INTO auth.users (id, email, username, password_hash, is_active, is_admin, tenant_id, email_verified)
VALUES
    ('66666666-6666-6666-6666-666666666666', 'admin@test.local', 'admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY/JF8WqhLxqbXC', true, true, '11111111-1111-1111-1111-111111111111', true),
    ('77777777-7777-7777-7777-777777777777', 'user@test.local', 'testuser', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY/JF8WqhLxqbXC', true, false, '11111111-1111-1111-1111-111111111111', true),
    ('88888888-8888-8888-8888-888888888888', 'demo@test.local', 'demouser', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY/JF8WqhLxqbXC', true, false, '22222222-2222-2222-2222-222222222222', false)
ON CONFLICT DO NOTHING;

-- Link users to roles
INSERT INTO auth.user_roles (user_id, role_id)
VALUES
    ('66666666-6666-6666-6666-666666666666', '33333333-3333-3333-3333-333333333333'), -- admin -> admin role
    ('77777777-7777-7777-7777-777777777777', '44444444-4444-4444-4444-444444444444'), -- testuser -> user role
    ('88888888-8888-8888-8888-888888888888', '55555555-5555-5555-5555-555555555555')  -- demouser -> viewer role
ON CONFLICT DO NOTHING;

-- Insert test API keys
INSERT INTO auth.api_keys (id, key_hash, name, user_id, tenant_id, scopes, is_active)
VALUES
    ('99999999-9999-9999-9999-999999999999', '$2b$12$test_api_key_hash_1', 'Test API Key 1', '66666666-6666-6666-6666-666666666666', '11111111-1111-1111-1111-111111111111', ARRAY['read', 'write'], true),
    ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '$2b$12$test_api_key_hash_2', 'Test API Key 2', '77777777-7777-7777-7777-777777777777', '11111111-1111-1111-1111-111111111111', ARRAY['read'], true)
ON CONFLICT DO NOTHING;

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON auth.users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_api_keys_updated_at BEFORE UPDATE ON auth.api_keys
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tenants_updated_at BEFORE UPDATE ON tenant.tenants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_stores_updated_at BEFORE UPDATE ON secrets.stores
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions
GRANT ALL ON SCHEMA auth TO dotmac;
GRANT ALL ON SCHEMA secrets TO dotmac;
GRANT ALL ON SCHEMA tenant TO dotmac;
GRANT ALL ON ALL TABLES IN SCHEMA auth TO dotmac;
GRANT ALL ON ALL TABLES IN SCHEMA secrets TO dotmac;
GRANT ALL ON ALL TABLES IN SCHEMA tenant TO dotmac;
GRANT ALL ON ALL SEQUENCES IN SCHEMA auth TO dotmac;
GRANT ALL ON ALL SEQUENCES IN SCHEMA secrets TO dotmac;
GRANT ALL ON ALL SEQUENCES IN SCHEMA tenant TO dotmac;