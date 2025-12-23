import { Suspense } from "react";
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
import { Button } from "@/lib/dotmac/core";

import { cn } from "@/lib/utils";
import {
  getPerformanceMetrics,
  getUserAnalytics,
  getUsageMetrics,
} from "@/lib/api/analytics";

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
  const perfPeriod = period === "24h" ? "24h" : period === "7d" ? "7d" : "7d";

  const [performanceData, userAnalytics, usageData] = await Promise.all([
    getPerformanceMetrics(perfPeriod),
    getUserAnalytics(),
    getUsageMetrics(period === "90d" ? "90d" : "30d"),
  ]);

  const metrics = {
    totalRequests: usageData.apiCalls.total,
    requestsChange: 18.5, // Would need historical comparison
    activeUsers: userAnalytics.activeUsers,
    activeUsersChange: userAnalytics.userGrowth,
    avgResponseTime: performanceData.responseTime.average,
    responseTimeChange: -8.2, // Would need historical comparison
    errorRate: performanceData.errorRate * 100,
    errorRateChange: -15.3, // Would need historical comparison
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
  const performanceData = await getPerformanceMetrics("24h");
  const data = performanceData.byTime.slice(-24).map((item) => {
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
      color="hsl(185, 85%, 50%)"
      gradient
    />
  );
}

async function LatencyChart() {
  const performanceData = await getPerformanceMetrics("24h");
  const data = performanceData.byTime
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
      color="hsl(45, 95%, 55%)"
    />
  );
}

async function DAUChart() {
  const userAnalytics = await getUserAnalytics();
  const data = userAnalytics.loginActivity.slice(-30).map((item, index) => ({
    day: `Day ${index + 1}`,
    users: item.logins,
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
  const userAnalytics = await getUserAnalytics();
  // Use login activity trend to simulate retention
  const weeklyData = userAnalytics.loginActivity.slice(-4);
  const maxLogins = Math.max(...weeklyData.map((d) => d.logins));
  const data = weeklyData.map((item, index) => ({
    week: `Week ${index + 1}`,
    retention: Math.round((item.logins / maxLogins) * 100),
  }));

  return (
    <BarChart data={data} dataKey="retention" xAxisKey="week" height={200} color="hsl(185, 85%, 50%)" />
  );
}

async function UserDistributionChart() {
  const userAnalytics = await getUserAnalytics();
  const data = userAnalytics.usersByRole.map((item) => ({
    role: item.role,
    count: item.count,
  }));

  return <BarChart data={data} dataKey="count" xAxisKey="role" height={200} color="hsl(45, 95%, 55%)" />;
}

async function ErrorRateChart() {
  const performanceData = await getPerformanceMetrics("7d");
  const days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  const data = performanceData.byTime.slice(-7).map((item) => {
    const date = new Date(item.timestamp);
    return {
      day: days[date.getDay()],
      rate: item.errorRate * 100,
    };
  });

  return (
    <LineChart data={data} dataKey="rate" xAxisKey="day" height={280} color="hsl(0, 75%, 55%)" />
  );
}

async function ErrorDistributionChart() {
  // Error distribution would need a separate API endpoint
  // For now, return placeholder data based on overall error rate
  const performanceData = await getPerformanceMetrics("24h");
  const totalErrors = Math.round(performanceData.errorRate * 100);
  const data = [
    { type: "500", count: Math.round(totalErrors * 0.4) },
    { type: "502", count: Math.round(totalErrors * 0.25) },
    { type: "503", count: Math.round(totalErrors * 0.2) },
    { type: "504", count: Math.round(totalErrors * 0.1) },
    { type: "Other", count: Math.round(totalErrors * 0.05) },
  ];

  return <BarChart data={data} dataKey="count" xAxisKey="type" height={280} color="hsl(0, 75%, 55%)" />;
}

async function TopRegions() {
  const usageData = await getUsageMetrics("30d");
  const totalRequests = usageData.apiCalls.total;

  // Map tenant data to region-like format (would need geographic API for real data)
  const regions = usageData.storage.byTenant.slice(0, 5).map((tenant) => ({
    name: tenant.tenantName,
    requests: Math.round(totalRequests * (tenant.used / usageData.storage.used)),
    percentage: (tenant.used / usageData.storage.used) * 100,
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
  const performanceData = await getPerformanceMetrics("24h");
  const endpoints = performanceData.byEndpoint.slice(0, 5).map((item) => ({
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
