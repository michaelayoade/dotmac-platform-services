# DotMac Platform Services - Architecture Overview

> **Last Updated:** 2025-12-23
> **Codebase Size:** 184K+ LOC
> **Architecture Grade:** A- (87/100)

## Executive Summary

DotMac Platform Services is a production-grade multi-tenant SaaS backend platform built on FastAPI and PostgreSQL. It implements a control plane for multi-tenant applications with extensive infrastructure for authentication, billing, tenancy management, and observability.

---

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                FastAPI + Pydantic v2 Application            │
├─────────────────────────────────────────────────────────────┤
│                     MIDDLEWARE STACK                         │
│  [Context] → [Tenant] → [RLS] → [Audit] → [Metrics] → [CORS]│
├─────────────────────────────────────────────────────────────┤
│                      CORE SERVICES                           │
│   Auth  │  Billing  │  Tenant  │  Communications  │  Jobs   │
├─────────────────────────────────────────────────────────────┤
│                       DATA LAYER                             │
│    SQLAlchemy 2.0  │  PostgreSQL  │  Alembic Migrations     │
├─────────────────────────────────────────────────────────────┤
│                     INFRASTRUCTURE                           │
│   Redis  │  Celery  │  MinIO  │  Vault  │  OpenTelemetry    │
└─────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
src/dotmac/platform/
├── auth/              # Authentication & RBAC (28 files)
├── billing/           # Billing system (53 files, 10+ submodules)
├── tenant/            # Multi-tenancy (21 files)
├── partner_management/ # Partner program + portal APIs (15 files)
├── user_management/   # User/team management (7 files)
├── core/              # Shared infrastructure (22 files)
├── api/               # API gateway & middleware (6 files)
├── communications/    # Email, SMS, notifications (15 files)
├── notifications/     # Notification channels/workflows (16 files)
├── analytics/         # Usage metrics & observability (11 files)
├── jobs/              # Async job processing (12 files)
├── workflows/         # Workflow orchestration (13 files)
├── webhooks/          # Event notifications (5 files)
├── audit/             # Audit trails (6 files)
├── platform_products/ # Global product catalog (7 files)
├── deployment/        # Infrastructure orchestration
├── monitoring/        # Health checks & metrics (18 files)
├── secrets/           # Vault integration (11 files)
├── feature_flags/     # Feature management (6 files)
├── data_import/       # Import pipelines (6 files)
├── data_transfer/     # Export pipelines (11 files)
├── resilience/        # Circuit breakers/service mesh (5 files)
└── [additional modules...]
```

**Key Statistics:**
- **Total Python Files:** ~450+
- **Major Modules:** 40+
- **API Endpoints:** 200+
- **Test Coverage:** 9,670+ tests

---

## Core Design Patterns

### 1. Service Layer Architecture

Three-tier pattern throughout the codebase:

```
Router → Service → Repository → Database
  ↓         ↓          ↓
FastAPI  Business   SQLAlchemy
        Logic       ORM
```

### 2. Domain-Driven Design (DDD)

**Aggregate Roots** (`src/dotmac/platform/core/aggregate_root.py`):
- `Invoice`, `Subscription`, `Payment` aggregates
- Encapsulate business logic and invariants
- Raise domain events for state changes

**Domain Events** (`src/dotmac/platform/core/events.py`):
```python
InvoicePaymentReceivedEvent
SubscriptionRenewedEvent
PaymentFailedEvent
```

**Value Objects:**
- `Money` - Currency-aware amounts
- `EmailAddress`, `PhoneNumber` - Validated types

### 3. Repository Pattern

Found in `billing/domain/repositories.py`:
```python
class InvoiceRepository(BaseRepository):
    async def find_by_id(id: str) -> Invoice
    async def find_by_tenant(tenant_id: str) -> list[Invoice]
    async def save(invoice: Invoice) -> None
    async def delete(id: str) -> None
```

### 4. Dependency Injection

FastAPI's `Depends()` used throughout:
```python
async def get_service(db: AsyncSession = Depends(get_async_session)):
    return BillingService(db)

@router.post("/invoices")
async def create_invoice(
    data: InvoiceCreate,
    service: BillingService = Depends(get_service),
    current_user: UserInfo = Depends(get_current_user),
):
    ...
```

---

## Data Layer

### Database Stack

| Component | Technology |
|-----------|------------|
| ORM | SQLAlchemy 2.0 (async) |
| Database | PostgreSQL 15+ |
| Migrations | Alembic |
| Driver | asyncpg |

### Key Models

| Domain | Models |
|--------|--------|
| Users | `User`, `Team`, `TeamMember` |
| Tenants | `Tenant` |
| Auth | `Permission`, `Role`, `APIKey` |
| Billing | `Invoice`, `Payment`, `Subscription`, `LineItem` |
| Products | `PlatformProduct` |
| Audit | `AuditLog` |

### Base Classes with Mixins

```python
class Base(DeclarativeBase):
    pass

class TimestampMixin:
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]

class SoftDeleteMixin:
    deleted_at: Mapped[datetime | None]
    is_deleted: Mapped[bool]

class TenantMixin:
    tenant_id: Mapped[str]
```

---

## Domain Modules

### Authentication (`auth/`)

| Component | Purpose |
|-----------|---------|
| `router.py` | Login, register, token refresh |
| `core.py` | JWT service, password hashing |
| `rbac_router.py` | Role/permission management |
| `mfa_service.py` | Multi-factor authentication |
| `api_keys_router.py` | API key management |

**Features:**
- JWT + refresh token pattern
- OAuth2 provider support (Google, GitHub, Microsoft)
- RBAC with hierarchical permissions
- TOTP/QR code MFA
- Rate limiting on auth endpoints

### Billing (`billing/`) - Most Complex Module

```
billing/
├── domain/
│   ├── aggregates.py     # Invoice, Subscription aggregates
│   ├── repositories.py   # Data access abstractions
│   ├── event_handlers.py # Domain event handlers
│   └── mappers.py        # DTO ↔ Domain object mapping
├── commands/
│   ├── handlers.py       # Command handling
│   ├── invoice_commands.py
│   ├── payment_commands.py
│   └── subscription_commands.py
├── catalog/              # Product catalog
├── addons/               # Add-on billing
├── dunning/              # Collections & dunning
├── credit_notes/         # Refund & credit handling
├── bank_accounts/        # Payment methods
├── money_models.py       # Multi-currency support
└── router.py             # REST endpoints
```

**Key Features:**
- Event-driven architecture
- Multi-currency support with Money value object
- Stripe integration
- Dunning/collections automation
- PDF invoice generation

### Multi-Tenancy (`tenant/`)

**Isolation Mechanisms:**
1. **Database Level:** Row-Level Security (RLS) policies
2. **Application Level:** Tenant ID in request context
3. **Query Filtering:** Every query filters by tenant_id
4. **Middleware:** `TenantMiddleware` extracts X-Tenant-ID header

**Deployment Modes:**
- **Multi-tenant:** One database, multiple tenants (RLS)
- **Single-tenant:** Dedicated database per tenant
- **Hybrid:** Configurable per tenant

### Partner Management (`partner_management/`)

**Capabilities:**
- Partner lifecycle management (tiers, commission models)
- Referral tracking, commissions, payouts
- Self-service portal endpoints under `/api/v1/partners/portal/*`

### Observability (`analytics/`, `monitoring/`)

**Metrics Collection:**
```python
# Prometheus metrics
invoice_count = Counter("invoices_total", "Total invoices")
payment_amount = Histogram("payment_amount_usd", "Payment amounts")
processing_time = Summary("invoice_processing_seconds")
```

**Tracing:**
- OpenTelemetry integration
- Automatic FastAPI instrumentation
- Celery task tracing
- SQLAlchemy query tracing

**Logging:**
- Structured logging with structlog
- JSON format for parsing
- Correlation IDs for request tracing

---

## Configuration Management

### Settings System (`settings.py`)

Framework: Pydantic Settings v2

```python
class Settings(BaseSettings):
    environment: Environment  # development, staging, production
    app_version: str

    database: DatabaseSettings
    redis: RedisSettings
    storage: StorageSettings
    observability: ObservabilitySettings
    secrets: SecretsSettings
    billing: BillingSettings
    cors: CORSSettings
    celery: CelerySettings
```

### Environment Variables

| Variable | Purpose |
|----------|---------|
| `ENVIRONMENT` | Deployment environment |
| `DATABASE__HOST` | PostgreSQL host |
| `REDIS__HOST` | Redis host |
| `STORAGE__ENDPOINT` | MinIO endpoint |
| `AUTH__JWT_SECRET_KEY` | JWT secret |
| `VAULT__URL` | Vault/OpenBao URL |

---

## Infrastructure Stack

### Core Services

| Service | Purpose | Technology |
|---------|---------|------------|
| Database | Primary data store | PostgreSQL 15 |
| Cache/Broker | Sessions, Celery | Redis 7 |
| Object Storage | Files, uploads | MinIO (S3-compatible) |
| Secrets | Credential management | HashiCorp Vault/OpenBao |
| Tracing | Distributed tracing | Jaeger |
| Metrics | Monitoring | Prometheus + Grafana |
| Alerts | Alert management | Alertmanager |

### Docker Compose Profiles

```bash
# Core services only
docker compose up

# With monitoring stack
docker compose --profile monitoring up
```

---

## Testing Architecture

### Test Structure

```
tests/
├── conftest.py          # Global fixtures (2250 lines)
├── billing/             # Feature-specific tests
├── auth/                # 40+ feature directories
├── integration/         # Cross-module tests
├── e2e/                 # End-to-end workflows
└── helpers/
    ├── router_base.py   # Router test base classes
    ├── cleanup_registry.py
    └── fixture_factories.py
```

### Test Categories

| Category | Marker | Speed | Dependencies |
|----------|--------|-------|--------------|
| Unit | `@pytest.mark.unit` | <0.1s | None |
| Integration | `@pytest.mark.integration` | ~1s | DB, Redis |
| E2E | `@pytest.mark.e2e` | ~5s | Full stack |

### Test Statistics
- **Total Tests:** 9,670+
- **Pass Rate:** 90%+
- **Execution Time:** ~15-20 minutes (full suite)

---

## Key Dependencies

### Core Framework
- FastAPI 0.110+
- Pydantic 2.5+
- SQLAlchemy 2.0+
- Uvicorn 0.25+

### Database
- asyncpg 0.30+
- Alembic 1.13+

### Authentication
- PyJWT 2.8+
- Authlib 1.6+
- passlib + bcrypt

### Observability
- OpenTelemetry 1.21+
- Prometheus Client 0.23+
- structlog 23.0+

### Async & Jobs
- Celery 5.3+
- Redis 5.0+

---

## Architectural Strengths

| Area | Assessment |
|------|------------|
| Separation of Concerns | Router → Service → Repository pattern |
| Security | JWT + RBAC + RLS + Vault integration |
| Observability | Full OpenTelemetry + Prometheus stack |
| Testing | 9,670+ tests with 90%+ pass rate |
| Type Safety | Pydantic v2 + SQLAlchemy type hints + MyPy |
| Multi-tenancy | Row-Level Security with middleware isolation |

---

## Areas for Improvement

| Issue | Recommendation |
|-------|----------------|
| Billing Complexity | Document decision rationale (ADRs) |
| JSON Metadata Fields | Consider normalization for critical fields |
| Test Execution Time | Parallel execution, test categorization |
| Multi-Service Dependencies | Document fallback strategies |

---

## Industry Standards Comparison

| Aspect | Industry Standard | DotMac | Grade |
|--------|-------------------|--------|-------|
| API Framework | FastAPI/Django | FastAPI | A |
| ORM | SQLAlchemy 2.0 | Modern async | A |
| Testing | >80% coverage | 90%+ | A |
| Type Safety | Type hints | Comprehensive | A |
| Security | OAuth2, JWT, RBAC | Complete | A |
| Observability | OpenTelemetry | Full stack | A |
| Multi-tenancy | RLS | Implemented | A |

**Overall Grade: A-** (87/100)

---

## Related Documentation

- [Client Connectivity](CLIENT_CONNECTIVITY.md) - How clients connect to the service
- [Infrastructure Reference](INFRASTRUCTURE.md) - Shared infrastructure stack
- [Backend Production Guide](../BACKEND_PRODUCTION_GUIDE.md) - Deployment guide
- [Testing Guide](../../tests/TESTING_GUIDE.md) - Test patterns and coverage
