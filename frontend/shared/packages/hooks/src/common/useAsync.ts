/**
 * Universal Async Hook
 * Handles loading states, errors, and data management
 */

import { useCallback, useEffect, useReducer } from 'react';

interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  lastFetch: number | null;
}

type AsyncAction<T> =
  | { type: 'LOADING' }
  | { type: 'SUCCESS'; payload: T }
  | { type: 'ERROR'; error: Error }
  | { type: 'RESET' };

function asyncReducer<T>(state: AsyncState<T>, action: AsyncAction<T>): AsyncState<T> {
  switch (action.type) {
    case 'LOADING':
      return { ...state, loading: true, error: null };
    case 'SUCCESS':
      return {
        data: action.payload,
        loading: false,
        error: null,
        lastFetch: Date.now(),
      };
    case 'ERROR':
      return { ...state, loading: false, error: action.error };
    case 'RESET':
      return { data: null, loading: false, error: null, lastFetch: null };
    default:
      return state;
  }
}

export interface UseAsyncOptions<T> {
  immediate?: boolean;
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
  cacheKey?: string;
  cacheTime?: number; // ms
}

export interface UseAsyncReturn<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  execute: (...args: any[]) => Promise<T>;
  reset: () => void;
  refetch: () => Promise<T | void>;
  lastFetch: number | null;
}

export function useAsync<T>(
  asyncFunction: (...args: any[]) => Promise<T>,
  options: UseAsyncOptions<T> = {}
): UseAsyncReturn<T> {
  const { immediate = false, onSuccess, onError, cacheKey, cacheTime = 5 * 60 * 1000 } = options;

  const [state, dispatch] = useReducer(asyncReducer<T>, {
    data: null,
    loading: false,
    error: null,
    lastFetch: null,
  });

  // Check cache
  const getCachedData = useCallback((): T | null => {
    if (!cacheKey) return null;

    try {
      const cached = localStorage.getItem(`async-cache-${cacheKey}`);
      if (!cached) return null;

      const { data, timestamp } = JSON.parse(cached);
      if (Date.now() - timestamp > cacheTime) {
        localStorage.removeItem(`async-cache-${cacheKey}`);
        return null;
      }

      return data;
    } catch {
      return null;
    }
  }, [cacheKey, cacheTime]);

  // Save to cache
  const setCachedData = useCallback(
    (data: T) => {
      if (!cacheKey) return;

      try {
        localStorage.setItem(
          `async-cache-${cacheKey}`,
          JSON.stringify({
            data,
            timestamp: Date.now(),
          })
        );
      } catch {
        // Fail silently
      }
    },
    [cacheKey]
  );

  const execute = useCallback(
    async (...args: any[]): Promise<T> => {
      // Check cache first
      const cachedData = getCachedData();
      if (cachedData) {
        dispatch({ type: 'SUCCESS', payload: cachedData });
        return cachedData;
      }

      dispatch({ type: 'LOADING' });

      try {
        const result = await asyncFunction(...args);

        dispatch({ type: 'SUCCESS', payload: result });
        setCachedData(result);

        if (onSuccess) {
          onSuccess(result);
        }

        return result;
      } catch (error) {
        const err = error instanceof Error ? error : new Error(String(error));
        dispatch({ type: 'ERROR', error: err });

        if (onError) {
          onError(err);
        }

        throw err;
      }
    },
    [asyncFunction, onSuccess, onError, getCachedData, setCachedData]
  );

  const reset = useCallback(() => {
    dispatch({ type: 'RESET' });
    if (cacheKey) {
      localStorage.removeItem(`async-cache-${cacheKey}`);
    }
  }, [cacheKey]);

  const refetch = useCallback(async (): Promise<T | void> => {
    if (state.loading) return;

    try {
      return await execute();
    } catch (error) {
      // Error already handled in execute
    }
  }, [execute, state.loading]);

  // Execute immediately if requested
  useEffect(() => {
    if (immediate) {
      execute();
    }
  }, [immediate, execute]);

  return {
    data: state.data,
    loading: state.loading,
    error: state.error,
    execute,
    reset,
    refetch,
    lastFetch: state.lastFetch,
  };
}
