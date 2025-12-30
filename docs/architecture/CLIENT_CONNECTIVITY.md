# Client Connectivity Guide

> **Last Updated:** 2025-12-23

This document describes how clients connect to DotMac Platform Services, including authentication methods, request flow, headers, and error handling.

---

## Connection Entry Points

| Protocol | Path | Purpose | Auth Required |
|----------|------|---------|---------------|
| **REST API** | `/api/v1/*` | Primary client interface | Yes |
| **Public Onboarding** | `/api/v1/tenants/onboarding/public` | Tenant signup entry point | No |
| **WebSocket** | `/realtime/ws` | Real-time updates | Yes |
| **Health** | `/health/*` | Liveness/readiness probes | No |
| **Metrics** | `/metrics/` | Prometheus scraping | No |
| **Docs** | `/docs`, `/redoc` | OpenAPI documentation | No (dev/staging only) |

---

## Authentication Methods

### 1. JWT Bearer Token (Primary)

The primary authentication method for web and mobile clients.

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

| Property | Value |
|----------|-------|
| Algorithm | HS256 / RS256 |
| Access Token TTL | 15 minutes |
| Refresh Token TTL | 7 days |
| Revocation | Redis JTI blacklist |

**Token Claims:**
```json
{
  "sub": "user_id",
  "type": "access",
  "exp": 1703257845,
  "iat": 1703256945,
  "jti": "unique_token_id",
  "tenant_id": "tenant_uuid",
  "scopes": ["billing:read", "billing:write"]
}
```

**Endpoints:**
- `POST /api/v1/auth/login` - Obtain tokens
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Revoke tokens
- `POST /api/v1/auth/verify-email/confirm` - Confirm email verification (public)
- `POST /api/v1/auth/verify-email/resend` - Resend verification email (public)

### 2. API Keys (Service-to-Service)

For service integrations and automated systems.

```http
X-API-Key: sk_live_abc123def456...
```

| Property | Description |
|----------|-------------|
| Format | High-entropy random tokens |
| Storage | SHA-256 hashed in Redis |
| Features | Scopes, expiration, tenant binding |

**Endpoints:**
- `POST /api/v1/auth/api-keys` - Create API key
- `GET /api/v1/auth/api-keys` - List API keys
- `DELETE /api/v1/auth/api-keys/{id}` - Revoke API key

### 3. HttpOnly Cookies (Browser)

For browser-based applications with enhanced XSS protection.

| Cookie | Properties |
|--------|------------|
| `access_token` | HttpOnly, Secure, SameSite=Strict |
| `refresh_token` | HttpOnly, Secure, SameSite=Strict |

### 4. OAuth2 (Social Login)

For authentication via third-party providers.

| Provider | Authorize Endpoint | Callback Endpoint |
|----------|-------------------|-------------------|
| Google | `/api/v1/auth/oauth/google/authorize` | `/api/v1/auth/oauth/google/callback` |
| GitHub | `/api/v1/auth/oauth/github/authorize` | `/api/v1/auth/oauth/github/callback` |
| Microsoft | `/api/v1/auth/oauth/microsoft/authorize` | `/api/v1/auth/oauth/microsoft/callback` |

---

## Required Headers

### Authentication Headers

| Header | Required For | Example |
|--------|--------------|---------|
| `Authorization` | Authenticated endpoints | `Bearer eyJhbG...` |
| `X-Tenant-ID` | Multi-tenant requests | `550e8400-e29b-41d4-a716-446655440000` |
| `X-API-Key` | Service auth (alternative to JWT) | `sk_live_abc123...` |

Public onboarding and verification endpoints do not require `X-Tenant-ID`; tenant context is forced to `public`.

### Optional Headers

| Header | Purpose | Example |
|--------|---------|---------|
| `X-Correlation-ID` | Distributed tracing | `corr_abc123` |
| `X-Request-ID` | Request tracking | `req_xyz789` |
| `traceparent` | OpenTelemetry W3C format | W3C trace context |
| `X-Target-Tenant-ID` | Platform admin impersonation | UUID |
| `X-Active-Tenant-Id` | Partner multi-tenant switching | UUID |

### Response Headers

| Header | Source | Contains |
|--------|--------|----------|
| `X-Request-ID` | RequestContextMiddleware | Generated/echoed request ID |
| `X-Correlation-ID` | RequestContextMiddleware | Correlation ID for tracing |
| `X-Trace-ID` | RequestContextMiddleware | OpenTelemetry trace ID |
| `X-Gateway-Request-ID` | GatewayMiddleware | Gateway request identifier |
| `X-Gateway-Time-Ms` | GatewayMiddleware | Request duration in milliseconds |

---

## Request Lifecycle

### Middleware Chain

Requests pass through the following middleware stack (in order):

```
Client Request
      ↓
┌─────────────────────────────────────────────┐
│ 1. GZipMiddleware                           │
│    Compresses responses > 1KB               │
├─────────────────────────────────────────────┤
│ 2. TrustedHostMiddleware                    │
│    Validates Host header                    │
├─────────────────────────────────────────────┤
│ 3. RequestContextMiddleware                 │
│    Generates correlation IDs                │
│    Sets: request_id, correlation_id,        │
│          trace_id, user_id, tenant_id       │
├─────────────────────────────────────────────┤
│ 4. ErrorTrackingMiddleware                  │
│    Counts HTTP errors (Prometheus)          │
├─────────────────────────────────────────────┤
│ 5. RequestMetricsMiddleware                 │
│    Records request duration                 │
├─────────────────────────────────────────────┤
│ 6. TenantMiddleware                         │
│    Resolves X-Tenant-ID header              │
│    Exempts: /health*, /docs, /api/v1/auth/*, │
│             /api/v1/tenants/onboarding/public │
├─────────────────────────────────────────────┤
│ 7. RLSMiddleware                            │
│    Enforces Row-Level Security              │
├─────────────────────────────────────────────┤
│ 8. SingleTenantMiddleware (if configured)   │
│    Overwrites tenant_id with config value   │
├─────────────────────────────────────────────┤
│ 9. AuditContextMiddleware                   │
│    Captures user info for audit trails      │
├─────────────────────────────────────────────┤
│ 10. AppBoundaryMiddleware                   │
│     Enforces platform vs tenant routes      │
├─────────────────────────────────────────────┤
│ 11. CORSMiddleware                          │
│     Adds CORS headers to response           │
└─────────────────────────────────────────────┘
      ↓
Route Handler (with dependency injection)
      ↓
Response + Headers
```

### Route Boundaries

| Path Pattern | Access | Requirement |
|--------------|--------|-------------|
| `/api/platform/*` | Platform admin only | `platform:*` scope |
| `/api/tenant/*` | Tenant context required | Valid X-Tenant-ID |
| `/api/v1/*` | Both platform and tenant | Scope-based filtering |
| `/api/v1/partners/portal/*` | Partner portal | Partner association, optional X-Active-Tenant-Id |
| `/api/v1/tenants/onboarding/public` | Public | No authentication |
| `/health`, `/docs` | Public | No authentication |

---

## API Route Organization

### Route Domains (84 routers)

| Domain | Prefix | Routers |
|--------|--------|---------|
| Authentication | `/api/v1/auth/*` | 6 |
| Billing | `/api/v1/billing/*` | 12 |
| Tenants | `/api/v1/tenants/*` | 4 |
| Tenant Portal | `/api/v1/tenants/portal/*` | 1 |
| Users/Teams | `/api/v1/users`, `/api/v1/teams` | 2 |
| Partners | `/api/v1/partners/*` | 4 |
| Partner Portal | `/api/v1/partners/portal/*` | 1 |
| Monitoring | `/api/v1/monitoring/*` | 4 |
| Analytics | `/api/v1/analytics/*` | 2 |
| Workflows/Jobs | `/api/v1/workflows`, `/api/v1/jobs` | 3 |
| Files | `/api/v1/files/*` | 2 |
| Webhooks | `/api/v1/webhooks/*` | 1 |
| Secrets | `/api/v1/secrets/*` | 1 |
| Audit | `/api/v1/audit/*` | 2 |

### Versioning Strategy

- **Current Version:** v1
- **Path Format:** `/api/v1/{service}/{resource}/{action}`
- **Strategy:** Version embedded in path (not header)

---

## Rate Limiting

### Configuration

| Endpoint Type | Limit |
|---------------|-------|
| Authentication endpoints | 10/minute |
| Public endpoints | 100/minute |
| Authenticated endpoints | 1000/minute |

### Implementation

- **Backend:** SlowAPI with Redis storage
- **Key Function:** IP address
- **Tenant Isolation:** Per-tenant limits in multi-tenant mode

### Rate Limit Response

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 60
Content-Type: application/json

{
    "detail": "100 per 1 minute"
}
```

---

## CORS Configuration

### Default Settings

```python
origins: [
    "http://localhost:3000",    # Frontend dev
    "http://localhost:3001",    # Admin dev
    "http://localhost:3000",    # Partner portal
    "http://localhost:8000",    # API dev
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000"
]
credentials: True
methods: ["*"]
headers: ["*"]
max_age: 3600  # 1 hour preflight cache
```

### CORS Headers

```http
Access-Control-Allow-Origin: <origin>
Access-Control-Allow-Credentials: true
Access-Control-Allow-Methods: *
Access-Control-Allow-Headers: *
Access-Control-Max-Age: 3600
```

---

## Error Responses

### Standard Error Format

All errors return a consistent JSON structure:

```json
{
    "error": "ERROR_CODE",
    "message": "Human-readable message",
    "status_code": 400,
    "timestamp": "2024-12-22T10:30:45.123Z",
    "correlation_id": "corr_abc123",
    "category": "validation",
    "severity": "error",
    "retryable": false,
    "recovery_hint": "Suggested action to resolve",
    "details": {}
}
```

### Error Categories

| Category | Description |
|----------|-------------|
| `validation` | Request validation errors |
| `authentication` | Token/credential errors |
| `authorization` | Permission/scope errors |
| `rate_limit` | Rate limit exceeded |
| `service_error` | Internal service errors |

### HTTP Status Code Mapping

| Status | Error Type | DotMac Exception |
|--------|------------|------------------|
| 400 | Bad Request | `ValidationError`, `BadRequest` |
| 401 | Unauthorized | `TokenError`, `InvalidToken`, `TokenExpired` |
| 403 | Forbidden | `InsufficientScope`, `InsufficientRole`, `TenantMismatch` |
| 404 | Not Found | `NotFound` |
| 422 | Unprocessable Entity | Pydantic validation errors |
| 429 | Too Many Requests | `RateLimitError` |
| 500 | Internal Server Error | `DotMacError`, unhandled exceptions |
| 503 | Service Unavailable | Circuit breaker open |
| 504 | Gateway Timeout | Operation timeout |

### Example Error Responses

**Authentication Error:**
```json
{
    "error": "INVALID_TOKEN",
    "message": "Invalid authentication token",
    "status_code": 401,
    "correlation_id": "corr_req_123",
    "category": "authentication",
    "details": {
        "reason": "Token signature verification failed"
    }
}
```

**Validation Error:**
```json
{
    "error": "ValidationError",
    "message": "Request validation failed",
    "status_code": 422,
    "correlation_id": "corr_req_456",
    "category": "validation",
    "errors": {
        "email": "invalid email format",
        "age": "must be >= 18"
    }
}
```

---

## WebSocket / Real-Time

### Connection

```javascript
const ws = new WebSocket('wss://api.example.com/realtime/ws');
ws.onopen = () => {
    ws.send(JSON.stringify({
        type: 'auth',
        token: 'Bearer eyJhbG...'
    }));
};
```

### Channels

| Channel | Purpose |
|---------|---------|
| `jobs:{job_id}` | Job status updates |
| `alerts:{tenant_id}` | Alert notifications |
| `tickets:{ticket_id}` | Ticket updates |

### Message Format

```json
{
    "type": "job_status",
    "channel": "jobs:abc123",
    "data": {
        "status": "completed",
        "progress": 100
    },
    "timestamp": "2024-12-22T10:30:45Z"
}
```

---

## Health Endpoints

### Available Endpoints

| Endpoint | Purpose | Response |
|----------|---------|----------|
| `/health` | Basic health check | `{"status": "healthy"}` |
| `/health/live` | Kubernetes liveness | Always responds if running |
| `/health/ready` | Kubernetes readiness | Checks all dependencies |
| `/health/redis` | Redis status | Redis connection health |

### Readiness Response

```json
{
    "status": "ready",
    "healthy": true,
    "services": {
        "database": "healthy",
        "redis": "healthy",
        "vault": "degraded"
    },
    "failed_services": [],
    "timestamp": "2024-12-22T10:30:45Z"
}
```

---

## API Documentation

### OpenAPI/Swagger

| Endpoint | Environment | Purpose |
|----------|-------------|---------|
| `/docs` | dev/staging only | Swagger UI |
| `/redoc` | dev/staging only | ReDoc documentation |
| `/openapi.json` | all | OpenAPI schema |

**Note:** Swagger UI and ReDoc are disabled in production for security.

### Security Schemes

```yaml
components:
  securitySchemes:
    HTTPBearer:
      type: http
      scheme: bearer
      bearerFormat: JWT
    APIKey:
      type: apiKey
      name: X-API-Key
      in: header
```

---

## Complete Request Flow

```
┌─────────────────────────────────────────────────────────────┐
│                      CLIENT REQUEST                          │
│  Headers: Authorization, X-Tenant-ID, X-Correlation-ID      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    MIDDLEWARE CHAIN                          │
│  Host Validation → Context → Metrics → Tenant → RLS → CORS │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  DEPENDENCY INJECTION                        │
│  get_current_user() → JWT/API Key validation → UserInfo    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    ROUTE HANDLER                             │
│  Business logic with tenant context, scopes validated       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   CLIENT RESPONSE                            │
│  JSON body + X-Request-ID + X-Correlation-ID + CORS        │
└─────────────────────────────────────────────────────────────┘
```

---

## Security Features

| Feature | Implementation |
|---------|----------------|
| Multi-layer Auth | JWT + API Keys + OAuth2 + Cookies |
| Tenant Isolation | RLS middleware + X-Tenant-ID header |
| Token Revocation | Redis JTI blacklist |
| Rate Limiting | Redis-backed per-IP limiting |
| Correlation Tracking | Request/trace IDs across services |
| API Key Security | SHA-256 hashed, scoped, tenant-bound |
| Session Security | HttpOnly, Secure, SameSite cookies |
| Fail-Fast | Production startup fails if Redis/DB unavailable |

---

## Client Integration Examples

### Python (httpx)

```python
import httpx

client = httpx.AsyncClient(
    base_url="https://api.example.com",
    headers={
        "Authorization": f"Bearer {access_token}",
        "X-Tenant-ID": tenant_id,
        "X-Correlation-ID": correlation_id,
    }
)

response = await client.get("/api/v1/billing/invoices")
```

### JavaScript (fetch)

```javascript
const response = await fetch('https://api.example.com/api/v1/billing/invoices', {
    headers: {
        'Authorization': `Bearer ${accessToken}`,
        'X-Tenant-ID': tenantId,
        'Content-Type': 'application/json'
    }
});
```

### cURL

```bash
curl -X GET "https://api.example.com/api/v1/billing/invoices" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "X-Tenant-ID: ${TENANT_ID}" \
  -H "Content-Type: application/json"
```

---

## Related Documentation

- [Architecture Overview](ARCHITECTURE.md) - System architecture
- [Infrastructure Reference](INFRASTRUCTURE.md) - Shared infrastructure
- [Backend Production Guide](../BACKEND_PRODUCTION_GUIDE.md) - Deployment
