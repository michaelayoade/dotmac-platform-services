/**
 * Universal Data Table Component
 *
 * ELIMINATES DUPLICATION: Consolidates ALL table implementations across the platform
 * - Admin Portal: InvoicesTable, CustomersTable, UsersTable, etc.
 * - Customer Portal: BillingHistory, UsageHistory, TicketsTable, etc.
 * - Reseller Portal: ClientsTable, CommissionsTable, etc.
 * - Technician Portal: WorkOrdersTable, DevicesTable, etc.
 * - Management Portal: RevenueTable, MetricsTable, etc.
 *
 * SINGLE SOURCE OF TRUTH for all data table functionality
 */

'use client';

import React, { useMemo, useState, useCallback, useRef } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getGroupedRowModel,
  getExpandedRowModel,
  flexRender,
  type ColumnDef,
  type SortingState,
  type ColumnFiltersState,
  type VisibilityState,
  type RowSelectionState,
  type PaginationState,
} from '@tanstack/react-table';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ChevronDown,
  ChevronRight,
  ChevronUp,
  MoreHorizontal,
  RefreshCw,
  Download,
  Search,
  Filter,
  Eye,
  EyeOff,
  Settings,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Loader2,
  AlertCircle,
  Inbox,
  CheckSquare,
  Square,
  Minus,
} from 'lucide-react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../utils/cn';
import type {
  UniversalDataTableProps,
  PortalVariant,
  TableState,
  TableAction,
  BulkOperation,
} from '../types';
import { TableToolbar } from './TableToolbar';
import { TablePagination } from './TablePagination';
import { TableSearch } from './TableSearch';
import { TableFilters } from './TableFilters';
import { BulkActions } from './BulkActions';
import { LoadingSpinner } from './LoadingSpinner';
import { ErrorDisplay } from './ErrorDisplay';
import { EmptyState } from './EmptyState';

// Portal-aware styling variants
const tableVariants = cva('w-full border-separate border-spacing-0 bg-white dark:bg-gray-900', {
  variants: {
    variant: {
      default: 'border border-gray-200 dark:border-gray-800',
      striped: 'border border-gray-200 dark:border-gray-800',
      bordered: 'border border-gray-300 dark:border-gray-700',
      compact: 'border border-gray-200 dark:border-gray-800',
      spacious: 'border border-gray-200 dark:border-gray-800',
    },
    size: {
      xs: 'text-xs',
      sm: 'text-sm',
      md: 'text-sm',
      lg: 'text-base',
      xl: 'text-lg',
    },
    portal: {
      admin: 'border-blue-200 dark:border-blue-800',
      customer: 'border-green-200 dark:border-green-800',
      reseller: 'border-purple-200 dark:border-purple-800',
      technician: 'border-orange-200 dark:border-orange-800',
      management: 'border-indigo-200 dark:border-indigo-800',
    } as Record<PortalVariant, string>,
  },
});

const headerVariants = cva('sticky top-0 z-10 border-b bg-gray-50 dark:bg-gray-800', {
  variants: {
    portal: {
      admin: 'border-blue-200 bg-blue-50 dark:bg-blue-950 dark:border-blue-800',
      customer: 'border-green-200 bg-green-50 dark:bg-green-950 dark:border-green-800',
      reseller: 'border-purple-200 bg-purple-50 dark:bg-purple-950 dark:border-purple-800',
      technician: 'border-orange-200 bg-orange-50 dark:bg-orange-950 dark:border-orange-800',
      management: 'border-indigo-200 bg-indigo-50 dark:bg-indigo-950 dark:border-indigo-800',
    } as Record<PortalVariant, string>,
  },
});

const rowVariants = cva(
  'transition-colors duration-150 border-b border-gray-100 dark:border-gray-800',
  {
    variants: {
      variant: {
        default: 'hover:bg-gray-50 dark:hover:bg-gray-800',
        striped: 'odd:bg-gray-50 dark:odd:bg-gray-900 hover:bg-gray-100 dark:hover:bg-gray-800',
        bordered: 'hover:bg-gray-50 dark:hover:bg-gray-800',
        compact: 'hover:bg-gray-50 dark:hover:bg-gray-800',
        spacious: 'hover:bg-gray-50 dark:hover:bg-gray-800',
      },
      selected: {
        true: 'bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800',
        false: '',
      },
      portal: {
        admin: 'hover:bg-blue-50/30 dark:hover:bg-blue-950/30',
        customer: 'hover:bg-green-50/30 dark:hover:bg-green-950/30',
        reseller: 'hover:bg-purple-50/30 dark:hover:bg-purple-950/30',
        technician: 'hover:bg-orange-50/30 dark:hover:bg-orange-950/30',
        management: 'hover:bg-indigo-50/30 dark:hover:bg-indigo-950/30',
      } as Record<PortalVariant, string>,
    },
  }
);

const cellVariants = cva('px-4 py-3 text-left', {
  variants: {
    size: {
      xs: 'px-2 py-1 text-xs',
      sm: 'px-3 py-2 text-sm',
      md: 'px-4 py-3 text-sm',
      lg: 'px-6 py-4 text-base',
      xl: 'px-8 py-6 text-lg',
    },
    density: {
      comfortable: '',
      compact: 'py-2',
      spacious: 'py-4',
    },
    align: {
      left: 'text-left',
      center: 'text-center',
      right: 'text-right',
    },
  },
});

export function UniversalDataTable<TData = any>({
  // Data
  data,
  columns,

  // Identity
  id = 'universal-data-table',

  // Portal Integration
  portal = 'admin',

  // Core Features
  enableSorting = true,
  enableFiltering = true,
  enableGlobalFilter = true,
  enablePagination = true,
  enableSelection = false,
  enableMultiRowSelection = true,

  // Configuration
  searchConfig = { enabled: true },
  exportConfig,

  // Pagination
  pageSize = 10,
  pageSizeOptions = [5, 10, 25, 50, 100],

  // Selection
  rowSelectionMode = 'multiple',
  getRowId,

  // Actions
  actions = [],
  bulkActions = [],
  toolbarActions = [],

  // UI Customization
  variant = 'default',
  size = 'md',
  density = 'comfortable',

  // Layout
  height,
  maxHeight,
  stickyHeader = true,

  // State Management
  initialState,

  // Loading & Error States
  loading = false,
  error = null,
  emptyState,

  // Events
  onRowClick,
  onSelectionChange,
  onSortingChange,
  onFilteringChange,
  onGlobalFilterChange,

  // Styling
  className = '',
  tableClassName = '',
  rowClassName = '',

  // Custom Components
  components = {},

  ...rest
}: UniversalDataTableProps<TData>) {
  // ===========================
  // State Management
  // ===========================

  const [sorting, setSorting] = useState<SortingState>(initialState?.sorting || []);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>(
    initialState?.columnFilters || []
  );
  const [globalFilter, setGlobalFilter] = useState<string>(initialState?.globalFilter || '');
  const [pagination, setPagination] = useState<PaginationState>(
    initialState?.pagination || { pageIndex: 0, pageSize }
  );
  const [rowSelection, setRowSelection] = useState<RowSelectionState>(
    initialState?.rowSelection || {}
  );
  const [columnVisibility, setColumnVisibility] = useState<VisibilityState>(
    initialState?.columnVisibility || {}
  );

  const containerRef = useRef<HTMLDivElement>(null);

  // ===========================
  // Table Configuration
  // ===========================

  const table = useReactTable({
    data,
    columns: columns as ColumnDef<TData>[],

    // Core
    getCoreRowModel: getCoreRowModel(),

    // Sorting
    enableSorting,
    getSortedRowModel: getSortedRowModel(),
    onSortingChange: (updater) => {
      const newSorting = typeof updater === 'function' ? updater(sorting) : updater;
      setSorting(newSorting);
      onSortingChange?.(newSorting);
    },

    // Filtering
    enableColumnFilters: enableFiltering,
    enableGlobalFilter,
    getFilteredRowModel: getFilteredRowModel(),
    onColumnFiltersChange: (updater) => {
      const newFilters = typeof updater === 'function' ? updater(columnFilters) : updater;
      setColumnFilters(newFilters);
      onFilteringChange?.(newFilters);
    },
    onGlobalFilterChange: (updater) => {
      const newFilter = typeof updater === 'function' ? updater(globalFilter) : updater;
      setGlobalFilter(newFilter);
      onGlobalFilterChange?.(newFilter);
    },

    // Pagination
    enablePagination,
    getPaginationRowModel: getPaginationRowModel(),
    onPaginationChange: setPagination,

    // Selection
    enableRowSelection: enableSelection,
    enableMultiRowSelection: enableMultiRowSelection,
    onRowSelectionChange: (updater) => {
      const newSelection = typeof updater === 'function' ? updater(rowSelection) : updater;
      setRowSelection(newSelection);

      // Get selected rows for callback
      if (onSelectionChange) {
        const selectedRows = Object.keys(newSelection)
          .filter((key) => newSelection[key])
          .map((key) => {
            const index = parseInt(key);
            return table.getRowModel().rows[index]?.original;
          })
          .filter(Boolean);
        onSelectionChange(selectedRows);
      }
    },

    // Column Visibility
    onColumnVisibilityChange: setColumnVisibility,

    // Row ID
    getRowId: getRowId || ((row, index) => `${index}`),

    // Initial State
    initialState: {
      pagination: { pageIndex: 0, pageSize },
      ...initialState,
    },

    // Current State
    state: {
      sorting,
      columnFilters,
      globalFilter,
      pagination,
      rowSelection,
      columnVisibility,
    },
  });

  // ===========================
  // Derived Values
  // ===========================

  const selectedRows = useMemo(() => {
    return table.getSelectedRowModel().rows.map((row) => row.original);
  }, [table, rowSelection]);

  const hasSelection = selectedRows.length > 0;
  const totalRows = table.getFilteredRowModel().rows.length;
  const visibleRows = table.getRowModel().rows;

  // ===========================
  // Event Handlers
  // ===========================

  const handleRowClick = useCallback(
    (row: TData, event: React.MouseEvent) => {
      if (onRowClick) {
        onRowClick(row, event as any);
      }
    },
    [onRowClick]
  );

  const handleSelectAll = useCallback(() => {
    table.toggleAllRowsSelected();
  }, [table]);

  const handleClearSelection = useCallback(() => {
    table.resetRowSelection();
  }, [table]);

  const handleExport = useCallback(
    async (format: 'csv' | 'xlsx' | 'json' | 'pdf') => {
      // Implementation would go here - this is a placeholder
      // TODO: Implement export functionality for ${format} format
      // In real implementation, would use libraries like:
      // - csv: Papa Parse or custom CSV generator
      // - xlsx: SheetJS (xlsx)
      // - json: JSON.stringify
      // - pdf: jsPDF with autoTable plugin
    },
    [selectedRows, totalRows]
  );

  const handleRefresh = useCallback(() => {
    // Emit refresh event - parent component should handle data refetch
    // This is just a placeholder implementation
    // Refresh requested - handled by parent component
  }, []);

  // ===========================
  // Render Helpers
  // ===========================

  const renderCell = useCallback(
    (cell: any, row: any) => {
      const content = flexRender(cell.column.columnDef.cell, cell.getContext());
      const align = cell.column.columnDef.meta?.align || 'left';

      return (
        <td
          key={cell.id}
          className={cn(
            cellVariants({
              size,
              density,
              align: align as 'left' | 'center' | 'right',
            }),
            cell.column.columnDef.meta?.cellClassName
          )}
        >
          {content}
        </td>
      );
    },
    [size, density]
  );

  const renderHeaderCell = useCallback(
    (header: any) => {
      const canSort = header.column.getCanSort();
      const sortDirection = header.column.getIsSorted();
      const align = header.column.columnDef.meta?.align || 'left';

      return (
        <th
          key={header.id}
          className={cn(
            cellVariants({
              size,
              density,
              align: align as 'left' | 'center' | 'right',
            }),
            'font-medium text-gray-900 dark:text-gray-100',
            canSort && 'cursor-pointer select-none hover:bg-gray-100 dark:hover:bg-gray-800',
            header.column.columnDef.meta?.headerClassName
          )}
          onClick={canSort ? header.column.getToggleSortingHandler() : undefined}
          style={{ width: header.column.columnDef.meta?.width }}
        >
          <div className='flex items-center space-x-2'>
            <span>{flexRender(header.column.columnDef.header, header.getContext())}</span>
            {canSort && (
              <span className='ml-2'>
                {sortDirection === 'asc' && <ArrowUp className='h-4 w-4' />}
                {sortDirection === 'desc' && <ArrowDown className='h-4 w-4' />}
                {!sortDirection && <ArrowUpDown className='h-4 w-4 opacity-50' />}
              </span>
            )}
          </div>
        </th>
      );
    },
    [size, density]
  );

  // ===========================
  // Loading & Error States
  // ===========================

  if (loading) {
    return (
      <div className='space-y-4'>
        <div className='flex items-center justify-between'>
          <div className='h-8 w-48 bg-gray-200 rounded animate-pulse' />
          <div className='flex space-x-2'>
            <div className='h-8 w-24 bg-gray-200 rounded animate-pulse' />
            <div className='h-8 w-24 bg-gray-200 rounded animate-pulse' />
          </div>
        </div>
        <div className='border border-gray-200 rounded-lg p-8'>
          <LoadingSpinner size='lg' />
          <p className='text-center text-gray-500 mt-4'>Loading data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return <ErrorDisplay error={error} onRetry={handleRefresh} />;
  }

  if (!data.length && !loading) {
    return (
      <div className='space-y-4'>
        {(searchConfig?.enabled || enableFiltering || toolbarActions.length > 0) && (
          <TableToolbar
            table={table}
            portal={portal}
            searchConfig={searchConfig}
            enableFiltering={enableFiltering}
            actions={toolbarActions}
            onRefresh={handleRefresh}
            onExport={exportConfig ? handleExport : undefined}
          />
        )}
        {emptyState || (
          <EmptyState
            icon={Inbox}
            title='No data found'
            description='There are no items to display.'
            portal={portal}
          />
        )}
      </div>
    );
  }

  // ===========================
  // Main Render
  // ===========================

  return (
    <div className={cn('space-y-4', className)} ref={containerRef}>
      {/* Toolbar */}
      {(searchConfig?.enabled || enableFiltering || toolbarActions.length > 0 || hasSelection) && (
        <div className='flex items-center justify-between gap-4'>
          <div className='flex items-center space-x-4 flex-1'>
            {searchConfig?.enabled && (
              <TableSearch
                value={globalFilter}
                onChange={setGlobalFilter}
                placeholder={searchConfig.placeholder}
                portal={portal}
                debounceMs={searchConfig.debounceMs}
              />
            )}

            {enableFiltering && <TableFilters table={table} portal={portal} />}
          </div>

          <div className='flex items-center space-x-2'>
            {toolbarActions.map((action) => (
              <button
                key={action.id}
                onClick={() => action.onClick(data)}
                disabled={action.disabled || action.loading}
                className={cn(
                  'inline-flex items-center px-3 py-2 text-sm font-medium rounded-md',
                  'border border-gray-300 bg-white hover:bg-gray-50',
                  'focus:outline-none focus:ring-2 focus:ring-offset-2',
                  portal === 'admin' && 'focus:ring-blue-500',
                  portal === 'customer' && 'focus:ring-green-500',
                  portal === 'reseller' && 'focus:ring-purple-500',
                  portal === 'technician' && 'focus:ring-orange-500',
                  portal === 'management' && 'focus:ring-indigo-500'
                )}
                title={action.tooltip}
              >
                {action.icon && <action.icon className='h-4 w-4 mr-2' />}
                {action.label}
              </button>
            ))}

            <button
              onClick={handleRefresh}
              className='p-2 text-gray-400 hover:text-gray-600 rounded-md hover:bg-gray-100'
              title='Refresh'
            >
              <RefreshCw className='h-4 w-4' />
            </button>
          </div>
        </div>
      )}

      {/* Bulk Actions */}
      <AnimatePresence>
        {hasSelection && bulkActions.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
          >
            <BulkActions
              selectedCount={selectedRows.length}
              totalCount={totalRows}
              actions={bulkActions}
              selectedData={selectedRows}
              portal={portal}
              onClearSelection={handleClearSelection}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Table */}
      <div
        className={cn(
          'relative overflow-hidden rounded-lg border border-gray-200 dark:border-gray-800',
          maxHeight && 'overflow-y-auto'
        )}
        style={{ height, maxHeight }}
      >
        <table className={cn(tableVariants({ variant, size, portal }), tableClassName)}>
          {/* Header */}
          <thead className={cn(headerVariants({ portal }), stickyHeader && 'sticky top-0 z-10')}>
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {enableSelection && (
                  <th className={cn(cellVariants({ size, density }), 'w-12')}>
                    <div className='flex items-center justify-center'>
                      {enableMultiRowSelection ? (
                        <button
                          onClick={handleSelectAll}
                          className='p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-800'
                        >
                          {table.getIsAllRowsSelected() ? (
                            <CheckSquare className='h-4 w-4' />
                          ) : table.getIsSomeRowsSelected() ? (
                            <Minus className='h-4 w-4' />
                          ) : (
                            <Square className='h-4 w-4' />
                          )}
                        </button>
                      ) : null}
                    </div>
                  </th>
                )}

                {headerGroup.headers.map(renderHeaderCell)}

                {actions.length > 0 && (
                  <th className={cn(cellVariants({ size, density }), 'w-20')}>
                    <span className='sr-only'>Actions</span>
                  </th>
                )}
              </tr>
            ))}
          </thead>

          {/* Body */}
          <tbody className='divide-y divide-gray-200 dark:divide-gray-800'>
            {visibleRows.map((row) => {
              const isSelected = row.getIsSelected();
              const rowData = row.original;

              return (
                <motion.tr
                  key={row.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className={cn(
                    rowVariants({ variant, selected: isSelected, portal }),
                    typeof rowClassName === 'function'
                      ? rowClassName(rowData, row.index)
                      : rowClassName,
                    onRowClick && 'cursor-pointer'
                  )}
                  onClick={(e) => handleRowClick(rowData, e)}
                >
                  {/* Selection Column */}
                  {enableSelection && (
                    <td className={cn(cellVariants({ size, density }))}>
                      <div className='flex items-center justify-center'>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            row.toggleSelected();
                          }}
                          className='p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-800'
                        >
                          {isSelected ? (
                            <CheckSquare className='h-4 w-4' />
                          ) : (
                            <Square className='h-4 w-4' />
                          )}
                        </button>
                      </div>
                    </td>
                  )}

                  {/* Data Columns */}
                  {row.getVisibleCells().map((cell) => renderCell(cell, row))}

                  {/* Actions Column */}
                  {actions.length > 0 && (
                    <td className={cn(cellVariants({ size, density }))}>
                      <div className='flex items-center justify-end space-x-1'>
                        {actions
                          .filter(
                            (action) =>
                              action.visible !== false &&
                              (typeof action.visible !== 'function' || action.visible(rowData))
                          )
                          .map((action) => (
                            <button
                              key={action.id}
                              onClick={(e) => {
                                e.stopPropagation();
                                action.onClick(rowData);
                              }}
                              disabled={
                                action.disabled ||
                                (typeof action.disabled === 'function' && action.disabled(rowData))
                              }
                              className='p-1 text-gray-400 hover:text-gray-600 rounded hover:bg-gray-100 dark:hover:bg-gray-800'
                              title={action.tooltip || action.label}
                            >
                              {action.icon ? <action.icon className='h-4 w-4' /> : action.label}
                            </button>
                          ))}
                      </div>
                    </td>
                  )}
                </motion.tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {enablePagination && (
        <TablePagination table={table} pageSizeOptions={pageSizeOptions} portal={portal} />
      )}
    </div>
  );
}

export default UniversalDataTable;
