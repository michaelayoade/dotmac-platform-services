/**
 * Admin Portal Data Table Component
 *
 * High-density data table optimized for admin interfaces. Supports advanced
 * features like sorting, filtering, bulk actions, and inline editing.
 */

import {
  DataTable as PrimitiveDataTable,
  type DataTableProps as PrimitiveDataTableProps,
} from '@dotmac/primitives';
import * as React from 'react';
import { cn } from '../lib/utils';
import { AdminButton } from './Button';
import { AdminInput } from './Input';

/**
 * Admin Data Table component props
 */
export interface AdminDataTableProps<T = Record<string, unknown>>
  extends PrimitiveDataTableProps<T> {
  /**
   * Enable bulk actions with checkboxes
   */
  enableBulkActions?: boolean;
  /**
   * Bulk action buttons
   */
  bulkActions?: Array<{
    label: string;
    icon?: React.ReactNode;
    variant?: 'default' | 'destructive' | 'outline';
    action: (selectedRows: T[]) => void;
  }>;
  /**
   * Enable inline editing for cells
   */
  enableInlineEdit?: boolean;
  /**
   * Quick filter/search input
   */
  enableQuickFilter?: boolean;
  /**
   * Placeholder text for quick filter
   */
  quickFilterPlaceholder?: string;
  /**
   * Quick filter value
   */
  quickFilterValue?: string;
  /**
   * Quick filter change handler
   */
  onQuickFilterChange?: (value: string) => void;
  /**
   * Compact row height for dense data
   */
  compact?: boolean;
  /**
   * Show row numbers
   */
  showRowNumbers?: boolean;
}

/**
 * Admin Portal Data Table Component
 *
 * High-performance data table designed for admin interfaces. Features dense
 * layout, advanced controls, and optimizations for large datasets.
 *
 * @example
 * ```tsx
 * const columns: Column<Customer>[] = [
 *   {
 *     key: 'name',
 *     title: 'Customer Name',
 *     dataIndex: 'name',
 *     sortable: true,
 *     width: 200,
 *   },
 *   {
 *     key: 'email',
 *     title: 'Email',
 *     dataIndex: 'email',
 *     render: (email) => (
 *       <a href={`mailto:${email}`} className="text-admin-primary hover:underline">
 *         {email}
 *       </a>
 *     ),
 *   },
 *   {
 *     key: 'status',
 *     title: 'Status',
 *     dataIndex: 'status',
 *     render: (status) => (
 *       <AdminBadge variant={status === 'active' ? 'success' : 'secondary'}>
 *         {status}
 *       </AdminBadge>
 *     ),
 *   },
 *   {
 *     key: 'actions',
 *     title: 'Actions',
 *     width: 120,
 *     render: (_, customer) => (
 *       <div className="flex items-center space-x-1">
 *         <AdminButton size="sm" variant="ghost">
 *           <EditIcon />
 *         </AdminButton>
 *         <AdminButton size="sm" variant="ghost">
 *           <DeleteIcon />
 *         </AdminButton>
 *       </div>
 *     ),
 *   },
 * ];
 *
 * <AdminDataTable
 *   columns={columns}
 *   data={customers}
 *   enableBulkActions
 *   enableQuickFilter
 *   compact
 *   bulkActions={[
 *     {
 *       label: 'Export Selected',
 *       icon: <ExportIcon />,
 *       variant: 'outline',
 *       action: (rows) => exportCustomers(rows),
 *     },
 *     {
 *       label: 'Delete Selected',
 *       icon: <DeleteIcon />,
 *       variant: 'destructive',
 *       action: (rows) => deleteCustomers(rows),
 *     },
 *   ]}
 *   pagination={{
 *     current: 1,
 *     pageSize: 50,
 *     total: 1000,
 *     onChange: handlePaginationChange,
 *   }}
 *   sorting={{
 *     field: 'name',
 *     order: 'asc',
 *     onChange: handleSortChange,
 *   }}
 * />
 * ```
 */
export function AdminDataTable<T = Record<string, unknown>>({
  className,
  columns,
  data,
  enableBulkActions = false,
  bulkActions = [],
  enableQuickFilter = false,
  quickFilterPlaceholder = 'Search...',
  quickFilterValue = '',
  onQuickFilterChange,
  compact = true,
  showRowNumbers = false,
  enableInlineEdit: _enableInlineEdit,
  selection,
  ...props
}: AdminDataTableProps<T>) {
  const [selectedRows, setSelectedRows] = React.useState<T[]>([]);

  // Handle selection changes
  const handleSelectionChange = React.useCallback(
    (selectedKeys: string[]) => {
      if (selection?.getRowKey) {
        const selected = data.filter((item) => selectedKeys.includes(selection.getRowKey?.(item)));
        setSelectedRows(selected);
      }
      selection?.onChange?.(selectedKeys);
    },
    [data, selection]
  );

  // Enhanced columns with row numbers
  const enhancedColumns = React.useMemo(() => {
    const cols = [...columns];

    if (showRowNumbers) {
      cols.unshift({
        key: '__row_number',
        title: '#',
        width: 60,
        render: (_, __, index) => (
          <span className='text-admin-muted-foreground text-xs'>
            {(props.pagination?.current || 1 - 1) * (props.pagination?.pageSize || 10) + index + 1}
          </span>
        ),
      });
    }

    return cols;
  }, [columns, showRowNumbers, props.pagination]);

  return (
    <div className='space-y-3'>
      {/* Table Controls */}
      <div className='flex items-center justify-between'>
        <div className='flex items-center space-x-2'>
          {enableQuickFilter && (
            <AdminInput
              placeholder={quickFilterPlaceholder}
              value={quickFilterValue}
              onChange={(e) => onQuickFilterChange?.(e.target.value)}
              size='sm'
              className='w-64'
              leftIcon={
                <svg
                  aria-label='icon'
                  className='h-4 w-4'
                  fill='none'
                  stroke='currentColor'
                  viewBox='0 0 24 24'
                >
                  <title>Icon</title>
                  <path
                    strokeLinecap='round'
                    strokeLinejoin='round'
                    strokeWidth={2}
                    d='M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z'
                  />
                </svg>
              }
            />
          )}

          {enableBulkActions && selectedRows.length > 0 && (
            <div className='flex items-center space-x-2'>
              <span className='text-admin-muted-foreground text-xs'>
                {selectedRows.length} selected
              </span>
              {bulkActions.map((action, index) => (
                <AdminButton
                  key={`item-${index}`}
                  size='sm'
                  variant={action.variant || 'outline'}
                  onClick={() => action.action(selectedRows)}
                  leftIcon={action.icon}
                >
                  {action.label}
                </AdminButton>
              ))}
            </div>
          )}
        </div>

        <div className='flex items-center space-x-2'>{/* Additional controls can go here */}</div>
      </div>

      {/* Data Table */}
      <div className='rounded-md border border-admin-border'>
        <PrimitiveDataTable
          className={cn(
            'admin-data-table',
            {
              compact: compact,
            },
            className
          )}
          columns={enhancedColumns}
          data={data}
          selection={
            enableBulkActions
              ? {
                  ...selection,
                  onChange: handleSelectionChange,
                }
              : undefined
          }
          {...props}
        />
      </div>

      {/* Table Footer with Pagination Info */}
      {props.pagination && (
        <div className='flex items-center justify-between text-admin-muted-foreground text-xs'>
          <div>
            Showing {(props.pagination.current - 1) * props.pagination.pageSize + 1} to{' '}
            {Math.min(props.pagination.current * props.pagination.pageSize, props.pagination.total)}{' '}
            of {props.pagination.total} results
          </div>

          <div className='flex items-center space-x-2'>
            <AdminButton
              size='sm'
              variant='outline'
              disabled={props.pagination.current <= 1}
              onClick={() =>
                props.pagination?.onChange?.(
                  props.pagination.current - 1,
                  props.pagination.pageSize
                )
              }
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  props.pagination?.onChange?.(
                    props.pagination.current - 1,
                    props.pagination.pageSize
                  );
                }
              }}
            >
              Previous
            </AdminButton>

            <span className='px-2'>
              Page {props.pagination.current} of{' '}
              {Math.ceil(props.pagination.total / props.pagination.pageSize)}
            </span>

            <AdminButton
              size='sm'
              variant='outline'
              disabled={
                props.pagination.current >=
                Math.ceil(props.pagination.total / props.pagination.pageSize)
              }
              onClick={() =>
                props.pagination?.onChange?.(
                  props.pagination.current + 1,
                  props.pagination.pageSize
                )
              }
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  props.pagination?.onChange?.(
                    props.pagination.current + 1,
                    props.pagination.pageSize
                  );
                }
              }}
            >
              Next
            </AdminButton>
          </div>
        </div>
      )}
    </div>
  );
}

AdminDataTable.displayName = 'AdminDataTable';

export type { AdminDataTableProps };
