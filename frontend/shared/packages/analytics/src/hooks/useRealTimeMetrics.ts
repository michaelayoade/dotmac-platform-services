import { useState, useEffect, useCallback, useRef } from 'react';
import { AnalyticsService } from '../services/AnalyticsService';
import type { RealTimeMetric } from '../types';

interface UseRealTimeMetricsOptions {
  metricIds: string[];
  enabled?: boolean;
  bufferSize?: number;
  alertThresholds?: Record<string, { min?: number; max?: number }>;
  onAlert?: (metric: RealTimeMetric, alert: any) => void;
}

export const useRealTimeMetrics = (options: UseRealTimeMetricsOptions) => {
  const [metrics, setMetrics] = useState<Record<string, RealTimeMetric[]>>({});
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const { metricIds, enabled = true, bufferSize = 100, alertThresholds = {}, onAlert } = options;

  const subscriptionsRef = useRef<(() => void)[]>([]);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const reconnectAttempts = useRef(0);

  const addMetricData = useCallback(
    (metricId: string, data: RealTimeMetric) => {
      setMetrics((prev) => {
        const existing = prev[metricId] || [];
        const updated = [...existing, data].slice(-bufferSize);

        return {
          ...prev,
          [metricId]: updated,
        };
      });

      setLastUpdate(new Date());

      // Check for alerts
      if (alertThresholds[metricId] && onAlert) {
        const threshold = alertThresholds[metricId];

        if (threshold.min !== undefined && data.value < threshold.min) {
          onAlert(data, {
            type: 'threshold',
            condition: 'below_minimum',
            value: threshold.min,
            triggered: true,
          });
        }

        if (threshold.max !== undefined && data.value > threshold.max) {
          onAlert(data, {
            type: 'threshold',
            condition: 'above_maximum',
            value: threshold.max,
            triggered: true,
          });
        }
      }

      // Check for built-in alerts
      if (data.alerts) {
        data.alerts.forEach((alert) => {
          if (alert.triggered && onAlert) {
            onAlert(data, alert);
          }
        });
      }
    },
    [bufferSize, alertThresholds, onAlert]
  );

  const subscribe = useCallback(async () => {
    if (!enabled || metricIds.length === 0) return;

    try {
      setError(null);

      // Unsubscribe from existing subscriptions
      subscriptionsRef.current.forEach((unsubscribe) => unsubscribe());
      subscriptionsRef.current = [];

      // Subscribe to each metric
      const subscriptions = await Promise.all(
        metricIds.map(async (metricId) => {
          return AnalyticsService.subscribeToMetric(metricId, (data: RealTimeMetric) => {
            addMetricData(metricId, data);
          });
        })
      );

      subscriptionsRef.current = subscriptions;
      setIsConnected(true);
      reconnectAttempts.current = 0;
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to subscribe to real-time metrics';
      setError(errorMessage);
      setIsConnected(false);

      // Attempt to reconnect with exponential backoff
      const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
      reconnectAttempts.current++;

      reconnectTimeoutRef.current = setTimeout(() => {
        if (enabled) subscribe();
      }, delay);
    }
  }, [enabled, metricIds, addMetricData]);

  const unsubscribe = useCallback(() => {
    subscriptionsRef.current.forEach((unsubscribeFn) => unsubscribeFn());
    subscriptionsRef.current = [];
    setIsConnected(false);

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
  }, []);

  // Subscribe when enabled or metricIds change
  useEffect(() => {
    if (enabled && metricIds.length > 0) {
      subscribe();
    } else {
      unsubscribe();
    }

    return () => unsubscribe();
  }, [enabled, metricIds, subscribe, unsubscribe]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      unsubscribe();
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [unsubscribe]);

  const getLatestMetric = useCallback(
    (metricId: string): RealTimeMetric | null => {
      const metricData = metrics[metricId];
      return metricData && metricData.length > 0 ? metricData[metricData.length - 1] : null;
    },
    [metrics]
  );

  const getMetricHistory = useCallback(
    (metricId: string, limit?: number): RealTimeMetric[] => {
      const metricData = metrics[metricId] || [];
      return limit ? metricData.slice(-limit) : metricData;
    },
    [metrics]
  );

  const getMetricValue = useCallback(
    (metricId: string): number | null => {
      const latest = getLatestMetric(metricId);
      return latest ? latest.value : null;
    },
    [getLatestMetric]
  );

  const clearMetricHistory = useCallback((metricId?: string) => {
    if (metricId) {
      setMetrics((prev) => ({
        ...prev,
        [metricId]: [],
      }));
    } else {
      setMetrics({});
    }
  }, []);

  const reconnect = useCallback(() => {
    unsubscribe();
    subscribe();
  }, [unsubscribe, subscribe]);

  // Calculate summary statistics
  const summary = {
    connectedMetrics: Object.keys(metrics).filter((id) => metrics[id].length > 0).length,
    totalDataPoints: Object.values(metrics).reduce((sum, data) => sum + data.length, 0),
    isHealthy: isConnected && error === null,
    lastUpdate,
    averageLatency: Object.values(metrics)
      .flat()
      .filter((m) => m.timestamp)
      .slice(-10) // Last 10 data points
      .reduce((sum, m, _, arr) => {
        const latency = Date.now() - m.timestamp.getTime();
        return sum + latency / arr.length;
      }, 0),
  };

  return {
    metrics,
    isConnected,
    error,
    lastUpdate,
    summary,
    subscribe,
    unsubscribe,
    reconnect,
    getLatestMetric,
    getMetricHistory,
    getMetricValue,
    clearMetricHistory,
  };
};
