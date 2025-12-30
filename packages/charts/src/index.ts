/**
 * @dotmac/charts
 *
 * Chart components built on Recharts with DotMac theming
 *
 * @example
 * ```tsx
 * import { LineChart, BarChart, PieChart, AreaChart, Sparkline } from '@dotmac/charts';
 *
 * <LineChart
 *   data={[{ name: 'Jan', value: 100 }, { name: 'Feb', value: 200 }]}
 *   dataKey="value"
 *   xAxisKey="name"
 * />
 *
 * // Inline sparkline for tables
 * <Sparkline data={[{value: 10}, {value: 20}, {value: 15}]} variant="trend" />
 *
 * // Chart with export functionality
 * <ExportableChart title="Revenue">
 *   <LineChart data={data} dataKey="value" xAxisKey="name" />
 * </ExportableChart>
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
// Sparklines
// ============================================================================

export {
  Sparkline,
  PositiveSparkline,
  NegativeSparkline,
  TrendSparkline,
  type SparklineProps,
  type SparklineDataPoint,
} from "./Sparkline";

// ============================================================================
// Export Functionality
// ============================================================================

export {
  ExportableChart,
  ExportButton,
  useChartExport,
  exportChartToPng,
  exportChartToSvg,
  type ChartContainerProps,
  type ChartExportOptions,
  type ExportButtonProps,
  type ExportFormat,
} from "./ChartExport";

// ============================================================================
// Utilities
// ============================================================================

export {
  chartColors,
  chartColorsDark,
  getChartColor,
  getChartColors,
  chartTheme,
  chartThemeLight,
  chartThemeDark,
  getChartTheme,
  chartBreakpoints,
  chartExportColors,
} from "./theme";

// ============================================================================
// Version
// ============================================================================

export const version = "1.0.0";
