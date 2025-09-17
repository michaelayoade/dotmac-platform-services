import { useState, useEffect, useCallback } from 'react';
import { AnalyticsService } from '../services/AnalyticsService';
import type { KPIMetric } from '../types';

interface UseMetricsOptions {
  category?: string;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export const useMetrics = (options: UseMetricsOptions = {}) => {
  const [metrics, setMetrics] = useState<KPIMetric[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const {
    category,
    autoRefresh = false,
    refreshInterval = 30000, // 30 seconds
  } = options;

  const fetchMetrics = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const data = await AnalyticsService.getKPIMetrics({
        category,
        includeTargets: true,
        includeTrends: true,
      });

      setMetrics(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch metrics';
      setError(errorMessage);
      console.error('Error fetching metrics:', err);
    } finally {
      setIsLoading(false);
    }
  }, [category]);

  // Initial fetch
  useEffect(() => {
    fetchMetrics();
  }, [fetchMetrics]);

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(fetchMetrics, refreshInterval);
    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, fetchMetrics]);

  const refresh = useCallback(() => {
    fetchMetrics();
  }, [fetchMetrics]);

  const getMetricById = useCallback(
    (id: string) => {
      return metrics.find((metric) => metric.id === id);
    },
    [metrics]
  );

  const getMetricsByCategory = useCallback(
    (targetCategory: string) => {
      return metrics.filter((metric) => metric.category === targetCategory);
    },
    [metrics]
  );

  const getMetricsByStatus = useCallback(
    (status: KPIMetric['status']) => {
      return metrics.filter((metric) => metric.status === status);
    },
    [metrics]
  );

  // Calculate summary statistics
  const summary = {
    total: metrics.length,
    good: metrics.filter((m) => m.status === 'good').length,
    warning: metrics.filter((m) => m.status === 'warning').length,
    critical: metrics.filter((m) => m.status === 'critical').length,
    unknown: metrics.filter((m) => m.status === 'unknown').length,
    categories: [...new Set(metrics.map((m) => m.category))],
    lastUpdated:
      metrics.length > 0 ? new Date(Math.max(...metrics.map((m) => m.updatedAt.getTime()))) : null,
  };

  return {
    metrics,
    isLoading,
    error,
    refresh,
    summary,
    getMetricById,
    getMetricsByCategory,
    getMetricsByStatus,
  };
};
