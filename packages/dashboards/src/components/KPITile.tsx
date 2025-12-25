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
  /** KPI description/subtitle */
  description?: string;
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
  description,
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
    if (previousValue === 0) {
      change = currentValue === 0 ? 0 : undefined;
    } else {
      change = ((currentValue - previousValue) / previousValue) * 100;
    }
  }

  const hasValidChange = typeof change === "number" && Number.isFinite(change);
  const changeText = hasValidChange ? Math.abs(change!).toFixed(1) : "";

  if (changeType === undefined && hasValidChange && change !== undefined) {
    if (change > 0) changeType = "increase";
    else if (change < 0) changeType = "decrease";
    else changeType = "neutral";
  }

  const changeColors = {
    increase: "text-success bg-success/10",
    decrease: "text-destructive bg-destructive/10",
    neutral: "text-muted-foreground bg-muted",
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
          "bg-card rounded-lg border border-border",
          compact ? "p-3" : "p-4",
          className
        )}
      >
        <div className="animate-pulse">
          <div className="h-4 w-24 bg-muted rounded mb-2" />
          <div className="h-8 w-32 bg-muted rounded mb-2" />
          <div className="h-4 w-20 bg-muted rounded" />
        </div>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "bg-card rounded-lg border border-border shadow-sm",
        compact ? "p-3" : "p-4",
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div>
          <span className="text-sm font-medium text-muted-foreground">{title}</span>
          {description && (
            <p className="text-xs text-muted-foreground/70 mt-0.5">{description}</p>
          )}
        </div>
        {icon && (
          <div className="p-2 rounded-lg bg-primary/10 text-primary">{icon}</div>
        )}
      </div>

      {/* Value */}
      <div className={cn("font-bold text-foreground", compact ? "text-xl" : "text-2xl")}>
        {value}
      </div>

      {/* Change Indicator */}
      {hasValidChange && changeType && (
        <div className="flex items-center gap-2 mt-2">
          <span
            className={cn(
              "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium",
              changeColors[changeType]
            )}
            aria-label={`${changeType === "increase" ? "Increased" : changeType === "decrease" ? "Decreased" : "No change"} by ${changeText} percent`}
          >
            {(() => {
              const Icon = ChangeIcon[changeType];
              return <Icon className="h-3 w-3" aria-hidden="true" />;
            })()}
            {changeText}%
          </span>
          {changeLabel && (
            <span className="text-xs text-muted-foreground">{changeLabel}</span>
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
