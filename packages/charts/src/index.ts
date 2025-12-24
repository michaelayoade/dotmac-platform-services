/**
 * @dotmac/charts
 *
 * Chart components built on Recharts with DotMac theming
 *
 * @example
 * ```tsx
 * import { LineChart, BarChart, PieChart, AreaChart } from '@dotmac/charts';
 *
 * <LineChart
 *   data={[{ name: 'Jan', value: 100 }, { name: 'Feb', value: 200 }]}
 *   dataKey="value"
 *   xAxisKey="name"
 * />
 * ```
 */

// ============================================================================
// Charts
// ============================================================================

export { LineChart, type LineChartProps } from "./LineChart";
export { BarChart, type BarChartProps } from "./BarChart";
export { AreaChart, type AreaChartProps } from "./AreaChart";
export { PieChart, type PieChartProps } from "./PieChart";

// ============================================================================
// Utilities
// ============================================================================

export { chartColors, getChartColor, chartTheme } from "./theme";

// ============================================================================
// Version
// ============================================================================

export const version = "1.0.0";
