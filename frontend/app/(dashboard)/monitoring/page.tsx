"use client";

import { useMemo } from "react";
import Link from "next/link";
import {
  Activity,
  AlertTriangle,
  FileText,
  GitBranch,
  Clock,
  TrendingUp,
  TrendingDown,
  Server,
  Database,
  RefreshCcw,
  ExternalLink,
  CheckCircle2,
  XCircle,
  ArrowRight,
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { Button, Card } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import { useLogStats, useLogServices } from "@/lib/hooks/api/use-monitoring";
import { useAlertHistory, useAlertStats } from "@/lib/hooks/api/use-alerts";
import { useServiceMap, usePerformanceAnalytics } from "@/lib/hooks/api/use-observability";
import type { AlertEvent } from "@/lib/api/alerts";
import type { LogLevel } from "@/lib/api/monitoring";

export default function MonitoringPage() {
  const logStatsRange = useMemo(() => {
    const endTime = new Date();
    const startTime = new Date(endTime.getTime() - 24 * 60 * 60 * 1000);
    return { startTime: startTime.toISOString(), endTime: endTime.toISOString() };
  }, []);
  const { data: logStats, refetch: refetchLogStats } = useLogStats(logStatsRange);
  const { data: services } = useLogServices();
  const { data: alertStats } = useAlertStats({ periodDays: 1 });
  const { data: alertHistory } = useAlertHistory({ page: 1, pageSize: 5 });
  const { data: serviceMap } = useServiceMap();
  const { data: performance } = usePerformanceAnalytics({ periodDays: 1 });

  const recentAlerts: AlertEvent[] = alertHistory?.events ?? [];
  const levelCounts = logStats?.byLevel ?? ({} as Record<LogLevel, number>);
  const totalLogs = logStats?.total ?? 0;
  const errorCount = (levelCounts.ERROR ?? 0) + (levelCounts.CRITICAL ?? 0);
  const warningCount = levelCounts.WARNING ?? 0;
  const infoCount = levelCounts.INFO ?? 0;
  const debugCount = levelCounts.DEBUG ?? 0;
  const timeRangeSeconds = logStats?.timeRange
    ? (new Date(logStats.timeRange.end).getTime() - new Date(logStats.timeRange.start).getTime()) /
      1000
    : undefined;
  const throughput =
    timeRangeSeconds && timeRangeSeconds > 0 ? totalLogs / timeRangeSeconds : undefined;
  const errorRate = totalLogs > 0 ? (errorCount / totalLogs) * 100 : undefined;
  const serviceNames = services ?? serviceMap?.services ?? [];
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

  const getServiceStatus = (serviceName: string) => {
    const healthScore = serviceMap?.healthScores?.[serviceName];
    if (healthScore === undefined) {
      return { label: "unknown", color: "bg-surface-overlay text-text-muted" };
    }
    if (healthScore >= 90) {
      return { label: "healthy", color: "bg-status-success/15 text-status-success" };
    }
    if (healthScore >= 70) {
      return { label: "degraded", color: "bg-status-warning/15 text-status-warning" };
    }
    return { label: "down", color: "bg-status-error/15 text-status-error" };
  };

  return (
    <div className="space-y-8 animate-fade-up">
      <PageHeader
        title="Monitoring"
        description="System health, logs, alerts, and distributed tracing"
        actions={
          <Button variant="ghost" onClick={() => refetchLogStats()}>
            <RefreshCcw className="w-4 h-4" />
          </Button>
        }
      />

      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-status-info/15 flex items-center justify-center">
              <FileText className="w-5 h-5 text-status-info" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Logs (24h)</p>
              <p className="text-2xl font-semibold text-text-primary">
                {totalLogs.toLocaleString()}
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
              <p className="text-sm text-text-muted">Errors (24h)</p>
              <p className="text-2xl font-semibold text-status-error">
                {errorCount.toLocaleString()}
              </p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-status-warning/15 flex items-center justify-center">
              <AlertTriangle className="w-5 h-5 text-status-warning" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Active Alerts</p>
              <p className="text-2xl font-semibold text-status-warning">
                {alertStats?.firing || 0}
              </p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-status-success/15 flex items-center justify-center">
              <Activity className="w-5 h-5 text-status-success" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Services</p>
              <p className="text-2xl font-semibold text-text-primary">
                {serviceNames.length}
              </p>
            </div>
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Quick Links & Services */}
        <div className="space-y-6">
          {/* Quick Links */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-text-primary mb-4">Quick Links</h3>
            <div className="space-y-2">
              <Link href="/monitoring/logs">
                <Button variant="outline" className="w-full justify-between">
                  <span className="flex items-center gap-2">
                    <FileText className="w-4 h-4" />
                    Logs Explorer
                  </span>
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </Link>
              <Link href="/monitoring/alerts">
                <Button variant="outline" className="w-full justify-between">
                  <span className="flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4" />
                    Alert Management
                  </span>
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </Link>
              <Link href="/monitoring/traces">
                <Button variant="outline" className="w-full justify-between">
                  <span className="flex items-center gap-2">
                    <GitBranch className="w-4 h-4" />
                    Distributed Tracing
                  </span>
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </Link>
            </div>
          </Card>

          {/* Services */}
          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-text-primary">Services</h3>
              <span className="text-sm text-text-muted">{serviceNames.length} active</span>
            </div>
            {serviceNames.length > 0 ? (
              <div className="space-y-3">
                {serviceNames.slice(0, 6).map((serviceName) => {
                  const status = getServiceStatus(serviceName);
                  return (
                    <div
                      key={serviceName}
                      className="flex items-center justify-between p-3 bg-surface-overlay rounded-lg"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-accent-subtle flex items-center justify-center">
                          <Server className="w-4 h-4 text-accent" />
                        </div>
                        <span className="font-medium text-text-primary">{serviceName}</span>
                      </div>
                      <span
                        className={cn(
                          "px-2 py-0.5 rounded-full text-xs font-medium",
                          status.color
                        )}
                      >
                        {status.label}
                      </span>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-text-muted text-center py-4">No services detected</p>
            )}
          </Card>
        </div>

        {/* Middle Column - Recent Alerts */}
        <div className="space-y-6">
          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-text-primary">Recent Alerts</h3>
              <Link href="/monitoring/alerts">
                <Button variant="ghost" size="sm">
                  View All
                  <ExternalLink className="w-3.5 h-3.5 ml-1" />
                </Button>
              </Link>
            </div>
            {recentAlerts.length > 0 ? (
              <div className="space-y-3">
                {recentAlerts.map((alert) => (
                  <div
                    key={alert.id}
                    className={cn(
                      "p-4 rounded-lg border",
                      alert.status === "firing"
                        ? "border-status-error/30 bg-status-error/5"
                        : "border-border-subtle bg-surface-overlay"
                    )}
                  >
                    <div className="flex items-start gap-3">
                      <AlertTriangle
                        className={cn(
                          "w-5 h-5 mt-0.5",
                          alert.status === "firing" ? "text-status-error" : "text-status-success"
                        )}
                      />
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-text-primary truncate">
                          {alert.alertName}
                        </p>
                        <p className="text-sm text-text-muted mt-1">{alert.message}</p>
                        <div className="flex items-center gap-4 mt-2 text-xs text-text-muted">
                          <span className={cn(
                            "px-1.5 py-0.5 rounded",
                            alert.severity === "critical"
                              ? "bg-status-error/15 text-status-error"
                              : alert.severity === "warning"
                              ? "bg-status-warning/15 text-status-warning"
                              : "bg-status-info/15 text-status-info"
                          )}>
                            {alert.severity}
                          </span>
                          <span>
                            {formatDistanceToNow(new Date(alert.createdAt), { addSuffix: true })}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <CheckCircle2 className="w-12 h-12 text-status-success mx-auto mb-3" />
                <p className="text-text-primary font-medium">All clear</p>
                <p className="text-sm text-text-muted">No active alerts</p>
              </div>
            )}
          </Card>
        </div>

        {/* Right Column - Performance & Stats */}
        <div className="space-y-6">
          {/* Performance Overview */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-text-primary mb-4">Performance (24h)</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-surface-overlay rounded-lg">
                <div className="flex items-center gap-3">
                  <Clock className="w-5 h-5 text-text-muted" />
                  <span className="text-text-secondary">Avg Response</span>
                </div>
                <span className="font-mono font-medium text-text-primary">
                  {p50Latency !== undefined ? `${p50Latency.toFixed(0)}ms` : "N/A"}
                </span>
              </div>
              <div className="flex items-center justify-between p-3 bg-surface-overlay rounded-lg">
                <div className="flex items-center gap-3">
                  <TrendingUp className="w-5 h-5 text-text-muted" />
                  <span className="text-text-secondary">P99 Latency</span>
                </div>
                <span className="font-mono font-medium text-text-primary">
                  {p99Latency !== undefined ? `${p99Latency.toFixed(0)}ms` : "N/A"}
                </span>
              </div>
              <div className="flex items-center justify-between p-3 bg-surface-overlay rounded-lg">
                <div className="flex items-center gap-3">
                  <Activity className="w-5 h-5 text-text-muted" />
                  <span className="text-text-secondary">Throughput</span>
                </div>
                <span className="font-mono font-medium text-text-primary">
                  {throughput !== undefined ? `${throughput.toFixed(1)} req/s` : "N/A"}
                </span>
              </div>
              <div className="flex items-center justify-between p-3 bg-surface-overlay rounded-lg">
                <div className="flex items-center gap-3">
                  <XCircle className="w-5 h-5 text-text-muted" />
                  <span className="text-text-secondary">Error Rate</span>
                </div>
                <span
                  className={cn(
                    "font-mono font-medium",
                    errorRate !== undefined && errorRate > 5
                      ? "text-status-error"
                      : errorRate !== undefined && errorRate > 1
                      ? "text-status-warning"
                      : "text-status-success"
                  )}
                >
                  {errorRate !== undefined ? `${errorRate.toFixed(2)}%` : "N/A"}
                </span>
              </div>
            </div>
          </Card>

          {/* Log Level Distribution */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-text-primary mb-4">Log Levels (24h)</h3>
            <div className="space-y-3">
              {[
                { level: "error", count: errorCount, color: "bg-status-error" },
                { level: "warning", count: warningCount, color: "bg-status-warning" },
                { level: "info", count: infoCount, color: "bg-status-info" },
                { level: "debug", count: debugCount, color: "bg-text-muted" },
              ].map((item) => {
                const total = totalLogs || 1;
                const percentage = (item.count / total) * 100;

                return (
                  <div key={item.level} className="space-y-1">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-text-secondary capitalize">{item.level}</span>
                      <span className="text-text-muted">{item.count.toLocaleString()}</span>
                    </div>
                    <div className="h-2 bg-surface-overlay rounded-full overflow-hidden">
                      <div
                        className={cn("h-full rounded-full transition-all", item.color)}
                        style={{ width: `${Math.min(percentage, 100)}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
