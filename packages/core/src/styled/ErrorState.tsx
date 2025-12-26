/**
 * ErrorState Component
 *
 * Display when data fetching fails or an error occurs.
 * Includes optional retry functionality.
 */

"use client";

import { forwardRef } from "react";
import { cn } from "../utils/cn";

// ============================================================================
// Error State Props
// ============================================================================

export interface ErrorStateProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Custom icon (defaults to alert circle) */
  icon?: React.ReactNode;
  /** Error title */
  title?: string;
  /** Error description or message */
  description?: string;
  /** Retry callback - if provided, shows retry button */
  onRetry?: () => void;
  /** Custom retry button text */
  retryText?: string;
  /** Whether retry is in progress */
  isRetrying?: boolean;
  /** Size variant */
  size?: "sm" | "md" | "lg";
  /** Visual variant */
  variant?: "default" | "card" | "inline" | "destructive";
}

// ============================================================================
// Default Alert Icon
// ============================================================================

const AlertCircleIcon = ({ className }: { className?: string }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
    aria-hidden="true"
  >
    <circle cx="12" cy="12" r="10" />
    <line x1="12" y1="8" x2="12" y2="12" />
    <line x1="12" y1="16" x2="12.01" y2="16" />
  </svg>
);

const RefreshIcon = ({ className }: { className?: string }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
    aria-hidden="true"
  >
    <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
    <path d="M3 3v5h5" />
    <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16" />
    <path d="M16 16h5v5" />
  </svg>
);

// ============================================================================
// Size Configuration
// ============================================================================

const sizeConfig = {
  sm: {
    container: "py-4 px-4",
    icon: "w-6 h-6",
    title: "text-sm font-medium",
    description: "text-xs",
    button: "text-xs px-3 py-1.5",
    gap: "gap-2",
  },
  md: {
    container: "py-8 px-6",
    icon: "w-10 h-10",
    title: "text-base font-semibold",
    description: "text-sm",
    button: "text-sm px-4 py-2",
    gap: "gap-3",
  },
  lg: {
    container: "py-12 px-8",
    icon: "w-14 h-14",
    title: "text-lg font-semibold",
    description: "text-base",
    button: "text-base px-5 py-2.5",
    gap: "gap-4",
  },
};

const variantConfig = {
  default: {
    container: "bg-transparent",
    icon: "text-status-error",
    text: "text-text-primary",
    description: "text-text-muted",
  },
  card: {
    container: "bg-card border border-border rounded-lg",
    icon: "text-status-error",
    text: "text-text-primary",
    description: "text-text-muted",
  },
  inline: {
    container: "bg-status-error/5 border border-status-error/20 rounded-md",
    icon: "text-status-error",
    text: "text-status-error",
    description: "text-status-error/80",
  },
  destructive: {
    container: "bg-status-error/10 border border-status-error/30 rounded-lg",
    icon: "text-status-error",
    text: "text-status-error",
    description: "text-status-error/80",
  },
};

// ============================================================================
// ErrorState Component
// ============================================================================

export const ErrorState = forwardRef<HTMLDivElement, ErrorStateProps>(
  (
    {
      className,
      icon,
      title = "Something went wrong",
      description,
      onRetry,
      retryText = "Try again",
      isRetrying = false,
      size = "md",
      variant = "default",
      ...props
    },
    ref
  ) => {
    const sizes = sizeConfig[size];
    const variantStyles = variantConfig[variant];

    return (
      <div
        ref={ref}
        className={cn(
          "flex flex-col items-center justify-center text-center",
          sizes.container,
          sizes.gap,
          variantStyles.container,
          className
        )}
        role="alert"
        aria-live="polite"
        {...props}
      >
        <div className={cn(variantStyles.icon, sizes.icon)}>
          {icon || <AlertCircleIcon className="w-full h-full" />}
        </div>

        <div className={cn("space-y-1", sizes.gap)}>
          <h3 className={cn(variantStyles.text, sizes.title)}>{title}</h3>
          {description && (
            <p className={cn(variantStyles.description, sizes.description, "max-w-sm mx-auto")}>
              {description}
            </p>
          )}
        </div>

        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            disabled={isRetrying}
            className={cn(
              "inline-flex items-center justify-center gap-2 rounded-md font-medium",
              "bg-surface-elevated border border-border",
              "hover:bg-surface-overlay",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              "transition-colors",
              sizes.button
            )}
          >
            <RefreshIcon
              className={cn("w-4 h-4", isRetrying && "animate-spin")}
            />
            {isRetrying ? "Retrying..." : retryText}
          </button>
        )}
      </div>
    );
  }
);

ErrorState.displayName = "ErrorState";

export default ErrorState;
