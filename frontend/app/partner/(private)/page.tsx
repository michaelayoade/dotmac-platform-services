"use client";

import { Suspense } from "react";
import Link from "next/link";
import {
  DollarSign,
  Users,
  TrendingUp,
  FileText,
  UserPlus,
  ArrowUpRight,
  ArrowDownRight,
} from "lucide-react";

import { PageHeader } from "@/components/shared";
import { usePartnerDashboard } from "@/lib/hooks/api/use-partner-portal";
import { cn } from "@/lib/utils";

// KPI Tile Component
interface KPITileProps {
  title: string;
  value: string;
  change?: number;
  changeLabel?: string;
  icon: React.ReactNode;
  description?: string;
}

function KPITile({
  title,
  value,
  change,
  changeLabel,
  icon,
  description,
}: KPITileProps) {
  const isPositive = change !== undefined && change >= 0;

  return (
    <div className="bg-surface-elevated rounded-lg border border-border p-6 hover:border-border-hover transition-colors">
      <div className="flex items-start justify-between">
        <div className="p-2 rounded-lg bg-accent/10 text-accent">{icon}</div>
        {change !== undefined && (
          <div
            className={cn(
              "flex items-center gap-1 text-sm font-medium",
              isPositive ? "text-status-success" : "text-status-error"
            )}
          >
            {isPositive ? (
              <ArrowUpRight className="w-4 h-4" />
            ) : (
              <ArrowDownRight className="w-4 h-4" />
            )}
            {Math.abs(change)}%
          </div>
        )}
      </div>
      <div className="mt-4">
        <p className="text-sm text-text-muted">{title}</p>
        <p className="text-2xl font-semibold text-text-primary mt-1">{value}</p>
        {description && (
          <p className="text-xs text-text-muted mt-1">{description}</p>
        )}
        {changeLabel && (
          <p className="text-xs text-text-muted mt-1">{changeLabel}</p>
        )}
      </div>
    </div>
  );
}

// Simple Bar Chart Component
interface BarChartProps {
  data: { label: string; value: number }[];
  maxValue?: number;
  color?: string;
}

function SimpleBarChart({ data, maxValue, color = "bg-accent" }: BarChartProps) {
  const max = maxValue || Math.max(...data.map((d) => d.value), 1);

  return (
    <div className="space-y-3">
      {data.map((item, index) => (
        <div key={index} className="space-y-1">
          <div className="flex justify-between text-sm">
            <span className="text-text-secondary">{item.label}</span>
            <span className="text-text-primary font-medium">
              ${item.value.toLocaleString()}
            </span>
          </div>
          <div className="h-2 bg-surface-overlay rounded-full overflow-hidden">
            <div
              className={cn("h-full rounded-full transition-all duration-500", color)}
              style={{ width: `${(item.value / max) * 100}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

// Recent Activity Item
interface ActivityItemProps {
  type: "referral" | "commission" | "conversion" | "payout";
  title: string;
  description: string;
  time: string;
}

function ActivityItem({ type, title, description, time }: ActivityItemProps) {
  const iconMap = {
    referral: <UserPlus className="w-4 h-4" />,
    commission: <DollarSign className="w-4 h-4" />,
    conversion: <TrendingUp className="w-4 h-4" />,
    payout: <FileText className="w-4 h-4" />,
  };

  const colorMap = {
    referral: "bg-blue-500/10 text-blue-500",
    commission: "bg-green-500/10 text-green-500",
    conversion: "bg-purple-500/10 text-purple-500",
    payout: "bg-amber-500/10 text-amber-500",
  };

  return (
    <div className="flex items-start gap-3 py-3 border-b border-border last:border-0">
      <div className={cn("p-2 rounded-lg", colorMap[type])}>{iconMap[type]}</div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-text-primary truncate">{title}</p>
        <p className="text-xs text-text-muted">{description}</p>
      </div>
      <span className="text-xs text-text-muted whitespace-nowrap">{time}</span>
    </div>
  );
}

// Loading Skeleton
function DashboardSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="bg-surface-elevated rounded-lg border border-border p-6 h-32"
          >
            <div className="h-4 w-20 bg-surface-overlay rounded" />
            <div className="h-8 w-32 bg-surface-overlay rounded mt-4" />
          </div>
        ))}
      </div>
    </div>
  );
}

function DashboardContent() {
  const { data, isLoading, error } = usePartnerDashboard();

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  if (error) {
    // Show demo data on error
    return <DemoContent />;
  }

  if (!data) {
    return <DemoContent />;
  }

  const { stats, revenueHistory, commissionHistory } = data;

  return (
    <div className="space-y-6">
      {/* KPI Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <KPITile
          title="Total Revenue Generated"
          value={`$${stats.totalRevenue.toLocaleString()}`}
          change={stats.revenueChange}
          icon={<DollarSign className="w-5 h-5" />}
          description="From your referred customers"
        />
        <KPITile
          title="Pending Commissions"
          value={`$${stats.pendingCommissions.toLocaleString()}`}
          icon={<TrendingUp className="w-5 h-5" />}
          description={`$${stats.paidCommissions.toLocaleString()} paid to date`}
        />
        <KPITile
          title="Active Customers"
          value={stats.activeCustomers.toLocaleString()}
          change={stats.customerChange}
          icon={<Users className="w-5 h-5" />}
          description="Customers assigned to you"
        />
        <KPITile
          title="Conversion Rate"
          value={`${stats.conversionRate.toFixed(1)}%`}
          icon={<TrendingUp className="w-5 h-5" />}
          description={`${stats.convertedReferrals} of ${stats.totalReferrals} referrals`}
        />
      </div>

      {/* Charts Row */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Revenue Trend */}
        <div className="bg-surface-elevated rounded-lg border border-border p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="font-semibold text-text-primary">Revenue Trend</h3>
              <p className="text-sm text-text-muted">Monthly revenue generated</p>
            </div>
            <Link
              href="/partner/customers"
              className="text-sm text-accent hover:text-accent-hover inline-flex items-center gap-1"
            >
              View Customers <ArrowUpRight className="w-3 h-3" />
            </Link>
          </div>
          <SimpleBarChart
            data={revenueHistory.slice(-6).map((item) => ({
              label: item.date,
              value: item.revenue,
            }))}
          />
        </div>

        {/* Commission History */}
        <div className="bg-surface-elevated rounded-lg border border-border p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="font-semibold text-text-primary">
                Commission History
              </h3>
              <p className="text-sm text-text-muted">Monthly commissions earned</p>
            </div>
            <Link
              href="/partner/commissions"
              className="text-sm text-accent hover:text-accent-hover inline-flex items-center gap-1"
            >
              View All <ArrowUpRight className="w-3 h-3" />
            </Link>
          </div>
          <SimpleBarChart
            data={commissionHistory.slice(-6).map((item) => ({
              label: item.month,
              value: item.amount,
            }))}
            color="bg-status-success"
          />
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Submit Referral */}
        <Link
          href="/partner/referrals?action=new"
          className="bg-surface-elevated rounded-lg border border-border p-6 hover:border-accent transition-colors group"
        >
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-lg bg-accent/10 text-accent group-hover:bg-accent group-hover:text-white transition-colors">
              <UserPlus className="w-6 h-6" />
            </div>
            <div>
              <h3 className="font-semibold text-text-primary">Submit Referral</h3>
              <p className="text-sm text-text-muted">Add a new customer referral</p>
            </div>
          </div>
        </Link>

        {/* View Statements */}
        <Link
          href="/partner/statements"
          className="bg-surface-elevated rounded-lg border border-border p-6 hover:border-accent transition-colors group"
        >
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-lg bg-highlight/10 text-highlight group-hover:bg-highlight group-hover:text-white transition-colors">
              <FileText className="w-6 h-6" />
            </div>
            <div>
              <h3 className="font-semibold text-text-primary">View Statements</h3>
              <p className="text-sm text-text-muted">Download monthly statements</p>
            </div>
          </div>
        </Link>

        {/* Track Performance */}
        <Link
          href="/partner/commissions"
          className="bg-surface-elevated rounded-lg border border-border p-6 hover:border-accent transition-colors group"
        >
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-lg bg-status-success/10 text-status-success group-hover:bg-status-success group-hover:text-white transition-colors">
              <TrendingUp className="w-6 h-6" />
            </div>
            <div>
              <h3 className="font-semibold text-text-primary">Track Commissions</h3>
              <p className="text-sm text-text-muted">Monitor your earnings</p>
            </div>
          </div>
        </Link>
      </div>
    </div>
  );
}

// Demo content when API is not available
function DemoContent() {
  return (
    <div className="space-y-6">
      {/* KPI Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <KPITile
          title="Total Revenue Generated"
          value="$124,500"
          change={12.5}
          icon={<DollarSign className="w-5 h-5" />}
          description="From your referred customers"
        />
        <KPITile
          title="Pending Commissions"
          value="$3,250"
          icon={<TrendingUp className="w-5 h-5" />}
          description="$18,750 paid to date"
        />
        <KPITile
          title="Active Customers"
          value="23"
          change={8.3}
          icon={<Users className="w-5 h-5" />}
          description="Customers assigned to you"
        />
        <KPITile
          title="Conversion Rate"
          value="34.5%"
          icon={<TrendingUp className="w-5 h-5" />}
          description="10 of 29 referrals"
        />
      </div>

      {/* Charts Row */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Revenue Trend */}
        <div className="bg-surface-elevated rounded-lg border border-border p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="font-semibold text-text-primary">Revenue Trend</h3>
              <p className="text-sm text-text-muted">Monthly revenue generated</p>
            </div>
            <Link
              href="/partner/customers"
              className="text-sm text-accent hover:text-accent-hover inline-flex items-center gap-1"
            >
              View Customers <ArrowUpRight className="w-3 h-3" />
            </Link>
          </div>
          <SimpleBarChart
            data={[
              { label: "Jul", value: 18500 },
              { label: "Aug", value: 21200 },
              { label: "Sep", value: 19800 },
              { label: "Oct", value: 24100 },
              { label: "Nov", value: 22300 },
              { label: "Dec", value: 18600 },
            ]}
          />
        </div>

        {/* Commission History */}
        <div className="bg-surface-elevated rounded-lg border border-border p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="font-semibold text-text-primary">
                Commission History
              </h3>
              <p className="text-sm text-text-muted">Monthly commissions earned</p>
            </div>
            <Link
              href="/partner/commissions"
              className="text-sm text-accent hover:text-accent-hover inline-flex items-center gap-1"
            >
              View All <ArrowUpRight className="w-3 h-3" />
            </Link>
          </div>
          <SimpleBarChart
            data={[
              { label: "Jul", value: 2775 },
              { label: "Aug", value: 3180 },
              { label: "Sep", value: 2970 },
              { label: "Oct", value: 3615 },
              { label: "Nov", value: 3345 },
              { label: "Dec", value: 2790 },
            ]}
            color="bg-status-success"
          />
        </div>
      </div>

      {/* Recent Activity */}
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 bg-surface-elevated rounded-lg border border-border p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-text-primary">Recent Activity</h3>
            <span className="text-xs text-text-muted">Last 7 days</span>
          </div>
          <div className="divide-y divide-border">
            <ActivityItem
              type="commission"
              title="Commission Approved"
              description="$450 from Acme Corp subscription"
              time="2 hours ago"
            />
            <ActivityItem
              type="referral"
              title="New Referral Submitted"
              description="TechStart Inc. - Enterprise inquiry"
              time="5 hours ago"
            />
            <ActivityItem
              type="conversion"
              title="Referral Converted"
              description="CloudNine Solutions signed up for Pro"
              time="1 day ago"
            />
            <ActivityItem
              type="payout"
              title="Payout Processed"
              description="$2,850 transferred to your account"
              time="3 days ago"
            />
            <ActivityItem
              type="referral"
              title="New Referral Submitted"
              description="DataFlow Systems - Professional tier"
              time="5 days ago"
            />
          </div>
        </div>

        {/* Quick Actions */}
        <div className="space-y-4">
          <Link
            href="/partner/referrals?action=new"
            className="block bg-surface-elevated rounded-lg border border-border p-6 hover:border-accent transition-colors group"
          >
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-lg bg-accent/10 text-accent group-hover:bg-accent group-hover:text-white transition-colors">
                <UserPlus className="w-6 h-6" />
              </div>
              <div>
                <h3 className="font-semibold text-text-primary">Submit Referral</h3>
                <p className="text-sm text-text-muted">Add a new lead</p>
              </div>
            </div>
          </Link>

          <Link
            href="/partner/statements"
            className="block bg-surface-elevated rounded-lg border border-border p-6 hover:border-accent transition-colors group"
          >
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-lg bg-highlight/10 text-highlight group-hover:bg-highlight group-hover:text-white transition-colors">
                <FileText className="w-6 h-6" />
              </div>
              <div>
                <h3 className="font-semibold text-text-primary">View Statements</h3>
                <p className="text-sm text-text-muted">Download reports</p>
              </div>
            </div>
          </Link>

          <Link
            href="/partner/commissions"
            className="block bg-surface-elevated rounded-lg border border-border p-6 hover:border-accent transition-colors group"
          >
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-lg bg-status-success/10 text-status-success group-hover:bg-status-success group-hover:text-white transition-colors">
                <TrendingUp className="w-6 h-6" />
              </div>
              <div>
                <h3 className="font-semibold text-text-primary">Track Commissions</h3>
                <p className="text-sm text-text-muted">View earnings</p>
              </div>
            </div>
          </Link>
        </div>
      </div>
    </div>
  );
}

export default function PartnerDashboardPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Partner Dashboard"
        description="Track your referrals, customers, and commissions"
      />
      <DashboardContent />
    </div>
  );
}
