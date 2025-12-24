/**
 * Observability API
 *
 * Distributed tracing, metrics, service maps, and performance analytics
 */

import { api } from "./client";

// ============================================================================
// Trace Types
// ============================================================================

export type TraceStatus = "success" | "error" | "warning";

export interface TraceSpan {
  spanId: string;
  parentSpanId?: string;
  name: string;
  service: string;
  duration: number;
  startTime: string;
  attributes?: Record<string, unknown>;
}

export interface TraceData {
  traceId: string;
  service: string;
  operation: string;
  duration: number;
  status: TraceStatus;
  timestamp: string;
  spans: number;
  spanDetails: TraceSpan[];
}

export interface TracesResponse {
  traces: TraceData[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}

// ============================================================================
// Trace Queries
// ============================================================================

export interface GetTracesParams {
  service?: string;
  status?: TraceStatus | "ok" | "unset";
  minDuration?: number;
  startTime?: string;
  endTime?: string;
  page?: number;
  pageSize?: number;
}

function normalizeTraceStatus(status?: GetTracesParams["status"]): TraceStatus | undefined {
  if (!status || status === "unset") {
    return undefined;
  }
  if (status === "ok") {
    return "success";
  }
  return status;
}

export async function getTraces(params: GetTracesParams = {}): Promise<TracesResponse> {
  return api.get<TracesResponse>("/api/v1/observability/traces", {
    params: {
      service: params.service,
      status: normalizeTraceStatus(params.status),
      minDuration: params.minDuration,
      startTime: params.startTime,
      endTime: params.endTime,
      page: params.page,
      pageSize: params.pageSize,
    },
  });
}

export async function getTrace(traceId: string): Promise<TraceData> {
  return api.get<TraceData>(`/api/v1/observability/traces/${traceId}`);
}

export async function getTraceSpans(traceId: string): Promise<TraceSpan[]> {
  const trace = await getTrace(traceId);
  return trace.spanDetails ?? [];
}

export async function searchTraces(query: {
  query: string;
  startTime?: string;
  endTime?: string;
  limit?: number;
}): Promise<TraceData[]> {
  const response = await getTraces({
    startTime: query.startTime,
    endTime: query.endTime,
    pageSize: query.limit,
  });
  const needle = query.query.trim().toLowerCase();
  if (!needle) {
    return response.traces;
  }

  return response.traces.filter((trace) => {
    return (
      trace.traceId.toLowerCase().includes(needle) ||
      trace.service.toLowerCase().includes(needle) ||
      trace.operation.toLowerCase().includes(needle) ||
      trace.status.toLowerCase().includes(needle)
    );
  });
}

// ============================================================================
// Metrics Types
// ============================================================================

export type MetricType = "counter" | "gauge" | "histogram";

export interface MetricDataPoint {
  timestamp: string;
  value: number;
  labels?: Record<string, string>;
}

export interface MetricSeries {
  name: string;
  type: MetricType;
  unit?: string;
  dataPoints: MetricDataPoint[];
}

export interface MetricsQueryParams {
  metricName?: string;
  metricNames?: string[];
  startTime?: string;
  endTime?: string;
}

export interface MetricsResponse {
  metrics: MetricSeries[];
  timeRange: { start: string; end: string };
}

export async function getMetrics(params: MetricsQueryParams = {}): Promise<MetricsResponse> {
  const metricNames = params.metricNames ?? (params.metricName ? [params.metricName] : undefined);

  return api.get<MetricsResponse>("/api/v1/observability/metrics", {
    params: {
      metrics: metricNames?.join(","),
      startTime: params.startTime,
      endTime: params.endTime,
    },
  });
}

export async function getMetricsSeries(
  metricName: string,
  params?: { startTime?: string; endTime?: string; step?: string }
): Promise<MetricSeries> {
  const response = await getMetrics({
    metricName,
    startTime: params?.startTime,
    endTime: params?.endTime,
  });

  const series = response.metrics.find((metric) => metric.name === metricName);
  return (
    series ?? {
      name: metricName,
      type: "gauge",
      unit: "count",
      dataPoints: [],
    }
  );
}

export async function queryMetrics(query: {
  promql: string;
  startTime?: string;
  endTime?: string;
  step?: string;
}): Promise<MetricsResponse> {
  return getMetrics({
    metricName: query.promql,
    startTime: query.startTime,
    endTime: query.endTime,
  });
}

// ============================================================================
// Service Map
// ============================================================================

export interface ServiceDependency {
  fromService: string;
  toService: string;
  requestCount: number;
  errorRate: number;
  avgLatency: number;
}

export interface ServiceMap {
  services: string[];
  dependencies: ServiceDependency[];
  healthScores: Record<string, number>;
}

export async function getServiceMap(params?: { timeRange?: string }): Promise<ServiceMap> {
  void params;
  return api.get<ServiceMap>("/api/v1/observability/service-map");
}

export async function getServiceDependencies(serviceName: string): Promise<ServiceDependency[]> {
  const serviceMap = await getServiceMap();
  return serviceMap.dependencies.filter(
    (dependency) => dependency.fromService === serviceName || dependency.toService === serviceName
  );
}

// ============================================================================
// Performance Analytics
// ============================================================================

export interface PerformancePercentile {
  percentile: string;
  value: number;
  target: number;
  withinSla: boolean;
}

export interface EndpointPerformance {
  endpoint: string;
  avgLatency: number;
  statusCode?: number;
}

export interface ErrorSummary {
  errorType?: string;
  count?: number;
  statusCode?: number;
}

export interface PerformanceAnalytics {
  percentiles: PerformancePercentile[];
  slowestEndpoints: EndpointPerformance[];
  mostFrequentErrors: ErrorSummary[];
}

export async function getPerformanceAnalytics(params?: {
  periodDays?: number;
  percentile?: number;
}): Promise<PerformanceAnalytics> {
  void params;
  return api.get<PerformanceAnalytics>("/api/v1/observability/performance");
}

export async function getEndpointPerformance(
  endpoint: string,
  params?: { periodDays?: number }
): Promise<EndpointPerformance> {
  void params;
  const analytics = await getPerformanceAnalytics();
  const match = analytics.slowestEndpoints.find((item) => item.endpoint === endpoint);
  return (
    match ?? {
      endpoint,
      avgLatency: 0,
    }
  );
}

export async function getSlowEndpoints(params?: {
  threshold?: number;
  limit?: number;
}): Promise<EndpointPerformance[]> {
  void params;
  const analytics = await getPerformanceAnalytics();
  return analytics.slowestEndpoints;
}

// ============================================================================
// Aggregated Queries
// ============================================================================

export interface ObservabilityOverview {
  traces: {
    total: number;
    errorCount: number;
    avgDuration: number;
  };
  metrics: {
    seriesCount: number;
    dataPointsCount: number;
  };
  services: {
    total: number;
    healthy: number;
    degraded: number;
    down: number;
  };
  timestamp: string;
}

export async function getObservabilityOverview(params?: {
  period?: "1h" | "24h" | "7d";
}): Promise<ObservabilityOverview> {
  const [tracesResponse, metricsResponse, serviceMap] = await Promise.all([
    getTraces({
      page: 1,
      pageSize: 100,
    }),
    getMetrics(),
    getServiceMap(),
  ]);

  const totalDuration = tracesResponse.traces.reduce(
    (sum, trace) => sum + trace.duration,
    0
  );
  const errorCount = tracesResponse.traces.filter((trace) => trace.status === "error").length;

  const dataPointsCount = metricsResponse.metrics.reduce(
    (sum, series) => sum + series.dataPoints.length,
    0
  );

  const healthScores = Object.values(serviceMap.healthScores);
  const healthy = healthScores.filter((score) => score >= 90).length;
  const degraded = healthScores.filter((score) => score >= 70 && score < 90).length;
  const down = healthScores.filter((score) => score < 70).length;

  return {
    traces: {
      total: tracesResponse.total,
      errorCount,
      avgDuration: tracesResponse.traces.length ? totalDuration / tracesResponse.traces.length : 0,
    },
    metrics: {
      seriesCount: metricsResponse.metrics.length,
      dataPointsCount,
    },
    services: {
      total: serviceMap.services.length,
      healthy,
      degraded,
      down,
    },
    timestamp: new Date().toISOString(),
  };
}
