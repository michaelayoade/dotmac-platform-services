/**
 * @dotmac/data-tables
 * Universal data table system for all DotMac portals
 *
 * ELIMINATES DUPLICATION: 7+ table implementations → 1 universal system
 * FEATURES:
 * - Portal-aware theming (Admin, Customer, Reseller, Technician, Management)
 * - Advanced search with fuzzy matching
 * - Column filtering and global filters
 * - Pagination with customizable page sizes
 * - Row selection and bulk operations
 * - Export to CSV, XLSX, JSON, PDF
 * - Column sorting, resizing, and reordering
 * - Virtualization for large datasets
 * - Fully accessible with keyboard navigation
 * - TypeScript-first with comprehensive types
 */

// Main components
export {
  UniversalDataTable,
  TableSearch,
  TableFilters,
  TablePagination,
  TableToolbar,
  BulkActions,
} from './components';

// Types
export type {
  UniversalDataTableProps,
  TableColumn,
  ColumnDef,
  TableAction,
  FilterDefinition,
  ExportConfig,
  BulkOperation,
  SearchConfig,
  VirtualizationConfig,
  PaginationState,
  FilteringState,
  SelectionState,
  SortingState,
  TableState,
  TableEvents,
  PortalVariant,
  PortalTheme,
  TableInstance,
  DataTableHookReturn,
} from './types';

// Utilities
export {
  exportData,
  exportToCSV,
  exportToJSON,
  exportToXLSX,
  exportToPDF,
  getRecommendedExportFormat,
} from './utils/export';

// Hooks (to be implemented)
// export { useUniversalDataTable } from './hooks/useUniversalDataTable';
// export { useTableState } from './hooks/useTableState';
// export { useTableExport } from './hooks/useTableExport';

// Default export for convenience
export { UniversalDataTable as default } from './components';
