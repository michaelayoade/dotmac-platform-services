"""Reusable workflow primitives for orchestrating business processes."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4


class BusinessWorkflowStatus(str, Enum):
    """Lifecycle states a business workflow can occupy."""

    NOT_STARTED = "not_started"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowResult:
    """Outcome captured while executing a workflow step."""

    name: str
    status: str = "completed"
    details: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        """Serialize the result for external consumers."""
        return {
            "name": self.name,
            "status": self.status,
            "details": self.details,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }


class BusinessWorkflow(ABC):
    """Base class for orchestrated workflows managed by the process engine."""

    workflow_type: str

    def __init__(self, workflow_id: Optional[str] = None, tenant_id: Optional[str] = None) -> None:
        self.workflow_id = workflow_id or uuid4().hex
        self.tenant_id = tenant_id
        self.status = BusinessWorkflowStatus.NOT_STARTED
        self.context: dict[str, Any] = {}
        self.db_session: Any = None
        self.results: list[WorkflowResult] = []
        self.error: Optional[str] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

        if not hasattr(self, "workflow_type"):
            self.workflow_type = self.__class__.__name__

    def set_business_context(
        self, context: dict[str, Any], db_session: Optional[Any] = None
    ) -> None:
        """Attach runtime context and optional data access handle."""
        self.context = dict(context or {})
        self.db_session = db_session

    async def execute(self) -> None:
        """Run the workflow lifecycle and manage common state transitions."""
        self.start_time = datetime.now(timezone.utc)
        self.status = BusinessWorkflowStatus.RUNNING

        try:
            await self.run()
        except Exception as exc:  # pragma: no cover - defensive propagation
            self.status = BusinessWorkflowStatus.FAILED
            self.error = str(exc)
            self.end_time = datetime.now(timezone.utc)
            raise
        else:
            now = datetime.now(timezone.utc)
            if self.status == BusinessWorkflowStatus.RUNNING:
                self.status = BusinessWorkflowStatus.COMPLETED
                self.end_time = now
            elif self.status in {
                BusinessWorkflowStatus.COMPLETED,
                BusinessWorkflowStatus.FAILED,
                BusinessWorkflowStatus.CANCELLED,
            }:
                self.end_time = self.end_time or now
            # WAITING_APPROVAL keeps end_time unset until resumed

    @abstractmethod
    async def run(self) -> None:
        """Perform the unit of work for the workflow."""

    def add_result(self, result: WorkflowResult) -> None:
        """Record an intermediate outcome."""
        self.results.append(result)

    async def approve_and_continue(self, approval_data: Optional[dict[str, Any]] = None) -> None:
        """Resume execution after an approval gate."""
        if self.status != BusinessWorkflowStatus.WAITING_APPROVAL:
            raise ValueError("Workflow is not waiting for approval")

        self.status = BusinessWorkflowStatus.RUNNING
        await self.on_approve(approval_data)

        if self.status == BusinessWorkflowStatus.RUNNING:
            self.status = BusinessWorkflowStatus.COMPLETED
            self.end_time = datetime.now(timezone.utc)

    async def on_approve(self, approval_data: Optional[dict[str, Any]]) -> None:
        """Hook for subclasses to continue processing after approval."""

    async def reject_and_cancel(self, rejection_reason: Optional[str] = None) -> None:
        """Abort a workflow that was awaiting approval."""
        if self.status != BusinessWorkflowStatus.WAITING_APPROVAL:
            raise ValueError("Workflow is not waiting for approval")

        self.status = BusinessWorkflowStatus.CANCELLED
        self.error = rejection_reason
        self.end_time = datetime.now(timezone.utc)
        await self.on_reject(rejection_reason)

    async def on_reject(self, rejection_reason: Optional[str]) -> None:
        """Hook for subclasses to react to rejections."""

    async def cancel(self) -> None:
        """Cancel the workflow without raising additional errors."""
        self.status = BusinessWorkflowStatus.CANCELLED
        self.end_time = datetime.now(timezone.utc)
        await self.on_cancel()

    async def on_cancel(self) -> None:
        """Hook for subclasses to clean up after cancellation."""

    @property
    def is_completed(self) -> bool:
        return self.status == BusinessWorkflowStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        return self.status == BusinessWorkflowStatus.FAILED

    def mark_waiting_for_approval(self) -> None:
        """Convenience for workflows that need external approval."""
        self.status = BusinessWorkflowStatus.WAITING_APPROVAL
        self.end_time = None

    def to_dict(self) -> dict[str, Any]:
        """Represent workflow state in a serializable structure."""
        return {
            "workflow_id": self.workflow_id,
            "tenant_id": self.tenant_id,
            "workflow_type": self.workflow_type,
            "status": self.status.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "error": self.error,
            "results": [result.to_dict() for result in self.results],
            "context": self.context,
        }
