import { Suspense } from "react";
import {
  DashboardLayout,
  DashboardSection,
  KPITile,
  KPIGrid,
  ChartGrid,
  ChartCard,
} from "@dotmac/dashboards";
import { LineChart, BarChart, AreaChart } from "@dotmac/charts";
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
import { RecentActivityFeed } from "@/components/features/dashboard/recent-activity";
import { SystemHealthWidget } from "@/components/features/dashboard/system-health";
import { QuickActions } from "@/components/features/dashboard/quick-actions";

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
            trend={metrics.revenue.trend}
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
  // In production, this would fetch from API
  const data = [
    { month: "Jan", revenue: 45000 },
    { month: "Feb", revenue: 52000 },
    { month: "Mar", revenue: 48000 },
    { month: "Apr", revenue: 61000 },
    { month: "May", revenue: 55000 },
    { month: "Jun", revenue: 67000 },
    { month: "Jul", revenue: 72000 },
    { month: "Aug", revenue: 78000 },
    { month: "Sep", revenue: 82000 },
    { month: "Oct", revenue: 89000 },
    { month: "Nov", revenue: 94000 },
    { month: "Dec", revenue: 102000 },
  ];

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
  const data = [
    { week: "W1", users: 120 },
    { week: "W2", users: 145 },
    { week: "W3", users: 132 },
    { week: "W4", users: 168 },
    { week: "W5", users: 189 },
    { week: "W6", users: 203 },
    { week: "W7", users: 215 },
    { week: "W8", users: 248 },
  ];

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
  const data = [
    { name: "Enterprise", value: 35, color: "hsl(185, 85%, 50%)" },
    { name: "Professional", value: 45, color: "hsl(185, 85%, 65%)" },
    { name: "Starter", value: 15, color: "hsl(185, 50%, 45%)" },
    { name: "Trial", value: 5, color: "hsl(220, 15%, 40%)" },
  ];

  return <BarChart data={data} dataKey="value" xAxisKey="name" height={200} />;
}

async function APITrafficChart() {
  // Generate 24 hours of data
  const data = Array.from({ length: 24 }, (_, i) => ({
    hour: `${i}:00`,
    requests: Math.floor(Math.random() * 5000) + 1000,
  }));

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
  const data = [
    { day: "Mon", rate: 0.8 },
    { day: "Tue", rate: 1.2 },
    { day: "Wed", rate: 0.5 },
    { day: "Thu", rate: 0.9 },
    { day: "Fri", rate: 1.5 },
    { day: "Sat", rate: 0.3 },
    { day: "Sun", rate: 0.4 },
  ];

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
