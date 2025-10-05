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

The full quick start with runnable snippets now lives in the documentation site: see
[`docs/quick_start.md`](docs/quick_start.md).

- Authentication entry point: [`dotmac.platform.auth`](src/dotmac/platform/auth/)
- Secrets entry point: [`dotmac.platform.secrets`](src/dotmac/platform/secrets/)
- Observability entry point: [`dotmac.platform.observability`](src/dotmac/platform/observability/)

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

---

## 📚 Documentation

**Comprehensive Documentation Index**: See [`docs/INDEX.md`](docs/INDEX.md)

### Quick Links
- **Setup Guide**: [`docs/guides/DEV_SETUP_GUIDE.md`](docs/guides/DEV_SETUP_GUIDE.md)
- **Testing Guide**: [`docs/guides/QUICK_START_NEW_TESTS.md`](docs/guides/QUICK_START_NEW_TESTS.md)
- **Architecture**: [`docs/architecture/`](docs/architecture/)
- **Coverage Reports**: [`docs/coverage-reports/`](docs/coverage-reports/)
- **Contributing**: [`CONTRIBUTING.md`](CONTRIBUTING.md)

### Recent Achievements
- ✅ **90%+ Test Coverage** across all critical modules
- ✅ **CI/CD Coverage Threshold**: Increased to 90% (from 80%)
- ✅ **Documentation Organized**: 225+ files structured in clear categories
- ✅ **Clean Codebase**: Root directory streamlined to essentials only
