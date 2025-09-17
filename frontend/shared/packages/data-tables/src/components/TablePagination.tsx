/**
 * TablePagination Component
 * Universal pagination with portal theming and comprehensive controls
 */

import React from 'react';
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react';
import { Button, Select } from '@dotmac/primitives';
import { cva } from 'class-variance-authority';
import { clsx } from 'clsx';
import type { PaginationState, PortalVariant } from '../types';

const paginationVariants = cva(
  'flex items-center justify-between gap-4 px-4 py-3 border-t bg-white',
  {
    variants: {
      portal: {
        admin: 'border-blue-200',
        customer: 'border-green-200',
        reseller: 'border-purple-200',
        technician: 'border-orange-200',
        management: 'border-red-200',
      },
      size: {
        sm: 'px-2 py-2 text-sm',
        md: 'px-4 py-3 text-base',
        lg: 'px-6 py-4 text-lg',
      },
    },
    defaultVariants: {
      portal: 'admin',
      size: 'md',
    },
  }
);

const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-md font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      portal: {
        admin: 'hover:bg-blue-50 focus:ring-blue-500 text-blue-600',
        customer: 'hover:bg-green-50 focus:ring-green-500 text-green-600',
        reseller: 'hover:bg-purple-50 focus:ring-purple-500 text-purple-600',
        technician: 'hover:bg-orange-50 focus:ring-orange-500 text-orange-600',
        management: 'hover:bg-red-50 focus:ring-red-500 text-red-600',
      },
      size: {
        sm: 'h-7 px-2 text-xs',
        md: 'h-9 px-3 text-sm',
        lg: 'h-11 px-4 text-base',
      },
    },
    defaultVariants: {
      portal: 'admin',
      size: 'md',
    },
  }
);

interface TablePaginationProps {
  pagination: PaginationState;
  onPaginationChange: (
    updater: PaginationState | ((old: PaginationState) => PaginationState)
  ) => void;
  totalRows: number;
  pageSizeOptions?: number[];
  showPageSizeSelector?: boolean;
  showRowsInfo?: boolean;
  showPageNumbers?: boolean;
  maxPageNumbers?: number;
  portal?: PortalVariant;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  compactMode?: boolean;
  pageCount?: number; // For manual pagination
}

export const TablePagination: React.FC<TablePaginationProps> = ({
  pagination,
  onPaginationChange,
  totalRows,
  pageSizeOptions = [10, 25, 50, 100],
  showPageSizeSelector = true,
  showRowsInfo = true,
  showPageNumbers = true,
  maxPageNumbers = 7,
  portal = 'admin',
  size = 'md',
  className,
  compactMode = false,
  pageCount,
}) => {
  const { pageIndex, pageSize } = pagination;

  // Calculate pagination values
  const totalPages = pageCount || Math.ceil(totalRows / pageSize);
  const currentPage = pageIndex + 1;
  const startRow = pageIndex * pageSize + 1;
  const endRow = Math.min(startRow + pageSize - 1, totalRows);

  // Generate page numbers to show
  const getPageNumbers = () => {
    if (totalPages <= maxPageNumbers) {
      return Array.from({ length: totalPages }, (_, i) => i + 1);
    }

    const half = Math.floor(maxPageNumbers / 2);
    let start = Math.max(1, currentPage - half);
    let end = Math.min(totalPages, start + maxPageNumbers - 1);

    if (end - start + 1 < maxPageNumbers) {
      start = Math.max(1, end - maxPageNumbers + 1);
    }

    const pages: (number | string)[] = [];

    if (start > 1) {
      pages.push(1);
      if (start > 2) {
        pages.push('...');
      }
    }

    for (let i = start; i <= end; i++) {
      pages.push(i);
    }

    if (end < totalPages) {
      if (end < totalPages - 1) {
        pages.push('...');
      }
      pages.push(totalPages);
    }

    return pages;
  };

  // Navigation handlers
  const goToFirstPage = () => {
    onPaginationChange({ ...pagination, pageIndex: 0 });
  };

  const goToPreviousPage = () => {
    onPaginationChange({ ...pagination, pageIndex: Math.max(0, pageIndex - 1) });
  };

  const goToNextPage = () => {
    onPaginationChange({ ...pagination, pageIndex: Math.min(totalPages - 1, pageIndex + 1) });
  };

  const goToLastPage = () => {
    onPaginationChange({ ...pagination, pageIndex: totalPages - 1 });
  };

  const goToPage = (page: number) => {
    onPaginationChange({ ...pagination, pageIndex: page - 1 });
  };

  const changePageSize = (newPageSize: number) => {
    onPaginationChange({
      pageIndex: 0, // Reset to first page when changing page size
      pageSize: newPageSize,
    });
  };

  if (totalRows === 0) {
    return null;
  }

  return (
    <div className={clsx(paginationVariants({ portal, size }), className)}>
      {/* Left side - Rows info and page size selector */}
      <div className='flex items-center gap-4'>
        {showRowsInfo && !compactMode && (
          <div className='text-sm text-gray-600'>
            Showing {startRow.toLocaleString()} to {endRow.toLocaleString()} of{' '}
            {totalRows.toLocaleString()} entries
          </div>
        )}

        {showPageSizeSelector && (
          <div className='flex items-center gap-2'>
            <span className='text-sm text-gray-600'>Show</span>
            <Select
              value={pageSize.toString()}
              onValueChange={(value) => changePageSize(Number(value))}
              className='w-20'
            >
              {pageSizeOptions.map((size) => (
                <option key={size} value={size.toString()}>
                  {size}
                </option>
              ))}
            </Select>
            {!compactMode && <span className='text-sm text-gray-600'>entries</span>}
          </div>
        )}
      </div>

      {/* Right side - Navigation controls */}
      <div className='flex items-center gap-2'>
        {showRowsInfo && compactMode && (
          <div className='text-sm text-gray-600 mr-4'>
            {currentPage} of {totalPages}
          </div>
        )}

        {/* First page button */}
        <Button
          variant='ghost'
          size={size}
          onClick={goToFirstPage}
          disabled={currentPage === 1}
          className={buttonVariants({ portal, size })}
          title='First page'
        >
          <ChevronsLeft className='w-4 h-4' />
        </Button>

        {/* Previous page button */}
        <Button
          variant='ghost'
          size={size}
          onClick={goToPreviousPage}
          disabled={currentPage === 1}
          className={buttonVariants({ portal, size })}
          title='Previous page'
        >
          <ChevronLeft className='w-4 h-4' />
        </Button>

        {/* Page numbers */}
        {showPageNumbers && !compactMode && (
          <div className='flex items-center gap-1'>
            {getPageNumbers().map((page, index) => {
              if (page === '...') {
                return (
                  <span key={`ellipsis-${index}`} className='px-2 text-gray-400'>
                    ...
                  </span>
                );
              }

              const pageNumber = page as number;
              const isCurrentPage = pageNumber === currentPage;

              return (
                <Button
                  key={pageNumber}
                  variant={isCurrentPage ? 'default' : 'ghost'}
                  size={size}
                  onClick={() => goToPage(pageNumber)}
                  className={clsx(
                    buttonVariants({ portal, size }),
                    isCurrentPage && {
                      'bg-blue-600 text-white hover:bg-blue-700': portal === 'admin',
                      'bg-green-600 text-white hover:bg-green-700': portal === 'customer',
                      'bg-purple-600 text-white hover:bg-purple-700': portal === 'reseller',
                      'bg-orange-600 text-white hover:bg-orange-700': portal === 'technician',
                      'bg-red-600 text-white hover:bg-red-700': portal === 'management',
                    }
                  )}
                  title={`Go to page ${pageNumber}`}
                >
                  {pageNumber}
                </Button>
              );
            })}
          </div>
        )}

        {/* Next page button */}
        <Button
          variant='ghost'
          size={size}
          onClick={goToNextPage}
          disabled={currentPage === totalPages}
          className={buttonVariants({ portal, size })}
          title='Next page'
        >
          <ChevronRight className='w-4 h-4' />
        </Button>

        {/* Last page button */}
        <Button
          variant='ghost'
          size={size}
          onClick={goToLastPage}
          disabled={currentPage === totalPages}
          className={buttonVariants({ portal, size })}
          title='Last page'
        >
          <ChevronsRight className='w-4 h-4' />
        </Button>
      </div>
    </div>
  );
};

export default TablePagination;
