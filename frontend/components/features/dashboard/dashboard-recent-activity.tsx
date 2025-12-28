"use client";

import { formatDistanceToNow } from "date-fns";
import { Activity, Clock } from "lucide-react";
import type { RecentActivityItem } from "@/lib/api/types/dashboard";

interface DashboardRecentActivityProps {
  activities: RecentActivityItem[];
  title?: string;
  className?: string;
  maxItems?: number;
  showEmpty?: boolean;
  emptyMessage?: string;
}

/**
 * Status colors mapped to design tokens:
 * - success → network (green)
 * - warning → alert (orange)
 * - error → critical (red)
 * - info → primary (blue)
 */
const statusColors: Record<string, string> = {
  // Success states → network (green)
  completed: "bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400",
  active: "bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400",
  paid: "bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400",
  delivered: "bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400",
  resolved: "bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400",
  closed: "bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400",

  // Warning states → alert (orange)
  pending: "bg-orange-100 text-orange-800 dark:bg-orange-900/20 dark:text-orange-400",
  in_progress: "bg-orange-100 text-orange-800 dark:bg-orange-900/20 dark:text-orange-400",
  waiting: "bg-orange-100 text-orange-800 dark:bg-orange-900/20 dark:text-orange-400",
  trial: "bg-orange-100 text-orange-800 dark:bg-orange-900/20 dark:text-orange-400",
  open: "bg-orange-100 text-orange-800 dark:bg-orange-900/20 dark:text-orange-400",

  // Error states → critical (red)
  failed: "bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400",
  cancelled: "bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400",
  overdue: "bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400",
  suspended: "bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400",
  error: "bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400",

  // Info states → primary (blue)
  running: "bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400",
  processing: "bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400",

  // Default → neutral (gray)
  unknown: "bg-gray-100 text-gray-800 dark:bg-gray-800/20 dark:text-gray-400",
};

function getStatusColor(status: string): string {
  const normalizedStatus = status.toLowerCase().replace(/[-\s]/g, "_");
  return statusColors[normalizedStatus] || statusColors.unknown;
}

function formatTimestamp(timestamp: string): string {
  try {
    return formatDistanceToNow(new Date(timestamp), { addSuffix: true });
  } catch {
    return timestamp;
  }
}

function formatAmount(amount?: number): string | null {
  if (amount === undefined || amount === null) return null;
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(amount);
}

export function DashboardRecentActivity({
  activities,
  title = "Recent Activity",
  className = "",
  maxItems = 10,
  showEmpty = true,
  emptyMessage = "No recent activity",
}: DashboardRecentActivityProps) {
  const displayedActivities = activities.slice(0, maxItems);

  return (
    <div className={`bg-surface-primary rounded-lg border border-border-primary ${className}`}>
      <div className="px-4 py-3 border-b border-border-primary">
        <h3 className="font-semibold text-text-primary flex items-center gap-2">
          <Activity className="w-4 h-4" />
          {title}
        </h3>
      </div>

      <div className="divide-y divide-border-primary">
        {displayedActivities.length === 0 ? (
          showEmpty && (
            <div className="px-4 py-8 text-center text-text-muted">
              {emptyMessage}
            </div>
          )
        ) : (
          displayedActivities.map((activity) => (
            <div
              key={activity.id}
              className="px-4 py-3 hover:bg-surface-secondary/50 transition-colors"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-text-primary truncate">
                    {activity.description}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 text-xs font-medium rounded-full ${getStatusColor(
                        activity.status
                      )}`}
                    >
                      {activity.status.replace(/_/g, " ")}
                    </span>
                    <span className="text-xs text-text-muted flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {formatTimestamp(activity.timestamp)}
                    </span>
                  </div>
                </div>
                {activity.amount !== undefined && activity.amount !== null && (
                  <span className="text-sm font-medium text-text-primary tabular-nums">
                    {formatAmount(activity.amount)}
                  </span>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default DashboardRecentActivity;
