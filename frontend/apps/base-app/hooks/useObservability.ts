import { useState, useEffect } from 'react';
import axios from 'axios';
import { useToast } from '@/components/ui/use-toast';

// Migrated from sonner to useToast hook
// Note: toast options have changed:
// - sonner: toast.success('msg') -> useToast: toast({ title: 'Success', description: 'msg' })
// - sonner: toast.error('msg') -> useToast: toast({ title: 'Error', description: 'msg', variant: 'destructive' })
// - For complex options, refer to useToast documentation

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export interface SpanData {
  span_id: string;
  parent_span_id?: string;
  name: string;
  service: string;
  duration: number;
  start_time: string;
  attributes: Record<string, unknown>;
}

export interface TraceData {
  trace_id: string;
  service: string;
  operation: string;
  duration: number;
  status: 'success' | 'error' | 'warning';
  timestamp: string;
  spans: number;
  span_details: SpanData[];
}

export interface TracesResponse {
  traces: TraceData[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

export interface MetricDataPoint {
  timestamp: string;
  value: number;
  labels: Record<string, string>;
}

export interface MetricSeries {
  name: string;
  type: 'counter' | 'gauge' | 'histogram';
  data_points: MetricDataPoint[];
  unit: string;
}

export interface MetricsResponse {
  metrics: MetricSeries[];
  time_range: {
    start: string;
    end: string;
  };
}

export interface ServiceDependency {
  from_service: string;
  to_service: string;
  request_count: number;
  error_rate: number;
  avg_latency: number;
}

export interface ServiceMapResponse {
  services: string[];
  dependencies: ServiceDependency[];
  health_scores: Record<string, number>;
}

export interface PerformanceMetrics {
  percentile: string;
  value: number;
  target: number;
  within_sla: boolean;
}

export interface PerformanceResponse {
  percentiles: PerformanceMetrics[];
  slowest_endpoints: Array<{
    endpoint: string;
    avg_latency: number;
    status_code: number;
  }>;
  most_frequent_errors: Array<{
    error_type: string;
    count: number;
    status_code: number;
  }>;
}

export interface TracesFilter {
  service?: string;
  status?: 'success' | 'error' | 'warning';
  min_duration?: number;
  start_time?: string;
  end_time?: string;
  page?: number;
  page_size?: number;
}

export function useTraces(filters: TracesFilter = {}) {
  const { toast } = useToast();

  const [traces, setTraces] = useState<TraceData[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pagination, setPagination] = useState({
    total: 0,
    page: 1,
    page_size: 50,
    has_more: false,
  });

  const fetchTraces = async (customFilters?: TracesFilter) => {
    const activeFilters = { ...filters, ...customFilters };

    try {
      setIsLoading(true);
      setError(null);

      const params = new URLSearchParams();
      if (activeFilters.service) params.append('service', activeFilters.service);
      if (activeFilters.status) params.append('status', activeFilters.status);
      if (activeFilters.min_duration) params.append('min_duration', activeFilters.min_duration.toString());
      if (activeFilters.start_time) params.append('start_time', activeFilters.start_time);
      if (activeFilters.end_time) params.append('end_time', activeFilters.end_time);
      if (activeFilters.page) params.append('page', activeFilters.page.toString());
      if (activeFilters.page_size) params.append('page_size', activeFilters.page_size.toString());

      const response = await axios.get<TracesResponse>(
        `${API_BASE_URL}/api/v1/observability/traces?${params.toString()}`,
        { withCredentials: true }
      );

      setTraces(response.data.traces);
      setPagination({
        total: response.data.total,
        page: response.data.page,
        page_size: response.data.page_size,
        has_more: response.data.has_more,
      });
    } catch (err: unknown) {
      const message = axios.isAxiosError(err)
        ? err.response?.data?.detail || 'Failed to fetch traces'
        : 'An error occurred';
      setError(message);
      toast({ title: 'Error', description: message, variant: 'destructive' });
    } finally {
      setIsLoading(false);
    }
  };

  const fetchTraceDetails = async (traceId: string): Promise<TraceData | null> => {
    try {
      const response = await axios.get<TraceData>(
        `${API_BASE_URL}/api/v1/observability/traces/${traceId}`,
        { withCredentials: true }
      );
      return response.data;
    } catch (err: unknown) {
      console.error('Failed to fetch trace details:', err);
      return null;
    }
  };

  useEffect(() => {
    fetchTraces();
  }, []);

  return {
    traces,
    isLoading,
    error,
    pagination,
    refetch: fetchTraces,
    fetchTraceDetails,
  };
}

export function useMetrics(metricNames?: string[]) {
  const { toast } = useToast();
  const [metrics, setMetrics] = useState<MetricSeries[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchMetrics = async (customMetrics?: string[], startTime?: string, endTime?: string) => {
    const metricsToFetch = customMetrics || metricNames;

    try {
      setIsLoading(true);
      setError(null);

      const params = new URLSearchParams();
      if (metricsToFetch && metricsToFetch.length > 0) {
        params.append('metrics', metricsToFetch.join(','));
      }
      if (startTime) params.append('start_time', startTime);
      if (endTime) params.append('end_time', endTime);

      const response = await axios.get<MetricsResponse>(
        `${API_BASE_URL}/api/v1/observability/metrics?${params.toString()}`,
        { withCredentials: true }
      );

      setMetrics(response.data.metrics);
    } catch (err: unknown) {
      const message = axios.isAxiosError(err)
        ? err.response?.data?.detail || 'Failed to fetch metrics'
        : 'An error occurred';
      setError(message);
      toast({ title: 'Error', description: message, variant: 'destructive' });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
  }, []);

  return {
    metrics,
    isLoading,
    error,
    refetch: fetchMetrics,
  };
}

export function useServiceMap() {
  const { toast } = useToast();
  const [serviceMap, setServiceMap] = useState<ServiceMapResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchServiceMap = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await axios.get<ServiceMapResponse>(
        `${API_BASE_URL}/api/v1/observability/service-map`,
        { withCredentials: true }
      );

      setServiceMap(response.data);
    } catch (err: unknown) {
      const message = axios.isAxiosError(err)
        ? err.response?.data?.detail || 'Failed to fetch service map'
        : 'An error occurred';
      setError(message);
      toast({ title: 'Error', description: message, variant: 'destructive' });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchServiceMap();
  }, []);

  return {
    serviceMap,
    isLoading,
    error,
    refetch: fetchServiceMap,
  };
}

export function usePerformance() {
  const { toast } = useToast();
  const [performance, setPerformance] = useState<PerformanceResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPerformance = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await axios.get<PerformanceResponse>(
        `${API_BASE_URL}/api/v1/observability/performance`,
        { withCredentials: true }
      );

      setPerformance(response.data);
    } catch (err: unknown) {
      const message = axios.isAxiosError(err)
        ? err.response?.data?.detail || 'Failed to fetch performance metrics'
        : 'An error occurred';
      setError(message);
      toast({ title: 'Error', description: message, variant: 'destructive' });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPerformance();
  }, []);

  return {
    performance,
    isLoading,
    error,
    refetch: fetchPerformance,
  };
}