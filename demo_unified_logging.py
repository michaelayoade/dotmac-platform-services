#!/usr/bin/env python3
"""
Demonstration of the DotMac Platform Unified Logging System.

This script showcases the features of the new centralized logging system
with OpenTelemetry integration.
"""

import asyncio
import sys
import time
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from dotmac.platform.observability.unified_logging import (
    get_logger,
    set_context,
    clear_context,
    audit_log,
    log_performance,
    setup_otel_logging
)

# Get a logger for this module
logger = get_logger(__name__)


def demo_basic_logging():
    """Demonstrate basic logging capabilities."""
    print("\n=== Basic Logging ===")

    logger.info("Starting application", version="1.0.0", environment="demo")
    logger.debug("Debug message with context", debug_level=2)
    logger.warning("Warning message", threshold_exceeded=True, value=95.5)

    try:
        raise ValueError("Demo error for logging")
    except ValueError as e:
        logger.error("Error occurred", error=str(e), exc_info=True)


def demo_context_logging():
    """Demonstrate context-aware logging."""
    print("\n=== Context-Aware Logging ===")

    # Set context for a request
    set_context(
        correlation_id="req-12345",
        tenant_id="tenant-001",
        user_id="user-42"
    )

    logger.info("Processing request", endpoint="/api/data")
    logger.info("Database query executed", query_time_ms=45.2, rows_returned=150)
    logger.info("Response sent", status_code=200, response_time_ms=120.5)

    # Clear context after request
    clear_context()
    logger.info("Context cleared - no correlation ID in this log")


def demo_audit_logging():
    """Demonstrate audit logging for security events."""
    print("\n=== Audit Logging ===")

    # Set user context
    set_context(tenant_id="tenant-001", user_id="admin-user")

    # Log audit events
    audit_log(
        action="user.login",
        resource="authentication_system",
        outcome="success",
        details={"ip": "192.168.1.100", "method": "password"}
    )

    audit_log(
        action="secret.access",
        resource="api_keys/production",
        outcome="success",
        details={"purpose": "deployment"}
    )

    audit_log(
        action="permission.denied",
        resource="admin_panel",
        outcome="denied",
        details={"required_role": "super_admin", "user_role": "admin"}
    )

    clear_context()


@log_performance
def slow_operation():
    """Demonstrate performance logging decorator."""
    logger.info("Performing slow operation")
    time.sleep(0.1)  # Simulate work
    return "Operation completed"


@log_performance
async def async_operation():
    """Demonstrate async performance logging."""
    logger.info("Performing async operation")
    await asyncio.sleep(0.1)  # Simulate async work
    return "Async operation completed"


def demo_performance_logging():
    """Demonstrate performance logging decorators."""
    print("\n=== Performance Logging ===")

    # Synchronous function
    result = slow_operation()
    logger.info("Sync result", result=result)

    # Async function
    async def run_async():
        result = await async_operation()
        logger.info("Async result", result=result)

    asyncio.run(run_async())


def demo_structured_data():
    """Demonstrate structured data logging."""
    print("\n=== Structured Data Logging ===")

    # Log complex data structures
    logger.info(
        "api_metrics",
        endpoint="/api/users",
        method="GET",
        metrics={
            "response_time_ms": 45.2,
            "db_queries": 3,
            "cache_hits": 2,
            "cache_misses": 1
        },
        user_agent="Mozilla/5.0",
        status_code=200
    )

    # Log lists and nested structures
    logger.info(
        "batch_processing_complete",
        batch_id="batch-789",
        items_processed=100,
        errors=[
            {"item_id": 23, "error": "validation_failed"},
            {"item_id": 67, "error": "duplicate_key"}
        ],
        processing_time_seconds=12.5
    )


def demo_multi_tenant():
    """Demonstrate multi-tenant logging."""
    print("\n=== Multi-Tenant Logging ===")

    tenants = ["tenant-A", "tenant-B", "tenant-C"]

    for tenant_id in tenants:
        set_context(tenant_id=tenant_id, correlation_id=f"batch-{tenant_id}")

        logger.info(
            "Processing tenant data",
            operation="data_sync",
            records_processed=100
        )

        # Each log will automatically include the tenant context
        logger.info("Tenant processing complete")
        clear_context()


def demo_error_scenarios():
    """Demonstrate error logging scenarios."""
    print("\n=== Error Scenarios ===")

    # Validation error
    logger.error(
        "validation_failed",
        field="email",
        value="invalid@",
        validation_rule="email_format"
    )

    # Connection error
    logger.error(
        "connection_failed",
        service="redis",
        host="localhost",
        port=6379,
        retry_count=3,
        error="Connection refused"
    )

    # Business logic error
    logger.error(
        "business_rule_violation",
        rule="credit_limit_exceeded",
        requested_amount=10000,
        available_credit=5000,
        customer_id="cust-123"
    )


def main():
    """Run all demonstrations."""
    print("=" * 60)
    print("DotMac Platform Unified Logging System Demo")
    print("=" * 60)

    # Optional: Setup OpenTelemetry export (commented out for demo)
    # setup_otel_logging(
    #     service_name="demo-app",
    #     otlp_endpoint="localhost:4317"
    # )

    demo_basic_logging()
    demo_context_logging()
    demo_audit_logging()
    demo_performance_logging()
    demo_structured_data()
    demo_multi_tenant()
    demo_error_scenarios()

    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)
    print("\nKey Features Demonstrated:")
    print("✓ Structured logging with rich context")
    print("✓ Automatic correlation ID tracking")
    print("✓ Multi-tenant context management")
    print("✓ Performance logging decorators")
    print("✓ Audit logging for security events")
    print("✓ OpenTelemetry trace correlation")
    print("✓ Colored console output in development")
    print("✓ JSON output in production")


if __name__ == "__main__":
    main()