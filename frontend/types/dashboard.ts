// Dashboard & Analytics Types
// Types for dashboard widgets, charts, and analytics data

/**
 * KPI Metric data
 */
export interface KpiMetric {
  id: string;
  label: string;
  value: number;
  previousValue?: number;
  change?: number;
  changeType?: "increase" | "decrease" | "neutral";
  format: MetricFormat;
  trend?: TrendData[];
  target?: number;
  unit?: string;
}

export type MetricFormat = "number" | "currency" | "percentage" | "duration" | "bytes";

export interface TrendData {
  date: string;
  value: number;
}

/**
 * Chart data structures
 */
export interface TimeSeriesData {
  timestamp: string;
  value: number;
  label?: string;
}

export interface ChartDataPoint {
  name: string;
  value: number;
  color?: string;
  metadata?: Record<string, unknown>;
}

export interface MultiSeriesData {
  name: string;
  data: TimeSeriesData[];
  color?: string;
}

export interface PieChartData {
  name: string;
  value: number;
  color: string;
  percentage?: number;
}

/**
 * Dashboard configuration
 */
export interface DashboardConfig {
  id: string;
  name: string;
  layout: DashboardLayout;
  widgets: DashboardWidget[];
  filters?: DashboardFilter[];
  refreshInterval?: number; // seconds
  isDefault?: boolean;
}

export interface DashboardLayout {
  columns: number;
  rows?: number;
  gap?: number;
}

export interface DashboardWidget {
  id: string;
  type: WidgetType;
  title: string;
  position: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  config: WidgetConfig;
  dataSource?: DataSource;
}

export type WidgetType =
  | "kpi"
  | "line_chart"
  | "bar_chart"
  | "pie_chart"
  | "area_chart"
  | "table"
  | "list"
  | "map"
  | "gauge"
  | "heatmap"
  | "text";

export interface WidgetConfig {
  showLegend?: boolean;
  showGrid?: boolean;
  showTooltip?: boolean;
  stacked?: boolean;
  colors?: string[];
  thresholds?: Threshold[];
  [key: string]: unknown;
}

export interface Threshold {
  value: number;
  color: string;
  label?: string;
}

export interface DataSource {
  endpoint: string;
  method?: "GET" | "POST";
  params?: Record<string, unknown>;
  transform?: string; // JSONPath or transformation expression
}

export interface DashboardFilter {
  id: string;
  label: string;
  type: "date_range" | "select" | "multi_select" | "search";
  field: string;
  options?: { label: string; value: string }[];
  defaultValue?: unknown;
}

/**
 * Analytics data
 */
export interface AnalyticsOverview {
  totalUsers: number;
  activeUsers: number;
  newUsers: number;
  sessions: number;
  avgSessionDuration: number;
  bounceRate: number;
  pageViews: number;
  uniquePageViews: number;
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

export interface DeviceData {
  device: "desktop" | "mobile" | "tablet";
  users: number;
  percentage: number;
}

export interface BrowserData {
  browser: string;
  users: number;
  percentage: number;
}

export interface ReferralData {
  source: string;
  medium: string;
  users: number;
  sessions: number;
  conversions: number;
}

/**
 * System health metrics
 */
export interface SystemHealth {
  status: "healthy" | "degraded" | "down";
  services: ServiceHealth[];
  lastChecked: string;
  uptime: number; // percentage
  incidents: IncidentSummary[];
}

export interface ServiceHealth {
  name: string;
  status: "operational" | "degraded" | "partial_outage" | "major_outage";
  latency: number; // ms
  errorRate: number; // percentage
  lastChecked: string;
}

export interface IncidentSummary {
  id: string;
  title: string;
  status: "investigating" | "identified" | "monitoring" | "resolved";
  severity: "critical" | "major" | "minor";
  startedAt: string;
  resolvedAt?: string;
  affectedServices: string[];
}

/**
 * Activity feed types
 */
export interface ActivityItem {
  id: string;
  type: ActivityType;
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

export type ActivityType =
  | "user_action"
  | "system_event"
  | "deployment"
  | "billing"
  | "security"
  | "integration";

/**
 * Report types
 */
export interface Report {
  id: string;
  name: string;
  type: ReportType;
  schedule?: ReportSchedule;
  filters: Record<string, unknown>;
  columns: string[];
  lastGenerated?: string;
  status: "ready" | "generating" | "failed";
}

export type ReportType =
  | "users"
  | "billing"
  | "usage"
  | "audit"
  | "performance"
  | "custom";

export interface ReportSchedule {
  frequency: "daily" | "weekly" | "monthly";
  dayOfWeek?: number; // 0-6 for weekly
  dayOfMonth?: number; // 1-31 for monthly
  time: string; // HH:mm format
  timezone: string;
  recipients: string[];
  format: "csv" | "xlsx" | "pdf";
}

/**
 * Alert configuration
 */
export interface AlertRule {
  id: string;
  name: string;
  metric: string;
  condition: AlertCondition;
  threshold: number;
  duration: number; // seconds
  severity: "critical" | "warning" | "info";
  enabled: boolean;
  channels: AlertChannel[];
}

export interface AlertCondition {
  operator: "gt" | "gte" | "lt" | "lte" | "eq" | "neq";
  value: number;
}

export interface AlertChannel {
  type: "email" | "slack" | "webhook" | "pagerduty";
  config: Record<string, string>;
}

export interface Alert {
  id: string;
  ruleId: string;
  ruleName: string;
  status: "firing" | "resolved";
  severity: "critical" | "warning" | "info";
  message: string;
  value: number;
  threshold: number;
  firedAt: string;
  resolvedAt?: string;
  acknowledgedBy?: string;
  acknowledgedAt?: string;
}
