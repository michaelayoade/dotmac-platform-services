"use client";

import type { ElementType } from "react";
import { formatDistanceToNow } from "date-fns";
import {
  UserPlus,
  CreditCard,
  Server,
  AlertTriangle,
  Settings,
  Building2,
  Loader2,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { useActivityFeed, type ActivityItem as APIActivityItem } from "@/lib/hooks/api";

// Display types
type ActivityType = "user_created" | "payment_received" | "deployment_started" | "alert" | "tenant_created" | "settings_changed";

interface ActivityDisplay {
  id: string;
  type: ActivityType;
  title: string;
  description: string;
  timestamp: string;
  actor?: {
    name: string;
    email: string;
  };
}

// Map API activity types to display types
function mapActivityType(apiType: APIActivityItem["type"]): ActivityType {
  const typeMap: Record<string, ActivityType> = {
    user_action: "user_created",
    system_event: "settings_changed",
    deployment: "deployment_started",
    billing: "payment_received",
    security: "alert",
  };
  return typeMap[apiType] || "settings_changed";
}

function mapActivityToDisplay(activity: APIActivityItem): ActivityDisplay {
  return {
    id: activity.id,
    type: mapActivityType(activity.type),
    title: activity.action,
    description: activity.target ? `${activity.target.name}` : "",
    timestamp: activity.timestamp,
    actor: activity.actor ? { name: activity.actor.name, email: "" } : undefined,
  };
}

const activityIcons: Record<ActivityType, ElementType> = {
  user_created: UserPlus,
  payment_received: CreditCard,
  deployment_started: Server,
  alert: AlertTriangle,
  tenant_created: Building2,
  settings_changed: Settings,
};

const activityColors: Record<ActivityType, string> = {
  user_created: "bg-status-info/15 text-status-info",
  payment_received: "bg-status-success/15 text-status-success",
  deployment_started: "bg-accent-subtle text-accent",
  alert: "bg-status-warning/15 text-status-warning",
  tenant_created: "bg-highlight-subtle text-highlight",
  settings_changed: "bg-surface-overlay text-text-muted",
};

export function RecentActivityFeed() {
  const { data: apiActivities, isLoading, error } = useActivityFeed({ limit: 6 });
  const activities = apiActivities?.map(mapActivityToDisplay) || [];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-6 h-6 text-accent animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8 text-text-muted">
        <p className="text-sm">Failed to load activity feed</p>
      </div>
    );
  }

  if (activities.length === 0) {
    return (
      <div className="text-center py-8 text-text-muted">
        <p className="text-sm">No recent activity</p>
      </div>
    );
  }

  return (
    <div className="space-y-1">
      {activities.map((activity, index) => {
        const Icon = activityIcons[activity.type];
        const colorClass = activityColors[activity.type];

        return (
          <div
            key={activity.id}
            className={cn(
              "group flex items-start gap-4 p-3 -mx-3 rounded-lg",
              "hover:bg-surface-overlay/50 cursor-pointer transition-colors",
              "animate-fade-up"
            )}
            style={{ animationDelay: `${index * 50}ms` }}
          >
            {/* Icon */}
            <div className={cn("p-2 rounded-lg flex-shrink-0", colorClass)}>
              <Icon className="w-4 h-4" />
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="text-sm font-medium text-text-primary group-hover:text-accent transition-colors">
                    {activity.title}
                  </p>
                  <p className="text-sm text-text-secondary mt-0.5">
                    {activity.description}
                  </p>
                </div>
                <span className="text-xs text-text-muted whitespace-nowrap">
                  {formatDistanceToNow(new Date(activity.timestamp), { addSuffix: true })}
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

      {/* View all link */}
      <div className="pt-3 border-t border-border mt-3">
        <button className="text-sm text-accent hover:text-accent-hover font-medium">
          View all activity →
        </button>
      </div>
    </div>
  );
}
