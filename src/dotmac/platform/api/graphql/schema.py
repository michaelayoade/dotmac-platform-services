"""Comprehensive GraphQL schema definitions for the DotMac platform."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from dotmac.platform.observability.unified_logging import get_logger

logger = get_logger(__name__)

try:  # pragma: no cover - optional dependency import
    import strawberry
    from strawberry.types import Info
except ImportError:  # pragma: no cover - graceful fallback when Strawberry not installed
    strawberry = None  # type: ignore[assignment]
    logger.info(
        "Strawberry not installed; GraphQL endpoint will remain disabled unless the dependency is provided."
    )

if strawberry:  # pragma: no branch - executed only when strawberry is available
    from .resolvers import (
        AuthResolver,
        FeatureFlagResolver,
        SecretsResolver,
        ObservabilityResolver,
        AuditTrailResolver,
        ServiceRegistryResolver,
    )

    # ===============================
    # Core Types
    # ===============================

    @strawberry.type
    class HealthInfo:
        """System health status information."""
        status: str
        version: str
        timestamp: datetime
        services: List[str]

    @strawberry.type
    class PageInfo:
        """Pagination information."""
        has_next_page: bool
        has_previous_page: bool
        start_cursor: Optional[str]
        end_cursor: Optional[str]
        total_count: int

    # ===============================
    # Authentication & Authorization
    # ===============================

    @strawberry.type
    class User:
        """User information."""
        id: str
        username: Optional[str]
        email: Optional[str]
        full_name: Optional[str]
        tenant_id: Optional[str]
        roles: List[str]
        scopes: List[str]
        is_active: bool
        created_at: datetime
        last_login: Optional[datetime]

    @strawberry.type
    class APIKey:
        """API key information."""
        id: str
        name: str
        prefix: str
        scopes: List[str]
        expires_at: Optional[datetime]
        created_at: datetime
        last_used: Optional[datetime]
        is_active: bool

    @strawberry.type
    class Session:
        """User session information."""
        id: str
        user_id: str
        ip_address: Optional[str]
        user_agent: Optional[str]
        created_at: datetime
        expires_at: datetime
        is_active: bool

    # ===============================
    # Feature Flags
    # ===============================

    @strawberry.enum
    class RolloutStrategy(strawberry.Enum):
        ALL_ON = "all_on"
        ALL_OFF = "all_off"
        PERCENTAGE = "percentage"
        USER_LIST = "user_list"
        TENANT_LIST = "tenant_list"
        GRADUAL = "gradual"
        AB_TEST = "ab_test"
        CANARY = "canary"

    @strawberry.type
    class FeatureFlag:
        """Feature flag definition."""
        key: str
        name: str
        description: Optional[str]
        enabled: bool
        strategy: RolloutStrategy
        config: Dict[str, Any]
        created_at: datetime
        updated_at: datetime
        created_by: str

    @strawberry.type
    class FeatureFlagEvaluation:
        """Feature flag evaluation result."""
        flag_key: str
        enabled: bool
        variant: Optional[str]
        reason: str
        context: Dict[str, Any]

    # ===============================
    # Secrets Management
    # ===============================

    @strawberry.type
    class SecretMetadata:
        """Secret metadata (no sensitive data)."""
        path: str
        version: int
        created_at: datetime
        updated_at: datetime
        tags: Dict[str, str]
        description: Optional[str]

    @strawberry.type
    class SecretHistory:
        """Secret version history."""
        version: int
        created_at: datetime
        created_by: str
        description: Optional[str]

    # ===============================
    # Observability
    # ===============================

    @strawberry.type
    class MetricValue:
        """Metric data point."""
        timestamp: datetime
        value: float
        labels: Dict[str, str]

    @strawberry.type
    class Metric:
        """Metric definition and recent values."""
        name: str
        description: Optional[str]
        type: str  # counter, gauge, histogram
        unit: Optional[str]
        recent_values: List[MetricValue]

    @strawberry.type
    class TraceSpan:
        """Distributed trace span information."""
        trace_id: str
        span_id: str
        parent_span_id: Optional[str]
        operation_name: str
        start_time: datetime
        end_time: datetime
        duration_ms: float
        status: str
        tags: Dict[str, str]

    @strawberry.type
    class HealthCheck:
        """Service health check result."""
        service_name: str
        status: str  # healthy, unhealthy, unknown
        message: Optional[str]
        last_check: datetime
        response_time_ms: float

    # ===============================
    # Audit Trail
    # ===============================

    @strawberry.enum
    class AuditCategory(strawberry.Enum):
        AUTHENTICATION = "authentication"
        AUTHORIZATION = "authorization"
        DATA_ACCESS = "data_access"
        SECURITY_EVENT = "security_event"
        USER_MANAGEMENT = "user_management"
        SYSTEM_CHANGE = "system_change"

    @strawberry.enum
    class AuditLevel(strawberry.Enum):
        DEBUG = "debug"
        INFO = "info"
        WARNING = "warning"
        ERROR = "error"
        CRITICAL = "critical"

    @strawberry.type
    class AuditEvent:
        """Audit trail event."""
        id: str
        timestamp: datetime
        category: AuditCategory
        level: AuditLevel
        action: str
        resource: str
        actor: str
        tenant_id: Optional[str]
        ip_address: Optional[str]
        user_agent: Optional[str]
        details: Dict[str, Any]
        outcome: str  # success, failure, denied

    # ===============================
    # Service Registry
    # ===============================

    @strawberry.enum
    class ServiceStatus(strawberry.Enum):
        HEALTHY = "healthy"
        UNHEALTHY = "unhealthy"
        UNKNOWN = "unknown"
        STARTING = "starting"
        STOPPING = "stopping"

    @strawberry.type
    class ServiceInstance:
        """Registered service instance."""
        id: str
        name: str
        version: str
        status: ServiceStatus
        endpoint: str
        health_check_url: Optional[str]
        tags: Dict[str, str]
        metadata: Dict[str, Any]
        registered_at: datetime
        last_heartbeat: datetime

    # ===============================
    # Pagination
    # ===============================

    @strawberry.type
    class AuditEventsConnection:
        """Paginated audit events."""
        nodes: List[AuditEvent]
        page_info: PageInfo

    @strawberry.type
    class FeatureFlagsConnection:
        """Paginated feature flags."""
        nodes: List[FeatureFlag]
        page_info: PageInfo

    @strawberry.type
    class ServiceInstancesConnection:
        """Paginated service instances."""
        nodes: List[ServiceInstance]
        page_info: PageInfo

    # ===============================
    # Input Types
    # ===============================

    @strawberry.input
    class FeatureFlagInput:
        """Input for creating/updating feature flags."""
        key: str
        name: str
        description: Optional[str] = None
        enabled: bool = False
        strategy: RolloutStrategy = RolloutStrategy.ALL_OFF
        config: Dict[str, Any] = strawberry.field(default_factory=dict)

    @strawberry.input
    class AuditEventFilter:
        """Filter for audit events query."""
        category: Optional[AuditCategory] = None
        level: Optional[AuditLevel] = None
        actor: Optional[str] = None
        resource: Optional[str] = None
        start_time: Optional[datetime] = None
        end_time: Optional[datetime] = None

    @strawberry.input
    class MetricsFilter:
        """Filter for metrics query."""
        name_pattern: Optional[str] = None
        labels: Optional[Dict[str, str]] = None
        start_time: Optional[datetime] = None
        end_time: Optional[datetime] = None

    # ===============================
    # Root Query Type
    # ===============================

    @strawberry.type
    class Query:
        """Root GraphQL query type."""

        @strawberry.field(description="System health information.")
        async def health(self) -> HealthInfo:
            """Get system health status."""
            return HealthInfo(
                status="ok",
                version="1.0.0",
                timestamp=datetime.utcnow(),
                services=["auth", "secrets", "observability", "audit", "registry"]
            )

        # ===============================
        # Authentication & Authorization
        # ===============================

        @strawberry.field(description="Get current user information.")
        async def current_user(self, info: Info) -> Optional[User]:
            """Get the currently authenticated user."""
            return await AuthResolver.get_current_user(info)

        @strawberry.field(description="List user's API keys.")
        async def api_keys(self, info: Info) -> List[APIKey]:
            """Get API keys for the current user."""
            return await AuthResolver.get_api_keys(info)

        @strawberry.field(description="Get user sessions.")
        async def sessions(self, info: Info, user_id: Optional[str] = None) -> List[Session]:
            """Get user sessions."""
            return await AuthResolver.get_sessions(info, user_id)

        # ===============================
        # Feature Flags
        # ===============================

        @strawberry.field(description="Get all feature flags.")
        async def feature_flags(
            self,
            info: Info,
            first: Optional[int] = 50,
            after: Optional[str] = None
        ) -> FeatureFlagsConnection:
            """List feature flags with pagination."""
            return await FeatureFlagResolver.get_feature_flags(info, first, after)

        @strawberry.field(description="Get a specific feature flag.")
        async def feature_flag(self, info: Info, key: str) -> Optional[FeatureFlag]:
            """Get a feature flag by key."""
            return await FeatureFlagResolver.get_feature_flag(info, key)

        @strawberry.field(description="Evaluate feature flags for current user.")
        async def evaluate_flags(
            self,
            info: Info,
            flags: List[str],
            context: Optional[Dict[str, Any]] = None
        ) -> List[FeatureFlagEvaluation]:
            """Evaluate multiple feature flags."""
            return await FeatureFlagResolver.evaluate_flags(info, flags, context or {})

        # ===============================
        # Secrets Management
        # ===============================

        @strawberry.field(description="List secret metadata.")
        async def secrets(
            self,
            info: Info,
            path_prefix: Optional[str] = None
        ) -> List[SecretMetadata]:
            """List secrets metadata (no values)."""
            return await SecretsResolver.list_secrets(info, path_prefix)

        @strawberry.field(description="Get secret history.")
        async def secret_history(self, info: Info, path: str) -> List[SecretHistory]:
            """Get version history for a secret."""
            return await SecretsResolver.get_secret_history(info, path)

        # ===============================
        # Observability
        # ===============================

        @strawberry.field(description="Get system metrics.")
        async def metrics(
            self,
            info: Info,
            filter: Optional[MetricsFilter] = None
        ) -> List[Metric]:
            """Get system metrics."""
            return await ObservabilityResolver.get_metrics(info, filter)

        @strawberry.field(description="Get health checks.")
        async def health_checks(self, info: Info) -> List[HealthCheck]:
            """Get service health checks."""
            return await ObservabilityResolver.get_health_checks(info)

        @strawberry.field(description="Get recent traces.")
        async def traces(
            self,
            info: Info,
            service_name: Optional[str] = None,
            limit: Optional[int] = 100
        ) -> List[TraceSpan]:
            """Get recent trace spans."""
            return await ObservabilityResolver.get_traces(info, service_name, limit)

        # ===============================
        # Audit Trail
        # ===============================

        @strawberry.field(description="Search audit events.")
        async def audit_events(
            self,
            info: Info,
            filter: Optional[AuditEventFilter] = None,
            first: Optional[int] = 50,
            after: Optional[str] = None
        ) -> AuditEventsConnection:
            """Search audit events with pagination."""
            return await AuditTrailResolver.search_events(info, filter, first, after)

        @strawberry.field(description="Get audit event by ID.")
        async def audit_event(self, info: Info, event_id: str) -> Optional[AuditEvent]:
            """Get a specific audit event."""
            return await AuditTrailResolver.get_event(info, event_id)

        # ===============================
        # Service Registry
        # ===============================

        @strawberry.field(description="List registered services.")
        async def services(
            self,
            info: Info,
            status: Optional[ServiceStatus] = None,
            first: Optional[int] = 50,
            after: Optional[str] = None
        ) -> ServiceInstancesConnection:
            """List registered service instances."""
            return await ServiceRegistryResolver.get_services(info, status, first, after)

        @strawberry.field(description="Get service by ID.")
        async def service(self, info: Info, service_id: str) -> Optional[ServiceInstance]:
            """Get a specific service instance."""
            return await ServiceRegistryResolver.get_service(info, service_id)

    # ===============================
    # Root Mutation Type
    # ===============================

    @strawberry.type
    class Mutation:
        """Root GraphQL mutation type."""

        # ===============================
        # Authentication
        # ===============================

        @strawberry.field(description="Create a new API key.")
        async def create_api_key(
            self,
            info: Info,
            name: str,
            scopes: List[str],
            expires_at: Optional[datetime] = None
        ) -> APIKey:
            """Create a new API key."""
            return await AuthResolver.create_api_key(info, name, scopes, expires_at)

        @strawberry.field(description="Revoke an API key.")
        async def revoke_api_key(self, info: Info, api_key_id: str) -> bool:
            """Revoke an API key."""
            return await AuthResolver.revoke_api_key(info, api_key_id)

        @strawberry.field(description="Invalidate user session.")
        async def invalidate_session(self, info: Info, session_id: str) -> bool:
            """Invalidate a user session."""
            return await AuthResolver.invalidate_session(info, session_id)

        # ===============================
        # Feature Flags
        # ===============================

        @strawberry.field(description="Create or update a feature flag.")
        async def upsert_feature_flag(
            self,
            info: Info,
            input: FeatureFlagInput
        ) -> FeatureFlag:
            """Create or update a feature flag."""
            return await FeatureFlagResolver.upsert_feature_flag(info, input)

        @strawberry.field(description="Delete a feature flag.")
        async def delete_feature_flag(self, info: Info, key: str) -> bool:
            """Delete a feature flag."""
            return await FeatureFlagResolver.delete_feature_flag(info, key)

        @strawberry.field(description="Toggle a feature flag.")
        async def toggle_feature_flag(self, info: Info, key: str, enabled: bool) -> FeatureFlag:
            """Toggle a feature flag on/off."""
            return await FeatureFlagResolver.toggle_feature_flag(info, key, enabled)

        # ===============================
        # Audit Trail
        # ===============================

        @strawberry.field(description="Log an audit event.")
        async def log_audit_event(
            self,
            info: Info,
            category: AuditCategory,
            level: AuditLevel,
            action: str,
            resource: str,
            details: Optional[Dict[str, Any]] = None
        ) -> AuditEvent:
            """Log a new audit event."""
            return await AuditTrailResolver.log_event(
                info, category, level, action, resource, details or {}
            )

    # ===============================
    # Subscription Type
    # ===============================

    @strawberry.type
    class Subscription:
        """Root GraphQL subscription type for real-time updates."""

        @strawberry.subscription(description="Subscribe to audit events.")
        async def audit_events_stream(
            self,
            info: Info,
            filter: Optional[AuditEventFilter] = None
        ) -> AuditEvent:
            """Stream audit events in real-time."""
            async for event in AuditTrailResolver.stream_events(info, filter):
                yield event

        @strawberry.subscription(description="Subscribe to metrics updates.")
        async def metrics_stream(
            self,
            info: Info,
            metric_names: List[str]
        ) -> MetricValue:
            """Stream metric updates in real-time."""
            async for metric in ObservabilityResolver.stream_metrics(info, metric_names):
                yield metric

        @strawberry.subscription(description="Subscribe to service health changes.")
        async def service_health_stream(self, info: Info) -> HealthCheck:
            """Stream service health updates."""
            async for health in ServiceRegistryResolver.stream_health(info):
                yield health

    # Create the schema
    schema: Optional["strawberry.Schema"] = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        subscription=Subscription
    )

else:
    # Graceful fallback when strawberry is not available
    schema = None
    Query = None  # type: ignore[assignment]
    Mutation = None  # type: ignore[assignment]
    Subscription = None  # type: ignore[assignment]

__all__ = ["schema", "Query", "Mutation", "Subscription"]
