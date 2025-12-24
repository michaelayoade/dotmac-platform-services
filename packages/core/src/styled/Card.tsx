/**
 * Styled Card
 *
 * Pre-styled card component with DotMac design system
 */

"use client";

import { forwardRef } from "react";

import {
  Card as CardPrimitive,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
  cardVariants,
  type CardProps,
} from "../primitives/Card";
import { cn } from "../utils/cn";

// ============================================================================
// Styled Card Component
// ============================================================================

export const StyledCard = forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant = "default", ...props }, ref) => {
    return (
      <CardPrimitive
        ref={ref}
        variant={variant}
        className={cn(
          "bg-card text-card-foreground border-border",
          className
        )}
        {...props}
      />
    );
  }
);

StyledCard.displayName = "StyledCard";

// ============================================================================
// Metric Card (for dashboards)
// ============================================================================

export interface MetricCardProps extends CardProps {
  title: string;
  value: string | number;
  change?: {
    value: number;
    type: "increase" | "decrease" | "neutral";
  };
  icon?: React.ReactNode;
  trend?: React.ReactNode;
  footer?: React.ReactNode;
}

export const MetricCard = forwardRef<HTMLDivElement, MetricCardProps>(
  ({ className, title, value, change, icon, trend, footer, ...props }, ref) => {
    const changeColors = {
      increase: "text-green-600",
      decrease: "text-red-600",
      neutral: "text-gray-600",
    };

    return (
      <StyledCard ref={ref} className={cn("", className)} {...props}>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-sm font-medium text-muted-foreground">{title}</p>
              <p className="text-2xl font-bold">{value}</p>
            </div>
            {icon && (
              <div className="rounded-full bg-primary/10 p-3 text-primary">
                {icon}
              </div>
            )}
          </div>

          {(change || trend) && (
            <div className="mt-4 flex items-center gap-2">
              {change && (
                <span className={cn("text-sm font-medium", changeColors[change.type])}>
                  {change.type === "increase" ? "+" : change.type === "decrease" ? "-" : ""}
                  {Math.abs(change.value)}%
                </span>
              )}
              {trend && <span className="text-sm text-muted-foreground">{trend}</span>}
            </div>
          )}
        </CardContent>
        {footer && <CardFooter className="border-t pt-4">{footer}</CardFooter>}
      </StyledCard>
    );
  }
);

MetricCard.displayName = "MetricCard";

// ============================================================================
// Status Card
// ============================================================================

export interface StatusCardProps extends CardProps {
  title: string;
  status: "online" | "offline" | "degraded" | "maintenance" | "unknown";
  description?: string;
  lastUpdated?: string;
}

const statusConfig = {
  online: { color: "bg-green-500", label: "Online" },
  offline: { color: "bg-red-500", label: "Offline" },
  degraded: { color: "bg-yellow-500", label: "Degraded" },
  maintenance: { color: "bg-purple-500", label: "Maintenance" },
  unknown: { color: "bg-gray-500", label: "Unknown" },
};

export const StatusCard = forwardRef<HTMLDivElement, StatusCardProps>(
  ({ className, title, status, description, lastUpdated, ...props }, ref) => {
    const config = statusConfig[status];

    return (
      <StyledCard ref={ref} className={cn("", className)} {...props}>
        <CardHeader>
          <div className="flex items-center gap-3">
            <span
              className={cn("h-3 w-3 rounded-full", config.color)}
              aria-hidden="true"
            />
            <CardTitle className="text-base">{title}</CardTitle>
          </div>
          <CardDescription>{config.label}</CardDescription>
        </CardHeader>
        {(description || lastUpdated) && (
          <CardContent>
            {description && (
              <p className="text-sm text-muted-foreground">{description}</p>
            )}
            {lastUpdated && (
              <p className="mt-2 text-xs text-muted-foreground">
                Last updated: {lastUpdated}
              </p>
            )}
          </CardContent>
        )}
      </StyledCard>
    );
  }
);

StatusCard.displayName = "StatusCard";

// Re-export primitives for convenience
export {
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
  cardVariants,
};
export type { CardProps };
export default StyledCard;
