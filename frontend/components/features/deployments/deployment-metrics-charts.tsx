"use client";

import { useState } from "react";
import {
  LineChart,
  AreaChart,
  Sparkline,
  ExportableChart,
  ExportButton,
  useChartExport,
  chartColors,
} from "@dotmac/charts";
import { Card } from "@dotmac/core";
import { Activity, Cpu, HardDrive, TrendingUp, Clock, AlertTriangle, RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";

// ============================================================================
// Types
// ============================================================================

export interface MetricDataPoint {
  timestamp: string;
  value: number;
}

export interface DeploymentMetrics {
  cpu: MetricDataPoint[];
  memory: MetricDataPoint[];
  requests: MetricDataPoint[];
  latency: MetricDataPoint[];
  errors: MetricDataPoint[];
}

export interface DeploymentMetricsChartsProps {
  deploymentId: string;
  metrics?: DeploymentMetrics;
  isLoading?: boolean;
  className?: string;
}

// ============================================================================
// Metric Card Component
// ============================================================================

interface MetricCardProps {
  title: string;
  icon: React.ElementType;
  iconColor: string;
  value: string;
  unit: string;
  trend?: "up" | "down" | "neutral";
  trendValue?: string;
  sparklineData: MetricDataPoint[];
  sparklineColor?: string;
  className?: string;
}

function MetricCard({
  title,
  icon: Icon,
  iconColor,
  value,
  unit,
  trend,
  trendValue,
  sparklineData,
  sparklineColor = chartColors.primary,
  className,
}: MetricCardProps) {
  const trendColors = {
    up: "text-status-success",
    down: "text-status-error",
    neutral: "text-text-muted",
  };

  return (
    <div className={cn("p-4 rounded-lg bg-surface-overlay", className)}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Icon className={cn("w-4 h-4", iconColor)} />
          <span className="text-sm font-medium text-text-secondary">{title}</span>
        </div>
        {trend && trendValue && (
          <span className={cn("text-xs font-medium", trendColors[trend])}>
            {trend === "up" ? "↑" : trend === "down" ? "↓" : "→"} {trendValue}
          </span>
        )}
      </div>

      <div className="flex items-end justify-between">
        <div>
          <span className="text-2xl font-semibold text-text-primary tabular-nums">{value}</span>
          <span className="text-sm text-text-muted ml-1">{unit}</span>
        </div>
        <Sparkline
          data={sparklineData.map((d) => ({ value: d.value }))}
          width={80}
          height={32}
          color={sparklineColor}
          showArea
          variant="trend"
        />
      </div>
    </div>
  );
}

// ============================================================================
// Time Range Selector
// ============================================================================

type TimeRange = "1h" | "6h" | "24h" | "7d";

interface TimeRangeSelectorProps {
  value: TimeRange;
  onChange: (value: TimeRange) => void;
}

function TimeRangeSelector({ value, onChange }: TimeRangeSelectorProps) {
  const options: { value: TimeRange; label: string }[] = [
    { value: "1h", label: "1H" },
    { value: "6h", label: "6H" },
    { value: "24h", label: "24H" },
    { value: "7d", label: "7D" },
  ];

  return (
    <div className="flex items-center gap-1 p-1 bg-surface-overlay rounded-lg">
      {options.map((opt) => (
        <button
          key={opt.value}
          onClick={() => onChange(opt.value)}
          className={cn(
            "px-3 py-1 text-xs font-medium rounded transition-colors",
            value === opt.value
              ? "bg-accent text-text-inverse"
              : "text-text-muted hover:text-text-secondary"
          )}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function DeploymentMetricsCharts({
  deploymentId,
  metrics: propMetrics,
  isLoading = false,
  className,
}: DeploymentMetricsChartsProps) {
  const [timeRange, setTimeRange] = useState<TimeRange>("24h");
  const [activeChart, setActiveChart] = useState<"cpu" | "memory" | "requests">("cpu");

  const metrics = propMetrics;
  const hasMetrics =
    metrics &&
    Object.values(metrics).some((series) => Array.isArray(series) && series.length > 0);

  // Calculate current values (last data point)
  const getCurrentValue = (data: MetricDataPoint[]) => data[data.length - 1]?.value ?? 0;
  const getAvgValue = (data: MetricDataPoint[]) => {
    const sum = data.reduce((acc, d) => acc + d.value, 0);
    return data.length ? sum / data.length : 0;
  };
  const getTrend = (data: MetricDataPoint[]): "up" | "down" | "neutral" => {
    if (data.length < 2) return "neutral";
    const first = data.slice(0, data.length / 4).reduce((a, b) => a + b.value, 0) / (data.length / 4);
    const last = data.slice(-data.length / 4).reduce((a, b) => a + b.value, 0) / (data.length / 4);
    const diff = ((last - first) / first) * 100;
    if (Math.abs(diff) < 5) return "neutral";
    return diff > 0 ? "up" : "down";
  };
  const getTrendValue = (data: MetricDataPoint[]): string => {
    if (data.length < 2) return "0%";
    const first = data.slice(0, data.length / 4).reduce((a, b) => a + b.value, 0) / (data.length / 4);
    const last = data.slice(-data.length / 4).reduce((a, b) => a + b.value, 0) / (data.length / 4);
    const diff = ((last - first) / first) * 100;
    return `${Math.abs(diff).toFixed(1)}%`;
  };

  // Format data for charts
  const formatChartData = (data: MetricDataPoint[]) => {
    return data.map((d) => ({
      time: new Date(d.timestamp).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }),
      value: d.value,
    }));
  };

  const chartConfigs = {
    cpu: {
      title: "CPU Usage",
      data: metrics?.cpu ?? [],
      color: chartColors.primary,
      unit: "%",
      icon: Cpu,
    },
    memory: {
      title: "Memory Usage",
      data: metrics?.memory ?? [],
      color: chartColors.success,
      unit: "%",
      icon: Activity,
    },
    requests: {
      title: "Requests/min",
      data: metrics?.requests ?? [],
      color: chartColors.warning,
      unit: "req/min",
      icon: TrendingUp,
    },
  };

  const activeConfig = chartConfigs[activeChart];

  if (isLoading) {
    return (
      <Card className={cn("p-6", className)}>
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="w-6 h-6 text-text-muted animate-spin" />
        </div>
      </Card>
    );
  }

  if (!hasMetrics) {
    return (
      <Card className={cn("p-6", className)}>
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <AlertTriangle className="w-6 h-6 text-text-muted mb-3" />
          <p className="text-sm text-text-muted">No deployment metrics available yet.</p>
        </div>
      </Card>
    );
  }

  return (
    <div className={cn("space-y-6", className)}>
      {/* Metric Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <MetricCard
          title="CPU"
          icon={Cpu}
          iconColor="text-accent"
          value={getCurrentValue(metrics.cpu).toFixed(1)}
          unit="%"
          trend={getTrend(metrics.cpu)}
          trendValue={getTrendValue(metrics.cpu)}
          sparklineData={metrics.cpu}
          sparklineColor={chartColors.primary}
        />
        <MetricCard
          title="Memory"
          icon={Activity}
          iconColor="text-status-success"
          value={getCurrentValue(metrics.memory).toFixed(1)}
          unit="%"
          trend={getTrend(metrics.memory)}
          trendValue={getTrendValue(metrics.memory)}
          sparklineData={metrics.memory}
          sparklineColor={chartColors.success}
        />
        <MetricCard
          title="Requests"
          icon={TrendingUp}
          iconColor="text-status-warning"
          value={getCurrentValue(metrics.requests).toFixed(0)}
          unit="/min"
          trend={getTrend(metrics.requests)}
          trendValue={getTrendValue(metrics.requests)}
          sparklineData={metrics.requests}
          sparklineColor={chartColors.warning}
        />
        <MetricCard
          title="Latency"
          icon={Clock}
          iconColor="text-status-info"
          value={getAvgValue(metrics.latency).toFixed(0)}
          unit="ms"
          trend={getTrend(metrics.latency)}
          trendValue={getTrendValue(metrics.latency)}
          sparklineData={metrics.latency}
          sparklineColor={chartColors.info}
        />
        <MetricCard
          title="Error Rate"
          icon={AlertTriangle}
          iconColor="text-status-error"
          value={getCurrentValue(metrics.errors).toFixed(2)}
          unit="%"
          trend={getTrend(metrics.errors)}
          trendValue={getTrendValue(metrics.errors)}
          sparklineData={metrics.errors}
          sparklineColor={chartColors.error}
        />
      </div>

      {/* Detailed Chart */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <h3 className="text-lg font-semibold text-text-primary">Performance Metrics</h3>
            <div className="flex items-center gap-1 p-1 bg-surface-overlay rounded-lg">
              {(Object.keys(chartConfigs) as Array<keyof typeof chartConfigs>).map((key) => (
                <button
                  key={key}
                  onClick={() => setActiveChart(key)}
                  className={cn(
                    "px-3 py-1 text-xs font-medium rounded transition-colors",
                    activeChart === key
                      ? "bg-accent text-text-inverse"
                      : "text-text-muted hover:text-text-secondary"
                  )}
                >
                  {chartConfigs[key].title}
                </button>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-3">
            <TimeRangeSelector value={timeRange} onChange={setTimeRange} />
          </div>
        </div>

        <ExportableChart title={`deployment-${deploymentId}-${activeChart}`}>
          <AreaChart
            data={formatChartData(activeConfig.data)}
            xAxisKey="time"
            dataKey="value"
            height={300}
            color={activeConfig.color}
            showGrid
            showTooltip
            curved
          />
        </ExportableChart>

        <div className="flex items-center justify-between mt-4 pt-4 border-t border-border-subtle text-sm text-text-muted">
          <span>
            Average: {getAvgValue(activeConfig.data).toFixed(1)} {activeConfig.unit}
          </span>
          <span>
            Peak: {Math.max(...activeConfig.data.map((d) => d.value)).toFixed(1)} {activeConfig.unit}
          </span>
        </div>
      </Card>
    </div>
  );
}

export default DeploymentMetricsCharts;
