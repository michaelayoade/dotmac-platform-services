/**
 * Chart Theme
 *
 * Colors and styling for charts, integrated with @dotmac/design-tokens
 */

import { colors } from "@dotmac/design-tokens";

// ============================================================================
// Chart Colors - derived from design tokens
// ============================================================================

export const chartColors = {
  primary: colors.primary[500],
  secondary: colors.secondary[500],
  success: colors.network[500],
  warning: colors.alert[500],
  error: colors.critical[500],
  info: colors.cyan[500],
  purple: colors.purple[500],
  cyan: colors.cyan[500],
  pink: "#ec4899", // pink-500 (not in design tokens)
  indigo: "#6366f1", // indigo-500 (not in design tokens)
  teal: "#14b8a6", // teal-500 (not in design tokens)

  // Series colors (for multi-line/bar charts) - light mode
  series: [
    colors.primary[500],
    colors.network[500],
    colors.alert[500],
    colors.purple[500],
    colors.cyan[500],
    "#ec4899", // pink
    "#6366f1", // indigo
    "#14b8a6", // teal
    colors.critical[500],
    "#fbbf24", // amber
  ],

  // Gradients
  gradients: {
    primary: { start: colors.primary[500], end: colors.primary[700] },
    success: { start: colors.network[500], end: colors.network[700] },
    warning: { start: colors.alert[500], end: colors.alert[600] },
    error: { start: colors.critical[500], end: colors.critical[600] },
  },
} as const;

/**
 * Dark mode adjusted chart colors (increased lightness for dark backgrounds)
 */
export const chartColorsDark = {
  primary: colors.primary[400],
  secondary: colors.secondary[400],
  success: colors.network[400],
  warning: colors.alert[400],
  error: colors.critical[400],
  info: colors.cyan[400],
  purple: colors.purple[400],
  cyan: colors.cyan[400],
  pink: "#f472b6", // pink-400
  indigo: "#818cf8", // indigo-400
  teal: "#2dd4bf", // teal-400

  // Series colors (for multi-line/bar charts) - dark mode adjusted
  series: [
    colors.primary[400],
    colors.network[400],
    colors.alert[400],
    colors.purple[400],
    colors.cyan[400],
    "#f472b6", // pink-400
    "#818cf8", // indigo-400
    "#2dd4bf", // teal-400
    colors.critical[400],
    "#fcd34d", // amber-300
  ],

  // Gradients - adjusted for dark mode
  gradients: {
    primary: { start: colors.primary[400], end: colors.primary[500] },
    success: { start: colors.network[400], end: colors.network[500] },
    warning: { start: colors.alert[400], end: colors.alert[500] },
    error: { start: colors.critical[400], end: colors.critical[500] },
  },
} as const;

/**
 * Get chart color by index (cycles through series colors)
 */
export function getChartColor(index: number, isDarkMode = false): string {
  const colorSet = isDarkMode ? chartColorsDark : chartColors;
  return colorSet.series[index % colorSet.series.length];
}

/**
 * Get chart colors based on dark mode preference
 */
export function getChartColors(isDarkMode: boolean) {
  return isDarkMode ? chartColorsDark : chartColors;
}

// ============================================================================
// Chart Theme Configuration
// ============================================================================

/**
 * Light mode chart theme configuration
 */
export const chartThemeLight = {
  // Axis styling
  axis: {
    stroke: colors.secondary[200],
    tick: {
      fill: colors.secondary[500],
      fontSize: 12,
    },
  },

  // Grid styling
  grid: {
    stroke: colors.secondary[100],
    strokeDasharray: "3 3",
  },

  // Tooltip styling
  tooltip: {
    background: "#ffffff",
    border: colors.secondary[200],
    text: colors.secondary[800],
    shadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
    borderRadius: "8px",
    padding: "12px",
  },

  // Legend styling
  legend: {
    text: colors.secondary[500],
    fontSize: 12,
    iconSize: 12,
  },
} as const;

/**
 * Dark mode chart theme configuration
 */
export const chartThemeDark = {
  // Axis styling
  axis: {
    stroke: colors.secondary[700],
    tick: {
      fill: colors.secondary[400],
      fontSize: 12,
    },
  },

  // Grid styling
  grid: {
    stroke: colors.secondary[800],
    strokeDasharray: "3 3",
  },

  // Tooltip styling
  tooltip: {
    background: colors.secondary[800],
    border: colors.secondary[700],
    text: colors.secondary[100],
    shadow: "0 4px 6px -1px rgba(0, 0, 0, 0.3)",
    borderRadius: "8px",
    padding: "12px",
  },

  // Legend styling
  legend: {
    text: colors.secondary[400],
    fontSize: 12,
    iconSize: 12,
  },
} as const;

/**
 * Get chart theme based on dark mode preference
 */
export function getChartTheme(isDarkMode: boolean) {
  return isDarkMode ? chartThemeDark : chartThemeLight;
}

/**
 * Default chart theme (light mode for backwards compatibility)
 */
export const chartTheme = chartThemeLight;

/**
 * Responsive breakpoints
 */
export const chartBreakpoints = {
  sm: 640,
  md: 768,
  lg: 1024,
} as const;

/**
 * Chart export background colors (aligned with design tokens)
 */
export const chartExportColors = {
  light: "#ffffff",
  dark: colors.secondary[900],
} as const;
