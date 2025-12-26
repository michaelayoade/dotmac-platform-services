import { Suspense } from "react";
import Link from "next/link";
import {
  DashboardLayout,
  KPITile,
  KPIGrid,
  ChartGrid,
  ChartCard,
  FilterBar,
  type FilterConfig,
} from "@/lib/dotmac/dashboards";
import { LineChart, BarChart, AreaChart, PieChart } from "@/lib/dotmac/charts";
import {
  Users,
  Activity,
  Zap,
  Globe,
  Clock,
  ArrowUpRight,
  Download,
} from "lucide-react";
import { Button } from "@/lib/dotmac/core";

import { cn } from "@/lib/utils";
import { fetchOrNull } from "@/lib/api/fetch-or-null";
import {
  getPerformanceMetrics,
  getUserAnalytics,
  getUsageMetrics,
} from "@/lib/api/analytics";

export const metadata = {
  title: "Analytics",
  description: "Platform usage metrics and insights",
};

function EmptyChart({ height = 200, message = "No data available" }: { height?: number; message?: string }) {
  return (
    <div
      className="flex items-center justify-center text-sm text-text-muted"
      style={{ height }}
    >
      {message}
    </div>
  );
}

export default async function AnalyticsPage({
  searchParams,
}: {
  searchParams: { period?: string };
}) {
  const period = searchParams.period || "30d";
  const perfPeriod = period === "24h" ? "24h" : period === "7d" ? "7d" : "7d";

  const [performanceData, userAnalytics, usageData] = await Promise.all([
    fetchOrNull(() => getPerformanceMetrics(perfPeriod)),
    fetchOrNull(getUserAnalytics),
    fetchOrNull(() => getUsageMetrics(period === "90d" ? "90d" : "30d")),
  ]);

  const metrics = {
    totalRequests: usageData?.apiCalls?.total ?? null,
    activeUsers: userAnalytics?.activeUsers ?? null,
    avgResponseTime: performanceData?.responseTime?.average ?? null,
    errorRate: performanceData?.errorRate !== undefined ? performanceData.errorRate * 100 : null,
  };

  return (
    <div className="space-y-6">
      {/* Breadcrumbs */}
      <nav aria-label="Breadcrumb" className="flex items-center gap-2 text-sm text-text-muted">
        <Link href="/" className="hover:text-text-secondary">
          Dashboard
        </Link>
        <span aria-hidden="true">/</span>
        <span className="text-text-primary">Analytics</span>
      </nav>

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
            value={
              metrics.totalRequests === null
                ? "—"
                : formatLargeNumber(metrics.totalRequests)
            }
            icon={<Zap className="w-5 h-5" />}
          />
          <KPITile
            title="Active Users"
            value={metrics.activeUsers === null ? "—" : metrics.activeUsers.toLocaleString()}
            icon={<Users className="w-5 h-5" />}
          />
          <KPITile
            title="Avg Response Time"
            value={metrics.avgResponseTime === null ? "—" : `${metrics.avgResponseTime}ms`}
            icon={<Clock className="w-5 h-5" />}
          />
          <KPITile
            title="Error Rate"
            value={metrics.errorRate === null ? "—" : `${metrics.errorRate.toFixed(2)}%`}
            icon={<Activity className="w-5 h-5" />}
          />
        </KPIGrid>
      </section>

      {/* Traffic Charts */}
      <section className="animate-fade-up delay-150">
        <ChartGrid columns={2}>
          <ChartCard
            title="API Traffic"
            subtitle="Requests per hour over the selected period"
            actions={
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
            subtitle="P50, P95, and P99 latencies"
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
          <ChartCard title="Daily Active Users" subtitle="DAU over 30 days">
            <Suspense fallback={<ChartSkeleton height={200} />}>
              <DAUChart />
            </Suspense>
          </ChartCard>

          <ChartCard title="User Retention" subtitle="30-day cohort retention">
            <Suspense fallback={<ChartSkeleton height={200} />}>
              <RetentionChart />
            </Suspense>
          </ChartCard>

          <ChartCard title="User Distribution" subtitle="By role">
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
          <ChartCard title="Error Rate Trend" subtitle="5xx errors over time">
            <Suspense fallback={<ChartSkeleton />}>
              <ErrorRateChart />
            </Suspense>
          </ChartCard>

          <ChartCard title="Error Distribution" subtitle="By error type">
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

function formatLargeNumber(num: number | null): string {
  if (num === null) return "—";
  if (num >= 1e9) return (num / 1e9).toFixed(1) + "B";
  if (num >= 1e6) return (num / 1e6).toFixed(1) + "M";
  if (num >= 1e3) return (num / 1e3).toFixed(1) + "K";
  return num.toString();
}

// Chart Components

async function TrafficChart() {
  const performanceData = await fetchOrNull(() => getPerformanceMetrics("24h"));
  const series = performanceData?.byTime ?? [];
  if (series.length === 0) {
    return <EmptyChart height={280} />;
  }
  const data = series.slice(-24).map((item) => {
    const date = new Date(item.timestamp);
    return {
      hour: `${date.getHours()}:00`,
      requests: item.requests,
    };
  });

  return (
    <AreaChart
      data={data}
      dataKey="requests"
      xAxisKey="hour"
      height={280}
      color="hsl(var(--color-accent))"
      gradient
    />
  );
}

async function LatencyChart() {
  const performanceData = await fetchOrNull(() => getPerformanceMetrics("24h"));
  const series = performanceData?.byTime ?? [];
  if (series.length === 0) {
    return <EmptyChart height={280} />;
  }
  const data = series
    .filter((_, i) => i % 4 === 0) // Sample every 4 hours
    .slice(-6)
    .map((item) => {
      const date = new Date(item.timestamp);
      return {
        time: `${date.getHours().toString().padStart(2, "0")}:00`,
        p95: item.responseTime,
      };
    });

  return (
    <LineChart
      data={data}
      dataKey="p95"
      xAxisKey="time"
      height={280}
      color="hsl(var(--color-highlight))"
    />
  );
}

async function DAUChart() {
  const userAnalytics = await fetchOrNull(getUserAnalytics);
  const activity = userAnalytics?.loginActivity ?? [];
  if (activity.length === 0) {
    return <EmptyChart height={200} />;
  }
  const data = activity.slice(-30).map((item, index) => ({
    day: `Day ${index + 1}`,
    users: item.logins,
  }));

  return (
    <AreaChart
      data={data}
      dataKey="users"
      xAxisKey="day"
      height={200}
      color="hsl(var(--color-status-success))"
      gradient
    />
  );
}

async function RetentionChart() {
  const userAnalytics = await fetchOrNull(getUserAnalytics);
  const weeklyData = (userAnalytics?.loginActivity ?? []).slice(-4);
  if (weeklyData.length === 0) {
    return <EmptyChart height={200} />;
  }
  const maxLogins = Math.max(...weeklyData.map((d) => d.logins || 0), 1);
  const data = weeklyData.map((item, index) => ({
    week: `Week ${index + 1}`,
    retention: Math.round((item.logins / maxLogins) * 100),
  }));

  return (
    <BarChart data={data} dataKey="retention" xAxisKey="week" height={200} color="hsl(var(--color-accent))" />
  );
}

async function UserDistributionChart() {
  const userAnalytics = await fetchOrNull(getUserAnalytics);
  const roles = userAnalytics?.usersByRole ?? [];
  if (roles.length === 0) {
    return <EmptyChart height={200} />;
  }
  const data = roles.map((item) => ({
    role: item.role,
    count: item.count,
  }));

  return <BarChart data={data} dataKey="count" xAxisKey="role" height={200} color="hsl(var(--color-highlight))" />;
}

async function ErrorRateChart() {
  const performanceData = await fetchOrNull(() => getPerformanceMetrics("7d"));
  const series = performanceData?.byTime ?? [];
  if (series.length === 0) {
    return <EmptyChart height={280} />;
  }
  const days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  const data = series.slice(-7).map((item) => {
    const date = new Date(item.timestamp);
    return {
      day: days[date.getDay()],
      rate: item.errorRate * 100,
    };
  });

  return (
    <LineChart data={data} dataKey="rate" xAxisKey="day" height={280} color="hsl(var(--color-status-error))" />
  );
}

async function ErrorDistributionChart() {
  return <EmptyChart height={280} message="Error distribution data not available." />;
}

async function TopRegions() {
  const usageData = await fetchOrNull(() => getUsageMetrics("30d"));
  const totalRequests = usageData?.apiCalls?.total ?? 0;
  const totalStorage = usageData?.storage?.used ?? 0;
  const byTenant = usageData?.storage?.byTenant ?? [];
  if (byTenant.length === 0 || totalStorage === 0) {
    return <EmptyChart height={140} message="No region data available." />;
  }

  const regions = byTenant.slice(0, 5).map((tenant) => ({
    name: tenant.tenantName,
    requests: Math.round(totalRequests * (tenant.used / totalStorage)),
    percentage: (tenant.used / totalStorage) * 100,
  }));

  return (
    <div className="space-y-3">
      {regions.map((region, i) => (
        <div key={region.name} className="flex items-center gap-3">
          <span className="text-sm text-text-muted w-4">{i + 1}</span>
          <div className="flex-1">
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm font-medium text-text-primary">{region.name}</span>
              <span className="text-sm text-text-secondary tabular-nums">
                {region.requests >= 1e6
                  ? (region.requests / 1e6).toFixed(1) + "M"
                  : (region.requests / 1e3).toFixed(0) + "K"}
              </span>
            </div>
            <div className="h-1.5 bg-surface-overlay rounded-full overflow-hidden">
              <div
                className="h-full bg-accent rounded-full transition-all"
                style={{ width: `${Math.min(region.percentage, 100)}%` }}
              />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

async function TopEndpoints() {
  const performanceData = await fetchOrNull(() => getPerformanceMetrics("24h"));
  const endpointSeries = performanceData?.byEndpoint ?? [];
  if (endpointSeries.length === 0) {
    return <EmptyChart height={160} message="No endpoint data available." />;
  }
  const endpoints = endpointSeries.slice(0, 5).map((item) => ({
    path: item.endpoint,
    requests: item.requestCount,
    avgTime: Math.round(item.averageTime),
  }));

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
              {endpoint.requests >= 1e6
                ? (endpoint.requests / 1e6).toFixed(1) + "M"
                : (endpoint.requests / 1e3).toFixed(1) + "K"}
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
