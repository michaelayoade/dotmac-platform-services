/**
 * Integrations API
 *
 * External service integrations and health monitoring
 */

import { api, ApiClientError } from "./client";

// ============================================================================
// Integration Types
// ============================================================================

export type IntegrationType =
  | "email"
  | "sms"
  | "storage"
  | "payment"
  | "analytics"
  | "monitoring"
  | "authentication"
  | "notification"
  | "custom";

export type IntegrationStatus = "connected" | "disconnected" | "error" | "pending" | string;

export interface Integration {
  name: string;
  type: IntegrationType | string;
  provider: string;
  enabled: boolean;
  status: IntegrationStatus;
  message?: string | null;
  lastCheck?: string | null;
  settingsCount: number;
  hasSecrets: boolean;
  requiredPackages: string[];
  metadata?: Record<string, unknown>;
}

export interface IntegrationHealth {
  name: string;
  status: IntegrationStatus;
  message?: string;
  latencyMs?: number;
  lastCheck?: string;
  metadata?: Record<string, unknown>;
}

export interface AvailableIntegration {
  type: string;
  provider: string;
  name: string;
  description?: string;
  configSchema?: Record<string, unknown>;
  iconUrl?: string;
}

export interface IntegrationLog {
  id: string;
  message: string;
  level: string;
  timestamp: string;
}

// ============================================================================
// Integration Discovery
// ============================================================================

export async function getIntegrations(): Promise<{ integrations: Integration[]; total: number }> {
  return api.get<{ integrations: Integration[]; total: number }>("/api/v1/integrations");
}

export async function getIntegration(name: string): Promise<Integration> {
  return api.get<Integration>(`/api/v1/integrations/${name}`);
}

export async function getAvailableIntegrations(): Promise<AvailableIntegration[]> {
  throw new ApiClientError("Available integrations are not exposed by the backend", 501, "NOT_IMPLEMENTED");
}

// ============================================================================
// Integration CRUD (not supported)
// ============================================================================

export interface CreateIntegrationData {
  name: string;
  type: IntegrationType;
  provider: string;
  config: Record<string, unknown>;
  isEnabled?: boolean;
}

export async function createIntegration(_data: CreateIntegrationData): Promise<Integration> {
  throw new ApiClientError("Creating integrations is not supported", 501, "NOT_IMPLEMENTED");
}

export async function updateIntegration(
  _id: string,
  _data: Partial<CreateIntegrationData>
): Promise<Integration> {
  throw new ApiClientError("Updating integrations is not supported", 501, "NOT_IMPLEMENTED");
}

export async function deleteIntegration(_id: string): Promise<void> {
  throw new ApiClientError("Deleting integrations is not supported", 501, "NOT_IMPLEMENTED");
}

// ============================================================================
// Integration Health & Testing
// ============================================================================

export async function getIntegrationHealth(): Promise<IntegrationHealth[]> {
  const response = await getIntegrations();
  return response.integrations.map((integration) => ({
    name: integration.name,
    status: integration.status,
    message: integration.message ?? undefined,
    lastCheck: integration.lastCheck ?? undefined,
    metadata: integration.metadata,
  }));
}

export async function testIntegration(name: string): Promise<Integration> {
  return api.post<Integration>(`/api/v1/integrations/${name}/health-check`);
}

export async function refreshIntegration(name: string): Promise<Integration> {
  return testIntegration(name);
}

// ============================================================================
// Integration Actions (not supported)
// ============================================================================

export async function enableIntegration(_id: string): Promise<Integration> {
  throw new ApiClientError("Enabling integrations is not supported", 501, "NOT_IMPLEMENTED");
}

export async function disableIntegration(_id: string): Promise<Integration> {
  throw new ApiClientError("Disabling integrations is not supported", 501, "NOT_IMPLEMENTED");
}

export async function syncIntegration(_id: string): Promise<{ synced: boolean }> {
  throw new ApiClientError("Syncing integrations is not supported", 501, "NOT_IMPLEMENTED");
}

export async function getIntegrationLogs(
  _integrationId: string,
  _params?: { page?: number; pageSize?: number }
): Promise<{ logs: IntegrationLog[]; totalCount: number; pageCount: number }> {
  throw new ApiClientError("Integration logs are not supported", 501, "NOT_IMPLEMENTED");
}
