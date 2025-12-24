"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getPlugins,
  getPlugin,
  getPluginSchema,
  getAvailablePlugins,
  refreshPlugins,
  getPluginInstances,
  getPluginInstance,
  createPluginInstance,
  updatePluginInstance,
  deletePluginInstance,
  getPluginInstanceConfiguration,
  updatePluginInstanceConfiguration,
  testPlugin,
  testPluginInstance,
  getPluginInstanceHealth,
  checkAllInstancesHealth,
  enablePlugin,
  disablePlugin,
  updatePlugin,
  getPluginCategories,
  getPluginsByCategory,
  type Plugin,
  type PluginConfigSchema,
  type PluginInstance,
  type PluginTestResult,
  type PluginStatus,
} from "@/lib/api/plugins";
import { queryKeys } from "@/lib/api/query-keys";

// ============================================================================
// Plugins Hooks
// ============================================================================

export function usePlugins() {
  return useQuery({
    queryKey: queryKeys.plugins.all(),
    queryFn: getPlugins,
  });
}

export function usePlugin(pluginName: string) {
  return useQuery({
    queryKey: queryKeys.plugins.detail(pluginName),
    queryFn: () => getPlugin(pluginName),
    enabled: !!pluginName,
  });
}

export function usePluginSchema(pluginName: string) {
  return useQuery({
    queryKey: queryKeys.plugins.schema(pluginName),
    queryFn: () => getPluginSchema(pluginName),
    enabled: !!pluginName,
  });
}

export function useAvailablePlugins() {
  return useQuery({
    queryKey: queryKeys.plugins.available(),
    queryFn: getAvailablePlugins,
  });
}

export function useRefreshPlugins() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: refreshPlugins,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.plugins.all(),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.plugins.available(),
      });
    },
  });
}

// ============================================================================
// Plugin Actions Hooks
// ============================================================================

export function useEnablePlugin() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: enablePlugin,
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.plugins.detail(data.name), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.plugins.all(),
      });
    },
  });
}

export function useDisablePlugin() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: disablePlugin,
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.plugins.detail(data.name), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.plugins.all(),
      });
    },
  });
}

export function useUpdatePlugin() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: updatePlugin,
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.plugins.detail(data.name), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.plugins.all(),
      });
    },
  });
}

// ============================================================================
// Plugin Instances Hooks
// ============================================================================

export function usePluginInstances(pluginName: string) {
  return useQuery({
    queryKey: queryKeys.plugins.instances.list(pluginName),
    queryFn: () => getPluginInstances(pluginName),
    enabled: !!pluginName,
  });
}

export function usePluginInstance(pluginName: string, instanceId: string) {
  return useQuery({
    queryKey: queryKeys.plugins.instances.detail(pluginName, instanceId),
    queryFn: () => getPluginInstance(pluginName, instanceId),
    enabled: !!pluginName && !!instanceId,
  });
}

export function useCreatePluginInstance() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      pluginName,
      instanceName,
      configuration,
    }: {
      pluginName: string;
      instanceName: string;
      configuration: Record<string, unknown>;
    }) => createPluginInstance(pluginName, { instanceName, configuration }),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.plugins.instances.all(variables.pluginName),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.plugins.detail(variables.pluginName),
      });
    },
  });
}

export function useUpdatePluginInstance() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      pluginName,
      instanceId,
      configuration,
    }: {
      pluginName: string;
      instanceId: string;
      configuration: Record<string, unknown>;
    }) => updatePluginInstance(pluginName, instanceId, configuration),
    onSuccess: (data, variables) => {
      queryClient.setQueryData(
        queryKeys.plugins.instances.detail(variables.pluginName, variables.instanceId),
        data
      );
      queryClient.invalidateQueries({
        queryKey: queryKeys.plugins.instances.all(variables.pluginName),
      });
    },
  });
}

export function useDeletePluginInstance() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ pluginName, instanceId }: { pluginName: string; instanceId: string }) =>
      deletePluginInstance(pluginName, instanceId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.plugins.instances.all(variables.pluginName),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.plugins.detail(variables.pluginName),
      });
    },
  });
}

// ============================================================================
// Plugin Instance Configuration Hooks
// ============================================================================

export function usePluginInstanceConfiguration(instanceId: string) {
  return useQuery({
    queryKey: queryKeys.plugins.instances.configuration(instanceId),
    queryFn: () => getPluginInstanceConfiguration(instanceId),
    enabled: !!instanceId,
  });
}

export function useUpdatePluginInstanceConfiguration() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      instanceId,
      configuration,
    }: {
      instanceId: string;
      configuration: Record<string, unknown>;
    }) => updatePluginInstanceConfiguration(instanceId, configuration),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.plugins.instances.configuration(variables.instanceId),
      });
    },
  });
}

// ============================================================================
// Plugin Testing & Health Hooks
// ============================================================================

export function useTestPlugin() {
  return useMutation({
    mutationFn: testPlugin,
  });
}

export function useTestPluginInstance() {
  return useMutation({
    mutationFn: ({ pluginName, instanceId }: { pluginName: string; instanceId: string }) =>
      testPluginInstance(pluginName, instanceId),
  });
}

export function usePluginInstanceHealth(instanceId: string) {
  return useQuery({
    queryKey: queryKeys.plugins.instances.health(instanceId),
    queryFn: () => getPluginInstanceHealth(instanceId),
    enabled: !!instanceId,
    refetchInterval: 60 * 1000, // Poll every minute
  });
}

export function useCheckAllInstancesHealth() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: checkAllInstancesHealth,
    onSuccess: () => {
      // Invalidate all instance health queries
      queryClient.invalidateQueries({
        queryKey: queryKeys.plugins.instances.all(""),
      });
    },
  });
}

// ============================================================================
// Plugin Categories Hooks
// ============================================================================

export function usePluginCategories() {
  return useQuery({
    queryKey: queryKeys.plugins.categories(),
    queryFn: getPluginCategories,
    staleTime: 60 * 60 * 1000, // 1 hour
  });
}

export function usePluginsByCategory(category: string) {
  return useQuery({
    queryKey: queryKeys.plugins.byCategory(category),
    queryFn: () => getPluginsByCategory(category),
    enabled: !!category,
  });
}

// ============================================================================
// Re-export types
// ============================================================================

export type {
  Plugin,
  PluginConfigSchema,
  PluginInstance,
  PluginTestResult,
  PluginStatus,
};
