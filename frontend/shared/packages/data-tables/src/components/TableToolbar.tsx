/**
 * TableToolbar Component
 * Universal toolbar with search, filters, actions, and export controls
 */

import React, { useState } from 'react';
import { Download, Filter, Settings, RefreshCw, Eye, EyeOff } from 'lucide-react';
import {
  Button,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  Badge,
} from '@dotmac/primitives';
import { cva } from 'class-variance-authority';
import { clsx } from 'clsx';
import { TableSearch } from './TableSearch';
import { TableFilters } from './TableFilters';
import type {
  SearchConfig,
  FilterDefinition,
  FilteringState,
  ExportConfig,
  TableAction,
  PortalVariant,
} from '../types';
import { exportData, getRecommendedExportFormat } from '../utils/export';

const toolbarVariants = cva('flex flex-col gap-4 p-4 bg-white border-b', {
  variants: {
    portal: {
      admin: 'border-blue-200',
      customer: 'border-green-200',
      reseller: 'border-purple-200',
      technician: 'border-orange-200',
      management: 'border-red-200',
    },
    variant: {
      default: '',
      compact: 'p-2 gap-2',
      spacious: 'p-6 gap-6',
    },
  },
  defaultVariants: {
    portal: 'admin',
    variant: 'default',
  },
});

const actionButtonVariants = cva(
  'inline-flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2',
  {
    variants: {
      variant: {
        primary: '',
        secondary: 'bg-gray-100 text-gray-700 hover:bg-gray-200',
        outline: 'border border-gray-300 bg-white text-gray-700 hover:bg-gray-50',
      },
      portal: {
        admin: {
          primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
        },
        customer: {
          primary: 'bg-green-600 text-white hover:bg-green-700 focus:ring-green-500',
        },
        reseller: {
          primary: 'bg-purple-600 text-white hover:bg-purple-700 focus:ring-purple-500',
        },
        technician: {
          primary: 'bg-orange-600 text-white hover:bg-orange-700 focus:ring-orange-500',
        },
        management: {
          primary: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
        },
      },
    },
    defaultVariants: {
      variant: 'primary',
      portal: 'admin',
    },
  }
);

interface TableToolbarProps<TData = any> {
  // Search
  searchConfig?: SearchConfig;
  searchValue: string;
  onSearchChange: (value: string) => void;

  // Filters
  filters?: FilterDefinition[];
  filterValues: FilteringState[];
  onFilterChange: (filters: FilteringState[]) => void;

  // Export
  exportConfig?: ExportConfig;
  data: TData[];
  selectedData?: TData[];

  // Actions
  toolbarActions?: TableAction<TData>[];

  // Column visibility
  columnVisibility?: Record<string, boolean>;
  onColumnVisibilityChange?: (visibility: Record<string, boolean>) => void;

  // Refresh
  onRefresh?: () => Promise<void>;
  isRefreshing?: boolean;

  // Portal theming
  portal?: PortalVariant;
  variant?: 'default' | 'compact' | 'spacious';
  className?: string;

  // Layout
  showSearch?: boolean;
  showFilters?: boolean;
  showExport?: boolean;
  showColumnToggle?: boolean;
  showRefresh?: boolean;

  // State
  title?: string;
  subtitle?: string;
}

export const TableToolbar = <TData extends any>({
  // Search
  searchConfig,
  searchValue,
  onSearchChange,

  // Filters
  filters = [],
  filterValues,
  onFilterChange,

  // Export
  exportConfig,
  data,
  selectedData,

  // Actions
  toolbarActions = [],

  // Column visibility
  columnVisibility = {},
  onColumnVisibilityChange,

  // Refresh
  onRefresh,
  isRefreshing = false,

  // Portal theming
  portal = 'admin',
  variant = 'default',
  className,

  // Layout
  showSearch = true,
  showFilters = true,
  showExport = true,
  showColumnToggle = true,
  showRefresh = true,

  // State
  title,
  subtitle,
}: TableToolbarProps<TData>) => {
  const [showFiltersPanel, setShowFiltersPanel] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  // Active filters count
  const activeFiltersCount = filterValues.filter((filter) => {
    const value = filter.value;
    if (Array.isArray(value)) return value.length > 0;
    return value !== undefined && value !== null && value !== '';
  }).length;

  // Visible columns count
  const visibleColumnsCount = Object.values(columnVisibility).filter(Boolean).length;
  const totalColumnsCount = Object.keys(columnVisibility).length;

  // Export handler
  const handleExport = async (format: 'csv' | 'xlsx' | 'json' | 'pdf') => {
    if (!exportConfig) return;

    setIsExporting(true);
    try {
      const dataToExport = exportConfig.selectedOnly && selectedData?.length ? selectedData : data;

      await exportData(format, dataToExport, exportConfig, {
        portal,
        title: title || 'Data Export',
      });
    } catch (error) {
      console.error('Export failed:', error);
      // TODO: Add toast notification
    } finally {
      setIsExporting(false);
    }
  };

  // Column visibility toggle
  const toggleColumnVisibility = (columnId: string) => {
    if (!onColumnVisibilityChange) return;

    onColumnVisibilityChange({
      ...columnVisibility,
      [columnId]: !columnVisibility[columnId],
    });
  };

  // Toggle all columns
  const toggleAllColumns = (visible: boolean) => {
    if (!onColumnVisibilityChange) return;

    const newVisibility = { ...columnVisibility };
    Object.keys(newVisibility).forEach((key) => {
      newVisibility[key] = visible;
    });
    onColumnVisibilityChange(newVisibility);
  };

  return (
    <>
      <div className={clsx(toolbarVariants({ portal, variant }), className)}>
        {/* Header section */}
        <div className='flex items-center justify-between'>
          {/* Title and subtitle */}
          <div>
            {title && <h2 className='text-lg font-semibold text-gray-900'>{title}</h2>}
            {subtitle && <p className='text-sm text-gray-600 mt-1'>{subtitle}</p>}
          </div>

          {/* Primary actions */}
          <div className='flex items-center gap-2'>
            {/* Custom toolbar actions */}
            {toolbarActions.map((action) => {
              const Icon = action.icon;
              return (
                <Button
                  key={action.id}
                  variant={action.variant === 'primary' ? 'default' : action.variant || 'outline'}
                  size={action.size || 'sm'}
                  onClick={() => action.onClick(selectedData || [])}
                  disabled={action.disabled || action.loading}
                  className={actionButtonVariants({
                    variant: action.variant === 'primary' ? 'primary' : 'outline',
                    portal,
                  })}
                  title={action.tooltip}
                >
                  {Icon && <Icon className='w-4 h-4' />}
                  {action.loading ? action.loadingText || 'Loading...' : action.label}
                </Button>
              );
            })}

            {/* Refresh */}
            {showRefresh && onRefresh && (
              <Button
                variant='outline'
                size='sm'
                onClick={onRefresh}
                disabled={isRefreshing}
                title='Refresh data'
              >
                <RefreshCw className={clsx('w-4 h-4', isRefreshing && 'animate-spin')} />
              </Button>
            )}

            {/* Export dropdown */}
            {showExport && exportConfig && exportConfig.formats.length > 0 && (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant='outline' size='sm' disabled={isExporting}>
                    <Download className='w-4 h-4' />
                    Export
                    {isExporting && (
                      <div className='ml-2 w-3 h-3 border border-gray-400 border-t-transparent rounded-full animate-spin' />
                    )}
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align='end'>
                  {exportConfig.formats.map((format) => {
                    const isRecommended =
                      format === getRecommendedExportFormat(data, exportConfig.formats);
                    return (
                      <DropdownMenuItem
                        key={format}
                        onClick={() => handleExport(format)}
                        className='flex items-center justify-between'
                      >
                        <span className='capitalize'>{format}</span>
                        {isRecommended && (
                          <Badge variant='secondary' className='ml-2 text-xs'>
                            Recommended
                          </Badge>
                        )}
                      </DropdownMenuItem>
                    );
                  })}
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    onClick={() => {
                      const format = getRecommendedExportFormat(data, exportConfig.formats);
                      handleExport(format);
                    }}
                    className='font-medium'
                  >
                    Quick Export
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            )}

            {/* Column visibility toggle */}
            {showColumnToggle && onColumnVisibilityChange && totalColumnsCount > 0 && (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant='outline' size='sm'>
                    <Settings className='w-4 h-4' />
                    Columns
                    <Badge variant='secondary' className='ml-1'>
                      {visibleColumnsCount}/{totalColumnsCount}
                    </Badge>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align='end' className='w-56'>
                  <div className='p-2 border-b'>
                    <div className='flex gap-1'>
                      <Button
                        variant='ghost'
                        size='sm'
                        onClick={() => toggleAllColumns(true)}
                        className='flex-1 h-7 text-xs'
                      >
                        <Eye className='w-3 h-3 mr-1' />
                        Show All
                      </Button>
                      <Button
                        variant='ghost'
                        size='sm'
                        onClick={() => toggleAllColumns(false)}
                        className='flex-1 h-7 text-xs'
                      >
                        <EyeOff className='w-3 h-3 mr-1' />
                        Hide All
                      </Button>
                    </div>
                  </div>
                  {Object.entries(columnVisibility).map(([columnId, visible]) => (
                    <DropdownMenuItem
                      key={columnId}
                      onClick={() => toggleColumnVisibility(columnId)}
                      className='flex items-center gap-2'
                    >
                      {visible ? (
                        <Eye className='w-4 h-4 text-green-500' />
                      ) : (
                        <EyeOff className='w-4 h-4 text-gray-400' />
                      )}
                      <span className={clsx('capitalize', !visible && 'text-gray-500')}>
                        {columnId.replace(/([A-Z])/g, ' $1').trim()}
                      </span>
                    </DropdownMenuItem>
                  ))}
                </DropdownMenuContent>
              </DropdownMenu>
            )}
          </div>
        </div>

        {/* Controls section */}
        <div className='flex flex-col sm:flex-row gap-3 items-start sm:items-center justify-between'>
          {/* Search */}
          {showSearch && searchConfig && (
            <div className='flex-1 max-w-md'>
              <TableSearch
                searchConfig={searchConfig}
                value={searchValue}
                onChange={onSearchChange}
                data={data}
                portal={portal}
              />
            </div>
          )}

          {/* Filter controls */}
          {showFilters && filters.length > 0 && (
            <div className='flex items-center gap-2'>
              <Button
                variant='outline'
                size='sm'
                onClick={() => setShowFiltersPanel(!showFiltersPanel)}
                className='flex items-center gap-2'
              >
                <Filter className='w-4 h-4' />
                Filters
                {activeFiltersCount > 0 && (
                  <Badge variant='secondary' className='ml-1'>
                    {activeFiltersCount}
                  </Badge>
                )}
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Filters panel */}
      {showFiltersPanel && filters.length > 0 && (
        <TableFilters
          filters={filters}
          values={filterValues}
          onChange={onFilterChange}
          portal={portal}
        />
      )}
    </>
  );
};

export default TableToolbar;
