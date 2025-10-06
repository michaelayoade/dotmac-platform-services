# DotMac Platform Services
[![Python](https://img.shields.io/badge/python-3.12--3.13-blue.svg)](https://python.org)
[![Coverage](https://img.shields.io/badge/coverage-85%25-green.svg)](.)
[![Tests](https://img.shields.io/badge/tests-6146%20passing-green.svg)](.)

**Complete SaaS platform backend** providing authentication, billing, customer management, communications, and 25+ integrated services for building production-ready applications.

## 🎯 What is DotMac Platform Services?

A **batteries-included backend platform** that eliminates months of infrastructure work. Deploy a complete SaaS backend with authentication, billing, multi-tenancy, communications, file storage, and analytics in minutes instead of months.

### Core Value Proposition

✅ **Skip the Infrastructure**: All essential SaaS services pre-integrated
✅ **Production Ready**: Battle-tested with 85%+ test coverage (6,146 tests)
✅ **Multi-Tenant by Default**: Built-in tenant isolation and management
✅ **Modern Stack**: Python 3.12+, FastAPI, SQLAlchemy 2.0, Pydantic v2
✅ **API-First**: RESTful APIs + GraphQL with auto-generated documentation

## 📦 Complete Feature Set

### 🔐 Authentication & Security
- **JWT Authentication** - RS256/HS256 token management with refresh tokens
- **Role-Based Access Control (RBAC)** - Flexible permissions system
- **Multi-Factor Authentication (MFA)** - TOTP, SMS, Email support
- **Session Management** - Redis-backed sessions with SSO support
- **API Key Management** - Service-to-service authentication
- **OAuth2/OIDC Integration** - Social login providers
- **Platform Admin** - Cross-tenant super admin capabilities

### 💰 Billing & Revenue Management
- **Subscription Management** - Recurring billing with multiple plans
- **Product Catalog** - Flexible product and pricing management
- **Invoice Generation** - Automated invoicing with PDF export
- **Payment Processing** - Stripe integration with webhook handling
- **Usage-Based Billing** - Metered billing and quotas
- **Multi-Currency Support** - International pricing
- **Tax Calculation** - Automated tax computation
- **Bank Accounts & Manual Payments** - Offline payment tracking
- **Credit Notes & Refunds** - Full refund workflow

### 👥 Customer & User Management
- **Customer Relationship Management** - Complete customer lifecycle
- **User Management** - User profiles, roles, and permissions
- **Contact Management** - Centralized contact database
- **Partner Management** - Partner onboarding and commission tracking
- **Tenant Management** - Multi-organization support with isolation

### 📧 Communications
- **Email Service** - Template-based email with SendGrid/SMTP
- **SMS Notifications** - Twilio integration
- **Email Templates** - Jinja2 templating with versioning
- **Bulk Messaging** - Queue-based batch communications
- **Webhook Management** - Generic webhook subscriptions and delivery
- **Event System** - Domain events for decoupled architecture

### 📊 Analytics & Monitoring
- **Business Analytics** - Customer metrics, revenue analytics
- **Event Tracking** - Custom event collection and aggregation
- **OpenTelemetry Integration** - Distributed tracing and metrics
- **Structured Logging** - Correlation IDs and log aggregation
- **Health Checks** - Readiness and liveness probes
- **Performance Monitoring** - Response time and throughput metrics
- **GraphQL Analytics API** - Flexible query interface for dashboards

### 🗄️ Data Management
- **File Storage** - MinIO/S3-compatible object storage
- **Data Import/Export** - CSV, JSON, Excel support
- **Data Transfer** - Bulk data operations with progress tracking
- **Search Functionality** - Elasticsearch/OpenSearch integration
- **Audit Logging** - Complete audit trail for compliance

### ⚙️ Platform Services
- **Feature Flags** - Toggle features by tenant/user
- **Plugin System** - Extensible plugin architecture (WhatsApp, etc.)
- **Admin Settings** - Platform-wide configuration
- **Secrets Management** - HashiCorp Vault/OpenBao integration
- **Service Registry** - Consul-based service discovery
- **Resilience Patterns** - Circuit breakers, retries, rate limiting

## 🚀 Quick Start

### Requirements

- Python 3.12 or 3.13
- PostgreSQL 14+ (or SQLite for development)
- Redis 6+ (for sessions and caching)
- Optional: Vault/OpenBao, MinIO, Elasticsearch

### Installation

```bash
# Clone the repository
git clone https://github.com/michaelayoade/dotmac-platform-services.git
cd dotmac-platform-services

# Install with Poetry
poetry install --with dev

# Set up infrastructure (PostgreSQL, Redis, Vault, MinIO, etc.)
make infra-up

# Run database migrations
poetry run alembic upgrade head

# Seed initial data (optional)
make seed-db

# Start the development server
make dev-backend
```

The API will be available at:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **GraphQL**: http://localhost:8000/api/v1/graphql

### Environment Configuration

Create a `.env` file:

```bash
# Database
DATABASE_URL=postgresql://dotmac_user:password@localhost:5432/dotmac

# Redis
REDIS_URL=redis://localhost:6379/0

# Authentication
JWT_SECRET=your-super-secret-jwt-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Tenant Mode
TENANT_MODE=multi  # or "single" for single-tenant
DEFAULT_TENANT_ID=default

# Optional Services
VAULT__ENABLED=false  # Set to true if using Vault
VAULT_URL=http://localhost:8200
VAULT_TOKEN=root

OTEL_ENABLED=false  # Set to true for observability
OTEL_ENDPOINT=http://localhost:4318
```

## 🏗️ Architecture

### Design Principles

1. **Multi-Tenant First** - Complete tenant isolation at database and API level
2. **Domain-Driven Design** - Business logic organized by domain boundaries
3. **Event-Driven** - Decoupled architecture with domain events
4. **API-First** - RESTful + GraphQL with OpenAPI documentation
5. **Production Ready** - Comprehensive testing, logging, monitoring

### Technology Stack

| Layer | Technology |
|-------|-----------|
| **Language** | Python 3.12+ |
| **Web Framework** | FastAPI with Pydantic v2 |
| **Database** | SQLAlchemy 2.0 + Alembic (PostgreSQL/SQLite) |
| **Caching** | Redis |
| **Task Queue** | Celery with Redis broker |
| **Authentication** | JWT (PyJWT) with RBAC |
| **Secrets** | HashiCorp Vault / OpenBao |
| **File Storage** | MinIO (S3-compatible) |
| **Search** | Elasticsearch / OpenSearch |
| **Observability** | OpenTelemetry (Jaeger/SigNoz) |
| **Testing** | pytest + pytest-asyncio (6,146 tests) |

### Package Structure

```
src/dotmac/platform/
├── auth/                  # Authentication, RBAC, MFA, sessions
├── billing/               # Subscriptions, invoices, payments
│   ├── catalog/          # Product catalog
│   ├── subscriptions/    # Subscription management
│   ├── pricing/          # Pricing engine
│   ├── invoicing/        # Invoice generation
│   ├── payments/         # Payment processing
│   ├── bank_accounts/    # Manual payments
│   └── webhooks/         # Stripe webhooks
├── customer_management/   # CRM functionality
├── user_management/       # User profiles and management
├── communications/        # Email, SMS, templates
├── partner_management/    # Partner onboarding and commissions
├── tenant/               # Multi-tenant organization management
├── analytics/            # Business analytics and metrics
├── file_storage/         # Object storage (MinIO/S3)
├── data_transfer/        # Import/export operations
├── data_import/          # File-based imports
├── search/               # Search functionality
├── webhooks/             # Webhook management
├── contacts/             # Contact database
├── plugins/              # Plugin system
├── feature_flags/        # Feature toggles
├── secrets/              # Vault integration
├── audit/                # Audit logging
├── monitoring/           # Logs, traces, metrics
├── observability/        # OpenTelemetry setup
├── admin/                # Admin settings
└── core/                 # Shared utilities
```

## 📚 API Endpoints

Over **40 API routes** organized by domain:

### Authentication (`/api/v1/auth`)
- `POST /login/cookie` - Login with HTTP-only cookies
- `POST /register` - User registration
- `POST /logout` - Logout
- `GET /me` - Current user profile
- `POST /refresh` - Refresh access token
- `POST /mfa/enable` - Enable MFA
- `GET /api-keys` - List API keys

### Billing (`/api/v1/billing`)
- **Subscriptions**: Create, update, cancel subscriptions
- **Invoices**: Generate, list, download invoices
- **Payments**: Process payments, webhooks
- **Catalog**: Manage products and pricing
- **Bank Accounts**: Manual payment tracking

### Customers (`/api/v1/customers`)
- CRUD operations for customers
- Customer metrics and analytics
- Contact assignment

### Communications (`/api/v1/communications`)
- Send emails and SMS
- Template management
- Bulk message operations
- Delivery tracking

### File Storage (`/api/v1/files/storage`)
- Upload/download files
- File metadata management
- Storage quotas

### Tenants (`/api/v1/tenants`)
- Organization management
- Tenant settings and quotas
- Usage tracking

### Analytics (`/api/v1/analytics`)
- Event tracking
- Custom metrics
- Business KPIs

### GraphQL (`/api/v1/graphql`)
- Flexible analytics queries
- Dashboard data aggregation
- Real-time metrics

[View complete API documentation at `/docs` when running]

## 🧪 Testing

### Test Coverage

- **6,146 automated tests** with 85%+ coverage
- Unit, integration, and end-to-end tests
- Mock-based testing for external services
- Parallel test execution with pytest-xdist

### Running Tests

```bash
# Quick tests (no coverage)
make test-fast

# Full test suite with coverage
make test-unit

# Integration tests (requires infrastructure)
make test-integration

# Specific module
poetry run pytest tests/billing/ -v

# Coverage report
make test-cov  # Opens HTML report
```

### CI/CD

- **GitHub Actions** with Python 3.12 and 3.13 matrix
- **85% baseline coverage** requirement
- **95% diff coverage** for new code
- Bandit security scanning
- Dependency vulnerability audits
- Automated test runs on every PR

## 🔧 Development

### Available Commands

```bash
make install          # Install dependencies
make dev              # Start full stack (infra + backend + frontend)
make dev-backend      # Backend only
make dev-frontend     # Frontend only
make infra-up         # Start infrastructure (PostgreSQL, Redis, etc.)
make infra-down       # Stop infrastructure
make seed-db          # Seed database with test data
make format           # Auto-format code (black, isort, ruff)
make lint             # Run linters
make test-unit        # Run tests with coverage
make clean            # Clean build artifacts
```

### Code Quality Standards

- **PEP 8** compliance enforced
- **Black** code formatting
- **isort** import sorting
- **Ruff** linting (100+ rules)
- **mypy** type checking
- **Bandit** security scanning
- **85% test coverage** minimum

## 🌐 Frontend Integration

Includes a **Next.js 14 frontend** (`frontend/apps/base-app/`) with:

- TypeScript + React 18
- TailwindCSS + shadcn/ui components
- OpenAPI client auto-generation
- Multi-theme support (light/dark)
- Responsive dashboard layouts
- Real-time metrics and charts

Frontend connects to backend via:
- REST API calls with auto-generated TypeScript types
- GraphQL for analytics dashboards
- Server-side rendering with Next.js

## 📖 Documentation

### Available Documentation

- **[DEV_SETUP_GUIDE.md](docs/guides/DEV_SETUP_GUIDE.md)** - Complete development setup
- **[TESTING_GUIDE.md](docs/TESTING_GUIDE.md)** - Testing strategy and patterns
- **[CI_CD_ENVIRONMENT_ALIGNMENT.md](CI_CD_ENVIRONMENT_ALIGNMENT.md)** - CI/CD configuration
- **[API Documentation](http://localhost:8000/docs)** - Interactive OpenAPI docs (when running)
- **[CLAUDE.md](CLAUDE.md)** - AI-assisted development guidelines

### Quick Reference

| Task | Command | Documentation |
|------|---------|---------------|
| Setup dev environment | `make install && make infra-up` | DEV_SETUP_GUIDE.md |
| Run tests | `make test-unit` | TESTING_GUIDE.md |
| Add new module | Follow DDD patterns | Architecture docs |
| Deploy to production | Use Docker compose | Deployment guide |

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:

- Code of conduct
- Development workflow
- Pull request process
- Coding standards
- Testing requirements

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🎯 Use Cases

Perfect for building:

- **SaaS Applications** - Multi-tenant with built-in billing
- **B2B Platforms** - Customer management and partner portals
- **API-as-a-Service** - Authentication and usage tracking included
- **Marketplaces** - Complete transaction and communication flows
- **Internal Tools** - RBAC and audit logging out of the box

## 🚦 Project Status

- ✅ **Production Ready** - Used in live deployments
- ✅ **Actively Maintained** - Regular updates and security patches
- ✅ **Well Tested** - 6,146 tests with 85%+ coverage
- ✅ **Documented** - Comprehensive API and development docs
- ✅ **Modern Stack** - Python 3.12+, FastAPI, Pydantic v2

## 📞 Support

- **Documentation**: [docs/INDEX.md](docs/INDEX.md)
- **Issues**: [GitHub Issues](https://github.com/michaelayoade/dotmac-platform-services/issues)
- **Discussions**: [GitHub Discussions](https://github.com/michaelayoade/dotmac-platform-services/discussions)

---

**Built with** ❤️ **for developers who want to ship products, not infrastructure.**
