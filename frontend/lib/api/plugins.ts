/**
 * Plugins API
 *
 * Plugin discovery, management, and instance configuration
 */

import { api } from "./client";

// ============================================================================
// Plugin Types
// ============================================================================

export type PluginStatus = "active" | "inactive" | "error" | "updating";

export interface PluginConfigSchema {
  type: "object";
  properties: Record<
    string,
    {
      type: string;
      title?: string;
      description?: string;
      default?: unknown;
      enum?: unknown[];
      required?: boolean;
      secret?: boolean;
    }
  >;
  required?: string[];
}

export interface Plugin {
  id: string;
  name: string;
  version?: string;
  description?: string;
  author?: string;
  homepage?: string;
  category?: string;
  iconUrl?: string;
  configSchema?: PluginConfigSchema;
  capabilities?: string[];
  isBuiltIn?: boolean;
  isEnabled?: boolean;
  enabled?: boolean;
  instanceCount?: number;
  createdAt?: string;
  updatedAt?: string;
}

export interface PluginInstance {
  id: string;
  pluginId: string;
  pluginName: string;
  instanceName: string;
  configuration: Record<string, unknown>;
  status: PluginStatus;
  lastError?: string;
  lastHealthCheck?: string;
  createdAt: string;
  updatedAt: string;
}

// ============================================================================
// Plugin Discovery
// ============================================================================

export async function getPlugins(): Promise<Plugin[]> {
  return api.get<Plugin[]>("/api/v1/plugins");
}

export async function getPlugin(pluginName: string): Promise<Plugin> {
  return api.get<Plugin>(`/api/v1/plugins/${encodeURIComponent(pluginName)}`);
}

export async function getPluginSchema(pluginName: string): Promise<PluginConfigSchema> {
  return api.get<PluginConfigSchema>(`/api/v1/plugins/${encodeURIComponent(pluginName)}/schema`);
}

export interface AvailablePlugin {
  name: string;
  version: string;
  description: string;
  category: string;
  author?: string;
  homepage?: string;
}

export async function getAvailablePlugins(): Promise<AvailablePlugin[]> {
  const plugins = await api.get<
    Array<{
      name: string;
      type: string;
      version: string;
      description: string;
      author?: string;
      homepage?: string;
    }>
  >("/api/v1/plugins/available");

  return plugins.map((plugin) => ({
    name: plugin.name,
    version: plugin.version,
    description: plugin.description,
    category: plugin.type,
    author: plugin.author,
    homepage: plugin.homepage,
  }));
}

export async function refreshPlugins(): Promise<{ discovered: number }> {
  return api.post<{ discovered: number }>("/api/v1/plugins/refresh");
}

// ============================================================================
// Plugin Instance Management
// ============================================================================

export async function getPluginInstances(pluginName: string): Promise<PluginInstance[]> {
  return api.get<PluginInstance[]>(`/api/v1/plugins/${encodeURIComponent(pluginName)}/instances`);
}

export async function getPluginInstance(
  pluginName: string,
  instanceId: string
): Promise<PluginInstance> {
  return api.get<PluginInstance>(
    `/api/v1/plugins/${encodeURIComponent(pluginName)}/instances/${instanceId}`
  );
}

export async function createPluginInstance(
  pluginName: string,
  data: {
    instanceName: string;
    configuration: Record<string, unknown>;
  }
): Promise<PluginInstance> {
  return api.post<PluginInstance>(`/api/v1/plugins/${encodeURIComponent(pluginName)}/instances`, {
    instance_name: data.instanceName,
    configuration: data.configuration,
  });
}

export async function updatePluginInstance(
  pluginName: string,
  instanceId: string,
  configuration: Record<string, unknown>
): Promise<PluginInstance> {
  return api.patch<PluginInstance>(
    `/api/v1/plugins/${encodeURIComponent(pluginName)}/instances/${instanceId}`,
    { configuration }
  );
}

export async function deletePluginInstance(pluginName: string, instanceId: string): Promise<void> {
  return api.delete(`/api/v1/plugins/${encodeURIComponent(pluginName)}/instances/${instanceId}`);
}

// ============================================================================
// Plugin Instance Configuration
// ============================================================================

export async function getPluginInstanceConfiguration(
  instanceId: string
): Promise<Record<string, unknown>> {
  return api.get<Record<string, unknown>>(`/api/v1/plugins/instances/${instanceId}/configuration`);
}

export async function updatePluginInstanceConfiguration(
  instanceId: string,
  configuration: Record<string, unknown>
): Promise<PluginInstance> {
  return api.put<PluginInstance>(`/api/v1/plugins/instances/${instanceId}/configuration`, {
    configuration,
  });
}

// ============================================================================
// Plugin Testing & Health
// ============================================================================

export interface PluginTestResult {
  success: boolean;
  message: string;
  latencyMs?: number;
  details?: Record<string, unknown>;
}

export async function testPlugin(pluginName: string): Promise<PluginTestResult> {
  return api.post<PluginTestResult>(`/api/v1/plugins/${encodeURIComponent(pluginName)}/test`);
}

export async function testPluginInstance(
  pluginName: string,
  instanceId: string
): Promise<PluginTestResult> {
  return api.post<PluginTestResult>(
    `/api/v1/plugins/${encodeURIComponent(pluginName)}/instances/${instanceId}/test`
  );
}

export async function getPluginInstanceHealth(
  instanceId: string
): Promise<{
  status: PluginStatus;
  lastCheck: string;
  message?: string;
  metrics?: Record<string, number>;
}> {
  return api.get(`/api/v1/plugins/instances/${instanceId}/health`);
}

export async function checkAllInstancesHealth(): Promise<
  Array<{
    instanceId: string;
    pluginName: string;
    instanceName: string;
    status: PluginStatus;
    message?: string;
  }>
> {
  return api.post("/api/v1/plugins/instances/health-check");
}

// ============================================================================
// Plugin Actions
// ============================================================================

export async function enablePlugin(pluginName: string): Promise<Plugin> {
  return api.post<Plugin>(`/api/v1/plugins/${encodeURIComponent(pluginName)}/enable`);
}

export async function disablePlugin(pluginName: string): Promise<Plugin> {
  return api.post<Plugin>(`/api/v1/plugins/${encodeURIComponent(pluginName)}/disable`);
}

export async function updatePlugin(pluginName: string): Promise<Plugin> {
  return api.patch<Plugin>(`/api/v1/plugins/${encodeURIComponent(pluginName)}`, {
    action: "update",
  });
}

// ============================================================================
// Plugin Categories
// ============================================================================

export async function getPluginCategories(): Promise<
  Array<{
    name: string;
    description: string;
    pluginCount: number;
  }>
> {
  return api.get("/api/v1/plugins/categories");
}

export async function getPluginsByCategory(category: string): Promise<Plugin[]> {
  return api.get<Plugin[]>("/api/v1/plugins", {
    params: { category },
  });
}
