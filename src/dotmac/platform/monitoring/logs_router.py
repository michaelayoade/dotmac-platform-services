"""
Logs API router.

Provides REST endpoints for application log retrieval and filtering.
"""

from datetime import UTC, datetime
from enum import Enum

import structlog
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.audit.models import ActivitySeverity, AuditActivity
from dotmac.platform.auth.dependencies import CurrentUser, get_current_user
from dotmac.platform.db import get_session_dependency

logger = structlog.get_logger(__name__)


# ============================================================
# Models
# ============================================================


class LogLevel(str, Enum):
    """Log level enumeration."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogMetadata(BaseModel):
    """Log entry metadata."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="allow",
    )

    request_id: str | None = Field(None, description="Request correlation ID")
    user_id: str | None = Field(None, description="User ID")
    tenant_id: str | None = Field(None, description="Tenant ID")
    duration: int | None = Field(None, description="Duration in milliseconds")
    ip: str | None = Field(None, description="Client IP address")


class LogEntry(BaseModel):
    """Individual log entry."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    id: str = Field(description="Log entry ID")
    timestamp: datetime = Field(description="Log timestamp")
    level: LogLevel = Field(description="Log level")
    service: str = Field(description="Service name")
    message: str = Field(description="Log message")
    metadata: LogMetadata = Field(
        default_factory=lambda: LogMetadata(), description="Additional metadata"
    )


class LogsResponse(BaseModel):
    """Response for log queries."""

    model_config = ConfigDict(validate_assignment=True)

    logs: list[LogEntry] = Field(default_factory=list, description="Log entries")
    total: int = Field(description="Total number of matching logs")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Number of logs per page")
    has_more: bool = Field(description="Whether more logs are available")


class LogStats(BaseModel):
    """Log statistics."""

    total: int = Field(description="Total log count")
    by_level: dict[str, int] = Field(default_factory=dict, description="Count by log level")
    by_service: dict[str, int] = Field(default_factory=dict, description="Count by service")
    time_range: dict[str, str] = Field(default_factory=dict, description="Time range of logs")


# ============================================================
# Router
# ============================================================

logs_router = APIRouter()


# ============================================================
# Service Layer (Placeholder for now - will integrate with OpenTelemetry)
# ============================================================


class LogsService:
    """Service for fetching and filtering logs from audit activities."""

    def __init__(self, session: AsyncSession) -> None:
        self.logger = structlog.get_logger(__name__)
        self.session = session

    async def get_logs(
        self,
        level: LogLevel | None = None,
        service: str | None = None,
        search: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        page: int = 1,
        page_size: int = 100,
    ) -> LogsResponse:
        """Fetch logs from audit activities with filtering.

        Args:
            level: Filter by log level (maps to severity)
            service: Filter by service name (extracted from activity_type)
            search: Search in log messages
            start_time: Start of time range
            end_time: End of time range
            page: Page number (1-indexed)
            page_size: Number of logs per page

        Returns:
            LogsResponse with filtered logs from database
        """
        try:
            # Build query
            query = select(AuditActivity)

            # Apply filters
            if level:
                # Map log level to severity
                severity_map = {
                    LogLevel.DEBUG: ActivitySeverity.LOW,
                    LogLevel.INFO: ActivitySeverity.LOW,
                    LogLevel.WARNING: ActivitySeverity.MEDIUM,
                    LogLevel.ERROR: ActivitySeverity.HIGH,
                    LogLevel.CRITICAL: ActivitySeverity.CRITICAL,
                }
                severity = severity_map.get(level)
                if severity:
                    query = query.where(AuditActivity.severity == severity.value)

            if search:
                query = query.where(AuditActivity.description.ilike(f"%{search}%"))

            if start_time:
                query = query.where(AuditActivity.created_at >= start_time)

            if end_time:
                query = query.where(AuditActivity.created_at <= end_time)

            # Get total count
            count_query = select(func.count()).select_from(AuditActivity)
            if level or search or start_time or end_time:
                # Apply same filters for count
                count_query = select(func.count()).select_from(query.subquery())

            result = await self.session.execute(count_query)
            total = result.scalar() or 0

            # Apply pagination and ordering
            query = query.order_by(AuditActivity.created_at.desc())
            query = query.offset((page - 1) * page_size).limit(page_size)

            # Execute query
            result = await self.session.execute(query)
            activities = result.scalars().all()

            # Convert to LogEntry format
            logs = []
            for activity in activities:
                # Handle None values before validation
                if not activity:
                    continue

                # Map severity to log level
                level_map = {
                    ActivitySeverity.LOW.value: LogLevel.INFO,
                    ActivitySeverity.MEDIUM.value: LogLevel.WARNING,
                    ActivitySeverity.HIGH.value: LogLevel.ERROR,
                    ActivitySeverity.CRITICAL.value: LogLevel.CRITICAL,
                }
                log_level = level_map.get(activity.severity, LogLevel.INFO)

                # Extract service from activity_type (e.g., "user.login" -> "user")
                service_name = (
                    activity.activity_type.split(".")[0]
                    if activity.activity_type and "." in activity.activity_type
                    else "platform"
                )

                log_entry = LogEntry(
                    id=str(activity.id),
                    timestamp=activity.created_at,
                    level=log_level,
                    service=service_name,
                    message=activity.description or activity.activity_type or "",
                    metadata=LogMetadata(
                        user_id=activity.user_id,
                        tenant_id=str(activity.tenant_id) if activity.tenant_id else None,
                        ip=activity.ip_address,  # Use the ip_address field directly
                    ),
                )
                logs.append(log_entry)

            return LogsResponse(
                logs=logs,
                total=total,
                page=page,
                page_size=page_size,
                has_more=(page * page_size) < total,
            )
        except Exception as e:
            self.logger.error("Failed to fetch logs", error=str(e), page=page, page_size=page_size)
            # Return empty response on error
            return LogsResponse(
                logs=[],
                total=0,
                page=page,
                page_size=page_size,
                has_more=False,
            )

    async def get_log_stats(
        self,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> LogStats:
        """Get log statistics from audit activities."""
        try:
            # Build base query
            query = select(AuditActivity)

            if start_time:
                query = query.where(AuditActivity.created_at >= start_time)
            if end_time:
                query = query.where(AuditActivity.created_at <= end_time)

            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            result = await self.session.execute(count_query)
            total = result.scalar() or 0

            # Count by severity (map to log levels)
            severity_query = select(AuditActivity.severity, func.count(AuditActivity.id)).group_by(
                AuditActivity.severity
            )

            if start_time:
                severity_query = severity_query.where(AuditActivity.created_at >= start_time)
            if end_time:
                severity_query = severity_query.where(AuditActivity.created_at <= end_time)

            result = await self.session.execute(severity_query)
            severity_counts = dict(result.all())

            # Map severities to log levels
            by_level = {
                "INFO": severity_counts.get(ActivitySeverity.LOW.value, 0),
                "WARNING": severity_counts.get(ActivitySeverity.MEDIUM.value, 0),
                "ERROR": severity_counts.get(ActivitySeverity.HIGH.value, 0),
                "CRITICAL": severity_counts.get(ActivitySeverity.CRITICAL.value, 0),
            }

            # Count by service (extract from activity_type)
            activities_result = await self.session.execute(
                select(AuditActivity.activity_type).select_from(query.subquery())
            )
            activities = activities_result.scalars().all()

            by_service: dict[str, int] = {}
            for activity_type in activities:
                # Handle None values before validation
                if not activity_type:
                    continue
                service = activity_type.split(".")[0] if "." in activity_type else "platform"
                by_service[service] = by_service.get(service, 0) + 1

            # Determine time range
            if not start_time or not end_time:
                time_query = select(
                    func.min(AuditActivity.created_at), func.max(AuditActivity.created_at)
                )
                result = await self.session.execute(time_query)
                min_time, max_time = result.one()
                start_time = start_time or min_time or datetime.now(UTC)
                end_time = end_time or max_time or datetime.now(UTC)

            return LogStats(
                total=total,
                by_level=by_level,
                by_service=by_service,
                time_range={
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat(),
                },
            )
        except Exception as e:
            self.logger.error("Failed to fetch log stats", error=str(e))
            # Return empty stats on error
            now = datetime.now(UTC)
            return LogStats(
                total=0,
                by_level={},
                by_service={},
                time_range={
                    "start": (start_time or now).isoformat(),
                    "end": (end_time or now).isoformat(),
                },
            )


def get_logs_service(session: AsyncSession = Depends(get_session_dependency)) -> LogsService:
    """Get logs service instance with database session."""
    return LogsService(session=session)


# ============================================================
# Endpoints
# ============================================================


@logs_router.get("/logs", response_model=LogsResponse)
async def get_logs(
    level: LogLevel | None = Query(None, description="Filter by log level"),
    service: str | None = Query(None, description="Filter by service name"),
    search: str | None = Query(None, description="Search in log messages"),
    start_time: datetime | None = Query(None, description="Start of time range"),
    end_time: datetime | None = Query(None, description="End of time range"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(100, ge=1, le=1000, description="Logs per page"),
    current_user: CurrentUser = Depends(get_current_user),
    logs_service: LogsService = Depends(get_logs_service),
) -> LogsResponse:
    """
    Retrieve application logs with filtering and pagination.

    **Filters:**
    - level: Filter by log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - service: Filter by service name
    - search: Search term in log messages
    - start_time: ISO 8601 datetime for start of range
    - end_time: ISO 8601 datetime for end of range

    **Pagination:**
    - page: Page number (starts at 1)
    - page_size: Number of logs per page (max 1000)

    **Note:** Returns audit activities from the database.
    """
    logger.info(
        "logs.query",
        user_id=current_user.user_id,
        level=level.value if level else None,
        service=service,
        search=search,
        page=page,
        page_size=page_size,
    )

    return await logs_service.get_logs(
        level=level,
        service=service,
        search=search,
        start_time=start_time,
        end_time=end_time,
        page=page,
        page_size=page_size,
    )


@logs_router.get("/logs/stats", response_model=LogStats)
async def get_log_statistics(
    start_time: datetime | None = Query(None, description="Start of time range"),
    end_time: datetime | None = Query(None, description="End of time range"),
    current_user: CurrentUser = Depends(get_current_user),
    logs_service: LogsService = Depends(get_logs_service),
) -> LogStats:
    """
    Get log statistics and aggregations.

    Returns counts by log level, service, and time range information.
    """
    logger.info(
        "logs.stats.query",
        user_id=current_user.user_id,
        start_time=start_time,
        end_time=end_time,
    )

    return await logs_service.get_log_stats(
        start_time=start_time,
        end_time=end_time,
    )


@logs_router.get("/logs/services", response_model=list[str])
async def get_available_services(
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session_dependency),
) -> list[str]:
    """Get list of available services from audit activities."""
    logger.info("logs.services.list", user_id=current_user.user_id)

    try:
        # Query distinct activity types and extract service names
        query = select(AuditActivity.activity_type).distinct()
        result = await session.execute(query)
        activity_types = result.scalars().all()

        # Extract unique service names
        services = set()
        for activity_type in activity_types:
            # Handle None values before validation
            if not activity_type:
                continue
            service = activity_type.split(".")[0] if "." in activity_type else "platform"
            services.add(service)

        return sorted(services)
    except Exception as e:
        logger.error(
            "Failed to fetch available services", error=str(e), user_id=current_user.user_id
        )
        # Return empty list on error
        return []
