/**
 * EmptyState Component
 *
 * Display when lists, tables, or grids have no data to show.
 */

"use client";

import { forwardRef } from "react";
import { cn } from "../utils/cn";

// ============================================================================
// Empty State Props
// ============================================================================

export interface EmptyStateProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Icon to display above the title */
  icon?: React.ReactNode;
  /** Main heading text */
  title: string;
  /** Optional description text */
  description?: string;
  /** Optional action button or link */
  action?: React.ReactNode;
  /** Size variant */
  size?: "sm" | "md" | "lg";
  /** Visual variant */
  variant?: "default" | "card" | "inline";
}

// ============================================================================
// Size Configuration
// ============================================================================

const sizeConfig = {
  sm: {
    container: "py-6",
    icon: "w-8 h-8",
    title: "text-sm font-medium",
    description: "text-xs",
    gap: "gap-2",
  },
  md: {
    container: "py-12",
    icon: "w-12 h-12",
    title: "text-lg font-semibold",
    description: "text-sm",
    gap: "gap-3",
  },
  lg: {
    container: "py-16",
    icon: "w-16 h-16",
    title: "text-xl font-semibold",
    description: "text-base",
    gap: "gap-4",
  },
};

const variantConfig = {
  default: "bg-transparent",
  card: "bg-surface-elevated border border-border rounded-lg",
  inline: "bg-surface-overlay rounded-md",
};

// ============================================================================
// EmptyState Component
// ============================================================================

export const EmptyState = forwardRef<HTMLDivElement, EmptyStateProps>(
  (
    {
      className,
      icon,
      title,
      description,
      action,
      size = "md",
      variant = "default",
      ...props
    },
    ref
  ) => {
    const sizes = sizeConfig[size];
    const variantClass = variantConfig[variant];

    return (
      <div
        ref={ref}
        className={cn(
          "flex flex-col items-center justify-center text-center",
          sizes.container,
          sizes.gap,
          variantClass,
          className
        )}
        role="status"
        aria-label={title}
        {...props}
      >
        {icon && (
          <div
            className={cn(
              "flex items-center justify-center text-text-muted",
              sizes.icon
            )}
            aria-hidden="true"
          >
            {icon}
          </div>
        )}
        <div className={cn("space-y-1", sizes.gap)}>
          <h3 className={cn("text-text-primary", sizes.title)}>{title}</h3>
          {description && (
            <p className={cn("text-text-muted max-w-sm mx-auto", sizes.description)}>
              {description}
            </p>
          )}
        </div>
        {action && <div className="mt-4">{action}</div>}
      </div>
    );
  }
);

EmptyState.displayName = "EmptyState";

export default EmptyState;
