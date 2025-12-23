"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getIntegrations,
  getIntegration,
  createIntegration,
  updateIntegration,
  deleteIntegration,
  enableIntegration,
  disableIntegration,
  testIntegration,
  syncIntegration,
  getIntegrationLogs,
  getAvailableIntegrations,
  type Integration,
  type CreateIntegrationData,
  type IntegrationLog,
  type AvailableIntegration,
} from "@/lib/api/integrations";
import { queryKeys } from "@/lib/api/query-keys";

// ============================================================================
// Integrations Hooks
// ============================================================================

export function useIntegrations() {
  return useQuery({
    queryKey: queryKeys.integrations.all(),
    queryFn: getIntegrations,
  });
}

export function useIntegration(id: string) {
  return useQuery({
    queryKey: queryKeys.integrations.detail(id),
    queryFn: () => getIntegration(id),
    enabled: !!id,
  });
}

export function useCreateIntegration() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createIntegration,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.integrations.all(),
      });
    },
  });
}

export function useUpdateIntegration() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CreateIntegrationData> }) =>
      updateIntegration(id, data),
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.integrations.detail(data.name), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.integrations.all(),
      });
    },
  });
}

export function useDeleteIntegration() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteIntegration,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.integrations.all(),
      });
    },
  });
}

export function useEnableIntegration() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: enableIntegration,
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.integrations.detail(data.name), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.integrations.all(),
      });
    },
  });
}

export function useDisableIntegration() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: disableIntegration,
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.integrations.detail(data.name), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.integrations.all(),
      });
    },
  });
}

export function useTestIntegration() {
  return useMutation({
    mutationFn: testIntegration,
  });
}

export function useSyncIntegration() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: syncIntegration,
    onSuccess: (_, integrationId) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.integrations.detail(integrationId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.integrations.logs(integrationId),
      });
    },
  });
}

// ============================================================================
// Integration Logs Hook
// ============================================================================

export function useIntegrationLogs(integrationId: string, params?: { page?: number; pageSize?: number }) {
  return useQuery({
    queryKey: queryKeys.integrations.logs(integrationId, params),
    queryFn: () => getIntegrationLogs(integrationId, params),
    enabled: !!integrationId,
    placeholderData: (previousData) => previousData,
  });
}

// ============================================================================
// Available Integrations Hook
// ============================================================================

export function useAvailableIntegrations() {
  return useQuery({
    queryKey: queryKeys.integrations.available(),
    queryFn: getAvailableIntegrations,
    staleTime: 60 * 60 * 1000, // 1 hour
  });
}

// ============================================================================
// Re-export types
// ============================================================================

export type {
  Integration,
  CreateIntegrationData,
  IntegrationLog,
  AvailableIntegration,
};
