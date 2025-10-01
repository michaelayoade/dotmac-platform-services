"""
Centralized router registration for all API endpoints.

All routes except /health, /ready, and /metrics require authentication.
"""

import importlib
from dataclasses import dataclass
from typing import Any, Dict, List

import structlog
from fastapi import Depends, FastAPI
from fastapi.security import HTTPBearer

logger = structlog.get_logger(__name__)

# Security scheme for Swagger UI
security = HTTPBearer(auto_error=False)


@dataclass
class RouterConfig:
    """Configuration for a router to be registered."""

    module_path: str
    router_name: str
    prefix: str
    tags: List[str]
    requires_auth: bool = True
    description: str = ""


# Define router configurations
ROUTER_CONFIGS = [
    RouterConfig(
        module_path="dotmac.platform.auth.router",
        router_name="auth_router",
        prefix="/api/v1/auth",
        tags=["Authentication"],
        requires_auth=False,  # Auth router doesn't require auth
        description="Authentication endpoints",
    ),
    RouterConfig(
        module_path="dotmac.platform.auth.rbac_read_router",
        router_name="router",
        prefix="/api/v1/auth/rbac",
        tags=["RBAC"],
        requires_auth=True,
        description="RBAC read-only endpoints for frontend",
    ),
    RouterConfig(
        module_path="dotmac.platform.secrets.api",
        router_name="router",
        prefix="/api/v1/secrets",
        tags=["Secrets Management"],
        description="Vault/OpenBao secrets management",
    ),
    RouterConfig(
        module_path="dotmac.platform.analytics.router",
        router_name="analytics_router",
        prefix="/api/v1/analytics",
        tags=["Analytics"],
        description="Analytics and metrics endpoints",
    ),
    RouterConfig(
        module_path="dotmac.platform.file_storage.router",
        router_name="file_storage_router",
        prefix="/api/v1/files/storage",
        tags=["File Storage"],
        description="File storage management",
    ),
    RouterConfig(
        module_path="dotmac.platform.communications.router",
        router_name="router",
        prefix="/api/v1/communications",
        tags=["Communications"],
        description="Communications API with email, templates, and background tasks",
    ),
    RouterConfig(
        module_path="dotmac.platform.search.router",
        router_name="search_router",
        prefix="/api/v1/search",
        tags=["Search"],
        description="Search functionality",
    ),
    RouterConfig(
        module_path="dotmac.platform.data_transfer.router",
        router_name="data_transfer_router",
        prefix="/api/v1/data-transfer",
        tags=["Data Transfer"],
        description="Data import/export operations",
    ),
    RouterConfig(
        module_path="dotmac.platform.user_management.router",
        router_name="user_router",
        prefix="/api/v1/users",
        tags=["User Management"],
        description="User management endpoints",
    ),
    RouterConfig(
        module_path="dotmac.platform.feature_flags.router",
        router_name="feature_flags_router",
        prefix="/api/v1/feature-flags",
        tags=["Feature Flags"],
        description="Feature flags management",
    ),
    RouterConfig(
        module_path="dotmac.platform.customer_management.router",
        router_name="router",
        prefix="/api/v1/customers",
        tags=["Customer Management"],
        description="Customer relationship management",
    ),
    RouterConfig(
        module_path="dotmac.platform.contacts.router",
        router_name="router",
        prefix="/api/v1/contacts",
        tags=["Contacts"],
        description="Contact management system",
    ),
    RouterConfig(
        module_path="dotmac.platform.auth.api_keys_router",
        router_name="router",
        prefix="/api/v1/auth/api-keys",
        tags=["API Keys"],
        description="API key management",
    ),
    RouterConfig(
        module_path="dotmac.platform.webhooks.router",
        router_name="router",
        prefix="/api/v1/webhooks",
        tags=["Webhooks"],
        description="Generic webhook subscription and event management",
        requires_auth=True,
    ),
    RouterConfig(
        module_path="dotmac.platform.billing.router",
        router_name="router",
        prefix="/api/v1/billing",
        tags=["Billing"],
        description="Billing and payment management",
    ),
    RouterConfig(
        module_path="dotmac.platform.plugins.router",
        router_name="router",
        prefix="/api/v1",
        tags=["Plugin Management"],
        description="Dynamic plugin system management",
    ),
    RouterConfig(
        module_path="dotmac.platform.audit.router",
        router_name="router",
        prefix="/api/v1/audit",
        tags=["Audit"],
        description="Audit trails and activity tracking",
    ),
    RouterConfig(
        module_path="dotmac.platform.admin.settings.router",
        router_name="router",
        prefix="/api/v1/admin/settings",
        tags=["Admin", "Settings"],
        description="Platform settings management (admin only)",
        requires_auth=True,  # Uses require_admin internally
    ),
    RouterConfig(
        module_path="dotmac.platform.billing.catalog.router",
        router_name="router",
        prefix="/api/v1/billing/catalog",
        tags=["Billing", "Products"],
        description="Product catalog management",
        requires_auth=True,
    ),
    RouterConfig(
        module_path="dotmac.platform.billing.subscriptions.router",
        router_name="router",
        prefix="/api/v1/billing/subscriptions",
        tags=["Billing", "Subscriptions"],
        description="Subscription management",
        requires_auth=True,
    ),
    RouterConfig(
        module_path="dotmac.platform.billing.pricing.router",
        router_name="router",
        prefix="/api/v1/billing/pricing",
        tags=["Billing", "Pricing"],
        description="Pricing engine and rules",
        requires_auth=True,
    ),
    RouterConfig(
        module_path="dotmac.platform.billing.bank_accounts.router",
        router_name="router",
        prefix="/api/v1/billing/bank-accounts",
        tags=["Billing", "Bank Accounts"],
        description="Bank accounts and manual payments",
        requires_auth=True,
    ),
    RouterConfig(
        module_path="dotmac.platform.billing.settings.router",
        router_name="router",
        prefix="/api/v1/billing/settings",
        tags=["Billing", "Settings"],
        description="Billing configuration and settings",
        requires_auth=True,
    ),
    RouterConfig(
        module_path="dotmac.platform.monitoring.logs_router",
        router_name="logs_router",
        prefix="/api/v1/monitoring",
        tags=["Monitoring", "Logs"],
        description="Application logs with filtering and search",
        requires_auth=True,
    ),
    RouterConfig(
        module_path="dotmac.platform.monitoring.traces_router",
        router_name="traces_router",
        prefix="/api/v1/observability",
        tags=["Observability", "Traces", "Metrics"],
        description="Distributed traces, metrics, and performance data",
        requires_auth=True,
    ),
    RouterConfig(
        module_path="dotmac.platform.partner_management.router",
        router_name="router",
        prefix="/api/v1/partners",
        tags=["Partner Management"],
        description="Partner relationship management",
        requires_auth=True,
    ),
    RouterConfig(
        module_path="dotmac.platform.monitoring_metrics_router",
        router_name="logs_router",
        prefix="/api/v1/logs",
        tags=["Logs"],
        description="Application logs and error monitoring",
        requires_auth=True,
    ),
    RouterConfig(
        module_path="dotmac.platform.monitoring_metrics_router",
        router_name="metrics_router",
        prefix="/api/v1/metrics",
        tags=["Metrics"],
        description="Performance and resource metrics",
        requires_auth=True,
    ),
]


def _register_router(app: FastAPI, config: RouterConfig) -> bool:
    """Register a single router with the application.

    Args:
        app: FastAPI application instance
        config: Router configuration

    Returns:
        True if registration successful, False otherwise.
    """
    try:
        # Dynamically import the module
        module = importlib.import_module(config.module_path)
        router = getattr(module, config.router_name)

        # Build kwargs for include_router
        kwargs = {
            "prefix": config.prefix,
            "tags": config.tags,
        }

        # Add auth dependency if required
        if config.requires_auth:
            kwargs["dependencies"] = [Depends(security)]

        # Register the router
        app.include_router(router, **kwargs)

        logger.info(f"✅ {config.description or config.tags[0]} registered at {config.prefix}")
        return True

    except ImportError as e:
        # Use debug level for optional routers
        if "user_management" in config.module_path:
            logger.debug(f"{config.description} not available: {e}")
        else:
            logger.warning(f"⚠️  {config.description} not available: {e}")
        return False
    except AttributeError as e:
        logger.error(f"❌ Router '{config.router_name}' not found in {config.module_path}: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Failed to register {config.description}: {e}")
        return False


def register_routers(app: FastAPI) -> None:
    """
    Register all API routers with the application.

    Structure:
    - /api/v1/* - REST API endpoints (auth required except /auth)
    - /health, /ready, /metrics - Public health endpoints
    """
    registered_count = 0
    failed_count = 0

    # Register all configured routers
    for config in ROUTER_CONFIGS:
        if _register_router(app, config):
            registered_count += 1
        else:
            failed_count += 1

    # GraphQL removed - using REST APIs only

    # Log summary
    logger.info(
        f"\n{'=' * 60}\n"
        f"🚀 Router Registration Complete\n"
        f"   ✅ Registered: {registered_count} routers\n"
        f"   ⚠️  Skipped: {failed_count} routers\n"
        f"{'=' * 60}"
    )


def get_api_info() -> Dict[str, Any]:
    """Get information about registered API endpoints.

    Returns:
        Dictionary containing API version, endpoints, and configuration.
    """
    # Build endpoints dict from router configs
    endpoints = {}
    for config in ROUTER_CONFIGS:
        # Extract endpoint name from prefix
        parts = config.prefix.replace("/api/v1/", "").split("/")
        if len(parts) == 1:
            endpoints[parts[0]] = config.prefix
        elif len(parts) == 2:
            # Nested endpoints like files/process
            if parts[0] not in endpoints:
                endpoints[parts[0]] = {}
            if isinstance(endpoints[parts[0]], dict):
                endpoints[parts[0]][parts[1]] = config.prefix

    # GraphQL removed - using REST APIs only

    return {
        "version": "v1",
        "base_path": "/api/v1",
        "endpoints": endpoints,
        "public_endpoints": [
            "/health",
            "/ready",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/auth/login",  # Login doesn't require auth
            "/api/v1/auth/register",  # Registration doesn't require auth
        ],
        "authenticated_endpoints": [
            config.prefix for config in ROUTER_CONFIGS if config.requires_auth
        ],
    }


def get_registered_routers() -> List[RouterConfig]:
    """Get list of all configured routers.

    Returns:
        List of RouterConfig objects.
    """
    return ROUTER_CONFIGS.copy()
