/**
 * API Module Exports
 *
 * Central export point for all API modules
 */

// Core client and utilities
export * from "./client";
export * from "./query-keys";

// Domain APIs
export * from "./users";
export * from "./tenants";
export * from "./billing";
export * from "./customers";
export * from "./deployments";
export {
  getDashboardMetrics,
  getRevenueData,
  getRevenueBreakdown,
  getActivityFeed,
  getUserAnalytics,
  getTenantAnalytics,
  getDeploymentAnalytics,
  getSystemHealth,
  getUsageMetrics,
  getPerformanceMetrics,
  type DashboardMetrics,
  type RevenueData,
  type RevenueBreakdown,
  type ActivityItem,
  type UserAnalytics,
  type TenantAnalytics,
  type DeploymentAnalytics,
  type HealthStatus,
  type SystemHealth,
  type UsageMetrics,
  type PerformanceMetrics,
} from "./analytics";
export {
  getDashboardMetrics as getDashboardOverviewMetrics,
  getRevenueData as getDashboardRevenueData,
  getRecentActivity,
  getSystemHealth as getDashboardSystemHealth,
  type ActivityItem as DashboardActivityItem,
  type DashboardMetrics as DashboardOverviewMetrics,
  type HealthStatus as DashboardHealthStatus,
  type RevenueData as DashboardRevenueData,
} from "./dashboard";

// New API Modules
export {
  getSecurityMetrics,
  getOperationsMetrics,
  getBillingDashboard,
  getInfrastructureHealth,
  getMonitoringMetrics,
  getLogStats as getConsolidatedLogStats,
  getBillingOverview,
  getCustomerOverview,
  getExpiringSubscriptions,
  getActivityStats,
  type SecurityMetrics,
  type OperationsMetrics,
  type BillingDashboardMetrics,
  type InfrastructureHealth,
  type MonitoringMetrics,
  type LogStats as ConsolidatedLogStats,
  type BillingOverview,
  type CustomerOverview,
  type ExpiringSubscription,
  type ExpiringSubscriptionsResponse,
  type ActivityStats,
} from "./consolidated";
export {
  getLogs,
  getLogEntry,
  getLogStats,
  getLogServices,
  searchLogs,
  exportLogs,
  getInfrastructureMetrics,
  getPerformanceMetrics as getMonitoringPerformanceMetrics,
  type LogLevel,
  type LogEntry,
  type LogStats,
  type GetLogsParams,
  type LogSearchQuery,
  type InfrastructureMetrics,
} from "./monitoring";
export * from "./alerts";
export * from "./observability";
export * from "./ticketing";
export * from "./workflows";
export * from "./jobs";
export * from "./communications";
export * from "./partners";
export * from "./contacts";
export * from "./notifications";
export * from "./webhooks";
export * from "./integrations";
export * from "./secrets";
export * from "./feature-flags";
export * from "./licensing";
export * from "./audit";
export * from "./plugins";
