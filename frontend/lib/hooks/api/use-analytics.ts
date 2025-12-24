"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import { queryKeys } from "@/lib/api/query-keys";
import type { DateRange } from "@/types/api";

// Types
export interface DashboardMetrics {
  totalUsers: number;
  activeUsers: number;
  userGrowth: number;
  totalTenants: number;
  activeTenants: number;
  tenantGrowth: number;
  totalRevenue: number;
  revenueGrowth: number;
  mrr: number;
  arr: number;
  activeDeployments: number;
  deploymentUptime: number;
}

export interface RevenueDataPoint {
  date: string;
  revenue: number;
  subscriptions: number;
  newCustomers: number;
}

export interface ActivityItem {
  id: string;
  type: "user_action" | "system_event" | "deployment" | "billing" | "security";
  actor: {
    id: string;
    name: string;
    avatar?: string;
  };
  action: string;
  target?: {
    type: string;
    id: string;
    name: string;
  };
  metadata?: Record<string, unknown>;
  timestamp: string;
}

export interface SystemHealthService {
  name: string;
  status: "operational" | "degraded" | "partial_outage" | "major_outage";
  latency: number;
  errorRate: number;
  lastChecked: string;
}

export interface SystemHealth {
  status: "healthy" | "degraded" | "down";
  services: SystemHealthService[];
  lastChecked: string;
  uptime: number;
}

export interface TrafficData {
  date: string;
  visits: number;
  uniqueVisitors: number;
  pageViews: number;
  avgDuration: number;
  bounceRate: number;
}

export interface GeographicData {
  country: string;
  countryCode: string;
  users: number;
  sessions: number;
  percentage: number;
}

// API functions
async function getDashboardMetrics(): Promise<DashboardMetrics> {
  return api.get<DashboardMetrics>("/api/v1/analytics/dashboard");
}

async function getRevenueData(range?: DateRange): Promise<RevenueDataPoint[]> {
  return api.get<RevenueDataPoint[]>("/api/v1/analytics/revenue", {
    params: {
      start: range?.start,
      end: range?.end,
    },
  });
}

async function getActivityFeed(params?: {
  limit?: number;
  type?: string;
}): Promise<ActivityItem[]> {
  return api.get<ActivityItem[]>("/api/v1/analytics/activity", { params });
}

async function getSystemHealth(): Promise<SystemHealth> {
  return api.get<SystemHealth>("/health", { requiresAuth: false });
}

async function getTrafficData(range?: DateRange): Promise<TrafficData[]> {
  return api.get<TrafficData[]>("/api/v1/analytics/traffic", {
    params: {
      start: range?.start,
      end: range?.end,
    },
  });
}

async function getGeographicData(): Promise<GeographicData[]> {
  return api.get<GeographicData[]>("/api/v1/analytics/geographic");
}

async function getMetrics(
  type: string,
  range?: DateRange
): Promise<Record<string, number>> {
  return api.get<Record<string, number>>(`/api/v1/analytics/metrics/${type}`, {
    params: {
      start: range?.start,
      end: range?.end,
    },
  });
}

// Hooks
export function useDashboardMetrics() {
  return useQuery({
    queryKey: queryKeys.analytics.dashboard(),
    queryFn: getDashboardMetrics,
    staleTime: 60 * 1000, // 1 minute
    refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
  });
}

export function useRevenueData(range?: DateRange) {
  return useQuery({
    queryKey: queryKeys.analytics.revenue(range),
    queryFn: () => getRevenueData(range),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useActivityFeed(params?: { limit?: number; type?: string }) {
  return useQuery({
    queryKey: [...queryKeys.analytics.activity(), params],
    queryFn: () => getActivityFeed(params),
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 60 * 1000, // Refetch every minute
  });
}

export function useSystemHealth() {
  return useQuery({
    queryKey: queryKeys.health.status(),
    queryFn: getSystemHealth,
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 60 * 1000, // Refetch every minute
  });
}

export function useTrafficData(range?: DateRange) {
  return useQuery({
    queryKey: [...queryKeys.analytics.all, "traffic", range],
    queryFn: () => getTrafficData(range),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useGeographicData() {
  return useQuery({
    queryKey: [...queryKeys.analytics.all, "geographic"],
    queryFn: getGeographicData,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}

export function useAnalyticsMetrics(type: string, range?: DateRange) {
  return useQuery({
    queryKey: queryKeys.analytics.metrics(type),
    queryFn: () => getMetrics(type, range),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}
