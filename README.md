# DotMac Platform Services

[![Python](https://img.shields.io/badge/python-3.12--3.13-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)

**Multi-tenant SaaS Platform Microservices** - A comprehensive backend platform providing core services for building multi-tenant applications. This API-first platform handles authentication, billing, tenancy, and other common SaaS infrastructure needs.

## What is DotMac Platform Services?

A **backend microservices platform** that provides the foundational services needed by any multi-tenant SaaS application:

- **Authentication & Authorization** - JWT auth, RBAC, API keys, OAuth2
- **Multi-Tenancy** - Tenant isolation, onboarding, usage tracking
- **Billing & Subscriptions** - Invoicing, payments, Stripe integration, dunning
- **Licensing** - Feature flags, license management, plan enforcement
- **Communications** - Email, SMS, templates, notifications
- **Analytics & Monitoring** - Usage metrics, audit trails, observability

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  DotMac Platform Services                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │    Auth     │  │   Billing   │  │   Tenant    │             │
│  │  - JWT/RBAC │  │  - Invoices │  │  - Isolation│             │
│  │  - API Keys │  │  - Payments │  │  - Onboard  │             │
│  │  - OAuth2   │  │  - Stripe   │  │  - Usage    │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  Licensing  │  │   Comms     │  │  Analytics  │             │
│  │  - Features │  │  - Email    │  │  - Metrics  │             │
│  │  - Plans    │  │  - SMS      │  │  - Audit    │             │
│  │  - Enforce  │  │  - Templates│  │  - Traces   │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Jobs      │  │  Workflows  │  │  Webhooks   │             │
│  │  - Async    │  │  - Orchestr │  │  - Events   │             │
│  │  - Schedule │  │  - Automate │  │  - Notify   │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Core Services

### Authentication & Authorization
- JWT-based authentication with refresh tokens
- Role-Based Access Control (RBAC) with permissions
- API key management for service-to-service auth
- OAuth2 provider integration
- Multi-factor authentication support

### Multi-Tenancy
- Complete tenant isolation
- Tenant onboarding automation
- Usage tracking and billing integration
- Custom domain verification
- Per-tenant configuration

### Billing & Payments
- Product catalog management
- Subscription lifecycle management
- Invoice generation and PDF export
- Payment processing (Stripe integration)
- Dunning and collections
- Credit notes and refunds

### Licensing & Feature Flags
- Dynamic feature flag management
- License activation and validation
- Plan-based feature enforcement
- Usage-based billing support

### Communications
- Email templates and sending
- SMS notifications
- Push notifications (PWA)
- In-app notifications
- Template management

### Analytics & Observability
- Usage analytics and metrics
- Audit trail logging
- Distributed tracing (OpenTelemetry)
- Real-time dashboards (GraphQL)

## Quick Start

### Prerequisites
- Python 3.12+
- PostgreSQL 15+
- Redis 7+
- Docker (optional)

### Installation

```bash
# Clone the repository
git clone https://github.com/michaelayoade/dotmac-platform-services.git
cd dotmac-platform-services

# Install dependencies
poetry install

# Copy environment file
cp .env.example .env

# Run database migrations
poetry run alembic upgrade head

# Start the server
poetry run uvicorn dotmac.platform.main:app --reload
```

### Docker

```bash
# Build and run with Docker Compose
docker compose up -d

# Or build the image directly
docker build -t dotmac-platform-services .
```

## API Documentation

Once running, access the API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## Configuration

Key environment variables:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/dotmac

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256

# Stripe (optional)
STRIPE_SECRET_KEY=sk_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

See `.env.example` for all configuration options.

## Integration with Other Services

This platform is designed to be consumed by other applications. Integration is done via:

1. **REST API** - Standard HTTP endpoints with JWT auth
2. **API Keys** - For service-to-service communication
3. **Webhooks** - Event notifications to external systems
4. **GraphQL** - For analytics and dashboard queries

## Project Structure

```
src/dotmac/platform/
├── auth/           # Authentication & RBAC
├── tenant/         # Multi-tenancy
├── billing/        # Billing & payments
├── licensing/      # License management
├── communications/ # Email, SMS, notifications
├── analytics/      # Usage analytics
├── audit/          # Audit trails
├── jobs/           # Async job processing
├── workflows/      # Workflow orchestration
├── webhooks/       # Webhook management
├── monitoring/     # Observability
└── ...
```

## Development

```bash
# Run tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src/dotmac

# Lint
poetry run ruff check .

# Type check
poetry run mypy src/
```

## License

MIT License - see [LICENSE](LICENSE) for details.
