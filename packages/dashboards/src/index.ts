/**
 * @dotmac/dashboards
 *
 * Dashboard layout patterns - filters, KPI tiles, chart grids, and drill-down panels
 *
 * @example
 * ```tsx
 * import {
 *   DashboardLayout,
 *   DashboardSection,
 *   KPITile,
 *   KPIGrid,
 *   FilterBar,
 *   ChartGrid,
 *   ChartCard,
 *   DrillDownPanel,
 * } from '@dotmac/dashboards';
 *
 * function MyDashboard() {
 *   return (
 *     <DashboardLayout
 *       title="Analytics Dashboard"
 *       filters={<FilterBar filters={filterConfig} />}
 *     >
 *       <KPIGrid>
 *         <KPITile title="Revenue" value="$12,345" change={12.5} changeType="increase" />
 *         <KPITile title="Users" value="1,234" change={-3.2} changeType="decrease" />
 *       </KPIGrid>
 *
 *       <ChartGrid>
 *         <ChartCard title="Revenue Over Time">
 *           <LineChart data={revenueData} />
 *         </ChartCard>
 *       </ChartGrid>
 *     </DashboardLayout>
 *   );
 * }
 * ```
 */

// ============================================================================
// Layouts
// ============================================================================

export {
  DashboardLayout,
  DashboardSection,
  type DashboardLayoutProps,
  type DashboardSectionProps,
} from "./layouts/DashboardLayout";

// ============================================================================
// Components
// ============================================================================

export {
  KPITile,
  KPIGrid,
  type KPITileProps,
  type KPIGridProps,
} from "./components/KPITile";

export {
  FilterBar,
  type FilterBarProps,
  type FilterConfig,
  type FilterOption,
  type FilterValues,
} from "./components/FilterBar";

export {
  ChartGrid,
  ChartCard,
  type ChartGridProps,
  type ChartCardProps,
} from "./components/ChartGrid";

export {
  DrillDownPanel,
  type DrillDownPanelProps,
} from "./components/DrillDownPanel";

// ============================================================================
// Utilities
// ============================================================================

export { cn } from "./utils/cn";

// ============================================================================
// Version
// ============================================================================

export const version = "1.0.0";
