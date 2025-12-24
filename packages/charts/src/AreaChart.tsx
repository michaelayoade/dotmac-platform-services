/**
 * Area Chart Component
 */

"use client";

import {
  AreaChart as RechartsAreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

import { chartColors, chartTheme, getChartColor } from "./theme";

// ============================================================================
// Types
// ============================================================================

export interface AreaChartDataPoint {
  [key: string]: string | number;
}

export interface AreaChartSeries {
  dataKey: string;
  name?: string;
  color?: string;
  fillOpacity?: number;
  stackId?: string;
}

export interface AreaChartProps {
  /** Data array */
  data: AreaChartDataPoint[];
  /** X-axis data key */
  xAxisKey: string;
  /** Single data key (for simple charts) */
  dataKey?: string;
  /** Multiple series configuration */
  series?: AreaChartSeries[];
  /** Chart height */
  height?: number;
  /** Show grid */
  showGrid?: boolean;
  /** Show legend */
  showLegend?: boolean;
  /** Show tooltip */
  showTooltip?: boolean;
  /** Curved lines */
  curved?: boolean;
  /** Stacked areas */
  stacked?: boolean;
  /** Area color (for single dataKey) */
  color?: string;
  /** Fill opacity */
  fillOpacity?: number;
  /** Use gradient fill */
  gradient?: boolean;
  /** CSS class name */
  className?: string;
}

// ============================================================================
// Component
// ============================================================================

export function AreaChart({
  data,
  xAxisKey,
  dataKey,
  series,
  height = 300,
  showGrid = true,
  showLegend = false,
  showTooltip = true,
  curved = true,
  stacked = false,
  color = chartColors.primary,
  fillOpacity = 0.3,
  gradient = true,
  className,
}: AreaChartProps) {
  // Build series from dataKey or series prop
  const chartSeries: AreaChartSeries[] = series ?? (dataKey ? [{ dataKey, color }] : []);

  // For stacked charts, assign same stackId
  const processedSeries = stacked
    ? chartSeries.map((s) => ({ ...s, stackId: s.stackId ?? "stack" }))
    : chartSeries;

  return (
    <div className={className} style={{ width: "100%", height }}>
      <ResponsiveContainer>
        <RechartsAreaChart
          data={data}
          margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
        >
          {/* Gradient definitions */}
          {gradient && (
            <defs>
              {processedSeries.map((s, index) => {
                const seriesColor = s.color ?? getChartColor(index);
                return (
                  <linearGradient
                    key={`gradient-${s.dataKey}`}
                    id={`gradient-${s.dataKey}`}
                    x1="0"
                    y1="0"
                    x2="0"
                    y2="1"
                  >
                    <stop offset="5%" stopColor={seriesColor} stopOpacity={0.8} />
                    <stop offset="95%" stopColor={seriesColor} stopOpacity={0.1} />
                  </linearGradient>
                );
              })}
            </defs>
          )}

          {showGrid && (
            <CartesianGrid
              stroke={chartTheme.grid.stroke}
              strokeDasharray={chartTheme.grid.strokeDasharray}
              vertical={false}
            />
          )}

          <XAxis
            dataKey={xAxisKey}
            stroke={chartTheme.axis.stroke}
            tick={{ fill: chartTheme.axis.tick.fill, fontSize: chartTheme.axis.tick.fontSize }}
            tickLine={false}
            axisLine={{ stroke: chartTheme.axis.stroke }}
          />

          <YAxis
            stroke={chartTheme.axis.stroke}
            tick={{ fill: chartTheme.axis.tick.fill, fontSize: chartTheme.axis.tick.fontSize }}
            tickLine={false}
            axisLine={false}
          />

          {showTooltip && (
            <Tooltip
              contentStyle={{
                backgroundColor: chartTheme.tooltip.background,
                border: `1px solid ${chartTheme.tooltip.border}`,
                borderRadius: chartTheme.tooltip.borderRadius,
                padding: chartTheme.tooltip.padding,
                boxShadow: chartTheme.tooltip.shadow,
              }}
              labelStyle={{ color: chartTheme.tooltip.text, fontWeight: 600 }}
              itemStyle={{ color: chartTheme.tooltip.text }}
            />
          )}

          {showLegend && (
            <Legend
              wrapperStyle={{
                fontSize: chartTheme.legend.fontSize,
                color: chartTheme.legend.text,
              }}
            />
          )}

          {processedSeries.map((s, index) => {
            const seriesColor = s.color ?? getChartColor(index);
            return (
              <Area
                key={s.dataKey}
                type={curved ? "monotone" : "linear"}
                dataKey={s.dataKey}
                name={s.name ?? s.dataKey}
                stroke={seriesColor}
                strokeWidth={2}
                fill={gradient ? `url(#gradient-${s.dataKey})` : seriesColor}
                fillOpacity={gradient ? 1 : s.fillOpacity ?? fillOpacity}
                stackId={s.stackId}
              />
            );
          })}
        </RechartsAreaChart>
      </ResponsiveContainer>
    </div>
  );
}

export default AreaChart;
