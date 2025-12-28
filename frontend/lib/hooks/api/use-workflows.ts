"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getWorkflows,
  getWorkflow,
  createWorkflow,
  updateWorkflow,
  deleteWorkflow,
  getWorkflowExecutions,
  getWorkflowExecution,
  executeWorkflow,
  cancelWorkflowExecution,
  getWorkflowStats,
  getWorkflowsDashboard,
  type GetWorkflowsParams,
  type GetExecutionsParams,
  type WorkflowDefinition,
  type WorkflowExecution,
  type WorkflowStats,
  type CreateWorkflowData,
} from "@/lib/api/workflows";
import { queryKeys } from "@/lib/api/query-keys";
import type { DashboardQueryParams } from "@/lib/api/types/dashboard";

type Workflow = WorkflowDefinition;

interface WorkflowVersion {
  id: string;
  workflowId: string;
  version: string;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

interface ExecutionLog {
  timestamp: string;
  level: "debug" | "info" | "warn" | "error";
  message: string;
}

async function publishWorkflow(id: string): Promise<WorkflowDefinition> {
  return updateWorkflow(id, { isActive: true });
}

async function unpublishWorkflow(id: string): Promise<WorkflowDefinition> {
  return updateWorkflow(id, { isActive: false });
}

async function cloneWorkflow(id: string, newName: string): Promise<WorkflowDefinition> {
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

async function getWorkflowVersions(workflowId: string): Promise<WorkflowVersion[]> {
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

async function getWorkflowVersion(
  workflowId: string,
  _version: number
): Promise<WorkflowVersion> {
  const versions = await getWorkflowVersions(workflowId);
  if (!versions[0]) {
    throw new Error("Workflow version not found");
  }
  return versions[0];
}

async function cancelExecution(
  _workflowId: string,
  executionId: string
): Promise<WorkflowExecution> {
  await cancelWorkflowExecution(executionId);
  return getWorkflowExecution(executionId);
}

async function retryExecution(
  workflowId: string,
  executionId: string
): Promise<WorkflowExecution> {
  const execution = await getWorkflowExecution(executionId);
  return executeWorkflow(workflowId, execution.context);
}

async function getExecutionLogs(
  _workflowId: string,
  _executionId: string
): Promise<ExecutionLog[]> {
  return [];
}

// ============================================================================
// Workflows Dashboard Hook
// ============================================================================

export function useWorkflowsDashboard(params?: DashboardQueryParams) {
  return useQuery({
    queryKey: queryKeys.workflows.dashboard(params),
    queryFn: () => getWorkflowsDashboard(params),
    staleTime: 60 * 1000, // 1 minute
  });
}

// ============================================================================
// Workflows Hooks
// ============================================================================

export function useWorkflows(params?: GetWorkflowsParams) {
  return useQuery({
    queryKey: queryKeys.workflows.list(params),
    queryFn: () => getWorkflows(params),
    placeholderData: (previousData) => previousData,
  });
}

export function useWorkflow(id: string) {
  return useQuery({
    queryKey: queryKeys.workflows.detail(id),
    queryFn: () => getWorkflow(id),
    enabled: !!id,
  });
}

export function useCreateWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createWorkflow,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.workflows.all,
      });
    },
  });
}

export function useUpdateWorkflow() {
  const queryClient = useQueryClient();

  return useMutation<WorkflowDefinition, Error, { id: string; data: Partial<CreateWorkflowData> }>({
    mutationFn: ({ id, data }: { id: string; data: Partial<CreateWorkflowData> }) =>
      updateWorkflow(id, data),
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.workflows.detail(data.id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.workflows.all,
      });
    },
  });
}

export function useDeleteWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteWorkflow,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.workflows.all,
      });
    },
  });
}

export function usePublishWorkflow() {
  const queryClient = useQueryClient();

  return useMutation<Workflow, Error, string>({
    mutationFn: (id: string) => publishWorkflow(id),
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.workflows.detail(data.id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.workflows.all,
      });
    },
  });
}

export function useUnpublishWorkflow() {
  const queryClient = useQueryClient();

  return useMutation<Workflow, Error, string>({
    mutationFn: (id: string) => unpublishWorkflow(id),
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.workflows.detail(data.id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.workflows.all,
      });
    },
  });
}

export function useCloneWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, newName }: { id: string; newName: string }) =>
      cloneWorkflow(id, newName),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.workflows.all,
      });
    },
  });
}

// ============================================================================
// Workflow Versions Hooks
// ============================================================================

export function useWorkflowVersions(workflowId: string) {
  return useQuery({
    queryKey: queryKeys.workflows.versions(workflowId),
    queryFn: () => getWorkflowVersions(workflowId),
    enabled: !!workflowId,
  });
}

export function useWorkflowVersion(workflowId: string, version: number) {
  return useQuery({
    queryKey: queryKeys.workflows.version(workflowId, version),
    queryFn: () => getWorkflowVersion(workflowId, version),
    enabled: !!workflowId && version > 0,
  });
}

// ============================================================================
// Workflow Executions Hooks
// ============================================================================

export function useWorkflowExecutions(
  workflowId: string,
  params?: Omit<GetExecutionsParams, "workflowId">
) {
  return useQuery({
    queryKey: queryKeys.workflows.executions.list(workflowId, params),
    queryFn: () => getWorkflowExecutions({ workflowId, ...(params ?? {}) }),
    enabled: !!workflowId,
    placeholderData: (previousData) => previousData,
  });
}

export function useWorkflowExecution(workflowId: string, executionId: string) {
  return useQuery({
    queryKey: queryKeys.workflows.executions.detail(workflowId, executionId),
    queryFn: () => getWorkflowExecution(executionId),
    enabled: !!workflowId && !!executionId,
    refetchInterval: (query) => {
      // Poll while execution is running
      const data = query.state.data as WorkflowExecution | undefined;
      if (data?.status === "running" || data?.status === "pending") {
        return 2000; // Poll every 2 seconds
      }
      return false;
    },
  });
}

export function useExecuteWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ workflowId, context }: { workflowId: string; context?: Record<string, unknown> }) =>
      executeWorkflow(workflowId, context),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.workflows.executions.all(variables.workflowId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.workflows.stats(),
      });
    },
  });
}

export function useCancelExecution() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ workflowId, executionId }: { workflowId: string; executionId: string }) =>
      cancelExecution(workflowId, executionId),
    onSuccess: (data, variables) => {
      queryClient.setQueryData(
        queryKeys.workflows.executions.detail(variables.workflowId, variables.executionId),
        data
      );
      queryClient.invalidateQueries({
        queryKey: queryKeys.workflows.executions.all(variables.workflowId),
      });
    },
  });
}

export function useRetryExecution() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ workflowId, executionId }: { workflowId: string; executionId: string }) =>
      retryExecution(workflowId, executionId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.workflows.executions.all(variables.workflowId),
      });
    },
  });
}

export function useExecutionLogs(workflowId: string, executionId: string) {
  return useQuery({
    queryKey: queryKeys.workflows.executions.logs(workflowId, executionId),
    queryFn: () => getExecutionLogs(workflowId, executionId),
    enabled: !!workflowId && !!executionId,
  });
}

// ============================================================================
// Workflow Stats Hook
// ============================================================================

export function useWorkflowStats(params?: { periodDays?: number }) {
  return useQuery({
    queryKey: queryKeys.workflows.stats(params),
    queryFn: () => getWorkflowStats(params),
    staleTime: 2 * 60 * 1000,
  });
}

// ============================================================================
// Re-export types
// ============================================================================

export type {
  GetWorkflowsParams,
  Workflow,
  WorkflowVersion,
  WorkflowExecution,
  ExecutionLog,
  WorkflowStats,
  CreateWorkflowData,
};
