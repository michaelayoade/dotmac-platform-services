"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getLogs,
  getLogEntry,
  getLogStats,
  getLogServices,
  searchLogs,
  exportLogs,
  type GetLogsParams,
  type LogEntry,
  type LogStats,
} from "@/lib/api/monitoring";
import { queryKeys } from "@/lib/api/query-keys";

type LogStatsParams = {
  periodDays?: number;
  startTime?: string;
  endTime?: string;
  service?: string;
};
type LogSearchParams = Parameters<typeof searchLogs> extends [infer P] ? P : never;
type ExportLogsParams = Parameters<typeof exportLogs> extends [infer P] ? P : never;

// ============================================================================
// Logs Hooks
// ============================================================================

export function useLogs(params?: GetLogsParams) {
  return useQuery({
    queryKey: queryKeys.monitoring.logs.list(params),
    queryFn: () => getLogs(params),
    placeholderData: (previousData) => previousData,
  });
}

export function useLogEntry(id: string) {
  return useQuery({
    queryKey: queryKeys.monitoring.logs.detail(id),
    queryFn: () => getLogEntry(id),
    enabled: !!id,
  });
}

export function useLogStats(params?: LogStatsParams) {
  return useQuery({
    queryKey: queryKeys.monitoring.logs.stats(params),
    queryFn: () => {
      const now = new Date();
      const startTime =
        params?.startTime ??
        (params?.periodDays
          ? new Date(now.getTime() - params.periodDays * 24 * 60 * 60 * 1000).toISOString()
          : undefined);
      const endTime =
        params?.endTime ?? (params?.periodDays ? now.toISOString() : undefined);

      return getLogStats({
        startTime,
        endTime,
        service: params?.service,
      });
    },
    staleTime: 2 * 60 * 1000,
  });
}

export function useLogServices() {
  return useQuery({
    queryKey: queryKeys.monitoring.logs.services(),
    queryFn: getLogServices,
    staleTime: 5 * 60 * 1000,
  });
}

export function useSearchLogs() {
  return useMutation({
    mutationFn: (query: LogSearchParams) => searchLogs(query),
  });
}

export function useExportLogs() {
  return useMutation({
    mutationFn: (params: ExportLogsParams) => exportLogs(params),
  });
}

// ============================================================================
// Re-export types
// ============================================================================

export type {
  GetLogsParams,
  LogEntry,
  LogStats,
  LogSearchParams as LogSearchQuery,
  ExportLogsParams,
};
