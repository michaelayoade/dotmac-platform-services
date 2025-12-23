"use client";

import { useQuery, useMutation } from "@tanstack/react-query";
import {
  getAuditActivities,
  getAuditActivity,
  searchAuditActivities,
  getAuditStats,
  exportAuditActivities,
  logFrontendError,
  logFrontendErrors,
  getUserActivitySummary,
  type GetAuditParams,
  type AuditActivity,
  type AuditSearchQuery,
  type AuditStats,
  type FrontendLogEntry,
  type UserActivitySummary,
} from "@/lib/api/audit";
import { queryKeys } from "@/lib/api/query-keys";

// ============================================================================
// Audit Activities Hooks
// ============================================================================

export function useAuditActivities(params?: GetAuditParams) {
  return useQuery({
    queryKey: queryKeys.audit.activities.list(params),
    queryFn: () => getAuditActivities(params),
    placeholderData: (previousData) => previousData,
  });
}

export function useAuditActivity(id: string) {
  return useQuery({
    queryKey: queryKeys.audit.activities.detail(id),
    queryFn: () => getAuditActivity(id),
    enabled: !!id,
  });
}

export function useSearchAuditActivities() {
  return useMutation({
    mutationFn: (query: AuditSearchQuery) => searchAuditActivities(query),
  });
}

// ============================================================================
// Audit Stats Hook
// ============================================================================

export function useAuditStats(params?: { periodDays?: number; activityType?: string }) {
  return useQuery({
    queryKey: queryKeys.audit.stats(params),
    queryFn: () => getAuditStats(params),
    staleTime: 5 * 60 * 1000,
  });
}

// ============================================================================
// Audit Export Hook
// ============================================================================

export function useExportAuditActivities() {
  return useMutation({
    mutationFn: (params: {
      format: "json" | "csv";
      startDate?: string;
      endDate?: string;
      activityType?: string;
      severity?: string;
    }) => exportAuditActivities(params),
  });
}

// ============================================================================
// Frontend Error Logging Hooks
// ============================================================================

export function useLogFrontendError() {
  return useMutation({
    mutationFn: logFrontendError,
  });
}

export function useLogFrontendErrors() {
  return useMutation({
    mutationFn: logFrontendErrors,
  });
}

// ============================================================================
// User Activity Summary Hook
// ============================================================================

export function useUserActivitySummary(userId: string, params?: { periodDays?: number }) {
  return useQuery({
    queryKey: queryKeys.audit.userSummary(userId, params),
    queryFn: () => getUserActivitySummary(userId, params),
    enabled: !!userId,
  });
}

// ============================================================================
// Re-export types
// ============================================================================

export type {
  GetAuditParams,
  AuditActivity,
  AuditSearchQuery,
  AuditStats,
  FrontendLogEntry,
  UserActivitySummary,
};
