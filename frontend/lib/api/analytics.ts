/**
 * Analytics API
 *
 * Dashboard metrics and analytics data fetching
 * Connected to real backend endpoints
 */

import { api } from "./client";

// Dashboard metrics
export interface DashboardMetrics {
  users: {
    total: number;
    active: number;
    change: number;
  };
  tenants: {
    total: number;
    trial: number;
    change: number;
  };
  revenue: {
    current: number;
    change: number;
    trend: number[];
  };
  deployments: {
    active: number;
    pending: number;
    change: number;
  };
}

export async function getDashboardMetrics(): Promise<DashboardMetrics> {
  return api.get<DashboardMetrics>("/api/v1/analytics/dashboard");
}

// Revenue analytics
export interface RevenueData {
  month: string;
  revenue: number;
  projected?: number;
}

export interface RevenueBreakdown {
  byPlan: Array<{
    plan: string;
    revenue: number;
    percentage: number;
  }>;
  byRegion: Array<{
    region: string;
    revenue: number;
    percentage: number;
  }>;
  mrr: number;
  arr: number;
  mrrGrowth: number;
  netRevenue: number;
  churn: number;
  expansion: number;
}

export async function getRevenueData(
  period: "6m" | "12m" | "ytd" | "all" = "12m"
): Promise<RevenueData[]> {
  return api.get<RevenueData[]>("/api/v1/analytics/revenue", {
    params: { period },
  });
}

export async function getRevenueBreakdown(): Promise<RevenueBreakdown> {
  return api.get<RevenueBreakdown>("/api/v1/analytics/revenue/breakdown");
}

// Activity feed
export interface ActivityItem {
  id: string;
  type: string;
  title: string;
  description: string;
  timestamp: string;
  actor?: {
    name: string;
    email: string;
    avatarUrl?: string;
  };
  metadata?: Record<string, unknown>;
}

export async function getActivityFeed(params?: {
  limit?: number;
  offset?: number;
  types?: string[];
}): Promise<ActivityItem[]> {
  const { limit = 20, offset = 0, types } = params || {};
  return api.get<ActivityItem[]>("/api/v1/analytics/activity", {
    params: {
      limit,
      offset,
      types: types?.join(","),
    },
  });
}

// User analytics
export interface UserAnalytics {
  totalUsers: number;
  activeUsers: number;
  newUsersThisMonth: number;
  userGrowth: number;
  usersByRole: Array<{
    role: string;
    count: number;
  }>;
  usersByTenant: Array<{
    tenantId: string;
    tenantName: string;
    count: number;
  }>;
  loginActivity: Array<{
    date: string;
    logins: number;
  }>;
}

export async function getUserAnalytics(): Promise<UserAnalytics> {
  return api.get<UserAnalytics>("/api/v1/analytics/users");
}

// Tenant analytics
export interface TenantAnalytics {
  totalTenants: number;
  activeTenants: number;
  trialTenants: number;
  tenantGrowth: number;
  tenantsByPlan: Array<{
    plan: string;
    count: number;
    revenue: number;
  }>;
  topTenants: Array<{
    id: string;
    name: string;
    users: number;
    revenue: number;
  }>;
  conversionRate: number;
  churnRate: number;
}

export async function getTenantAnalytics(): Promise<TenantAnalytics> {
  return api.get<TenantAnalytics>("/api/v1/analytics/tenants");
}

// Deployment analytics
export interface DeploymentAnalytics {
  totalDeployments: number;
  activeDeployments: number;
  deploymentsByStatus: Array<{
    status: string;
    count: number;
  }>;
  deploymentsByEnvironment: Array<{
    environment: string;
    count: number;
  }>;
  deploymentsByRegion: Array<{
    region: string;
    count: number;
  }>;
  resourceUtilization: {
    cpuAverage: number;
    memoryAverage: number;
    storageUsed: number;
  };
  uptimePercentage: number;
}

export async function getDeploymentAnalytics(): Promise<DeploymentAnalytics> {
  return api.get<DeploymentAnalytics>("/api/v1/analytics/deployments");
}

// System health
export interface HealthStatus {
  service: string;
  status: "healthy" | "degraded" | "down";
  latency?: number;
  message?: string;
  lastCheck?: string;
}

export interface SystemHealth {
  overall: "healthy" | "degraded" | "down";
  services: HealthStatus[];
  uptime: number;
  lastIncident?: {
    title: string;
    status: string;
    timestamp: string;
  };
}

export async function getSystemHealth(): Promise<SystemHealth> {
  const services = await api.get<HealthStatus[]>("/health", { requiresAuth: false });

  // Determine overall status based on individual services
  const hasDown = services.some((s) => s.status === "down");
  const hasDegraded = services.some((s) => s.status === "degraded");
  const overall = hasDown ? "down" : hasDegraded ? "degraded" : "healthy";

  return {
    overall,
    services,
    uptime: 99.9, // This would come from the backend
  };
}

// Usage metrics
export interface UsageMetrics {
  apiCalls: {
    total: number;
    byEndpoint: Array<{
      endpoint: string;
      count: number;
    }>;
    byDay: Array<{
      date: string;
      count: number;
    }>;
  };
  storage: {
    used: number;
    limit: number;
    byTenant: Array<{
      tenantId: string;
      tenantName: string;
      used: number;
    }>;
  };
  bandwidth: {
    used: number;
    limit: number;
    byDay: Array<{
      date: string;
      bytes: number;
    }>;
  };
}

export async function getUsageMetrics(period: "7d" | "30d" | "90d" = "30d"): Promise<UsageMetrics> {
  return api.get<UsageMetrics>("/api/v1/analytics/usage", {
    params: { period },
  });
}

// Performance metrics
export interface PerformanceMetrics {
  responseTime: {
    p50: number;
    p95: number;
    p99: number;
    average: number;
  };
  errorRate: number;
  requestsPerSecond: number;
  byEndpoint: Array<{
    endpoint: string;
    averageTime: number;
    errorRate: number;
    requestCount: number;
  }>;
  byTime: Array<{
    timestamp: string;
    responseTime: number;
    errorRate: number;
    requests: number;
  }>;
}

export async function getPerformanceMetrics(
  period: "1h" | "24h" | "7d" = "24h"
): Promise<PerformanceMetrics> {
  return api.get<PerformanceMetrics>("/api/v1/analytics/performance", {
    params: { period },
  });
}
