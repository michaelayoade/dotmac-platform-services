export interface MetricDefinition {
  id: string;
  name: string;
  description: string;
  unit: string;
  type: 'counter' | 'gauge' | 'histogram' | 'summary';
  category: 'business' | 'technical' | 'operational' | 'financial';
  tags?: string[];
  aggregation?: {
    method: 'sum' | 'avg' | 'min' | 'max' | 'count' | 'distinct';
    interval: 'minute' | 'hour' | 'day' | 'week' | 'month' | 'year';
  };
  format?: {
    prefix?: string;
    suffix?: string;
    decimals?: number;
    percentage?: boolean;
    currency?: string;
  };
}

export interface DataPoint {
  timestamp: Date;
  value: number;
  metadata?: Record<string, any>;
  tags?: Record<string, string>;
}

export interface TimeSeries {
  metricId: string;
  data: DataPoint[];
  startTime: Date;
  endTime: Date;
  resolution: 'minute' | 'hour' | 'day' | 'week' | 'month';
  aggregation?: string;
}

export interface KPIMetric {
  id: string;
  name: string;
  value: number;
  previousValue?: number;
  target?: number;
  unit: string;
  trend: 'up' | 'down' | 'stable';
  trendPercentage: number;
  status: 'good' | 'warning' | 'critical' | 'unknown';
  category: 'revenue' | 'growth' | 'efficiency' | 'satisfaction' | 'operational';
  updatedAt: Date;
  description?: string;
  formula?: string;
}

export interface DashboardWidget {
  id: string;
  type: 'metric' | 'chart' | 'table' | 'kpi' | 'funnel' | 'heatmap';
  title: string;
  description?: string;
  position: { x: number; y: number; width: number; height: number };
  config: WidgetConfig;
  dataSource: DataSourceConfig;
  filters?: FilterConfig[];
  refreshInterval?: number;
  isVisible: boolean;
}

export interface WidgetConfig {
  chartType?: 'line' | 'area' | 'bar' | 'pie' | 'donut' | 'scatter' | 'heatmap';
  metrics?: string[];
  dimensions?: string[];
  showLegend?: boolean;
  showGrid?: boolean;
  colorScheme?: string[];
  aggregation?: {
    timeWindow: string;
    groupBy?: string[];
  };
  formatting?: {
    numberFormat?: string;
    dateFormat?: string;
    showPercentage?: boolean;
  };
}

export interface DataSourceConfig {
  type: 'api' | 'database' | 'realtime' | 'csv' | 'external';
  endpoint?: string;
  query?: string;
  parameters?: Record<string, any>;
  cacheMinutes?: number;
  authentication?: {
    type: 'bearer' | 'api_key' | 'basic';
    credentials?: Record<string, string>;
  };
}

export interface FilterConfig {
  id: string;
  name: string;
  type: 'date_range' | 'select' | 'multiselect' | 'text' | 'number_range';
  field: string;
  defaultValue?: any;
  options?: Array<{ label: string; value: any }>;
  required?: boolean;
}

export interface AnalyticsDashboard {
  id: string;
  name: string;
  description?: string;
  category: 'executive' | 'operational' | 'financial' | 'marketing' | 'technical';
  widgets: DashboardWidget[];
  layout: 'grid' | 'free' | 'tabs';
  theme: 'light' | 'dark' | 'auto';
  isPublic: boolean;
  owner: string;
  sharedWith: string[];
  tags?: string[];
  createdAt: Date;
  updatedAt: Date;
  settings: {
    autoRefresh: boolean;
    refreshInterval: number;
    timezone: string;
    currency: string;
  };
}

export interface AnalyticsReport {
  id: string;
  name: string;
  description?: string;
  type: 'scheduled' | 'ad_hoc' | 'alert';
  format: 'pdf' | 'excel' | 'csv' | 'json' | 'html';
  dashboardId?: string;
  schedule?: {
    frequency: 'daily' | 'weekly' | 'monthly' | 'quarterly';
    time: string; // HH:MM format
    timezone: string;
    daysOfWeek?: number[]; // 0-6, Sunday-Saturday
    dayOfMonth?: number; // 1-31
  };
  recipients: string[];
  filters?: FilterConfig[];
  template?: string;
  isActive: boolean;
  lastGenerated?: Date;
  nextRun?: Date;
}

export interface BusinessIntelligenceInsight {
  id: string;
  type: 'anomaly' | 'trend' | 'correlation' | 'prediction' | 'recommendation';
  title: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  confidence: number; // 0-1
  metrics: string[];
  timeframe: {
    start: Date;
    end: Date;
  };
  data: {
    observed?: number;
    expected?: number;
    threshold?: number;
    correlation?: number;
    prediction?: {
      value: number;
      confidence: number;
      factors: Array<{ factor: string; impact: number }>;
    };
  };
  actions?: Array<{
    type: 'investigate' | 'alert' | 'optimize' | 'automate';
    description: string;
    priority: 'low' | 'medium' | 'high';
  }>;
  createdAt: Date;
  resolvedAt?: Date;
  status: 'new' | 'investigating' | 'resolved' | 'dismissed';
}

export interface AnalyticsQuery {
  id?: string;
  name?: string;
  query: string;
  type: 'sql' | 'graphql' | 'aggregation';
  parameters?: Record<string, any>;
  cache?: {
    enabled: boolean;
    ttl: number;
  };
  rateLimit?: {
    maxRequests: number;
    windowMs: number;
  };
}

export interface DataExport {
  id: string;
  name: string;
  format: 'csv' | 'excel' | 'json' | 'pdf';
  dashboardId?: string;
  query?: AnalyticsQuery;
  filters?: FilterConfig[];
  dateRange: {
    start: Date;
    end: Date;
  };
  status: 'pending' | 'processing' | 'completed' | 'failed';
  downloadUrl?: string;
  fileSize?: number;
  requestedBy: string;
  requestedAt: Date;
  completedAt?: Date;
  expiresAt?: Date;
}

export interface RealTimeMetric {
  id: string;
  name: string;
  value: number;
  unit: string;
  timestamp: Date;
  source: string;
  tags?: Record<string, string>;
  alerts?: Array<{
    type: 'threshold' | 'anomaly' | 'rate';
    condition: string;
    value: number;
    triggered: boolean;
  }>;
}

export interface AnalyticsEvent {
  id: string;
  type: string;
  category: 'user_action' | 'system_event' | 'business_event' | 'error';
  userId?: string;
  sessionId?: string;
  tenantId?: string;
  timestamp: Date;
  properties: Record<string, any>;
  metadata?: {
    source: string;
    version: string;
    device?: string;
    browser?: string;
    location?: {
      country: string;
      region: string;
      city: string;
    };
  };
}

export interface Cohort {
  id: string;
  name: string;
  description?: string;
  definition: {
    criteria: Array<{
      field: string;
      operator: 'equals' | 'contains' | 'greater_than' | 'less_than' | 'in' | 'between';
      value: any;
    }>;
    timeframe: {
      type: 'absolute' | 'relative';
      start?: Date;
      end?: Date;
      days?: number;
    };
  };
  size: number;
  createdAt: Date;
  lastCalculated: Date;
}

export interface FunnelAnalysis {
  id: string;
  name: string;
  steps: Array<{
    id: string;
    name: string;
    event: string;
    filters?: FilterConfig[];
  }>;
  timeframe: {
    start: Date;
    end: Date;
  };
  results: Array<{
    stepId: string;
    count: number;
    percentage: number;
    dropoffCount?: number;
    dropoffPercentage?: number;
  }>;
  segments?: Array<{
    name: string;
    filter: FilterConfig;
    results: Array<{
      stepId: string;
      count: number;
      percentage: number;
    }>;
  }>;
}

export interface RetentionAnalysis {
  id: string;
  name: string;
  cohortDefinition: Cohort['definition'];
  returnEvent: string;
  periods: Array<{
    period: number;
    label: string; // "Day 1", "Week 2", etc.
    count: number;
    percentage: number;
  }>;
  timeframe: {
    start: Date;
    end: Date;
  };
  granularity: 'daily' | 'weekly' | 'monthly';
}

// Analytics Context and Hooks Types
export interface AnalyticsContextValue {
  // Current state
  dashboards: AnalyticsDashboard[];
  currentDashboard: AnalyticsDashboard | null;
  reports: AnalyticsReport[];
  insights: BusinessIntelligenceInsight[];

  // Loading states
  isLoading: boolean;
  isDashboardLoading: boolean;
  isReportLoading: boolean;

  // Error handling
  error: string | null;

  // Actions
  actions: {
    // Dashboard management
    createDashboard: (
      dashboard: Omit<AnalyticsDashboard, 'id' | 'createdAt' | 'updatedAt'>
    ) => Promise<string>;
    updateDashboard: (id: string, updates: Partial<AnalyticsDashboard>) => Promise<void>;
    deleteDashboard: (id: string) => Promise<void>;
    duplicateDashboard: (id: string, name?: string) => Promise<string>;

    // Widget management
    addWidget: (dashboardId: string, widget: Omit<DashboardWidget, 'id'>) => Promise<void>;
    updateWidget: (
      dashboardId: string,
      widgetId: string,
      updates: Partial<DashboardWidget>
    ) => Promise<void>;
    removeWidget: (dashboardId: string, widgetId: string) => Promise<void>;

    // Data operations
    executeQuery: (query: AnalyticsQuery) => Promise<any>;
    exportData: (config: Omit<DataExport, 'id' | 'status' | 'requestedAt'>) => Promise<string>;

    // Reports
    generateReport: (reportId: string) => Promise<string>;
    scheduleReport: (report: Omit<AnalyticsReport, 'id'>) => Promise<string>;

    // Real-time data
    subscribeToMetric: (metricId: string, callback: (data: RealTimeMetric) => void) => () => void;

    // Insights
    getInsights: (filters?: {
      category?: string;
      severity?: string;
    }) => Promise<BusinessIntelligenceInsight[]>;
    resolveInsight: (id: string) => Promise<void>;

    // Utilities
    refresh: () => Promise<void>;
    reset: () => void;
  };
}

// Component Props Types
export interface AnalyticsDashboardProps {
  dashboardId?: string;
  isReadOnly?: boolean;
  theme?: 'light' | 'dark' | 'auto';
  height?: string | number;
  className?: string;
  onWidgetClick?: (widget: DashboardWidget) => void;
  onError?: (error: string) => void;
}

export interface MetricCardProps {
  metric: KPIMetric;
  size?: 'sm' | 'md' | 'lg';
  showTrend?: boolean;
  showTarget?: boolean;
  onClick?: (metric: KPIMetric) => void;
  className?: string;
}

export interface ChartWidgetProps {
  widget: DashboardWidget;
  data?: TimeSeries[];
  isLoading?: boolean;
  error?: string | null;
  onRefresh?: () => void;
  onEdit?: () => void;
  className?: string;
}

export interface ReportBuilderProps {
  dashboardId?: string;
  initialReport?: Partial<AnalyticsReport>;
  onSave?: (report: AnalyticsReport) => void;
  onCancel?: () => void;
  className?: string;
}

// API Response Types
export interface AnalyticsApiResponse<T = any> {
  data: T;
  pagination?: {
    page: number;
    size: number;
    total: number;
    totalPages: number;
  };
  metadata?: {
    executionTime: number;
    cacheHit: boolean;
    dataSource: string;
    lastUpdated: Date;
  };
}

export interface MetricsResponse {
  metrics: KPIMetric[];
  trends: TimeSeries[];
  insights: BusinessIntelligenceInsight[];
}

export interface QueryResult {
  columns: Array<{ name: string; type: string }>;
  rows: any[][];
  totalRows: number;
  executionTime: number;
  fromCache: boolean;
}

// Configuration Types
export interface AnalyticsConfig {
  apiEndpoint: string;
  realTimeEndpoint: string;
  defaultRefreshInterval: number;
  maxCacheAge: number;
  enableRealTime: boolean;
  theme: {
    colors: Record<string, string>;
    charts: {
      defaultHeight: number;
      colorPalette: string[];
    };
  };
  features: {
    exportEnabled: boolean;
    sharingEnabled: boolean;
    alertsEnabled: boolean;
    predictiveInsights: boolean;
  };
}

// Utility Types
export type TimeGranularity = 'minute' | 'hour' | 'day' | 'week' | 'month' | 'quarter' | 'year';
export type ChartType =
  | 'line'
  | 'area'
  | 'bar'
  | 'pie'
  | 'donut'
  | 'scatter'
  | 'heatmap'
  | 'funnel';
export type AggregationType =
  | 'sum'
  | 'avg'
  | 'min'
  | 'max'
  | 'count'
  | 'distinct'
  | 'median'
  | 'percentile';
export type ComparisonType = 'previous_period' | 'same_period_last_year' | 'target' | 'baseline';
export type AlertCondition =
  | 'greater_than'
  | 'less_than'
  | 'equals'
  | 'percentage_change'
  | 'anomaly';
