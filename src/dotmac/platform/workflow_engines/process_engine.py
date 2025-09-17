"""
Business Process Engine for executing business workflows and processes.
"""

import logging
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Dict, List, Type, Awaitable

from sqlalchemy.ext.asyncio import AsyncSession

from .base import BusinessWorkflow, BusinessWorkflowStatus
from .policy_engine import PolicyEngine
from .rules_engine import BusinessRulesEngine

logger = logging.getLogger(__name__)


class BusinessProcessEngine:
    """Execute and orchestrate business processes and workflows."""

    def __init__(self, db_session_factory: Optional[Callable[[], Awaitable[AsyncSession]]] = None):
        self.db_session_factory = db_session_factory
        self.rules_engine = BusinessRulesEngine()
        self.policy_engine = PolicyEngine()

        # Registered workflows and processes
        self.workflows: Dict[str, Type[BusinessWorkflow]] = {}
        self.process_definitions: Dict[str, Dict[str, Any]] = {}

        # Runtime state
        self.active_workflows: Dict[str, BusinessWorkflow] = {}
        self.workflow_history: List[Dict[str, Any]] = []

    def register_workflow(self, workflow_type: str, workflow_class: Type[BusinessWorkflow]) -> None:
        """Register a workflow type."""
        self.workflows[workflow_type] = workflow_class

    def register_process(self, process_id: str, process_definition: Dict[str, Any]) -> None:
        """Register a business process definition."""
        self.process_definitions[process_id] = process_definition

    async def start_workflow(
        self,
        workflow_type: str,
        context: Dict[str, Any],
        tenant_id: str,
        db_session: Optional[AsyncSession] = None,
        workflow_id: Optional[str] = None,
    ) -> BusinessWorkflow:
        """Start a new business workflow."""
        try:
            if workflow_type not in self.workflows:
                raise ValueError(f"Unknown workflow type: {workflow_type}")

            # Create workflow instance
            workflow_class = self.workflows[workflow_type]
            workflow = workflow_class(
                workflow_id=workflow_id,
                tenant_id=tenant_id,
            )

            # Set context
            db = db_session or (
                await self._get_db_session() if self.db_session_factory else None
            )
            workflow.set_business_context(context, db)

            # Validate business rules
            rules_result = await self.rules_engine.validate_workflow_rules(
                workflow_type, context, tenant_id
            )

            if not rules_result.valid:
                logger.error(
                    f"Business rules validation failed for {workflow_type}: {rules_result.errors}"
                )
                raise ValueError(
                    f"Business rules validation failed: {rules_result.errors}"
                )

            # Check policies
            policy_result = await self.policy_engine.check_workflow_policies(
                workflow_type, context, tenant_id
            )

            if not policy_result.allowed:
                logger.error(
                    f"Policy check failed for {workflow_type}: {policy_result.reason}"
                )
                raise ValueError(f"Policy violation: {policy_result.reason}")

            # Add to active workflows
            self.active_workflows[workflow.workflow_id] = workflow

            # Start execution
            await workflow.execute()

            # Log workflow started
            logger.info(
                f"Started workflow {workflow.workflow_id} of type {workflow_type}"
            )

            return workflow

        except Exception as e:
            logger.error(f"Failed to start workflow {workflow_type}: {str(e)}")
            raise

    async def resume_workflow(
        self,
        workflow_id: str,
        approval_data: Optional[Dict[str, Any]] = None,
    ) -> BusinessWorkflow:
        """Resume a paused workflow after approval."""
        if workflow_id not in self.active_workflows:
            raise ValueError(f"Workflow {workflow_id} not found in active workflows")

        workflow = self.active_workflows[workflow_id]

        if workflow.status != BusinessWorkflowStatus.WAITING_APPROVAL:
            raise ValueError(f"Workflow {workflow_id} is not waiting for approval")

        # Resume execution
        await workflow.approve_and_continue(approval_data)

        logger.info(f"Resumed workflow {workflow_id}")

        return workflow

    async def reject_workflow(
        self,
        workflow_id: str,
        rejection_reason: Optional[str] = None,
    ) -> BusinessWorkflow:
        """Reject and cancel a workflow waiting for approval."""
        if workflow_id not in self.active_workflows:
            raise ValueError(f"Workflow {workflow_id} not found in active workflows")

        workflow = self.active_workflows[workflow_id]

        if workflow.status != BusinessWorkflowStatus.WAITING_APPROVAL:
            raise ValueError(f"Workflow {workflow_id} is not waiting for approval")

        # Reject and cancel
        await workflow.reject_and_cancel(rejection_reason)

        logger.info(f"Rejected workflow {workflow_id}: {rejection_reason}")

        return workflow

    async def cancel_workflow(self, workflow_id: str) -> BusinessWorkflow:
        """Cancel an active workflow."""
        if workflow_id not in self.active_workflows:
            raise ValueError(f"Workflow {workflow_id} not found in active workflows")

        workflow = self.active_workflows[workflow_id]
        await workflow.cancel()

        logger.info(f"Cancelled workflow {workflow_id}")

        return workflow

    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get the status of a workflow."""
        if workflow_id not in self.active_workflows:
            raise ValueError(f"Workflow {workflow_id} not found")

        workflow = self.active_workflows[workflow_id]
        return workflow.to_dict()

    async def list_active_workflows(
        self,
        tenant_id: Optional[str] = None,
        workflow_type: Optional[str] = None,
        status: Optional[BusinessWorkflowStatus] = None,
    ) -> List[Dict[str, Any]]:
        """List active workflows with optional filters."""
        workflows: List[Dict[str, Any]] = []

        for workflow in self.active_workflows.values():
            # Apply filters
            if tenant_id and workflow.tenant_id != tenant_id:
                continue
            if workflow_type and workflow.workflow_type != workflow_type:
                continue
            if status and workflow.status != status:
                continue

            workflows.append(workflow.to_dict())

        return workflows

    async def execute_process(
        self,
        process_id: str,
        context: Dict[str, Any],
        tenant_id: str,
        db_session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """Execute a defined business process."""
        if process_id not in self.process_definitions:
            raise ValueError(f"Unknown process: {process_id}")

        process_def = self.process_definitions[process_id]

        try:
            # Initialize process execution context
            process_context: Dict[str, Any] = {
                "process_id": process_id,
                "tenant_id": tenant_id,
                "started_at": datetime.now(timezone.utc),
                "context": context,
                "steps_completed": 0,
                "total_steps": len(process_def.get("steps", [])),
                "results": [],
            }

            # Execute process steps
            for step in process_def.get("steps", []):
                step_result = await self._execute_process_step(
                    step, process_context, db_session
                )

                process_context["results"].append(step_result)
                process_context["steps_completed"] += 1

                # Check if step failed
                if not step_result.get("success", False):
                    process_context["status"] = "failed"
                    process_context["error"] = step_result.get("error")
                    break

            # Mark as completed if all steps succeeded
            if process_context["steps_completed"] == process_context["total_steps"]:
                process_context["status"] = "completed"

            process_context["completed_at"] = datetime.now(timezone.utc)

            # Log process execution
            logger.info(
                f"Executed process {process_id} for tenant {tenant_id}: "
                f"{process_context['status']}"
            )

            return process_context

        except Exception as e:
            logger.error(f"Failed to execute process {process_id}: {str(e)}")
            raise

    async def _execute_process_step(
        self,
        step: Dict[str, Any],
        process_context: Dict[str, Any],
        db_session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """Execute a single process step."""
        step_type = step.get("type")
        step_name = step.get("name", "unknown_step")

        try:
            if step_type == "workflow":
                # Execute a workflow as part of the process
                workflow_type = step.get("workflow_type")
                workflow_context = {
                    **process_context["context"],
                    "process_context": process_context,
                }

                workflow = await self.start_workflow(
                    workflow_type,
                    workflow_context,
                    process_context["tenant_id"],
                    db_session,
                )

                return {
                    "success": workflow.is_completed,
                    "step_name": step_name,
                    "step_type": step_type,
                    "workflow_id": workflow.workflow_id,
                    "workflow_results": [r.to_dict() for r in workflow.results],
                }

            elif step_type == "rule_check":
                # Check business rules
                rule_name = step.get("rule_name")
                result = await self.rules_engine.evaluate_rule(
                    rule_name,
                    process_context["context"],
                    process_context["tenant_id"],
                )

                return {
                    "success": result.valid,
                    "step_name": step_name,
                    "step_type": step_type,
                    "rule_result": result.to_dict(),
                }

            elif step_type == "policy_check":
                # Check policies
                policy_name = step.get("policy_name")
                result = await self.policy_engine.evaluate_policy(
                    policy_name,
                    process_context["context"],
                    process_context["tenant_id"],
                )

                return {
                    "success": result.allowed,
                    "step_name": step_name,
                    "step_type": step_type,
                    "policy_result": result.to_dict(),
                }

            elif step_type == "custom":
                # Execute custom function
                function_name = step.get("function")
                # This would be implemented to call registered custom functions

                return {
                    "success": True,
                    "step_name": step_name,
                    "step_type": step_type,
                    "message": f"Custom function {function_name} executed",
                }

            else:
                return {
                    "success": False,
                    "step_name": step_name,
                    "step_type": step_type,
                    "error": f"Unknown step type: {step_type}",
                }

        except Exception as e:
            return {
                "success": False,
                "step_name": step_name,
                "step_type": step_type,
                "error": str(e),
            }

    async def _get_db_session(self) -> AsyncSession:
        """Get database session."""
        if not self.db_session_factory:
            raise ValueError("No database session factory configured")
        return await self.db_session_factory()

    async def cleanup_completed_workflows(self, max_age_hours: int = 24):
        """Clean up completed workflows older than specified age."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)

        workflows_to_remove = []

        for workflow_id, workflow in self.active_workflows.items():
            if (workflow.is_completed or workflow.is_failed) and workflow.end_time:
                if workflow.end_time < cutoff_time:
                    # Move to history
                    self.workflow_history.append(workflow.to_dict())
                    workflows_to_remove.append(workflow_id)

        # Remove from active workflows
        for workflow_id in workflows_to_remove:
            del self.active_workflows[workflow_id]

        logger.info(f"Cleaned up {len(workflows_to_remove)} completed workflows")
