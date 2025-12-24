/**
 * Bar Chart Component
 */

"use client";

import {
  BarChart as RechartsBarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from "recharts";

import { chartColors, chartTheme, getChartColor } from "./theme";

// ============================================================================
// Types
// ============================================================================

export interface BarChartDataPoint {
  [key: string]: string | number;
}

export interface BarChartSeries {
  dataKey: string;
  name?: string;
  color?: string;
  stackId?: string;
}

export interface BarChartProps {
  /** Data array */
  data: BarChartDataPoint[];
  /** X-axis data key */
  xAxisKey: string;
  /** Single data key (for simple charts) */
  dataKey?: string;
  /** Multiple series configuration */
  series?: BarChartSeries[];
  /** Chart height */
  height?: number;
  /** Show grid */
  showGrid?: boolean;
  /** Show legend */
  showLegend?: boolean;
  /** Show tooltip */
  showTooltip?: boolean;
  /** Horizontal bars */
  horizontal?: boolean;
  /** Stacked bars */
  stacked?: boolean;
  /** Bar color (for single dataKey) */
  color?: string;
  /** Color each bar differently */
  colorByValue?: boolean;
  /** Bar radius */
  barRadius?: number;
  /** Bar size (width) */
  barSize?: number;
  /** CSS class name */
  className?: string;
}

// ============================================================================
// Component
// ============================================================================

export function BarChart({
  data,
  xAxisKey,
  dataKey,
  series,
  height = 300,
  showGrid = true,
  showLegend = false,
  showTooltip = true,
  horizontal = false,
  stacked = false,
  color = chartColors.primary,
  colorByValue = false,
  barRadius = 4,
  barSize,
  className,
}: BarChartProps) {
  // Build series from dataKey or series prop
  const chartSeries: BarChartSeries[] = series ?? (dataKey ? [{ dataKey, color }] : []);

  // For stacked charts, assign same stackId
  const processedSeries = stacked
    ? chartSeries.map((s) => ({ ...s, stackId: s.stackId ?? "stack" }))
    : chartSeries;

  return (
    <div className={className} style={{ width: "100%", height }}>
      <ResponsiveContainer>
        <RechartsBarChart
          data={data}
          layout={horizontal ? "vertical" : "horizontal"}
          margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
        >
          {showGrid && (
            <CartesianGrid
              stroke={chartTheme.grid.stroke}
              strokeDasharray={chartTheme.grid.strokeDasharray}
              horizontal={!horizontal}
              vertical={horizontal}
            />
          )}

          {horizontal ? (
            <>
              <XAxis
                type="number"
                stroke={chartTheme.axis.stroke}
                tick={{ fill: chartTheme.axis.tick.fill, fontSize: chartTheme.axis.tick.fontSize }}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                type="category"
                dataKey={xAxisKey}
                stroke={chartTheme.axis.stroke}
                tick={{ fill: chartTheme.axis.tick.fill, fontSize: chartTheme.axis.tick.fontSize }}
                tickLine={false}
                axisLine={{ stroke: chartTheme.axis.stroke }}
                width={80}
              />
            </>
          ) : (
            <>
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
            </>
          )}

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
              cursor={{ fill: "rgba(0, 0, 0, 0.05)" }}
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

          {processedSeries.map((s, seriesIndex) => (
            <Bar
              key={s.dataKey}
              dataKey={s.dataKey}
              name={s.name ?? s.dataKey}
              fill={s.color ?? getChartColor(seriesIndex)}
              stackId={s.stackId}
              radius={[barRadius, barRadius, 0, 0]}
              barSize={barSize}
            >
              {colorByValue &&
                data.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={getChartColor(index)} />
                ))}
            </Bar>
          ))}
        </RechartsBarChart>
      </ResponsiveContainer>
    </div>
  );
}

export default BarChart;
