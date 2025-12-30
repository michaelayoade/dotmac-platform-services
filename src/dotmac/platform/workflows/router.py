"""
Workflow API Router

REST API endpoints for workflow management and execution.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.rbac_dependencies import require_permission
from ..database import get_async_session
from .builtin_workflows import get_all_builtin_workflows
from .models import WorkflowStatus
from .schemas import (
    WorkflowCreate,
    WorkflowExecuteRequest,
    WorkflowExecutionListResponse,
    WorkflowExecutionResponse,
    WorkflowListResponse,
    WorkflowResponse,
    WorkflowStatsResponse,
    WorkflowUpdate,
)
from .service import WorkflowService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workflows", tags=["Workflows"])


def get_workflow_service(db: AsyncSession = Depends(get_async_session)) -> WorkflowService:
    """Dependency to get workflow service instance"""
    return WorkflowService(db)


# Workflow Template Endpoints


@router.post(
    "/",
    response_model=WorkflowResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("workflows:create"))],
)
async def create_workflow(
    workflow_data: WorkflowCreate,
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowResponse:
    """
    Create a new workflow template.

    Required permission: workflows:create
    """
    try:
        workflow = await service.create_workflow(
            name=workflow_data.name,
            definition=workflow_data.definition,
            description=workflow_data.description,
            version=workflow_data.version,
            tags=workflow_data.tags,
        )
        return WorkflowResponse.model_validate(workflow)
    except Exception as e:
        logger.error(f"Error creating workflow: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create workflow: {str(e)}",
        )


@router.get(
    "/",
    response_model=WorkflowListResponse,
    dependencies=[Depends(require_permission("workflows:read"))],
)
async def list_workflows(
    is_active: bool | None = Query(None, description="Filter by active status"),
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowListResponse:
    """
    List all workflow templates.

    Required permission: workflows:read
    """
    workflows = await service.list_workflows(is_active=is_active)
    return WorkflowListResponse(
        workflows=[WorkflowResponse.model_validate(w) for w in workflows],
        total=len(workflows),
    )


@router.get(
    "/builtin",
    response_model=list[dict],
    dependencies=[Depends(require_permission("workflows:read"))],
)
async def list_builtin_workflows() -> list[dict]:
    """
    List all built-in workflow definitions.

    Required permission: workflows:read
    """
    return get_all_builtin_workflows()


# NOTE: Specific routes like /executions and /stats must come BEFORE /{workflow_id}
# to prevent FastAPI from matching them as parameterized routes


@router.get(
    "/executions",
    response_model=WorkflowExecutionListResponse,
    dependencies=[Depends(require_permission("workflows:read"))],
)
async def list_executions(
    workflow_id: int | None = Query(None, description="Filter by workflow ID"),
    status_filter: WorkflowStatus | None = Query(
        None, alias="status", description="Filter by status"
    ),
    tenant_id: str | None = Query(None, description="Filter by tenant ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Results offset"),
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowExecutionListResponse:
    """
    List workflow executions with filtering.

    Required permission: workflows:read
    """
    executions = await service.list_executions(
        workflow_id=workflow_id,
        status=status_filter,
        tenant_id=tenant_id,
        limit=limit,
        offset=offset,
    )
    return WorkflowExecutionListResponse(
        executions=[WorkflowExecutionResponse.model_validate(e) for e in executions],
        total=len(executions),
    )


@router.get(
    "/stats",
    response_model=WorkflowStatsResponse,
    dependencies=[Depends(require_permission("workflows:read"))],
)
async def get_workflow_stats(
    workflow_id: int | None = Query(None, description="Filter by workflow ID"),
    tenant_id: str | None = Query(None, description="Filter by tenant ID"),
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowStatsResponse:
    """
    Get workflow execution statistics.

    Required permission: workflows:read
    """
    stats = await service.get_execution_stats(
        workflow_id=workflow_id,
        tenant_id=tenant_id,
    )
    return WorkflowStatsResponse(**stats)


@router.get(
    "/{workflow_id}",
    response_model=WorkflowResponse,
    dependencies=[Depends(require_permission("workflows:read"))],
)
async def get_workflow(
    workflow_id: int,
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowResponse:
    """
    Get a workflow template by ID.

    Required permission: workflows:read
    """
    workflow = await service.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found",
        )
    return WorkflowResponse.model_validate(workflow)


@router.patch(
    "/{workflow_id}",
    response_model=WorkflowResponse,
    dependencies=[Depends(require_permission("workflows:update"))],
)
async def update_workflow(
    workflow_id: int,
    workflow_data: WorkflowUpdate,
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowResponse:
    """
    Update a workflow template.

    Required permission: workflows:update
    """
    try:
        workflow = await service.update_workflow(
            workflow_id=workflow_id,
            definition=workflow_data.definition,
            description=workflow_data.description,
            is_active=workflow_data.is_active,
            tags=workflow_data.tags,
        )
        return WorkflowResponse.model_validate(workflow)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error updating workflow {workflow_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update workflow: {str(e)}",
        )


@router.delete(
    "/{workflow_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("workflows:delete"))],
)
async def delete_workflow(
    workflow_id: int,
    service: WorkflowService = Depends(get_workflow_service),
) -> None:
    """
    Delete a workflow template.

    Required permission: workflows:delete
    """
    try:
        await service.delete_workflow(workflow_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# Workflow Execution Endpoints


@router.post(
    "/execute",
    response_model=WorkflowExecutionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(require_permission("workflows:execute"))],
)
async def execute_workflow(
    request: WorkflowExecuteRequest,
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowExecutionResponse:
    """
    Execute a workflow by name.

    Required permission: workflows:execute
    """
    try:
        execution = await service.execute_workflow(
            workflow_name=request.workflow_name,
            context=request.context,
            trigger_type=request.trigger_type,
            trigger_source=request.trigger_source,
            tenant_id=request.tenant_id,
        )
        return WorkflowExecutionResponse.model_validate(execution)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error executing workflow {request.workflow_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow execution failed: {str(e)}",
        )


@router.post(
    "/{workflow_id}/execute",
    response_model=WorkflowExecutionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(require_permission("workflows:execute"))],
)
async def execute_workflow_by_id(
    workflow_id: int,
    context: dict,
    trigger_type: str = "manual",
    trigger_source: str | None = None,
    tenant_id: str | None = None,
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowExecutionResponse:
    """
    Execute a workflow by ID.

    Required permission: workflows:execute
    """
    try:
        execution = await service.execute_workflow_by_id(
            workflow_id=workflow_id,
            context=context,
            trigger_type=trigger_type,
            trigger_source=trigger_source,
            tenant_id=tenant_id,
        )
        return WorkflowExecutionResponse.model_validate(execution)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error executing workflow {workflow_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow execution failed: {str(e)}",
        )


@router.get(
    "/executions/{execution_id}",
    response_model=WorkflowExecutionResponse,
    dependencies=[Depends(require_permission("workflows:read"))],
)
async def get_execution(
    execution_id: int,
    include_steps: bool = Query(False, description="Include step details"),
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowExecutionResponse:
    """
    Get a workflow execution by ID.

    Required permission: workflows:read
    """
    execution = await service.get_execution(execution_id, include_steps=include_steps)
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution {execution_id} not found",
        )
    return WorkflowExecutionResponse.model_validate(execution)


@router.post(
    "/executions/{execution_id}/cancel",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("workflows:execute"))],
)
async def cancel_execution(
    execution_id: int,
    service: WorkflowService = Depends(get_workflow_service),
) -> None:
    """
    Cancel a running workflow execution.

    Required permission: workflows:execute
    """
    try:
        await service.cancel_execution(execution_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# Statistics Endpoints


@router.get(
    "/{workflow_id}/stats",
    response_model=WorkflowStatsResponse,
    dependencies=[Depends(require_permission("workflows:read"))],
)
async def get_workflow_stats_by_id(
    workflow_id: int,
    tenant_id: int | None = Query(None, description="Filter by tenant ID"),
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowStatsResponse:
    """
    Get execution statistics for a specific workflow.

    Required permission: workflows:read
    """
    # Verify workflow exists
    workflow = await service.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found",
        )

    stats = await service.get_execution_stats(
        workflow_id=workflow_id,
        tenant_id=tenant_id,
    )
    return WorkflowStatsResponse(**stats)


# =============================================================================
# Dashboard Endpoint
# =============================================================================


class WorkflowDashboardSummary(BaseModel):
    """Summary statistics for workflow dashboard."""

    model_config = ConfigDict()

    total_workflows: int = Field(description="Total workflow templates")
    active_workflows: int = Field(description="Active workflow templates")
    total_executions: int = Field(description="Total executions")
    pending_executions: int = Field(description="Pending executions")
    running_executions: int = Field(description="Running executions")
    completed_executions: int = Field(description="Completed executions")
    failed_executions: int = Field(description="Failed executions")
    success_rate_pct: float = Field(description="Execution success rate")


class WorkflowChartDataPoint(BaseModel):
    """Single data point for workflow charts."""

    model_config = ConfigDict()

    label: str
    value: float
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkflowCharts(BaseModel):
    """Chart data for workflow dashboard."""

    model_config = ConfigDict()

    executions_by_status: list[WorkflowChartDataPoint] = Field(description="Executions by status")
    executions_by_workflow: list[WorkflowChartDataPoint] = Field(description="Executions by workflow")
    executions_trend: list[WorkflowChartDataPoint] = Field(description="Daily execution trend")
    success_trend: list[WorkflowChartDataPoint] = Field(description="Daily success rate trend")


class WorkflowAlert(BaseModel):
    """Alert item for workflow dashboard."""

    model_config = ConfigDict()

    type: str = Field(description="Alert type: warning, error, info")
    title: str
    message: str
    count: int = 0
    action_url: str | None = None


class WorkflowRecentActivity(BaseModel):
    """Recent activity item for workflow dashboard."""

    model_config = ConfigDict()

    id: str
    type: str = Field(description="Activity type: execution, workflow")
    description: str
    status: str
    timestamp: datetime
    workflow_id: int | None = None
    tenant_id: str | None = None


class WorkflowDashboardResponse(BaseModel):
    """Consolidated workflow dashboard response."""

    model_config = ConfigDict()

    summary: WorkflowDashboardSummary
    charts: WorkflowCharts
    alerts: list[WorkflowAlert]
    recent_activity: list[WorkflowRecentActivity]
    generated_at: datetime


@router.get(
    "/dashboard",
    response_model=WorkflowDashboardResponse,
    summary="Get workflow dashboard data",
    description="Returns consolidated workflow metrics, charts, and alerts for the dashboard",
    dependencies=[Depends(require_permission("workflows:read"))],
)
async def get_workflow_dashboard(
    period_days: int = Query(30, ge=1, le=90, description="Days of trend data"),
    filter_tenant_id: str | None = Query(None, alias="tenant_id", description="Filter by tenant ID"),
    service: WorkflowService = Depends(get_workflow_service),
    db: AsyncSession = Depends(get_async_session),
) -> WorkflowDashboardResponse:
    """
    Get consolidated workflow dashboard data including:
    - Summary statistics (workflow counts, execution stats)
    - Chart data (trends, breakdowns)
    - Alerts (failed executions)
    - Recent activity
    """
    from .models import Workflow, WorkflowExecution

    try:
        now = datetime.now(timezone.utc)

        # ========== SUMMARY STATS ==========
        # Workflow template counts
        workflow_counts_query = select(
            func.count(Workflow.id).label("total"),
            func.sum(case((Workflow.is_active.is_(True), 1), else_=0)).label("active"),
        )
        workflow_counts_result = await db.execute(workflow_counts_query)
        workflow_counts = workflow_counts_result.one()

        # Execution counts
        exec_counts_query = select(
            func.count(WorkflowExecution.id).label("total"),
            func.sum(case((WorkflowExecution.status == WorkflowStatus.PENDING, 1), else_=0)).label("pending"),
            func.sum(case((WorkflowExecution.status == WorkflowStatus.RUNNING, 1), else_=0)).label("running"),
            func.sum(case((WorkflowExecution.status == WorkflowStatus.COMPLETED, 1), else_=0)).label("completed"),
            func.sum(case((WorkflowExecution.status == WorkflowStatus.FAILED, 1), else_=0)).label("failed"),
        )
        if filter_tenant_id:
            exec_counts_query = exec_counts_query.where(WorkflowExecution.tenant_id == filter_tenant_id)
        exec_counts_result = await db.execute(exec_counts_query)
        exec_counts = exec_counts_result.one()

        # Calculate success rate
        total_finished = (exec_counts.completed or 0) + (exec_counts.failed or 0)
        success_rate = ((exec_counts.completed or 0) / total_finished * 100) if total_finished > 0 else 0.0

        summary = WorkflowDashboardSummary(
            total_workflows=workflow_counts.total or 0,
            active_workflows=workflow_counts.active or 0,
            total_executions=exec_counts.total or 0,
            pending_executions=exec_counts.pending or 0,
            running_executions=exec_counts.running or 0,
            completed_executions=exec_counts.completed or 0,
            failed_executions=exec_counts.failed or 0,
            success_rate_pct=round(success_rate, 2),
        )

        # ========== CHART DATA ==========
        # Executions by status
        status_query = select(
            WorkflowExecution.status,
            func.count(WorkflowExecution.id),
        )
        if filter_tenant_id:
            status_query = status_query.where(WorkflowExecution.tenant_id == filter_tenant_id)
        status_query = status_query.group_by(WorkflowExecution.status)
        status_result = await db.execute(status_query)
        executions_by_status = [
            WorkflowChartDataPoint(label=row[0].value if row[0] else "unknown", value=row[1])
            for row in status_result.all()
        ]

        # Executions by workflow
        workflow_query = select(
            Workflow.name,
            func.count(WorkflowExecution.id),
        ).join(Workflow, WorkflowExecution.workflow_id == Workflow.id)
        if filter_tenant_id:
            workflow_query = workflow_query.where(WorkflowExecution.tenant_id == filter_tenant_id)
        workflow_query = workflow_query.group_by(Workflow.name).limit(10)
        workflow_result = await db.execute(workflow_query)
        executions_by_workflow = [
            WorkflowChartDataPoint(label=row[0] if row[0] else "Unknown", value=row[1])
            for row in workflow_result.all()
        ]

        # Execution trend (daily)
        executions_trend = []
        success_trend = []
        for i in range(min(period_days, 14) - 1, -1, -1):
            day_date = now - timedelta(days=i)
            next_day = day_date + timedelta(days=1)

            day_count_query = select(func.count(WorkflowExecution.id)).where(
                WorkflowExecution.created_at >= day_date.replace(hour=0, minute=0, second=0),
                WorkflowExecution.created_at < next_day.replace(hour=0, minute=0, second=0),
            )
            if filter_tenant_id:
                day_count_query = day_count_query.where(WorkflowExecution.tenant_id == filter_tenant_id)
            day_count_result = await db.execute(day_count_query)
            day_count = day_count_result.scalar() or 0

            executions_trend.append(WorkflowChartDataPoint(
                label=day_date.strftime("%b %d"),
                value=day_count,
            ))
            success_trend.append(WorkflowChartDataPoint(
                label=day_date.strftime("%b %d"),
                value=success_rate,
            ))

        charts = WorkflowCharts(
            executions_by_status=executions_by_status,
            executions_by_workflow=executions_by_workflow,
            executions_trend=executions_trend,
            success_trend=success_trend,
        )

        # ========== ALERTS ==========
        alerts = []

        if exec_counts.failed and exec_counts.failed > 0:
            alerts.append(WorkflowAlert(
                type="error",
                title="Failed Executions",
                message=f"{exec_counts.failed} workflow execution(s) have failed",
                count=exec_counts.failed,
                action_url="/workflows/executions?status=failed",
            ))

        if exec_counts.running and exec_counts.running > 10:
            alerts.append(WorkflowAlert(
                type="warning",
                title="High Execution Load",
                message=f"{exec_counts.running} executions currently running",
                count=exec_counts.running,
                action_url="/workflows/executions?status=running",
            ))

        # ========== RECENT ACTIVITY ==========
        recent_executions = await service.list_executions(
            tenant_id=filter_tenant_id,
            limit=10,
            offset=0,
        )

        recent_activity = [
            WorkflowRecentActivity(
                id=str(e.id),
                type="execution",
                description=f"Execution: {e.workflow.name if e.workflow else 'Unknown Workflow'}",
                status=e.status.value if e.status else "unknown",
                timestamp=e.created_at,
                workflow_id=e.workflow_id,
                tenant_id=e.tenant_id,
            )
            for e in recent_executions
        ]

        return WorkflowDashboardResponse(
            summary=summary,
            charts=charts,
            alerts=alerts,
            recent_activity=recent_activity,
            generated_at=now,
        )

    except Exception as e:
        logger.error(f"Failed to generate workflow dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate workflow dashboard: {str(e)}",
        )
