"use client";

import { useQuery } from "@tanstack/react-query";
import {
  getSecurityMetrics,
  getOperationsMetrics,
  getBillingDashboard,
  getInfrastructureHealth,
  getMonitoringMetrics,
  getLogStats,
  type SecurityMetrics,
  type OperationsMetrics,
  type BillingDashboardMetrics,
  type InfrastructureHealth,
  type MonitoringMetrics,
  type LogStats,
} from "@/lib/api/consolidated";
import { queryKeys } from "@/lib/api/query-keys";

// ============================================================================
// Security Metrics Hook
// ============================================================================

export function useSecurityMetrics(timeRange = "30d") {
  return useQuery({
    queryKey: queryKeys.consolidated.security(timeRange),
    queryFn: () => getSecurityMetrics(timeRange),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

// ============================================================================
// Operations Metrics Hook
// ============================================================================

export function useOperationsMetrics(timeRange = "30d") {
  return useQuery({
    queryKey: queryKeys.consolidated.operations(timeRange),
    queryFn: () => getOperationsMetrics(timeRange),
    staleTime: 5 * 60 * 1000,
  });
}

// ============================================================================
// Billing Dashboard Hook
// ============================================================================

export function useBillingDashboard(timeRange = "30d") {
  return useQuery({
    queryKey: queryKeys.consolidated.billingDashboard(timeRange),
    queryFn: () => getBillingDashboard(timeRange),
    staleTime: 5 * 60 * 1000,
  });
}

// ============================================================================
// Infrastructure Health Hook
// ============================================================================

export function useInfrastructureHealth() {
  return useQuery({
    queryKey: queryKeys.consolidated.infrastructure(),
    queryFn: getInfrastructureHealth,
    staleTime: 30 * 1000, // 30 seconds - health checks should be fresh
    refetchInterval: 60 * 1000, // Auto-refetch every minute
  });
}

// ============================================================================
// Monitoring Metrics Hook
// ============================================================================

export function useMonitoringMetrics(periodDays = 30) {
  return useQuery({
    queryKey: queryKeys.consolidated.monitoring(periodDays),
    queryFn: () => getMonitoringMetrics(periodDays),
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

// ============================================================================
// Log Stats Hook
// ============================================================================

export function useLogStats(periodDays = 30) {
  return useQuery({
    queryKey: queryKeys.consolidated.logStats(periodDays),
    queryFn: () => getLogStats(periodDays),
    staleTime: 2 * 60 * 1000,
  });
}

// ============================================================================
// Re-export types
// ============================================================================

export type {
  SecurityMetrics,
  OperationsMetrics,
  BillingDashboardMetrics,
  InfrastructureHealth,
  MonitoringMetrics,
  LogStats,
};
