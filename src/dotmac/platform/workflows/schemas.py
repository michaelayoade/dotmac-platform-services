"""
Workflow Schemas

Pydantic schemas for API request/response validation.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .models import StepStatus, WorkflowStatus

# Workflow Template Schemas


class WorkflowCreate(BaseModel):
    """Schema for creating a workflow template"""

    name: str = Field(..., min_length=1, max_length=255, description="Unique workflow name")
    description: str | None = Field(None, description="Workflow description")
    definition: dict[str, Any] = Field(..., description="Workflow definition with steps")
    version: str = Field(default="1.0.0", description="Workflow version")
    tags: list[str] | None = Field(None, description="Workflow tags")


class WorkflowUpdate(BaseModel):
    """Schema for updating a workflow template"""

    description: str | None = None
    definition: dict[str, Any] | None = None
    is_active: bool | None = None
    tags: list[str] | None = None


class WorkflowResponse(BaseModel):
    """Schema for workflow template response"""

    id: str
    name: str
    description: str | None
    definition: dict[str, Any]
    is_active: bool
    version: str
    tags: list[str] | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def convert_id(cls, v: Any) -> str:
        """Convert ID to string."""
        return str(v) if v is not None else ""


class WorkflowListResponse(BaseModel):
    """Schema for workflow list response"""

    workflows: list[WorkflowResponse]
    total: int


# Workflow Execution Schemas


class WorkflowExecuteRequest(BaseModel):
    """Schema for executing a workflow"""

    workflow_name: str = Field(..., description="Name of workflow to execute")
    context: dict[str, Any] = Field(default_factory=dict, description="Input context")
    trigger_type: str = Field(default="manual", description="Trigger type")
    trigger_source: str | None = Field(None, description="Trigger source")
    tenant_id: str | None = Field(None, description="Tenant ID")


class WorkflowStepResponse(BaseModel):
    """Schema for workflow step response"""

    id: str
    step_name: str
    step_type: str
    sequence_number: int
    status: StepStatus
    input_data: dict[str, Any] | None
    output_data: dict[str, Any] | None
    error_message: str | None
    error_details: dict[str, Any] | None
    retry_count: int
    max_retries: int
    started_at: datetime | None
    completed_at: datetime | None
    duration_seconds: int | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def convert_id(cls, v: Any) -> str:
        """Convert ID to string."""
        return str(v) if v is not None else ""


class WorkflowExecutionResponse(BaseModel):
    """Schema for workflow execution response"""

    id: str
    workflow_id: str
    status: WorkflowStatus
    context: dict[str, Any] | None
    result: dict[str, Any] | None
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    trigger_type: str | None
    trigger_source: str | None
    tenant_id: str | None
    created_at: datetime
    updated_at: datetime
    steps: list[WorkflowStepResponse] | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", "workflow_id", mode="before")
    @classmethod
    def convert_ids(cls, v: Any) -> str:
        """Convert IDs to string."""
        return str(v) if v is not None else ""


class WorkflowExecutionListResponse(BaseModel):
    """Schema for execution list response"""

    executions: list[WorkflowExecutionResponse]
    total: int


class WorkflowStatsResponse(BaseModel):
    """Schema for workflow statistics response"""

    total: int
    by_status: dict[str, int]


# Built-in Workflow Definitions


class StepDefinition(BaseModel):
    """Schema for a single workflow step definition"""

    name: str = Field(..., description="Step name")
    type: str = Field(..., description="Step type: service_call, transform, condition, wait")
    description: str | None = Field(None, description="Step description")
    input: dict[str, Any] | None = Field(None, description="Step input parameters")
    params: dict[str, Any] | None = Field(None, description="Service call parameters")
    service: str | None = Field(None, description="Service name for service_call type")
    method: str | None = Field(None, description="Method name for service_call type")
    transform_type: str | None = Field(None, description="Transform type: map, filter")
    mapping: dict[str, str] | None = Field(None, description="Key mapping for transform")
    condition: dict[str, Any] | None = Field(None, description="Condition expression")
    duration: int | None = Field(None, description="Wait duration in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")


class WorkflowDefinition(BaseModel):
    """Schema for complete workflow definition"""

    steps: list[StepDefinition] = Field(..., description="Workflow steps")
    metadata: dict[str, Any] | None = Field(None, description="Workflow metadata")


# Examples for documentation


EXAMPLE_WORKFLOW = {
    "name": "tenant_status_check",
    "description": "Minimal workflow example for control-plane operations.",
    "definition": {
        "steps": [
            {
                "name": "send_status_notification",
                "type": "service_call",
                "service": "communications_service",
                "method": "send_template_email",
                "params": {
                    "template": "status_update",
                    "recipient": "${context.recipient_email}",
                    "variables": {
                        "tenant_id": "${context.tenant_id}",
                        "status": "${context.status}",
                    },
                },
                "max_retries": 2,
            }
        ]
    },
    "version": "1.0.0",
    "tags": ["ops", "low-priority"],
}
