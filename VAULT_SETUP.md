# Vault/OpenBao Integration Guide

This guide explains how to set up and use HashiCorp Vault or OpenBao for secure secrets management in the DotMac platform.

## Quick Start

### 1. Start Vault/OpenBao Server

For development, use the provided setup script:

```bash
# Start Vault in dev mode and configure secrets
./scripts/setup_vault.sh

# Or use OpenBao instead
USE_OPENBAO=true ./scripts/setup_vault.sh
```

### 2. Configure Environment

The setup script generates a `.env.vault` file. Copy it to `.env`:

```bash
cp .env.vault .env
```

Or set environment variables manually:

```bash
export VAULT_ADDR="http://localhost:8200"
export VAULT_TOKEN="root-token"
export VAULT_ENABLED=true
```

### 3. Test Connection

Run the test script to verify everything is working:

```bash
python -m dotmac.platform.secrets.test_vault
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VAULT_ADDR` | Vault server URL | `http://localhost:8200` |
| `VAULT_TOKEN` | Authentication token | None |
| `VAULT_NAMESPACE` | Vault namespace (enterprise) | None |
| `VAULT_MOUNT_PATH` | KV secrets engine mount | `secret` |
| `VAULT_KV_VERSION` | KV version (1 or 2) | `2` |
| `VAULT_SKIP_VERIFY` | Skip SSL verification | `false` |
| `VAULT_ROLE_ID` | AppRole role ID | None |
| `VAULT_SECRET_ID` | AppRole secret ID | None |
| `VAULT_KUBERNETES_ROLE` | Kubernetes auth role | None |

### Platform Settings

Configure Vault in `settings.py` or environment:

```python
# settings.py
vault = VaultSettings(
    enabled=True,
    url="http://localhost:8200",
    token="your-token",
    mount_path="secret",
    kv_version=2
)
```

```bash
# Environment variables
VAULT__ENABLED=true
VAULT__URL=http://localhost:8200
VAULT__TOKEN=your-token
VAULT__MOUNT_PATH=secret
VAULT__KV_VERSION=2
```

## Secret Structure

The platform expects secrets to be organized in the following structure:

```
secret/
├── jwt/
│   ├── secret_key
│   ├── algorithm
│   ├── issuer
│   └── audience
├── database/
│   └── postgres/
│       ├── host
│       ├── port
│       ├── database
│       ├── username
│       └── password
├── redis/
│   ├── host
│   ├── port
│   ├── password
│   └── db
├── email/
│   └── sendgrid/
│       ├── api_key
│       ├── from_email
│       └── from_name
├── sms/
│   └── twilio/
│       ├── username (account_sid)
│       ├── password (auth_token)
│       └── from_number
├── storage/
│   └── s3/
│       ├── access_key
│       ├── secret_key
│       ├── endpoint
│       ├── bucket
│       └── region
├── search/
│   └── meilisearch/
│       ├── api_key
│       └── url
├── encryption/
│   ├── fernet_key
│   └── aes_key
├── oauth/
│   ├── google/
│   │   ├── client_id
│   │   └── client_secret
│   └── github/
│       ├── client_id
│       └── client_secret
└── monitoring/
    ├── sentry/
    │   └── dsn
    └── datadog/
        ├── api_key
        └── app_key
```

## Usage in Code

### Basic Usage

```python
from dotmac.platform.secrets import get_vault_client, VaultError

# Get configured client
client = get_vault_client()

# Read a secret
try:
    jwt_config = client.get_secret("jwt")
    secret_key = jwt_config["secret_key"]
except VaultError as e:
    print(f"Failed to get secret: {e}")

# Write a secret
client.set_secret("myapp/config", {
    "api_key": "secret-value",
    "endpoint": "https://api.example.com"
})

# List secrets
secrets = client.list_secrets("myapp")

# Delete a secret
client.delete_secret("myapp/config")
```

### Async Usage

```python
from dotmac.platform.secrets import get_async_vault_client

async def get_secrets():
    client = get_async_vault_client()

    # Get multiple secrets in parallel
    secrets = await client.get_secrets([
        "jwt",
        "database/postgres",
        "redis"
    ])

    return secrets
```

### Automatic Settings Loading

The platform can automatically load secrets at startup:

```python
from dotmac.platform.secrets import load_secrets_from_vault
from dotmac.platform.settings import settings

# Load secrets and update settings
await load_secrets_from_vault(settings)

# Now settings contain values from Vault
print(settings.jwt.secret_key)  # Loaded from Vault
```

### Connection Management

```python
from dotmac.platform.secrets import VaultConnectionManager

# Create a connection manager
manager = VaultConnectionManager()

# Get clients
sync_client = manager.get_sync_client()
async_client = manager.get_async_client()

# Cleanup when done
manager.close()
```

## Authentication Methods

### Token Authentication (Default)

```bash
export VAULT_TOKEN="your-vault-token"
```

### AppRole Authentication

```bash
export VAULT_ROLE_ID="your-role-id"
export VAULT_SECRET_ID="your-secret-id"
```

### Kubernetes Authentication

When running in Kubernetes, the service account token is used automatically:

```bash
export VAULT_KUBERNETES_ROLE="your-k8s-role"
```

## Production Setup

### 1. Install Vault/OpenBao

**Vault:**
```bash
# Download and install
wget https://releases.hashicorp.com/vault/1.15.0/vault_1.15.0_linux_amd64.zip
unzip vault_1.15.0_linux_amd64.zip
sudo mv vault /usr/local/bin/

# Start server (production mode)
vault server -config=/etc/vault/vault.hcl
```

**OpenBao:**
```bash
# Install from GitHub releases
wget https://github.com/openbao/openbao/releases/download/v2.0.0/bao_2.0.0_linux_amd64.tar.gz
tar -xzf bao_2.0.0_linux_amd64.tar.gz
sudo mv bao /usr/local/bin/

# Start server
bao server -config=/etc/openbao/config.hcl
```

### 2. Initialize and Unseal

```bash
# Initialize Vault
vault operator init

# Unseal (repeat 3 times with different keys)
vault operator unseal

# Login
vault login
```

### 3. Configure Auth Methods

**AppRole:**
```bash
# Enable AppRole
vault auth enable approle

# Create role
vault write auth/approle/role/dotmac \
    token_ttl=1h \
    token_max_ttl=4h \
    policies="dotmac-policy"

# Get credentials
vault read auth/approle/role/dotmac/role-id
vault write -f auth/approle/role/dotmac/secret-id
```

**Kubernetes:**
```bash
# Enable Kubernetes auth
vault auth enable kubernetes

# Configure
vault write auth/kubernetes/config \
    kubernetes_host="https://k8s.example.com:6443" \
    kubernetes_ca_cert=@ca.crt \
    token_reviewer_jwt="$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)"

# Create role
vault write auth/kubernetes/role/dotmac \
    bound_service_account_names=dotmac \
    bound_service_account_namespaces=default \
    policies=dotmac-policy \
    ttl=1h
```

### 4. Create Policies

```hcl
# dotmac-policy.hcl
path "secret/data/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

path "secret/metadata/*" {
  capabilities = ["list", "read", "delete"]
}
```

Apply policy:
```bash
vault policy write dotmac-policy dotmac-policy.hcl
```

### 5. Enable Audit Logging

```bash
vault audit enable file file_path=/var/log/vault/audit.log
```

## Monitoring

### Health Check Endpoint

The platform provides a health check for Vault:

```python
from dotmac.platform.secrets import check_vault_health

health = check_vault_health()
print(f"Healthy: {health['healthy']}")
print(f"Sealed: {health['sealed']}")
print(f"Version: {health['version']}")
```

### Metrics

Monitor these key metrics:
- Vault server health
- Authentication failures
- Secret read/write operations
- Response times
- Token expiration

## Security Best Practices

1. **Never commit secrets to version control**
   - Use Vault for all sensitive data
   - Keep `.env` files in `.gitignore`

2. **Use appropriate authentication**
   - Token auth for development
   - AppRole for applications
   - Kubernetes auth for k8s deployments

3. **Implement least privilege**
   - Create specific policies per service
   - Limit access to required paths only

4. **Enable audit logging**
   - Track all Vault operations
   - Monitor for suspicious activity

5. **Rotate credentials regularly**
   - Use dynamic secrets where possible
   - Rotate static secrets periodically

6. **Use TLS in production**
   - Always use HTTPS for Vault communication
   - Verify SSL certificates

7. **Backup Vault data**
   - Regular snapshots of Vault storage
   - Test restore procedures

## Troubleshooting

### Connection Refused

```bash
# Check if Vault is running
curl http://localhost:8200/v1/sys/health

# Check environment variables
echo $VAULT_ADDR
echo $VAULT_TOKEN
```

### Permission Denied

```bash
# Check token capabilities
vault token capabilities secret/jwt

# Verify policy
vault policy read dotmac-policy
```

### Secret Not Found

```bash
# List available secrets
vault kv list secret/

# Check if path exists
vault kv get secret/jwt
```

### SSL Certificate Errors

```bash
# Skip verification (development only!)
export VAULT_SKIP_VERIFY=true

# Or add CA certificate
export VAULT_CACERT=/path/to/ca.crt
```

## Migration from Environment Variables

To migrate existing environment-based secrets to Vault:

1. Export current configuration:
```bash
env | grep -E "(JWT|DATABASE|REDIS)" > current_secrets.env
```

2. Load into Vault:
```bash
# Use the provided script
./scripts/migrate_to_vault.sh current_secrets.env
```

3. Update application configuration:
```bash
# Enable Vault
VAULT_ENABLED=true

# Disable local secrets
FEATURES__SECRETS_VAULT=true
```

4. Test the migration:
```bash
python -m dotmac.platform.secrets.test_vault
```

## Resources

- [Vault Documentation](https://www.vaultproject.io/docs)
- [OpenBao Documentation](https://github.com/openbao/openbao/wiki)
- [Vault Best Practices](https://learn.hashicorp.com/tutorials/vault/production-hardening)
- [KV Secrets Engine](https://www.vaultproject.io/docs/secrets/kv)