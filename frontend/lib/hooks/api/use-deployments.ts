"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, normalizePaginatedResponse } from "@/lib/api/client";
import { queryKeys } from "@/lib/api/query-keys";
import type {
  Deployment,
  DeploymentStatus,
  DeploymentEnvironment,
  DeploymentResources,
  DeploymentMetrics,
} from "@/types/models";
import type { PaginatedResponse, ListQueryParams } from "@/types/api";

// Types
export interface ListDeploymentsParams extends ListQueryParams {
  status?: DeploymentStatus;
  environment?: DeploymentEnvironment;
}

export interface CreateDeploymentData {
  name: string;
  environment: DeploymentEnvironment;
  image: string;
  version: string;
  replicas?: number;
  resources?: DeploymentResources;
  envVars?: Record<string, string>;
}

export interface UpdateDeploymentData {
  name?: string;
  replicas?: number;
  resources?: DeploymentResources;
  envVars?: Record<string, string>;
}

export interface ScaleDeploymentData {
  replicas: number;
  resources?: DeploymentResources;
}

export interface DeploymentStatusResponse {
  status: DeploymentStatus;
  health: "healthy" | "degraded" | "unhealthy";
  replicas: {
    desired: number;
    ready: number;
    available: number;
  };
  lastUpdated: string;
  events: Array<{
    type: string;
    message: string;
    timestamp: string;
  }>;
}

export interface DeploymentLogs {
  logs: Array<{
    timestamp: string;
    level: "info" | "warn" | "error";
    message: string;
    pod?: string;
  }>;
  cursor?: string;
}

type DeploymentsResponse = PaginatedResponse<Deployment>;

// API functions
async function getDeployments(
  params?: ListDeploymentsParams
): Promise<DeploymentsResponse> {
  const response = await api.get<unknown>("/api/v1/deployments", {
    params: {
      page: params?.page ?? 1,
      page_size: params?.pageSize ?? 10,
      sort_by: params?.sort?.[0]?.field,
      sort_order: params?.sort?.[0]?.direction,
      search: params?.search,
      status: params?.status,
      environment: params?.environment,
    },
  });
  return normalizePaginatedResponse<Deployment>(response);
}

async function getDeployment(id: string): Promise<Deployment> {
  return api.get<Deployment>(`/api/v1/deployments/${id}`);
}

async function createDeployment(data: CreateDeploymentData): Promise<Deployment> {
  return api.post<Deployment>("/api/v1/deployments", data);
}

async function updateDeployment({
  id,
  data,
}: {
  id: string;
  data: UpdateDeploymentData;
}): Promise<Deployment> {
  return api.patch<Deployment>(`/api/v1/deployments/${id}`, data);
}

async function deleteDeployment(id: string): Promise<void> {
  return api.delete<void>(`/api/v1/deployments/${id}`);
}

async function provisionDeployment(id: string): Promise<Deployment> {
  return api.post<Deployment>(`/api/v1/deployments/${id}/provision`);
}

async function destroyDeployment(id: string): Promise<Deployment> {
  return api.post<Deployment>(`/api/v1/deployments/${id}/destroy`);
}

async function scaleDeployment({
  id,
  data,
}: {
  id: string;
  data: ScaleDeploymentData;
}): Promise<Deployment> {
  return api.patch<Deployment>(`/api/v1/deployments/${id}/scale`, data);
}

async function restartDeployment(id: string): Promise<Deployment> {
  return api.post<Deployment>(`/api/v1/deployments/${id}/restart`);
}

async function upgradeDeployment({
  id,
  version,
}: {
  id: string;
  version: string;
}): Promise<Deployment> {
  return api.post<Deployment>(`/api/v1/deployments/${id}/upgrade`, { version });
}

async function getDeploymentStatus(id: string): Promise<DeploymentStatusResponse> {
  return api.get<DeploymentStatusResponse>(`/api/v1/deployments/${id}/status`);
}

async function getDeploymentMetrics(id: string): Promise<DeploymentMetrics> {
  return api.get<DeploymentMetrics>(`/api/v1/deployments/${id}/metrics`);
}

async function getDeploymentLogs(
  id: string,
  params?: { cursor?: string; limit?: number }
): Promise<DeploymentLogs> {
  return api.get<DeploymentLogs>(`/api/v1/deployments/${id}/logs`, { params });
}

// Hooks
export function useDeployments(params?: ListDeploymentsParams) {
  return useQuery({
    queryKey: queryKeys.deployments.list(params),
    queryFn: () => getDeployments(params),
    placeholderData: (previousData) => previousData,
  });
}

export function useDeployment(id: string) {
  return useQuery({
    queryKey: queryKeys.deployments.detail(id),
    queryFn: () => getDeployment(id),
    enabled: !!id,
  });
}

export function useCreateDeployment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createDeployment,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.deployments.all });
    },
  });
}

export function useUpdateDeployment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: updateDeployment,
    onSuccess: (data, { id }) => {
      queryClient.setQueryData(queryKeys.deployments.detail(id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.deployments.lists(),
      });
    },
  });
}

export function useDeleteDeployment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteDeployment,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.deployments.all });
    },
  });
}

export function useProvisionDeployment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: provisionDeployment,
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.deployments.detail(data.id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.deployments.lists(),
      });
    },
  });
}

export function useDestroyDeployment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: destroyDeployment,
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.deployments.detail(data.id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.deployments.lists(),
      });
    },
  });
}

export function useScaleDeployment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: scaleDeployment,
    onSuccess: (data, { id }) => {
      queryClient.setQueryData(queryKeys.deployments.detail(id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.deployments.status(id),
      });
    },
  });
}

export function useRestartDeployment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: restartDeployment,
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.deployments.detail(data.id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.deployments.status(data.id),
      });
    },
  });
}

export function useUpgradeDeployment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: upgradeDeployment,
    onSuccess: (data, { id }) => {
      queryClient.setQueryData(queryKeys.deployments.detail(id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.deployments.status(id),
      });
    },
  });
}

export function useDeploymentStatus(id: string, options?: { refetchInterval?: number }) {
  return useQuery({
    queryKey: queryKeys.deployments.status(id),
    queryFn: () => getDeploymentStatus(id),
    enabled: !!id,
    refetchInterval: options?.refetchInterval ?? 10000, // Poll every 10 seconds
  });
}

export function useDeploymentMetrics(id: string) {
  return useQuery({
    queryKey: [...queryKeys.deployments.detail(id), "metrics"],
    queryFn: () => getDeploymentMetrics(id),
    enabled: !!id,
    refetchInterval: 30000, // Poll every 30 seconds
  });
}

export function useDeploymentLogs(
  id: string,
  params?: { cursor?: string; limit?: number }
) {
  return useQuery({
    queryKey: queryKeys.deployments.logs(id),
    queryFn: () => getDeploymentLogs(id, params),
    enabled: !!id,
  });
}

// ============================================
// Deployment Configuration API and Hooks
// ============================================

export interface DeploymentConfig {
  envVars: Record<string, string>;
  resources: DeploymentResources;
  scaling: {
    minReplicas: number;
    maxReplicas: number;
    targetCpuUtilization: number;
  };
  healthCheck: {
    enabled: boolean;
    path: string;
    interval: number;
    timeout: number;
    healthyThreshold: number;
    unhealthyThreshold: number;
  };
  network: {
    port: number;
    protocol: "http" | "https" | "grpc";
    publicAccess: boolean;
    customDomain?: string;
  };
}

export interface UpdateConfigData {
  envVars?: Record<string, string>;
  resources?: DeploymentResources;
  scaling?: Partial<DeploymentConfig["scaling"]>;
  healthCheck?: Partial<DeploymentConfig["healthCheck"]>;
  network?: Partial<DeploymentConfig["network"]>;
}

async function getDeploymentConfig(id: string): Promise<DeploymentConfig> {
  return api.get<DeploymentConfig>(`/api/v1/deployments/${id}/config`);
}

async function updateDeploymentConfig({
  id,
  data,
}: {
  id: string;
  data: UpdateConfigData;
}): Promise<DeploymentConfig> {
  return api.patch<DeploymentConfig>(`/api/v1/deployments/${id}/config`, data);
}

export function useDeploymentConfig(id: string) {
  return useQuery({
    queryKey: [...queryKeys.deployments.detail(id), "config"],
    queryFn: () => getDeploymentConfig(id),
    enabled: !!id,
  });
}

export function useUpdateDeploymentConfig() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: updateDeploymentConfig,
    onSuccess: (data, { id }) => {
      queryClient.setQueryData(
        [...queryKeys.deployments.detail(id), "config"],
        data
      );
    },
  });
}
