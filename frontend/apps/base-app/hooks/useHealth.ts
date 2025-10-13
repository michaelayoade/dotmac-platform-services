import { useState, useCallback, useEffect } from 'react';
import { apiClient } from '@/lib/api/client';
import { logger } from '@/lib/logger';

export interface ServiceHealth {
  name: string;
  status: 'healthy' | 'degraded' | 'unhealthy';
  message: string;
  required: boolean;
  uptime?: number;
  responseTime?: number;
  lastCheck?: string;
}

export interface HealthSummary {
  status: string;
  healthy: boolean;
  services: ServiceHealth[];
  failed_services: string[];
  version?: string;
  timestamp?: string;
}

export const useHealth = () => {
  const [health, setHealth] = useState<HealthSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.get<HealthSummary>('/ready');

      if ('success' in response && (response as any).success && (response as any).data) {
        setHealth((response as any).data);
      } else if ('error' in response && (response as any).error) {
        setError((response as any).error.message);
      } else if (response.data) {
        setHealth(response.data);
      }
    } catch (err) {
      logger.error('Failed to fetch health data', err instanceof Error ? err : new Error(String(err)));
      setError('Failed to fetch health data');
    } finally {
      setLoading(false);
    }
  }, []);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, [fetchHealth]);

  return {
    health,
    loading,
    error,
    refreshHealth: fetchHealth,
  };
};