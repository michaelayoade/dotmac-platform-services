"use client";

import type { ElementType, ReactNode } from "react";
import { Inbox, Search, FileX, Users, Server, AlertCircle } from "lucide-react";
import { Button } from "@dotmac/core";
import { cn } from "@/lib/utils";

type EmptyStateVariant = "default" | "search" | "error" | "no-data" | "no-users" | "no-deployments";

interface EmptyStateProps {
  variant?: EmptyStateVariant;
  title?: string;
  description?: string;
  icon?: ElementType;
  action?: {
    label: string;
    onClick: () => void;
  };
  secondaryAction?: {
    label: string;
    onClick: () => void;
  };
  className?: string;
  children?: ReactNode;
}

const variantConfig: Record<
  EmptyStateVariant,
  {
    icon: ElementType;
    title: string;
    description: string;
  }
> = {
  default: {
    icon: Inbox,
    title: "No items yet",
    description: "Get started by creating your first item.",
  },
  search: {
    icon: Search,
    title: "No results found",
    description: "Try adjusting your search or filter criteria.",
  },
  error: {
    icon: AlertCircle,
    title: "Something went wrong",
    description: "We couldn't load the data. Please try again.",
  },
  "no-data": {
    icon: FileX,
    title: "No data available",
    description: "There's no data to display at the moment.",
  },
  "no-users": {
    icon: Users,
    title: "No users found",
    description: "Invite team members to get started.",
  },
  "no-deployments": {
    icon: Server,
    title: "No deployments",
    description: "Create your first deployment to get started.",
  },
};

export function EmptyState({
  variant = "default",
  title,
  description,
  icon,
  action,
  secondaryAction,
  className,
  children,
}: EmptyStateProps) {
  const config = variantConfig[variant];
  const Icon = icon || config.icon;
  const displayTitle = title || config.title;
  const displayDescription = description || config.description;

  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center py-16 px-4 text-center",
        className
      )}
    >
      {/* Icon */}
      <div className="w-16 h-16 rounded-full bg-surface-overlay flex items-center justify-center mb-6">
        <Icon className="w-8 h-8 text-text-muted" />
      </div>

      {/* Content */}
      <h3 className="text-lg font-semibold text-text-primary mb-2">
        {displayTitle}
      </h3>
      <p className="text-sm text-text-muted max-w-sm mb-6">
        {displayDescription}
      </p>

      {/* Actions */}
      {(action || secondaryAction) && (
        <div className="flex items-center gap-3">
          {secondaryAction && (
            <Button variant="outline" onClick={secondaryAction.onClick}>
              {secondaryAction.label}
            </Button>
          )}
          {action && (
            <Button onClick={action.onClick} className="shadow-glow-sm">
              {action.label}
            </Button>
          )}
        </div>
      )}

      {/* Custom content */}
      {children}
    </div>
  );
}
