/**
 * StatusBadge Component
 *
 * Consistent status indicator badges for use across the application.
 */

"use client";

import { forwardRef } from "react";
import { cn } from "../utils/cn";

// ============================================================================
// Status Badge Props
// ============================================================================

export type StatusVariant =
  | "success"
  | "error"
  | "warning"
  | "info"
  | "neutral"
  | "primary"
  | "secondary";

export type StatusSize = "xs" | "sm" | "md" | "lg";

export interface StatusBadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  /** Status variant determines the color scheme */
  variant?: StatusVariant;
  /** Size of the badge */
  size?: StatusSize;
  /** Whether to show a dot indicator */
  dot?: boolean;
  /** Whether to show a pulsing animation (for live/active states) */
  pulse?: boolean;
  /** Optional icon to show before the text */
  icon?: React.ReactNode;
  /** Badge content */
  children: React.ReactNode;
}

// ============================================================================
// Variant Configuration
// ============================================================================

const variantConfig: Record<
  StatusVariant,
  { bg: string; text: string; dot: string; border: string }
> = {
  success: {
    bg: "bg-status-success/15",
    text: "text-status-success",
    dot: "bg-status-success",
    border: "border-status-success/30",
  },
  error: {
    bg: "bg-status-error/15",
    text: "text-status-error",
    dot: "bg-status-error",
    border: "border-status-error/30",
  },
  warning: {
    bg: "bg-status-warning/15",
    text: "text-status-warning",
    dot: "bg-status-warning",
    border: "border-status-warning/30",
  },
  info: {
    bg: "bg-status-info/15",
    text: "text-status-info",
    dot: "bg-status-info",
    border: "border-status-info/30",
  },
  neutral: {
    bg: "bg-text-muted/15",
    text: "text-text-muted",
    dot: "bg-text-muted",
    border: "border-text-muted/30",
  },
  primary: {
    bg: "bg-accent/15",
    text: "text-accent",
    dot: "bg-accent",
    border: "border-accent/30",
  },
  secondary: {
    bg: "bg-highlight/15",
    text: "text-highlight",
    dot: "bg-highlight",
    border: "border-highlight/30",
  },
};

const sizeConfig: Record<
  StatusSize,
  { padding: string; text: string; dot: string; iconSize: string }
> = {
  xs: {
    padding: "px-1.5 py-0.5",
    text: "text-[10px] leading-tight",
    dot: "w-1 h-1",
    iconSize: "w-2.5 h-2.5",
  },
  sm: {
    padding: "px-2 py-0.5",
    text: "text-xs",
    dot: "w-1.5 h-1.5",
    iconSize: "w-3 h-3",
  },
  md: {
    padding: "px-2.5 py-1",
    text: "text-sm",
    dot: "w-2 h-2",
    iconSize: "w-4 h-4",
  },
  lg: {
    padding: "px-3 py-1.5",
    text: "text-base",
    dot: "w-2.5 h-2.5",
    iconSize: "w-5 h-5",
  },
};

// ============================================================================
// StatusBadge Component
// ============================================================================

export const StatusBadge = forwardRef<HTMLSpanElement, StatusBadgeProps>(
  (
    {
      className,
      variant = "neutral",
      size = "sm",
      dot = false,
      pulse = false,
      icon,
      children,
      ...props
    },
    ref
  ) => {
    const variantStyles = variantConfig[variant];
    const sizeStyles = sizeConfig[size];

    return (
      <span
        ref={ref}
        role="status"
        className={cn(
          "inline-flex items-center gap-1.5 rounded-full font-medium border",
          variantStyles.bg,
          variantStyles.text,
          variantStyles.border,
          sizeStyles.padding,
          sizeStyles.text,
          className
        )}
        {...props}
      >
        {dot && (
          <span className="relative flex">
            <span
              className={cn(
                "rounded-full",
                variantStyles.dot,
                sizeStyles.dot
              )}
            />
            {pulse && (
              <span
                className={cn(
                  "absolute inline-flex h-full w-full rounded-full opacity-75 animate-ping",
                  variantStyles.dot
                )}
              />
            )}
          </span>
        )}
        {icon && (
          <span className={cn("flex-shrink-0", sizeStyles.iconSize)}>
            {icon}
          </span>
        )}
        {children}
      </span>
    );
  }
);

StatusBadge.displayName = "StatusBadge";

// ============================================================================
// Preset Status Badges for Common Use Cases
// ============================================================================

export interface PresetStatusBadgeProps
  extends Omit<StatusBadgeProps, "variant" | "children"> {
  children?: React.ReactNode;
}

/** Active/Online status badge */
export const ActiveBadge = forwardRef<HTMLSpanElement, PresetStatusBadgeProps>(
  ({ children = "Active", dot = true, pulse = true, ...props }, ref) => (
    <StatusBadge ref={ref} variant="success" dot={dot} pulse={pulse} {...props}>
      {children}
    </StatusBadge>
  )
);
ActiveBadge.displayName = "ActiveBadge";

/** Inactive/Offline status badge */
export const InactiveBadge = forwardRef<HTMLSpanElement, PresetStatusBadgeProps>(
  ({ children = "Inactive", dot = true, ...props }, ref) => (
    <StatusBadge ref={ref} variant="neutral" dot={dot} {...props}>
      {children}
    </StatusBadge>
  )
);
InactiveBadge.displayName = "InactiveBadge";

/** Pending/Processing status badge */
export const PendingBadge = forwardRef<HTMLSpanElement, PresetStatusBadgeProps>(
  ({ children = "Pending", dot = true, pulse = true, ...props }, ref) => (
    <StatusBadge ref={ref} variant="warning" dot={dot} pulse={pulse} {...props}>
      {children}
    </StatusBadge>
  )
);
PendingBadge.displayName = "PendingBadge";

/** Error/Failed status badge */
export const ErrorBadge = forwardRef<HTMLSpanElement, PresetStatusBadgeProps>(
  ({ children = "Error", dot = true, ...props }, ref) => (
    <StatusBadge ref={ref} variant="error" dot={dot} {...props}>
      {children}
    </StatusBadge>
  )
);
ErrorBadge.displayName = "ErrorBadge";

export default StatusBadge;
