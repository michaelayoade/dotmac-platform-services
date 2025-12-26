"use client";

import { CheckCircle, AlertTriangle, XCircle, ExternalLink, Loader2 } from "lucide-react";

import { cn } from "@/lib/utils";
import { useSystemHealth, type SystemHealthService } from "@/lib/hooks/api";

interface HealthCheck {
  name: string;
  status: "healthy" | "degraded" | "down";
  latency?: number;
  message?: string;
  url?: string;
}

// Map API service status to display status
function mapServiceStatus(apiStatus: SystemHealthService["status"]): HealthCheck["status"] {
  const statusMap: Record<string, HealthCheck["status"]> = {
    operational: "healthy",
    degraded: "degraded",
    partial_outage: "degraded",
    major_outage: "down",
  };
  return statusMap[apiStatus] || "degraded";
}

function mapServiceToHealthCheck(service: SystemHealthService): HealthCheck {
  return {
    name: service.name,
    status: mapServiceStatus(service.status),
    latency: service.latency,
    message: service.errorRate > 0.01 ? `Error rate: ${(service.errorRate * 100).toFixed(1)}%` : undefined,
  };
}

export function SystemHealthWidget() {
  const { data: health, isLoading, error } = useSystemHealth();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-6 h-6 text-accent animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8 text-text-muted">
        <p className="text-sm">Failed to load system health</p>
      </div>
    );
  }

  const healthChecks: HealthCheck[] = (health?.services ?? []).map(mapServiceToHealthCheck);

  const statusConfig = {
    healthy: {
      icon: CheckCircle,
      color: "text-status-success",
      bgColor: "bg-status-success/15",
      label: "Healthy",
    },
    degraded: {
      icon: AlertTriangle,
      color: "text-status-warning",
      bgColor: "bg-status-warning/15",
      label: "Degraded",
    },
    down: {
      icon: XCircle,
      color: "text-status-error",
      bgColor: "bg-status-error/15",
      label: "Down",
    },
  };

  const overallStatus = healthChecks.every((h) => h.status === "healthy")
    ? "healthy"
    : healthChecks.some((h) => h.status === "down")
    ? "down"
    : "degraded";

  const OverallIcon = statusConfig[overallStatus].icon;

  return (
    <div className="space-y-4">
      {/* Overall status */}
      <div
        className={cn(
          "flex items-center gap-3 p-3 rounded-lg",
          statusConfig[overallStatus].bgColor
        )}
      >
        <OverallIcon className={cn("w-5 h-5", statusConfig[overallStatus].color)} />
        <div className="flex-1">
          <p className={cn("text-sm font-medium", statusConfig[overallStatus].color)}>
            {overallStatus === "healthy"
              ? "All Systems Operational"
              : overallStatus === "degraded"
              ? "Partial Degradation"
              : "System Outage"}
          </p>
          <p className="text-xs text-text-muted">
            {healthChecks.filter((h) => h.status === "healthy").length} of{" "}
            {healthChecks.length} services healthy
          </p>
        </div>
      </div>

      {/* Individual checks */}
      <div className="space-y-2">
        {healthChecks.map((check) => {
          const config = statusConfig[check.status];
          const Icon = config.icon;

          return (
            <div
              key={check.name}
              className="flex items-center justify-between py-2 border-b border-border-subtle last:border-0"
            >
              <div className="flex items-center gap-2">
                <Icon className={cn("w-4 h-4", config.color)} />
                <span className="text-sm text-text-primary">{check.name}</span>
              </div>
              <div className="flex items-center gap-3">
                {check.latency !== undefined && (
                  <span className="text-xs text-text-muted tabular-nums">
                    {check.latency}ms
                  </span>
                )}
                <span
                  className={cn(
                    "text-2xs font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full",
                    config.bgColor,
                    config.color
                  )}
                >
                  {config.label}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Status page link */}
      <a
        href="/status"
        className="flex items-center justify-center gap-2 text-sm text-text-muted hover:text-text-secondary py-2 border border-border rounded-lg hover:bg-surface-overlay transition-colors"
      >
        <ExternalLink className="w-4 h-4" />
        View Status Page
      </a>
    </div>
  );
}
