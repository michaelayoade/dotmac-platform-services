import { Suspense, type ElementType } from "react";
import Link from "next/link";
import {
  Plus,
  Download,
  CreditCard,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Receipt,
  Calendar,
  ArrowUpRight,
  CheckCircle,
  Clock,
  AlertCircle,
  XCircle,
} from "lucide-react";
import {
  DashboardSection,
  KPITile,
  KPIGrid,
  ChartGrid,
  ChartCard,
  FilterBar,
  type FilterConfig as DashboardFilterConfig,
} from "@/lib/dotmac/dashboards";
import { LineChart, BarChart } from "@/lib/dotmac/charts";
import { Button } from "@/lib/dotmac/core";
import { DataTable, type ColumnDef } from "@/lib/dotmac/data-table";

import { getBillingDashboard, getBillingMetrics, getRecentInvoices, type Invoice } from "@/lib/api/billing";
import { getRevenueData, getRevenueBreakdown } from "@/lib/api/analytics";
import { fetchOrNull } from "@/lib/api/fetch-or-null";
import { cn } from "@/lib/utils";
import { DashboardAlerts, DashboardRecentActivity } from "@/components/features/dashboard";

export const dynamic = "force-dynamic";

export const metadata = {
  title: "Billing",
  description: "Revenue, invoices, and payment management",
};

function EmptyChart({ height = 280, message = "No data available" }: { height?: number; message?: string }) {
  return (
    <div className="flex items-center justify-center text-sm text-text-muted" style={{ height }}>
      {message}
    </div>
  );
}

export default async function BillingPage() {
  // Use the consolidated dashboard endpoint for main data
  const [dashboardData, metrics, recentInvoicesResponse] = await Promise.all([
    fetchOrNull(() => getBillingDashboard({ periodMonths: 12 })),
    fetchOrNull(getBillingMetrics),
    fetchOrNull(() => getRecentInvoices()),
  ]);
  const recentInvoices = recentInvoicesResponse ?? [];
  const alerts = dashboardData?.alerts ?? [];
  const recentActivity = dashboardData?.recentActivity ?? [];

  return (
    <div className="space-y-6">
      {/* Breadcrumbs */}
      <nav aria-label="Breadcrumb" className="flex items-center gap-2 text-sm text-text-muted">
        <Link href="/" className="hover:text-text-secondary">
          Dashboard
        </Link>
        <span aria-hidden="true">/</span>
        <span className="text-text-primary">Billing</span>
      </nav>

      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Billing</h1>
          <p className="page-description">
            Revenue analytics, invoices, and payment management
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline">
            <Download className="w-4 h-4 mr-2" />
            Export Report
          </Button>
          <Link href="/billing/invoices/new">
            <Button className="shadow-glow-sm hover:shadow-glow">
              <Plus className="w-4 h-4 mr-2" />
              Create Invoice
            </Button>
          </Link>
        </div>
      </div>

      {/* Dashboard Alerts */}
      {alerts.length > 0 && (
        <DashboardAlerts alerts={alerts} className="animate-fade-up" />
      )}

      {/* Revenue KPIs */}
      <section className="animate-fade-up">
        <KPIGrid>
          <KPITile
            title="Monthly Revenue"
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
            changeLabel="Monthly Recurring Revenue"
          />
          <KPITile
            title="Annual Revenue"
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
            changeLabel="Annual Recurring Revenue"
          />
          <KPITile
            title="Outstanding"
            value={metrics ? `$${(metrics.outstanding / 100).toLocaleString()}` : "—"}
            icon={<Clock className="w-5 h-5" />}
            changeLabel={
              metrics ? `${metrics.overdueCount} invoices overdue` : undefined
            }
            className={metrics && metrics.overdueCount > 0 ? "border-status-warning/30" : ""}
          />
          <KPITile
            title="Collections"
            value={metrics ? `${metrics.collectionRate}%` : "—"}
            change={metrics?.collectionRateChange}
            changeType={
              metrics?.collectionRateChange !== undefined
                ? metrics.collectionRateChange >= 0
                  ? "increase"
                  : "decrease"
                : undefined
            }
            icon={<Receipt className="w-5 h-5" />}
            changeLabel="30-day collection rate"
          />
        </KPIGrid>
      </section>

      {/* Revenue Charts */}
      <section className="animate-fade-up delay-150">
        <ChartGrid columns={2}>
          <ChartCard
            title="Revenue Trend"
            subtitle="Monthly revenue over the past 12 months"
            actions={
              <Link
                href="/billing/analytics"
                className="text-sm text-accent hover:text-accent-hover inline-flex items-center gap-1"
              >
                View Analytics <ArrowUpRight className="w-3 h-3" />
              </Link>
            }
          >
            <Suspense fallback={<ChartSkeleton />}>
              <RevenueChart />
            </Suspense>
          </ChartCard>

          <ChartCard
            title="Payment Methods"
            subtitle="Revenue by payment method"
          >
            <Suspense fallback={<ChartSkeleton />}>
              <PaymentMethodChart />
            </Suspense>
          </ChartCard>
        </ChartGrid>
      </section>

      {/* Invoices Section */}
      <section className="animate-fade-up delay-300">
        <div className="card">
          <div className="flex items-center justify-between p-6 border-b border-border">
            <div>
              <h3 className="section-title">Recent Invoices</h3>
              <p className="text-sm text-text-muted mt-1">
                {recentInvoices.length} invoices this month
              </p>
            </div>
            <Link
              href="/billing/invoices"
              className="text-sm text-accent hover:text-accent-hover font-medium"
            >
              View All →
            </Link>
          </div>

          <div className="overflow-x-auto">
            <InvoicesTable invoices={recentInvoices} />
          </div>
        </div>
      </section>

      {/* Subscription Stats & Recent Activity */}
      <section className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-fade-up delay-450">
        <div className="lg:col-span-2 grid grid-cols-1 md:grid-cols-3 gap-6">
          <SubscriptionCard
            title="Active Subscriptions"
            count={metrics?.activeSubscriptions ?? null}
            change={metrics?.subscriptionChange}
            breakdown={[]}
          />

          <SubscriptionCard
            title="Churned This Month"
            count={metrics?.churnedThisMonth ?? null}
            breakdown={[]}
          />

          <SubscriptionCard
            title="Upgrades This Month"
            count={metrics?.upgradesThisMonth ?? null}
            breakdown={[]}
          />
        </div>

        {/* Recent Activity Panel */}
        {recentActivity.length > 0 && (
          <DashboardRecentActivity
            activities={recentActivity}
            title="Recent Billing Activity"
            maxItems={5}
          />
        )}
      </section>
    </div>
  );
}

// Invoices Table Component
function InvoicesTable({ invoices }: { invoices: Invoice[] }) {
  const statusConfig: Record<
    Invoice["status"],
    { icon: ElementType; class: string; label: string }
  > = {
    paid: { icon: CheckCircle, class: "status-badge--success", label: "Paid" },
    pending: { icon: Clock, class: "status-badge--warning", label: "Pending" },
    overdue: { icon: AlertCircle, class: "status-badge--error", label: "Overdue" },
    draft: { icon: Receipt, class: "bg-surface-overlay text-text-muted", label: "Draft" },
    cancelled: { icon: XCircle, class: "bg-surface-overlay text-text-muted", label: "Cancelled" },
  };

  return (
    <table className="data-table" aria-label="Recent invoices"><caption className="sr-only">Recent invoices</caption>
      <thead>
        <tr>
          <th scope="col">Invoice</th>
          <th scope="col">Tenant</th>
          <th scope="col">Amount</th>
          <th scope="col">Status</th>
          <th scope="col">Due Date</th>
          <th scope="col"><span className="sr-only">Actions</span></th>
        </tr>
      </thead>
      <tbody>
        {invoices.map((invoice) => {
          const config = statusConfig[invoice.status];
          const Icon = config.icon;
          return (
            <tr key={invoice.id} className="group">
              <td>
                <Link
                  href={`/billing/invoices/${invoice.id}`}
                  className="font-mono text-sm text-accent hover:text-accent-hover"
                >
                  {invoice.number}
                </Link>
              </td>
              <td>
                <div>
                  <p className="text-sm font-medium text-text-primary">
                    {invoice.customer.name}
                  </p>
                  <p className="text-xs text-text-muted">{invoice.customer.email}</p>
                </div>
              </td>
              <td>
                <span className="text-sm font-semibold tabular-nums">
                  ${(invoice.amount / 100).toLocaleString()}
                </span>
              </td>
              <td>
                <span className={cn("status-badge", config.class)}>
                  <Icon className="w-3 h-3" />
                  {config.label}
                </span>
              </td>
              <td>
                <span className="text-sm text-text-secondary tabular-nums">
                  {new Date(invoice.dueDate).toLocaleDateString()}
                </span>
              </td>
              <td>
                <Link
                  href={`/billing/invoices/${invoice.id}`}
                  className="text-sm text-text-muted hover:text-text-secondary opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  View →
                </Link>
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

// Subscription Card Component
function SubscriptionCard({
  title,
  count,
  change,
  breakdown,
}: {
  title: string;
  count: number | null;
  change?: number;
  breakdown: { label: string; count: number; color: string }[];
}) {
  return (
    <div className="card p-6">
      <div className="flex items-start justify-between mb-4">
        <div>
          <p className="text-sm text-text-muted">{title}</p>
          <p className="text-3xl font-semibold text-text-primary mt-1 tabular-nums">
            {count === null ? "—" : count}
          </p>
        </div>
        {typeof change === "number" && (
          <span
            className={cn(
              "metric-change",
              change >= 0 ? "metric-change--positive" : "metric-change--negative"
            )}
          >
            {change >= 0 ? (
              <TrendingUp className="w-4 h-4" />
            ) : (
              <TrendingDown className="w-4 h-4" />
            )}
            {Math.abs(change)}%
          </span>
        )}
      </div>

      <div className="space-y-2">
        {breakdown.length === 0 ? (
          <p className="text-sm text-text-muted">No breakdown data available.</p>
        ) : (
          breakdown.map((item) => (
            <div key={item.label} className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className={cn("w-2 h-2 rounded-full", item.color)} />
                <span className="text-sm text-text-secondary">{item.label}</span>
              </div>
              <span className="text-sm font-medium text-text-primary tabular-nums">
                {item.count}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

// Chart Components
async function RevenueChart() {
  const revenueData = await fetchOrNull(() => getRevenueData("12m"));
  if (!revenueData || revenueData.length === 0) {
    return <EmptyChart />;
  }
  const data = revenueData.map((item) => ({
    month: item.month,
    revenue: item.revenue / 100, // Convert cents to dollars
  }));

  return (
    <LineChart
      data={data}
      dataKey="revenue"
      xAxisKey="month"
      height={280}
      color="hsl(var(--color-accent))"
    />
  );
}

async function PaymentMethodChart() {
  const breakdown = await fetchOrNull(getRevenueBreakdown);
  const byPlan = breakdown?.byPlan ?? [];
  if (byPlan.length === 0) {
    return <EmptyChart />;
  }
  const data = byPlan.map((item) => ({
    method: item.plan,
    amount: item.revenue / 100, // Convert cents to dollars
  }));

  return (
    <BarChart
      data={data}
      dataKey="amount"
      xAxisKey="method"
      height={280}
      color="hsl(var(--color-highlight))"
    />
  );
}

function ChartSkeleton() {
  return (
    <div className="h-[280px] flex items-center justify-center">
      <div className="w-full h-full bg-surface-overlay rounded animate-pulse" />
    </div>
  );
}
