/**
 * Line Chart Component
 */

"use client";

import {
  LineChart as RechartsLineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  type TooltipProps,
} from "recharts";

import { chartColors, chartTheme, getChartColor } from "./theme";

// ============================================================================
// Types
// ============================================================================

export interface LineChartDataPoint {
  [key: string]: string | number;
}

export interface LineChartSeries {
  dataKey: string;
  name?: string;
  color?: string;
  strokeWidth?: number;
  dashed?: boolean;
}

export interface LineChartProps {
  /** Data array */
  data: LineChartDataPoint[];
  /** X-axis data key */
  xAxisKey: string;
  /** Single data key (for simple charts) or series config */
  dataKey?: string;
  /** Multiple series configuration */
  series?: LineChartSeries[];
  /** Chart height */
  height?: number;
  /** Show grid */
  showGrid?: boolean;
  /** Show legend */
  showLegend?: boolean;
  /** Show tooltip */
  showTooltip?: boolean;
  /** Show dots on lines */
  showDots?: boolean;
  /** Curved lines */
  curved?: boolean;
  /** Line color (for single dataKey) */
  color?: string;
  /** Y-axis label */
  yAxisLabel?: string;
  /** X-axis label */
  xAxisLabel?: string;
  /** Custom tooltip formatter */
  tooltipFormatter?: (value: number, name: string) => string;
  /** Custom tooltip */
  customTooltip?: React.FC<TooltipProps<number, string>>;
  /** CSS class name */
  className?: string;
}

// ============================================================================
// Component
// ============================================================================

export function LineChart({
  data,
  xAxisKey,
  dataKey,
  series,
  height = 300,
  showGrid = true,
  showLegend = false,
  showTooltip = true,
  showDots = true,
  curved = true,
  color = chartColors.primary,
  yAxisLabel,
  xAxisLabel,
  tooltipFormatter,
  customTooltip,
  className,
}: LineChartProps) {
  // Build series from dataKey or series prop
  const chartSeries: LineChartSeries[] = series ?? (dataKey ? [{ dataKey, color }] : []);

  return (
    <div className={className} style={{ width: "100%", height }}>
      <ResponsiveContainer>
        <RechartsLineChart
          data={data}
          margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
        >
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
            label={xAxisLabel ? { value: xAxisLabel, position: "bottom", offset: -5 } : undefined}
          />

          <YAxis
            stroke={chartTheme.axis.stroke}
            tick={{ fill: chartTheme.axis.tick.fill, fontSize: chartTheme.axis.tick.fontSize }}
            tickLine={false}
            axisLine={false}
            label={
              yAxisLabel
                ? { value: yAxisLabel, angle: -90, position: "insideLeft", offset: 10 }
                : undefined
            }
          />

          {showTooltip && (
            <Tooltip
              content={customTooltip as any}
              formatter={tooltipFormatter}
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

          {chartSeries.map((s, index) => (
            <Line
              key={s.dataKey}
              type={curved ? "monotone" : "linear"}
              dataKey={s.dataKey}
              name={s.name ?? s.dataKey}
              stroke={s.color ?? getChartColor(index)}
              strokeWidth={s.strokeWidth ?? 2}
              strokeDasharray={s.dashed ? "5 5" : undefined}
              dot={showDots ? { r: 4, fill: s.color ?? getChartColor(index) } : false}
              activeDot={showDots ? { r: 6 } : false}
            />
          ))}
        </RechartsLineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default LineChart;
