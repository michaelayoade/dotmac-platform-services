"use client";

import { useState } from "react";
import Link from "next/link";
import {
  BarChart3,
  TrendingUp,
  Database,
  Globe,
  Users,
  Zap,
  Calendar,
  RefreshCw,
  ArrowUp,
  ArrowDown,
} from "lucide-react";
import { Button } from "@/lib/dotmac/core";
import { cn } from "@/lib/utils";
import {
  useUsageMetrics,
  useUsageRecords,
  useUsageChart,
  type UsageRecord,
} from "@/lib/hooks/api/use-billing";

type ChartPeriod = "day" | "week" | "month";
type UsageType = UsageRecord["type"] | undefined;

export default function UsageBillingPage() {
  const [chartPeriod, setChartPeriod] = useState<ChartPeriod>("week");
  const [usageTypeFilter, setUsageTypeFilter] = useState<UsageType>(undefined);

  const { data: metrics, isLoading: metricsLoading } = useUsageMetrics();
  const { data: recordsData, isLoading: recordsLoading } = useUsageRecords({
    type: usageTypeFilter,
  });
  const { data: chartData, isLoading: chartLoading } = useUsageChart(chartPeriod);

  const usageRecords = recordsData?.items || [];

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB", "TB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const formatNumber = (num: number): string => {
    return new Intl.NumberFormat("en-US", {
      notation: "compact",
      compactDisplay: "short",
    }).format(num);
  };

  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(amount / 100);
  };

  const formatDate = (dateStr: string): string => {
    return new Date(dateStr).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    });
  };

  const getUsagePercentage = (current: number, limit: number): number => {
    if (limit === 0) return 0;
    return Math.min((current / limit) * 100, 100);
  };

  const usageTypeConfig: Record<string, { icon: React.ElementType; label: string; color: string }> = {
    api_calls: { icon: Zap, label: "API Calls", color: "text-accent" },
    storage: { icon: Database, label: "Storage", color: "text-status-info" },
    bandwidth: { icon: Globe, label: "Bandwidth", color: "text-status-success" },
    users: { icon: Users, label: "Users", color: "text-status-warning" },
  };

  return (
    <div className="space-y-6">
      {/* Page Header with Breadcrumbs */}
      <div>
        <div className="flex items-center gap-2 text-sm text-text-muted mb-4">
          <Link href="/billing" className="hover:text-text-secondary">
            Billing
          </Link>
          <span>/</span>
          <span className="text-text-primary">Usage</span>
        </div>

        <div className="page-header">
          <div>
            <h1 className="page-title">Usage & Metering</h1>
            <p className="page-description">
              Monitor your resource usage and costs
            </p>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Current Usage */}
        <div className="card p-4">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
              <BarChart3 className="w-5 h-5 text-accent" />
            </div>
            <div>
              <p className="text-xs text-text-muted">Current Period</p>
              <p className="text-sm font-medium text-text-primary">API Calls</p>
            </div>
          </div>
          {metricsLoading ? (
            <div className="animate-pulse h-8 bg-surface-overlay rounded"></div>
          ) : (
            <>
              <p className="text-2xl font-bold text-text-primary tabular-nums">
                {formatNumber(metrics?.currentPeriod.apiCalls || 0)}
              </p>
              <p className="text-xs text-text-muted mt-1">
                of {formatNumber(metrics?.limits.apiCalls || 0)} limit
              </p>
              <div className="mt-2 h-1.5 bg-surface-overlay rounded-full overflow-hidden">
                <div
                  className="h-full bg-accent rounded-full transition-all"
                  style={{
                    width: `${getUsagePercentage(
                      metrics?.currentPeriod.apiCalls || 0,
                      metrics?.limits.apiCalls || 0
                    )}%`,
                  }}
                />
              </div>
            </>
          )}
        </div>

        {/* Storage */}
        <div className="card p-4">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-lg bg-status-info/15 flex items-center justify-center">
              <Database className="w-5 h-5 text-status-info" />
            </div>
            <div>
              <p className="text-xs text-text-muted">Current Period</p>
              <p className="text-sm font-medium text-text-primary">Storage</p>
            </div>
          </div>
          {metricsLoading ? (
            <div className="animate-pulse h-8 bg-surface-overlay rounded"></div>
          ) : (
            <>
              <p className="text-2xl font-bold text-text-primary tabular-nums">
                {formatBytes(metrics?.currentPeriod.storage || 0)}
              </p>
              <p className="text-xs text-text-muted mt-1">
                of {formatBytes(metrics?.limits.storage || 0)} limit
              </p>
              <div className="mt-2 h-1.5 bg-surface-overlay rounded-full overflow-hidden">
                <div
                  className="h-full bg-status-info rounded-full transition-all"
                  style={{
                    width: `${getUsagePercentage(
                      metrics?.currentPeriod.storage || 0,
                      metrics?.limits.storage || 0
                    )}%`,
                  }}
                />
              </div>
            </>
          )}
        </div>

        {/* Forecast */}
        <div className="card p-4">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-lg bg-status-warning/15 flex items-center justify-center">
              <TrendingUp className="w-5 h-5 text-status-warning" />
            </div>
            <div>
              <p className="text-xs text-text-muted">Projected</p>
              <p className="text-sm font-medium text-text-primary">End of Period</p>
            </div>
          </div>
          {metricsLoading ? (
            <div className="animate-pulse h-8 bg-surface-overlay rounded"></div>
          ) : (
            <>
              <p className="text-2xl font-bold text-text-primary tabular-nums">
                {formatNumber(metrics?.forecast.apiCalls || 0)}
              </p>
              <p className="text-xs text-text-muted mt-1">API calls forecast</p>
            </>
          )}
        </div>

        {/* Cost to Date */}
        <div className="card p-4">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-lg bg-status-success/15 flex items-center justify-center">
              <BarChart3 className="w-5 h-5 text-status-success" />
            </div>
            <div>
              <p className="text-xs text-text-muted">Cost to Date</p>
              <p className="text-sm font-medium text-text-primary">This Period</p>
            </div>
          </div>
          {metricsLoading ? (
            <div className="animate-pulse h-8 bg-surface-overlay rounded"></div>
          ) : (
            <>
              <p className="text-2xl font-bold text-text-primary tabular-nums">
                {formatCurrency(metrics?.costToDate || 0)}
              </p>
              <p className="text-xs text-text-muted mt-1">
                Forecast: {formatCurrency(metrics?.forecast.cost || 0)}
              </p>
            </>
          )}
        </div>
      </div>

      {/* Usage Chart */}
      <div className="card">
        <div className="p-4 border-b border-border flex items-center justify-between">
          <h2 className="text-sm font-semibold text-text-primary">
            Usage Over Time
          </h2>
          <div className="flex items-center gap-2">
            {(["day", "week", "month"] as ChartPeriod[]).map((period) => (
              <Button
                key={period}
                variant={chartPeriod === period ? "default" : "outline"}
                size="sm"
                onClick={() => setChartPeriod(period)}
              >
                {period === "day" ? "24h" : period === "week" ? "7d" : "30d"}
              </Button>
            ))}
          </div>
        </div>
        <div className="p-4">
          {chartLoading ? (
            <div className="h-64 flex items-center justify-center">
              <RefreshCw className="w-6 h-6 animate-spin text-text-muted" />
            </div>
          ) : chartData ? (
            <div className="h-64 flex items-end gap-1">
              {/* Simple bar chart visualization */}
              {chartData.labels.map((label, idx) => {
                const value = chartData.datasets[0]?.data[idx] || 0;
                const maxValue = Math.max(...(chartData.datasets[0]?.data || [1]));
                const height = maxValue > 0 ? (value / maxValue) * 100 : 0;
                return (
                  <div
                    key={idx}
                    className="flex-1 flex flex-col items-center group"
                  >
                    <div className="w-full flex-1 flex items-end">
                      <div
                        className="w-full bg-accent/80 rounded-t hover:bg-accent transition-colors"
                        style={{ height: `${height}%` }}
                        title={`${label}: ${formatNumber(value)}`}
                      />
                    </div>
                    <span className="text-xs text-text-muted mt-2 truncate w-full text-center">
                      {label}
                    </span>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="h-64 flex items-center justify-center text-text-muted">
              No data available
            </div>
          )}
        </div>
      </div>

      {/* Usage Records */}
      <div className="card">
        <div className="p-4 border-b border-border flex items-center justify-between">
          <h2 className="text-sm font-semibold text-text-primary">
            Usage Records
          </h2>
          <div className="flex items-center gap-2">
            <span className="text-sm text-text-muted">Type:</span>
            {[
              { value: undefined, label: "All" },
              { value: "api_calls" as UsageRecord["type"], label: "API" },
              { value: "storage" as UsageRecord["type"], label: "Storage" },
              { value: "bandwidth" as UsageRecord["type"], label: "Bandwidth" },
            ].map((option) => (
              <Button
                key={option.label}
                variant={usageTypeFilter === option.value ? "default" : "outline"}
                size="sm"
                onClick={() => setUsageTypeFilter(option.value)}
              >
                {option.label}
              </Button>
            ))}
          </div>
        </div>

        {recordsLoading ? (
          <div className="p-8 text-center text-text-muted">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2" />
            Loading records...
          </div>
        ) : usageRecords.length === 0 ? (
          <div className="p-8 text-center">
            <BarChart3 className="w-12 h-12 mx-auto text-text-muted mb-4" />
            <h3 className="text-lg font-semibold text-text-primary mb-2">
              No usage records
            </h3>
            <p className="text-text-muted">
              Usage records will appear here as you use the platform
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table" aria-label="Usage records"><caption className="sr-only">Usage records</caption>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Type</th>
                  <th>Quantity</th>
                  <th>Unit Price</th>
                  <th>Total</th>
                </tr>
              </thead>
              <tbody>
                {usageRecords.map((record: UsageRecord) => {
                  const typeConfig = usageTypeConfig[record.type];
                  const TypeIcon = typeConfig?.icon || Zap;

                  return (
                    <tr key={record.id}>
                      <td>
                        <div className="flex items-center gap-1 text-sm text-text-secondary">
                          <Calendar className="w-3 h-3" />
                          {formatDate(record.date)}
                        </div>
                      </td>
                      <td>
                        <div className="flex items-center gap-2">
                          <TypeIcon className={cn("w-4 h-4", typeConfig?.color)} />
                          <span className="text-sm text-text-primary">
                            {typeConfig?.label || record.type}
                          </span>
                        </div>
                      </td>
                      <td>
                        <span className="text-sm tabular-nums text-text-primary">
                          {record.type === "storage" || record.type === "bandwidth"
                            ? formatBytes(record.quantity)
                            : formatNumber(record.quantity)}
                        </span>
                      </td>
                      <td>
                        <span className="text-sm tabular-nums text-text-muted">
                          {formatCurrency(record.unitPrice)}
                        </span>
                      </td>
                      <td>
                        <span className="text-sm font-semibold tabular-nums text-text-primary">
                          {formatCurrency(record.total)}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Usage Limits Info */}
      <div className="card p-4">
        <div className="flex items-start gap-3">
          <TrendingUp className="w-5 h-5 text-accent flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-text-primary">
              Need more resources?
            </p>
            <p className="text-sm text-text-muted mt-1">
              Upgrade your plan to increase your usage limits and unlock additional features.
            </p>
            <Link href="/billing/subscriptions">
              <Button variant="outline" size="sm" className="mt-3">
                View Plans
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
