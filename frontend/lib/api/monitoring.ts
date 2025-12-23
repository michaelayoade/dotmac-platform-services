/**
 * Monitoring API
 *
 * Application logs, monitoring metrics, and log statistics
 */

import { api, PaginatedResponse, normalizePaginatedResponse } from "./client";

// ============================================================================
// Log Types
// ============================================================================

export type LogLevel = "DEBUG" | "INFO" | "WARNING" | "ERROR" | "CRITICAL";

export interface LogEntry {
  id: string;
  timestamp: string;
  level: LogLevel;
  service: string;
  message: string;
  metadata?: Record<string, unknown>;
  traceId?: string;
  spanId?: string;
  userId?: string;
  tenantId?: string;
}

export interface LogStats {
  total: number;
  byLevel: Record<LogLevel, number>;
  byService: Record<string, number>;
  timeRange: {
    start: string;
    end: string;
  };
}

// ============================================================================
// Log Queries
// ============================================================================

export interface GetLogsParams {
  page?: number;
  pageSize?: number;
  level?: LogLevel;
  service?: string;
  search?: string;
  startTime?: string;
  endTime?: string;
  traceId?: string;
  userId?: string;
  sortBy?: string;
  sortOrder?: "asc" | "desc";
}

export interface LogSearchQuery {
  query: string;
  filters?: Record<string, unknown>;
  startDate?: string;
  endDate?: string;
  limit?: number;
}

export async function getLogs(params: GetLogsParams = {}): Promise<{
  logs: LogEntry[];
  totalCount: number;
  pageCount: number;
}> {
  const {
    page = 1,
    pageSize = 50,
    level,
    service,
    search,
    startTime,
    endTime,
    traceId,
    userId,
    sortBy,
    sortOrder,
  } = params;

  const response = await api.get<unknown>("/api/v1/monitoring/logs", {
    params: {
      page,
      page_size: pageSize,
      level,
      service,
      search,
      start_time: startTime,
      end_time: endTime,
      trace_id: traceId,
      user_id: userId,
      sort_by: sortBy,
      sort_order: sortOrder,
    },
  });
  const normalized = normalizePaginatedResponse<LogEntry>(response);

  return {
    logs: normalized.items,
    totalCount: normalized.total,
    pageCount: normalized.totalPages,
  };
}

export async function getLogEntry(id: string): Promise<LogEntry> {
  return api.get<LogEntry>(`/api/v1/monitoring/logs/${id}`);
}

export async function getLogStats(params?: {
  startTime?: string;
  endTime?: string;
  service?: string;
}): Promise<LogStats> {
  return api.get<LogStats>("/api/v1/monitoring/logs/stats", {
    params: {
      start_time: params?.startTime,
      end_time: params?.endTime,
      service: params?.service,
    },
  });
}

export async function getLogServices(): Promise<string[]> {
  return api.get<string[]>("/api/v1/monitoring/logs/services");
}

export async function searchLogs(query: LogSearchQuery): Promise<LogEntry[]> {
  return api.post<LogEntry[]>("/api/v1/monitoring/logs/search", {
    query: query.query,
    filters: query.filters,
    start_date: query.startDate,
    end_date: query.endDate,
    limit: query.limit,
  });
}

export async function exportLogs(params: {
  format: "json" | "csv";
  startDate?: string;
  endDate?: string;
  level?: LogLevel;
  service?: string;
}): Promise<Blob> {
  return api.post<Blob>("/api/v1/monitoring/logs/export", {
    format: params.format,
    start_date: params.startDate,
    end_date: params.endDate,
    level: params.level,
    service: params.service,
  });
}

// ============================================================================
// Infrastructure Monitoring
// ============================================================================

export interface InfrastructureMetrics {
  health: {
    status: "healthy" | "degraded" | "down";
    uptime: number;
  };
  performance: {
    avgLatency: number;
    p95Latency: number;
    p99Latency: number;
    throughput: number;
    errorRate: number;
    requestsPerSecond: number;
  };
}

export async function getInfrastructureMetrics(): Promise<InfrastructureMetrics> {
  return api.get<InfrastructureMetrics>("/api/v1/monitoring/health");
}

export async function getPerformanceMetrics(params?: {
  period?: "1h" | "24h" | "7d" | "30d";
}): Promise<{
  current: InfrastructureMetrics["performance"];
  history: Array<{
    timestamp: string;
    latency: number;
    errorRate: number;
    requests: number;
  }>;
}> {
  return api.get("/api/v1/monitoring/performance", {
    params: { period: params?.period },
  });
}
