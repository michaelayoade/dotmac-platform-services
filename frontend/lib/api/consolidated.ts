/**
 * Consolidated API
 *
 * Dashboard aggregation endpoints that combine data from multiple services
 * These endpoints reduce the number of API calls needed for dashboard views
 */

import { api } from "./client";

// ============================================================================
// Security Metrics (Auth + API Keys + Secrets)
// ============================================================================

export interface SecurityMetrics {
  auth: {
    activeSessions: number;
    failedAttempts: number;
    mfaEnabled: number;
    passwordResets: number;
  };
  apiKeys: {
    total: number;
    active: number;
    expiringSoon: number;
  };
  secrets: {
    total: number;
    active: number;
    expired: number;
    rotated: number;
  };
  compliance: {
    score: number;
    issues: number;
  };
}

export async function getSecurityMetrics(
  timeRange: string = "30d"
): Promise<SecurityMetrics> {
  return api.get<SecurityMetrics>("/api/v1/analytics/security/metrics", {
    params: { timeRange },
    transformParams: false,
  });
}

// ============================================================================
// Operations Metrics (Customers + Communications + Files + Monitoring)
// ============================================================================

export interface OperationsMetrics {
  customers: {
    total: number;
    newThisMonth: number;
    growthRate: number;
    churnRisk: number;
  };
  communications: {
    totalSent: number;
    deliveryRate: number;
    todayCount: number;
  };
  files: {
    totalFiles: number;
    totalSizeMb: number;
    uploadsToday: number;
    downloadsToday: number;
  };
  activity: {
    eventsPerHour: number;
    activeUsers: number;
  };
}

export async function getOperationsMetrics(
  timeRange: string = "30d"
): Promise<OperationsMetrics> {
  return api.get<OperationsMetrics>("/api/v1/analytics/operations/metrics", {
    params: { timeRange },
    transformParams: false,
  });
}

// ============================================================================
// Billing Dashboard Metrics
// ============================================================================

export interface BillingDashboardMetrics {
  revenue: {
    total: number;
    mrr: number;
    growthRate: number;
  };
  subscriptions: {
    total: number;
    active: number;
    pending: number;
    cancelled: number;
    trial: number;
    churnRate: number;
  };
  invoices: {
    total: number;
    paid: number;
    overdue: number;
    outstanding: number;
    pending: number;
  };
  payments: {
    total: number;
    successful: number;
    failed: number;
    successRate: number;
  };
  // Time series data for charts
  revenueTimeSeries?: Array<{
    date: string;
    revenue: number;
    projected?: number;
  }>;
}

export async function getBillingDashboard(
  timeRange: string = "30d"
): Promise<BillingDashboardMetrics> {
  return api.get<BillingDashboardMetrics>("/api/v1/analytics/billing/metrics", {
    params: { timeRange },
    transformParams: false,
  });
}

// ============================================================================
// Infrastructure Health
// ============================================================================

export interface InfrastructureHealth {
  health: {
    status: "healthy" | "degraded" | "down";
    uptime: number;
    services: Record<string, { status: string; latency: number }>;
  };
  performance: {
    avgLatency: number;
    p99Latency: number;
    throughput: number;
    errorRate: number;
    requestsPerSecond: number;
  };
  logs: {
    totalLogs: number;
    errors: number;
    warnings: number;
  };
  resources: {
    cpu: number;
    memory: number;
    disk: number;
    network: number;
  };
}

export async function getInfrastructureHealth(): Promise<InfrastructureHealth> {
  return api.get<InfrastructureHealth>("/api/v1/analytics/infrastructure/health");
}

// ============================================================================
// Monitoring Metrics
// ============================================================================

export interface MonitoringMetrics {
  errorRate: number;
  criticalErrors: number;
  warningCount: number;
  avgResponseTimeMs: number;
  p95ResponseTimeMs: number;
  p99ResponseTimeMs: number;
  totalRequests: number;
  successfulRequests: number;
  failedRequests: number;
  apiRequests: number;
  userActivities: number;
  systemActivities: number;
  highLatencyRequests: number;
  timeoutCount: number;
  topErrors: Array<{
    errorType: string;
    count: number;
  }>;
  period: string;
  timestamp: string;
}

export async function getMonitoringMetrics(
  periodDays: number = 30
): Promise<MonitoringMetrics> {
  return api.get<MonitoringMetrics>("/api/v1/metrics/monitoring/metrics", {
    params: { period_days: periodDays },
  });
}

// ============================================================================
// Log Statistics
// ============================================================================

export interface LogStats {
  // Severity breakdown
  criticalLogs: number;
  highLogs: number;
  mediumLogs: number;
  lowLogs: number;
  // Activity type breakdown
  authLogs: number;
  apiLogs: number;
  systemLogs: number;
  secretLogs: number;
  fileLogs: number;
  // Error analysis
  errorLogs: number;
  uniqueErrorTypes: number;
  mostCommonErrors: Array<{
    errorType: string;
    count: number;
  }>;
  // User activity
  uniqueUsers: number;
  uniqueIps: number;
  // Recent trends
  logsLastHour: number;
  logsLast24h: number;
  period: string;
  timestamp: string;
}

export async function getLogStats(periodDays: number = 30): Promise<LogStats> {
  return api.get<LogStats>("/api/v1/metrics/monitoring/logs/stats", {
    params: { period_days: periodDays },
  });
}

// ============================================================================
// Billing Overview (from billing metrics router)
// ============================================================================

export interface BillingOverview {
  mrr: number;
  arr: number;
  activeSubscriptions: number;
  totalInvoices: number;
  paidInvoices: number;
  overdueInvoices: number;
  totalPayments: number;
  successfulPayments: number;
  failedPayments: number;
  totalPaymentAmount: number;
  period: string;
  timestamp: string;
}

export async function getBillingOverview(
  periodDays: number = 30
): Promise<BillingOverview> {
  return api.get<BillingOverview>("/api/v1/metrics", {
    params: { period_days: periodDays },
  });
}

// ============================================================================
// Customer Overview
// ============================================================================

export interface CustomerOverview {
  totalCustomers: number;
  activeCustomers: number;
  newCustomersThisMonth: number;
  churnedCustomersThisMonth: number;
  customerGrowthRate: number;
  churnRate: number;
  customersByStatus: Record<string, number>;
  atRiskCustomers: number;
  period: string;
  timestamp: string;
}

export async function getCustomerOverview(
  periodDays: number = 30
): Promise<CustomerOverview> {
  return api.get<CustomerOverview>("/api/v1/overview", {
    params: { period_days: periodDays },
  });
}

// ============================================================================
// Expiring Subscriptions
// ============================================================================

export interface ExpiringSubscription {
  subscriptionId: string;
  customerId: string;
  planId: string;
  currentPeriodEnd: string;
  daysUntilExpiry: number;
  status: string;
  cancelAtPeriodEnd: boolean;
}

export interface ExpiringSubscriptionsResponse {
  subscriptions: ExpiringSubscription[];
  totalCount: number;
  daysThreshold: number;
  timestamp: string;
}

export async function getExpiringSubscriptions(
  days: number = 30,
  limit: number = 50
): Promise<ExpiringSubscriptionsResponse> {
  return api.get<ExpiringSubscriptionsResponse>("/api/v1/subscriptions/expiring", {
    params: { days, limit },
  });
}

// ============================================================================
// Activity Statistics
// ============================================================================

export interface ActivityStats {
  totalEvents: number;
  pageViews: number;
  userActions: number;
  apiCalls: number;
  errors: number;
  customEvents: number;
  activeUsers: number;
  activeSessions: number;
  apiRequestsCount: number;
  avgApiLatencyMs: number;
  topEvents: Array<{
    eventType: string;
    count: number;
  }>;
  period: string;
  timestamp: string;
}

export async function getActivityStats(
  periodDays: number = 30
): Promise<ActivityStats> {
  return api.get<ActivityStats>("/api/v1/metrics/analytics/activity", {
    params: { period_days: periodDays },
  });
}
