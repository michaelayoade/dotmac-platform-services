-- Minimal create for deployment_templates to satisfy FK in migrations
-- Run with: psql -U dotmac_user -d dotmac -f scripts/create_deployment_templates.sql

CREATE TABLE IF NOT EXISTS deployment_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE,
    description TEXT,
    backend VARCHAR(50),
    template_version VARCHAR(50),
    configuration JSONB,
    cpu_cores NUMERIC,
    memory_gb INTEGER,
    storage_gb INTEGER,
    network_config JSONB,
    security_config JSONB,
    monitoring_config JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add a single placeholder row so future FK inserts can reference a valid template
INSERT INTO deployment_templates (name, description, backend, template_version, is_active)
SELECT 'default_placeholder_template', 'Placeholder created to allow migrations to run', 'kubernetes', '1.0.0', true
WHERE NOT EXISTS (SELECT 1 FROM deployment_templates WHERE name = 'default_placeholder_template');
