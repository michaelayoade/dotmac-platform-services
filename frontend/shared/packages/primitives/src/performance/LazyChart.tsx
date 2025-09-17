/**
 * Lazy Chart Component
 * Lazy-loading wrapper for charts with performance optimization
 */

import React, { Suspense, lazy, useState, useEffect, useRef, useCallback } from 'react';
import { Skeleton } from '@dotmac/primitives';
import { trackError, markPerformance, measurePerformance } from '@dotmac/monitoring/observability';

// Lazy load chart components
const LazyLineChart = lazy(() => import('@dotmac/charts').then((m) => ({ default: m.LineChart })));
const LazyBarChart = lazy(() => import('@dotmac/charts').then((m) => ({ default: m.BarChart })));
const LazyPieChart = lazy(() => import('@dotmac/charts').then((m) => ({ default: m.PieChart })));
const LazyAreaChart = lazy(() => import('@dotmac/charts').then((m) => ({ default: m.AreaChart })));
const LazyScatterChart = lazy(() =>
  import('@dotmac/charts').then((m) => ({ default: m.ScatterChart }))
);

export interface LazyChartProps {
  type: 'line' | 'bar' | 'pie' | 'area' | 'scatter';
  data: any[];
  width?: number;
  height?: number;
  loading?: boolean;
  error?: string | null;
  intersectionThreshold?: number;
  loadOnVisible?: boolean;
  retryAttempts?: number;
  cacheKey?: string;
  onLoad?: () => void;
  onError?: (error: Error) => void;
  className?: string;
  [key: string]: any; // Allow other props to pass through to chart
}

interface ChartComponentMap {
  line: typeof LazyLineChart;
  bar: typeof LazyBarChart;
  pie: typeof LazyPieChart;
  area: typeof LazyAreaChart;
  scatter: typeof LazyScatterChart;
}

const CHART_COMPONENTS: ChartComponentMap = {
  line: LazyLineChart,
  bar: LazyBarChart,
  pie: LazyPieChart,
  area: LazyAreaChart,
  scatter: LazyScatterChart,
};

// Chart data cache
const chartCache = new Map<string, any>();

// Loading skeleton for charts
function ChartSkeleton({ width = 400, height = 300 }: { width?: number; height?: number }) {
  return (
    <div style={{ width, height }} className='bg-gray-50 rounded-lg animate-pulse'>
      <Skeleton className='h-full w-full' />
    </div>
  );
}

// Error fallback component
function ChartErrorFallback({
  error,
  onRetry,
  chartType,
}: {
  error: string;
  onRetry?: () => void;
  chartType: string;
}) {
  return (
    <div className='flex flex-col items-center justify-center p-8 bg-red-50 rounded-lg border border-red-200'>
      <div className='text-red-600 mb-2'>
        <svg className='w-8 h-8' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
          <path
            strokeLinecap='round'
            strokeLinejoin='round'
            strokeWidth={2}
            d='M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
          />
        </svg>
      </div>
      <div className='text-red-800 font-medium mb-1'>Chart Load Error</div>
      <div className='text-red-600 text-sm mb-4 text-center'>{error}</div>
      {onRetry && (
        <button
          onClick={onRetry}
          className='px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 text-sm'
        >
          Retry Loading {chartType} Chart
        </button>
      )}
    </div>
  );
}

export function LazyChart({
  type,
  data,
  width = 400,
  height = 300,
  loading = false,
  error = null,
  intersectionThreshold = 0.1,
  loadOnVisible = true,
  retryAttempts = 3,
  cacheKey,
  onLoad,
  onError,
  className = '',
  ...chartProps
}: LazyChartProps) {
  const [isVisible, setIsVisible] = useState(!loadOnVisible);
  const [loadError, setLoadError] = useState<string | null>(error);
  const [retryCount, setRetryCount] = useState(0);
  const [isLoading, setIsLoading] = useState(loading);
  const containerRef = useRef<HTMLDivElement>(null);
  const observerRef = useRef<IntersectionObserver | null>(null);

  // Setup intersection observer for lazy loading
  useEffect(() => {
    if (!loadOnVisible || isVisible) return;

    observerRef.current = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          markPerformance(`chart-visible-${type}`, { type, cacheKey });
          setIsVisible(true);
          observerRef.current?.disconnect();
        }
      },
      { threshold: intersectionThreshold }
    );

    if (containerRef.current) {
      observerRef.current.observe(containerRef.current);
    }

    return () => {
      observerRef.current?.disconnect();
    };
  }, [loadOnVisible, isVisible, intersectionThreshold, type, cacheKey]);

  // Handle component loading
  const handleLoad = useCallback(() => {
    setIsLoading(false);
    measurePerformance(`chart-load-${type}`, `chart-visible-${type}`);
    onLoad?.();
  }, [type, onLoad]);

  // Handle loading errors
  const handleError = useCallback(
    (err: Error) => {
      const errorMessage = err.message || 'Failed to load chart';
      setLoadError(errorMessage);
      setIsLoading(false);

      trackError(err, {
        component: 'LazyChart',
        chartType: type,
        retryCount,
        cacheKey,
      });

      onError?.(err);
    },
    [type, retryCount, cacheKey, onError]
  );

  // Retry loading
  const handleRetry = useCallback(() => {
    if (retryCount >= retryAttempts) return;

    setRetryCount((prev) => prev + 1);
    setLoadError(null);
    setIsLoading(true);

    markPerformance(`chart-retry-${type}-${retryCount + 1}`, {
      type,
      retryCount: retryCount + 1,
      cacheKey,
    });
  }, [retryCount, retryAttempts, type, cacheKey]);

  // Get chart component
  const ChartComponent = CHART_COMPONENTS[type];

  if (!ChartComponent) {
    return <ChartErrorFallback error={`Unknown chart type: ${type}`} chartType={type} />;
  }

  // Check cache if cacheKey is provided
  const cachedData = cacheKey ? chartCache.get(cacheKey) : null;
  const chartData = cachedData || data;

  // Cache data if cacheKey is provided and data is available
  useEffect(() => {
    if (cacheKey && data && data.length > 0) {
      chartCache.set(cacheKey, data);
    }
  }, [cacheKey, data]);

  return (
    <div ref={containerRef} className={`relative ${className}`} style={{ width, height }}>
      {!isVisible ? (
        <ChartSkeleton width={width} height={height} />
      ) : loadError ? (
        <ChartErrorFallback
          error={loadError}
          onRetry={retryCount < retryAttempts ? handleRetry : undefined}
          chartType={type}
        />
      ) : (
        <Suspense fallback={<ChartSkeleton width={width} height={height} />}>
          <ErrorBoundary
            onError={handleError}
            fallback={(error) => (
              <ChartErrorFallback
                error={error}
                onRetry={retryCount < retryAttempts ? handleRetry : undefined}
                chartType={type}
              />
            )}
          >
            {isLoading ? (
              <ChartSkeleton width={width} height={height} />
            ) : (
              <ChartComponent
                data={chartData}
                width={width}
                height={height}
                onLoad={handleLoad}
                onError={handleError}
                {...chartProps}
              />
            )}
          </ErrorBoundary>
        </Suspense>
      )}
    </div>
  );
}

// Error boundary for chart components
class ErrorBoundary extends React.Component<
  {
    children: React.ReactNode;
    fallback: (error: string) => React.ReactNode;
    onError?: (error: Error) => void;
  },
  { hasError: boolean; error: string }
> {
  constructor(props: any) {
    super(props);
    this.state = { hasError: false, error: '' };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error: error.message };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    this.props.onError?.(error);

    trackError(error, {
      component: 'ChartErrorBoundary',
      errorInfo: errorInfo.componentStack,
    });
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback(this.state.error);
    }

    return this.props.children;
  }
}

// Preload chart components
export function preloadChartComponents(types: string[] = ['line', 'bar', 'pie']) {
  types.forEach((type) => {
    if (type in CHART_COMPONENTS) {
      markPerformance(`chart-preload-${type}`);
      // Trigger lazy loading
      const Component = CHART_COMPONENTS[type as keyof ChartComponentMap];
      Component.preload?.();
    }
  });
}

// Clear chart cache
export function clearChartCache(cacheKey?: string) {
  if (cacheKey) {
    chartCache.delete(cacheKey);
  } else {
    chartCache.clear();
  }
}

// Get cache statistics
export function getChartCacheStats() {
  return {
    size: chartCache.size,
    keys: Array.from(chartCache.keys()),
  };
}

export default LazyChart;
