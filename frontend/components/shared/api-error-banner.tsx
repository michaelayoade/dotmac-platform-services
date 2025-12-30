"use client";

import { AlertTriangle, RefreshCw } from "lucide-react";
import { Button } from "@/lib/dotmac/core";
import { cn } from "@/lib/utils";

interface APIErrorBannerProps {
  message?: string;
  onRetry?: () => void;
  isRetrying?: boolean;
}

/**
 * Banner to display when API calls fail
 * Shows a warning message with optional retry button
 */
export function APIErrorBanner({
  message = "Some data could not be loaded",
  onRetry,
  isRetrying = false,
}: APIErrorBannerProps) {
  return (
    <div
      role="alert"
      className="flex items-center gap-3 p-3 bg-status-warning/15 border border-status-warning/30 rounded-lg text-sm"
    >
      <AlertTriangle
        className="w-4 h-4 text-status-warning flex-shrink-0"
        aria-hidden="true"
      />
      <span className="text-text-primary flex-1">{message}</span>
      {onRetry && (
        <Button
          variant="outline"
          size="sm"
          onClick={onRetry}
          disabled={isRetrying}
          aria-label="Retry loading data"
        >
          <RefreshCw
            className={cn("w-3 h-3 mr-1", isRetrying && "animate-spin")}
            aria-hidden="true"
          />
          {isRetrying ? "Retrying..." : "Retry"}
        </Button>
      )}
    </div>
  );
}
