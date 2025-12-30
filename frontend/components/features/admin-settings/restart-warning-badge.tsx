"use client";

import { RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";

interface RestartWarningBadgeProps {
  className?: string;
}

export function RestartWarningBadge({ className }: RestartWarningBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 text-2xs px-2 py-0.5 rounded-full bg-warning-subtle text-warning",
        className
      )}
      title="Changing this setting requires a service restart to take effect"
    >
      <RefreshCw className="w-3 h-3" />
      Restart required
    </span>
  );
}
