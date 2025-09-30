# OpenBao Docker Status Report

**Date**: September 30, 2025  
**Container**: `dotmac-openbao`  
**Image**: `quay.io/openbao/openbao:latest` (v2.4.0)

## Current Status

✅ **Running**: Container is UP and operational  
✅ **Unsealed**: Vault is unsealed and ready  
✅ **Accessible**: API responding on http://localhost:8200  
⚠️ **Health Check**: Shows "unhealthy" (false alarm - IPv6 issue)

## Access Credentials

**Current Root Token**: `s.g1FFtEJwImaxNGjKUNCVPpF3`  
**Unseal Key**: `bTFrRSTsSMZZw0eywJHoOIL9OD5e2aV8Uaomg0aHZec=`

**Important**: These tokens are regenerated every time the container restarts in dev mode.

## Configuration

- **Mode**: Development (NOT for production)
- **Listen Address**: 0.0.0.0:8200
- **Port Mapping**: 8200:8200
- **Volume**: `openbao_data` (freshly recreated)

## Mounted Secrets Engines

- **sys/**: System endpoints (control, policy, debugging)
- **identity/**: Identity store
- **cubbyhole/**: Per-token private secret storage
- **secret/**: KV secrets engine (v2)

## Usage Examples

### Set Environment Variable
```bash
export BAO_ADDR='http://localhost:8200'
export BAO_TOKEN='s.g1FFtEJwImaxNGjKUNCVPpF3'
```

### API Access
```bash
# Health check
curl -s http://localhost:8200/v1/sys/health | jq

# List mounts
curl -s -H "X-Vault-Token: $BAO_TOKEN" \
  http://localhost:8200/v1/sys/mounts | jq

# Write a secret
curl -s -H "X-Vault-Token: $BAO_TOKEN" \
  -d '{"data":{"password":"secret123"}}' \
  http://localhost:8200/v1/secret/data/myapp/config

# Read a secret
curl -s -H "X-Vault-Token: $BAO_TOKEN" \
  http://localhost:8200/v1/secret/data/myapp/config | jq
```

## Known Issues

### 1. Health Check Failing (Cosmetic Only)
**Issue**: Docker health check shows "unhealthy"  
**Cause**: Health check uses IPv6 `[::1]:8200` which fails, but IPv4 `127.0.0.1:8200` works  
**Impact**: None - service is fully functional  
**Fix**: Update health check in docker-compose.yml:
```yaml
healthcheck:
  test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://127.0.0.1:8200/v1/sys/health"]
```

### 2. Token Changes on Restart
**Issue**: Root token changes every container restart  
**Cause**: Dev mode generates random tokens  
**Solution**: Always check logs after restart:
```bash
docker logs dotmac-openbao 2>&1 | grep "Root Token:"
```

### 3. VAULT_DEV_ROOT_TOKEN_ID Ignored
**Issue**: Environment variable doesn't set root token  
**Cause**: OpenBao dev mode always generates random tokens  
**Workaround**: Extract token from logs after each start

## Performance Warnings (Non-Critical)

Logs show gauge collection time warnings:
- `gauge kv_secrets_by_mountpoint` - Took 1m25s (target: 6s)
- `gauge token_by_auth` - Took 1m17s (target: 6s)
- `gauge token_by_policy` - Took 32s (target: 6s)

These are metrics collection delays and don't affect functionality in dev mode.

## Integration with Platform

The platform's secrets service should be configured to use:
- **URL**: `http://localhost:8200`
- **Token**: Check logs or use service discovery
- **Mount Path**: `secret/` (KV v2)

Example platform configuration:
```python
VAULT_ADDR = "http://localhost:8200"
VAULT_TOKEN = "s.g1FFtEJwImaxNGjKUNCVPpF3"  # Update from logs
VAULT_MOUNT_POINT = "secret"
```

## Maintenance Commands

```bash
# Restart container
docker restart dotmac-openbao

# View logs
docker logs dotmac-openbao

# Access shell
docker exec -it dotmac-openbao sh

# Recreate with fresh data
docker-compose down openbao
docker volume rm dotmac-platform-services_openbao_data
docker-compose up -d openbao
```

---

**Status**: ✅ OpenBao is fully operational and ready for development use
