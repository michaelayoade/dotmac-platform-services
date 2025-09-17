/**
 * Analytics Service Tests
 * Critical business intelligence and metrics testing
 */

import { AnalyticsService } from '../AnalyticsService';
import type {
  AnalyticsDashboard,
  KPIMetric,
  TimeSeries,
  AnalyticsQuery,
  BusinessIntelligenceInsight,
  RealTimeMetric,
} from '../../types';

// Mock the API client
jest.mock('@dotmac/headless/api', () => ({
  getApiClient: () => ({
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
  }),
}));

describe('AnalyticsService', () => {
  let analyticsService: AnalyticsService;
  let mockApiClient: jest.Mocked<any>;

  beforeEach(() => {
    analyticsService = new AnalyticsService();
    mockApiClient = require('@dotmac/headless/api').getApiClient();
    jest.clearAllMocks();
  });

  describe('Dashboard Management', () => {
    const mockDashboard: AnalyticsDashboard = {
      id: 'dashboard_001',
      name: 'ISP Performance Dashboard',
      description: 'Key metrics for ISP operations',
      widgets: [
        {
          id: 'widget_001',
          type: 'metric_card',
          title: 'Total Revenue',
          config: { metric: 'monthly_revenue' },
          position: { x: 0, y: 0, width: 4, height: 2 },
        },
        {
          id: 'widget_002',
          type: 'chart',
          title: 'Customer Growth',
          config: { chartType: 'line', metric: 'customer_count' },
          position: { x: 4, y: 0, width: 8, height: 4 },
        },
      ],
      filters: { dateRange: 'last_30_days', region: 'all' },
      refreshInterval: 300000, // 5 minutes
      isPublic: false,
      createdBy: 'user_001',
      createdAt: '2024-08-01T00:00:00Z',
      updatedAt: '2024-08-30T12:00:00Z',
    };

    test('fetches dashboards with filtering', async () => {
      mockApiClient.get.mockResolvedValue({
        data: { dashboards: [mockDashboard], total: 1 },
      });

      const result = await analyticsService.getDashboards({
        category: 'operations',
        isPublic: false,
      });

      expect(mockApiClient.get).toHaveBeenCalledWith('/analytics/dashboards', {
        params: { category: 'operations', isPublic: false },
      });
      expect(result.dashboards).toHaveLength(1);
      expect(result.dashboards[0]).toMatchObject(mockDashboard);
    });

    test('creates dashboard with validation', async () => {
      const newDashboard = {
        name: 'Customer Satisfaction Dashboard',
        description: 'Track customer satisfaction metrics',
        widgets: [],
      };

      mockApiClient.post.mockResolvedValue({
        data: { ...mockDashboard, ...newDashboard },
      });

      const result = await analyticsService.createDashboard(newDashboard);

      expect(mockApiClient.post).toHaveBeenCalledWith('/analytics/dashboards', newDashboard);
      expect(result.name).toBe(newDashboard.name);
    });

    test('updates dashboard widgets', async () => {
      const updatedWidgets = [
        {
          id: 'widget_003',
          type: 'gauge',
          title: 'Network Uptime',
          config: { metric: 'uptime_percentage', threshold: 99.9 },
          position: { x: 0, y: 4, width: 6, height: 3 },
        },
      ];

      mockApiClient.put.mockResolvedValue({
        data: { ...mockDashboard, widgets: updatedWidgets },
      });

      const result = await analyticsService.updateDashboard('dashboard_001', {
        widgets: updatedWidgets,
      });

      expect(result.widgets).toHaveLength(1);
      expect(result.widgets[0].title).toBe('Network Uptime');
    });
  });

  describe('KPI Metrics', () => {
    const mockKPIs: KPIMetric[] = [
      {
        id: 'revenue_monthly',
        name: 'Monthly Revenue',
        value: 125000,
        target: 150000,
        unit: 'USD',
        trend: 'up',
        changePercent: 8.5,
        category: 'financial',
        period: '2024-08',
        lastUpdated: '2024-08-30T23:59:59Z',
      },
      {
        id: 'customer_churn',
        name: 'Customer Churn Rate',
        value: 2.1,
        target: 2.0,
        unit: 'percent',
        trend: 'up',
        changePercent: 5.0,
        category: 'customer',
        period: '2024-08',
        lastUpdated: '2024-08-30T23:59:59Z',
      },
    ];

    test('retrieves KPI metrics with trend analysis', async () => {
      mockApiClient.get.mockResolvedValue({
        data: { kpis: mockKPIs, metadata: { calculated_at: '2024-08-30T23:59:59Z' } },
      });

      const result = await analyticsService.getKPIMetrics({
        category: ['financial', 'customer'],
        period: '2024-08',
      });

      expect(result.kpis).toHaveLength(2);
      expect(result.kpis[0].trend).toBe('up');
      expect(result.kpis[1].changePercent).toBe(5.0);
    });

    test('calculates KPI targets and thresholds', async () => {
      const kpi = mockKPIs[0]; // Revenue KPI
      const achievement = (kpi.value / kpi.target!) * 100;

      expect(achievement).toBeCloseTo(83.33, 2); // 125000/150000 * 100
      expect(kpi.trend).toBe('up');
    });

    test('handles missing KPI data gracefully', async () => {
      mockApiClient.get.mockResolvedValue({
        data: { kpis: [], metadata: { error: 'No data available' } },
      });

      const result = await analyticsService.getKPIMetrics({
        period: '2024-99', // Invalid period
      });

      expect(result.kpis).toHaveLength(0);
      expect(result.metadata.error).toBe('No data available');
    });
  });

  describe('Time Series Analytics', () => {
    const mockTimeSeries: TimeSeries = {
      metric: 'customer_growth',
      data: [
        { timestamp: '2024-08-01T00:00:00Z', value: 1000 },
        { timestamp: '2024-08-15T00:00:00Z', value: 1050 },
        { timestamp: '2024-08-30T00:00:00Z', value: 1120 },
      ],
      aggregation: 'daily',
      unit: 'count',
      metadata: {
        trend: 'increasing',
        growthRate: 12.0, // 12% growth over period
        seasonality: 'none',
      },
    };

    test('processes time series data with trend analysis', async () => {
      mockApiClient.get.mockResolvedValue({
        data: mockTimeSeries,
      });

      const result = await analyticsService.getTimeSeriesData({
        metric: 'customer_growth',
        dateRange: { start: '2024-08-01', end: '2024-08-30' },
        aggregation: 'daily',
      });

      expect(result.data).toHaveLength(3);
      expect(result.metadata.trend).toBe('increasing');
      expect(result.metadata.growthRate).toBe(12.0);
    });

    test('calculates time series statistics', () => {
      const values = mockTimeSeries.data.map((d) => d.value);
      const mean = values.reduce((a, b) => a + b, 0) / values.length;
      const variance =
        values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length;
      const stdDev = Math.sqrt(variance);

      expect(mean).toBeCloseTo(1056.67, 2);
      expect(stdDev).toBeGreaterThan(0);
    });

    test('detects anomalies in time series', async () => {
      const anomalousData: TimeSeries = {
        ...mockTimeSeries,
        data: [
          { timestamp: '2024-08-01T00:00:00Z', value: 1000 },
          { timestamp: '2024-08-15T00:00:00Z', value: 500 }, // Anomalous drop
          { timestamp: '2024-08-30T00:00:00Z', value: 1050 },
        ],
      };

      mockApiClient.get.mockResolvedValue({
        data: anomalousData,
      });

      const result = await analyticsService.detectAnomalies('customer_growth', {
        sensitivity: 0.8,
        algorithm: 'statistical',
      });

      expect(result.anomalies).toHaveLength(1);
      expect(result.anomalies[0].timestamp).toBe('2024-08-15T00:00:00Z');
      expect(result.anomalies[0].severity).toBe('high');
    });
  });

  describe('Real-time Analytics', () => {
    test('subscribes to real-time metrics', () => {
      const mockCallback = jest.fn();
      const metricId = 'active_connections';

      analyticsService.subscribeToRealTimeMetric(metricId, mockCallback);

      // Simulate real-time update
      const realtimeUpdate: RealTimeMetric = {
        id: metricId,
        value: 1250,
        timestamp: '2024-08-30T15:30:00Z',
        trend: 'stable',
        alerts: [],
      };

      analyticsService['handleRealtimeUpdate'](realtimeUpdate);

      expect(mockCallback).toHaveBeenCalledWith(realtimeUpdate);
    });

    test('handles real-time alerts and thresholds', () => {
      const alertMetric: RealTimeMetric = {
        id: 'network_latency',
        value: 250, // High latency
        timestamp: '2024-08-30T15:30:00Z',
        trend: 'up',
        alerts: [
          {
            level: 'warning',
            message: 'Network latency above acceptable threshold',
            threshold: 200,
            timestamp: '2024-08-30T15:30:00Z',
          },
        ],
      };

      const alertCallback = jest.fn();
      analyticsService.subscribeToRealTimeMetric('network_latency', alertCallback);
      analyticsService['handleRealtimeUpdate'](alertMetric);

      expect(alertCallback).toHaveBeenCalledWith(alertMetric);
      expect(alertMetric.alerts).toHaveLength(1);
      expect(alertMetric.alerts[0].level).toBe('warning');
    });

    test('unsubscribes from real-time metrics', () => {
      const callback = jest.fn();
      const metricId = 'bandwidth_usage';

      analyticsService.subscribeToRealTimeMetric(metricId, callback);
      analyticsService.unsubscribeFromRealTimeMetric(metricId, callback);

      // Simulate update after unsubscribe
      const update: RealTimeMetric = {
        id: metricId,
        value: 75.5,
        timestamp: '2024-08-30T15:30:00Z',
        trend: 'stable',
        alerts: [],
      };

      analyticsService['handleRealtimeUpdate'](update);

      expect(callback).not.toHaveBeenCalled();
    });
  });

  describe('Query Processing', () => {
    test('processes complex analytical queries', async () => {
      const query: AnalyticsQuery = {
        select: ['revenue', 'customer_count', 'churn_rate'],
        from: 'monthly_metrics',
        where: {
          date: { gte: '2024-01-01', lte: '2024-08-31' },
          region: { in: ['north', 'south'] },
        },
        groupBy: ['region', 'month'],
        orderBy: [{ field: 'revenue', direction: 'desc' }],
        limit: 100,
      };

      const mockQueryResult = {
        data: [
          {
            revenue: 125000,
            customer_count: 1120,
            churn_rate: 2.1,
            region: 'north',
            month: '2024-08',
          },
          {
            revenue: 98000,
            customer_count: 890,
            churn_rate: 1.8,
            region: 'south',
            month: '2024-08',
          },
        ],
        metadata: {
          totalRows: 16,
          executionTime: 45,
          fromCache: false,
        },
      };

      mockApiClient.post.mockResolvedValue({
        data: mockQueryResult,
      });

      const result = await analyticsService.executeQuery(query);

      expect(result.data).toHaveLength(2);
      expect(result.metadata.executionTime).toBe(45);
    });

    test('validates query syntax and parameters', () => {
      const invalidQuery = {
        select: [], // Empty select
        from: '', // Empty table
        where: { invalid_field: 'test' },
      };

      expect(() => analyticsService.validateQuery(invalidQuery)).toThrow('Invalid query structure');
    });

    test('optimizes query performance with caching', async () => {
      const query: AnalyticsQuery = {
        select: ['total_revenue'],
        from: 'daily_revenue',
        where: { date: '2024-08-30' },
      };

      // First query execution
      mockApiClient.post.mockResolvedValue({
        data: { data: [{ total_revenue: 4250 }], metadata: { fromCache: false } },
      });

      const result1 = await analyticsService.executeQuery(query);
      expect(result1.metadata.fromCache).toBe(false);

      // Second identical query (should hit cache)
      const result2 = await analyticsService.executeQuery(query);
      expect(result2.data).toEqual(result1.data);
    });
  });

  describe('Business Intelligence Insights', () => {
    test('generates automated insights from data patterns', async () => {
      const mockInsights: BusinessIntelligenceInsight[] = [
        {
          id: 'insight_001',
          type: 'trend',
          title: 'Customer Growth Acceleration',
          description: 'Customer acquisition rate has increased by 35% compared to last quarter',
          confidence: 0.92,
          impact: 'high',
          category: 'growth',
          metrics: ['customer_count', 'acquisition_rate'],
          recommendations: [
            'Consider expanding marketing budget in high-performing regions',
            'Analyze customer acquisition channels for optimization opportunities',
          ],
          generatedAt: '2024-08-30T10:00:00Z',
        },
        {
          id: 'insight_002',
          type: 'anomaly',
          title: 'Unusual Churn Pattern',
          description: 'Enterprise customer churn increased by 15% in the last 2 weeks',
          confidence: 0.87,
          impact: 'high',
          category: 'retention',
          metrics: ['churn_rate', 'enterprise_customers'],
          recommendations: [
            'Reach out to at-risk enterprise accounts',
            'Review recent service quality metrics',
          ],
          generatedAt: '2024-08-30T10:00:00Z',
        },
      ];

      mockApiClient.get.mockResolvedValue({
        data: { insights: mockInsights, confidence_threshold: 0.8 },
      });

      const result = await analyticsService.getBusinessIntelligenceInsights({
        categories: ['growth', 'retention'],
        minConfidence: 0.8,
      });

      expect(result.insights).toHaveLength(2);
      expect(result.insights[0].confidence).toBeGreaterThan(0.9);
      expect(result.insights[1].impact).toBe('high');
    });

    test('prioritizes insights by business impact', () => {
      const insights = [
        { impact: 'low', confidence: 0.95, category: 'operational' },
        { impact: 'high', confidence: 0.85, category: 'financial' },
        { impact: 'medium', confidence: 0.9, category: 'customer' },
      ];

      const prioritized = analyticsService.prioritizeInsights(insights);

      expect(prioritized[0].impact).toBe('high');
      expect(prioritized[1].confidence).toBeGreaterThan(prioritized[2].confidence);
    });
  });

  describe('Data Export and Reporting', () => {
    test('exports analytics data in multiple formats', async () => {
      const exportRequest = {
        query: { select: ['*'], from: 'customer_metrics' },
        format: 'xlsx',
        includeCharts: true,
        filename: 'customer_analytics_2024_08',
      };

      mockApiClient.post.mockResolvedValue({
        data: {
          downloadUrl: 'https://exports.example.com/file123.xlsx',
          fileSize: 2048576, // 2MB
          expiresAt: '2024-08-31T23:59:59Z',
        },
      });

      const result = await analyticsService.exportData(exportRequest);

      expect(result.downloadUrl).toContain('.xlsx');
      expect(result.fileSize).toBeGreaterThan(0);
      expect(result.expiresAt).toBeDefined();
    });

    test('schedules recurring reports', async () => {
      const scheduleConfig = {
        name: 'Weekly Performance Report',
        query: { select: ['revenue', 'customers'], from: 'weekly_summary' },
        format: 'pdf',
        schedule: '0 9 * * 1', // Every Monday at 9 AM
        recipients: ['manager@company.com', 'analyst@company.com'],
        includeInsights: true,
      };

      mockApiClient.post.mockResolvedValue({
        data: {
          scheduleId: 'schedule_001',
          nextRun: '2024-09-02T09:00:00Z',
          status: 'active',
        },
      });

      const result = await analyticsService.scheduleReport(scheduleConfig);

      expect(result.scheduleId).toBe('schedule_001');
      expect(result.status).toBe('active');
    });
  });

  describe('Performance and Optimization', () => {
    test('handles large dataset queries efficiently', async () => {
      const largeDataQuery = {
        select: ['*'],
        from: 'transaction_logs',
        where: { date: { gte: '2024-01-01', lte: '2024-08-31' } },
        limit: 10000,
      };

      const startTime = performance.now();

      mockApiClient.post.mockResolvedValue({
        data: {
          data: Array.from({ length: 10000 }, (_, i) => ({ id: i, value: Math.random() * 1000 })),
          metadata: { totalRows: 50000, executionTime: 1200 },
        },
      });

      const result = await analyticsService.executeQuery(largeDataQuery);
      const duration = performance.now() - startTime;

      expect(result.data).toHaveLength(10000);
      expect(duration).toBeLessThan(5000); // Should complete within 5 seconds
    });

    test('implements efficient caching strategy', () => {
      const cacheKey = 'revenue_2024_08';
      const testData = { revenue: 125000, period: '2024-08' };

      analyticsService['cache'].set(cacheKey, { data: testData, expires: Date.now() + 300000 });

      const cached = analyticsService['getCachedData'](cacheKey);
      expect(cached).toEqual(testData);

      // Test expiration
      analyticsService['cache'].set(cacheKey, { data: testData, expires: Date.now() - 1000 });
      const expired = analyticsService['getCachedData'](cacheKey);
      expect(expired).toBeNull();
    });
  });
});
