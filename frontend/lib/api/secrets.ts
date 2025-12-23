/**
 * Secrets API
 *
 * Secrets management and access metrics (Vault/OpenBao integration)
 */

import { api } from "./client";

// ============================================================================
// Secret Types
// ============================================================================

export interface Secret {
  path: string;
  version: number;
  createdAt: string;
  updatedAt: string;
  metadata?: Record<string, unknown>;
}

export interface SecretValue {
  path: string;
  data: Record<string, unknown>;
  version: number;
  createdAt: string;
}

export interface SecretMetadata {
  path: string;
  currentVersion: number;
  versions: Array<{
    version: number;
    createdAt: string;
    deletedAt?: string;
  }>;
  customMetadata?: Record<string, unknown>;
}

// ============================================================================
// Secret CRUD
// ============================================================================

export async function listSecrets(path?: string): Promise<Secret[]> {
  return api.get<Secret[]>("/api/v1/secrets", {
    params: { path },
  });
}

export async function getSecret(path: string, version?: number): Promise<SecretValue> {
  return api.get<SecretValue>(`/api/v1/secrets/${encodeURIComponent(path)}`, {
    params: { version },
  });
}

export async function getSecretMetadata(path: string): Promise<SecretMetadata> {
  return api.get<SecretMetadata>(`/api/v1/secrets/${encodeURIComponent(path)}/metadata`);
}

export async function createSecret(
  path: string,
  data: Record<string, unknown>,
  metadata?: Record<string, unknown>
): Promise<SecretValue> {
  return api.post<SecretValue>(`/api/v1/secrets/${encodeURIComponent(path)}`, {
    data,
    metadata,
  });
}

export async function updateSecret(
  path: string,
  data: Record<string, unknown>,
  metadata?: Record<string, unknown>
): Promise<SecretValue> {
  return api.patch<SecretValue>(`/api/v1/secrets/${encodeURIComponent(path)}`, {
    data,
    metadata,
  });
}

export async function deleteSecret(path: string, versions?: number[]): Promise<void> {
  return api.delete(`/api/v1/secrets/${encodeURIComponent(path)}`, {
    params: { versions: versions?.join(",") },
  });
}

export async function undeleteSecret(path: string, versions: number[]): Promise<void> {
  return api.post(`/api/v1/secrets/${encodeURIComponent(path)}/undelete`, {
    versions,
  });
}

export async function destroySecret(path: string, versions: number[]): Promise<void> {
  return api.post(`/api/v1/secrets/${encodeURIComponent(path)}/destroy`, {
    versions,
  });
}

// ============================================================================
// Secret Health
// ============================================================================

export async function getSecretsHealth(): Promise<{
  status: "healthy" | "degraded" | "down";
  sealed: boolean;
  version: string;
  clusterName?: string;
}> {
  return api.get("/api/v1/secrets/health");
}

// ============================================================================
// Secret Metrics
// ============================================================================

export interface SecretsMetrics {
  totalSecretsAccessed: number;
  uniqueSecrets: number;
  avgAccessesPerSecret: number;
  accessPatterns: {
    reads: number;
    writes: number;
    deletes: number;
  };
  topSecrets: Array<{
    path: string;
    accessCount: number;
  }>;
  topUsers: Array<{
    userId: string;
    accessCount: number;
  }>;
  failedAccesses: number;
  afterHoursAccess: number;
  recentActivity: Array<{
    date: string;
    accessCount: number;
  }>;
  period: string;
  timestamp: string;
}

export async function getSecretsMetrics(params?: {
  periodDays?: number;
}): Promise<SecretsMetrics> {
  return api.get<SecretsMetrics>("/api/v1/metrics/secrets", {
    params: { period_days: params?.periodDays },
  });
}

// ============================================================================
// Secret Rotation
// ============================================================================

export async function rotateSecret(
  path: string,
  newData: Record<string, unknown>
): Promise<SecretValue> {
  return api.post<SecretValue>(`/api/v1/secrets/${encodeURIComponent(path)}/rotate`, {
    data: newData,
  });
}

export interface RotationPolicy {
  path: string;
  rotationPeriodDays: number;
  lastRotatedAt?: string;
  nextRotationAt?: string;
  isEnabled: boolean;
}

export async function getRotationPolicies(): Promise<RotationPolicy[]> {
  return api.get<RotationPolicy[]>("/api/v1/secrets/rotation-policies");
}

export async function setRotationPolicy(
  path: string,
  policy: {
    rotationPeriodDays: number;
    isEnabled: boolean;
  }
): Promise<RotationPolicy> {
  return api.post<RotationPolicy>(`/api/v1/secrets/${encodeURIComponent(path)}/rotation-policy`, {
    rotation_period_days: policy.rotationPeriodDays,
    is_enabled: policy.isEnabled,
  });
}
