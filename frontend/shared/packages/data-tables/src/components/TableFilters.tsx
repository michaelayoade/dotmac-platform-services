/**
 * TableFilters Component
 * Universal column filters with multiple filter types and portal theming
 */

import React, { useMemo } from 'react';
import { Filter, X, ChevronDown } from 'lucide-react';
import { Button, Select, Input, Checkbox, Badge } from '@dotmac/primitives';
import { cva } from 'class-variance-authority';
import { clsx } from 'clsx';
import type { FilterDefinition, FilteringState, PortalVariant } from '../types';

const filtersVariants = cva('flex flex-wrap items-center gap-3 p-4 bg-gray-50 rounded-lg border', {
  variants: {
    portal: {
      admin: 'border-blue-200 bg-blue-50/50',
      customer: 'border-green-200 bg-green-50/50',
      reseller: 'border-purple-200 bg-purple-50/50',
      technician: 'border-orange-200 bg-orange-50/50',
      management: 'border-red-200 bg-red-50/50',
    },
    variant: {
      default: '',
      compact: 'p-2 gap-2',
      spacious: 'p-6 gap-4',
    },
  },
  defaultVariants: {
    portal: 'admin',
    variant: 'default',
  },
});

const filterBadgeVariants = cva(
  'inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium',
  {
    variants: {
      portal: {
        admin: 'bg-blue-100 text-blue-800 border-blue-200',
        customer: 'bg-green-100 text-green-800 border-green-200',
        reseller: 'bg-purple-100 text-purple-800 border-purple-200',
        technician: 'bg-orange-100 text-orange-800 border-orange-200',
        management: 'bg-red-100 text-red-800 border-red-200',
      },
    },
    defaultVariants: {
      portal: 'admin',
    },
  }
);

interface TableFiltersProps {
  filters: FilterDefinition[];
  values: FilteringState[];
  onChange: (filters: FilteringState[]) => void;
  portal?: PortalVariant;
  variant?: 'default' | 'compact' | 'spacious';
  className?: string;
  showActiveCount?: boolean;
  collapsible?: boolean;
  defaultCollapsed?: boolean;
}

export const TableFilters: React.FC<TableFiltersProps> = ({
  filters,
  values,
  onChange,
  portal = 'admin',
  variant = 'default',
  className,
  showActiveCount = true,
  collapsible = false,
  defaultCollapsed = false,
}) => {
  const [isCollapsed, setIsCollapsed] = React.useState(defaultCollapsed);

  // Active filters count
  const activeFiltersCount = useMemo(() => {
    return values.filter((filter) => {
      const value = filter.value;
      if (Array.isArray(value)) {
        return value.length > 0;
      }
      return value !== undefined && value !== null && value !== '';
    }).length;
  }, [values]);

  // Get current filter value
  const getFilterValue = (filterId: string) => {
    const filter = values.find((f) => f.id === filterId);
    return filter?.value;
  };

  // Update specific filter
  const updateFilter = (filterId: string, value: any) => {
    const newFilters = values.filter((f) => f.id !== filterId);
    if (
      value !== undefined &&
      value !== null &&
      value !== '' &&
      (!Array.isArray(value) || value.length > 0)
    ) {
      newFilters.push({ id: filterId, value });
    }
    onChange(newFilters);
  };

  // Clear all filters
  const clearAllFilters = () => {
    onChange([]);
  };

  // Clear specific filter
  const clearFilter = (filterId: string) => {
    onChange(values.filter((f) => f.id !== filterId));
  };

  // Render individual filter based on type
  const renderFilter = (filter: FilterDefinition) => {
    const currentValue = getFilterValue(filter.id);

    switch (filter.type) {
      case 'text':
        return (
          <Input
            key={filter.id}
            placeholder={filter.placeholder || `Filter by ${filter.label}`}
            value={currentValue || ''}
            onChange={(e) => updateFilter(filter.id, e.target.value)}
            className='w-48'
          />
        );

      case 'select':
        return (
          <Select
            key={filter.id}
            value={currentValue || ''}
            onValueChange={(value) => updateFilter(filter.id, value)}
            placeholder={filter.placeholder || `Select ${filter.label}`}
          >
            {filter.options?.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
                {option.count !== undefined && ` (${option.count})`}
              </option>
            ))}
          </Select>
        );

      case 'multiselect':
        return (
          <div key={filter.id} className='relative'>
            <Select
              value=''
              onValueChange={(value) => {
                const current = Array.isArray(currentValue) ? currentValue : [];
                if (!current.includes(value)) {
                  updateFilter(filter.id, [...current, value]);
                }
              }}
              placeholder={`Add ${filter.label} filter`}
            >
              {filter.options
                ?.filter(
                  (option) => !Array.isArray(currentValue) || !currentValue.includes(option.value)
                )
                .map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                    {option.count !== undefined && ` (${option.count})`}
                  </option>
                ))}
            </Select>
            {Array.isArray(currentValue) && currentValue.length > 0 && (
              <div className='flex flex-wrap gap-1 mt-1'>
                {currentValue.map((value) => {
                  const option = filter.options?.find((opt) => opt.value === value);
                  return (
                    <Badge
                      key={value}
                      variant='secondary'
                      className={filterBadgeVariants({ portal })}
                    >
                      {option?.label || value}
                      <Button
                        variant='ghost'
                        size='sm'
                        onClick={() => {
                          const newValue = currentValue.filter((v) => v !== value);
                          updateFilter(filter.id, newValue.length > 0 ? newValue : undefined);
                        }}
                        className='ml-1 h-3 w-3 p-0 hover:bg-transparent'
                      >
                        <X className='w-2 h-2' />
                      </Button>
                    </Badge>
                  );
                })}
              </div>
            )}
          </div>
        );

      case 'number':
        return (
          <Input
            key={filter.id}
            type='number'
            placeholder={filter.placeholder || `Filter by ${filter.label}`}
            value={currentValue || ''}
            onChange={(e) =>
              updateFilter(filter.id, e.target.value ? Number(e.target.value) : undefined)
            }
            className='w-32'
          />
        );

      case 'date':
        return (
          <Input
            key={filter.id}
            type='date'
            value={currentValue || ''}
            onChange={(e) => updateFilter(filter.id, e.target.value)}
            className='w-40'
          />
        );

      case 'daterange':
        const dateRange = Array.isArray(currentValue) ? currentValue : [null, null];
        return (
          <div key={filter.id} className='flex items-center gap-2'>
            <Input
              type='date'
              placeholder='Start date'
              value={dateRange[0] || ''}
              onChange={(e) => updateFilter(filter.id, [e.target.value, dateRange[1]])}
              className='w-36'
            />
            <span className='text-gray-400'>to</span>
            <Input
              type='date'
              placeholder='End date'
              value={dateRange[1] || ''}
              onChange={(e) => updateFilter(filter.id, [dateRange[0], e.target.value])}
              className='w-36'
            />
          </div>
        );

      case 'boolean':
        return (
          <label key={filter.id} className='flex items-center gap-2 cursor-pointer'>
            <Checkbox
              checked={currentValue || false}
              onChange={(e) => updateFilter(filter.id, e.target.checked)}
            />
            <span className='text-sm'>{filter.label}</span>
          </label>
        );

      default:
        return null;
    }
  };

  if (filters.length === 0) {
    return null;
  }

  return (
    <div className={clsx(filtersVariants({ portal, variant }), className)}>
      <div className='flex items-center gap-2'>
        <Filter className='w-4 h-4 text-gray-500' />
        <span className='text-sm font-medium text-gray-700'>Filters</span>
        {showActiveCount && activeFiltersCount > 0 && (
          <Badge variant='secondary' className={filterBadgeVariants({ portal })}>
            {activeFiltersCount}
          </Badge>
        )}
        {collapsible && (
          <Button
            variant='ghost'
            size='sm'
            onClick={() => setIsCollapsed(!isCollapsed)}
            className='ml-auto'
          >
            <ChevronDown
              className={clsx(
                'w-4 h-4 transition-transform',
                isCollapsed && 'transform rotate-180'
              )}
            />
          </Button>
        )}
      </div>

      {(!collapsible || !isCollapsed) && (
        <>
          <div className='flex flex-wrap items-center gap-3'>{filters.map(renderFilter)}</div>

          {activeFiltersCount > 0 && (
            <Button
              variant='outline'
              size='sm'
              onClick={clearAllFilters}
              className='text-gray-600 hover:text-gray-800'
            >
              Clear all filters
            </Button>
          )}
        </>
      )}
    </div>
  );
};

export default TableFilters;
