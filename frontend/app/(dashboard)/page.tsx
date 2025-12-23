import { Suspense } from "react";
import {
  DashboardLayout,
  DashboardSection,
  KPITile,
  KPIGrid,
  ChartGrid,
  ChartCard,
} from "@/lib/dotmac/dashboards";
import { LineChart, BarChart, AreaChart } from "@/lib/dotmac/charts";
import {
  TrendingUp,
  TrendingDown,
  Users,
  Building2,
  CreditCard,
  Server,
  Activity,
  ArrowUpRight,
} from "lucide-react";

import { getDashboardMetrics } from "@/lib/api/dashboard";
import {
  getRevenueData,
  getUserAnalytics,
  getTenantAnalytics,
  getPerformanceMetrics,
} from "@/lib/api/analytics";
import { RecentActivityFeed } from "@/components/features/dashboard/recent-activity";
import { SystemHealthWidget } from "@/components/features/dashboard/system-health";
import { QuickActions } from "@/components/features/dashboard/quick-actions";

export const dynamic = "force-dynamic";

export const metadata = {
  title: "Dashboard",
};

export default async function DashboardPage() {
  const metrics = await getDashboardMetrics();

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-description">
            Overview of your platform performance and key metrics
          </p>
        </div>
        <QuickActions />
      </div>

      {/* KPI Grid */}
      <section className="animate-fade-up">
        <KPIGrid>
          <KPITile
            title="Total Users"
            value={metrics.users.total.toLocaleString()}
            change={metrics.users.change}
            changeType={metrics.users.change >= 0 ? "increase" : "decrease"}
            icon={<Users className="w-5 h-5" />}
            description={`${metrics.users.active} active this month`}
          />
          <KPITile
            title="Active Tenants"
            value={metrics.tenants.total.toLocaleString()}
            change={metrics.tenants.change}
            changeType={metrics.tenants.change >= 0 ? "increase" : "decrease"}
            icon={<Building2 className="w-5 h-5" />}
            description={`${metrics.tenants.trial} in trial`}
          />
          <KPITile
            title="Monthly Revenue"
            value={`$${(metrics.revenue.current / 100).toLocaleString()}`}
            change={metrics.revenue.change}
            changeType={metrics.revenue.change >= 0 ? "increase" : "decrease"}
            icon={<CreditCard className="w-5 h-5" />}
            description="vs. last month"
          />
          <KPITile
            title="Active Deployments"
            value={metrics.deployments.active.toLocaleString()}
            change={metrics.deployments.change}
            changeType={metrics.deployments.change >= 0 ? "increase" : "decrease"}
            icon={<Server className="w-5 h-5" />}
            description={`${metrics.deployments.pending} pending`}
          />
        </KPIGrid>
      </section>

      {/* Charts Row */}
      <section className="animate-fade-up delay-150">
        <ChartGrid columns={2}>
          <ChartCard
            title="Revenue Trend"
            description="Monthly recurring revenue over time"
            action={
              <button className="text-sm text-accent hover:text-accent-hover inline-flex items-center gap-1">
                View Details <ArrowUpRight className="w-3 h-3" />
              </button>
            }
          >
            <Suspense fallback={<ChartSkeleton />}>
              <RevenueChart />
            </Suspense>
          </ChartCard>

          <ChartCard
            title="User Growth"
            description="New user registrations by week"
            action={
              <button className="text-sm text-accent hover:text-accent-hover inline-flex items-center gap-1">
                View Details <ArrowUpRight className="w-3 h-3" />
              </button>
            }
          >
            <Suspense fallback={<ChartSkeleton />}>
              <UserGrowthChart />
            </Suspense>
          </ChartCard>
        </ChartGrid>
      </section>

      {/* Lower Grid - Activity & System Health */}
      <section className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-fade-up delay-300">
        {/* Recent Activity */}
        <div className="lg:col-span-2">
          <div className="card p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="section-title">Recent Activity</h3>
              <span className="live-indicator text-xs text-text-muted">Live</span>
            </div>
            <Suspense fallback={<ActivitySkeleton />}>
              <RecentActivityFeed />
            </Suspense>
          </div>
        </div>

        {/* System Health */}
        <div>
          <div className="card p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="section-title">System Health</h3>
              <Activity className="w-4 h-4 text-status-success animate-pulse" />
            </div>
            <Suspense fallback={<HealthSkeleton />}>
              <SystemHealthWidget />
            </Suspense>
          </div>
        </div>
      </section>

      {/* Tenant Distribution Chart */}
      <section className="animate-fade-up delay-450">
        <ChartGrid columns={3}>
          <ChartCard title="Tenant Distribution" description="By subscription plan">
            <Suspense fallback={<ChartSkeleton />}>
              <TenantDistributionChart />
            </Suspense>
          </ChartCard>

          <ChartCard title="API Traffic" description="Requests per hour (24h)">
            <Suspense fallback={<ChartSkeleton />}>
              <APITrafficChart />
            </Suspense>
          </ChartCard>

          <ChartCard title="Error Rate" description="Last 7 days">
            <Suspense fallback={<ChartSkeleton />}>
              <ErrorRateChart />
            </Suspense>
          </ChartCard>
        </ChartGrid>
      </section>
    </div>
  );
}

// Async chart components that fetch their own data

async function RevenueChart() {
  const revenueData = await getRevenueData("12m");
  const data = revenueData.map((item) => ({
    month: item.month,
    revenue: item.revenue / 100, // Convert cents to dollars
  }));

  return (
    <AreaChart
      data={data}
      dataKey="revenue"
      xAxisKey="month"
      height={280}
      color="hsl(185, 85%, 50%)"
      gradient
    />
  );
}

async function UserGrowthChart() {
  const userAnalytics = await getUserAnalytics();
  // Use login activity as a proxy for user growth
  const data = userAnalytics.loginActivity.slice(-8).map((item, index) => ({
    week: `W${index + 1}`,
    users: item.logins,
  }));

  return (
    <BarChart
      data={data}
      dataKey="users"
      xAxisKey="week"
      height={280}
      color="hsl(45, 95%, 55%)"
    />
  );
}

async function TenantDistributionChart() {
  const tenantAnalytics = await getTenantAnalytics();
  const data = tenantAnalytics.tenantsByPlan.map((item) => ({
    name: item.plan,
    value: item.count,
  }));

  return <BarChart data={data} dataKey="value" xAxisKey="name" height={200} />;
}

async function APITrafficChart() {
  const performanceData = await getPerformanceMetrics("24h");
  const data = performanceData.byTime.slice(-24).map((item) => {
    const date = new Date(item.timestamp);
    return {
      hour: `${date.getHours()}:00`,
      requests: item.requests,
    };
  });

  return (
    <LineChart
      data={data}
      dataKey="requests"
      xAxisKey="hour"
      height={200}
      color="hsl(145, 72%, 45%)"
    />
  );
}

async function ErrorRateChart() {
  const performanceData = await getPerformanceMetrics("7d");
  const days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  const data = performanceData.byTime.slice(-7).map((item) => {
    const date = new Date(item.timestamp);
    return {
      day: days[date.getDay()],
      rate: item.errorRate * 100, // Convert to percentage
    };
  });

  return (
    <LineChart
      data={data}
      dataKey="rate"
      xAxisKey="day"
      height={200}
      color="hsl(0, 75%, 55%)"
    />
  );
}

// Skeleton components

function ChartSkeleton() {
  return (
    <div className="h-[280px] flex items-center justify-center">
      <div className="w-full h-full bg-surface-overlay rounded animate-pulse" />
    </div>
  );
}

function ActivitySkeleton() {
  return (
    <div className="space-y-4">
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-full skeleton" />
          <div className="flex-1 space-y-2">
            <div className="h-4 w-3/4 skeleton" />
            <div className="h-3 w-1/2 skeleton" />
          </div>
        </div>
      ))}
    </div>
  );
}

function HealthSkeleton() {
  return (
    <div className="space-y-3">
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className="flex items-center justify-between">
          <div className="h-4 w-24 skeleton" />
          <div className="h-4 w-16 skeleton" />
        </div>
      ))}
    </div>
  );
}
