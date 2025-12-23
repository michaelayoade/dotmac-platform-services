"""
Centralized router registration for all API endpoints.

All routes except /health, /ready, and /metrics require authentication.
"""

import importlib
import os
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Any

import structlog
from fastapi import Depends, FastAPI
from fastapi.security import HTTPBearer

from dotmac.platform.auth.dependencies import get_current_user

logger = structlog.get_logger(__name__)


def _is_truthy_env(value: str | None) -> bool:
    return (value or "").lower() in {"1", "true", "yes", "on"}


_SKIP_BILLING: bool = _is_truthy_env(
    os.getenv("DOTMAC_SKIP_BILLING_MODELS") or os.getenv("DOTMAC_SKIP_PLATFORM_MODELS")
)

# Security scheme for Swagger UI (documentation only - NOT for actual auth)
# IMPORTANT: This only validates Bearer token format, not JWT validity
# Real authentication uses get_current_user which validates the JWT
security = HTTPBearer(auto_error=True)


@dataclass
class RouterConfig:
    """Configuration for a router to be registered."""

    module_path: str
    router_name: str
    prefix: str
    tags: Sequence[str | Enum] | None
    requires_auth: bool = True
    description: str = ""


# Define router configurations - Platform Services Only
ROUTER_CONFIGS = [
    # ===========================================
    # Health & Configuration
    # ===========================================
    RouterConfig(
        module_path="dotmac.platform.config.router",
        router_name="health_router",
        prefix="/api/v1",
        tags=["Health"],
        requires_auth=False,
        description="Health check endpoint at /api/v1/health",
    ),
    RouterConfig(
        module_path="dotmac.platform.config.router",
        router_name="router",
        prefix="/api/v1",
        tags=["Platform"],
        requires_auth=False,
        description="Platform configuration and health endpoints",
    ),
    # ===========================================
    # Authentication & Authorization
    # ===========================================
    RouterConfig(
        module_path="dotmac.platform.auth.router",
        router_name="auth_router",
        prefix="/api/v1",
        tags=["Authentication"],
        requires_auth=False,
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
        module_path="dotmac.platform.auth.rbac_router",
        router_name="router",
        prefix="/api/v1/auth/rbac/admin",
        tags=["RBAC - Admin"],
        requires_auth=True,
        description="RBAC admin endpoints (create/update/delete roles and permissions)",
    ),
    RouterConfig(
        module_path="dotmac.platform.auth.platform_admin_router",
        router_name="router",
        prefix="/api/v1/admin/platform",
        tags=["Platform Administration"],
        requires_auth=True,
        description="Cross-tenant platform administration (super admin only)",
    ),
    RouterConfig(
        module_path="dotmac.platform.auth.platform_admin_router",
        router_name="router",
        prefix="/api/v1/platform-admin",
        tags=["Platform Administration"],
        requires_auth=True,
        description="Legacy platform administration path (deprecated)",
    ),
    RouterConfig(
        module_path="dotmac.platform.platform_admin",
        router_name="router",
        prefix="/api/v1",
        tags=["Platform Admin - Cross-Tenant"],
        requires_auth=True,
        description="Cross-tenant data access for platform administrators",
    ),
    RouterConfig(
        module_path="dotmac.platform.auth.api_keys_router",
        router_name="router",
        prefix="/api/v1",
        tags=["API Keys"],
        requires_auth=True,
        description="API key management",
    ),
    RouterConfig(
        module_path="dotmac.platform.auth.metrics_router",
        router_name="router",
        prefix="/api/v1",
        tags=["Auth Metrics"],
        description="Authentication and security metrics",
        requires_auth=True,
    ),
    RouterConfig(
        module_path="dotmac.platform.auth.api_keys_metrics_router",
        router_name="router",
        prefix="/api/v1",
        tags=["API Keys Metrics"],
        description="API key metrics",
        requires_auth=True,
    ),
    # ===========================================
    # User & Team Management
    # ===========================================
    RouterConfig(
        module_path="dotmac.platform.user_management.router",
        router_name="user_router",
        prefix="/api/v1",
        tags=["User Management"],
        requires_auth=True,
        description="User management endpoints",
    ),
    RouterConfig(
        module_path="dotmac.platform.user_management.team_router",
        router_name="router",
        prefix="/api/v1",
        tags=["Team Management"],
        description="Team and team member management",
        requires_auth=True,
    ),
    # ===========================================
    # Tenant Management
    # ===========================================
    RouterConfig(
        module_path="dotmac.platform.tenant.router",
        router_name="router",
        prefix="/api/v1",
        tags=["Tenant Management"],
        description="Multi-tenant organization management",
        requires_auth=True,
    ),
    RouterConfig(
        module_path="dotmac.platform.tenant.router",
        router_name="legacy_router",
        prefix="/api/v1",
        tags=["Tenant Management"],
        description="Legacy tenant endpoints (singular prefix)",
        requires_auth=True,
    ),
    RouterConfig(
        module_path="dotmac.platform.tenant.onboarding_router",
        router_name="router",
        prefix="/api/v1",
        tags=["Tenant Onboarding"],
        description="Tenant onboarding automation",
        requires_auth=True,
    ),
    RouterConfig(
        module_path="dotmac.platform.tenant.domain_verification_router",
        router_name="router",
        prefix="/api/v1",
        tags=["Tenant - Domain Verification"],
        description="Custom domain verification for tenants",
        requires_auth=True,
    ),
    RouterConfig(
        module_path="dotmac.platform.tenant.usage_billing_router",
        router_name="router",
        prefix="/api/v1/tenants",
        tags=["Tenant Usage Billing"],
        description="Usage tracking and billing integration",
        requires_auth=True,
    ),
    RouterConfig(
        module_path="dotmac.platform.tenant.portal_router",
        router_name="router",
        prefix="/api/v1/tenants",
        tags=["Tenant Portal"],
        description="Tenant self-service portal",
        requires_auth=True,
    ),
    # ===========================================
    # Billing & Payments
    # ===========================================
    RouterConfig(
        module_path="dotmac.platform.billing.router",
        router_name="router",
        prefix="/api/v1",
        tags=["Billing"],
        requires_auth=True,
        description="Billing and payment management",
    ),
    RouterConfig(
        module_path="dotmac.platform.billing.catalog.router",
        router_name="router",
        prefix="/api/v1/billing/catalog",
        tags=["Billing - Catalog"],
        description="Product catalog management",
        requires_auth=True,
    ),
    RouterConfig(
        module_path="dotmac.platform.billing.subscriptions.router",
        router_name="router",
        prefix="/api/v1",
        tags=["Billing - Subscriptions"],
        description="Subscription management",
        requires_auth=True,
    ),
    RouterConfig(
        module_path="dotmac.platform.billing.pricing.router",
        router_name="router",
        prefix="/api/v1",
        tags=["Billing - Pricing"],
        description="Pricing engine and rules",
        requires_auth=True,
    ),
    RouterConfig(
        module_path="dotmac.platform.billing.bank_accounts.router",
        router_name="router",
        prefix="/api/v1",
        tags=["Billing - Bank Accounts"],
        description="Bank accounts and manual payments",
        requires_auth=True,
    ),
    RouterConfig(
        module_path="dotmac.platform.billing.settings.router",
        router_name="router",
        prefix="/api/v1/billing",
        tags=["Billing - Settings"],
        description="Billing configuration and settings",
        requires_auth=True,
    ),
    RouterConfig(
        module_path="dotmac.platform.billing.reconciliation_router",
        router_name="router",
        prefix="/api/v1/billing",
        tags=["Billing - Reconciliation"],
        description="Payment reconciliation and recovery",
        requires_auth=True,
    ),
    RouterConfig(
        module_path="dotmac.platform.billing.dunning.router",
        router_name="router",
        prefix="/api/v1",
        tags=["Billing - Dunning"],
        description="Dunning and collections management",
        requires_auth=True,
    ),
    RouterConfig(
        module_path="dotmac.platform.billing.invoicing.router",
        router_name="router",
        prefix="/api/v1/billing",
        tags=["Billing - Invoices"],
        description="Invoice creation and management",
        requires_auth=True,
    ),
    RouterConfig(
        module_path="dotmac.platform.billing.invoicing.money_router",
        router_name="router",
        prefix="/api/v1/billing/invoices",
        tags=["Billing - Invoices (Money)"],
        description="Money-based invoice operations with PDF generation",
        requires_auth=True,
    ),
    RouterConfig(
        module_path="dotmac.platform.billing.payments.router",
        router_name="router",
        prefix="/api/v1/billing",
        tags=["Billing - Payments"],
        description="Payment processing and tracking",
        requires_auth=True,
    ),
    RouterConfig(
        module_path="dotmac.platform.billing.receipts.router",
        router_name="router",
        prefix="/api/v1/billing",
        tags=["Billing - Receipts"],
        description="Payment receipts and documentation",
        requires_auth=True,
    ),
    RouterConfig(
        module_path="dotmac.platform.billing.credit_notes.router",
        router_name="router",
        prefix="/api/v1/billing",
        tags=["Billing - Credit Notes"],
        description="Credit notes and refunds",
        requires_auth=True,
    ),
    RouterConfig(
        module_path="dotmac.platform.billing.webhooks.router",
        router_name="router",
        prefix="/api/v1/billing",
        tags=["Billing - Webhooks"],
        description="Billing webhook handlers (Stripe, etc.)",
        requires_auth=False,
    ),
    RouterConfig(
        module_path="dotmac.platform.billing.metrics_router",
        router_name="router",
        prefix="/api/v1",
        tags=["Billing Metrics"],
        description="Billing overview metrics (MRR, ARR, invoices, payments)",
        requires_auth=True,
    ),
    RouterConfig(
        module_path="dotmac.platform.billing.metrics_router",
        router_name="customer_metrics_router",
        prefix="/api/v1",
        tags=["Customer Metrics"],
        description="Customer metrics with growth and churn analysis",
        requires_auth=True,
    ),
    # ===========================================
    # Licensing
    # ===========================================
    RouterConfig(
        module_path="dotmac.platform.licensing.router",
        router_name="router",
        prefix="",
        tags=["Licensing"],
        description="Software licensing, activation, and compliance management",
        requires_auth=True,
    ),
    RouterConfig(
        module_path="dotmac.platform.licensing.router_framework",
        router_name="router",
        prefix="/api/v1",
        tags=["Licensing Framework"],
        description="Composable licensing with dynamic plan builder",
        requires_auth=True,
    ),
    # ===========================================
    # Customer Management
    # ===========================================
    RouterConfig(
        module_path="dotmac.platform.customer_management.router",
        router_name="router",
        prefix="/api/v1/customers",
        tags=["Customer Management"],
        requires_auth=True,
        description="Customer relationship management",
    ),
    RouterConfig(
        module_path="dotmac.platform.contacts.router",
        router_name="router",
        prefix="/api/v1",
        tags=["Contacts"],
        requires_auth=True,
        description="Contact management system",
    ),
    # ===========================================
    # Communications
    # ===========================================
    RouterConfig(
        module_path="dotmac.platform.communications.router",
        router_name="router",
        prefix="/api/v1",
        tags=["Communications"],
        requires_auth=True,
        description="Communications API with email, templates, and background tasks",
    ),
    RouterConfig(
        module_path="dotmac.platform.communications.metrics_router",
        router_name="router",
        prefix="/api/v1",
        tags=["Communications Metrics"],
        description="Communication stats (emails, SMS, delivery rates)",
        requires_auth=True,
    ),
    RouterConfig(
        module_path="dotmac.platform.notifications.router",
        router_name="router",
        prefix="/api/v1",
        tags=["Notifications"],
        description="User notifications and preferences",
        requires_auth=True,
    ),
    RouterConfig(
        module_path="dotmac.platform.push.router",
        router_name="router",
        prefix="",
        tags=["Push Notifications"],
        description="PWA push notification subscriptions and sending",
        requires_auth=True,
    ),
    # ===========================================
    # Ticketing & Support
    # ===========================================
    RouterConfig(
        module_path="dotmac.platform.ticketing.router",
        router_name="router",
        prefix="/api/v1",
        tags=["Ticketing"],
        description="Cross-organization ticketing workflows",
        requires_auth=True,
    ),
    RouterConfig(
        module_path="dotmac.platform.ticketing.availability_router",
        router_name="router",
        prefix="/api/v1",
        tags=["Agent Availability"],
        description="Agent availability status management",
        requires_auth=True,
    ),
    # ===========================================
    # Partner Management
    # ===========================================
    RouterConfig(
        module_path="dotmac.platform.partner_management.router",
        router_name="router",
        prefix="/api/v1",
        tags=["Partner Management"],
        description="Partner relationship management",
        requires_auth=True,
    ),
    RouterConfig(
        module_path="dotmac.platform.partner_management.portal_router",
        router_name="router",
        prefix="/api/v1/partners",
        tags=["Partner Portal"],
        description="Partner self-service portal",
        requires_auth=True,
    ),
    RouterConfig(
        module_path="dotmac.platform.partner_management.revenue_router",
        router_name="router",
        prefix="/api/v1/partners",
        tags=["Partner Revenue"],
        description="Partner revenue sharing and commissions",
        requires_auth=True,
    ),
    RouterConfig(
        module_path="dotmac.platform.partner_management.partner_multitenant_router",
        router_name="router",
        prefix="/api/v1",
        tags=["Partner Multi-Tenant"],
        description="Partner multi-tenant account management (MSP/Enterprise HQ)",
        requires_auth=True,
    ),
    # ===========================================
    # Analytics & Metrics
    # ===========================================
    RouterConfig(
        module_path="dotmac.platform.analytics.router",
        router_name="analytics_router",
        prefix="/api/v1",
        tags=["Analytics"],
        requires_auth=True,
        description="Analytics and metrics endpoints",
    ),
    RouterConfig(
        module_path="dotmac.platform.analytics.metrics_router",
        router_name="router",
        prefix="/api/v1",
        tags=["Analytics Activity"],
        description="Analytics activity stats (events, user activity, API usage)",
        requires_auth=True,
    ),
    # ===========================================
    # Monitoring & Observability
    # ===========================================
    RouterConfig(
        module_path="dotmac.platform.monitoring.logs_router",
        router_name="logs_router",
        prefix="/api/v1",
        tags=["Monitoring - Logs"],
        description="Application logs with filtering and search",
        requires_auth=True,
    ),
    RouterConfig(
        module_path="dotmac.platform.monitoring.infrastructure_router",
        router_name="router",
        prefix="/api/v1",
        tags=["Monitoring - Compatibility"],
        description="Frontend-friendly monitoring aliases (metrics, infrastructure)",
        requires_auth=True,
    ),
    RouterConfig(
        module_path="dotmac.platform.monitoring.traces_router",
        router_name="traces_router",
        prefix="/api/v1",
        tags=["Observability - Traces"],
        description="Distributed traces, metrics, and performance data",
        requires_auth=True,
    ),
    RouterConfig(
        module_path="dotmac.platform.monitoring.alert_router",
        router_name="router",
        prefix="/api/v1/monitoring",
        tags=["Monitoring - Alerts"],
        description="Alert webhook receiver and channel management",
        requires_auth=False,
    ),
    RouterConfig(
        module_path="dotmac.platform.monitoring.metrics_router",
        router_name="router",
        prefix="/api/v1",
        tags=["Monitoring Metrics"],
        description="Monitoring metrics (system health, performance, logs)",
        requires_auth=True,
    ),
    RouterConfig(
        module_path="dotmac.platform.monitoring_metrics_router",
        router_name="logs_router",
        prefix="/api/v1",
        tags=["Logs"],
        description="Application logs and error monitoring",
        requires_auth=True,
    ),
    RouterConfig(
        module_path="dotmac.platform.monitoring_metrics_router",
        router_name="metrics_router",
        prefix="/api/v1",
        tags=["Metrics"],
        description="Performance and resource metrics",
        requires_auth=True,
    ),
    # ===========================================
    # Audit & Security
    # ===========================================
    RouterConfig(
        module_path="dotmac.platform.audit.router",
        router_name="router",
        prefix="/api/v1",
        tags=["Audit"],
        requires_auth=True,
        description="Audit trails and activity tracking",
    ),
    RouterConfig(
        module_path="dotmac.platform.audit.router",
        router_name="public_router",
        prefix="/api/v1",
        tags=["Audit - Public"],
        requires_auth=False,
        description="Public audit endpoints (frontend error logging with rate limiting)",
    ),
    RouterConfig(
        module_path="dotmac.platform.secrets.api",
        router_name="router",
        prefix="/api/v1/secrets",
        tags=["Secrets Management"],
        requires_auth=True,
        description="Vault/OpenBao secrets management",
    ),
    RouterConfig(
        module_path="dotmac.platform.secrets.metrics_router",
        router_name="router",
        prefix="/api/v1",
        tags=["Secrets Metrics"],
        description="Secrets metrics (access patterns, security)",
        requires_auth=True,
    ),
    # ===========================================
    # File Storage & Data
    # ===========================================
    RouterConfig(
        module_path="dotmac.platform.file_storage.router",
        router_name="file_storage_router",
        prefix="/api/v1",
        tags=["File Storage"],
        requires_auth=True,
        description="File storage management",
    ),
    RouterConfig(
        module_path="dotmac.platform.file_storage.metrics_router",
        router_name="router",
        prefix="/api/v1",
        tags=["File Storage Metrics"],
        description="File storage stats (uploads, storage usage, file types)",
        requires_auth=True,
    ),
    RouterConfig(
        module_path="dotmac.platform.search.router",
        router_name="search_router",
        prefix="/api/v1/search",
        tags=["Search"],
        requires_auth=True,
        description="Search functionality",
    ),
    RouterConfig(
        module_path="dotmac.platform.data_transfer.router",
        router_name="data_transfer_router",
        prefix="/api/v1",
        tags=["Data Transfer"],
        requires_auth=True,
        description="Data import/export operations",
    ),
    RouterConfig(
        module_path="dotmac.platform.data_import.router",
        router_name="router",
        prefix="/api/v1",
        tags=["Data Import"],
        requires_auth=True,
        description="File-based data import operations (CSV, JSON)",
    ),
    # ===========================================
    # Webhooks & Integrations
    # ===========================================
    RouterConfig(
        module_path="dotmac.platform.webhooks.router",
        router_name="router",
        prefix="/api/v1",
        tags=["Webhooks"],
        description="Generic webhook subscription and event management",
        requires_auth=True,
    ),
    RouterConfig(
        module_path="dotmac.platform.integrations.router",
        router_name="integrations_router",
        prefix="/api/v1",
        tags=["Integrations"],
        description="External service integrations (Email, SMS, Storage, etc.)",
        requires_auth=True,
    ),
    # ===========================================
    # Feature Flags & Plugins
    # ===========================================
    RouterConfig(
        module_path="dotmac.platform.feature_flags.router",
        router_name="feature_flags_router",
        prefix="/api/v1",
        tags=["Feature Flags"],
        requires_auth=True,
        description="Feature flags management",
    ),
    RouterConfig(
        module_path="dotmac.platform.plugins.router",
        router_name="router",
        prefix="/api/v1/plugins",
        tags=["Plugin Management"],
        requires_auth=True,
        description="Dynamic plugin system management",
    ),
    # ===========================================
    # Jobs & Workflows
    # ===========================================
    RouterConfig(
        module_path="dotmac.platform.jobs.router",
        router_name="router",
        prefix="/api/v1",
        tags=["Jobs"],
        description="Async job tracking and management",
        requires_auth=True,
    ),
    RouterConfig(
        module_path="dotmac.platform.jobs.scheduler_router",
        router_name="router",
        prefix="/api/v1",
        tags=["Job Scheduler"],
        description="Scheduled jobs and job chain management",
        requires_auth=True,
    ),
    RouterConfig(
        module_path="dotmac.platform.workflows.router",
        router_name="router",
        prefix="/api/v1",
        tags=["Workflows"],
        description="Workflow orchestration and automation",
        requires_auth=True,
    ),
    RouterConfig(
        module_path="dotmac.platform.workflows.metrics_router",
        router_name="router",
        prefix="/api/v1",
        tags=["Workflow Metrics"],
        description="Workflow services metrics (operations, performance, errors)",
        requires_auth=True,
    ),
    # ===========================================
    # Real-time & Rate Limiting
    # ===========================================
    RouterConfig(
        module_path="dotmac.platform.rate_limit.router",
        router_name="router",
        prefix="/api/v1",
        tags=["Rate Limiting"],
        description="Rate limit rule management and monitoring",
        requires_auth=True,
    ),
    # ===========================================
    # Admin & Deployment
    # ===========================================
    RouterConfig(
        module_path="dotmac.platform.admin.settings.router",
        router_name="router",
        prefix="/api/v1/admin/settings",
        tags=["Admin - Settings"],
        description="Platform settings management (admin only)",
        requires_auth=True,
    ),
    RouterConfig(
        module_path="dotmac.platform.deployment.router",
        router_name="router",
        prefix="/api/v1",
        tags=["Deployment Orchestration"],
        description="Multi-tenant deployment provisioning and lifecycle management",
        requires_auth=True,
    ),
    # ===========================================
    # Public Catalog (No Auth Required)
    # ===========================================
    RouterConfig(
        module_path="dotmac.platform.platform_products.catalog_router",
        router_name="router",
        prefix="/api/v1",
        tags=["Public Catalog"],
        requires_auth=False,
        description="Public product catalog for marketing and signup pages",
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

        # Add auth dependency if required
        # CRITICAL: Use get_current_user for real JWT validation, not bare HTTPBearer
        # HTTPBearer only checks for Authorization header presence, not JWT validity
        dependencies = [Depends(get_current_user)] if config.requires_auth else None

        # Register the router with proper typing
        router_tags = list(config.tags) if config.tags is not None else None

        app.include_router(
            router,
            prefix=config.prefix,
            tags=router_tags,
            dependencies=dependencies,
        )

        tag_label = config.description or (config.tags[0] if config.tags else config.module_path)
        logger.info(f"✅ {tag_label} registered at {config.prefix}")
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
    skipped_count = 0

    # Register all configured routers
    for config in ROUTER_CONFIGS:
        if _SKIP_BILLING and "billing" in config.module_path:
            logger.info(
                "Skipping billing router due to DOTMAC_SKIP_BILLING_MODELS/DOTMAC_SKIP_PLATFORM_MODELS",
                module=config.module_path,
            )
            skipped_count += 1
            continue

        if _register_router(app, config):
            registered_count += 1
        else:
            failed_count += 1

    # Log summary
    logger.info(
        f"\n{'=' * 60}\n"
        f"🚀 Router Registration Complete\n"
        f"   ✅ Registered: {registered_count} routers\n"
        f"   ⚠️  Skipped: {skipped_count} routers\n"
        f"   ❌ Failed: {failed_count} routers\n"
        f"{'=' * 60}"
    )


def get_api_info() -> dict[str, Any]:
    """Get information about registered API endpoints.

    Returns:
        Dictionary containing API version, endpoints, and configuration.
    """
    # Build endpoints dict from router configs
    endpoints: dict[str, str | dict[str, str]] = {}
    for config in ROUTER_CONFIGS:
        # Extract endpoint name from prefix
        prefix = config.prefix
        if not prefix.startswith("/api/v1"):
            continue

        trimmed = prefix.replace("/api/v1/", "", 1).lstrip("/")
        if not trimmed:
            continue

        parts = trimmed.split("/")

        if len(parts) == 1:
            endpoints[parts[0]] = prefix
        elif len(parts) >= 2:
            top_key = parts[0]
            nested = endpoints.get(top_key)

            nested_dict: dict[str, str]
            if isinstance(nested, dict):
                nested_dict = nested
            else:
                nested_dict = {}
                if isinstance(nested, str):
                    nested_dict["_self"] = nested

            nested_dict[parts[1]] = prefix
            endpoints[top_key] = nested_dict

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
            "/api/v1/auth/login",
            "/api/v1/auth/register",
        ],
        "authenticated_endpoints": [
            config.prefix for config in ROUTER_CONFIGS if config.requires_auth
        ],
    }


def get_registered_routers() -> list[RouterConfig]:
    """Get list of all configured routers.

    Returns:
        List of RouterConfig objects.
    """
    return ROUTER_CONFIGS.copy()
