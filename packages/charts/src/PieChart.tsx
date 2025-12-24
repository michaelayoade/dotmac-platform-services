/**
 * Pie Chart Component
 */

"use client";

import {
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

import { chartColors, chartTheme } from "./theme";

// ============================================================================
// Types
// ============================================================================

export interface PieChartDataPoint {
  name: string;
  value: number;
  color?: string;
}

export interface PieChartProps {
  /** Data array */
  data: PieChartDataPoint[];
  /** Chart height */
  height?: number;
  /** Show legend */
  showLegend?: boolean;
  /** Show tooltip */
  showTooltip?: boolean;
  /** Show labels */
  showLabels?: boolean;
  /** Inner radius for donut chart */
  innerRadius?: number;
  /** Outer radius */
  outerRadius?: number;
  /** Padding angle between segments */
  paddingAngle?: number;
  /** Start angle */
  startAngle?: number;
  /** End angle */
  endAngle?: number;
  /** Label type */
  labelType?: "name" | "value" | "percent" | "custom";
  /** Custom label formatter */
  labelFormatter?: (entry: PieChartDataPoint, percent: number) => string;
  /** Colors array */
  colors?: readonly string[] | string[];
  /** CSS class name */
  className?: string;
}

// ============================================================================
// Custom Label
// ============================================================================

interface CustomLabelProps {
  cx: number;
  cy: number;
  midAngle: number;
  innerRadius: number;
  outerRadius: number;
  percent: number;
  name: string;
  value: number;
  labelType: PieChartProps["labelType"];
  labelFormatter?: PieChartProps["labelFormatter"];
}

function CustomLabel({
  cx,
  cy,
  midAngle,
  innerRadius,
  outerRadius,
  percent,
  name,
  value,
  labelType,
  labelFormatter,
}: CustomLabelProps) {
  const RADIAN = Math.PI / 180;
  const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);

  let label = "";
  switch (labelType) {
    case "name":
      label = name;
      break;
    case "value":
      label = String(value);
      break;
    case "percent":
      label = `${(percent * 100).toFixed(0)}%`;
      break;
    case "custom":
      label = labelFormatter?.({ name, value }, percent) ?? "";
      break;
    default:
      label = `${(percent * 100).toFixed(0)}%`;
  }

  // Only show label if segment is large enough
  if (percent < 0.05) return null;

  return (
    <text
      x={x}
      y={y}
      fill="white"
      textAnchor="middle"
      dominantBaseline="central"
      fontSize={12}
      fontWeight={500}
    >
      {label}
    </text>
  );
}

// ============================================================================
// Component
// ============================================================================

export function PieChart({
  data,
  height = 300,
  showLegend = true,
  showTooltip = true,
  showLabels = true,
  innerRadius = 0,
  outerRadius = 80,
  paddingAngle = 0,
  startAngle = 0,
  endAngle = 360,
  labelType = "percent",
  labelFormatter,
  colors = [...chartColors.series],
  className,
}: PieChartProps) {
  return (
    <div className={className} style={{ width: "100%", height }}>
      <ResponsiveContainer>
        <RechartsPieChart>
          {showTooltip && (
            <Tooltip
              contentStyle={{
                backgroundColor: chartTheme.tooltip.background,
                border: `1px solid ${chartTheme.tooltip.border}`,
                borderRadius: chartTheme.tooltip.borderRadius,
                padding: chartTheme.tooltip.padding,
                boxShadow: chartTheme.tooltip.shadow,
              }}
              formatter={(value: number, name: string) => [value, name]}
            />
          )}

          {showLegend && (
            <Legend
              layout="horizontal"
              verticalAlign="bottom"
              align="center"
              wrapperStyle={{
                fontSize: chartTheme.legend.fontSize,
                color: chartTheme.legend.text,
              }}
            />
          )}

          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={innerRadius}
            outerRadius={outerRadius}
            paddingAngle={paddingAngle}
            startAngle={startAngle}
            endAngle={endAngle}
            dataKey="value"
            nameKey="name"
            label={
              showLabels
                ? (props) => (
                    <CustomLabel
                      {...props}
                      labelType={labelType}
                      labelFormatter={labelFormatter}
                    />
                  )
                : false
            }
            labelLine={false}
          >
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.color ?? colors[index % colors.length]}
              />
            ))}
          </Pie>
        </RechartsPieChart>
      </ResponsiveContainer>
    </div>
  );
}

export default PieChart;
