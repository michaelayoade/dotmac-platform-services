/**
 * Deployments API
 *
 * Deployment orchestration data fetching and mutations
 * Connected to real backend endpoints
 */

import { api, normalizePaginatedResponse } from "./client";

// ============================================================================
// Backend API Response Types
// ============================================================================

interface DeploymentApiResponse {
  id: string;
  tenantId: string;
  templateId?: number;
  environment: string;
  state: string;
  stateReason?: string;
  version: string;
  name?: string;
  replicas?: number;
  region?: string;
  availabilityZone?: string;
  endpoints?: Record<string, string>;
  allocatedCpu?: number;
  allocatedMemoryGb?: number;
  allocatedStorageGb?: number;
  healthStatus?: string;
  healthDetails?: Record<string, unknown>;
  lastHealthCheck?: string;
  createdAt: string;
  updatedAt: string;
}

// ============================================================================
// Frontend Types
// ============================================================================

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

// ============================================================================
// Transformer Functions
// ============================================================================

const STATE_TO_STATUS: Record<string, Deployment["status"]> = {
  provisioned: "running",
  running: "running",
  active: "running",
  provisioning: "provisioning",
  pending: "pending",
  suspended: "stopped",
  stopped: "stopped",
  failed: "failed",
  error: "failed",
  scaling: "scaling",
};

const ENVIRONMENT_MAP: Record<string, Deployment["environment"]> = {
  prod: "production",
  production: "production",
  staging: "staging",
  stage: "staging",
  dev: "development",
  development: "development",
  test: "development",
};

function toDeployment(api: DeploymentApiResponse): Deployment {
  const status = STATE_TO_STATUS[api.state?.toLowerCase()] || "pending";
  const environment = ENVIRONMENT_MAP[api.environment?.toLowerCase()] || "development";

  // Parse health checks from health details if available
  const healthChecks: Deployment["health"]["checks"] = [];
  if (api.healthDetails && typeof api.healthDetails === "object") {
    const details = api.healthDetails as Record<string, unknown>;
    if (Array.isArray(details.checks)) {
      for (const check of details.checks) {
        if (typeof check === "object" && check !== null) {
          const c = check as Record<string, unknown>;
          healthChecks.push({
            name: String(c.name || "unknown"),
            status: (c.status as "passing" | "failing" | "warning") || "warning",
            message: c.message ? String(c.message) : undefined,
          });
        }
      }
    }
  }

  return {
    id: api.id,
    name: api.name || api.id,
    status,
    environment,
    tenantId: api.tenantId,
    region: api.region || api.availabilityZone || "",
    version: api.version,
    replicas: api.replicas || 1,
    resources: {
      cpu: api.allocatedCpu ? `${api.allocatedCpu}` : "1",
      memory: api.allocatedMemoryGb ? `${api.allocatedMemoryGb}GB` : "1GB",
      storage: api.allocatedStorageGb ? `${api.allocatedStorageGb}GB` : undefined,
    },
    health: {
      status: (api.healthStatus as "healthy" | "unhealthy" | "unknown") || "unknown",
      lastCheck: api.lastHealthCheck || new Date().toISOString(),
      checks: healthChecks,
    },
    url: api.endpoints ? Object.values(api.endpoints)[0] : undefined,
    createdAt: api.createdAt,
    updatedAt: api.updatedAt,
  };
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
  const normalized = normalizePaginatedResponse<DeploymentApiResponse>(response);

  return {
    deployments: normalized.items.map(toDeployment),
    totalCount: normalized.total,
    pageCount: normalized.totalPages,
  };
}

export async function getDeployment(id: string): Promise<Deployment> {
  const response = await api.get<DeploymentApiResponse>(`/api/v1/deployments/${id}`);
  return toDeployment(response);
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
