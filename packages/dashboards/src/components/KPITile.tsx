/**
 * KPI Tile Component
 *
 * Display key performance indicators with trend indicators
 */

"use client";

import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { type ReactNode } from "react";

import { cn } from "../utils/cn";

// ============================================================================
// Types
// ============================================================================

export interface KPITileProps {
  /** KPI title/label */
  title: string;
  /** KPI value */
  value: string | number;
  /** Previous value for comparison */
  previousValue?: number;
  /** Current value as number (for change calculation) */
  currentValue?: number;
  /** Change percentage (alternative to calculating from values) */
  change?: number;
  /** Change type */
  changeType?: "increase" | "decrease" | "neutral";
  /** Change label (e.g., "vs last month") */
  changeLabel?: string;
  /** Icon */
  icon?: ReactNode;
  /** Format for value display */
  format?: "number" | "currency" | "percent";
  /** Currency code for currency format */
  currency?: string;
  /** Loading state */
  loading?: boolean;
  /** Sparkline data */
  sparkline?: number[];
  /** CSS class name */
  className?: string;
  /** Compact mode */
  compact?: boolean;
}

// ============================================================================
// Component
// ============================================================================

export function KPITile({
  title,
  value,
  previousValue,
  currentValue,
  change: providedChange,
  changeType: providedChangeType,
  changeLabel,
  icon,
  loading = false,
  className,
  compact = false,
}: KPITileProps) {
  // Calculate change if not provided
  let change = providedChange;
  let changeType = providedChangeType;

  if (change === undefined && previousValue !== undefined && currentValue !== undefined) {
    change = ((currentValue - previousValue) / previousValue) * 100;
  }

  if (changeType === undefined && change !== undefined) {
    if (change > 0) changeType = "increase";
    else if (change < 0) changeType = "decrease";
    else changeType = "neutral";
  }

  const changeColors = {
    increase: "text-green-600 bg-green-50",
    decrease: "text-red-600 bg-red-50",
    neutral: "text-gray-600 bg-gray-50",
  };

  const ChangeIcon = {
    increase: TrendingUp,
    decrease: TrendingDown,
    neutral: Minus,
  };

  if (loading) {
    return (
      <div
        className={cn(
          "bg-white rounded-lg border border-gray-200 p-4",
          compact ? "p-3" : "p-4",
          className
        )}
      >
        <div className="animate-pulse">
          <div className="h-4 w-24 bg-gray-200 rounded mb-2" />
          <div className="h-8 w-32 bg-gray-200 rounded mb-2" />
          <div className="h-4 w-20 bg-gray-200 rounded" />
        </div>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "bg-white rounded-lg border border-gray-200 shadow-sm",
        compact ? "p-3" : "p-4",
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-gray-500">{title}</span>
        {icon && (
          <div className="p-2 rounded-lg bg-blue-50 text-blue-600">{icon}</div>
        )}
      </div>

      {/* Value */}
      <div className={cn("font-bold text-gray-900", compact ? "text-xl" : "text-2xl")}>
        {value}
      </div>

      {/* Change Indicator */}
      {change !== undefined && changeType && (
        <div className="flex items-center gap-2 mt-2">
          <span
            className={cn(
              "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium",
              changeColors[changeType]
            )}
          >
            {(() => {
              const Icon = ChangeIcon[changeType];
              return <Icon className="h-3 w-3" />;
            })()}
            {Math.abs(change).toFixed(1)}%
          </span>
          {changeLabel && (
            <span className="text-xs text-gray-500">{changeLabel}</span>
          )}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// KPI Grid
// ============================================================================

export interface KPIGridProps {
  children: ReactNode;
  columns?: 2 | 3 | 4 | 5 | 6;
  className?: string;
}

export function KPIGrid({ children, columns = 4, className }: KPIGridProps) {
  const gridCols = {
    2: "grid-cols-1 sm:grid-cols-2",
    3: "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3",
    4: "grid-cols-1 sm:grid-cols-2 lg:grid-cols-4",
    5: "grid-cols-1 sm:grid-cols-2 lg:grid-cols-5",
    6: "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6",
  };

  return (
    <div className={cn("grid gap-4", gridCols[columns], className)}>
      {children}
    </div>
  );
}

export default KPITile;
