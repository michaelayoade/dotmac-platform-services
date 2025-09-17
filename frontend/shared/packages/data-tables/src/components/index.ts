/**
 * Universal Data Tables - Component Exports
 * Single export point for all table components
 */

export { UniversalDataTable } from './UniversalDataTable';
export { TableSearch } from './TableSearch';
export { TableFilters } from './TableFilters';
export { TablePagination } from './TablePagination';
export { TableToolbar } from './TableToolbar';
export { BulkActions } from './BulkActions';

// Re-export types for convenience
export type {
  UniversalDataTableProps,
  TableColumn,
  TableAction,
  FilterDefinition,
  ExportConfig,
  BulkOperation,
  SearchConfig,
  PaginationState,
  FilteringState,
  SelectionState,
  PortalVariant,
  TableInstance,
  DataTableHookReturn,
} from '../types';

// Re-export utilities
export {
  exportData,
  exportToCSV,
  exportToJSON,
  exportToXLSX,
  exportToPDF,
  getRecommendedExportFormat,
} from '../utils/export';
