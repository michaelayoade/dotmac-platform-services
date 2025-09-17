/**
 * Universal Data Tables - Types
 * Consolidates ALL data table patterns from across the platform
 *
 * ELIMINATES DUPLICATION: 7+ table implementations → 1 universal system
 */

import type { ReactNode } from 'react';
import type { LucideIcon } from 'lucide-react';

// ===========================
// Core Data Table Types
// ===========================

export interface TableColumn<TData = any> {
  id: string;
  header: string | ReactNode;
  accessorKey?: keyof TData | string;
  accessorFn?: (row: TData) => any;

  // Rendering
  cell?: (props: { getValue: () => any; row: TData; column: TableColumn<TData> }) => ReactNode;
  header?: ReactNode | ((props: any) => ReactNode);
  footer?: ReactNode | ((props: any) => ReactNode);

  // Features
  enableSorting?: boolean;
  enableColumnFilter?: boolean;
  enableGlobalFilter?: boolean;
  enableGrouping?: boolean;
  enableResizing?: boolean;
  enableHiding?: boolean;
  enablePinning?: boolean;

  // Sizing
  size?: number;
  minSize?: number;
  maxSize?: number;

  // Filtering
  filterFn?: string | ((row: TData, columnId: string, filterValue: any) => boolean);

  // Sorting
  sortingFn?: string | ((rowA: any, rowB: any, columnId: string) => number);
  sortDescFirst?: boolean;

  // Grouping
  aggregationFn?: string | ((columnId: string, leafRows: any[], childRows: any[]) => any);
  aggregatedCell?: (props: any) => ReactNode;

  // Meta (for custom properties)
  meta?: {
    align?: 'left' | 'center' | 'right';
    className?: string;
    headerClassName?: string;
    cellClassName?: string;
    width?: string | number;
    sticky?: 'left' | 'right';
    type?: 'text' | 'number' | 'currency' | 'percentage' | 'date' | 'status' | 'badge' | 'actions';
    format?: {
      currency?: string;
      precision?: number;
      dateFormat?: string;
    };
    // Portal-specific styling
    portal?: PortalVariant;
  };
}

export interface TableAction<TData = any> {
  id: string;
  label: string;
  icon?: LucideIcon;
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost' | 'outline';
  size?: 'xs' | 'sm' | 'md' | 'lg';
  onClick: (data: TData | TData[]) => void | Promise<void>;
  disabled?: boolean | ((data: TData | TData[]) => boolean);
  visible?: boolean | ((data: TData | TData[]) => boolean);
  loading?: boolean;
  loadingText?: string;
  tooltip?: string;
  shortcut?: string;

  // Confirmation
  requiresConfirmation?: boolean;
  confirmationTitle?: string;
  confirmationMessage?: string | ((data: TData | TData[]) => string);

  // Bulk action specific
  minSelection?: number;
  maxSelection?: number;
}

export interface FilterDefinition {
  id: string;
  column: string;
  type: 'text' | 'select' | 'multiselect' | 'date' | 'daterange' | 'number' | 'boolean';
  label: string;
  placeholder?: string;
  options?: Array<{ label: string; value: any; count?: number }>;
  defaultValue?: any;
  multiple?: boolean;
  searchable?: boolean;
}

export interface SortingState {
  id: string;
  desc: boolean;
}

export interface FilteringState {
  [key: string]: any;
}

export interface PaginationState {
  pageIndex: number;
  pageSize: number;
}

export interface SelectionState {
  [key: string]: boolean;
}

// ===========================
// Export Types
// ===========================

export interface ExportConfig {
  formats: Array<'csv' | 'xlsx' | 'json' | 'pdf'>;
  filename?: string | ((data: any[]) => string);
  includeHeaders?: boolean;
  selectedOnly?: boolean;
  customFields?: Array<{
    key: string;
    label: string;
    accessor: (row: any) => any;
  }>;
}

export interface BulkOperation<TData = any> {
  id: string;
  label: string;
  icon?: LucideIcon;
  variant?: 'primary' | 'secondary' | 'danger';
  action: (selectedData: TData[]) => Promise<void>;
  requiresConfirmation?: boolean;
  confirmationMessage?: string | ((count: number) => string);
  minSelection?: number;
  maxSelection?: number;
}

// ===========================
// Portal Integration
// ===========================

export type PortalVariant = 'admin' | 'customer' | 'reseller' | 'technician' | 'management';

export interface PortalTheme {
  variant: PortalVariant;
  colors: {
    primary: string;
    secondary: string;
    accent: string;
    background: string;
    surface: string;
    border: string;
    text: {
      primary: string;
      secondary: string;
      muted: string;
    };
  };
  spacing: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
  };
}

// ===========================
// Advanced Features
// ===========================

export interface VirtualizationConfig {
  enabled: boolean;
  estimateSize?: number;
  overscan?: number;
  scrollMargin?: number;
}

export interface SearchConfig {
  enabled: boolean;
  placeholder?: string;
  debounceMs?: number;
  highlightMatches?: boolean;
  searchableColumns?: string[];
  fuzzySearch?: boolean;
  minSearchLength?: number;
}

export interface TableState {
  sorting: SortingState[];
  columnFilters: FilteringState[];
  globalFilter: string;
  pagination: PaginationState;
  rowSelection: SelectionState;
  columnVisibility: Record<string, boolean>;
  columnOrder: string[];
  columnPinning: {
    left?: string[];
    right?: string[];
  };
  columnSizing: Record<string, number>;
  expanded: Record<string, boolean>;
}

// ===========================
// Event Handlers
// ===========================

export interface TableEvents<TData = any> {
  onRowClick?: (row: TData, event: MouseEvent) => void;
  onRowDoubleClick?: (row: TData, event: MouseEvent) => void;
  onCellClick?: (cell: any, event: MouseEvent) => void;
  onSelectionChange?: (selectedRows: TData[]) => void;
  onSortingChange?: (sorting: SortingState[]) => void;
  onFilteringChange?: (filters: FilteringState[]) => void;
  onGlobalFilterChange?: (filter: string) => void;
  onPaginationChange?: (pagination: PaginationState) => void;
  onColumnVisibilityChange?: (visibility: Record<string, boolean>) => void;
  onColumnOrderChange?: (order: string[]) => void;
  onColumnSizingChange?: (sizing: Record<string, number>) => void;
  onStateChange?: (state: Partial<TableState>) => void;
}

// ===========================
// Main Table Props Interface
// ===========================

export interface UniversalDataTableProps<TData = any> extends TableEvents<TData> {
  // Data
  data: TData[];
  columns: TableColumn<TData>[];

  // Identity
  id?: string;

  // Portal Integration
  portal?: PortalVariant;
  theme?: Partial<PortalTheme>;

  // Core Features
  enableSorting?: boolean;
  enableFiltering?: boolean;
  enableGlobalFilter?: boolean;
  enableColumnFilters?: boolean;
  enablePagination?: boolean;
  enableSelection?: boolean;
  enableMultiRowSelection?: boolean;
  enableSubRowSelection?: boolean;

  // Advanced Features
  enableGrouping?: boolean;
  enableExpanding?: boolean;
  enableResizing?: boolean;
  enableReordering?: boolean;
  enableHiding?: boolean;
  enablePinning?: boolean;
  enableVirtualization?: boolean;

  // Configuration
  searchConfig?: SearchConfig;
  virtualizationConfig?: VirtualizationConfig;
  exportConfig?: ExportConfig;

  // Pagination
  pageSize?: number;
  pageSizeOptions?: number[];
  showPaginationControls?: boolean;
  paginationPosition?: 'top' | 'bottom' | 'both';

  // Selection
  rowSelectionMode?: 'single' | 'multiple';
  enableSelectAll?: boolean;
  getRowId?: (row: TData, index: number) => string;

  // Actions
  actions?: TableAction<TData>[];
  bulkActions?: BulkOperation<TData>[];
  toolbarActions?: TableAction<TData>[];

  // UI Customization
  variant?: 'default' | 'striped' | 'bordered' | 'compact' | 'spacious';
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  density?: 'comfortable' | 'compact' | 'spacious';

  // Layout
  height?: string | number;
  maxHeight?: string | number;
  stickyHeader?: boolean;
  stickyFooter?: boolean;
  fullWidth?: boolean;

  // State Management
  initialState?: Partial<TableState>;
  state?: Partial<TableState>;
  onStateChange?: (state: TableState) => void;

  // Loading & Error States
  loading?: boolean;
  loadingComponent?: ReactNode;
  error?: string | Error | null;
  errorComponent?: ReactNode;
  emptyState?: ReactNode;

  // Accessibility
  caption?: string;
  ariaLabel?: string;
  ariaDescription?: string;

  // Custom Components
  components?: {
    Table?: React.ComponentType<any>;
    TableHead?: React.ComponentType<any>;
    TableBody?: React.ComponentType<any>;
    TableRow?: React.ComponentType<any>;
    TableCell?: React.ComponentType<any>;
    Pagination?: React.ComponentType<any>;
    Search?: React.ComponentType<any>;
    Filter?: React.ComponentType<any>;
    Toolbar?: React.ComponentType<any>;
    Loading?: React.ComponentType<any>;
    Error?: React.ComponentType<any>;
    Empty?: React.ComponentType<any>;
  };

  // Styling
  className?: string;
  tableClassName?: string;
  headerClassName?: string;
  bodyClassName?: string;
  rowClassName?: string | ((row: TData, index: number) => string);
  cellClassName?: string;

  // Performance
  debugTable?: boolean;
  debugHeaders?: boolean;
  debugColumns?: boolean;

  // Server-side features
  manualSorting?: boolean;
  manualFiltering?: boolean;
  manualPagination?: boolean;
  pageCount?: number;
  dataUpdatedAt?: number;
}

// ===========================
// Utility Types
// ===========================

export type TableInstance<TData = any> = {
  getState: () => TableState;
  setState: (updater: TableState | ((old: TableState) => TableState)) => void;
  resetRowSelection: (defaultState?: boolean) => void;
  toggleAllRowsSelected: (value?: boolean) => void;
  getSelectedRowModel: () => { rows: Array<{ original: TData }> };
  getFilteredRowModel: () => { rows: Array<{ original: TData }> };
  getSortedRowModel: () => { rows: Array<{ original: TData }> };
  getPaginationRowModel: () => { rows: Array<{ original: TData }> };
  exportData: (
    format: 'csv' | 'xlsx' | 'json' | 'pdf',
    config?: Partial<ExportConfig>
  ) => Promise<void>;
  refresh: () => Promise<void>;
};

export type ColumnDef<TData = any> = TableColumn<TData>;

export type DataTableHookReturn<TData = any> = {
  table: TableInstance<TData>;
  state: TableState;
  selectedRows: TData[];
  filteredRows: TData[];
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  exportData: TableInstance<TData>['exportData'];
  refresh: () => Promise<void>;
};
