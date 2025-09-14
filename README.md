# DotMac Platform Services
[![Python](https://img.shields.io/badge/python-3.12--3.13-blue.svg)](https://python.org)

Unified platform services package providing authentication, secrets management, and observability capabilities for DotMac applications.

## Requirements

- Python 3.12

## Features

### 🔐 Authentication Services
- JWT token management with RS256/HS256 support
- Role-Based Access Control (RBAC) engine
- Multi-factor authentication (TOTP, SMS, Email)
- Session management with Redis backend
- Service-to-service authentication
- API key management
- OAuth2/OIDC provider integration

### 🔒 Secrets Management
- HashiCorp Vault integration
- Field-level encryption/decryption
- Secrets rotation automation
- Multi-tenant secrets isolation
- Environment-based configuration
- Audit logging for secret access

### 📊 Observability
- OpenTelemetry tracing and metrics
- OTLP metrics export (SigNoz)
- Structured logging with correlation IDs
- Performance monitoring
- Business metrics tracking
- Health check endpoints
- Dashboard integration ready

## Installation

Note: Requires Python 3.12–3.13.

```bash
# Basic installation (PyPI)
pip install dotmac-platform-services

# From source (editable)
pip install -e .
```

## Quick Start

### Authentication

```python
from dotmac.platform.auth import AuthService, JWTService, RBACEngine

# JWT token management
jwt_service = JWTService(
    secret_key="your-secret",
    algorithm="HS256"
)

token = jwt_service.create_access_token(
    subject="user123",
    permissions=["read:users", "write:users"]
)

# RBAC permissions
rbac = RBACEngine()
rbac.add_role("admin", ["read:*", "write:*", "delete:*"])
rbac.add_role("user", ["read:own", "write:own"])

has_permission = rbac.check_permission(
    user_roles=["admin"],
    required_permission="write:users"
)
```

#### API Key dependency (FastAPI)

```python
from fastapi import Depends, FastAPI
from dotmac.platform.auth.api_keys import APIKeyService, api_key_dependency

app = FastAPI()

# Attach the service once (e.g., at startup)
app.state.api_key_service = APIKeyService(database_session)

@app.get("/users", dependencies=[Depends(api_key_dependency(["read:users"]))])
async def list_users():
    return {"ok": True}
```

#### Service-to-service request signing (HMAC)

```python
import time
from dotmac.platform.auth.service_auth import (
    ServiceAuthMiddleware,
    sign_request,
)

signing_secret = "super-secret"

app.add_middleware(
    ServiceAuthMiddleware,
    token_manager=service_token_manager,
    service_name="users",
    require_request_signature=True,
    signing_secret=signing_secret,
)

# Client-side signing example
method, path, body, ts = "POST", "/internal/users", b"{}", str(int(time.time()))
sig = sign_request(signing_secret, method, path, body, ts)
headers = {"X-Signature": sig, "X-Timestamp": ts, "X-Service-Token": token}
```

#### CSRF protection (double-submit cookie)

```python
from dotmac.platform.auth.csrf import CSRFMiddleware

app.add_middleware(CSRFMiddleware, secure=True, samesite="lax")
```

### Secrets Management

```python
import asyncio
from dotmac.platform.secrets import SecretsManager, OpenBaoProvider

async def main():
    # OpenBao-backed provider (aka Vault), KV v2 at mount "secret"
    provider = OpenBaoProvider(
        url="http://localhost:8200",
        token="root",
        mount_point="secret",
        kv_version=2,
    )

    # Optionally seed a secret directly via provider
    await provider.set_secret("myapp/config", {"api_key": "s3cr3t"})

    # Manager adds caching/validation and typed accessors
    secrets = SecretsManager(provider=provider)

    data = await secrets.get_custom_secret("myapp/config")
    print(data["api_key"])  # s3cr3t

    await provider.close()

asyncio.run(main())
```

#### Rotation scheduler

```python
from dotmac.platform.secrets.rotation import (
    create_rotation_scheduler,
    create_database_rotation_rule,
)

scheduler = create_rotation_scheduler(secrets_provider)
scheduler.add_rotation_rule(create_database_rotation_rule("db/creds/app"))
# Run one-off rotation
result = asyncio.run(scheduler.rotate_secret("db/creds/app"))
print(result.status)
```

### Observability

```python
from fastapi import FastAPI
from dotmac.platform.observability import ObservabilityManager

# Initialize observability
mgr = ObservabilityManager(
    service_name="my-service",
    otlp_endpoint="http://localhost:4317",
    enable_tracing=True,
    enable_metrics=True,
    enable_logging=True,
)
mgr.initialize()

# Distributed tracing (optional)
from dotmac.platform.observability import get_tracer
tracer = get_tracer(__name__)
with tracer.start_as_current_span("operation"):
    ...

# Custom metrics via registry
registry = mgr.get_metrics_registry()
counter = registry.create_counter("requests_total")
counter.add(1, {"method": "GET", "status": "200"})

# FastAPI middleware
app = FastAPI()
mgr.apply_middleware(app)
```

## Architecture

### Design Principles

1. **DRY (Don't Repeat Yourself)**: Shared utilities in dotmac-core
2. **Logical Grouping**: Related functionality organized together
3. **Production Ready**: Battle-tested components with comprehensive testing
4. **Clear Dependencies**: core → platform-services → business-logic
5. **Extensible**: Plugin architecture for custom providers

### Package Structure

```
dotmac/platform/
├── auth/           # Authentication services
│   ├── jwt.py      # JWT token management
│   ├── rbac.py     # Role-based access control
│   ├── sessions.py # Session management
│   ├── mfa.py      # Multi-factor authentication
│   └── providers/  # OAuth2/OIDC providers
├── secrets/        # Secrets management
│   ├── manager.py  # Secrets manager interface
│   ├── vault.py    # HashiCorp Vault provider
│   ├── encryption.py # Field encryption
│   └── rotation.py # Secrets rotation
└── observability/  # Monitoring and observability
    ├── tracing.py  # OpenTelemetry tracing
    ├── metrics.py  # Metrics registry (OTLP)
    ├── logging.py  # Structured logging
    └── health.py   # Health checks
```

## Public API

- Core (`dotmac.platform`)
  - `get_version()`, `config` (global `PlatformConfig`), `initialize_platform_services(...)`
  - Factories: `create_jwt_service(...)`, `create_secrets_manager(...)`, `create_observability_manager(...)`
  - Registry: `register_service(name, service)`, `get_service(name)`, `get_initialized_services()`

- Auth (`dotmac.platform.auth`)
  - Services: `JWTService`, `create_complete_auth_system(config)`, `add_auth_middleware(app, config=..., service_name=...)`
  - Config: `get_platform_config(config)`
  - Availability helpers: `is_jwt_available()`, `is_rbac_available()`, `is_session_available()`, `is_mfa_available()`, `is_api_keys_available()`, `is_edge_validation_available()`, `is_service_auth_available()`
  - Exceptions (import from `dotmac.platform.auth.exceptions`):
    - Classes: `AuthenticationError`, `AuthorizationError`, `TokenExpired`, `InvalidToken`, etc.
    - Mapping: `EXCEPTION_STATUS_MAP`, helper: `get_http_status(exc)`
  - Notes: Edge validation, service-to-service auth, OAuth, MFA, and API keys are optional and require the corresponding extras installed.

- Secrets (`dotmac.platform.secrets`)
  - Manager: `SecretsManager`
  - Providers: `OpenBaoProvider` (alias: `VaultProvider`), factories: `create_openbao_provider(...)`
  - Config helpers: `SecretsConfig`, `create_default_config(...)`, `create_openbao_config(...)`, `create_production_config(...)`
  - Encryption & rotation (optional): `SymmetricEncryptionService`, `EncryptedField`, `RotationScheduler`, rules and policies

- Observability (`dotmac.platform.observability`)
  - Manager: `ObservabilityManager`, `add_observability_middleware(app)`
  - Logging/tracing/metrics helpers: `get_logger(...)`, `get_tracer(...)`, `initialize_metrics_registry(...)`
  - Health: `check_otel_health()`, `check_metrics_registry_health()`

- Database helpers (`dotmac.platform.database.session`)
  - Sessions: `get_database_session()` (sync), `get_db_session()` (async)
  - Engine: `create_async_database_engine(url, **kwargs)`
  - Health: `check_database_health()`

### Optional Extras

Install optional features via extras:

- `server`: Uvicorn server integrations
- `vault`: OpenBao/Vault client (`hvac`)
- `mfa`: TOTP/QR support (`pyotp`, `qrcode`)
- `sqlite`: Async SQLite driver (`aiosqlite`)
- `postgres`: Async PostgreSQL drivers (`asyncpg`, `psycopg2-binary`)

Examples:

```bash
pip install "dotmac-platform-services[server]"
pip install "dotmac-platform-services[mfa]"
pip install "dotmac-platform-services[postgres]"
```

### Integration with DotMac Core

Platform Services integrates seamlessly with other DotMac packages:

- **dotmac-core**: Shared utilities, exceptions, and base classes
- **dotmac-database**: Database session management and models
- **dotmac-tenant**: Multi-tenant awareness and isolation

## Configuration

### Environment Variables

```bash
# Authentication
DOTMAC_JWT_SECRET_KEY=your-jwt-secret
DOTMAC_JWT_ALGORITHM=HS256
DOTMAC_JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15

# Secrets Management
DOTMAC_VAULT_URL=https://vault.company.com
DOTMAC_VAULT_TOKEN=vault-token
DOTMAC_VAULT_MOUNT_POINT=secret

# Observability
DOTMAC_OTLP_ENDPOINT=http://localhost:4317

DOTMAC_LOG_LEVEL=INFO
```

### Application Factory Integration

```python
from fastapi import FastAPI
from dotmac.platform.auth import add_auth_middleware
from dotmac.platform.observability import add_observability_middleware

app = FastAPI()

# Add platform services
add_auth_middleware(app)
add_observability_middleware(app)
```

## Development

### Setup

```bash
cd dotmac-platform-services
poetry install --with dev
```

## OpenBao via Docker

```yaml
# docker-compose.yml
version: "3.9"
services:
  openbao:
    image: openbao/openbao:latest  # or hashicorp/vault:latest
    container_name: openbao
    ports:
      - "8200:8200"
    environment:
      VAULT_DEV_ROOT_TOKEN_ID: root
      VAULT_DEV_LISTEN_ADDRESS: 0.0.0.0:8200
    cap_add: ["IPC_LOCK"]
```

Then configure the app via environment variables:

```bash
export DOTMAC_VAULT_URL=http://localhost:8200
export DOTMAC_VAULT_TOKEN=root
export DOTMAC_VAULT_MOUNT_POINT=secret
```

For KV v2, ensure the `secret` mount is enabled (dev images usually do this for you):

```bash
docker exec openbao sh -lc "vault secrets enable -version=2 -path=secret kv"
```

### Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov

# Run specific test file
poetry run pytest tests/test_auth.py -v
```

### Code Quality

```bash
# Format code
poetry run black src tests

# Lint code
poetry run ruff check src tests

# Type checking
poetry run mypy src
```
## License

MIT License - see LICENSE file for details.
