import React, { useState, useMemo } from 'react';
import { cn } from '@dotmac/primitives/utils/cn';

interface Column {
  key: string;
  title: string;
  width?: number;
  sortable?: boolean;
  render?: (value: any, row: any, index: number) => React.ReactNode;
  align?: 'left' | 'center' | 'right';
}

interface DataTableProps {
  data: any[];
  columns: Column[];
  loading?: boolean;
  error?: string | null;
  pagination?: {
    page: number;
    size: number;
    total: number;
    onPageChange: (page: number) => void;
    onSizeChange: (size: number) => void;
  };
  sorting?: {
    key: string;
    direction: 'asc' | 'desc';
    onSort: (key: string, direction: 'asc' | 'desc') => void;
  };
  selection?: {
    selectedRows: string[];
    onSelectionChange: (selectedRows: string[]) => void;
    getRowId: (row: any) => string;
  };
  className?: string;
  emptyMessage?: string;
  maxHeight?: string;
}

export const DataTable: React.FC<DataTableProps> = ({
  data,
  columns,
  loading = false,
  error = null,
  pagination,
  sorting,
  selection,
  className,
  emptyMessage = 'No data available',
  maxHeight = '600px',
}) => {
  const [localSort, setLocalSort] = useState<{ key: string; direction: 'asc' | 'desc' } | null>(
    null
  );

  // Use provided sorting or local sorting
  const currentSort = sorting || localSort;

  // Sort data locally if no external sorting is provided
  const sortedData = useMemo(() => {
    if (!currentSort || sorting) return data; // Don't sort locally if external sorting is used

    const { key, direction } = currentSort;
    return [...data].sort((a, b) => {
      const aVal = a[key];
      const bVal = b[key];

      if (aVal === bVal) return 0;

      const result = aVal > bVal ? 1 : -1;
      return direction === 'asc' ? result : -result;
    });
  }, [data, currentSort, sorting]);

  const handleSort = (key: string) => {
    const newDirection =
      currentSort?.key === key && currentSort?.direction === 'asc' ? 'desc' : 'asc';

    if (sorting) {
      sorting.onSort(key, newDirection);
    } else {
      setLocalSort({ key, direction: newDirection });
    }
  };

  const handleSelectAll = (checked: boolean) => {
    if (!selection) return;

    if (checked) {
      const allIds = sortedData.map(selection.getRowId);
      selection.onSelectionChange(allIds);
    } else {
      selection.onSelectionChange([]);
    }
  };

  const handleSelectRow = (rowId: string, checked: boolean) => {
    if (!selection) return;

    const newSelection = checked
      ? [...selection.selectedRows, rowId]
      : selection.selectedRows.filter((id) => id !== rowId);

    selection.onSelectionChange(newSelection);
  };

  const isAllSelected =
    selection && selection.selectedRows.length === sortedData.length && sortedData.length > 0;
  const isPartiallySelected =
    selection &&
    selection.selectedRows.length > 0 &&
    selection.selectedRows.length < sortedData.length;

  if (error) {
    return (
      <div className='text-center p-8'>
        <div className='text-red-600 mb-2'>
          <svg className='w-12 h-12 mx-auto mb-4' fill='currentColor' viewBox='0 0 20 20'>
            <path
              fillRule='evenodd'
              d='M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z'
              clipRule='evenodd'
            />
          </svg>
        </div>
        <p className='text-gray-600'>{error}</p>
      </div>
    );
  }

  return (
    <div className={cn('bg-white rounded-lg border overflow-hidden', className)}>
      <div className='overflow-auto' style={{ maxHeight }}>
        <table className='min-w-full divide-y divide-gray-200'>
          <thead className='bg-gray-50 sticky top-0 z-10'>
            <tr>
              {/* Selection Column */}
              {selection && (
                <th className='px-6 py-3 text-left'>
                  <input
                    type='checkbox'
                    checked={isAllSelected}
                    ref={(el) => {
                      if (el) el.indeterminate = isPartiallySelected;
                    }}
                    onChange={(e) => handleSelectAll(e.target.checked)}
                    className='h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
                  />
                </th>
              )}

              {/* Data Columns */}
              {columns.map((column) => (
                <th
                  key={column.key}
                  className={cn(
                    'px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider',
                    column.align === 'center' && 'text-center',
                    column.align === 'right' && 'text-right',
                    column.sortable && 'cursor-pointer hover:bg-gray-100'
                  )}
                  style={{ width: column.width }}
                  onClick={column.sortable ? () => handleSort(column.key) : undefined}
                >
                  <div className='flex items-center space-x-1'>
                    <span>{column.title}</span>
                    {column.sortable && (
                      <div className='flex flex-col'>
                        <svg
                          className={cn(
                            'w-3 h-3',
                            currentSort?.key === column.key && currentSort.direction === 'asc'
                              ? 'text-blue-600'
                              : 'text-gray-400'
                          )}
                          fill='currentColor'
                          viewBox='0 0 20 20'
                        >
                          <path
                            fillRule='evenodd'
                            d='M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z'
                            clipRule='evenodd'
                          />
                        </svg>
                      </div>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>

          <tbody className='bg-white divide-y divide-gray-200'>
            {loading ? (
              Array.from({ length: 5 }).map((_, index) => (
                <tr key={index} className='animate-pulse'>
                  {selection && (
                    <td className='px-6 py-4'>
                      <div className='w-4 h-4 bg-gray-200 rounded'></div>
                    </td>
                  )}
                  {columns.map((column) => (
                    <td key={column.key} className='px-6 py-4'>
                      <div className='h-4 bg-gray-200 rounded w-3/4'></div>
                    </td>
                  ))}
                </tr>
              ))
            ) : sortedData.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length + (selection ? 1 : 0)}
                  className='px-6 py-12 text-center text-gray-500'
                >
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              sortedData.map((row, index) => {
                const rowId = selection?.getRowId(row) || String(index);
                const isSelected = selection?.selectedRows.includes(rowId) || false;

                return (
                  <tr
                    key={rowId}
                    className={cn('hover:bg-gray-50 transition-colors', isSelected && 'bg-blue-50')}
                  >
                    {/* Selection Column */}
                    {selection && (
                      <td className='px-6 py-4'>
                        <input
                          type='checkbox'
                          checked={isSelected}
                          onChange={(e) => handleSelectRow(rowId, e.target.checked)}
                          className='h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
                        />
                      </td>
                    )}

                    {/* Data Columns */}
                    {columns.map((column) => (
                      <td
                        key={column.key}
                        className={cn(
                          'px-6 py-4 whitespace-nowrap text-sm',
                          column.align === 'center' && 'text-center',
                          column.align === 'right' && 'text-right'
                        )}
                      >
                        {column.render
                          ? column.render(row[column.key], row, index)
                          : row[column.key]}
                      </td>
                    ))}
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {pagination && (
        <div className='px-6 py-3 bg-gray-50 border-t border-gray-200 flex items-center justify-between'>
          <div className='flex items-center space-x-2'>
            <span className='text-sm text-gray-700'>
              Showing {(pagination.page - 1) * pagination.size + 1} to{' '}
              {Math.min(pagination.page * pagination.size, pagination.total)} of {pagination.total}{' '}
              results
            </span>
          </div>

          <div className='flex items-center space-x-2'>
            {/* Page Size Selector */}
            <select
              value={pagination.size}
              onChange={(e) => pagination.onSizeChange(Number(e.target.value))}
              className='text-sm border border-gray-300 rounded px-2 py-1'
            >
              {[10, 25, 50, 100].map((size) => (
                <option key={size} value={size}>
                  {size} per page
                </option>
              ))}
            </select>

            {/* Pagination Buttons */}
            <div className='flex space-x-1'>
              <button
                onClick={() => pagination.onPageChange(pagination.page - 1)}
                disabled={pagination.page === 1}
                className='px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed'
              >
                Previous
              </button>

              <span className='px-3 py-1 text-sm'>
                Page {pagination.page} of {Math.ceil(pagination.total / pagination.size)}
              </span>

              <button
                onClick={() => pagination.onPageChange(pagination.page + 1)}
                disabled={pagination.page >= Math.ceil(pagination.total / pagination.size)}
                className='px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed'
              >
                Next
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
