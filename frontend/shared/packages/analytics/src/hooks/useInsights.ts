import { useState, useEffect, useCallback } from 'react';
import { AnalyticsService } from '../services/AnalyticsService';
import type { BusinessIntelligenceInsight } from '../types';

interface UseInsightsOptions {
  category?: string;
  severity?: string;
  status?: string;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export const useInsights = (options: UseInsightsOptions = {}) => {
  const [insights, setInsights] = useState<BusinessIntelligenceInsight[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const {
    category,
    severity,
    status,
    autoRefresh = false,
    refreshInterval = 60000, // 1 minute
  } = options;

  const fetchInsights = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const filters: Record<string, string> = {};
      if (category) filters.category = category;
      if (severity) filters.severity = severity;
      if (status) filters.status = status;

      const data = await AnalyticsService.getInsights(
        Object.keys(filters).length > 0 ? filters : undefined
      );

      setInsights(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch insights';
      setError(errorMessage);
      console.error('Error fetching insights:', err);
    } finally {
      setIsLoading(false);
    }
  }, [category, severity, status]);

  // Initial fetch
  useEffect(() => {
    fetchInsights();
  }, [fetchInsights]);

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(fetchInsights, refreshInterval);
    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, fetchInsights]);

  const resolveInsight = useCallback(async (insightId: string) => {
    try {
      await AnalyticsService.resolveInsight(insightId);

      // Update local state
      setInsights((prev) =>
        prev.map((insight) =>
          insight.id === insightId
            ? { ...insight, status: 'resolved', resolvedAt: new Date() }
            : insight
        )
      );
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to resolve insight';
      throw new Error(errorMessage);
    }
  }, []);

  const dismissInsight = useCallback(async (insightId: string) => {
    try {
      // Assuming there's a dismiss endpoint similar to resolve
      await AnalyticsService.dismissInsight?.(insightId);

      // Update local state
      setInsights((prev) =>
        prev.map((insight) =>
          insight.id === insightId ? { ...insight, status: 'dismissed' } : insight
        )
      );
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to dismiss insight';
      throw new Error(errorMessage);
    }
  }, []);

  const markAsInvestigating = useCallback(async (insightId: string) => {
    try {
      // Update local state - in a real implementation, this might call an API
      setInsights((prev) =>
        prev.map((insight) =>
          insight.id === insightId ? { ...insight, status: 'investigating' } : insight
        )
      );
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update insight status';
      throw new Error(errorMessage);
    }
  }, []);

  const getInsightById = useCallback(
    (id: string) => {
      return insights.find((insight) => insight.id === id);
    },
    [insights]
  );

  const getInsightsByType = useCallback(
    (type: BusinessIntelligenceInsight['type']) => {
      return insights.filter((insight) => insight.type === type);
    },
    [insights]
  );

  const getInsightsBySeverity = useCallback(
    (targetSeverity: BusinessIntelligenceInsight['severity']) => {
      return insights.filter((insight) => insight.severity === targetSeverity);
    },
    [insights]
  );

  const getInsightsByStatus = useCallback(
    (targetStatus: BusinessIntelligenceInsight['status']) => {
      return insights.filter((insight) => insight.status === targetStatus);
    },
    [insights]
  );

  const getCriticalInsights = useCallback(() => {
    return insights.filter(
      (insight) =>
        insight.severity === 'critical' &&
        (insight.status === 'new' || insight.status === 'investigating')
    );
  }, [insights]);

  const getActionableInsights = useCallback(() => {
    return insights.filter(
      (insight) =>
        insight.actions &&
        insight.actions.length > 0 &&
        (insight.status === 'new' || insight.status === 'investigating')
    );
  }, [insights]);

  const refresh = useCallback(() => {
    fetchInsights();
  }, [fetchInsights]);

  // Calculate summary statistics
  const summary = {
    total: insights.length,
    new: insights.filter((i) => i.status === 'new').length,
    investigating: insights.filter((i) => i.status === 'investigating').length,
    resolved: insights.filter((i) => i.status === 'resolved').length,
    dismissed: insights.filter((i) => i.status === 'dismissed').length,
    critical: insights.filter((i) => i.severity === 'critical').length,
    high: insights.filter((i) => i.severity === 'high').length,
    medium: insights.filter((i) => i.severity === 'medium').length,
    low: insights.filter((i) => i.severity === 'low').length,
    byType: insights.reduce(
      (acc, insight) => {
        acc[insight.type] = (acc[insight.type] || 0) + 1;
        return acc;
      },
      {} as Record<string, number>
    ),
    averageConfidence:
      insights.length > 0
        ? insights.reduce((sum, insight) => sum + insight.confidence, 0) / insights.length
        : 0,
    lastCreated:
      insights.length > 0
        ? new Date(Math.max(...insights.map((i) => i.createdAt.getTime())))
        : null,
  };

  return {
    insights,
    isLoading,
    error,
    refresh,
    summary,
    resolveInsight,
    dismissInsight,
    markAsInvestigating,
    getInsightById,
    getInsightsByType,
    getInsightsBySeverity,
    getInsightsByStatus,
    getCriticalInsights,
    getActionableInsights,
  };
};
