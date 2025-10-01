# Audit System with RBAC/User Integration

## Overview

The audit system is fully integrated with the authentication and RBAC system to automatically track user activities throughout the platform.

## Architecture

### 1. **Automatic User Context Tracking**

The `AuditContextMiddleware` automatically extracts authenticated user information from:
- JWT Bearer tokens
- API Keys
- Session cookies

This information is made available via `request.state` for audit logging throughout the request lifecycle.

### 2. **User Information Available for Audit**

When a user is authenticated, the following information is automatically available:
- `user_id` - Unique user identifier
- `username` - User's username
- `email` - User's email address
- `tenant_id` - Multi-tenant isolation
- `roles` - User's RBAC roles (admin, user, api_user, etc.)

### 3. **Integration Points**

## How It Works

### Authentication → Audit Flow

```python
# 1. User authenticates via login endpoint
POST /api/v1/auth/login
{
  "username": "john.doe",
  "password": "********"
}

# 2. JWT token created with user claims
{
  "sub": "user123",
  "username": "john.doe",
  "email": "john@example.com",
  "roles": ["user", "admin"],
  "tenant_id": "tenant456"
}

# 3. Audit log created automatically
{
  "activity_type": "user.login",
  "user_id": "user123",
  "tenant_id": "tenant456",
  "action": "login_success",
  "description": "User john.doe logged in successfully",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "details": {
    "username": "john.doe",
    "roles": ["user", "admin"]
  }
}
```

### API Request → Audit Flow

```python
# 1. User makes authenticated request
GET /api/v1/secrets/database/credentials
Authorization: Bearer eyJhbGc...

# 2. AuditContextMiddleware extracts user from token
request.state.user_id = "user123"
request.state.tenant_id = "tenant456"
request.state.roles = ["user", "admin"]

# 3. Audit log created with user context
{
  "activity_type": "secret.accessed",
  "user_id": "user123",  # Automatically from auth
  "tenant_id": "tenant456",  # Automatically from auth
  "action": "secret_access_success",
  "resource_type": "secret",
  "resource_id": "database/credentials",
  "description": "Successfully accessed secret",
  "details": {
    "path": "database/credentials",
    "keys": ["host", "username", "password"]
  }
}
```

## Usage Examples

### 1. **Automatic User Tracking in Endpoints**

```python
from fastapi import Request, Depends
from ..auth.core import get_current_user, UserInfo
from ..audit import log_api_activity, ActivityType

@router.post("/api/resource")
async def create_resource(
    request: Request,
    user: UserInfo = Depends(get_current_user),  # Auth enforced
    data: ResourceData
):
    # User context automatically available via middleware
    # No need to manually pass user_id

    # Create resource...
    resource = await create_resource_logic(data)

    # Audit log automatically includes authenticated user
    await log_api_activity(
        request=request,
        activity_type=ActivityType.API_REQUEST,
        action="resource_created",
        description=f"Created resource: {resource.id}",
        resource_type="resource",
        resource_id=resource.id,
        # user_id and tenant_id automatically extracted from request.state
    )

    return resource
```

### 2. **Manual User Context for Background Tasks**

```python
from ..audit import log_user_activity, ActivityType

async def background_task(user_id: str, tenant_id: str):
    # For background tasks, manually provide user context

    # Perform operation...
    result = await perform_operation()

    # Log with explicit user context
    await log_user_activity(
        user_id=user_id,
        activity_type=ActivityType.SYSTEM_EVENT,
        action="background_task_completed",
        description="Background task completed successfully",
        tenant_id=tenant_id,
        details={"result": result}
    )
```

### 3. **RBAC-Aware Audit Queries**

```python
from fastapi import Depends
from ..auth.core import get_current_user, UserInfo
from ..audit import AuditService

@router.get("/api/v1/audit/my-activities")
async def get_my_activities(
    user: UserInfo = Depends(get_current_user),
    service: AuditService = Depends()
):
    # Users can only see their own activities
    activities = await service.get_recent_activities(
        user_id=user.user_id,
        tenant_id=user.tenant_id,  # Tenant isolation
        limit=50
    )
    return activities

@router.get("/api/v1/audit/all-activities")
async def get_all_activities(
    user: UserInfo = Depends(get_current_user),
    service: AuditService = Depends()
):
    # Only admins can see all activities
    if "admin" not in user.roles:
        raise HTTPException(403, "Admin access required")

    activities = await service.get_recent_activities(
        tenant_id=user.tenant_id,  # Still tenant-isolated
        limit=100
    )
    return activities
```

## Security Features

### 1. **Failed Authentication Tracking**

All failed authentication attempts are logged with HIGH severity:
- Failed logins (wrong password)
- Disabled account access attempts
- Invalid API key usage
- Expired token usage

### 2. **Sensitive Operation Tracking**

High-severity activities are automatically tracked:
- Secret access/modification/deletion
- User creation/deletion
- Permission changes
- System configuration changes

### 3. **Tenant Isolation**

All audit logs are tenant-isolated:
- Users can only see activities within their tenant
- Tenant admins can see all tenant activities
- Super admins can query across tenants

### 4. **Audit Trail Integrity**

- Audit logs are immutable once created
- Timestamps are server-generated
- IP addresses and user agents are captured
- Request IDs enable correlation with logs

## Frontend Integration

### Dashboard Activity Feed

```javascript
// Fetch recent activities for the current user
const response = await fetch('/api/v1/audit/activities/recent', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

const activities = await response.json();

// Display in UI
activities.forEach(activity => {
  console.log(`
    ${activity.timestamp}:
    ${activity.description}
    User: ${activity.user_id}
    Type: ${activity.activity_type}
    Severity: ${activity.severity}
  `);
});
```

### Admin Audit Dashboard

```javascript
// Admin view - all tenant activities
const response = await fetch('/api/v1/audit/activities?days=7&severity=HIGH', {
  headers: {
    'Authorization': `Bearer ${adminToken}`
  }
});

const { activities, total, has_next } = await response.json();

// Show security-relevant activities
const securityEvents = activities.filter(a =>
  a.severity === 'HIGH' ||
  a.severity === 'CRITICAL'
);
```

## Configuration

### Enable/Disable Audit Levels

```python
# In settings or environment variables
AUDIT_LOG_LEVEL = "INFO"  # LOW, MEDIUM, HIGH, CRITICAL
AUDIT_SENSITIVE_OPERATIONS = True  # Log all sensitive ops
AUDIT_FAILED_AUTH = True  # Log failed auth attempts
AUDIT_API_ACCESS = True  # Log API access
```

### Retention Policy

```python
# Automatic cleanup of old audit logs
AUDIT_RETENTION_DAYS = 90  # Keep logs for 90 days
AUDIT_ARCHIVE_ENABLED = True  # Archive before deletion
AUDIT_ARCHIVE_LOCATION = "s3://audit-archive"
```

## Benefits

1. **Compliance** - Complete audit trail for regulatory requirements
2. **Security** - Track unauthorized access attempts and suspicious activities
3. **Debugging** - Understand user actions leading to issues
4. **Analytics** - Analyze user behavior and system usage
5. **Forensics** - Investigate security incidents with full context

## Summary

The audit system is fully integrated with RBAC and authentication:
- ✅ Automatic user context extraction via middleware
- ✅ Tenant-isolated audit trails
- ✅ Role-based access to audit logs
- ✅ Security event tracking with severity levels
- ✅ Frontend-ready API endpoints
- ✅ Compliance-ready audit trails