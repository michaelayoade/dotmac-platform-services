import { Suspense } from "react";
import {
  DashboardLayout,
  KPITile,
  KPIGrid,
  ChartGrid,
  ChartCard,
  FilterBar,
  type FilterConfig,
} from "@dotmac/dashboards";
import { LineChart, BarChart, AreaChart, PieChart } from "@dotmac/charts";
import {
  TrendingUp,
  TrendingDown,
  Users,
  Activity,
  Zap,
  Globe,
  Clock,
  ArrowUpRight,
  Download,
  Calendar,
} from "lucide-react";
import { Button } from "@dotmac/core";

import { cn } from "@/lib/utils";

export const metadata = {
  title: "Analytics",
  description: "Platform usage metrics and insights",
};

export default async function AnalyticsPage({
  searchParams,
}: {
  searchParams: { period?: string };
}) {
  const period = searchParams.period || "30d";

  // Mock metrics data
  const metrics = {
    totalRequests: 12450000,
    requestsChange: 18.5,
    activeUsers: 8923,
    activeUsersChange: 12.3,
    avgResponseTime: 145,
    responseTimeChange: -8.2,
    errorRate: 0.12,
    errorRateChange: -15.3,
  };

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Analytics</h1>
          <p className="page-description">
            Platform usage metrics, performance insights, and trends
          </p>
        </div>
        <div className="flex items-center gap-3">
          <PeriodSelector currentPeriod={period} />
          <Button variant="outline">
            <Download className="w-4 h-4 mr-2" />
            Export Report
          </Button>
        </div>
      </div>

      {/* Primary KPIs */}
      <section className="animate-fade-up">
        <KPIGrid>
          <KPITile
            title="API Requests"
            value={formatLargeNumber(metrics.totalRequests)}
            change={metrics.requestsChange}
            changeType="increase"
            icon={<Zap className="w-5 h-5" />}
            description="Total API calls this period"
          />
          <KPITile
            title="Active Users"
            value={metrics.activeUsers.toLocaleString()}
            change={metrics.activeUsersChange}
            changeType="increase"
            icon={<Users className="w-5 h-5" />}
            description="Unique users this period"
          />
          <KPITile
            title="Avg Response Time"
            value={`${metrics.avgResponseTime}ms`}
            change={metrics.responseTimeChange}
            changeType="decrease"
            icon={<Clock className="w-5 h-5" />}
            description="P95 latency"
          />
          <KPITile
            title="Error Rate"
            value={`${metrics.errorRate}%`}
            change={metrics.errorRateChange}
            changeType="decrease"
            icon={<Activity className="w-5 h-5" />}
            description="5xx errors"
          />
        </KPIGrid>
      </section>

      {/* Traffic Charts */}
      <section className="animate-fade-up delay-150">
        <ChartGrid columns={2}>
          <ChartCard
            title="API Traffic"
            description="Requests per hour over the selected period"
            action={
              <button className="text-sm text-accent hover:text-accent-hover inline-flex items-center gap-1">
                View Details <ArrowUpRight className="w-3 h-3" />
              </button>
            }
          >
            <Suspense fallback={<ChartSkeleton />}>
              <TrafficChart />
            </Suspense>
          </ChartCard>

          <ChartCard
            title="Response Time Distribution"
            description="P50, P95, and P99 latencies"
          >
            <Suspense fallback={<ChartSkeleton />}>
              <LatencyChart />
            </Suspense>
          </ChartCard>
        </ChartGrid>
      </section>

      {/* User Analytics */}
      <section className="animate-fade-up delay-300">
        <div className="section-header mb-4">
          <h2 className="section-title">User Analytics</h2>
        </div>
        <ChartGrid columns={3}>
          <ChartCard title="Daily Active Users" description="DAU over 30 days">
            <Suspense fallback={<ChartSkeleton height={200} />}>
              <DAUChart />
            </Suspense>
          </ChartCard>

          <ChartCard title="User Retention" description="30-day cohort retention">
            <Suspense fallback={<ChartSkeleton height={200} />}>
              <RetentionChart />
            </Suspense>
          </ChartCard>

          <ChartCard title="User Distribution" description="By role">
            <Suspense fallback={<ChartSkeleton height={200} />}>
              <UserDistributionChart />
            </Suspense>
          </ChartCard>
        </ChartGrid>
      </section>

      {/* Geographic & Device Analytics */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-6 animate-fade-up delay-450">
        {/* Top Regions */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="section-title">Top Regions</h3>
              <p className="text-sm text-text-muted mt-1">Traffic by geographic location</p>
            </div>
            <Globe className="w-5 h-5 text-text-muted" />
          </div>
          <Suspense fallback={<ListSkeleton />}>
            <TopRegions />
          </Suspense>
        </div>

        {/* Top Endpoints */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="section-title">Top Endpoints</h3>
              <p className="text-sm text-text-muted mt-1">Most accessed API endpoints</p>
            </div>
            <Zap className="w-5 h-5 text-text-muted" />
          </div>
          <Suspense fallback={<ListSkeleton />}>
            <TopEndpoints />
          </Suspense>
        </div>
      </section>

      {/* Error Analytics */}
      <section className="animate-fade-up delay-600">
        <ChartGrid columns={2}>
          <ChartCard title="Error Rate Trend" description="5xx errors over time">
            <Suspense fallback={<ChartSkeleton />}>
              <ErrorRateChart />
            </Suspense>
          </ChartCard>

          <ChartCard title="Error Distribution" description="By error type">
            <Suspense fallback={<ChartSkeleton />}>
              <ErrorDistributionChart />
            </Suspense>
          </ChartCard>
        </ChartGrid>
      </section>
    </div>
  );
}

// Helper Components

function PeriodSelector({ currentPeriod }: { currentPeriod: string }) {
  const periods = [
    { value: "24h", label: "24 Hours" },
    { value: "7d", label: "7 Days" },
    { value: "30d", label: "30 Days" },
    { value: "90d", label: "90 Days" },
  ];

  return (
    <div className="flex items-center gap-1 p-1 bg-surface-overlay rounded-lg">
      {periods.map((period) => (
        <a
          key={period.value}
          href={`/analytics?period=${period.value}`}
          className={cn(
            "px-3 py-1.5 rounded-md text-sm font-medium transition-colors",
            currentPeriod === period.value
              ? "bg-accent text-text-inverse"
              : "text-text-muted hover:text-text-secondary"
          )}
        >
          {period.label}
        </a>
      ))}
    </div>
  );
}

function formatLargeNumber(num: number): string {
  if (num >= 1e9) return (num / 1e9).toFixed(1) + "B";
  if (num >= 1e6) return (num / 1e6).toFixed(1) + "M";
  if (num >= 1e3) return (num / 1e3).toFixed(1) + "K";
  return num.toString();
}

// Chart Components

async function TrafficChart() {
  const data = Array.from({ length: 24 }, (_, i) => ({
    hour: `${i}:00`,
    requests: Math.floor(Math.random() * 50000) + 10000,
  }));

  return (
    <AreaChart
      data={data}
      dataKey="requests"
      xAxisKey="hour"
      height={280}
      color="hsl(185, 85%, 50%)"
      gradient
    />
  );
}

async function LatencyChart() {
  const data = [
    { time: "00:00", p50: 45, p95: 120, p99: 250 },
    { time: "04:00", p50: 42, p95: 115, p99: 230 },
    { time: "08:00", p50: 55, p95: 145, p99: 320 },
    { time: "12:00", p50: 68, p95: 180, p99: 380 },
    { time: "16:00", p50: 72, p95: 190, p99: 400 },
    { time: "20:00", p50: 58, p95: 155, p99: 340 },
  ];

  return (
    <LineChart
      data={data}
      dataKey="p95"
      xAxisKey="time"
      height={280}
      color="hsl(45, 95%, 55%)"
    />
  );
}

async function DAUChart() {
  const data = Array.from({ length: 30 }, (_, i) => ({
    day: `Day ${i + 1}`,
    users: Math.floor(Math.random() * 2000) + 6000,
  }));

  return (
    <AreaChart
      data={data}
      dataKey="users"
      xAxisKey="day"
      height={200}
      color="hsl(145, 72%, 45%)"
      gradient
    />
  );
}

async function RetentionChart() {
  const data = [
    { week: "Week 1", retention: 100 },
    { week: "Week 2", retention: 72 },
    { week: "Week 3", retention: 58 },
    { week: "Week 4", retention: 48 },
  ];

  return (
    <BarChart data={data} dataKey="retention" xAxisKey="week" height={200} color="hsl(185, 85%, 50%)" />
  );
}

async function UserDistributionChart() {
  const data = [
    { role: "Members", count: 65 },
    { role: "Admins", count: 20 },
    { role: "Viewers", count: 15 },
  ];

  return <BarChart data={data} dataKey="count" xAxisKey="role" height={200} color="hsl(45, 95%, 55%)" />;
}

async function ErrorRateChart() {
  const data = Array.from({ length: 7 }, (_, i) => ({
    day: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][i],
    rate: Math.random() * 0.3 + 0.05,
  }));

  return (
    <LineChart data={data} dataKey="rate" xAxisKey="day" height={280} color="hsl(0, 75%, 55%)" />
  );
}

async function ErrorDistributionChart() {
  const data = [
    { type: "500", count: 45 },
    { type: "502", count: 23 },
    { type: "503", count: 18 },
    { type: "504", count: 12 },
    { type: "Other", count: 8 },
  ];

  return <BarChart data={data} dataKey="count" xAxisKey="type" height={280} color="hsl(0, 75%, 55%)" />;
}

async function TopRegions() {
  const regions = [
    { name: "United States", requests: 4250000, percentage: 34.1 },
    { name: "Germany", requests: 1850000, percentage: 14.9 },
    { name: "United Kingdom", requests: 1420000, percentage: 11.4 },
    { name: "Japan", requests: 980000, percentage: 7.9 },
    { name: "France", requests: 720000, percentage: 5.8 },
  ];

  return (
    <div className="space-y-3">
      {regions.map((region, i) => (
        <div key={region.name} className="flex items-center gap-3">
          <span className="text-sm text-text-muted w-4">{i + 1}</span>
          <div className="flex-1">
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm font-medium text-text-primary">{region.name}</span>
              <span className="text-sm text-text-secondary tabular-nums">
                {(region.requests / 1e6).toFixed(1)}M
              </span>
            </div>
            <div className="h-1.5 bg-surface-overlay rounded-full overflow-hidden">
              <div
                className="h-full bg-accent rounded-full transition-all"
                style={{ width: `${region.percentage}%` }}
              />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

async function TopEndpoints() {
  const endpoints = [
    { path: "/api/v1/users", requests: 2100000, avgTime: 45 },
    { path: "/api/v1/auth/token", requests: 1850000, avgTime: 120 },
    { path: "/api/v1/tenants", requests: 980000, avgTime: 65 },
    { path: "/api/v1/billing/invoices", requests: 520000, avgTime: 180 },
    { path: "/api/v1/deployments", requests: 340000, avgTime: 250 },
  ];

  return (
    <div className="space-y-3">
      {endpoints.map((endpoint, i) => (
        <div
          key={endpoint.path}
          className="flex items-center justify-between py-2 border-b border-border-subtle last:border-0"
        >
          <div className="flex items-center gap-3">
            <span className="text-sm text-text-muted w-4">{i + 1}</span>
            <code className="text-sm text-accent">{endpoint.path}</code>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-text-secondary tabular-nums">
              {(endpoint.requests / 1e6).toFixed(1)}M
            </span>
            <span className="text-xs text-text-muted tabular-nums w-16 text-right">
              {endpoint.avgTime}ms avg
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}

// Skeletons

function ChartSkeleton({ height = 280 }: { height?: number }) {
  return (
    <div className="flex items-center justify-center" style={{ height }}>
      <div className="w-full h-full bg-surface-overlay rounded animate-pulse" />
    </div>
  );
}

function ListSkeleton() {
  return (
    <div className="space-y-3">
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className="flex items-center gap-3">
          <div className="w-4 h-4 skeleton" />
          <div className="flex-1 space-y-2">
            <div className="h-4 w-3/4 skeleton" />
            <div className="h-1.5 w-full skeleton rounded-full" />
          </div>
        </div>
      ))}
    </div>
  );
}
