/**
 * Dashboard API
 *
 * Data fetching for dashboard metrics and analytics
 * Connected to real backend endpoints
 */

import { api } from "./client";

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

export interface RevenueData {
  month: string;
  revenue: number;
  projected?: number;
}

export async function getRevenueData(
  period: "6m" | "12m" | "ytd" = "12m"
): Promise<RevenueData[]> {
  return api.get<RevenueData[]>("/api/v1/analytics/revenue", {
    params: { period },
  });
}

export interface ActivityItem {
  id: string;
  type: string;
  title: string;
  description: string;
  timestamp: string;
  actor?: {
    name: string;
    email: string;
  };
}

export async function getRecentActivity(limit = 10): Promise<ActivityItem[]> {
  return api.get<ActivityItem[]>("/api/v1/analytics/activity", {
    params: { limit },
  });
}

export interface HealthStatus {
  service: string;
  status: "healthy" | "degraded" | "down";
  latency?: number;
  message?: string;
}

export async function getSystemHealth(): Promise<HealthStatus[]> {
  return api.get<HealthStatus[]>("/health", { requiresAuth: false });
}
