import React from 'react';
import { cn } from '@dotmac/primitives/utils/cn';
import type { FilterConfig } from '../../types';

interface FilterBarProps {
  filters: FilterConfig[];
  values: Record<string, any>;
  onChange: (filterId: string, value: any) => void;
  className?: string;
  orientation?: 'horizontal' | 'vertical';
}

export const FilterBar: React.FC<FilterBarProps> = ({
  filters,
  values,
  onChange,
  className,
  orientation = 'horizontal',
}) => {
  if (filters.length === 0) return null;

  const renderFilter = (filter: FilterConfig) => {
    const value = values[filter.id] || filter.defaultValue;

    switch (filter.type) {
      case 'select':
        return (
          <select
            id={filter.id}
            value={value || ''}
            onChange={(e) => onChange(filter.id, e.target.value)}
            className='mt-1 block w-full pl-3 pr-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md'
            required={filter.required}
          >
            <option value=''>All {filter.name}</option>
            {filter.options?.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        );

      case 'multiselect':
        return (
          <select
            id={filter.id}
            multiple
            value={Array.isArray(value) ? value : []}
            onChange={(e) => {
              const selectedValues = Array.from(e.target.selectedOptions, (option) => option.value);
              onChange(filter.id, selectedValues);
            }}
            className='mt-1 block w-full pl-3 pr-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md'
            required={filter.required}
            size={Math.min(filter.options?.length || 5, 5)}
          >
            {filter.options?.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        );

      case 'date_range':
        const dateValue = value || {};
        return (
          <div className='flex space-x-2'>
            <input
              type='date'
              value={dateValue.start || ''}
              onChange={(e) => onChange(filter.id, { ...dateValue, start: e.target.value })}
              className='mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm'
              placeholder='Start date'
            />
            <input
              type='date'
              value={dateValue.end || ''}
              onChange={(e) => onChange(filter.id, { ...dateValue, end: e.target.value })}
              className='mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm'
              placeholder='End date'
            />
          </div>
        );

      case 'number_range':
        const numberValue = value || {};
        return (
          <div className='flex space-x-2'>
            <input
              type='number'
              value={numberValue.min || ''}
              onChange={(e) => onChange(filter.id, { ...numberValue, min: e.target.value })}
              className='mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm'
              placeholder='Min'
            />
            <input
              type='number'
              value={numberValue.max || ''}
              onChange={(e) => onChange(filter.id, { ...numberValue, max: e.target.value })}
              className='mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm'
              placeholder='Max'
            />
          </div>
        );

      case 'text':
      default:
        return (
          <input
            type='text'
            id={filter.id}
            value={value || ''}
            onChange={(e) => onChange(filter.id, e.target.value)}
            className='mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm'
            placeholder={`Filter by ${filter.name.toLowerCase()}`}
            required={filter.required}
          />
        );
    }
  };

  const containerClasses = cn(
    'flex gap-4',
    orientation === 'vertical' ? 'flex-col' : 'flex-wrap',
    className
  );

  return (
    <div className={containerClasses}>
      {filters.map((filter) => (
        <div key={filter.id} className='min-w-0 flex-1'>
          <label htmlFor={filter.id} className='block text-sm font-medium text-gray-700'>
            {filter.name}
            {filter.required && <span className='text-red-500 ml-1'>*</span>}
          </label>
          {renderFilter(filter)}
        </div>
      ))}

      {/* Clear filters button */}
      {Object.keys(values).some((key) => values[key] !== undefined && values[key] !== '') && (
        <div className='flex items-end'>
          <button
            onClick={() => {
              filters.forEach((filter) => onChange(filter.id, filter.defaultValue || ''));
            }}
            className='px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500'
          >
            Clear All
          </button>
        </div>
      )}
    </div>
  );
};
