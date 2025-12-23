"use client";

import { useState } from "react";
import Link from "next/link";
import {
  GitBranch,
  Search,
  Filter,
  RefreshCcw,
  Clock,
  Server,
  AlertCircle,
  CheckCircle2,
  XCircle,
  ChevronRight,
  ChevronDown,
  ExternalLink,
  Activity,
  Zap,
} from "lucide-react";
import { format, formatDistanceToNow, formatDuration, intervalToDuration } from "date-fns";
import { Button, Card, Input } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import type { TraceStatus as ApiTraceStatus } from "@/lib/api/observability";
import {
  useTraces,
  useServiceMap,
  usePerformanceAnalytics,
  useSlowEndpoints,
} from "@/lib/hooks/api/use-observability";

type TraceStatusFilter = "all" | "ok" | "unset" | ApiTraceStatus;

const statusConfig: Record<
  ApiTraceStatus,
  { label: string; color: string; icon: React.ElementType }
> = {
  success: { label: "OK", color: "bg-status-success/15 text-status-success", icon: CheckCircle2 },
  error: { label: "Error", color: "bg-status-error/15 text-status-error", icon: XCircle },
  warning: { label: "Warning", color: "bg-status-warning/15 text-status-warning", icon: AlertCircle },
};

export default function TracesPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [serviceFilter, setServiceFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<TraceStatusFilter>("all");
  const [page, setPage] = useState(1);
  const [expandedTrace, setExpandedTrace] = useState<string | null>(null);

  const { data: tracesData, isLoading, refetch } = useTraces({
    page,
    pageSize: 20,
    service: serviceFilter !== "all" ? serviceFilter : undefined,
    status: statusFilter !== "all" ? statusFilter : undefined,
  });
  const { data: serviceMap } = useServiceMap();
  const { data: performance } = usePerformanceAnalytics({ periodDays: 1 });
  const { data: slowEndpoints } = useSlowEndpoints({ limit: 5 });

  const traces = tracesData?.traces || [];
  const errorRate =
    traces.length > 0
      ? (traces.filter((trace) => trace.status === "error").length / traces.length) * 100
      : undefined;
  const filteredTraces = traces.filter((trace) => {
    if (!searchQuery) {
      return true;
    }
    const needle = searchQuery.toLowerCase();
    return (
      trace.traceId.toLowerCase().includes(needle) ||
      trace.operation.toLowerCase().includes(needle) ||
      trace.service.toLowerCase().includes(needle)
    );
  });
  const totalPages = tracesData
    ? Math.max(1, Math.ceil(tracesData.total / Math.max(tracesData.pageSize, 1)))
    : 1;
  const services = serviceMap?.services || [];
  const getPercentileValue = (target: string) => {
    const normalizedTarget = target.toLowerCase();
    const percentile = performance?.percentiles.find((item) => {
      const normalized = item.percentile.toLowerCase();
      return (
        normalized === normalizedTarget ||
        normalized === normalizedTarget.replace(/^p/, "")
      );
    });
    return percentile?.value;
  };
  const p50Latency = getPercentileValue("p50");
  const p99Latency = getPercentileValue("p99");
  const getServiceRequestCount = (serviceName: string) => {
    const dependencies = serviceMap?.dependencies ?? [];
    return dependencies.reduce((total, dependency) => {
      if (dependency.fromService === serviceName || dependency.toService === serviceName) {
        return total + dependency.requestCount;
      }
      return total;
    }, 0);
  };

  if (isLoading) {
    return <TracesSkeleton />;
  }

  return (
    <div className="space-y-6 animate-fade-up">
      <PageHeader
        title="Distributed Tracing"
        description="Track requests across services and analyze performance"
        breadcrumbs={[
          { label: "Monitoring", href: "/monitoring" },
          { label: "Traces" },
        ]}
        actions={
          <Button variant="ghost" onClick={() => refetch()}>
            <RefreshCcw className="w-4 h-4" />
          </Button>
        }
      />

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
              <GitBranch className="w-5 h-5 text-accent" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Traces (24h)</p>
              <p className="text-2xl font-semibold text-text-primary">
                {tracesData?.total.toLocaleString() || 0}
              </p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-status-success/15 flex items-center justify-center">
              <Clock className="w-5 h-5 text-status-success" />
            </div>
            <div>
              <p className="text-sm text-text-muted">P50 Latency</p>
              <p className="text-2xl font-semibold text-text-primary">
                {p50Latency !== undefined ? `${p50Latency.toFixed(0)}ms` : "N/A"}
              </p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-status-warning/15 flex items-center justify-center">
              <Activity className="w-5 h-5 text-status-warning" />
            </div>
            <div>
              <p className="text-sm text-text-muted">P99 Latency</p>
              <p className="text-2xl font-semibold text-text-primary">
                {p99Latency !== undefined ? `${p99Latency.toFixed(0)}ms` : "N/A"}
              </p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-status-error/15 flex items-center justify-center">
              <XCircle className="w-5 h-5 text-status-error" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Error Rate</p>
              <p className="text-2xl font-semibold text-status-error">
                {errorRate !== undefined ? `${errorRate.toFixed(2)}%` : "N/A"}
              </p>
            </div>
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Main Content - Traces */}
        <div className="lg:col-span-3 space-y-4">
          {/* Filters */}
          <Card className="p-4">
            <div className="flex items-center gap-4 flex-wrap">
              <div className="relative flex-1 min-w-[200px] max-w-md">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                <Input
                  value={searchQuery}
                  onChange={(e) => {
                    setSearchQuery(e.target.value);
                    setPage(1);
                  }}
                  placeholder="Search by trace ID or operation..."
                  className="pl-10"
                />
              </div>

              <div className="flex items-center gap-2">
                <Server className="w-4 h-4 text-text-muted" />
                <select
                  value={serviceFilter}
                  onChange={(e) => {
                    setServiceFilter(e.target.value);
                    setPage(1);
                  }}
                  className="px-3 py-2 bg-surface-primary border border-border-subtle rounded-md text-sm"
                >
                  <option value="all">All Services</option>
                  {services.map((service) => (
                    <option key={service} value={service}>
                      {service}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex items-center gap-2">
                <Filter className="w-4 h-4 text-text-muted" />
                <select
                  value={statusFilter}
                  onChange={(e) => {
                    setStatusFilter(e.target.value as TraceStatusFilter);
                    setPage(1);
                  }}
                  className="px-3 py-2 bg-surface-primary border border-border-subtle rounded-md text-sm"
                >
                  <option value="all">All Status</option>
                  <option value="ok">OK</option>
                  <option value="error">Error</option>
                  <option value="warning">Warning</option>
                </select>
              </div>
            </div>
          </Card>

          {/* Traces List */}
          {filteredTraces.length === 0 ? (
            <Card className="p-12 text-center">
              <GitBranch className="w-12 h-12 text-text-muted mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-text-primary mb-2">No traces found</h3>
              <p className="text-text-muted">
                {searchQuery || serviceFilter !== "all" || statusFilter !== "all"
                  ? "Try adjusting your filters"
                  : "Traces will appear here as requests are processed"}
              </p>
            </Card>
          ) : (
            <Card className="overflow-hidden">
              <div className="divide-y divide-border-subtle">
                {filteredTraces.map((trace) => {
                  const status = statusConfig[trace.status];
                  const StatusIcon = status.icon;
                  const isExpanded = expandedTrace === trace.traceId;
                  const spanDetails = trace.spanDetails ?? [];
                  const spanCount = trace.spans ?? spanDetails.length;

                  return (
                    <div
                      key={trace.traceId}
                      className={cn(
                        "p-4 hover:bg-surface-overlay/50 transition-colors",
                        trace.status === "error" && "border-l-2 border-l-status-error"
                      )}
                    >
                      <div
                        className="flex items-start gap-4 cursor-pointer"
                        onClick={() => setExpandedTrace(isExpanded ? null : trace.traceId)}
                      >
                        <button className="mt-1">
                          {isExpanded ? (
                            <ChevronDown className="w-4 h-4 text-text-muted" />
                          ) : (
                            <ChevronRight className="w-4 h-4 text-text-muted" />
                          )}
                        </button>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-mono text-sm text-accent">
                              {trace.traceId.slice(0, 16)}
                            </span>
                            <span className={cn("px-2 py-0.5 rounded text-xs font-medium", status.color)}>
                              <StatusIcon className="w-3 h-3 inline mr-1" />
                              {status.label}
                            </span>
                          </div>
                          <p className="text-text-primary font-medium truncate">
                            {trace.operation || "Unknown operation"}
                          </p>
                          <div className="flex items-center gap-4 mt-1 text-xs text-text-muted">
                            <span className="flex items-center gap-1">
                              <Server className="w-3 h-3" />
                              {trace.service}
                            </span>
                            <span className="flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {trace.duration ? `${trace.duration.toFixed(0)}ms` : "N/A"}
                            </span>
                            <span>
                              {formatDistanceToNow(new Date(trace.timestamp), { addSuffix: true })}
                            </span>
                            <span>{spanCount} spans</span>
                          </div>
                        </div>
                      </div>

                      {isExpanded && spanDetails.length > 0 && (
                        <div className="mt-4 ml-8">
                          {/* Timeline visualization */}
                          <div className="relative mb-4">
                            <div className="h-2 bg-surface-overlay rounded-full overflow-hidden">
                              <div
                                className="h-full bg-accent rounded-full"
                                style={{ width: "100%" }}
                              />
                            </div>
                            <div className="flex justify-between text-xs text-text-muted mt-1">
                              <span>0ms</span>
                              <span>{trace.duration?.toFixed(0) || 0}ms</span>
                            </div>
                          </div>

                          {/* Spans list */}
                          <div className="space-y-2">
                            {spanDetails.slice(0, 5).map((span, index) => {
                              const spanDuration = span.duration || 0;
                              const totalDuration = trace.duration || 1;
                              const widthPercentage = Math.min((spanDuration / totalDuration) * 100, 100);

                              return (
                                <div
                                  key={span.spanId}
                                  className="flex items-center gap-4 p-3 bg-surface-overlay rounded-lg"
                                >
                                  <div className="w-6 h-6 rounded-full bg-accent-subtle flex items-center justify-center text-xs text-accent font-medium">
                                    {index + 1}
                                  </div>
                                  <div className="flex-1 min-w-0">
                                    <p className="text-sm font-medium text-text-primary truncate">
                                      {span.name}
                                    </p>
                                    <div className="flex items-center gap-2 mt-1">
                                      <div className="flex-1 h-1.5 bg-surface-primary rounded-full overflow-hidden">
                                        <div
                                          className={cn(
                                            "h-full rounded-full",
                                            trace.status === "error" ? "bg-status-error" : "bg-accent"
                                          )}
                                          style={{ width: `${widthPercentage}%` }}
                                        />
                                      </div>
                                      <span className="text-xs text-text-muted font-mono shrink-0">
                                        {spanDuration.toFixed(0)}ms
                                      </span>
                                    </div>
                                  </div>
                                </div>
                              );
                            })}
                            {spanDetails.length > 5 && (
                              <p className="text-sm text-text-muted text-center py-2">
                                +{spanDetails.length - 5} more spans
                              </p>
                            )}
                          </div>

                          <div className="mt-4 pt-4 border-t border-border-subtle">
                            <Link href={`/monitoring/traces/${trace.traceId}`}>
                              <Button variant="outline" size="sm">
                                View Full Trace
                                <ExternalLink className="w-3.5 h-3.5 ml-1" />
                              </Button>
                            </Link>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {totalPages > 1 && (
                <div className="flex items-center justify-between px-4 py-3 border-t border-border-subtle">
                  <p className="text-sm text-text-muted">
                    Page {page} of {totalPages}
                  </p>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                      disabled={page === 1}
                    >
                      Previous
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                      disabled={page === totalPages}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </Card>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Service Map */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-text-primary mb-4">Service Map</h3>
            {services.length > 0 ? (
              <div className="space-y-3">
                {services.slice(0, 6).map((service) => (
                  <div
                    key={service}
                    className="flex items-center justify-between p-3 bg-surface-overlay rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-accent-subtle flex items-center justify-center">
                        <Server className="w-4 h-4 text-accent" />
                      </div>
                      <span className="font-medium text-text-primary text-sm">{service}</span>
                    </div>
                    <span className="text-xs text-text-muted">
                      {getServiceRequestCount(service).toLocaleString()} req
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-text-muted text-sm text-center py-4">No services detected</p>
            )}
          </Card>

          {/* Slow Endpoints */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-text-primary mb-4">Slowest Endpoints</h3>
            {slowEndpoints && slowEndpoints.length > 0 ? (
              <div className="space-y-3">
                {slowEndpoints.map((endpoint, index) => (
                  <div key={endpoint.endpoint} className="p-3 bg-surface-overlay rounded-lg">
                    <div className="flex items-center gap-2 mb-1">
                      <span
                        className={cn(
                          "w-5 h-5 rounded-full flex items-center justify-center text-xs font-medium",
                          index === 0
                            ? "bg-status-error/15 text-status-error"
                            : index === 1
                            ? "bg-status-warning/15 text-status-warning"
                            : "bg-surface-primary text-text-muted"
                        )}
                      >
                        {index + 1}
                      </span>
                      <span className="text-sm text-text-primary truncate flex-1">
                        {endpoint.endpoint}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 ml-7 text-xs text-text-muted">
                      <span>Avg: {endpoint.avgLatency.toFixed(0)}ms</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-text-muted text-sm text-center py-4">No data available</p>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}

function TracesSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="h-8 w-48 bg-surface-overlay rounded" />
      <div className="grid grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="card p-4 h-20" />
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-3 space-y-4">
          <div className="card p-4 h-16" />
          <div className="card">
            <div className="divide-y divide-border-subtle">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="p-4 h-20" />
              ))}
            </div>
          </div>
        </div>
        <div className="space-y-6">
          <div className="card p-6 h-64" />
          <div className="card p-6 h-48" />
        </div>
      </div>
    </div>
  );
}
