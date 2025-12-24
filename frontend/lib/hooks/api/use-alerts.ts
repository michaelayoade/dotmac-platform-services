"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getAlertChannels,
  getAlertChannel,
  createAlertChannel,
  updateAlertChannel,
  deleteAlertChannel,
  testAlertChannel,
  enableAlertChannel,
  disableAlertChannel,
  getAlertRules,
  getAlertRule,
  createAlertRule,
  updateAlertRule,
  deleteAlertRule,
  enableAlertRule,
  disableAlertRule,
  getAlertHistory,
  acknowledgeAlert,
  resolveAlert,
  getAlertStats,
  type AlertChannel,
  type CreateAlertChannelData,
  type AlertTestResult,
  type AlertRule,
  type CreateAlertRuleData,
  type AlertHistoryParams,
  type AlertEvent,
  type AlertStats,
} from "@/lib/api/alerts";
import { queryKeys } from "@/lib/api/query-keys";

// ============================================================================
// Alert Channels Hooks
// ============================================================================

export function useAlertChannels() {
  return useQuery({
    queryKey: queryKeys.alerts.channels.all(),
    queryFn: getAlertChannels,
  });
}

export function useAlertChannel(id: string) {
  return useQuery({
    queryKey: queryKeys.alerts.channels.detail(id),
    queryFn: () => getAlertChannel(id),
    enabled: !!id,
  });
}

export function useCreateAlertChannel() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createAlertChannel,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.alerts.channels.all(),
      });
    },
  });
}

export function useUpdateAlertChannel() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: CreateAlertChannelData }) =>
      updateAlertChannel(id, data),
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.alerts.channels.detail(data.id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.alerts.channels.all(),
      });
    },
  });
}

export function useDeleteAlertChannel() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteAlertChannel,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.alerts.channels.all(),
      });
    },
  });
}

export function useTestAlertChannel() {
  return useMutation({
    mutationFn: testAlertChannel,
  });
}

export function useEnableAlertChannel() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: enableAlertChannel,
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.alerts.channels.detail(data.id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.alerts.channels.all(),
      });
    },
  });
}

export function useDisableAlertChannel() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: disableAlertChannel,
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.alerts.channels.detail(data.id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.alerts.channels.all(),
      });
    },
  });
}

// ============================================================================
// Alert Rules Hooks
// ============================================================================

export function useAlertRules() {
  return useQuery({
    queryKey: queryKeys.alerts.rules.all(),
    queryFn: getAlertRules,
  });
}

export function useAlertRule(id: string) {
  return useQuery({
    queryKey: queryKeys.alerts.rules.detail(id),
    queryFn: () => getAlertRule(id),
    enabled: !!id,
  });
}

export function useCreateAlertRule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createAlertRule,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.alerts.rules.all(),
      });
    },
  });
}

export function useUpdateAlertRule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CreateAlertRuleData> }) =>
      updateAlertRule(id, data),
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.alerts.rules.detail(data.id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.alerts.rules.all(),
      });
    },
  });
}

export function useDeleteAlertRule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteAlertRule,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.alerts.rules.all(),
      });
    },
  });
}

export function useEnableAlertRule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: enableAlertRule,
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.alerts.rules.detail(data.id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.alerts.rules.all(),
      });
    },
  });
}

export function useDisableAlertRule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: disableAlertRule,
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.alerts.rules.detail(data.id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.alerts.rules.all(),
      });
    },
  });
}

// ============================================================================
// Alert History Hooks
// ============================================================================

export function useAlertHistory(params?: AlertHistoryParams) {
  return useQuery({
    queryKey: queryKeys.alerts.history.list(params),
    queryFn: () => getAlertHistory(params),
    placeholderData: (previousData) => previousData,
  });
}

export function useAcknowledgeAlert() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ alertId, note }: { alertId: string; note?: string }) =>
      acknowledgeAlert(alertId, note),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.alerts.history.all(),
      });
    },
  });
}

export function useResolveAlert() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ alertId, resolution }: { alertId: string; resolution?: string }) =>
      resolveAlert(alertId, resolution),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.alerts.history.all(),
      });
    },
  });
}

// ============================================================================
// Alert Stats Hook
// ============================================================================

export function useAlertStats(params?: { periodDays?: number }) {
  return useQuery({
    queryKey: queryKeys.alerts.stats(params),
    queryFn: () => getAlertStats(params),
    staleTime: 2 * 60 * 1000,
  });
}

// ============================================================================
// Re-export types
// ============================================================================

export type {
  AlertChannel,
  CreateAlertChannelData,
  AlertTestResult,
  AlertRule,
  CreateAlertRuleData,
  AlertHistoryParams,
  AlertEvent,
  AlertStats,
};
