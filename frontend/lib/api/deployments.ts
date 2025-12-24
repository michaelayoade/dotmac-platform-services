/**
 * Deployments API
 *
 * Deployment orchestration data fetching and mutations
 * Connected to real backend endpoints
 */

import { api, normalizePaginatedResponse } from "./client";

export interface Deployment {
  id: string;
  name: string;
  status: "running" | "pending" | "stopped" | "failed" | "provisioning" | "scaling";
  environment: "production" | "staging" | "development";
  tenantId: string;
  region: string;
  version: string;
  replicas: number;
  resources: {
    cpu: string;
    memory: string;
    storage?: string;
  };
  health: {
    status: "healthy" | "unhealthy" | "unknown";
    lastCheck: string;
    checks: Array<{
      name: string;
      status: "passing" | "failing" | "warning";
      message?: string;
    }>;
  };
  url?: string;
  createdAt: string;
  updatedAt: string;
  lastDeployedAt?: string;
}

export interface DeploymentMetrics {
  cpuUsage: number;
  memoryUsage: number;
  requestsPerMinute: number;
  errorRate: number;
  averageResponseTime: number;
  uptime: number;
}

export interface GetDeploymentsParams {
  page?: number;
  pageSize?: number;
  search?: string;
  status?: Deployment["status"];
  environment?: Deployment["environment"];
  tenantId?: string;
  sortBy?: string;
  sortOrder?: "asc" | "desc";
}

export async function getDeployments(params: GetDeploymentsParams = {}): Promise<{
  deployments: Deployment[];
  totalCount: number;
  pageCount: number;
}> {
  const { page = 1, pageSize = 20, search, status, environment, tenantId, sortBy, sortOrder } =
    params;

  const response = await api.get<unknown>("/api/v1/deployments", {
    params: {
      page,
      page_size: pageSize,
      search,
      status,
      environment,
      tenant_id: tenantId,
      sort_by: sortBy,
      sort_order: sortOrder,
    },
  });
  const normalized = normalizePaginatedResponse<Deployment>(response);

  return {
    deployments: normalized.items,
    totalCount: normalized.total,
    pageCount: normalized.totalPages,
  };
}

export async function getDeployment(id: string): Promise<Deployment> {
  return api.get<Deployment>(`/api/v1/deployments/${id}`);
}

export async function getDeploymentStatus(id: string): Promise<{
  status: Deployment["status"];
  health: Deployment["health"];
  lastUpdated: string;
}> {
  return api.get(`/api/v1/deployments/${id}/status`);
}

export async function getDeploymentMetrics(id: string): Promise<DeploymentMetrics> {
  return api.get<DeploymentMetrics>(`/api/v1/deployments/${id}/metrics`);
}

export interface CreateDeploymentData {
  name: string;
  environment: Deployment["environment"];
  region: string;
  version: string;
  replicas?: number;
  resources?: {
    cpu: string;
    memory: string;
    storage?: string;
  };
  config?: Record<string, unknown>;
}

export async function createDeployment(data: CreateDeploymentData): Promise<Deployment> {
  return api.post<Deployment>("/api/v1/deployments", data);
}

export interface UpdateDeploymentData {
  name?: string;
  version?: string;
  replicas?: number;
  resources?: {
    cpu: string;
    memory: string;
    storage?: string;
  };
  config?: Record<string, unknown>;
}

export async function updateDeployment(id: string, data: UpdateDeploymentData): Promise<Deployment> {
  return api.patch<Deployment>(`/api/v1/deployments/${id}`, data);
}

export async function deleteDeployment(id: string): Promise<void> {
  return api.delete(`/api/v1/deployments/${id}`);
}

// Deployment actions
export async function startDeployment(id: string): Promise<Deployment> {
  return api.post<Deployment>(`/api/v1/deployments/${id}/start`);
}

export async function stopDeployment(id: string): Promise<Deployment> {
  return api.post<Deployment>(`/api/v1/deployments/${id}/stop`);
}

export async function restartDeployment(id: string): Promise<Deployment> {
  return api.post<Deployment>(`/api/v1/deployments/${id}/restart`);
}

export async function scaleDeployment(id: string, replicas: number): Promise<Deployment> {
  return api.post<Deployment>(`/api/v1/deployments/${id}/scale`, { replicas });
}

export async function redeployDeployment(id: string, version?: string): Promise<Deployment> {
  return api.post<Deployment>(`/api/v1/deployments/${id}/redeploy`, { version });
}

export async function rollbackDeployment(id: string, targetVersion: string): Promise<Deployment> {
  return api.post<Deployment>(`/api/v1/deployments/${id}/rollback`, {
    target_version: targetVersion,
  });
}

// Deployment logs
export interface DeploymentLog {
  timestamp: string;
  level: "info" | "warning" | "error" | "debug";
  message: string;
  source?: string;
}

export async function getDeploymentLogs(
  id: string,
  params?: {
    since?: string;
    until?: string;
    level?: DeploymentLog["level"];
    limit?: number;
  }
): Promise<DeploymentLog[]> {
  return api.get<DeploymentLog[]>(`/api/v1/deployments/${id}/logs`, { params });
}

// Deployment events
export interface DeploymentEvent {
  id: string;
  type: "created" | "started" | "stopped" | "scaled" | "deployed" | "failed" | "health_changed";
  message: string;
  timestamp: string;
  actor?: {
    id: string;
    name: string;
  };
  metadata?: Record<string, unknown>;
}

export async function getDeploymentEvents(id: string, limit = 50): Promise<DeploymentEvent[]> {
  return api.get<DeploymentEvent[]>(`/api/v1/deployments/${id}/events`, {
    params: { limit },
  });
}

// Deployment versions
export interface DeploymentVersion {
  version: string;
  deployedAt: string;
  deployedBy: {
    id: string;
    name: string;
  };
  status: "current" | "previous" | "available";
  changelog?: string;
}

export async function getDeploymentVersions(id: string): Promise<DeploymentVersion[]> {
  return api.get<DeploymentVersion[]>(`/api/v1/deployments/${id}/versions`);
}
