/**
 * Universal EntityManagementTable Component
 * Production-ready, portal-agnostic entity management with CRUD operations
 * DRY pattern: Same table, different entities across all portals
 */

import React, { useState, useMemo, useCallback } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search,
  Filter,
  MoreVertical,
  ChevronUp,
  ChevronDown,
  Eye,
  Edit,
  Trash2,
  Plus,
  Download,
  RefreshCw,
  X,
} from 'lucide-react';
import { Card, Button, Input } from '@dotmac/primitives';
import type { PortalVariant, TableColumn, EntityAction } from '../../types';
import { cn } from '../../utils/cn';

const tableVariants = cva('w-full border-collapse', {
  variants: {
    variant: {
      admin: 'border-blue-200',
      customer: 'border-green-200',
      reseller: 'border-purple-200',
      technician: 'border-orange-200',
      management: 'border-indigo-200',
    },
  },
});

const headerVariants = cva(
  'px-4 py-3 text-left text-xs font-medium uppercase tracking-wider border-b',
  {
    variants: {
      variant: {
        admin: 'bg-blue-50 text-blue-900 border-blue-200',
        customer: 'bg-green-50 text-green-900 border-green-200',
        reseller: 'bg-purple-50 text-purple-900 border-purple-200',
        technician: 'bg-orange-50 text-orange-900 border-orange-200',
        management: 'bg-indigo-50 text-indigo-900 border-indigo-200',
      },
    },
  }
);

const rowVariants = cva('transition-colors duration-200 border-b border-gray-100', {
  variants: {
    variant: {
      admin: 'hover:bg-blue-50/30',
      customer: 'hover:bg-green-50/30',
      reseller: 'hover:bg-purple-50/30',
      technician: 'hover:bg-orange-50/30',
      management: 'hover:bg-indigo-50/30',
    },
    state: {
      normal: '',
      selected: 'bg-gray-50',
      disabled: 'opacity-50 cursor-not-allowed',
    },
  },
});

export interface EntityManagementTableProps<T = any> extends VariantProps<typeof tableVariants> {
  data: T[];
  columns: TableColumn[];
  variant: PortalVariant;
  className?: string;
  loading?: boolean;

  // Selection
  selectable?: boolean;
  selectedIds?: string[];
  onSelectionChange?: (selectedIds: string[]) => void;

  // Actions
  actions?: EntityAction[];
  primaryAction?: EntityAction;
  bulkActions?: EntityAction[];

  // Filtering & Search
  searchable?: boolean;
  searchPlaceholder?: string;
  filters?: Array<{
    key: string;
    label: string;
    options: Array<{ value: string; label: string }>;
  }>;

  // Sorting
  sortable?: boolean;
  defaultSort?: { column: string; direction: 'asc' | 'desc' };
  onSortChange?: (column: string, direction: 'asc' | 'desc') => void;

  // Pagination
  pagination?: {
    page: number;
    pageSize: number;
    total: number;
    onPageChange: (page: number) => void;
    onPageSizeChange: (pageSize: number) => void;
  };

  // Events
  onRowClick?: (entity: T) => void;
  onRefresh?: () => void;
  onExport?: (format: 'csv' | 'json') => void;

  // Customization
  emptyState?: React.ReactNode;
  rowKey?: string;
}

export const EntityManagementTable = <T extends Record<string, any>>({
  data,
  columns,
  variant,
  className,
  loading = false,
  selectable = false,
  selectedIds = [],
  onSelectionChange,
  actions = [],
  primaryAction,
  bulkActions = [],
  searchable = true,
  searchPlaceholder = 'Search...',
  filters = [],
  sortable = true,
  defaultSort,
  onSortChange,
  pagination,
  onRowClick,
  onRefresh,
  onExport,
  emptyState,
  rowKey = 'id',
  ...props
}: EntityManagementTableProps<T>) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeFilters, setActiveFilters] = useState<Record<string, string>>({});
  const [sortConfig, setSortConfig] = useState(
    defaultSort || { column: '', direction: 'asc' as const }
  );
  const [showFilters, setShowFilters] = useState(false);
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());

  // Memoized filtered and sorted data
  const processedData = useMemo(() => {
    let filtered = [...data];

    // Apply search
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter((item) =>
        columns.some((column) => {
          const value = item[column.key];
          return String(value).toLowerCase().includes(query);
        })
      );
    }

    // Apply filters
    Object.entries(activeFilters).forEach(([key, value]) => {
      if (value) {
        filtered = filtered.filter((item) => String(item[key]) === value);
      }
    });

    // Apply sorting
    if (sortConfig.column) {
      filtered.sort((a, b) => {
        const aVal = a[sortConfig.column];
        const bVal = b[sortConfig.column];

        let comparison = 0;
        if (aVal > bVal) comparison = 1;
        if (aVal < bVal) comparison = -1;

        return sortConfig.direction === 'desc' ? -comparison : comparison;
      });
    }

    return filtered;
  }, [data, searchQuery, activeFilters, sortConfig, columns]);

  // Handle sorting
  const handleSort = useCallback(
    (column: string) => {
      if (!sortable) return;

      const direction =
        sortConfig.column === column && sortConfig.direction === 'asc' ? 'desc' : 'asc';

      setSortConfig({ column, direction });
      onSortChange?.(column, direction);
    },
    [sortConfig, sortable, onSortChange]
  );

  // Handle selection
  const handleSelectAll = useCallback(() => {
    if (!onSelectionChange) return;

    const allIds = processedData.map((item) => item[rowKey]);
    const isAllSelected = allIds.every((id) => selectedIds.includes(id));

    onSelectionChange(isAllSelected ? [] : allIds);
  }, [processedData, selectedIds, onSelectionChange, rowKey]);

  const handleSelectRow = useCallback(
    (id: string) => {
      if (!onSelectionChange) return;

      const newSelection = selectedIds.includes(id)
        ? selectedIds.filter((selectedId) => selectedId !== id)
        : [...selectedIds, id];

      onSelectionChange(newSelection);
    },
    [selectedIds, onSelectionChange]
  );

  // Action handlers
  const handleActionClick = useCallback((action: EntityAction, entity: T) => {
    if (action.isDisabled?.(entity)) return;
    action.onClick(entity);
  }, []);

  // Loading state
  if (loading) {
    return (
      <Card className={cn('overflow-hidden', className)}>
        <div className='p-6'>
          <div className='animate-pulse space-y-4'>
            <div className='flex justify-between items-center'>
              <div className='h-8 bg-gray-200 rounded w-64'></div>
              <div className='flex gap-2'>
                <div className='h-8 w-20 bg-gray-200 rounded'></div>
                <div className='h-8 w-20 bg-gray-200 rounded'></div>
              </div>
            </div>
            <div className='space-y-2'>
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className='h-12 bg-gray-200 rounded'></div>
              ))}
            </div>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <Card className={cn('overflow-hidden', className)} {...props}>
      {/* Header Controls */}
      <div className='p-4 border-b border-gray-200'>
        <div className='flex items-center justify-between mb-4'>
          <div className='flex items-center gap-3'>
            {searchable && (
              <div className='relative'>
                <Search
                  size={16}
                  className='absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400'
                />
                <Input
                  placeholder={searchPlaceholder}
                  value={searchQuery}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setSearchQuery(e.target.value)
                  }
                  className='pl-10 w-64'
                />
              </div>
            )}

            {filters.length > 0 && (
              <Button
                variant='outline'
                size='sm'
                onClick={() => setShowFilters(!showFilters)}
                className='gap-2'
              >
                <Filter size={14} />
                Filters
              </Button>
            )}
          </div>

          <div className='flex items-center gap-2'>
            {selectedIds.length > 0 && bulkActions.length > 0 && (
              <div className='flex items-center gap-2 mr-3'>
                <span className='text-sm text-gray-600'>{selectedIds.length} selected</span>
                {bulkActions.map((action) => (
                  <Button
                    key={action.key}
                    variant={action.variant === 'danger' ? 'destructive' : 'outline'}
                    size='sm'
                    onClick={() => action.onClick(selectedIds)}
                    className='gap-1'
                  >
                    {action.icon &&
                      React.createElement(action.icon as any, { className: 'w-3.5 h-3.5' })}
                    {action.label}
                  </Button>
                ))}
              </div>
            )}

            {onExport && (
              <Button variant='outline' size='sm' onClick={() => onExport('csv')} className='gap-2'>
                <Download size={14} />
                Export
              </Button>
            )}

            {primaryAction && (
              <Button
                variant='default'
                size='sm'
                onClick={() => primaryAction.onClick({})}
                className='gap-2'
              >
                <Plus size={14} />
                {primaryAction.label}
              </Button>
            )}

            {onRefresh && (
              <Button variant='ghost' size='sm' onClick={onRefresh} className='gap-2'>
                <RefreshCw size={14} />
                Refresh
              </Button>
            )}
          </div>
        </div>

        {/* Filters Panel */}
        {showFilters && filters.length > 0 && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className='border-t border-gray-200 pt-4'
          >
            <div className='flex items-center gap-3 flex-wrap'>
              {filters.map((filter) => (
                <div key={filter.key} className='flex items-center gap-2'>
                  <label className='text-sm font-medium text-gray-700'>{filter.label}:</label>
                  <select
                    value={activeFilters[filter.key] || ''}
                    onChange={(e) =>
                      setActiveFilters((prev) => ({
                        ...prev,
                        [filter.key]: e.target.value,
                      }))
                    }
                    className='text-sm border border-gray-300 rounded px-2 py-1'
                  >
                    <option value=''>All</option>
                    {filter.options.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
              ))}

              <Button
                variant='ghost'
                size='sm'
                onClick={() => setActiveFilters({})}
                className='gap-1'
              >
                <X size={12} />
                Clear
              </Button>
            </div>
          </motion.div>
        )}
      </div>

      {/* Table */}
      <div className='overflow-x-auto'>
        <table className={cn(tableVariants({ variant }))}>
          {/* Header */}
          <thead>
            <tr>
              {selectable && (
                <th className={cn(headerVariants({ variant }), 'w-12')}>
                  <input
                    type='checkbox'
                    checked={
                      processedData.length > 0 &&
                      processedData.every((item) => selectedIds.includes(item[rowKey]))
                    }
                    onChange={handleSelectAll}
                    className='w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded'
                  />
                </th>
              )}

              {columns.map((column) => (
                <th
                  key={column.key}
                  className={cn(
                    headerVariants({ variant }),
                    column.width && { width: column.width },
                    column.sortable !== false && sortable && 'cursor-pointer select-none'
                  )}
                  onClick={() => column.sortable !== false && handleSort(column.key)}
                >
                  <div className='flex items-center gap-2'>
                    <span>{column.title}</span>
                    {column.sortable !== false && sortable && sortConfig.column === column.key && (
                      <span className='text-gray-400'>
                        {sortConfig.direction === 'asc' ? (
                          <ChevronUp size={12} />
                        ) : (
                          <ChevronDown size={12} />
                        )}
                      </span>
                    )}
                  </div>
                </th>
              ))}

              {actions.length > 0 && (
                <th className={cn(headerVariants({ variant }), 'w-20 text-center')}>Actions</th>
              )}
            </tr>
          </thead>

          {/* Body */}
          <tbody>
            <AnimatePresence>
              {processedData.length === 0 ? (
                <tr>
                  <td
                    colSpan={columns.length + (selectable ? 1 : 0) + (actions.length > 0 ? 1 : 0)}
                    className='px-4 py-12 text-center'
                  >
                    {emptyState || (
                      <div className='text-gray-500'>
                        <div className='text-4xl mb-2'>📄</div>
                        <p className='font-medium'>No data available</p>
                        <p className='text-sm text-gray-400'>
                          {searchQuery || Object.keys(activeFilters).length > 0
                            ? 'Try adjusting your search or filters'
                            : 'Get started by adding some data'}
                        </p>
                      </div>
                    )}
                  </td>
                </tr>
              ) : (
                processedData.map((item, index) => (
                  <motion.tr
                    key={item[rowKey]}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    transition={{ duration: 0.2, delay: index * 0.02 }}
                    className={cn(
                      rowVariants({
                        variant,
                        state: selectedIds.includes(item[rowKey]) ? 'selected' : 'normal',
                      }),
                      onRowClick && 'cursor-pointer'
                    )}
                    onClick={() => onRowClick?.(item)}
                  >
                    {selectable && (
                      <td className='px-4 py-3'>
                        <input
                          type='checkbox'
                          checked={selectedIds.includes(item[rowKey])}
                          onChange={() => handleSelectRow(item[rowKey])}
                          onClick={(e: React.MouseEvent) => e.stopPropagation()}
                          className='w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded'
                        />
                      </td>
                    )}

                    {columns.map((column) => (
                      <td key={column.key} className='px-4 py-3 text-sm text-gray-900'>
                        {column.render
                          ? column.render(item[column.key], item)
                          : String(item[column.key] || '-')}
                      </td>
                    ))}

                    {actions.length > 0 && (
                      <td className='px-4 py-3 text-center'>
                        <div className='flex items-center justify-center gap-1'>
                          {actions
                            .filter((action) => action.isVisible?.(item) !== false)
                            .slice(0, 2)
                            .map((action) => (
                              <Button
                                key={action.key}
                                variant='ghost'
                                size='sm'
                                onClick={(e: React.MouseEvent) => {
                                  e.stopPropagation();
                                  handleActionClick(action, item);
                                }}
                                disabled={action.isDisabled?.(item)}
                                className='h-8 w-8 p-0'
                              >
                                {action.icon &&
                                  React.createElement(action.icon as any, {
                                    className: 'w-3.5 h-3.5',
                                  })}
                              </Button>
                            ))}

                          {actions.filter((action) => action.isVisible?.(item) !== false).length >
                            2 && (
                            <Button
                              variant='ghost'
                              size='sm'
                              className='h-8 w-8 p-0'
                              onClick={(e: React.MouseEvent) => e.stopPropagation()}
                            >
                              <MoreVertical className='w-3.5 h-3.5' />
                            </Button>
                          )}
                        </div>
                      </td>
                    )}
                  </motion.tr>
                ))
              )}
            </AnimatePresence>
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {pagination && (
        <div className='px-4 py-3 border-t border-gray-200 flex items-center justify-between'>
          <div className='flex items-center gap-2 text-sm text-gray-600'>
            <span>Show</span>
            <select
              value={pagination.pageSize}
              onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
                pagination.onPageSizeChange(Number(e.target.value))
              }
              className='border border-gray-300 rounded px-2 py-1'
            >
              {[10, 25, 50, 100].map((size) => (
                <option key={size} value={size}>
                  {size}
                </option>
              ))}
            </select>
            <span>of {pagination.total} entries</span>
          </div>

          <div className='flex items-center gap-2'>
            <Button
              variant='outline'
              size='sm'
              onClick={() => pagination.onPageChange(pagination.page - 1)}
              disabled={pagination.page <= 1}
            >
              Previous
            </Button>

            <span className='text-sm text-gray-600'>
              Page {pagination.page} of {Math.ceil(pagination.total / pagination.pageSize)}
            </span>

            <Button
              variant='outline'
              size='sm'
              onClick={() => pagination.onPageChange(pagination.page + 1)}
              disabled={pagination.page >= Math.ceil(pagination.total / pagination.pageSize)}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </Card>
  );
};

// Portal-specific preset configurations for common entity tables
// DRY Table Configuration Factory
export const createTableColumn = (
  key: string,
  title: string,
  options?: {
    sortable?: boolean;
    filterable?: boolean;
    render?: (value: any, item: any) => React.ReactNode;
  }
): TableColumn => ({
  key,
  title,
  ...(options?.sortable && { sortable: options.sortable }),
  ...(options?.filterable && { filterable: options.filterable }),
  ...(options?.render && { render: options.render }),
});

export const createStatusColumn = (key: string, title = 'Status') =>
  createTableColumn(key, title, {
    filterable: true,
    render: (value) => (
      <span
        className={`inline-flex px-2 py-1 text-xs rounded-full ${
          value === 'active'
            ? 'bg-green-100 text-green-800'
            : value === 'suspended'
              ? 'bg-red-100 text-red-800'
              : 'bg-yellow-100 text-yellow-800'
        }`}
      >
        {value}
      </span>
    ),
  });

export const createEntityAction = (
  key: string,
  label: string,
  icon: React.ComponentType<any>,
  onClick: (item: any) => void,
  variant?: 'primary' | 'secondary' | 'danger'
): EntityAction => ({
  key,
  label,
  icon,
  onClick,
  ...(variant && { variant }),
});

// Common table configurations (DRY approach)
export const TABLE_CONFIGS = {
  tenants: {
    columns: [
      createTableColumn('name', 'Tenant Name', { sortable: true }),
      createTableColumn('domain', 'Domain', { sortable: true }),
      createTableColumn('plan', 'Plan', { filterable: true }),
      createStatusColumn('status'),
      createTableColumn('createdAt', 'Created', { sortable: true }),
    ],
    actions: [
      createEntityAction('view', 'View', Eye, (tenant) => console.log('View', tenant)),
      createEntityAction('edit', 'Edit', Edit, (tenant) => console.log('Edit', tenant)),
      createEntityAction(
        'delete',
        'Delete',
        Trash2,
        (tenant) => console.log('Delete', tenant),
        'danger'
      ),
    ],
  },
  customers: {
    columns: [
      createTableColumn('name', 'Customer Name', { sortable: true }),
      createTableColumn('email', 'Email', { sortable: true }),
      createTableColumn('plan', 'Service Plan', { filterable: true }),
      createStatusColumn('status'),
      createTableColumn('lastPayment', 'Last Payment', { sortable: true }),
      createTableColumn('dataUsage', 'Data Usage'),
    ],
    actions: [
      createEntityAction('view', 'View', Eye, (customer) => console.log('View', customer)),
      createEntityAction('edit', 'Edit', Edit, (customer) => console.log('Edit', customer)),
    ],
  },
} as const;

// Portal-specific preset aliases (leverages existing patterns)
export const EntityTablePresets = {
  management: {
    tenantsTable: () => TABLE_CONFIGS.tenants,
    usersTable: () => TABLE_CONFIGS.customers,
  },
  admin: {
    customersTable: () => TABLE_CONFIGS.customers,
    tenantsTable: () => TABLE_CONFIGS.tenants,
  },
  customer: TABLE_CONFIGS,
  reseller: TABLE_CONFIGS,
  technician: TABLE_CONFIGS,
} as const;
