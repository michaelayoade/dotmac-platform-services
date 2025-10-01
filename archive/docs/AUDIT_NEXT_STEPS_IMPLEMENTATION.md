# Audit System - Complete Implementation Guide

## ✅ Completed Components

### 1. **Database Migration**
- Migration file created: `alembic/versions/2025_09_25_1000-add_audit_activities_table.py`
- Includes all necessary indexes for performance
- Ready to run with: `alembic upgrade head`

### 2. **React Frontend Components**
- **AuditActivityFeed.tsx** - Real-time activity feed with auto-refresh
- **AuditDashboard.tsx** - Analytics dashboard with charts and metrics
- Both components are production-ready with error handling and loading states

### 3. **Retention & Archiving System**
- **retention.py** - Complete retention policy implementation
- Automatic archiving to compressed JSON files
- Configurable retention by severity level
- Scheduled cleanup task ready

### 4. **Platform Integration**
- Authentication module ✅
- Secrets management ✅
- RBAC/User context ✅
- Middleware for automatic user tracking ✅

## 📋 Implementation Steps

### Step 1: Run Database Migration

```bash
# Check current migration status
alembic current

# Run the audit table migration
alembic upgrade add_audit_activities

# Verify table creation
psql -U postgres -d dotmac_platform -c "\d audit_activities"
```

### Step 2: Configure Audit Settings

Add to your `.env` file or settings:

```bash
# Audit Configuration
AUDIT_LOG_LEVEL=INFO
AUDIT_RETENTION_DAYS=90
AUDIT_ARCHIVE_ENABLED=true
AUDIT_ARCHIVE_LOCATION=/var/audit/archive

# Severity-specific retention (days)
AUDIT_RETENTION_LOW=30
AUDIT_RETENTION_MEDIUM=60
AUDIT_RETENTION_HIGH=90
AUDIT_RETENTION_CRITICAL=365
```

### Step 3: Set Up Scheduled Cleanup

#### Option A: Using Celery (Recommended)

```python
# src/dotmac/platform/tasks/audit_tasks.py
from celery import shared_task
from ..audit.retention import cleanup_audit_logs_task

@shared_task
def cleanup_audit_logs():
    """Daily audit log cleanup task."""
    import asyncio
    return asyncio.run(cleanup_audit_logs_task())

# In celerybeat schedule
CELERYBEAT_SCHEDULE = {
    'cleanup-audit-logs': {
        'task': 'dotmac.platform.tasks.audit_tasks.cleanup_audit_logs',
        'schedule': crontab(hour=2, minute=0),  # Run at 2 AM daily
    },
}
```

#### Option B: Using Cron

```bash
# Add to crontab
0 2 * * * /usr/bin/python /app/src/dotmac/platform/audit/retention.py
```

### Step 4: Extend Audit Logging to Additional Modules

#### File Storage Module

```python
# Add to src/dotmac/platform/file_storage/router.py

from fastapi import Request
from ..audit import log_api_activity, ActivityType, ActivitySeverity

@file_storage_router.post("/upload")
async def upload_file(
    file: UploadFile,
    request: Request,
    user: UserInfo = Depends(get_current_user),
):
    # Upload logic...
    result = await storage_service.upload(file)

    # Audit log
    await log_api_activity(
        request=request,
        activity_type=ActivityType.FILE_UPLOADED,
        action="file_upload",
        description=f"Uploaded file: {file.filename}",
        severity=ActivitySeverity.LOW,
        resource_type="file",
        resource_id=result.file_id,
        details={
            "filename": file.filename,
            "size": file.size,
            "content_type": file.content_type,
        }
    )

    return result

@file_storage_router.get("/download/{file_id}")
async def download_file(
    file_id: str,
    request: Request,
    user: UserInfo = Depends(get_current_user),
):
    # Download logic...
    file_data = await storage_service.download(file_id)

    # Audit log
    await log_api_activity(
        request=request,
        activity_type=ActivityType.FILE_DOWNLOADED,
        action="file_download",
        description=f"Downloaded file: {file_id}",
        severity=ActivitySeverity.LOW,
        resource_type="file",
        resource_id=file_id,
    )

    return file_data

@file_storage_router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    request: Request,
    user: UserInfo = Depends(get_current_user),
):
    # Delete logic...
    await storage_service.delete(file_id)

    # Audit log
    await log_api_activity(
        request=request,
        activity_type=ActivityType.FILE_DELETED,
        action="file_delete",
        description=f"Deleted file: {file_id}",
        severity=ActivitySeverity.MEDIUM,
        resource_type="file",
        resource_id=file_id,
    )

    return {"status": "deleted"}
```

#### Analytics Module

```python
# Add to src/dotmac/platform/analytics/router.py

@analytics_router.post("/track")
async def track_event(
    event_data: EventData,
    request: Request,
    user: UserInfo = Depends(get_current_user),
):
    # Track analytics event
    result = await analytics_service.track(event_data)

    # Audit log for significant events
    if event_data.event_type in ["purchase", "subscription", "cancellation"]:
        await log_api_activity(
            request=request,
            activity_type=ActivityType.API_REQUEST,
            action="analytics_track",
            description=f"Tracked event: {event_data.event_type}",
            severity=ActivitySeverity.MEDIUM,
            resource_type="analytics_event",
            resource_id=result.event_id,
            details=event_data.dict(),
        )

    return result
```

### Step 5: Deploy Frontend Components

#### Install Dependencies

```bash
cd frontend
npm install date-fns recharts lucide-react
```

#### Use in Your App

```tsx
// In your main dashboard
import { AuditDashboard } from '@/components/audit/AuditDashboard';
import { AuditActivityFeed } from '@/components/audit/AuditActivityFeed';

export function AdminDashboard() {
  return (
    <div>
      <AuditDashboard />

      <div className="mt-8">
        <AuditActivityFeed
          limit={50}
          days={7}
          autoRefresh={true}
          refreshInterval={30000}
          onActivityClick={(activity) => {
            console.log('Activity clicked:', activity);
            // Open detail modal or navigate to detail page
          }}
        />
      </div>
    </div>
  );
}

// For user-specific activities
export function UserActivityPage({ userId }) {
  return (
    <AuditActivityFeed
      userId={userId}
      limit={100}
      days={30}
    />
  );
}
```

### Step 6: Monitor and Optimize

#### Create Monitoring Dashboard

```python
# src/dotmac/platform/audit/monitoring.py
from prometheus_client import Counter, Histogram, Gauge

# Metrics
audit_activities_total = Counter(
    'audit_activities_total',
    'Total number of audit activities logged',
    ['activity_type', 'severity']
)

audit_retention_deleted = Counter(
    'audit_retention_deleted_total',
    'Total number of audit records deleted by retention',
    ['severity']
)

audit_query_duration = Histogram(
    'audit_query_duration_seconds',
    'Duration of audit query operations',
    ['operation']
)

audit_storage_size = Gauge(
    'audit_storage_size_bytes',
    'Current size of audit log storage'
)
```

#### Performance Optimization

```sql
-- Additional indexes for common queries
CREATE INDEX CONCURRENTLY idx_audit_resource_lookup
ON audit_activities(resource_type, resource_id, timestamp DESC);

CREATE INDEX CONCURRENTLY idx_audit_user_actions
ON audit_activities(user_id, action, timestamp DESC);

-- Partitioning for large datasets (optional)
CREATE TABLE audit_activities_2024_q4 PARTITION OF audit_activities
FOR VALUES FROM ('2024-10-01') TO ('2025-01-01');
```

### Step 7: Testing

#### Unit Tests

```python
# tests/audit/test_audit_service.py
import pytest
from datetime import datetime, timedelta
from dotmac.platform.audit import AuditService, ActivityType

@pytest.mark.asyncio
async def test_log_activity(audit_service):
    activity = await audit_service.log_activity(
        activity_type=ActivityType.USER_LOGIN,
        action="login",
        description="Test login",
        user_id="test_user",
        tenant_id="test_tenant",
    )

    assert activity.id is not None
    assert activity.user_id == "test_user"
    assert activity.activity_type == ActivityType.USER_LOGIN

@pytest.mark.asyncio
async def test_retention_cleanup(audit_service, retention_service):
    # Create old activities
    old_date = datetime.utcnow() - timedelta(days=100)

    # ... create test data ...

    # Run cleanup
    results = await retention_service.cleanup_old_logs()

    assert results["total_deleted"] > 0
    assert results["total_archived"] > 0
```

#### Integration Tests

```python
# tests/audit/test_audit_integration.py
@pytest.mark.asyncio
async def test_audit_with_auth_flow(client, test_user):
    # Login
    response = await client.post("/api/v1/auth/login", json={
        "username": test_user.username,
        "password": "testpass",
    })
    assert response.status_code == 200

    token = response.json()["access_token"]

    # Check audit log was created
    audit_response = await client.get(
        "/api/v1/audit/activities/recent",
        headers={"Authorization": f"Bearer {token}"}
    )

    activities = audit_response.json()
    assert any(a["activity_type"] == "user.login" for a in activities)
```

## 🎯 Performance Considerations

### Database Optimization

1. **Indexing Strategy**
   - Composite indexes for common query patterns
   - Partial indexes for filtered queries
   - Consider BRIN indexes for timestamp columns

2. **Partitioning** (for high-volume)
   ```sql
   -- Monthly partitions
   CREATE TABLE audit_activities_2024_09
   PARTITION OF audit_activities
   FOR VALUES FROM ('2024-09-01') TO ('2024-10-01');
   ```

3. **Vacuum Strategy**
   ```sql
   -- Regular vacuum for deleted records
   VACUUM ANALYZE audit_activities;
   ```

### Application Optimization

1. **Async Logging**
   - Use background tasks for non-critical logging
   - Batch inserts for high-volume scenarios

2. **Caching**
   - Cache frequently accessed summaries
   - Use Redis for real-time activity feeds

3. **Rate Limiting**
   - Limit audit query API calls
   - Implement pagination properly

## 🔒 Security Considerations

1. **Audit Log Integrity**
   - Make audit logs append-only
   - Use checksums for archived files
   - Implement log signing for critical events

2. **Access Control**
   - Restrict audit log access by role
   - Separate read/write permissions
   - Log audit log access itself

3. **Data Privacy**
   - Sanitize sensitive data in audit logs
   - Implement data retention compliance
   - Support right-to-be-forgotten requests

## 📊 Monitoring & Alerts

### Key Metrics to Monitor

```yaml
# Prometheus alert rules
groups:
  - name: audit_alerts
    rules:
      - alert: HighSeverityAuditEvents
        expr: rate(audit_activities_total{severity="CRITICAL"}[5m]) > 0
        for: 1m
        annotations:
          summary: "Critical audit events detected"

      - alert: AuditLogStorageFull
        expr: audit_storage_size_bytes > 10737418240  # 10GB
        for: 5m
        annotations:
          summary: "Audit log storage exceeding limits"

      - alert: AuditRetentionFailed
        expr: increase(audit_retention_errors_total[1h]) > 0
        for: 5m
        annotations:
          summary: "Audit retention cleanup failures"
```

## 🚀 Production Checklist

- [ ] Database migration executed successfully
- [ ] Audit settings configured in environment
- [ ] Retention policy configured and tested
- [ ] Scheduled cleanup task running
- [ ] Frontend components deployed and tested
- [ ] Monitoring and alerts configured
- [ ] Performance baselines established
- [ ] Security review completed
- [ ] Documentation updated
- [ ] Team trained on audit features

## Summary

The audit system is now fully implemented with:

✅ **Complete backend infrastructure** - Models, services, API, retention
✅ **Frontend components** - Dashboard and activity feed
✅ **Platform integration** - Auth, secrets, RBAC
✅ **Production-ready features** - Archiving, monitoring, security

The system provides comprehensive activity tracking with automatic user context extraction, tenant isolation, and configurable retention policies. It's ready for deployment and will provide valuable insights into system usage and security events.