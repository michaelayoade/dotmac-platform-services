# Frontend Observability - Extending Backend OpenTelemetry

This document explains how the frontend connects to the existing backend observability infrastructure.

## Architecture Overview

```
┌─────────────────────┐
│  Next.js Frontend   │
│  (Browser + SSR)    │
└──────────┬──────────┘
           │
           │ HTTP/OTLP
           │ :4318
           ▼
┌─────────────────────┐
│  OTEL Collector     │  ◄─── Shared with Backend
│  localhost:4318     │
└──────────┬──────────┘
           │
           ├─────────────────┐
           │                 │
           ▼                 ▼
    ┌──────────┐      ┌──────────┐
    │  Jaeger  │      │Prometheus│
    │  :16686  │      │  :9090   │
    └──────────┘      └──────────┘
           │                 │
           └────────┬────────┘
                    ▼
             ┌──────────┐
             │ Grafana  │
             │  :3400   │
             └──────────┘
```

## What's Already Set Up

### ✅ Backend (Python/FastAPI)
- **Full OpenTelemetry instrumentation** in `src/dotmac/platform/telemetry.py`
- **OTEL Collector** running on `localhost:4318` (HTTP) and `localhost:4317` (gRPC)
- **Jaeger UI** for trace visualization: http://localhost:16686
- **Prometheus** for metrics: http://localhost:9090
- **Grafana** dashboards: http://localhost:3400

### ✅ Frontend Shared Package (`@dotmac/headless`)
- **OpenTelemetry SDK** already installed
- **Instrumentation utilities** in `src/utils/telemetry.ts`
- **Error logging** with tracing in `src/services/ErrorLoggingService.ts`
- **HTTP interceptors** with correlation IDs

### ✅ Frontend Base App (Just Added!)
- **Instrumentation hook** in `instrumentation.ts`
- **Next.js config** with instrumentation enabled
- **Environment variable** for OTEL endpoint

## Setup Instructions

### 1. Start the Observability Stack

```bash
# From project root
docker-compose -f docker-compose.observability.yml up -d

# Verify services are running
docker ps | grep dotmac
```

**Services Started:**
- OTEL Collector: `localhost:4318` (HTTP), `localhost:4317` (gRPC)
- Jaeger UI: http://localhost:16686
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3400 (admin/admin)

### 2. Configure Frontend

```bash
# In frontend/apps/base-app/
cp .env.local.example .env.local

# Edit .env.local and ensure this line exists:
NEXT_PUBLIC_OTEL_ENDPOINT=http://localhost:4318
```

### 3. Start Backend (if not already running)

```bash
# From project root
poetry install
poetry run uvicorn dotmac.platform.main:app --reload --port 8000

# Backend will send traces to localhost:4318
```

### 4. Start Frontend

```bash
# From frontend/apps/base-app/
pnpm install
pnpm dev
```

### 5. Verify End-to-End Tracing

1. **Open the app**: http://localhost:3000
2. **Login and navigate**: Go to dashboard, create a customer, etc.
3. **View traces in Jaeger**: http://localhost:16686
   - Select service: `dotmac-frontend` or `dotmac-platform`
   - You should see traces from both frontend and backend!

## What Gets Traced

### Backend (Automatic)
- ✅ All FastAPI HTTP requests
- ✅ Database queries (SQLAlchemy)
- ✅ Outgoing HTTP calls (requests library)
- ✅ Redis operations
- ✅ Celery tasks

### Frontend (Automatic via instrumentation.ts)
- ✅ Server-side Next.js requests
- ✅ API route handlers
- ✅ getServerSideProps/getStaticProps
- ✅ Server actions

### Frontend (Manual - Already Available)
The shared package provides utilities you can use:

```typescript
import { createSpan, recordMetric, performance } from '@dotmac/headless/utils/telemetry';

// Manual span creation
const span = createSpan('custom-operation', { userId: '123' });
try {
  await doSomething();
  span.setStatus({ code: 'OK' });
} catch (error) {
  span.setStatus({ code: 'ERROR', message: error.message });
} finally {
  span.end();
}

// Record custom metrics
recordMetric('button.click', 1, { buttonId: 'submit' });

// Track API performance (already integrated in http-client)
performance.trackAPICall('/api/v1/customers', 'GET', 123, 200);
```

## Correlation IDs

**Already Implemented!** The HTTP client automatically adds correlation IDs:

```typescript
// frontend/shared/packages/http-client/src/platform-interceptors.ts
headers['X-Correlation-ID'] = generateCorrelationId();
```

This allows you to trace a request from:
1. Frontend button click
2. → API call with correlation ID
3. → Backend receives and propagates ID
4. → Database query with correlation ID in SQL comments
5. → Response back to frontend

All visible in Jaeger as a single trace!

## Viewing Traces

### Jaeger UI (http://localhost:16686)

1. **Select Service**: Choose `dotmac-frontend` or `dotmac-platform`
2. **Find Traces**: Click "Find Traces"
3. **View Details**: Click on a trace to see:
   - Full request timeline
   - Frontend → Backend spans
   - Database queries
   - Error details
   - Custom attributes

### Example Trace Structure

```
┌─ GET /dashboard/operations/customers [dotmac-frontend]
│  └─ fetch /api/v1/customers [Next.js SSR]
│     └─ GET /api/v1/customers [dotmac-platform]
│        ├─ SELECT * FROM customers [PostgreSQL]
│        ├─ Check permissions [RBAC]
│        └─ Format response
```

## Metrics

### Available Metrics

**Backend:**
- HTTP request duration/count
- Database query duration
- Cache hit/miss rates
- Custom business metrics

**Frontend (Server-Side):**
- Next.js render duration
- API call duration
- Page load metrics

### Viewing Metrics

1. **Prometheus**: http://localhost:9090
   - Query: `{service_name="dotmac-frontend"}`
   - See all metrics

2. **Grafana**: http://localhost:3400
   - Add Prometheus data source
   - Create dashboards with frontend + backend metrics

## Troubleshooting

### No traces appearing in Jaeger

```bash
# Check OTEL Collector is running
curl http://localhost:13133

# Check frontend is sending traces
curl http://localhost:4318/v1/traces
```

### Frontend instrumentation not working

```bash
# Verify experimental flag is enabled
grep instrumentationHook next.config.mjs

# Should output: instrumentationHook: true

# Verify env variable is set
echo $NEXT_PUBLIC_OTEL_ENDPOINT
# Should output: http://localhost:4318

# Restart Next.js dev server
pnpm dev
```

### Backend traces not showing

```bash
# Check backend settings
python -c "from dotmac.platform.settings import settings; print(settings.observability.otel_endpoint)"

# Should output: http://localhost:4318
```

## Production Considerations

### Environment Variables

**Development:**
```bash
NEXT_PUBLIC_OTEL_ENDPOINT=http://localhost:4318
```

**Production:**
```bash
# Point to your production OTEL Collector
NEXT_PUBLIC_OTEL_ENDPOINT=https://otel-collector.your-domain.com

# Or use cloud provider endpoints
# AWS: https://otlp.cloudwatch.amazonaws.com
# GCP: https://cloudtrace.googleapis.com
# Azure: https://dc.services.visualstudio.com
```

### Sampling

To reduce cost in production, configure sampling in `instrumentation.ts`:

```typescript
// Only sample 10% of traces
const sdk = new NodeSDK({
  resource,
  traceExporter,
  sampler: new TraceIdRatioBased(0.1), // 10% sampling
});
```

### Security

- ✅ Use HTTPS endpoints in production
- ✅ Authenticate to OTEL Collector (use headers)
- ✅ Don't send PII in trace attributes
- ✅ Sanitize error messages

## Additional Resources

- [OpenTelemetry JS Docs](https://opentelemetry.io/docs/instrumentation/js/)
- [Next.js Instrumentation](https://nextjs.org/docs/app/building-your-application/optimizing/instrumentation)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)
- [Backend Telemetry Code](../../src/dotmac/platform/telemetry.py)

## Summary

You now have **unified observability** across your entire stack:

1. ✅ **Frontend traces** sent to same OTEL Collector as backend
2. ✅ **Correlation IDs** automatically propagated
3. ✅ **Single view** of requests in Jaeger (frontend → backend → database)
4. ✅ **Metrics** from both frontend and backend in Prometheus
5. ✅ **Shared infrastructure** - no duplicate setup needed!

This is exactly what you wanted - extending your existing backend observability to the frontend! 🎉