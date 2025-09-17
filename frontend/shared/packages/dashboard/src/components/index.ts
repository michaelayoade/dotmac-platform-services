/**
 * Universal Dashboard Components
 * Production-ready, portal-agnostic components for DRY architecture
 */

export { ActivityFeed, ActivityFeedPresets } from './ActivityFeed/ActivityFeed';
export { MetricsCard, MetricsCardPresets } from './MetricsCard/MetricsCard';
export { ResourceUsageChart, ResourceUsagePresets } from './ResourceUsageChart/ResourceUsageChart';
export {
  EntityManagementTable,
  EntityTablePresets,
} from './EntityManagementTable/EntityManagementTable';

// Re-export types for convenience
export type {
  Activity,
  ResourceMetrics,
  TableColumn,
  EntityAction,
  MetricsCardData,
  ActivityFeedConfig,
  ChartTimeframe,
  PortalVariant,
} from '../types';
