/**
 * Performance Components Index
 * High-performance components for large datasets and optimization
 */

export { VirtualizedDataTable } from './VirtualizedDataTable';
export type { VirtualizedColumn, VirtualizedDataTableProps } from './VirtualizedDataTable';

export {
  LazyChart,
  preloadChartComponents,
  clearChartCache,
  getChartCacheStats,
} from './LazyChart';
export type { LazyChartProps } from './LazyChart';
