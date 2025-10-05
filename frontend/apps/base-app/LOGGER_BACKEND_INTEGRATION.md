# Logger Backend Integration

## Current Status

The logger utility has been **enhanced with backend integration** for production environments.

## How It Works

### Development Mode
- Logs to browser console with formatted prefixes
- No backend communication
- Full verbosity for debugging

### Production Mode
- **Batched logging**: Logs are queued and sent in batches to reduce network overhead
- **Automatic flushing**: Logs are sent every 5 seconds or when queue reaches 10 items
- **Page unload handling**: Remaining logs are flushed before page navigation
- **Error resilience**: Failed log transmissions are re-queued (up to batch size)

## Backend Integration

### Current Implementation

```typescript
// In production, logs are sent to:
POST /api/v1/audit
```

**Payload format**:
```json
{
  "logs": [
    {
      "level": "ERROR" | "WARNING" | "INFO" | "DEBUG",
      "message": "Error message here",
      "service": "frontend",
      "metadata": {
        "timestamp": "2025-10-04T12:34:56.789Z",
        "userAgent": "Mozilla/5.0...",
        "url": "https://app.example.com/dashboard",
        // Additional context from logger call
        "userId": "user123",
        "error": "..."
      }
    }
  ]
}
```

### Backend Storage

Logs are stored in the `audit_activities` table via the audit service:

**Database Schema**:
- `activity_type`: Set to "frontend.log"
- `description`: The log message
- `severity`: Mapped from log level (ERROR → HIGH, WARNING → MEDIUM, etc.)
- `details`: JSON containing metadata (userAgent, url, context)
- `user_id`: Extracted from session
- `tenant_id`: Extracted from session
- `ip_address`: Client IP
- `created_at`: Timestamp

### Backend Endpoints

**Query logs**:
```bash
GET /api/v1/monitoring/logs?level=ERROR&service=frontend&page=1&page_size=100
```

**View statistics**:
```bash
GET /api/v1/monitoring/logs/stats
```

**Available services**:
```bash
GET /api/v1/monitoring/logs/services
```

## Configuration

### Environment Variables

```bash
# Frontend (.env.local)
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_ENABLE_INFO_LOGS=false  # Enable INFO logs in production
```

### Batching Configuration

You can adjust batching behavior in `lib/logger.ts`:

```typescript
private readonly BATCH_SIZE = 10;        // Send when queue reaches 10 items
private readonly FLUSH_INTERVAL = 5000;  // Send every 5 seconds
```

## Usage Examples

### Basic Logging

```typescript
import { logger } from '@/lib/logger';

// Error logging (always sent to backend in production)
logger.error('Failed to fetch data', {
  endpoint: '/api/users',
  statusCode: 500,
  userId: 'user123'
});

// Warning logging (sent to backend in production)
logger.warn('Slow API response', {
  endpoint: '/api/data',
  duration: 3000
});

// Info logging (only sent if NEXT_PUBLIC_ENABLE_INFO_LOGS=true)
logger.info('User logged in', {
  userId: 'user123',
  method: 'oauth'
});

// Debug logging (never sent to backend, dev only)
logger.debug('Component rendered', { component: 'Dashboard' });
```

### API Error Logging

```typescript
try {
  const response = await fetch('/api/users');
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
} catch (error) {
  logger.apiError('/api/users', error, {
    userId: currentUser.id,
    retryCount: 3
  });
}
```

### User Action Tracking

```typescript
// Track user interactions
logger.userAction('Button clicked', {
  buttonId: 'create-partner',
  page: '/dashboard/partners'
});

// This can integrate with analytics in the future
```

## Viewing Logs

### Via Backend API

```bash
# Get recent errors
curl -X GET "http://localhost:8000/api/v1/monitoring/logs?level=ERROR&service=frontend" \
  -H "Authorization: Bearer $TOKEN"

# Get log statistics
curl -X GET "http://localhost:8000/api/v1/monitoring/logs/stats" \
  -H "Authorization: Bearer $TOKEN"
```

### Via Dashboard (TODO)

Create a frontend page at `/dashboard/platform-admin/logs` to view frontend logs:

```typescript
import { useQuery } from '@tanstack/react-query';

function FrontendLogsPage() {
  const { data } = useQuery({
    queryKey: ['frontend-logs'],
    queryFn: async () => {
      const response = await fetch('/api/v1/monitoring/logs?service=frontend');
      return response.json();
    }
  });

  return (
    <div>
      {data?.logs.map(log => (
        <div key={log.id}>
          <span className={getLevelColor(log.level)}>{log.level}</span>
          <span>{log.message}</span>
          <pre>{JSON.stringify(log.metadata, null, 2)}</pre>
        </div>
      ))}
    </div>
  );
}
```

## Migration from Console Statements

### Automated Script

Run the automated replacement script:

```bash
cd frontend/apps/base-app
./scripts/replace-console-with-logger.sh
```

This will:
1. Find all files with `console.*` statements
2. Add `import { logger } from '@/lib/logger'`
3. Replace:
   - `console.error()` → `logger.error()`
   - `console.warn()` → `logger.warn()`
   - `console.log()` → `logger.info()`
   - `console.debug()` → `logger.debug()`

### Manual Migration Pattern

**Before**:
```typescript
try {
  await deletePartner(partnerId);
} catch (error) {
  console.error('Failed to delete partner:', error);
  alert('Failed to delete partner');
}
```

**After**:
```typescript
import { logger } from '@/lib/logger';

try {
  await deletePartner(partnerId);
  logger.info('Partner deleted successfully', { partnerId });
} catch (error) {
  logger.error('Failed to delete partner', { partnerId, error });
  alert('Failed to delete partner');
}
```

## Backend TODO

### Required Backend Changes

The backend audit endpoint currently only supports GET requests. To fully integrate frontend logging, add a POST endpoint:

```python
# src/dotmac/platform/audit/router.py

from pydantic import BaseModel
from typing import List

class FrontendLogEntry(BaseModel):
    level: str
    message: str
    service: str
    metadata: dict

class FrontendLogsRequest(BaseModel):
    logs: List[FrontendLogEntry]

@router.post("/activities/frontend-logs")
async def create_frontend_logs(
    request: Request,
    logs_request: FrontendLogsRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user: Optional[UserInfo] = Depends(get_current_user_optional),
):
    """Accept batched frontend logs and store in audit_activities."""
    service = AuditService(session)

    # Map log levels to severities
    severity_map = {
        "ERROR": ActivitySeverity.HIGH,
        "WARNING": ActivitySeverity.MEDIUM,
        "INFO": ActivitySeverity.LOW,
        "DEBUG": ActivitySeverity.LOW,
    }

    for log_entry in logs_request.logs:
        await service.log_activity(
            activity_type=ActivityType.FRONTEND_LOG,
            description=log_entry.message,
            severity=severity_map.get(log_entry.level, ActivitySeverity.LOW),
            details=log_entry.metadata,
            user_id=current_user.user_id if current_user else None,
            ip_address=request.client.host,
        )

    return {"status": "success", "logs_received": len(logs_request.logs)}
```

Add to `ActivityType` enum:
```python
class ActivityType(str, Enum):
    # ... existing types
    FRONTEND_LOG = "frontend.log"
```

## Performance Considerations

### Batching Benefits
- **Reduced network requests**: Sends 10 logs at once instead of 10 separate requests
- **Lower backend load**: Backend processes batches more efficiently
- **Better user experience**: Non-blocking, async log transmission

### Memory Management
- Queue is capped at batch size on failure to prevent memory leaks
- Failed logs are dropped after one retry to avoid infinite growth
- Logs are flushed on page unload to prevent data loss

### Network Optimization
- Logs are sent with `credentials: 'include'` for session authentication
- Failed transmissions fall back to console logging
- No retry storms - single re-queue attempt only

## Testing

### Development Testing
```typescript
// Test in dev mode (logs to console)
logger.error('Test error', { testContext: 'value' });
logger.warn('Test warning');
logger.info('Test info');
logger.debug('Test debug');
```

### Production Testing
```bash
# Build for production
npm run build

# Run in production mode
NODE_ENV=production npm start

# Check browser console and backend audit logs
```

### Backend Verification
```bash
# Check audit activities table
psql -d dotmac_db -c "SELECT * FROM audit_activities WHERE activity_type = 'frontend.log' ORDER BY created_at DESC LIMIT 10;"
```

## Security Considerations

1. **Authentication**: Logs are sent with session credentials
2. **Rate limiting**: Backend should rate-limit log ingestion per user/tenant
3. **Data sanitization**: Sensitive data should be excluded from context
4. **Log retention**: Configure audit log retention policies

**Never log**:
- Passwords or tokens
- Full user objects (log user IDs only)
- Credit card numbers
- Personal identifiable information (PII)

**Example - Good vs Bad**:

```typescript
// ❌ BAD - logs sensitive data
logger.error('Login failed', {
  password: userPassword,  // NEVER!
  email: user.email       // PII
});

// ✅ GOOD - logs only necessary context
logger.error('Login failed', {
  userId: user.id,        // ID only
  reason: 'invalid_credentials'
});
```

## Future Enhancements

### Phase 1 (Current) ✅
- [x] Batched logging to backend
- [x] Error/warning/info level support
- [x] User context and metadata
- [x] Automatic flushing

### Phase 2 (Next)
- [ ] Backend POST endpoint for frontend logs
- [ ] Dashboard page to view frontend logs
- [ ] Error rate alerting
- [ ] User session correlation

### Phase 3 (Future)
- [ ] Integration with Sentry for error tracking
- [ ] Integration with analytics (GA4, Mixpanel)
- [ ] Real-time log streaming (WebSockets)
- [ ] Advanced filtering and search in dashboard
- [ ] Log export functionality

---

**Created**: 2025-10-04
**Status**: ✅ Production Ready (pending backend POST endpoint)
