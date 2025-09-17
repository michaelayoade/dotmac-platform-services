# DotMac Platform Services - Integration Guide

## Overview

This document provides a comprehensive guide for integrating and using the DotMac Platform Services framework in other projects. The platform provides a unified set of services for authentication, service discovery, audit logging, distributed locking, and more.

## New Services Added

### 1. Service Registry & Discovery

**Purpose**: Centralized service registration and discovery with health monitoring and load balancing.

**Key Features**:
- Automatic service registration with TTL
- Health check monitoring with configurable intervals
- Load balancing strategies (round robin, least connections, random)
- Service metadata and tag-based filtering

**Configuration**:
```python
from dotmac.platform.service_registry.config import ServiceRegistryConfig

config = ServiceRegistryConfig(
    redis_url="redis://localhost:6379/0",
    default_ttl=60,
    health_check_interval=30,
    load_balancing_strategy="round_robin"
)
```

**Usage Example**:
```python
from dotmac.platform.service_registry import ServiceRegistry

# Initialize registry
registry = ServiceRegistry(redis_url="redis://localhost:6379/0")

# Register a service
await registry.register_service(
    name="user-service",
    version="1.0.0",
    host="localhost",
    port=8001,
    tags=["user", "auth"],
    health_check_url="http://localhost:8001/health"
)

# Discover services
services = await registry.discover_services("user-service")
service = await registry.get_service("user-service")  # Load balanced

# Health monitoring
await registry.start_health_monitoring()
```

### 2. Audit Trail Aggregator

**Purpose**: Centralized audit logging with compliance reporting and anomaly detection.

**Key Features**:
- Structured audit event collection
- Real-time anomaly detection
- Compliance reporting (SOX, GDPR, HIPAA)
- Event correlation and pattern analysis
- Export to multiple formats (JSON, CSV, PDF)

**Configuration**:
```python
from dotmac.platform.audit_trail.config import AuditTrailConfig

config = AuditTrailConfig(
    postgres_url="postgresql+asyncpg://user:pass@localhost:5432/dotmac",
    redis_url="redis://localhost:6379/0",
    retention_days=365,
    anomaly_detection_enabled=True
)
```

**Usage Example**:
```python
from dotmac.platform.audit_trail import AuditAggregator, AuditCategory, AuditLevel

# Initialize aggregator
aggregator = AuditAggregator(
    postgres_url="postgresql+asyncpg://user:pass@localhost:5432/dotmac",
    redis_url="redis://localhost:6379/0"
)

# Log audit events
event_id = await aggregator.log_event(
    category=AuditCategory.AUTHENTICATION,
    action="user.login",
    level=AuditLevel.INFO,
    user_id="user123",
    tenant_id="tenant456",
    metadata={"ip_address": "192.168.1.1", "user_agent": "..."}
)

# Query events
events = await aggregator.query_events(
    start_time=datetime.now() - timedelta(days=7),
    categories=[AuditCategory.AUTHENTICATION],
    user_id="user123"
)

# Generate compliance report
report = await aggregator.generate_compliance_report(
    start_date=date.today() - timedelta(days=30),
    end_date=date.today(),
    report_type="access_log"
)
```

### 3. Distributed Lock Manager

**Purpose**: Redis-based distributed locking with automatic renewal and deadlock detection.

**Key Features**:
- Automatic lock renewal to prevent timeouts
- Deadlock detection and resolution
- Fair queueing for lock acquisition
- Context manager and decorator interfaces
- Performance monitoring and metrics

**Configuration**:
```python
from dotmac.platform.distributed_locks.config import DistributedLockConfig

config = DistributedLockConfig(
    redis_url="redis://localhost:6379/0",
    default_timeout=10.0,
    auto_renewal_enabled=True,
    deadlock_detection_enabled=True
)
```

**Usage Example**:
```python
from dotmac.platform.distributed_locks import DistributedLockManager, DistributedLock

# Initialize lock manager
lock_manager = DistributedLockManager(redis_url="redis://localhost:6379/0")

# Use as context manager
async with lock_manager.acquire_lock("resource:123", timeout=30.0) as lock:
    # Critical section - only one process can execute this
    await process_resource("123")

# Use as decorator
@lock_manager.with_lock("user:{user_id}", timeout=10.0)
async def update_user_profile(user_id: str, data: dict):
    # This function is automatically locked per user
    await update_database(user_id, data)

# Manual lock management
lock = DistributedLock(redis_client, "payment:processing", timeout=60.0)
acquired = await lock.acquire()
if acquired:
    try:
        await process_payment()
    finally:
        await lock.release()
```

## Unified Configuration System

The platform now includes a unified configuration system that aggregates all service configurations:

### Using Unified Configuration

```python
from dotmac.platform.core.unified_config import get_config, PlatformConfig

# Get full configuration
config = get_config()

# Access specific service configurations
auth_config = config.auth
db_config = config.database
registry_config = config.service_registry
audit_config = config.audit_trail
locks_config = config.distributed_locks

# Check environment
if config.is_production():
    # Production-specific logic
    pass

# Get common URLs
redis_url = config.get_redis_url()
db_url = config.get_database_url()
service_name = config.get_service_name()
```

### Environment Variables

Configure the platform using environment variables:

```bash
# Application settings
export APP_NAME="my-service"
export APP_VERSION="2.0.0"
export ENVIRONMENT="production"
export DEBUG="false"

# Database
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/mydb"

# Redis
export REDIS_URL="redis://localhost:6379/0"

# Service Registry
export SERVICE_REGISTRY_DEFAULT_TTL="120"
export SERVICE_REGISTRY_HEALTH_CHECK_INTERVAL="60"

# Audit Trail
export AUDIT_TRAIL_RETENTION_DAYS="730"
export AUDIT_TRAIL_ANOMALY_DETECTION_ENABLED="true"

# Distributed Locks
export DISTRIBUTED_LOCKS_DEFAULT_TIMEOUT="15.0"
export DISTRIBUTED_LOCKS_AUTO_RENEWAL_ENABLED="true"
```

## Integration Examples

### 1. FastAPI Application Integration

```python
from fastapi import FastAPI
from dotmac.platform.core.unified_config import get_config
from dotmac.platform.service_registry import ServiceRegistry
from dotmac.platform.audit_trail import AuditAggregator
from dotmac.platform.distributed_locks import DistributedLockManager

app = FastAPI()

# Initialize platform services
config = get_config()
registry = ServiceRegistry(redis_url=config.get_redis_url())
audit = AuditAggregator(
    postgres_url=config.get_database_url(),
    redis_url=config.get_redis_url()
)
locks = DistributedLockManager(redis_url=config.get_redis_url())

@app.on_event("startup")
async def startup():
    # Register this service
    await registry.register_service(
        name="my-api",
        version=config.app_version,
        host="localhost",
        port=8000,
        health_check_url="http://localhost:8000/health"
    )

    # Start health monitoring
    await registry.start_health_monitoring()

@app.get("/users/{user_id}")
async def get_user(user_id: str):
    # Log access
    await audit.log_event(
        category="DATA_ACCESS",
        action="user.read",
        user_id=current_user.id,
        metadata={"accessed_user": user_id}
    )

    # Use distributed lock for consistent reads
    async with locks.acquire_lock(f"user:{user_id}"):
        return await get_user_from_db(user_id)

@app.put("/users/{user_id}")
@locks.with_lock("user:{user_id}", timeout=30.0)
async def update_user(user_id: str, data: dict):
    # Automatically locked - only one update per user at a time
    await audit.log_event(
        category="DATA_CHANGE",
        action="user.update",
        user_id=current_user.id,
        metadata={"target_user": user_id, "changes": list(data.keys())}
    )

    return await update_user_in_db(user_id, data)
```

### 2. Microservice Communication

```python
# Service A: Producer
from dotmac.platform.service_registry import ServiceRegistry

registry = ServiceRegistry()

# Discover service B
service_b = await registry.get_service("service-b")
if service_b:
    response = await httpx.get(f"http://{service_b.host}:{service_b.port}/api/data")

# Service B: Consumer
@app.on_event("startup")
async def startup():
    await registry.register_service(
        name="service-b",
        version="1.0.0",
        host="localhost",
        port=8001,
        tags=["data", "processing"]
    )
```

### 3. Background Task Processing

```python
from celery import Celery
from dotmac.platform.distributed_locks import DistributedLockManager

app = Celery('tasks')
locks = DistributedLockManager()

@app.task
@locks.with_lock("report:generation", timeout=300.0)
async def generate_monthly_report():
    # Ensure only one report generation runs at a time
    await audit.log_event(
        category="SYSTEM_TASK",
        action="report.generate",
        metadata={"report_type": "monthly"}
    )

    # Generate report logic
    pass
```

## Migration Guide

### From Existing Projects

1. **Install Dependencies**:
   ```bash
   pip install redis asyncpg sqlalchemy[asyncio] pydantic
   ```

2. **Update Configuration**:
   Replace existing config with unified config:
   ```python
   # Old way
   DATABASE_URL = os.getenv("DATABASE_URL")
   REDIS_URL = os.getenv("REDIS_URL")

   # New way
   from dotmac.platform.core.unified_config import get_config
   config = get_config()
   database_url = config.get_database_url()
   redis_url = config.get_redis_url()
   ```

3. **Add Service Registration**:
   ```python
   # In your startup code
   from dotmac.platform.service_registry import ServiceRegistry

   registry = ServiceRegistry()
   await registry.register_service(
       name="your-service",
       version="1.0.0",
       host="localhost",
       port=8000
   )
   ```

4. **Add Audit Logging**:
   ```python
   # Replace existing logging
   from dotmac.platform.audit_trail import AuditAggregator

   audit = AuditAggregator()

   # Before sensitive operations
   await audit.log_event(
       category="AUTHENTICATION",
       action="user.login",
       user_id=user.id
   )
   ```

5. **Add Distributed Locking**:
   ```python
   # For critical sections
   from dotmac.platform.distributed_locks import DistributedLockManager

   locks = DistributedLockManager()

   async with locks.acquire_lock("critical:resource"):
       # Your critical code here
       pass
   ```

## Best Practices

### 1. Service Registry

- Use meaningful service names and consistent versioning
- Include comprehensive health checks
- Use tags for service categorization
- Set appropriate TTL values based on service reliability

### 2. Audit Trail

- Log all authentication and authorization events
- Include contextual metadata (IP, user agent, etc.)
- Use appropriate audit levels (INFO for normal operations, WARNING for suspicious activity)
- Regular cleanup of old audit data

### 3. Distributed Locks

- Use descriptive lock names with clear scope
- Set reasonable timeouts to prevent indefinite blocking
- Use the shortest possible critical sections
- Always use try/finally or context managers for lock cleanup

### 4. Configuration

- Use environment variables for deployment-specific settings
- Keep sensitive data in environment variables or secret management
- Validate configuration at startup
- Use type hints and Pydantic models for configuration classes

## Troubleshooting

### Common Issues

1. **Service Discovery Failures**:
   - Check Redis connectivity
   - Verify service registration TTL
   - Ensure health check endpoints are accessible

2. **Audit Events Not Appearing**:
   - Check PostgreSQL connectivity
   - Verify audit event configuration
   - Check for database migration status

3. **Lock Acquisition Timeouts**:
   - Check Redis connectivity
   - Review lock timeout settings
   - Look for potential deadlocks

4. **Configuration Errors**:
   - Validate environment variables
   - Check Pydantic validation errors
   - Ensure all required configuration is provided

### Monitoring and Observability

The platform integrates with OpenTelemetry for comprehensive observability:

```python
from dotmac.platform.observability.unified_logging import get_logger

logger = get_logger(__name__)

# All platform services automatically emit metrics and traces
# Check your observability dashboard for:
# - Service registry metrics (registrations, discoveries, health checks)
# - Audit trail metrics (events per second, anomalies detected)
# - Lock metrics (acquisition time, contention, timeouts)
```

## Support and Resources

- **Documentation**: Check individual service modules for detailed API documentation
- **Examples**: See `examples/` directory for complete integration examples
- **Configuration Reference**: Check `config.py` files in each service module
- **Troubleshooting**: Enable debug logging with `DEBUG=true` environment variable

This integration guide provides the foundation for using the DotMac Platform Services in any project requiring scalable, observable, and reliable microservice infrastructure.