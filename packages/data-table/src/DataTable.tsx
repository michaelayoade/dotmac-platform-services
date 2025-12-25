/**
 * @dotmac/data-table - DataTable
 *
 * A feature-rich, accessible data table component built on TanStack Table.
 *
 * @description
 * Advanced data table component providing enterprise-grade features for
 * displaying and interacting with tabular data.
 *
 * ## Features
 * - **Server-side pagination** - Full support for paginated API responses
 * - **Row selection** - Single and bulk selection with customizable actions
 * - **Column management** - Show/hide columns, reorder, and pin
 * - **Search & filtering** - Global search, column filters, and quick filters
 * - **Sorting** - Client and server-side sorting support
 * - **Export** - CSV export with selection support
 * - **Responsive** - Mobile card view for small screens
 * - **Accessible** - ARIA labels and keyboard navigation
 *
 * @example
 * ```tsx
 * import { DataTable } from '@dotmac/data-table';
 *
 * const columns = [
 *   { accessorKey: 'name', header: 'Name' },
 *   { accessorKey: 'email', header: 'Email' },
 * ];
 *
 * <DataTable
 *   data={users}
 *   columns={columns}
 *   searchable
 *   pagination
 *   selectable
 * />
 * ```
 *
 * @see {@link DataTableProps} for full prop documentation
 */

"use client";

import {
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
  type ColumnDef,
  type ColumnFiltersState,
  type PaginationState,
  type Row,
  type SortingState,
  type VisibilityState,
  type OnChangeFn,
} from "@tanstack/react-table";
import { Download, Filter, Columns3, ChevronUp, ChevronDown } from "lucide-react";
import * as React from "react";

import { cn } from "./utils/cn";

// ============================================================================
// Types
// ============================================================================

export interface BulkAction<TData> {
  label: string;
  icon?: React.ElementType;
  action: (selectedRows: TData[]) => void | Promise<void>;
  variant?: "default" | "destructive" | "outline" | "secondary" | "ghost";
  disabled?: (selectedRows: TData[]) => boolean;
  confirm?: {
    title: string;
    description: string;
    confirmLabel?: string;
  };
}

export interface QuickFilter<TData> {
  label: string;
  icon?: React.ComponentType<{ className?: string }>;
  description?: string;
  defaultActive?: boolean;
  filter: (row: TData) => boolean;
}

export interface FilterConfig {
  column: string;
  label: string;
  type: "text" | "select" | "date" | "number" | "boolean";
  options?: { label: string; value: string }[];
}

export interface ServerSidePagination {
  pageIndex: number;
  pageSize: number;
  pageCount: number;
  totalRows: number;
  onPageChange: (pageIndex: number) => void;
  onPageSizeChange: (pageSize: number) => void;
}

export interface DataTableTranslations {
  searchPlaceholder: string;
  filtersLabel: string;
  clearFilters: string;
  exportLabel: string;
  columnsLabel: string;
  bulkActionsLabel: string;
  selectedCount: (selected: number, total: number) => string;
  totalCount: (total: number) => string;
  loadingLabel: string;
  emptyLabel: string;
  rowsPerPage: string;
  pageOf: (page: number, pageCount: number) => string;
  previous: string;
  next: string;
  sortAscending: string;
  sortDescending: string;
}

const DEFAULT_TRANSLATIONS: DataTableTranslations = {
  searchPlaceholder: "Search...",
  filtersLabel: "Filters",
  clearFilters: "Clear filters",
  exportLabel: "Export",
  columnsLabel: "Columns",
  bulkActionsLabel: "Bulk Actions",
  selectedCount: (selected, total) => `${selected} of ${total} row(s) selected`,
  totalCount: (total) => `${total} total row(s)`,
  loadingLabel: "Loading...",
  emptyLabel: "No results.",
  rowsPerPage: "Rows per page",
  pageOf: (page, pageCount) => `Page ${page} of ${pageCount}`,
  previous: "Previous",
  next: "Next",
  sortAscending: "Sort ascending",
  sortDescending: "Sort descending",
};

/**
 * Props for the DataTable component.
 *
 * @template TData - The type of data in each row
 * @template TValue - The type of cell values (usually inferred)
 */
export interface DataTableProps<TData, TValue> {
  // Required
  /** Column definitions using TanStack Table's ColumnDef format */
  columns: ColumnDef<TData, TValue>[];
  /** Array of data objects to display in the table */
  data: TData[];

  // Pagination
  /** Enable client-side pagination. Default: true */
  pagination?: boolean;
  /** Configuration for server-side pagination. Overrides client-side pagination when provided */
  serverSidePagination?: ServerSidePagination;
  /** Available page size options. Default: [10, 20, 50, 100] */
  pageSizeOptions?: number[];
  /** Initial page size. Default: 10 */
  defaultPageSize?: number;

  // Selection
  /** Enable row selection with checkboxes. Default: false */
  selectable?: boolean;
  /** Callback fired when selection changes */
  onSelectionChange?: (selectedRows: TData[]) => void;
  /** Actions available when rows are selected */
  bulkActions?: BulkAction<TData>[];

  // Search & Filtering
  /** Enable global search input. Default: true */
  searchable?: boolean;
  /** Placeholder text for search input */
  searchPlaceholder?: string;
  /** Limit search to specific column keys */
  searchableColumns?: string[];
  /** Controlled global filter value */
  globalFilter?: string;
  /** Callback for controlled global filter */
  onGlobalFilterChange?: (value: string) => void;
  /** Advanced filter configurations for column-specific filtering */
  filters?: FilterConfig[];
  /** Quick filter presets that can be toggled on/off */
  quickFilters?: QuickFilter<TData>[];

  // Sorting
  /** Enable column sorting. Default: true */
  sortable?: boolean;
  /** Initial sorting state */
  defaultSorting?: SortingState;
  /** Controlled sorting callback */
  onSortingChange?: OnChangeFn<SortingState>;

  // Column Management
  /** Enable column visibility toggle menu. Default: true */
  columnVisibility?: boolean;
  /** Initial column visibility state */
  defaultColumnVisibility?: VisibilityState;
  /** Controlled column visibility callback */
  onColumnVisibilityChange?: OnChangeFn<VisibilityState>;

  // Export
  /** Enable CSV export button. Default: false */
  exportable?: boolean;
  /** Filename for exported CSV (without extension) */
  exportFilename?: string;
  /** Columns to include in export. Defaults to all columns */
  exportColumns?: (keyof TData)[];

  // State
  /** Show loading skeleton. Default: false */
  loading?: boolean;
  /** Error message to display */
  error?: string;

  // Callbacks
  /** Callback when a row is clicked */
  onRowClick?: (row: TData) => void;
  /** Custom row ID generator for selection tracking */
  getRowId?: (row: TData, index: number) => string;

  // Responsive
  /** Enable mobile card view below breakpoint. Default: false */
  enableResponsiveCards?: boolean;
  /** Custom render function for mobile cards */
  renderMobileCard?: (row: Row<TData>) => React.ReactNode;
  /** Breakpoint (px) for switching to mobile view. Default: 768 */
  responsiveBreakpoint?: number;

  // Styling
  /** Additional CSS class for the container */
  className?: string;
  /** Hide the toolbar (search, filters, actions). Default: false */
  hideToolbar?: boolean;
  /** Custom actions to render in the toolbar */
  toolbarActions?: React.ReactNode;
  /** Custom translations for UI text */
  translations?: Partial<DataTableTranslations>;

  // Adapters (for optional features)
  /** Adapter for confirmation dialogs (used by bulk actions with confirm) */
  confirmAdapter?: (options: {
    title: string;
    description: string;
    confirmLabel?: string;
  }) => Promise<boolean>;
}

// ============================================================================
// Component
// ============================================================================

export function DataTable<TData, TValue>({
  columns,
  data,
  pagination = true,
  serverSidePagination,
  pageSizeOptions = [10, 20, 50, 100],
  defaultPageSize = 10,
  selectable = false,
  onSelectionChange,
  bulkActions = [],
  searchable = true,
  searchPlaceholder,
  searchableColumns = [],
  globalFilter: controlledGlobalFilter,
  onGlobalFilterChange,
  filters = [],
  quickFilters = [],
  sortable = true,
  defaultSorting = [],
  onSortingChange,
  columnVisibility: enableColumnVisibility = true,
  defaultColumnVisibility = {},
  onColumnVisibilityChange,
  exportable = false,
  exportFilename = "data",
  exportColumns,
  loading = false,
  error,
  onRowClick,
  getRowId,
  enableResponsiveCards = false,
  renderMobileCard,
  responsiveBreakpoint = 768,
  className,
  hideToolbar = false,
  toolbarActions,
  translations,
  confirmAdapter,
}: DataTableProps<TData, TValue>) {
  const t = { ...DEFAULT_TRANSLATIONS, ...translations };
  if (searchPlaceholder) t.searchPlaceholder = searchPlaceholder;

  // State
  const [sorting, setSorting] = React.useState<SortingState>(defaultSorting);
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>([]);
  const [columnVisibilityState, setColumnVisibilityState] =
    React.useState<VisibilityState>(defaultColumnVisibility);
  const [rowSelection, setRowSelection] = React.useState({});
  const [internalGlobalFilter, setInternalGlobalFilter] = React.useState("");
  const [showFilters, setShowFilters] = React.useState(false);
  const [activeQuickFilters, setActiveQuickFilters] = React.useState<Set<string>>(
    new Set(quickFilters.filter((f) => f.defaultActive).map((f) => f.label))
  );
  const [isMobileView, setIsMobileView] = React.useState(false);
  const [showColumnMenu, setShowColumnMenu] = React.useState(false);
  const columnMenuRef = React.useRef<HTMLDivElement>(null);
  const [paginationState, setPaginationState] = React.useState<PaginationState>({
    pageIndex: serverSidePagination?.pageIndex ?? 0,
    pageSize: serverSidePagination?.pageSize ?? defaultPageSize,
  });

  const globalFilter = controlledGlobalFilter ?? internalGlobalFilter;
  const handleGlobalFilterChange = onGlobalFilterChange ?? setInternalGlobalFilter;

  // Responsive detection
  React.useEffect(() => {
    if (!enableResponsiveCards) return;

    const mediaQuery = window.matchMedia(`(max-width: ${responsiveBreakpoint}px)`);
    const handleChange = () => setIsMobileView(mediaQuery.matches);
    handleChange();
    mediaQuery.addEventListener("change", handleChange);
    return () => mediaQuery.removeEventListener("change", handleChange);
  }, [enableResponsiveCards, responsiveBreakpoint]);

  // Close column menu on click outside
  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        columnMenuRef.current &&
        !columnMenuRef.current.contains(event.target as Node)
      ) {
        setShowColumnMenu(false);
      }
    };

    if (showColumnMenu) {
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [showColumnMenu]);

  // Filter data by quick filters
  const filteredData = React.useMemo(() => {
    if (activeQuickFilters.size === 0) return data;
    return data.filter((row) =>
      Array.from(activeQuickFilters).every((label) => {
        const filter = quickFilters.find((f) => f.label === label);
        return filter ? filter.filter(row) : true;
      })
    );
  }, [data, quickFilters, activeQuickFilters]);

  // Selection column
  const selectionColumn: ColumnDef<TData> = {
    id: "select",
    header: ({ table }) => (
      <input
        type="checkbox"
        checked={table.getIsAllPageRowsSelected()}
        onChange={(e) => table.toggleAllPageRowsSelected(e.target.checked)}
        aria-label="Select all"
        className="h-4 w-4 rounded border-gray-300"
      />
    ),
    cell: ({ row }) => (
      <input
        type="checkbox"
        checked={row.getIsSelected()}
        onChange={(e) => row.toggleSelected(e.target.checked)}
        aria-label="Select row"
        className="h-4 w-4 rounded border-gray-300"
      />
    ),
    enableSorting: false,
    enableHiding: false,
    size: 40,
  };

  const tableColumns = React.useMemo(() => {
    return selectable ? [selectionColumn, ...columns] : columns;
  }, [columns, selectable]);

  // Global filter function
  const globalFilterFn = React.useCallback(
    (row: Row<TData>, _columnId: string, filterValue: string) => {
      const searchTerm = String(filterValue ?? "").trim().toLowerCase();
      if (!searchTerm) return true;

      if (searchableColumns.length > 0) {
        return searchableColumns.some((col) => {
          const value = (row.original as Record<string, unknown>)[col];
          return String(value ?? "").toLowerCase().includes(searchTerm);
        });
      }

      return row.getVisibleCells().some((cell) =>
        String(cell.getValue() ?? "").toLowerCase().includes(searchTerm)
      );
    },
    [searchableColumns]
  );

  // Table instance
  const table = useReactTable({
    data: filteredData,
    columns: tableColumns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: sortable ? getSortedRowModel() : undefined,
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: pagination && !serverSidePagination ? getPaginationRowModel() : undefined,
    onSortingChange: onSortingChange ?? setSorting,
    onColumnFiltersChange: setColumnFilters,
    onColumnVisibilityChange: onColumnVisibilityChange ?? setColumnVisibilityState,
    onRowSelectionChange: setRowSelection,
    onGlobalFilterChange: handleGlobalFilterChange,
    onPaginationChange: serverSidePagination ? undefined : setPaginationState,
    globalFilterFn,
    state: {
      sorting,
      columnFilters,
      columnVisibility: columnVisibilityState,
      rowSelection,
      globalFilter,
      pagination: serverSidePagination
        ? { pageIndex: serverSidePagination.pageIndex, pageSize: serverSidePagination.pageSize }
        : paginationState,
    },
    pageCount: serverSidePagination?.pageCount,
    manualPagination: !!serverSidePagination,
    getRowId: getRowId ? (row, index) => getRowId(row, index) : undefined,
  });

  // Selection change callback
  React.useEffect(() => {
    if (onSelectionChange) {
      const selectedRows = table.getSelectedRowModel().rows.map((row) => row.original);
      onSelectionChange(selectedRows);
    }
  }, [rowSelection, table, onSelectionChange]);

  const selectedRows = table.getSelectedRowModel().rows.map((row) => row.original);

  // Export handler
  const handleExport = React.useCallback(() => {
    const exportData = selectedRows.length > 0 ? selectedRows : filteredData;
    const cols = exportColumns ?? (Object.keys(filteredData[0] || {}) as (keyof TData)[]);

    const header = cols.join(",");
    const rows = exportData.map((row) =>
      cols
        .map((col) => {
          const value = String((row as Record<string, unknown>)[col as string] ?? "");
          return value.includes(",") ? `"${value}"` : value;
        })
        .join(",")
    );

    const csv = [header, ...rows].join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `${exportFilename}.csv`;
    link.click();
  }, [filteredData, selectedRows, exportColumns, exportFilename]);

  // Bulk action handler
  const handleBulkAction = React.useCallback(
    async (action: BulkAction<TData>) => {
      if (action.confirm && confirmAdapter) {
        const confirmed = await confirmAdapter(action.confirm);
        if (!confirmed) return;
      }
      await action.action(selectedRows);
      table.resetRowSelection();
    },
    [selectedRows, table, confirmAdapter]
  );

  // Toggle quick filter
  const toggleQuickFilter = (label: string) => {
    setActiveQuickFilters((prev) => {
      const next = new Set(prev);
      if (next.has(label)) {
        next.delete(label);
      } else {
        next.add(label);
      }
      return next;
    });
  };

  const showToolbar =
    !hideToolbar &&
    (searchable || filters.length > 0 || quickFilters.length > 0 || toolbarActions || exportable || enableColumnVisibility);

  const showMobileCards = enableResponsiveCards && isMobileView && renderMobileCard;

  const pageCount = serverSidePagination?.pageCount ?? table.getPageCount();
  const currentPage = serverSidePagination?.pageIndex ?? paginationState.pageIndex;
  const currentPageSize = serverSidePagination?.pageSize ?? paginationState.pageSize;

  return (
    <div className={cn("space-y-4", className)}>
      {/* Error message */}
      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Toolbar */}
      {showToolbar && (
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            {/* Search */}
            <div className="flex items-center gap-2 flex-1">
              {searchable && (
                <input
                  type="text"
                  placeholder={t.searchPlaceholder}
                  value={globalFilter}
                  onChange={(e) => handleGlobalFilterChange(e.target.value)}
                  className="max-w-sm h-10 px-3 rounded-md border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  aria-label={t.searchPlaceholder}
                />
              )}

              {filters.length > 0 && (
                <button
                  onClick={() => setShowFilters(!showFilters)}
                  className={cn(
                    "inline-flex items-center gap-2 h-10 px-4 rounded-md text-sm font-medium",
                    showFilters
                      ? "bg-blue-600 text-white"
                      : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                  )}
                >
                  <Filter className="h-4 w-4" />
                  {t.filtersLabel}
                </button>
              )}
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2">
              {toolbarActions}

              {exportable && (
                <button
                  onClick={handleExport}
                  disabled={filteredData.length === 0}
                  className="inline-flex items-center gap-2 h-10 px-4 rounded-md text-sm font-medium bg-gray-100 text-gray-700 hover:bg-gray-200 disabled:opacity-50"
                >
                  <Download className="h-4 w-4" />
                  {t.exportLabel}
                </button>
              )}

              {enableColumnVisibility && (
                <div className="relative" ref={columnMenuRef}>
                  <button
                    onClick={() => setShowColumnMenu(!showColumnMenu)}
                    className={cn(
                      "inline-flex items-center gap-2 h-10 px-4 rounded-md text-sm font-medium",
                      showColumnMenu
                        ? "bg-blue-600 text-white"
                        : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                    )}
                  >
                    <Columns3 className="h-4 w-4" />
                    {t.columnsLabel}
                  </button>
                  {showColumnMenu && (
                    <div className="absolute right-0 mt-2 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 z-50">
                      <div className="py-1 max-h-64 overflow-y-auto">
                        {table
                          .getAllColumns()
                          .filter((column) => column.getCanHide())
                          .map((column) => {
                            const header = column.columnDef.header;
                            const label =
                              typeof header === "string"
                                ? header
                                : column.id;
                            return (
                              <label
                                key={column.id}
                                className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 cursor-pointer"
                              >
                                <input
                                  type="checkbox"
                                  checked={column.getIsVisible()}
                                  onChange={(e) =>
                                    column.toggleVisibility(e.target.checked)
                                  }
                                  className="h-4 w-4 rounded border-gray-300"
                                />
                                {label}
                              </label>
                            );
                          })}
                      </div>
                      <div className="border-t border-gray-100 px-4 py-2">
                        <button
                          onClick={() => {
                            // Reset to defaultColumnVisibility, not empty state
                            table.setColumnVisibility(defaultColumnVisibility);
                          }}
                          className="text-sm text-blue-600 hover:text-blue-800"
                        >
                          Reset to default
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {selectable && bulkActions.length > 0 && selectedRows.length > 0 && (
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-600">
                    {selectedRows.length} selected
                  </span>
                  {bulkActions.map((action, i) => {
                    const Icon = action.icon;
                    return (
                      <button
                        key={i}
                        onClick={() => handleBulkAction(action)}
                        disabled={action.disabled?.(selectedRows)}
                        className={cn(
                          "inline-flex items-center gap-2 h-10 px-4 rounded-md text-sm font-medium",
                          action.variant === "destructive"
                            ? "bg-red-600 text-white hover:bg-red-700"
                            : "bg-blue-600 text-white hover:bg-blue-700",
                          "disabled:opacity-50"
                        )}
                      >
                        {Icon && <Icon className="h-4 w-4" />}
                        {action.label}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          </div>

          {/* Quick filters */}
          {quickFilters.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {quickFilters.map((filter) => {
                const isActive = activeQuickFilters.has(filter.label);
                const Icon = filter.icon;
                return (
                  <button
                    key={filter.label}
                    onClick={() => toggleQuickFilter(filter.label)}
                    className={cn(
                      "inline-flex items-center gap-2 h-8 px-3 rounded-full text-sm font-medium transition-colors",
                      isActive
                        ? "bg-blue-600 text-white"
                        : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                    )}
                  >
                    {Icon && <Icon className="h-4 w-4" />}
                    {filter.label}
                  </button>
                );
              })}
              {activeQuickFilters.size > 0 && (
                <button
                  onClick={() => setActiveQuickFilters(new Set())}
                  className="text-sm text-gray-500 hover:text-gray-700"
                >
                  {t.clearFilters}
                </button>
              )}
            </div>
          )}

          {/* Advanced filters */}
          {showFilters && filters.length > 0 && (
            <div className="flex flex-wrap gap-4 p-4 bg-gray-50 rounded-md border">
              {filters.map((filter) => (
                <div key={filter.column} className="flex flex-col gap-1">
                  <label className="text-sm font-medium text-gray-600">
                    {filter.label}
                  </label>
                  {filter.type === "select" && filter.options ? (
                    <select
                      value={(table.getColumn(filter.column)?.getFilterValue() as string) ?? ""}
                      onChange={(e) =>
                        table.getColumn(filter.column)?.setFilterValue(e.target.value || undefined)
                      }
                      className="h-8 px-2 rounded border border-gray-300 text-sm"
                    >
                      <option value="">All</option>
                      {filter.options.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <input
                      type={filter.type === "number" ? "number" : filter.type === "date" ? "date" : "text"}
                      value={(table.getColumn(filter.column)?.getFilterValue() as string) ?? ""}
                      onChange={(e) =>
                        table.getColumn(filter.column)?.setFilterValue(e.target.value || undefined)
                      }
                      className="h-8 px-2 w-40 rounded border border-gray-300 text-sm"
                    />
                  )}
                </div>
              ))}
              <button
                onClick={() => table.resetColumnFilters()}
                className="self-end h-8 px-3 text-sm text-gray-600 hover:text-gray-800"
              >
                {t.clearFilters}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Mobile card view */}
      {showMobileCards && (
        <div className="space-y-3 md:hidden">
          {loading ? (
            <div className="p-6 text-center text-gray-500">{t.loadingLabel}</div>
          ) : table.getRowModel().rows.length > 0 ? (
            table.getRowModel().rows.map((row) => (
              <div
                key={row.id}
                onClick={() => onRowClick?.(row.original)}
                className={cn(
                  "p-4 bg-white rounded-lg border shadow-sm",
                  onRowClick && "cursor-pointer hover:shadow-md"
                )}
              >
                {renderMobileCard!(row)}
              </div>
            ))
          ) : (
            <div className="p-6 text-center text-gray-500">{t.emptyLabel}</div>
          )}
        </div>
      )}

      {/* Table view */}
      <div
        className={cn(
          "rounded-md border bg-white overflow-hidden",
          showMobileCards && "hidden md:block"
        )}
      >
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th
                    key={header.id}
                    className={cn(
                      "px-4 py-3 text-left font-medium text-gray-700",
                      header.column.getCanSort() && "cursor-pointer select-none"
                    )}
                    onClick={header.column.getToggleSortingHandler()}
                    style={{ width: header.getSize() !== 150 ? header.getSize() : undefined }}
                  >
                    <div className="flex items-center gap-2">
                      {header.isPlaceholder
                        ? null
                        : flexRender(header.column.columnDef.header, header.getContext())}
                      {header.column.getIsSorted() === "asc" && (
                        <ChevronUp className="h-4 w-4" />
                      )}
                      {header.column.getIsSorted() === "desc" && (
                        <ChevronDown className="h-4 w-4" />
                      )}
                    </div>
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={tableColumns.length} className="px-4 py-12 text-center text-gray-500">
                  {t.loadingLabel}
                </td>
              </tr>
            ) : table.getRowModel().rows.length > 0 ? (
              table.getRowModel().rows.map((row) => (
                <tr
                  key={row.id}
                  onClick={() => onRowClick?.(row.original)}
                  className={cn(
                    "border-b last:border-0 hover:bg-gray-50",
                    row.getIsSelected() && "bg-blue-50",
                    onRowClick && "cursor-pointer"
                  )}
                >
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="px-4 py-3">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={tableColumns.length} className="px-4 py-12 text-center text-gray-500">
                  {t.emptyLabel}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {pagination && (
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-600">
            {selectedRows.length > 0 ? (
              <span>
                {t.selectedCount(
                  selectedRows.length,
                  serverSidePagination?.totalRows ?? table.getFilteredRowModel().rows.length
                )}
              </span>
            ) : (
              <span>
                {t.totalCount(
                  serverSidePagination?.totalRows ?? table.getFilteredRowModel().rows.length
                )}
              </span>
            )}
          </div>

          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600">{t.rowsPerPage}</span>
              <select
                value={currentPageSize}
                onChange={(e) => {
                  const newSize = Number(e.target.value);
                  if (serverSidePagination) {
                    serverSidePagination.onPageSizeChange(newSize);
                  } else {
                    setPaginationState((prev) => ({ ...prev, pageSize: newSize }));
                    table.setPageSize(newSize);
                  }
                }}
                className="h-8 px-2 rounded border border-gray-300 text-sm"
              >
                {pageSizeOptions.map((size) => (
                  <option key={size} value={size}>
                    {size}
                  </option>
                ))}
              </select>
            </div>

            <span className="text-sm text-gray-600">
              {t.pageOf(currentPage + 1, pageCount || 1)}
            </span>

            <div className="flex items-center gap-2">
              <button
                onClick={() => {
                  if (serverSidePagination) {
                    serverSidePagination.onPageChange(currentPage - 1);
                  } else {
                    table.previousPage();
                  }
                }}
                disabled={currentPage === 0}
                className="h-8 px-3 rounded border border-gray-300 text-sm disabled:opacity-50 hover:bg-gray-50"
              >
                {t.previous}
              </button>
              <button
                onClick={() => {
                  if (serverSidePagination) {
                    serverSidePagination.onPageChange(currentPage + 1);
                  } else {
                    table.nextPage();
                  }
                }}
                disabled={currentPage >= pageCount - 1}
                className="h-8 px-3 rounded border border-gray-300 text-sm disabled:opacity-50 hover:bg-gray-50"
              >
                {t.next}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default DataTable;
