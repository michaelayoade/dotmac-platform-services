/**
 * Workflows API
 *
 * Workflow orchestration, templates, and execution management
 */

import { api, normalizePaginatedResponse } from "./client";

// ============================================================================
// Workflow Types
// ============================================================================

export type WorkflowStatus = "pending" | "running" | "completed" | "failed" | "cancelled";
export type TriggerType = "manual" | "scheduled" | "webhook" | "event";

export interface WorkflowStep {
  id: string;
  name: string;
  type: string;
  config: Record<string, unknown>;
  dependsOn?: string[];
  retryPolicy?: {
    maxRetries: number;
    backoffMultiplier: number;
  };
}

export interface WorkflowDefinition {
  id: string;
  name: string;
  description?: string;
  version: string;
  steps: WorkflowStep[];
  triggers?: Array<{
    type: TriggerType;
    config: Record<string, unknown>;
  }>;
  tags?: string[];
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export type Workflow = WorkflowDefinition;

export interface WorkflowVersion {
  id: string;
  workflowId: string;
  version: string;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface WorkflowExecution {
  id: string;
  workflowId: string;
  workflowName: string;
  status: WorkflowStatus;
  triggerType: TriggerType;
  context?: Record<string, unknown>;
  result?: Record<string, unknown>;
  error?: string;
  startedAt: string;
  completedAt?: string;
  duration?: number;
  stepResults?: Array<{
    stepId: string;
    stepName: string;
    status: WorkflowStatus;
    result?: unknown;
    error?: string;
    startedAt: string;
    completedAt?: string;
  }>;
}

export interface ExecutionLog {
  timestamp: string;
  level: "debug" | "info" | "warn" | "error";
  message: string;
}

// ============================================================================
// Workflow Template CRUD
// ============================================================================

export interface GetWorkflowsParams {
  page?: number;
  pageSize?: number;
  search?: string;
  isActive?: boolean;
  tags?: string[];
  sortBy?: string;
  sortOrder?: "asc" | "desc";
}

export async function getWorkflows(params: GetWorkflowsParams = {}): Promise<{
  workflows: WorkflowDefinition[];
  totalCount: number;
  pageCount: number;
}> {
  const { page = 1, pageSize = 20, search, isActive, tags, sortBy, sortOrder } = params;

  const response = await api.get<unknown>("/api/v1/workflows", {
    params: {
      page,
      page_size: pageSize,
      search,
      is_active: isActive,
      tags: tags?.join(","),
      sort_by: sortBy,
      sort_order: sortOrder,
    },
  });
  const normalized = normalizePaginatedResponse<WorkflowDefinition>(response);

  return {
    workflows: normalized.items,
    totalCount: normalized.total,
    pageCount: normalized.totalPages,
  };
}

export async function getWorkflow(id: string): Promise<WorkflowDefinition> {
  return api.get<WorkflowDefinition>(`/api/v1/workflows/${id}`);
}

export async function getBuiltinWorkflows(): Promise<WorkflowDefinition[]> {
  return api.get<WorkflowDefinition[]>("/api/v1/workflows/builtin");
}

export interface CreateWorkflowData {
  name: string;
  description?: string;
  steps: WorkflowStep[];
  triggers?: WorkflowDefinition["triggers"];
  tags?: string[];
  isActive?: boolean;
}

export async function createWorkflow(data: CreateWorkflowData): Promise<WorkflowDefinition> {
  return api.post<WorkflowDefinition>("/api/v1/workflows", {
    name: data.name,
    description: data.description,
    steps: data.steps,
    triggers: data.triggers,
    tags: data.tags,
    is_active: data.isActive ?? true,
  });
}

export async function updateWorkflow(
  id: string,
  data: Partial<CreateWorkflowData>
): Promise<WorkflowDefinition> {
  return api.patch<WorkflowDefinition>(`/api/v1/workflows/${id}`, {
    name: data.name,
    description: data.description,
    steps: data.steps,
    triggers: data.triggers,
    tags: data.tags,
    is_active: data.isActive,
  });
}

export async function deleteWorkflow(id: string): Promise<void> {
  return api.delete(`/api/v1/workflows/${id}`);
}

export async function publishWorkflow(id: string): Promise<WorkflowDefinition> {
  return updateWorkflow(id, { isActive: true });
}

export async function unpublishWorkflow(id: string): Promise<WorkflowDefinition> {
  return updateWorkflow(id, { isActive: false });
}

export async function cloneWorkflow(id: string, newName: string): Promise<WorkflowDefinition> {
  const workflow = await getWorkflow(id);
  return createWorkflow({
    name: newName,
    description: workflow.description,
    steps: workflow.steps ?? [],
    triggers: workflow.triggers,
    tags: workflow.tags,
    isActive: workflow.isActive,
  });
}

export async function getWorkflowVersions(workflowId: string): Promise<WorkflowVersion[]> {
  const workflow = await getWorkflow(workflowId);
  return [
    {
      id: workflow.id,
      workflowId: workflow.id,
      version: workflow.version,
      isActive: workflow.isActive,
      createdAt: workflow.createdAt,
      updatedAt: workflow.updatedAt,
    },
  ];
}

export async function getWorkflowVersion(
  workflowId: string,
  _version: number
): Promise<WorkflowVersion> {
  const versions = await getWorkflowVersions(workflowId);
  if (!versions[0]) {
    throw new Error("Workflow version not found");
  }
  return versions[0];
}

// ============================================================================
// Workflow Execution
// ============================================================================

export interface GetExecutionsParams {
  page?: number;
  pageSize?: number;
  workflowId?: string;
  status?: WorkflowStatus;
  triggerType?: TriggerType;
  startDate?: string;
  endDate?: string;
  sortBy?: string;
  sortOrder?: "asc" | "desc";
}

export async function getWorkflowExecutions(params: GetExecutionsParams = {}): Promise<{
  executions: WorkflowExecution[];
  totalCount: number;
  pageCount: number;
}> {
  const {
    page = 1,
    pageSize = 20,
    workflowId,
    status,
    triggerType,
    startDate,
    endDate,
    sortBy,
    sortOrder,
  } = params;

  const response = await api.get<unknown>("/api/v1/workflows/executions", {
    params: {
      page,
      page_size: pageSize,
      workflow_id: workflowId,
      status,
      trigger_type: triggerType,
      start_date: startDate,
      end_date: endDate,
      sort_by: sortBy,
      sort_order: sortOrder,
    },
  });
  const normalized = normalizePaginatedResponse<WorkflowExecution>(response);

  return {
    executions: normalized.items,
    totalCount: normalized.total,
    pageCount: normalized.totalPages,
  };
}

export async function getWorkflowExecution(executionId: string): Promise<WorkflowExecution> {
  return api.get<WorkflowExecution>(`/api/v1/workflows/executions/${executionId}`);
}

export async function executeWorkflow(
  workflowId: string,
  context?: Record<string, unknown>
): Promise<WorkflowExecution> {
  return api.post<WorkflowExecution>(`/api/v1/workflows/${workflowId}/execute`, {
    context,
  });
}

export async function executeWorkflowByName(
  name: string,
  context?: Record<string, unknown>
): Promise<WorkflowExecution> {
  return api.post<WorkflowExecution>("/api/v1/workflows/execute", {
    name,
    context,
  });
}

export async function cancelWorkflowExecution(executionId: string): Promise<WorkflowExecution> {
  return api.post<WorkflowExecution>(`/api/v1/workflows/executions/${executionId}/cancel`);
}

export async function cancelExecution(
  _workflowId: string,
  executionId: string
): Promise<WorkflowExecution> {
  await cancelWorkflowExecution(executionId);
  return getWorkflowExecution(executionId);
}

export async function retryExecution(
  workflowId: string,
  executionId: string
): Promise<WorkflowExecution> {
  const execution = await getWorkflowExecution(executionId);
  return executeWorkflow(workflowId, execution.context);
}

export async function getExecutionLogs(
  _workflowId: string,
  _executionId: string
): Promise<ExecutionLog[]> {
  return [];
}

// ============================================================================
// Workflow Statistics
// ============================================================================

export interface WorkflowStats {
  totalExecutions: number;
  successfulExecutions: number;
  failedExecutions: number;
  avgDuration: number;
  successRate: number;
  failureRate: number;
  executionsByWorkflow: Array<{
    workflowId: string;
    workflowName: string;
    executionCount: number;
    successRate: number;
  }>;
  executionsTrend: Array<{
    date: string;
    total: number;
    successful: number;
    failed: number;
  }>;
}

export async function getWorkflowStats(params?: {
  periodDays?: number;
  workflowId?: string;
}): Promise<WorkflowStats> {
  return api.get<WorkflowStats>("/api/v1/workflows/stats", {
    params: {
      period_days: params?.periodDays,
      workflow_id: params?.workflowId,
    },
  });
}

// ============================================================================
// Workflow Metrics (Prometheus format)
// ============================================================================

export interface WorkflowMetricsOverview {
  activeWorkflows: number;
  runningExecutions: number;
  queuedExecutions: number;
  avgExecutionTime: number;
  successRate24h: number;
  failureRate24h: number;
}

export async function getWorkflowMetricsOverview(): Promise<WorkflowMetricsOverview> {
  return api.get<WorkflowMetricsOverview>("/api/v1/workflows/metrics/overview");
}
