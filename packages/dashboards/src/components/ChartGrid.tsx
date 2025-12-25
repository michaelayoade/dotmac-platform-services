/**
 * Chart Grid Component
 *
 * Responsive grid layout for charts
 */

"use client";

import { type ReactNode } from "react";

import { cn } from "../utils/cn";

// ============================================================================
// Types
// ============================================================================

export interface ChartGridProps {
  children: ReactNode;
  columns?: 1 | 2 | 3;
  gap?: "sm" | "md" | "lg";
  className?: string;
}

export interface ChartCardProps {
  /** Chart title */
  title?: string;
  /** Chart subtitle */
  subtitle?: string;
  /** Chart description (alias for subtitle) */
  description?: string;
  /** Chart content */
  children: ReactNode;
  /** Card actions */
  actions?: ReactNode;
  /** Card action (alias for actions) */
  action?: ReactNode;
  /** Card spans full width */
  fullWidth?: boolean;
  /** Card height */
  height?: string | number;
  /** Loading state */
  loading?: boolean;
  /** CSS class name */
  className?: string;
}

// ============================================================================
// Chart Grid
// ============================================================================

export function ChartGrid({
  children,
  columns = 2,
  gap = "md",
  className,
}: ChartGridProps) {
  const columnClasses = {
    1: "grid-cols-1",
    2: "grid-cols-1 lg:grid-cols-2",
    3: "grid-cols-1 md:grid-cols-2 lg:grid-cols-3",
  };

  const gapClasses = {
    sm: "gap-3",
    md: "gap-4",
    lg: "gap-6",
  };

  return (
    <div
      className={cn("grid", columnClasses[columns], gapClasses[gap], className)}
    >
      {children}
    </div>
  );
}

// ============================================================================
// Chart Card
// ============================================================================

export function ChartCard({
  title,
  subtitle,
  description,
  children,
  actions,
  action,
  fullWidth = false,
  height = 300,
  loading = false,
  className,
}: ChartCardProps) {
  // Support alias props
  const displaySubtitle = subtitle ?? description;
  const displayActions = actions ?? action;
  return (
    <div
      className={cn(
        "bg-white rounded-lg border border-gray-200 shadow-sm",
        fullWidth && "lg:col-span-2",
        className
      )}
    >
      {/* Header */}
      {(title || displayActions) && (
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
          <div>
            {title && (
              <h3 className="text-sm font-semibold text-gray-900">{title}</h3>
            )}
            {displaySubtitle && (
              <p className="text-xs text-gray-500 mt-0.5">{displaySubtitle}</p>
            )}
          </div>
          {displayActions && <div className="flex items-center gap-2">{displayActions}</div>}
        </div>
      )}

      {/* Content */}
      <div
        className="p-4"
        style={{ height: typeof height === "number" ? `${height}px` : height }}
      >
        {loading ? (
          <div className="h-full flex items-center justify-center">
            <div className="animate-pulse flex flex-col items-center gap-2">
              <div className="h-8 w-8 border-4 border-gray-200 border-t-blue-500 rounded-full animate-spin" />
              <span className="text-sm text-gray-500">Loading chart...</span>
            </div>
          </div>
        ) : (
          children
        )}
      </div>
    </div>
  );
}

export default ChartGrid;
