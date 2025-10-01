# Production Vault/OpenBao Configuration
# Secure secrets management for DotMac Platform

# Storage backend configuration
storage "file" {
  path = "/vault/data"
}

# For production, consider using:
# storage "consul" {
#   address = "consul:8500"
#   path    = "vault/"
#   token   = "${CONSUL_TOKEN}"
# }
#
# or for HA setup:
# storage "raft" {
#   path    = "/vault/data"
#   node_id = "node1"
# }

# Listener configuration
listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = 1  # Enable TLS in production

  # For production with TLS:
  # tls_cert_file = "/vault/config/cert.pem"
  # tls_key_file  = "/vault/config/key.pem"
  # tls_min_version = "tls12"

  # Performance tuning
  max_request_size = 33554432  # 32MB
  max_request_duration = "90s"
}

# API address advertise
api_addr = "http://vault:8200"
cluster_addr = "http://vault:8201"

# UI configuration
ui = false  # Set to true if you want the web UI

# Performance tuning
max_lease_ttl = "768h"
default_lease_ttl = "768h"

# Cache configuration
cache_size = 131072  # 128KB

# Disable mlock for container environments
disable_mlock = true

# Telemetry configuration
telemetry {
  prometheus_retention_time = "24h"
  disable_hostname = true

  # Statsd configuration (optional)
  # statsd_address = "statsd:8125"
  # statsite_address = "statsite:8125"
}

# Audit logging (production should enable this)
# audit {
#   file {
#     file_path = "/vault/logs/audit.log"
#     log_raw = false
#     hmac_accessor = true
#     mode = "0600"
#     format = "json"
#   }
# }

# Logging
log_level = "info"
log_format = "json"

# Plugin directory
plugin_directory = "/vault/plugins"

# Seal configuration (for auto-unseal in production)
# seal "awskms" {
#   region     = "us-east-1"
#   kms_key_id = "your-kms-key-id"
# }
#
# or for Azure:
# seal "azurekeyvault" {
#   tenant_id     = "your-tenant-id"
#   vault_name    = "your-vault-name"
#   key_name      = "your-key-name"
# }