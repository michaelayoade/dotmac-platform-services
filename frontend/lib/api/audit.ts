/**
 * Audit API
 *
 * Audit trail viewing, statistics, and frontend error logging
 */

import { api, ApiClientError, normalizePaginatedResponse } from "./client";

// ============================================================================
// Audit Types
// ============================================================================

export type AuditSeverity = "low" | "medium" | "high" | "critical";
export type AuditActivityType =
  | "auth"
  | "api"
  | "system"
  | "secret"
  | "file"
  | "user"
  | "tenant"
  | "billing"
  | "admin"
  | "other"
  | string;

export interface AuditActivity {
  id: string;
  activityType: AuditActivityType;
  action: string;
  description: string;
  severity: AuditSeverity;
  userId?: string | null;
  tenantId: string;
  resourceType?: string | null;
  resourceId?: string | null;
  ipAddress?: string | null;
  userAgent?: string | null;
  requestId?: string | null;
  details?: Record<string, unknown> | null;
  timestamp: string;
}

// ============================================================================
// Audit Trail Queries
// ============================================================================

export interface GetAuditParams {
  page?: number;
  pageSize?: number;
  activityType?: AuditActivityType;
  severity?: AuditSeverity;
  userId?: string;
  resourceType?: string;
  resourceId?: string;
  days?: number;
  startDate?: string;
}

function resolveDays(params: GetAuditParams): number | undefined {
  if (params.days) {
    return params.days;
  }
  if (params.startDate) {
    const start = new Date(params.startDate);
    if (!Number.isNaN(start.valueOf())) {
      const diff = Date.now() - start.valueOf();
      const days = Math.ceil(diff / (24 * 60 * 60 * 1000));
      return Math.max(days, 1);
    }
  }
  return undefined;
}

export async function getAuditActivities(params: GetAuditParams = {}): Promise<{
  activities: AuditActivity[];
  totalCount: number;
  pageCount: number;
}> {
  const { page = 1, pageSize = 50, activityType, severity, userId, resourceType, resourceId } =
    params;

  const response = await api.get<unknown>("/api/v1/audit/activities", {
    params: {
      page,
      perPage: pageSize,
      activityType,
      severity,
      userId,
      resourceType,
      resourceId,
      days: resolveDays(params) ?? 30,
    },
  });
  const normalized = normalizePaginatedResponse<AuditActivity>(response);

  return {
    activities: normalized.items,
    totalCount: normalized.total,
    pageCount: normalized.totalPages,
  };
}

export async function getAuditActivity(id: string): Promise<AuditActivity> {
  return api.get<AuditActivity>(`/api/v1/audit/activities/${id}`);
}

// ============================================================================
// Audit Search
// ============================================================================

export interface AuditSearchQuery {
  query: string;
}

export async function searchAuditActivities(_query: AuditSearchQuery): Promise<AuditActivity[]> {
  throw new ApiClientError("Audit search is not supported by the backend yet", 501, "NOT_IMPLEMENTED");
}

// ============================================================================
// Audit Statistics
// ============================================================================

export interface AuditStats {
  periodDays: number;
  totalActivities: number;
  byType: Record<string, number>;
  bySeverity: Record<string, number>;
  byUser: Array<{ userId: string; count: number }>;
  recentCritical: AuditActivity[];
  timeline: Array<{ date: string; count: number }>;
}

export async function getAuditStats(params?: {
  days?: number;
  periodDays?: number;
  activityType?: string;
}): Promise<AuditStats> {
  return api.get<AuditStats>("/api/v1/audit/activities/summary", {
    params: {
      days: params?.days ?? params?.periodDays ?? 7,
    },
  });
}

// ============================================================================
// Audit Export
// ============================================================================

export interface AuditExportResult {
  exportId: string;
  status: string;
  downloadUrl: string;
  expiresAt: string;
}

export async function exportAuditActivities(params: {
  format: "json" | "csv" | "pdf";
  startDate?: string;
  endDate?: string;
  activityType?: string;
  severity?: string;
}): Promise<AuditExportResult> {
  return api.post<AuditExportResult>("/api/v1/audit/export", {
    format: params.format,
    startDate: params.startDate,
    endDate: params.endDate,
    activityType: params.activityType,
    severity: params.severity,
  });
}

// ============================================================================
// Frontend Error Logging
// ============================================================================

export type FrontendLogLevel = "ERROR" | "WARNING" | "INFO" | "DEBUG" | "error" | "warning" | "info" | "debug";

export interface FrontendLogEntry {
  level: FrontendLogLevel;
  message: string;
  service?: string;
  stacktrace?: string;
  context?: {
    url?: string;
    userAgent?: string;
    componentStack?: string;
    userId?: string;
    sessionId?: string;
    [key: string]: unknown;
  };
  metadata?: Record<string, unknown>;
}

function normalizeFrontendLog(entry: FrontendLogEntry) {
  const level = entry.level.toString().toUpperCase() as FrontendLogLevel;
  const metadata = {
    ...entry.metadata,
    ...entry.context,
  } as Record<string, unknown>;

  if (entry.stacktrace) {
    metadata.stacktrace = entry.stacktrace;
  }

  return {
    level,
    message: entry.message,
    service: entry.service ?? "frontend",
    metadata,
  };
}

export async function logFrontendError(entry: FrontendLogEntry): Promise<{
  status: string;
  logsReceived: number;
  logsStored: number;
}> {
  return api.post("/api/v1/audit/frontend-logs", {
    logs: [normalizeFrontendLog(entry)],
  });
}

export async function logFrontendErrors(
  entries: FrontendLogEntry[]
): Promise<{ status: string; logsReceived: number; logsStored: number }> {
  return api.post("/api/v1/audit/frontend-logs", {
    logs: entries.map(normalizeFrontendLog),
  });
}

// ============================================================================
// User Activity Summary
// ============================================================================

export interface UserActivitySummary {
  userId: string;
  totalActivities: number;
  lastActivityAt?: string;
  activityByType: Record<string, number>;
  recentActivities: AuditActivity[];
}

export async function getUserActivitySummary(
  userId: string,
  params?: { periodDays?: number }
): Promise<UserActivitySummary> {
  const activities = await api.get<AuditActivity[]>(`/api/v1/audit/activities/user/${userId}`, {
    params: {
      days: params?.periodDays ?? 30,
    },
  });

  const activityByType: Record<string, number> = {};
  let lastActivityAt: string | undefined;

  activities.forEach((activity) => {
    activityByType[activity.activityType] = (activityByType[activity.activityType] ?? 0) + 1;
    if (!lastActivityAt || activity.timestamp > lastActivityAt) {
      lastActivityAt = activity.timestamp;
    }
  });

  return {
    userId,
    totalActivities: activities.length,
    lastActivityAt,
    activityByType,
    recentActivities: activities,
  };
}
