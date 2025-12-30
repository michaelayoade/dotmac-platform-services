/**
 * Sparkline Component
 *
 * Minimal inline chart for displaying trends in tables and compact spaces
 */

"use client";

import {
  LineChart,
  Line,
  ResponsiveContainer,
  ReferenceArea,
} from "recharts";

import { chartColors, getChartColor } from "./theme";

// ============================================================================
// Types
// ============================================================================

export interface SparklineDataPoint {
  value: number;
  [key: string]: unknown;
}

export interface SparklineProps {
  /** Data array with value property */
  data: SparklineDataPoint[];
  /** Data key for the value */
  dataKey?: string;
  /** Width of sparkline */
  width?: number | string;
  /** Height of sparkline */
  height?: number;
  /** Line color */
  color?: string;
  /** Show area fill under line */
  showArea?: boolean;
  /** Area fill opacity */
  areaOpacity?: number;
  /** Stroke width */
  strokeWidth?: number;
  /** Variant for automatic coloring based on trend */
  variant?: "default" | "positive" | "negative" | "trend";
  /** Show reference line at value */
  referenceLine?: number;
  /** Show dots on data points */
  showDots?: boolean;
  /** Animate on mount */
  animate?: boolean;
  /** CSS class */
  className?: string;
}

// ============================================================================
// Component
// ============================================================================

export function Sparkline({
  data,
  dataKey = "value",
  width = "100%",
  height = 24,
  color,
  showArea = false,
  areaOpacity = 0.1,
  strokeWidth = 1.5,
  variant = "default",
  referenceLine,
  showDots = false,
  animate = true,
  className,
}: SparklineProps) {
  // Determine color based on variant
  const getVariantColor = () => {
    if (color) return color;

    switch (variant) {
      case "positive":
        return chartColors.success;
      case "negative":
        return chartColors.error;
      case "trend": {
        // Compare first and last values
        if (data.length < 2) return chartColors.primary;
        const first = data[0]?.[dataKey] as number ?? 0;
        const last = data[data.length - 1]?.[dataKey] as number ?? 0;
        return last >= first ? chartColors.success : chartColors.error;
      }
      default:
        return chartColors.primary;
    }
  };

  const lineColor = getVariantColor();

  if (!data || data.length === 0) {
    return (
      <div
        className={className}
        style={{
          width: typeof width === "number" ? width : undefined,
          height,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <span style={{ color: "var(--text-muted)", fontSize: 10 }}>—</span>
      </div>
    );
  }

  return (
    <div
      className={className}
      style={{
        width: typeof width === "number" ? width : undefined,
        height,
      }}
    >
      <ResponsiveContainer width={width} height={height}>
        <LineChart
          data={data}
          margin={{ top: 2, right: 2, left: 2, bottom: 2 }}
        >
          {/* Reference area for threshold visualization */}
          {referenceLine !== undefined && (
            <ReferenceArea
              y1={0}
              y2={referenceLine}
              fill={chartColors.success}
              fillOpacity={0.05}
            />
          )}

          {/* Area fill */}
          {showArea && (
            <defs>
              <linearGradient id={`sparkline-gradient-${lineColor.replace("#", "")}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={lineColor} stopOpacity={areaOpacity * 2} />
                <stop offset="100%" stopColor={lineColor} stopOpacity={0} />
              </linearGradient>
            </defs>
          )}

          <Line
            type="monotone"
            dataKey={dataKey}
            stroke={lineColor}
            strokeWidth={strokeWidth}
            fill={showArea ? `url(#sparkline-gradient-${lineColor.replace("#", "")})` : "none"}
            dot={showDots ? { r: 2, fill: lineColor } : false}
            activeDot={false}
            isAnimationActive={animate}
            animationDuration={500}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

// ============================================================================
// Sparkline Variants
// ============================================================================

/** Positive trend sparkline (green) */
export function PositiveSparkline(props: Omit<SparklineProps, "variant">) {
  return <Sparkline {...props} variant="positive" />;
}

/** Negative trend sparkline (red) */
export function NegativeSparkline(props: Omit<SparklineProps, "variant">) {
  return <Sparkline {...props} variant="negative" />;
}

/** Auto-coloring sparkline based on first/last value comparison */
export function TrendSparkline(props: Omit<SparklineProps, "variant">) {
  return <Sparkline {...props} variant="trend" />;
}

export default Sparkline;
