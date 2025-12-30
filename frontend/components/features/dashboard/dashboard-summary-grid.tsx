"use client";

import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import type { ReactNode } from "react";

export interface SummaryMetric {
  label: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  icon?: ReactNode;
  format?: "number" | "currency" | "percent";
}

interface DashboardSummaryGridProps {
  metrics: SummaryMetric[];
  columns?: 2 | 3 | 4 | 5;
  className?: string;
}

function formatValue(value: string | number, format?: SummaryMetric["format"]): string {
  if (typeof value === "string") return value;

  switch (format) {
    case "currency":
      return new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      }).format(value);
    case "percent":
      return `${value.toFixed(1)}%`;
    case "number":
    default:
      return new Intl.NumberFormat("en-US").format(value);
  }
}

/**
 * Change indicator colors mapped to design tokens:
 * - positive → network (green)
 * - negative → critical (red)
 * - neutral → neutral (gray)
 */
function ChangeIndicator({ change, label }: { change?: number; label?: string }) {
  if (change === undefined || change === null) return null;

  const isPositive = change > 0;
  const isNegative = change < 0;

  const colorClass = isPositive
    ? "text-green-600 dark:text-green-400"
    : isNegative
    ? "text-red-600 dark:text-red-400"
    : "text-gray-500 dark:text-gray-400";

  const Icon = isPositive ? TrendingUp : isNegative ? TrendingDown : Minus;

  return (
    <div className={`flex items-center gap-1 text-sm ${colorClass}`}>
      <Icon className="w-4 h-4" />
      <span>
        {isPositive && "+"}
        {change.toFixed(1)}%
        {label && <span className="text-text-muted ml-1">{label}</span>}
      </span>
    </div>
  );
}

export function DashboardSummaryGrid({
  metrics,
  columns = 4,
  className = "",
}: DashboardSummaryGridProps) {
  const gridCols = {
    2: "grid-cols-1 sm:grid-cols-2",
    3: "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3",
    4: "grid-cols-1 sm:grid-cols-2 lg:grid-cols-4",
    5: "grid-cols-1 sm:grid-cols-2 lg:grid-cols-5",
  };

  /**
   * Accent colors mapped to design tokens:
   * - blue → primary
   * - green → network
   * - orange → alert
   * - red → critical
   * - purple → purple
   */
  const accentGradients = [
    "from-blue-500/15 via-blue-400/5 to-transparent",
    "from-green-500/15 via-green-400/5 to-transparent",
    "from-orange-500/15 via-orange-400/5 to-transparent",
    "from-red-500/15 via-red-400/5 to-transparent",
    "from-purple-500/15 via-purple-400/5 to-transparent",
  ];

  const accentIconStyles = [
    "bg-blue-100/80 text-blue-700 dark:bg-blue-500/20 dark:text-blue-300",
    "bg-green-100/80 text-green-700 dark:bg-green-500/20 dark:text-green-300",
    "bg-orange-100/80 text-orange-700 dark:bg-orange-500/20 dark:text-orange-300",
    "bg-red-100/80 text-red-700 dark:bg-red-500/20 dark:text-red-300",
    "bg-purple-100/80 text-purple-700 dark:bg-purple-500/20 dark:text-purple-300",
  ];

  const accentBorderStyles = [
    "border-l-blue-500/40 dark:border-l-blue-400/30",
    "border-l-green-500/40 dark:border-l-green-400/30",
    "border-l-orange-500/40 dark:border-l-orange-400/30",
    "border-l-red-500/40 dark:border-l-red-400/30",
    "border-l-purple-500/40 dark:border-l-purple-400/30",
  ];

  return (
    <div className={`grid ${gridCols[columns]} gap-4 ${className}`}>
      {metrics.map((metric, index) => {
        const accentIndex = index % accentGradients.length;
        return (
          <div
            key={`${metric.label}-${index}`}
            className={`relative overflow-hidden bg-surface-primary rounded-lg border border-border-primary border-l-2 p-4 ${accentBorderStyles[accentIndex]}`}
          >
            <div
              className={`pointer-events-none absolute inset-0 bg-gradient-to-br ${accentGradients[accentIndex]}`}
            />
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-sm text-text-muted mb-1">{metric.label}</p>
                <p className="text-2xl font-semibold text-text-primary tabular-nums">
                  {formatValue(metric.value, metric.format)}
                </p>
                <ChangeIndicator change={metric.change} label={metric.changeLabel} />
              </div>
              {metric.icon && (
                <div
                  className={`flex-shrink-0 p-2 rounded-lg ${accentIconStyles[accentIndex]}`}
                >
                  {metric.icon}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// Pre-built summary grids for common dashboard types
export function BillingSummaryGrid({
  summary,
}: {
  summary: {
    totalRevenue: number;
    revenueThisMonth: number;
    revenueChangePct: number;
    mrr: number;
    activeSubscriptions: number;
    openInvoices: number;
    overdueInvoices: number;
    outstandingBalance: number;
  };
}) {
  const metrics: SummaryMetric[] = [
    { label: "Total Revenue", value: summary.totalRevenue, format: "currency" },
    { label: "This Month", value: summary.revenueThisMonth, format: "currency", change: summary.revenueChangePct },
    { label: "MRR", value: summary.mrr, format: "currency" },
    { label: "Active Subscriptions", value: summary.activeSubscriptions, format: "number" },
    { label: "Open Invoices", value: summary.openInvoices, format: "number" },
    { label: "Overdue Invoices", value: summary.overdueInvoices, format: "number" },
    { label: "Outstanding Balance", value: summary.outstandingBalance, format: "currency" },
  ];

  return <DashboardSummaryGrid metrics={metrics} columns={4} />;
}

export function TenantSummaryGrid({
  summary,
}: {
  summary: {
    totalTenants: number;
    activeTenants: number;
    trialTenants: number;
    suspendedTenants: number;
    newThisMonth: number;
    growthRatePct: number;
  };
}) {
  const metrics: SummaryMetric[] = [
    { label: "Total Tenants", value: summary.totalTenants, format: "number" },
    { label: "Active", value: summary.activeTenants, format: "number" },
    { label: "Trial", value: summary.trialTenants, format: "number" },
    { label: "New This Month", value: summary.newThisMonth, format: "number", change: summary.growthRatePct },
  ];

  return <DashboardSummaryGrid metrics={metrics} columns={4} />;
}

export function PartnerSummaryGrid({
  summary,
}: {
  summary: {
    totalPartners: number;
    activePartners: number;
    pendingApplications: number;
    totalReferrals: number;
    convertedReferrals: number;
    conversionRatePct: number;
    totalCommissions: number;
  };
}) {
  const metrics: SummaryMetric[] = [
    { label: "Total Partners", value: summary.totalPartners, format: "number" },
    { label: "Active", value: summary.activePartners, format: "number" },
    { label: "Pending Applications", value: summary.pendingApplications, format: "number" },
    { label: "Total Referrals", value: summary.totalReferrals, format: "number" },
    { label: "Converted", value: summary.convertedReferrals, format: "number" },
    { label: "Conversion Rate", value: summary.conversionRatePct, format: "percent" },
    { label: "Total Commissions", value: summary.totalCommissions, format: "currency" },
  ];

  return <DashboardSummaryGrid metrics={metrics} columns={4} />;
}

export default DashboardSummaryGrid;
