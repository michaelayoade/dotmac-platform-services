import { useState, useEffect, useCallback } from 'react';
import { AnalyticsService } from '../services/AnalyticsService';
import type { AnalyticsQuery, QueryResult } from '../types';

interface UseAnalyticsQueryOptions {
  enabled?: boolean;
  refetchInterval?: number;
  onSuccess?: (data: QueryResult) => void;
  onError?: (error: Error) => void;
}

export const useAnalyticsQuery = (
  query: AnalyticsQuery | null,
  options: UseAnalyticsQueryOptions = {}
) => {
  const [data, setData] = useState<QueryResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { enabled = true, refetchInterval, onSuccess, onError } = options;

  const executeQuery = useCallback(
    async (queryToExecute: AnalyticsQuery) => {
      if (!enabled) return;

      setIsLoading(true);
      setError(null);

      try {
        const result = await AnalyticsService.executeQuery(queryToExecute);
        setData(result);
        onSuccess?.(result);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Query execution failed';
        setError(errorMessage);
        onError?.(new Error(errorMessage));
      } finally {
        setIsLoading(false);
      }
    },
    [enabled, onSuccess, onError]
  );

  // Execute query when it changes
  useEffect(() => {
    if (query && enabled) {
      executeQuery(query);
    }
  }, [query, executeQuery, enabled]);

  // Set up refetch interval
  useEffect(() => {
    if (!refetchInterval || !query || !enabled) return;

    const interval = setInterval(() => {
      executeQuery(query);
    }, refetchInterval);

    return () => clearInterval(interval);
  }, [query, refetchInterval, executeQuery, enabled]);

  const refetch = useCallback(() => {
    if (query) {
      executeQuery(query);
    }
  }, [query, executeQuery]);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setIsLoading(false);
  }, []);

  return {
    data,
    isLoading,
    error,
    refetch,
    reset,
  };
};
