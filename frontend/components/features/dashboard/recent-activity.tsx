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
} from "lucide-react";

import { cn } from "@/lib/utils";

interface ActivityItem {
  id: string;
  type: "user_created" | "payment_received" | "deployment_started" | "alert" | "tenant_created" | "settings_changed";
  title: string;
  description: string;
  timestamp: string;
  actor?: {
    name: string;
    email: string;
  };
  metadata?: Record<string, unknown>;
}

const activityIcons: Record<ActivityItem["type"], ElementType> = {
  user_created: UserPlus,
  payment_received: CreditCard,
  deployment_started: Server,
  alert: AlertTriangle,
  tenant_created: Building2,
  settings_changed: Settings,
};

const activityColors: Record<ActivityItem["type"], string> = {
  user_created: "bg-status-info/15 text-status-info",
  payment_received: "bg-status-success/15 text-status-success",
  deployment_started: "bg-accent-subtle text-accent",
  alert: "bg-status-warning/15 text-status-warning",
  tenant_created: "bg-highlight-subtle text-highlight",
  settings_changed: "bg-surface-overlay text-text-muted",
};

export function RecentActivityFeed() {
  // In a real app, this would be fetched on the server or via React Query
  const activities: ActivityItem[] = [
    {
      id: "1",
      type: "user_created",
      title: "New user registered",
      description: "john.doe@acme.com joined Acme Corp",
      timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
      actor: { name: "System", email: "system@dotmac.io" },
    },
    {
      id: "2",
      type: "payment_received",
      title: "Payment received",
      description: "$2,500.00 from TechStart Inc",
      timestamp: new Date(Date.now() - 1000 * 60 * 12).toISOString(),
      actor: { name: "Stripe", email: "payments@stripe.com" },
    },
    {
      id: "3",
      type: "deployment_started",
      title: "Deployment started",
      description: "Production environment for Global Corp",
      timestamp: new Date(Date.now() - 1000 * 60 * 25).toISOString(),
      actor: { name: "Mike Chen", email: "mike@globalcorp.com" },
    },
    {
      id: "4",
      type: "alert",
      title: "High API latency detected",
      description: "Response times above threshold in us-east-1",
      timestamp: new Date(Date.now() - 1000 * 60 * 45).toISOString(),
    },
    {
      id: "5",
      type: "tenant_created",
      title: "New tenant onboarded",
      description: "StartupXYZ signed up for Professional plan",
      timestamp: new Date(Date.now() - 1000 * 60 * 60).toISOString(),
      actor: { name: "Sales Team", email: "sales@dotmac.io" },
    },
    {
      id: "6",
      type: "settings_changed",
      title: "Security settings updated",
      description: "MFA enforcement enabled for admin users",
      timestamp: new Date(Date.now() - 1000 * 60 * 90).toISOString(),
      actor: { name: "Admin", email: "admin@dotmac.io" },
    },
  ];

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
