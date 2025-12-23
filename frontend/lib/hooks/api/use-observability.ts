"use client";

import { useQuery, useMutation } from "@tanstack/react-query";
import {
  getTraces,
  getTrace,
  getTraceSpans,
  getMetrics,
  getMetricsSeries,
  queryMetrics,
  getServiceMap,
  getServiceDependencies,
  getPerformanceAnalytics,
  getEndpointPerformance,
  getSlowEndpoints,
  type GetTracesParams,
  type TraceData,
  type TraceSpan,
  type MetricsQueryParams,
  type MetricSeries,
  type ServiceMap,
  type ServiceDependency,
  type PerformanceAnalytics,
  type EndpointPerformance,
} from "@/lib/api/observability";
import { queryKeys } from "@/lib/api/query-keys";

// ============================================================================
// Traces Hooks
// ============================================================================

export function useTraces(params?: GetTracesParams) {
  return useQuery({
    queryKey: queryKeys.observability.traces.list(params),
    queryFn: () => getTraces(params),
    placeholderData: (previousData) => previousData,
  });
}

export function useTrace(traceId: string) {
  return useQuery({
    queryKey: queryKeys.observability.traces.detail(traceId),
    queryFn: () => getTrace(traceId),
    enabled: !!traceId,
  });
}

export function useTraceSpans(traceId: string) {
  return useQuery({
    queryKey: queryKeys.observability.traces.spans(traceId),
    queryFn: () => getTraceSpans(traceId),
    enabled: !!traceId,
  });
}

// ============================================================================
// Metrics Hooks
// ============================================================================

export function useMetrics(params?: MetricsQueryParams) {
  return useQuery({
    queryKey: queryKeys.observability.metrics.list(params),
    queryFn: () => getMetrics(params),
    staleTime: 30 * 1000, // 30 seconds
  });
}

export function useMetricsSeries(
  metricName: string,
  params?: { startTime?: string; endTime?: string; step?: string }
) {
  return useQuery({
    queryKey: queryKeys.observability.metrics.series(metricName, params),
    queryFn: () => getMetricsSeries(metricName, params),
    enabled: !!metricName,
    staleTime: 30 * 1000,
  });
}

export function useQueryMetrics() {
  return useMutation({
    mutationFn: (query: { promql: string; startTime?: string; endTime?: string; step?: string }) =>
      queryMetrics(query),
  });
}

// ============================================================================
// Service Map Hooks
// ============================================================================

export function useServiceMap(params?: { timeRange?: string }) {
  return useQuery({
    queryKey: queryKeys.observability.serviceMap(params),
    queryFn: () => getServiceMap(params),
    staleTime: 60 * 1000, // 1 minute
  });
}

export function useServiceDependencies(serviceName: string) {
  return useQuery({
    queryKey: queryKeys.observability.serviceDependencies(serviceName),
    queryFn: () => getServiceDependencies(serviceName),
    enabled: !!serviceName,
  });
}

// ============================================================================
// Performance Analytics Hooks
// ============================================================================

export function usePerformanceAnalytics(params?: { periodDays?: number; percentile?: number }) {
  return useQuery({
    queryKey: queryKeys.observability.performance.analytics(params),
    queryFn: () => getPerformanceAnalytics(params),
    staleTime: 2 * 60 * 1000,
  });
}

export function useEndpointPerformance(
  endpoint: string,
  params?: { periodDays?: number }
) {
  return useQuery({
    queryKey: queryKeys.observability.performance.endpoint(endpoint, params),
    queryFn: () => getEndpointPerformance(endpoint, params),
    enabled: !!endpoint,
  });
}

export function useSlowEndpoints(params?: { threshold?: number; limit?: number }) {
  return useQuery({
    queryKey: queryKeys.observability.performance.slow(params),
    queryFn: () => getSlowEndpoints(params),
    staleTime: 2 * 60 * 1000,
  });
}

// ============================================================================
// Re-export types
// ============================================================================

export type {
  GetTracesParams,
  TraceData,
  TraceSpan,
  MetricsQueryParams,
  MetricSeries,
  ServiceMap,
  ServiceDependency,
  PerformanceAnalytics,
  EndpointPerformance,
};
