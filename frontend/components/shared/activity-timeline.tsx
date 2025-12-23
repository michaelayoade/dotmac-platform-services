"use client";

import { type ReactNode, type ElementType } from "react";
import { formatDistanceToNow } from "date-fns";
import { cn } from "@/lib/utils";

export interface ActivityItem {
  id: string;
  type: string;
  title: string;
  description?: string;
  timestamp: string;
  icon?: ElementType;
  iconColor?: string;
  iconBgColor?: string;
  actor?: {
    name: string;
    avatar?: string;
  };
  metadata?: Record<string, unknown>;
}

interface ActivityTimelineProps {
  activities: ActivityItem[];
  emptyMessage?: string;
  showRelativeTime?: boolean;
  maxItems?: number;
  className?: string;
}

export function ActivityTimeline({
  activities,
  emptyMessage = "No activity yet",
  showRelativeTime = true,
  maxItems,
  className,
}: ActivityTimelineProps) {
  const items = maxItems ? activities.slice(0, maxItems) : activities;

  if (items.length === 0) {
    return (
      <div className="text-center py-8 text-text-muted">
        <p className="text-sm">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className={cn("space-y-4", className)}>
      {items.map((activity, index) => {
        const Icon = activity.icon;
        const isLast = index === items.length - 1;

        return (
          <div key={activity.id} className="relative flex gap-4">
            {/* Timeline line */}
            {!isLast && (
              <div className="absolute left-4 top-8 bottom-0 w-px bg-border-subtle" />
            )}

            {/* Icon */}
            <div
              className={cn(
                "relative w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 z-10",
                activity.iconBgColor || "bg-surface-overlay"
              )}
            >
              {Icon ? (
                <Icon className={cn("w-4 h-4", activity.iconColor || "text-text-muted")} />
              ) : (
                <div className={cn("w-2 h-2 rounded-full", activity.iconColor || "bg-text-muted")} />
              )}
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0 pb-4">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="text-sm font-medium text-text-primary">
                    {activity.title}
                  </p>
                  {activity.description && (
                    <p className="text-sm text-text-muted mt-0.5">
                      {activity.description}
                    </p>
                  )}
                </div>
                <span className="text-xs text-text-muted whitespace-nowrap">
                  {showRelativeTime
                    ? formatDistanceToNow(new Date(activity.timestamp), { addSuffix: true })
                    : new Date(activity.timestamp).toLocaleDateString()}
                </span>
              </div>
              {activity.actor && (
                <p className="text-xs text-text-muted mt-1">
                  by {activity.actor.name}
                </p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// Activity type icon mapping helper
export function getActivityIcon(type: string): {
  icon: ElementType | undefined;
  color: string;
  bgColor: string;
} {
  // Import icons at usage point to avoid circular deps
  const icons: Record<string, { color: string; bgColor: string }> = {
    invoice: { color: "text-status-success", bgColor: "bg-status-success/15" },
    payment: { color: "text-status-success", bgColor: "bg-status-success/15" },
    subscription: { color: "text-accent", bgColor: "bg-accent-subtle" },
    support: { color: "text-status-info", bgColor: "bg-status-info/15" },
    note: { color: "text-text-muted", bgColor: "bg-surface-overlay" },
    update: { color: "text-highlight", bgColor: "bg-highlight-subtle" },
  };

  return {
    icon: undefined, // Let caller provide icon
    color: icons[type]?.color || "text-text-muted",
    bgColor: icons[type]?.bgColor || "bg-surface-overlay",
  };
}
