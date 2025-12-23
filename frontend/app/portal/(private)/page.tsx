"use client";

import Link from "next/link";
import {
  Users,
  CreditCard,
  BarChart3,
  Settings,
  UserPlus,
  ArrowUpRight,
  Zap,
  HardDrive,
  Clock,
  Activity,
} from "lucide-react";

import { PageHeader } from "@/components/shared";
import { useTenantDashboard } from "@/lib/hooks/api/use-tenant-portal";
import { cn } from "@/lib/utils";

// Usage Gauge Component
interface UsageGaugeProps {
  label: string;
  current: number;
  limit: number;
  unit: string;
  icon: React.ReactNode;
  color?: string;
}

function UsageGauge({
  label,
  current,
  limit,
  unit,
  icon,
  color = "bg-accent",
}: UsageGaugeProps) {
  const percentage = Math.min((current / limit) * 100, 100);
  const isWarning = percentage >= 80;
  const isCritical = percentage >= 95;

  return (
    <div className="bg-surface-elevated rounded-lg border border-border p-5">
      <div className="flex items-start justify-between mb-4">
        <div className="p-2 rounded-lg bg-accent/10 text-accent">{icon}</div>
        <span
          className={cn(
            "text-xs font-medium px-2 py-0.5 rounded-full",
            isCritical
              ? "bg-status-error/10 text-status-error"
              : isWarning
                ? "bg-status-warning/10 text-status-warning"
                : "bg-status-success/10 text-status-success"
          )}
        >
          {percentage.toFixed(0)}%
        </span>
      </div>

      <p className="text-sm text-text-muted">{label}</p>
      <p className="text-xl font-semibold text-text-primary mt-1">
        {current.toLocaleString()}{" "}
        <span className="text-sm font-normal text-text-muted">
          / {limit.toLocaleString()} {unit}
        </span>
      </p>

      <div className="mt-3 h-2 bg-surface-overlay rounded-full overflow-hidden">
        <div
          className={cn(
            "h-full rounded-full transition-all duration-500",
            isCritical
              ? "bg-status-error"
              : isWarning
                ? "bg-status-warning"
                : color
          )}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

// Activity Item
interface ActivityItemProps {
  type: string;
  description: string;
  userName?: string;
  time: string;
}

function ActivityItem({ type, description, userName, time }: ActivityItemProps) {
  const iconMap: Record<string, React.ReactNode> = {
    user_joined: <UserPlus className="w-4 h-4" />,
    user_removed: <Users className="w-4 h-4" />,
    role_changed: <Settings className="w-4 h-4" />,
    settings_updated: <Settings className="w-4 h-4" />,
    plan_upgraded: <Zap className="w-4 h-4" />,
  };

  const colorMap: Record<string, string> = {
    user_joined: "bg-status-success/10 text-status-success",
    user_removed: "bg-status-error/10 text-status-error",
    role_changed: "bg-blue-500/10 text-blue-500",
    settings_updated: "bg-purple-500/10 text-purple-500",
    plan_upgraded: "bg-highlight/10 text-highlight",
  };

  return (
    <div className="flex items-start gap-3 py-3 border-b border-border last:border-0">
      <div className={cn("p-2 rounded-lg", colorMap[type] || "bg-surface-overlay text-text-muted")}>
        {iconMap[type] || <Activity className="w-4 h-4" />}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-text-primary">{description}</p>
        {userName && <p className="text-xs text-text-muted">by {userName}</p>}
      </div>
      <span className="text-xs text-text-muted whitespace-nowrap">{time}</span>
    </div>
  );
}

// Loading Skeleton
function DashboardSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="bg-surface-elevated rounded-lg border border-border p-5 h-36"
          >
            <div className="h-8 w-8 bg-surface-overlay rounded-lg mb-4" />
            <div className="h-4 w-20 bg-surface-overlay rounded mb-2" />
            <div className="h-6 w-32 bg-surface-overlay rounded" />
          </div>
        ))}
      </div>
    </div>
  );
}

// Demo data
const demoData = {
  stats: {
    activeUsers: 8,
    maxUsers: 10,
    apiCallsThisMonth: 45230,
    apiCallsLimit: 100000,
    storageUsedMb: 2340,
    storageLimitMb: 5000,
    daysUntilRenewal: 18,
    planName: "Professional",
    planType: "PROFESSIONAL" as const,
  },
  recentActivity: [
    {
      id: "1",
      type: "user_joined",
      description: "Sarah Johnson joined the team",
      userName: "Admin",
      createdAt: "2024-12-22T14:30:00Z",
    },
    {
      id: "2",
      type: "role_changed",
      description: "Michael Chen's role changed to Admin",
      userName: "Admin",
      createdAt: "2024-12-21T10:15:00Z",
    },
    {
      id: "3",
      type: "settings_updated",
      description: "Security settings updated",
      userName: "Admin",
      createdAt: "2024-12-20T16:45:00Z",
    },
    {
      id: "4",
      type: "plan_upgraded",
      description: "Plan upgraded to Professional",
      createdAt: "2024-12-15T09:00:00Z",
    },
  ],
};

function DashboardContent() {
  const { data, isLoading, error } = useTenantDashboard();

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  const dashboardData = data || demoData;
  const { stats, recentActivity } = dashboardData;

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));

    if (diffInHours < 1) return "Just now";
    if (diffInHours < 24) return `${diffInHours}h ago`;
    if (diffInHours < 168) return `${Math.floor(diffInHours / 24)}d ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="space-y-6">
      {/* Plan Banner */}
      <div className="bg-gradient-to-r from-accent/10 to-highlight/10 rounded-lg border border-accent/20 p-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-lg bg-accent/20 text-accent">
              <Zap className="w-6 h-6" />
            </div>
            <div>
              <h2 className="font-semibold text-text-primary">
                {stats.planName} Plan
              </h2>
              <p className="text-sm text-text-muted">
                {stats.daysUntilRenewal} days until renewal
              </p>
            </div>
          </div>
          <Link
            href="/portal/billing"
            className="px-4 py-2 rounded-md bg-accent text-white hover:bg-accent-hover transition-colors inline-flex items-center gap-2"
          >
            Manage Plan
            <ArrowUpRight className="w-4 h-4" />
          </Link>
        </div>
      </div>

      {/* Usage Gauges */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <UsageGauge
          label="Team Members"
          current={stats.activeUsers}
          limit={stats.maxUsers}
          unit="users"
          icon={<Users className="w-5 h-5" />}
        />
        <UsageGauge
          label="API Calls"
          current={stats.apiCallsThisMonth}
          limit={stats.apiCallsLimit}
          unit="calls"
          icon={<Activity className="w-5 h-5" />}
          color="bg-highlight"
        />
        <UsageGauge
          label="Storage Used"
          current={stats.storageUsedMb}
          limit={stats.storageLimitMb}
          unit="MB"
          icon={<HardDrive className="w-5 h-5" />}
          color="bg-status-success"
        />
        <div className="bg-surface-elevated rounded-lg border border-border p-5">
          <div className="flex items-start justify-between mb-4">
            <div className="p-2 rounded-lg bg-accent/10 text-accent">
              <Clock className="w-5 h-5" />
            </div>
          </div>
          <p className="text-sm text-text-muted">Days Until Renewal</p>
          <p className="text-xl font-semibold text-text-primary mt-1">
            {stats.daysUntilRenewal}{" "}
            <span className="text-sm font-normal text-text-muted">days</span>
          </p>
          <Link
            href="/portal/billing"
            className="inline-flex items-center gap-1 text-sm text-accent hover:text-accent-hover mt-3"
          >
            View billing <ArrowUpRight className="w-3 h-3" />
          </Link>
        </div>
      </div>

      {/* Quick Actions & Activity */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Quick Actions */}
        <div className="space-y-4">
          <h3 className="font-semibold text-text-primary">Quick Actions</h3>

          <Link
            href="/portal/team?action=invite"
            className="block bg-surface-elevated rounded-lg border border-border p-5 hover:border-accent transition-colors group"
          >
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-lg bg-accent/10 text-accent group-hover:bg-accent group-hover:text-white transition-colors">
                <UserPlus className="w-5 h-5" />
              </div>
              <div>
                <h4 className="font-medium text-text-primary">Invite Team Member</h4>
                <p className="text-sm text-text-muted">
                  {stats.maxUsers - stats.activeUsers} seats available
                </p>
              </div>
            </div>
          </Link>

          <Link
            href="/portal/billing"
            className="block bg-surface-elevated rounded-lg border border-border p-5 hover:border-accent transition-colors group"
          >
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-lg bg-highlight/10 text-highlight group-hover:bg-highlight group-hover:text-white transition-colors">
                <CreditCard className="w-5 h-5" />
              </div>
              <div>
                <h4 className="font-medium text-text-primary">View Invoices</h4>
                <p className="text-sm text-text-muted">Billing history</p>
              </div>
            </div>
          </Link>

          <Link
            href="/portal/usage"
            className="block bg-surface-elevated rounded-lg border border-border p-5 hover:border-accent transition-colors group"
          >
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-lg bg-status-success/10 text-status-success group-hover:bg-status-success group-hover:text-white transition-colors">
                <BarChart3 className="w-5 h-5" />
              </div>
              <div>
                <h4 className="font-medium text-text-primary">Usage Analytics</h4>
                <p className="text-sm text-text-muted">Detailed breakdown</p>
              </div>
            </div>
          </Link>
        </div>

        {/* Recent Activity */}
        <div className="lg:col-span-2 bg-surface-elevated rounded-lg border border-border p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-text-primary">Recent Activity</h3>
            <span className="text-xs text-text-muted">Last 7 days</span>
          </div>

          {recentActivity.length === 0 ? (
            <p className="text-sm text-text-muted text-center py-8">
              No recent activity
            </p>
          ) : (
            <div className="divide-y divide-border">
              {recentActivity.map((activity) => (
                <ActivityItem
                  key={activity.id}
                  type={activity.type}
                  description={activity.description}
                  userName={activity.userName}
                  time={formatTimeAgo(activity.createdAt)}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function TenantDashboardPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Organization Dashboard"
        description="Manage your team, billing, and usage"
      />
      <DashboardContent />
    </div>
  );
}
