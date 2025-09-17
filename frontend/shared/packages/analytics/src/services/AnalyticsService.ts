import { getApiClient } from '@dotmac/headless/api';
import type {
  AnalyticsDashboard,
  DashboardWidget,
  AnalyticsReport,
  BusinessIntelligenceInsight,
  KPIMetric,
  TimeSeries,
  AnalyticsQuery,
  QueryResult,
  DataExport,
  AnalyticsApiResponse,
  MetricsResponse,
  RealTimeMetric,
  AnalyticsEvent,
  Cohort,
  FunnelAnalysis,
  RetentionAnalysis,
  MetricDefinition,
} from '../types';

export class AnalyticsService {
  private apiClient = getApiClient();
  private cache = new Map<string, { data: any; expires: number }>();
  private subscriptions = new Map<string, Set<(data: any) => void>>();

  /**
   * Dashboard Management
   */
  async getDashboards(filters?: {
    category?: string;
    tags?: string[];
    owner?: string;
  }): Promise<AnalyticsDashboard[]> {
    try {
      const queryParams = new URLSearchParams();
      if (filters?.category) queryParams.append('category', filters.category);
      if (filters?.tags) queryParams.append('tags', filters.tags.join(','));
      if (filters?.owner) queryParams.append('owner', filters.owner);

      const response = await this.apiClient.request<AnalyticsApiResponse<AnalyticsDashboard[]>>(
        `/api/v1/analytics/dashboards?${queryParams.toString()}`,
        { method: 'GET' }
      );

      return response.data.data;
    } catch (error) {
      throw new Error(
        `Failed to get dashboards: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }

  async getDashboard(id: string): Promise<AnalyticsDashboard> {
    try {
      const response = await this.apiClient.request<AnalyticsApiResponse<AnalyticsDashboard>>(
        `/api/v1/analytics/dashboards/${id}`,
        { method: 'GET' }
      );

      return response.data.data;
    } catch (error) {
      throw new Error(
        `Failed to get dashboard: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }

  async createDashboard(
    dashboard: Omit<AnalyticsDashboard, 'id' | 'createdAt' | 'updatedAt'>
  ): Promise<string> {
    try {
      const response = await this.apiClient.request<AnalyticsApiResponse<{ id: string }>>(
        '/api/v1/analytics/dashboards',
        {
          method: 'POST',
          body: JSON.stringify(dashboard),
          headers: { 'Content-Type': 'application/json' },
        }
      );

      return response.data.data.id;
    } catch (error) {
      throw new Error(
        `Failed to create dashboard: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }

  async updateDashboard(
    id: string,
    updates: Partial<AnalyticsDashboard>
  ): Promise<AnalyticsDashboard> {
    try {
      const response = await this.apiClient.request<AnalyticsApiResponse<AnalyticsDashboard>>(
        `/api/v1/analytics/dashboards/${id}`,
        {
          method: 'PUT',
          body: JSON.stringify(updates),
          headers: { 'Content-Type': 'application/json' },
        }
      );

      return response.data.data;
    } catch (error) {
      throw new Error(
        `Failed to update dashboard: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }

  async deleteDashboard(id: string): Promise<void> {
    try {
      await this.apiClient.request(`/api/v1/analytics/dashboards/${id}`, {
        method: 'DELETE',
      });
    } catch (error) {
      throw new Error(
        `Failed to delete dashboard: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }

  async duplicateDashboard(id: string, name?: string): Promise<string> {
    try {
      const response = await this.apiClient.request<AnalyticsApiResponse<{ id: string }>>(
        `/api/v1/analytics/dashboards/${id}/duplicate`,
        {
          method: 'POST',
          body: JSON.stringify({ name }),
          headers: { 'Content-Type': 'application/json' },
        }
      );

      return response.data.data.id;
    } catch (error) {
      throw new Error(
        `Failed to duplicate dashboard: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }

  /**
   * Widget Management
   */
  async addWidget(
    dashboardId: string,
    widget: Omit<DashboardWidget, 'id'>
  ): Promise<DashboardWidget> {
    try {
      const response = await this.apiClient.request<AnalyticsApiResponse<DashboardWidget>>(
        `/api/v1/analytics/dashboards/${dashboardId}/widgets`,
        {
          method: 'POST',
          body: JSON.stringify(widget),
          headers: { 'Content-Type': 'application/json' },
        }
      );

      return response.data.data;
    } catch (error) {
      throw new Error(
        `Failed to add widget: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }

  async updateWidget(
    dashboardId: string,
    widgetId: string,
    updates: Partial<DashboardWidget>
  ): Promise<DashboardWidget> {
    try {
      const response = await this.apiClient.request<AnalyticsApiResponse<DashboardWidget>>(
        `/api/v1/analytics/dashboards/${dashboardId}/widgets/${widgetId}`,
        {
          method: 'PUT',
          body: JSON.stringify(updates),
          headers: { 'Content-Type': 'application/json' },
        }
      );

      return response.data.data;
    } catch (error) {
      throw new Error(
        `Failed to update widget: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }

  async removeWidget(dashboardId: string, widgetId: string): Promise<void> {
    try {
      await this.apiClient.request(
        `/api/v1/analytics/dashboards/${dashboardId}/widgets/${widgetId}`,
        { method: 'DELETE' }
      );
    } catch (error) {
      throw new Error(
        `Failed to remove widget: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }

  /**
   * Metrics and KPIs
   */
  async getMetrics(filters?: {
    category?: string;
    tags?: string[];
    timeRange?: { start: Date; end: Date };
  }): Promise<MetricsResponse> {
    try {
      const queryParams = new URLSearchParams();
      if (filters?.category) queryParams.append('category', filters.category);
      if (filters?.tags) queryParams.append('tags', filters.tags.join(','));
      if (filters?.timeRange) {
        queryParams.append('start', filters.timeRange.start.toISOString());
        queryParams.append('end', filters.timeRange.end.toISOString());
      }

      const cacheKey = `metrics:${queryParams.toString()}`;
      const cached = this.getCachedData(cacheKey);
      if (cached) return cached;

      const response = await this.apiClient.request<AnalyticsApiResponse<MetricsResponse>>(
        `/api/v1/analytics/metrics?${queryParams.toString()}`,
        { method: 'GET' }
      );

      const data = response.data.data;
      this.setCacheData(cacheKey, data, 5 * 60 * 1000); // 5 minutes
      return data;
    } catch (error) {
      throw new Error(
        `Failed to get metrics: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }

  async getKPIs(category?: string): Promise<KPIMetric[]> {
    try {
      const queryParams = new URLSearchParams();
      if (category) queryParams.append('category', category);

      const response = await this.apiClient.request<AnalyticsApiResponse<KPIMetric[]>>(
        `/api/v1/analytics/kpis?${queryParams.toString()}`,
        { method: 'GET' }
      );

      return response.data.data;
    } catch (error) {
      throw new Error(
        `Failed to get KPIs: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }

  async getTimeSeries(
    metricIds: string[],
    options: {
      start: Date;
      end: Date;
      granularity: 'minute' | 'hour' | 'day' | 'week' | 'month';
      aggregation?: string;
    }
  ): Promise<TimeSeries[]> {
    try {
      const response = await this.apiClient.request<AnalyticsApiResponse<TimeSeries[]>>(
        '/api/v1/analytics/timeseries',
        {
          method: 'POST',
          body: JSON.stringify({
            metrics: metricIds,
            ...options,
          }),
          headers: { 'Content-Type': 'application/json' },
        }
      );

      return response.data.data;
    } catch (error) {
      throw new Error(
        `Failed to get time series: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }

  /**
   * Query Execution
   */
  async executeQuery(query: AnalyticsQuery): Promise<QueryResult> {
    try {
      const cacheKey = query.cache?.enabled ? `query:${JSON.stringify(query)}` : null;

      if (cacheKey) {
        const cached = this.getCachedData(cacheKey);
        if (cached) return { ...cached, fromCache: true };
      }

      const response = await this.apiClient.request<AnalyticsApiResponse<QueryResult>>(
        '/api/v1/analytics/query',
        {
          method: 'POST',
          body: JSON.stringify(query),
          headers: { 'Content-Type': 'application/json' },
        }
      );

      const result = response.data.data;

      if (cacheKey && query.cache?.ttl) {
        this.setCacheData(cacheKey, result, query.cache.ttl * 1000);
      }

      return { ...result, fromCache: false };
    } catch (error) {
      throw new Error(
        `Failed to execute query: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }

  /**
   * Reports
   */
  async getReports(filters?: { type?: string; isActive?: boolean }): Promise<AnalyticsReport[]> {
    try {
      const queryParams = new URLSearchParams();
      if (filters?.type) queryParams.append('type', filters.type);
      if (filters?.isActive !== undefined)
        queryParams.append('active', filters.isActive.toString());

      const response = await this.apiClient.request<AnalyticsApiResponse<AnalyticsReport[]>>(
        `/api/v1/analytics/reports?${queryParams.toString()}`,
        { method: 'GET' }
      );

      return response.data.data;
    } catch (error) {
      throw new Error(
        `Failed to get reports: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }

  async createReport(report: Omit<AnalyticsReport, 'id'>): Promise<string> {
    try {
      const response = await this.apiClient.request<AnalyticsApiResponse<{ id: string }>>(
        '/api/v1/analytics/reports',
        {
          method: 'POST',
          body: JSON.stringify(report),
          headers: { 'Content-Type': 'application/json' },
        }
      );

      return response.data.data.id;
    } catch (error) {
      throw new Error(
        `Failed to create report: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }

  async generateReport(reportId: string): Promise<string> {
    try {
      const response = await this.apiClient.request<AnalyticsApiResponse<{ downloadUrl: string }>>(
        `/api/v1/analytics/reports/${reportId}/generate`,
        { method: 'POST' }
      );

      return response.data.data.downloadUrl;
    } catch (error) {
      throw new Error(
        `Failed to generate report: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }

  /**
   * Data Export
   */
  async exportData(config: Omit<DataExport, 'id' | 'status' | 'requestedAt'>): Promise<string> {
    try {
      const response = await this.apiClient.request<AnalyticsApiResponse<{ exportId: string }>>(
        '/api/v1/analytics/export',
        {
          method: 'POST',
          body: JSON.stringify(config),
          headers: { 'Content-Type': 'application/json' },
        }
      );

      return response.data.data.exportId;
    } catch (error) {
      throw new Error(
        `Failed to export data: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }

  async getExportStatus(exportId: string): Promise<DataExport> {
    try {
      const response = await this.apiClient.request<AnalyticsApiResponse<DataExport>>(
        `/api/v1/analytics/export/${exportId}`,
        { method: 'GET' }
      );

      return response.data.data;
    } catch (error) {
      throw new Error(
        `Failed to get export status: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }

  /**
   * Business Intelligence Insights
   */
  async getInsights(filters?: {
    type?: string;
    severity?: string;
    status?: string;
  }): Promise<BusinessIntelligenceInsight[]> {
    try {
      const queryParams = new URLSearchParams();
      if (filters?.type) queryParams.append('type', filters.type);
      if (filters?.severity) queryParams.append('severity', filters.severity);
      if (filters?.status) queryParams.append('status', filters.status);

      const response = await this.apiClient.request<
        AnalyticsApiResponse<BusinessIntelligenceInsight[]>
      >(`/api/v1/analytics/insights?${queryParams.toString()}`, { method: 'GET' });

      return response.data.data;
    } catch (error) {
      throw new Error(
        `Failed to get insights: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }

  async resolveInsight(id: string): Promise<void> {
    try {
      await this.apiClient.request(`/api/v1/analytics/insights/${id}/resolve`, {
        method: 'POST',
      });
    } catch (error) {
      throw new Error(
        `Failed to resolve insight: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }

  /**
   * Event Tracking
   */
  async trackEvent(event: Omit<AnalyticsEvent, 'id' | 'timestamp'>): Promise<void> {
    try {
      await this.apiClient.request('/api/v1/analytics/events', {
        method: 'POST',
        body: JSON.stringify({
          ...event,
          timestamp: new Date(),
        }),
        headers: { 'Content-Type': 'application/json' },
      });
    } catch (error) {
      // Event tracking failures shouldn't break the application
      console.warn('Failed to track event:', error);
    }
  }

  /**
   * Advanced Analytics
   */
  async getCohortAnalysis(
    cohortId: string,
    options: {
      granularity: 'daily' | 'weekly' | 'monthly';
      periods: number;
    }
  ): Promise<RetentionAnalysis> {
    try {
      const response = await this.apiClient.request<AnalyticsApiResponse<RetentionAnalysis>>(
        `/api/v1/analytics/cohorts/${cohortId}/retention`,
        {
          method: 'POST',
          body: JSON.stringify(options),
          headers: { 'Content-Type': 'application/json' },
        }
      );

      return response.data.data;
    } catch (error) {
      throw new Error(
        `Failed to get cohort analysis: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }

  async getFunnelAnalysis(config: {
    steps: Array<{ name: string; event: string }>;
    timeframe: { start: Date; end: Date };
    segments?: Array<{ name: string; filter: any }>;
  }): Promise<FunnelAnalysis> {
    try {
      const response = await this.apiClient.request<AnalyticsApiResponse<FunnelAnalysis>>(
        '/api/v1/analytics/funnel',
        {
          method: 'POST',
          body: JSON.stringify(config),
          headers: { 'Content-Type': 'application/json' },
        }
      );

      return response.data.data;
    } catch (error) {
      throw new Error(
        `Failed to get funnel analysis: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }

  /**
   * Real-time Metrics
   */
  subscribeToMetric(metricId: string, callback: (data: RealTimeMetric) => void): () => void {
    if (!this.subscriptions.has(metricId)) {
      this.subscriptions.set(metricId, new Set());
    }

    this.subscriptions.get(metricId)!.add(callback);

    // In a real implementation, this would connect to a WebSocket or SSE
    // For now, simulate real-time updates
    this.startRealTimeUpdates(metricId);

    // Return unsubscribe function
    return () => {
      const callbacks = this.subscriptions.get(metricId);
      if (callbacks) {
        callbacks.delete(callback);
        if (callbacks.size === 0) {
          this.subscriptions.delete(metricId);
          this.stopRealTimeUpdates(metricId);
        }
      }
    };
  }

  private startRealTimeUpdates(metricId: string): void {
    // Implementation would depend on the real-time architecture
    // Could be WebSocket, Server-Sent Events, or polling
  }

  private stopRealTimeUpdates(metricId: string): void {
    // Clean up real-time subscriptions
  }

  /**
   * Metric Definitions
   */
  async getMetricDefinitions(category?: string): Promise<MetricDefinition[]> {
    try {
      const queryParams = new URLSearchParams();
      if (category) queryParams.append('category', category);

      const response = await this.apiClient.request<AnalyticsApiResponse<MetricDefinition[]>>(
        `/api/v1/analytics/metric-definitions?${queryParams.toString()}`,
        { method: 'GET' }
      );

      return response.data.data;
    } catch (error) {
      throw new Error(
        `Failed to get metric definitions: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }

  async createMetricDefinition(definition: Omit<MetricDefinition, 'id'>): Promise<string> {
    try {
      const response = await this.apiClient.request<AnalyticsApiResponse<{ id: string }>>(
        '/api/v1/analytics/metric-definitions',
        {
          method: 'POST',
          body: JSON.stringify(definition),
          headers: { 'Content-Type': 'application/json' },
        }
      );

      return response.data.data.id;
    } catch (error) {
      throw new Error(
        `Failed to create metric definition: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }

  /**
   * Cache Management
   */
  private getCachedData(key: string): any | null {
    const cached = this.cache.get(key);
    if (cached && cached.expires > Date.now()) {
      return cached.data;
    }
    if (cached) {
      this.cache.delete(key);
    }
    return null;
  }

  private setCacheData(key: string, data: any, ttl: number): void {
    this.cache.set(key, {
      data,
      expires: Date.now() + ttl,
    });
  }

  clearCache(): void {
    this.cache.clear();
  }
}
