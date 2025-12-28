import { Suspense } from "react";
import Link from "next/link";
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Users,
  ArrowUpRight,
  ArrowDownRight,
  RefreshCcw,
  Calendar,
  PieChart,
  BarChart3,
} from "lucide-react";
import {
  KPIGrid,
  KPITile,
  ChartGrid,
  ChartCard,
} from "@/lib/dotmac/dashboards";
import { LineChart, BarChart } from "@/lib/dotmac/charts";
import { Button } from "@/lib/dotmac/core";

import { getRevenueData, getRevenueBreakdown } from "@/lib/api/analytics";
import { getBillingMetrics } from "@/lib/api/billing";
import { fetchOrNull } from "@/lib/api/fetch-or-null";
import { cn } from "@/lib/utils";

export const dynamic = "force-dynamic";

export const metadata = {
  title: "Billing Analytics",
  description: "Revenue analytics and financial insights",
};

interface PageProps {
  searchParams: {
    period?: string;
  };
}

function EmptyChart({ height = 260, message = "No data available" }: { height?: number; message?: string }) {
  return (
    <div className="flex items-center justify-center text-sm text-text-muted" style={{ height }}>
      {message}
    </div>
  );
}

const periodOptions = [
  { value: "6m", label: "6 Months" },
  { value: "12m", label: "12 Months" },
  { value: "ytd", label: "Year to Date" },
  { value: "all", label: "All Time" },
];

export default async function BillingAnalyticsPage({ searchParams }: PageProps) {
  const period = (searchParams.period as "6m" | "12m" | "ytd" | "all") || "12m";
  const months = period === "6m" ? 6 : period === "12m" ? 12 : 12;

  const [metrics, breakdown, revenueData] = await Promise.all([
    fetchOrNull(getBillingMetrics),
    fetchOrNull(getRevenueBreakdown),
    fetchOrNull(() => getRevenueData(period)),
  ]);

  // Format data for charts
  const revenueTrendData = (revenueData ?? []).map((item) => ({
    month: item.month,
    revenue: item.revenue / 100,
  }));

  const planData = (breakdown?.byPlan ?? []).map((item) => ({
    plan: item.plan,
    revenue: item.revenue / 100,
    percentage: item.percentage,
  }));

  const regionData = (breakdown?.byRegion ?? []).map((item) => ({
    region: item.region,
    revenue: item.revenue / 100,
    percentage: item.percentage,
  }));

  // Calculate additional metrics
  const netRevenueRetention =
    breakdown && breakdown.netRevenue > 0
      ? (
          ((breakdown.netRevenue + breakdown.expansion - breakdown.churn) /
            breakdown.netRevenue) *
          100
        ).toFixed(1)
      : null;

  return (
    <div className="space-y-8">
      {/* Page Header with Breadcrumbs */}
      <div>
        <div className="flex items-center gap-2 text-sm text-text-muted mb-4">
          <Link href="/billing" className="hover:text-text-secondary">
            Billing
          </Link>
          <span>/</span>
          <span className="text-text-primary">Analytics</span>
        </div>

        <div className="page-header">
          <div>
            <h1 className="page-title">Billing Analytics</h1>
            <p className="page-description">
              Revenue metrics, growth trends, and financial insights
            </p>
          </div>
          <div className="flex items-center gap-3">
            <PeriodSelector currentPeriod={period} />
          </div>
        </div>
      </div>

      {/* Primary KPIs */}
      <section className="animate-fade-up">
        <KPIGrid>
          <KPITile
            title="Monthly Recurring Revenue"
            value={metrics ? `$${(metrics.mrr / 100).toLocaleString()}` : "—"}
            change={metrics?.mrrChange}
            changeType={
              metrics?.mrrChange !== undefined
                ? metrics.mrrChange >= 0
                  ? "increase"
                  : "decrease"
                : undefined
            }
            icon={<DollarSign className="w-5 h-5" />}
            description="Current MRR"
          />
          <KPITile
            title="Annual Recurring Revenue"
            value={metrics ? `$${(metrics.arr / 100).toLocaleString()}` : "—"}
            change={metrics?.arrChange}
            changeType={
              metrics?.arrChange !== undefined
                ? metrics.arrChange >= 0
                  ? "increase"
                  : "decrease"
                : undefined
            }
            icon={<TrendingUp className="w-5 h-5" />}
            description="Annualized revenue"
          />
          <KPITile
            title="Net Revenue Retention"
            value={netRevenueRetention === null ? "—" : `${netRevenueRetention}%`}
            change={breakdown?.mrrGrowth}
            changeType={
              breakdown?.mrrGrowth !== undefined
                ? breakdown.mrrGrowth >= 0
                  ? "increase"
                  : "decrease"
                : undefined
            }
            icon={<RefreshCcw className="w-5 h-5" />}
            description="Including expansion"
          />
          <KPITile
            title="Active Subscriptions"
            value={metrics ? metrics.activeSubscriptions.toLocaleString() : "—"}
            change={metrics?.subscriptionChange}
            changeType={
              metrics?.subscriptionChange !== undefined
                ? metrics.subscriptionChange >= 0
                  ? "increase"
                  : "decrease"
                : undefined
            }
            icon={<Users className="w-5 h-5" />}
            description="Paying tenants"
          />
        </KPIGrid>
      </section>

      {/* Revenue Trend Chart */}
      <section className="animate-fade-up delay-150">
        <ChartCard
          title="Revenue Trend"
          description={`Revenue over the past ${period === "6m" ? "6 months" : period === "12m" ? "12 months" : period === "ytd" ? "year" : "all time"}`}
        >
          <Suspense fallback={<ChartSkeleton />}>
            {revenueTrendData.length === 0 ? (
              <EmptyChart height={320} />
            ) : (
              <LineChart
                data={revenueTrendData}
                dataKey="revenue"
                xAxisKey="month"
                height={320}
                color="hsl(var(--color-accent))"
              />
            )}
          </Suspense>
        </ChartCard>
      </section>

      {/* Revenue Breakdown Charts */}
      <section className="animate-fade-up delay-300">
        <ChartGrid columns={2}>
          <ChartCard
            title="Revenue by Plan"
            description="Distribution across subscription plans"
          >
            <Suspense fallback={<ChartSkeleton />}>
              {planData.length === 0 ? (
                <EmptyChart height={280} />
              ) : (
                <BarChart
                  data={planData}
                  dataKey="revenue"
                  xAxisKey="plan"
                  height={280}
                  color="hsl(var(--color-highlight))"
                />
              )}
            </Suspense>
          </ChartCard>

          <ChartCard
            title="Revenue by Region"
            description="Geographic distribution"
          >
            <Suspense fallback={<ChartSkeleton />}>
              {regionData.length === 0 ? (
                <EmptyChart height={280} />
              ) : (
                <BarChart
                  data={regionData}
                  dataKey="revenue"
                  xAxisKey="region"
                  height={280}
                  color="hsl(var(--color-accent))"
                />
              )}
            </Suspense>
          </ChartCard>
        </ChartGrid>
      </section>

      {/* Secondary Metrics */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-fade-up delay-450">
        {/* Churn & Expansion */}
        <div className="card p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-lg bg-status-error/15 flex items-center justify-center">
              <TrendingDown className="w-5 h-5 text-status-error" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Churned Revenue</p>
              <p className="text-2xl font-semibold text-text-primary tabular-nums">
                {breakdown ? `$${(breakdown.churn / 100).toLocaleString()}` : "—"}
              </p>
            </div>
          </div>
          <p className="text-sm text-text-muted">
            {metrics ? `${metrics.churnedThisMonth} subscriptions churned this month` : "No churn data available."}
          </p>
        </div>

        <div className="card p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-lg bg-status-success/15 flex items-center justify-center">
              <TrendingUp className="w-5 h-5 text-status-success" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Expansion Revenue</p>
              <p className="text-2xl font-semibold text-text-primary tabular-nums">
                {breakdown ? `$${(breakdown.expansion / 100).toLocaleString()}` : "—"}
              </p>
            </div>
          </div>
          <p className="text-sm text-text-muted">
            {metrics ? `${metrics.upgradesThisMonth} upgrades this month` : "No upgrade data available."}
          </p>
        </div>

        <div className="card p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
              <PieChart className="w-5 h-5 text-accent" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Collection Rate</p>
              <p className="text-2xl font-semibold text-text-primary tabular-nums">
                {metrics ? `${metrics.collectionRate}%` : "—"}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-1 text-sm">
            {metrics && metrics.collectionRateChange !== undefined ? (
              metrics.collectionRateChange >= 0 ? (
              <>
                <ArrowUpRight className="w-4 h-4 text-status-success" />
                <span className="text-status-success">{metrics.collectionRateChange}%</span>
              </>
            ) : (
              <>
                <ArrowDownRight className="w-4 h-4 text-status-error" />
                <span className="text-status-error">{Math.abs(metrics.collectionRateChange)}%</span>
              </>
              )
            ) : (
              <span className="text-text-muted">No comparison data</span>
            )}
            <span className="text-text-muted">vs last month</span>
          </div>
        </div>
      </section>

      {/* Plan Distribution Table */}
      <section className="animate-fade-up delay-600">
        <div className="card">
          <div className="flex items-center justify-between p-6 border-b border-border">
            <div>
              <h3 className="section-title">Revenue by Plan</h3>
              <p className="text-sm text-text-muted mt-1">
                Detailed breakdown of revenue per subscription plan
              </p>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="data-table" aria-label="Revenue by plan"><caption className="sr-only">Revenue by plan</caption>
              <thead>
                <tr>
                  <th>Plan</th>
                  <th className="text-right">Revenue</th>
                  <th className="text-right">% of Total</th>
                  <th>Distribution</th>
                </tr>
              </thead>
              <tbody>
                {breakdown && breakdown.byPlan.length > 0 ? (
                  breakdown.byPlan.map((plan, index) => (
                    <tr key={plan.plan}>
                      <td>
                        <div className="flex items-center gap-2">
                          <span
                            className={cn(
                              "w-3 h-3 rounded-full",
                              index === 0 ? "bg-accent" : index === 1 ? "bg-highlight" : "bg-status-info"
                            )}
                          />
                          <span className="font-medium text-text-primary">{plan.plan}</span>
                        </div>
                      </td>
                      <td className="text-right font-semibold tabular-nums">
                        ${(plan.revenue / 100).toLocaleString()}
                      </td>
                      <td className="text-right text-text-secondary tabular-nums">
                        {plan.percentage.toFixed(1)}%
                      </td>
                      <td>
                        <div className="w-full bg-surface-overlay rounded-full h-2">
                          <div
                            className={cn(
                              "h-2 rounded-full",
                              index === 0 ? "bg-accent" : index === 1 ? "bg-highlight" : "bg-status-info"
                            )}
                            style={{ width: `${plan.percentage}%` }}
                          />
                        </div>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={4} className="text-center text-text-muted py-8">
                      No revenue data available
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Top Tenants would go here */}
    </div>
  );
}

function PeriodSelector({ currentPeriod }: { currentPeriod: string }) {
  return (
    <div className="flex items-center gap-1 bg-surface-overlay rounded-lg p-1">
      {periodOptions.map((option) => (
        <Link
          key={option.value}
          href={`/billing/analytics?period=${option.value}`}
          className={cn(
            "px-3 py-1.5 text-sm font-medium rounded-md transition-colors",
            currentPeriod === option.value
              ? "bg-surface text-text-primary shadow-sm"
              : "text-text-muted hover:text-text-secondary"
          )}
        >
          {option.label}
        </Link>
      ))}
    </div>
  );
}

function ChartSkeleton() {
  return (
    <div className="h-[280px] flex items-center justify-center">
      <div className="w-full h-full bg-surface-overlay rounded animate-pulse" />
    </div>
  );
}
