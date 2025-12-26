"use client";

import type { ElementType } from "react";
import {
  CheckCircle,
  Clock,
  AlertTriangle,
  XCircle,
  Pause,
  RefreshCw,
  Info,
} from "lucide-react";
import { cn } from "@/lib/utils";

type StatusVariant =
  | "success"
  | "warning"
  | "error"
  | "info"
  | "pending"
  | "inactive"
  | "processing";

interface StatusBadgeProps {
  status: StatusVariant;
  label?: string;
  showIcon?: boolean;
  size?: "sm" | "md";
  pulse?: boolean;
  className?: string;
}

const statusConfig: Record<
  StatusVariant,
  {
    class: string;
    icon: ElementType;
    defaultLabel: string;
  }
> = {
  success: {
    class: "bg-status-success/15 text-status-success",
    icon: CheckCircle,
    defaultLabel: "Active",
  },
  warning: {
    class: "bg-status-warning/15 text-status-warning",
    icon: AlertTriangle,
    defaultLabel: "Warning",
  },
  error: {
    class: "bg-status-error/15 text-status-error",
    icon: XCircle,
    defaultLabel: "Error",
  },
  info: {
    class: "bg-status-info/15 text-status-info",
    icon: Info,
    defaultLabel: "Info",
  },
  pending: {
    class: "bg-status-warning/15 text-status-warning",
    icon: Clock,
    defaultLabel: "Pending",
  },
  inactive: {
    class: "bg-surface-overlay text-text-muted",
    icon: Pause,
    defaultLabel: "Inactive",
  },
  processing: {
    class: "bg-status-info/15 text-status-info",
    icon: RefreshCw,
    defaultLabel: "Processing",
  },
};

export function StatusBadge({
  status,
  label,
  showIcon = true,
  size = "sm",
  pulse = false,
  className,
}: StatusBadgeProps) {
  const config = statusConfig[status];
  const Icon = config.icon;
  const displayLabel = label || config.defaultLabel;

  const sizeClasses = {
    sm: "px-2 py-0.5 text-2xs",
    md: "px-2.5 py-1 text-xs",
  };

  return (
    <span
      role="status"
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full font-semibold uppercase tracking-wider",
        config.class,
        sizeClasses[size],
        className
      )}
    >
      {showIcon && (
        <Icon
          className={cn(
            size === "sm" ? "w-3 h-3" : "w-3.5 h-3.5",
            status === "processing" && "animate-spin",
            pulse && "animate-pulse"
          )}
        />
      )}
      {displayLabel}
    </span>
  );
}

// Convenience components for common statuses
export function ActiveBadge({ label = "Active" }: { label?: string }) {
  return <StatusBadge status="success" label={label} />;
}

export function PendingBadge({ label = "Pending" }: { label?: string }) {
  return <StatusBadge status="pending" label={label} />;
}

export function ErrorBadge({ label = "Error" }: { label?: string }) {
  return <StatusBadge status="error" label={label} />;
}

export function ProcessingBadge({ label = "Processing" }: { label?: string }) {
  return <StatusBadge status="processing" label={label} />;
}
