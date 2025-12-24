/**
 * Chart Theme
 *
 * Default colors and styling for charts
 */

export const chartColors = {
  primary: "#3b82f6", // blue-500
  secondary: "#64748b", // slate-500
  success: "#22c55e", // green-500
  warning: "#f97316", // orange-500
  error: "#ef4444", // red-500
  purple: "#a855f7", // purple-500
  cyan: "#06b6d4", // cyan-500
  pink: "#ec4899", // pink-500
  indigo: "#6366f1", // indigo-500
  teal: "#14b8a6", // teal-500

  // Series colors (for multi-line/bar charts)
  series: [
    "#3b82f6", // blue
    "#22c55e", // green
    "#f97316", // orange
    "#a855f7", // purple
    "#06b6d4", // cyan
    "#ec4899", // pink
    "#6366f1", // indigo
    "#14b8a6", // teal
    "#ef4444", // red
    "#fbbf24", // amber
  ],

  // Gradients
  gradients: {
    primary: { start: "#3b82f6", end: "#1d4ed8" },
    success: { start: "#22c55e", end: "#15803d" },
    warning: { start: "#f97316", end: "#ea580c" },
    error: { start: "#ef4444", end: "#dc2626" },
  },
} as const;

/**
 * Get chart color by index (cycles through series colors)
 */
export function getChartColor(index: number): string {
  return chartColors.series[index % chartColors.series.length];
}

/**
 * Chart theme configuration
 */
export const chartTheme = {
  // Axis styling
  axis: {
    stroke: "#e2e8f0", // slate-200
    tick: {
      fill: "#64748b", // slate-500
      fontSize: 12,
    },
  },

  // Grid styling
  grid: {
    stroke: "#f1f5f9", // slate-100
    strokeDasharray: "3 3",
  },

  // Tooltip styling
  tooltip: {
    background: "#ffffff",
    border: "#e2e8f0",
    text: "#1e293b",
    shadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
    borderRadius: "8px",
    padding: "12px",
  },

  // Legend styling
  legend: {
    text: "#64748b",
    fontSize: 12,
    iconSize: 12,
  },

  // Responsive breakpoints
  responsive: {
    sm: 640,
    md: 768,
    lg: 1024,
  },
} as const;
