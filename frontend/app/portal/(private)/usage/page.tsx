"use client";

import { useState } from "react";
import {
  Activity,
  HardDrive,
  Users,
  Wifi,
  TrendingUp,
  TrendingDown,
  ArrowUpRight,
} from "lucide-react";

import { PageHeader } from "@/components/shared";
import { useTenantUsage, useTenantUsageBreakdown } from "@/lib/hooks/api/use-tenant-portal";
import { cn } from "@/lib/utils";

type Period = "7d" | "30d" | "90d" | "1y";

function EmptyUsageState() {
  return (
    <div className="bg-surface-elevated rounded-lg border border-border p-6">
      <h2 className="text-lg font-semibold text-text-primary">No usage data yet</h2>
      <p className="text-sm text-text-muted mt-2">
        Usage metrics will appear after your organization generates activity.
      </p>
    </div>
  );
}

// Usage Card Component
interface UsageCardProps {
  title: string;
  current: number;
  limit: number;
  unit: string;
  percentUsed: number;
  icon: React.ReactNode;
  history: { date: string; value: number }[];
  color: string;
}

function UsageCard({
  title,
  current,
  limit,
  unit,
  percentUsed,
  icon,
  history,
  color,
}: UsageCardProps) {
  const isWarning = percentUsed >= 80;
  const isCritical = percentUsed >= 95;

  // Calculate trend
  const lastValue = history[history.length - 1]?.value || 0;
  const prevValue = history[history.length - 2]?.value || lastValue;
  const trend = prevValue > 0 ? ((lastValue - prevValue) / prevValue) * 100 : 0;
  const isUp = trend > 0;

  // Get max for chart scaling
  const maxValue = Math.max(...history.map((h) => h.value), 1);

  return (
    <div className="bg-surface-elevated rounded-lg border border-border p-6">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={cn("p-2 rounded-lg", color)}>{icon}</div>
          <div>
            <h3 className="font-semibold text-text-primary">{title}</h3>
            <p className="text-sm text-text-muted">
              {current.toLocaleString()} / {limit.toLocaleString()} {unit}
            </p>
          </div>
        </div>
        <div
          className={cn(
            "flex items-center gap-1 text-sm font-medium",
            isUp ? "text-status-error" : "text-status-success"
          )}
        >
          {isUp ? (
            <TrendingUp className="w-4 h-4" />
          ) : (
            <TrendingDown className="w-4 h-4" />
          )}
          {Math.abs(trend).toFixed(1)}%
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-4">
        <div className="flex justify-between text-xs text-text-muted mb-1">
          <span>{percentUsed.toFixed(1)}% used</span>
          <span>{(100 - percentUsed).toFixed(1)}% remaining</span>
        </div>
        <div className="h-2 bg-surface-overlay rounded-full overflow-hidden">
          <div
            className={cn(
              "h-full rounded-full transition-all duration-500",
              isCritical
                ? "bg-status-error"
                : isWarning
                  ? "bg-status-warning"
                  : color.replace("/10", "").replace("bg-", "bg-")
            )}
            style={{ width: `${Math.min(percentUsed, 100)}%` }}
          />
        </div>
      </div>

      {/* Mini Chart */}
      <div className="h-16 flex items-end gap-1">
        {history.map((item, index) => (
          <div
            key={index}
            className="flex-1 flex flex-col items-center gap-1"
          >
            <div
              className={cn(
                "w-full rounded-sm transition-all duration-300",
                color.replace("/10", "/30")
              )}
              style={{
                height: `${(item.value / maxValue) * 100}%`,
                minHeight: "4px",
              }}
            />
            <span className="text-2xs text-text-muted truncate w-full text-center">
              {item.date.split(" ")[1]}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

// Usage Breakdown Table
function BreakdownTable({
  data,
}: {
  data: { feature: string; calls: number; percentage: number }[];
}) {
  return (
    <div className="bg-surface-elevated rounded-lg border border-border">
      <div className="p-6 border-b border-border">
        <h3 className="font-semibold text-text-primary">Usage by Feature</h3>
        <p className="text-sm text-text-muted">API calls breakdown by feature</p>
      </div>
      <div className="divide-y divide-border">
        {data.map((item) => (
          <div
            key={item.feature}
            className="px-6 py-4 flex items-center justify-between"
          >
            <div className="flex-1">
              <p className="font-medium text-text-primary">{item.feature}</p>
              <div className="flex items-center gap-2 mt-1">
                <div className="flex-1 h-1.5 bg-surface-overlay rounded-full overflow-hidden max-w-[200px]">
                  <div
                    className="h-full bg-accent rounded-full"
                    style={{ width: `${item.percentage}%` }}
                  />
                </div>
                <span className="text-xs text-text-muted">{item.percentage}%</span>
              </div>
            </div>
            <span className="text-sm font-medium text-text-primary">
              {item.calls.toLocaleString()} calls
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

// User Usage Table
function UserUsageTable({
  data,
}: {
  data: { userId: string; userName: string; apiCalls: number; storageUsed: number }[];
}) {
  return (
    <div className="bg-surface-elevated rounded-lg border border-border">
      <div className="p-6 border-b border-border">
        <h3 className="font-semibold text-text-primary">Usage by Team Member</h3>
        <p className="text-sm text-text-muted">Resource usage per user</p>
      </div>
      <div className="overflow-x-auto">
        <table className="data-table">
          <thead>
            <tr className="border-b border-border bg-surface-overlay/50">
              <th className="px-6 py-3 text-left text-xs font-semibold text-text-muted uppercase tracking-wider">
                User
              </th>
              <th className="px-6 py-3 text-right text-xs font-semibold text-text-muted uppercase tracking-wider">
                API Calls
              </th>
              <th className="px-6 py-3 text-right text-xs font-semibold text-text-muted uppercase tracking-wider">
                Storage
              </th>
            </tr>
          </thead>
          <tbody>
            {data.map((user) => (
              <tr
                key={user.userId}
                className="border-b border-border hover:bg-surface-overlay/50 transition-colors"
              >
                <td className="px-6 py-4">
                  <span className="font-medium text-text-primary">
                    {user.userName}
                  </span>
                </td>
                <td className="px-6 py-4 text-right text-text-secondary">
                  {user.apiCalls.toLocaleString()}
                </td>
                <td className="px-6 py-4 text-right text-text-secondary">
                  {user.storageUsed} MB
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function UsageSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="grid gap-4 md:grid-cols-2">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="bg-surface-elevated rounded-lg border border-border p-6 h-48"
          />
        ))}
      </div>
    </div>
  );
}

export default function UsagePage() {
  const [period, setPeriod] = useState<Period>("7d");

  const { data: usageData, isLoading: usageLoading } = useTenantUsage({ period });
  const { data: breakdownData, isLoading: breakdownLoading } = useTenantUsageBreakdown({ period });

  const usage = usageData ?? null;
  const breakdown = breakdownData ?? null;
  const isLoading = usageLoading || breakdownLoading;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Usage Analytics"
        description="Monitor your organization's resource usage"
      />

      {/* Period Filter */}
      <div className="flex gap-2">
        {(["7d", "30d", "90d", "1y"] as Period[]).map((p) => (
          <button
            key={p}
            onClick={() => setPeriod(p)}
            className={cn(
              "px-3 py-1.5 rounded-md text-sm font-medium transition-colors",
              period === p
                ? "bg-accent text-text-inverse"
                : "bg-surface-overlay text-text-secondary hover:text-text-primary"
            )}
          >
            {p === "7d"
              ? "7 Days"
              : p === "30d"
                ? "30 Days"
                : p === "90d"
                  ? "90 Days"
                  : "1 Year"}
          </button>
        ))}
      </div>

      {isLoading ? (
        <UsageSkeleton />
      ) : !usage || !breakdown ? (
        <EmptyUsageState />
      ) : (
        <>
          {/* Usage Cards */}
          <div className="grid gap-4 md:grid-cols-2">
            <UsageCard
              title="API Calls"
              {...usage.apiCalls}
              icon={<Activity className="w-5 h-5 text-accent" />}
              color="bg-accent/15"
            />
            <UsageCard
              title="Storage"
              {...usage.storage}
              icon={<HardDrive className="w-5 h-5 text-status-success" />}
              color="bg-status-success/15"
            />
            <UsageCard
              title="Team Members"
              {...usage.users}
              icon={<Users className="w-5 h-5 text-highlight" />}
              color="bg-highlight/15"
            />
            <UsageCard
              title="Bandwidth"
              {...usage.bandwidth}
              icon={<Wifi className="w-5 h-5 text-status-info" />}
              color="bg-status-info/15"
            />
          </div>

          {/* Breakdown Tables */}
          <div className="grid gap-6 lg:grid-cols-2">
            <BreakdownTable data={breakdown.byFeature} />
            <UserUsageTable data={breakdown.byUser} />
          </div>
        </>
      )}
    </div>
  );
}
