'use client';

import React, { useState, useCallback, useMemo, useRef, useEffect } from 'react';
import { Search, Filter, X, ChevronDown, Calendar, MoreHorizontal } from 'lucide-react';
import { EntityType, FilterConfig, SearchQuery, PortalVariant } from '../../types';
import { usePortalTheme } from '../../hooks/usePortalTheme';
import { cn } from '../../utils/cn';

interface UniversalSearchProps {
  entityType: EntityType;
  portalVariant: PortalVariant;
  filters: FilterConfig[];
  onSearch: (query: SearchQuery) => void;
  placeholder?: string;
  className?: string;
  initialQuery?: string;
  initialFilters?: Record<string, any>;
  debounceMs?: number;
  showFilters?: boolean;
  showSort?: boolean;
  sortOptions?: Array<{
    field: string;
    label: string;
  }>;
  savedSearches?: Array<{
    id: string;
    name: string;
    query: SearchQuery;
  }>;
  onSaveSearch?: (name: string, query: SearchQuery) => void;
}

export function UniversalSearch({
  entityType,
  portalVariant,
  filters,
  onSearch,
  placeholder,
  className,
  initialQuery = '',
  initialFilters = {},
  debounceMs = 300,
  showFilters = true,
  showSort = true,
  sortOptions = [],
  savedSearches = [],
  onSaveSearch,
}: UniversalSearchProps) {
  const theme = usePortalTheme(portalVariant);

  // Search state
  const [query, setQuery] = useState(initialQuery);
  const [activeFilters, setActiveFilters] = useState<Record<string, any>>(initialFilters);
  const [sortField, setSortField] = useState<string>('');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [showFilterPanel, setShowFilterPanel] = useState(false);
  const [showSortMenu, setShowSortMenu] = useState(false);

  // Refs for debouncing and outside click detection
  const searchTimeoutRef = useRef<NodeJS.Timeout>();
  const filterPanelRef = useRef<HTMLDivElement>(null);
  const sortMenuRef = useRef<HTMLDivElement>(null);

  // Debounced search execution
  const executeSearch = useCallback(() => {
    const searchQuery: SearchQuery = {
      query: query.trim() || undefined,
      filters: activeFilters,
      sort: sortField ? { field: sortField, direction: sortDirection } : undefined,
    };

    onSearch(searchQuery);
  }, [query, activeFilters, sortField, sortDirection, onSearch]);

  // Debounce search execution
  useEffect(() => {
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    searchTimeoutRef.current = setTimeout(() => {
      executeSearch();
    }, debounceMs);

    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, [executeSearch, debounceMs]);

  // Handle filter changes
  const updateFilter = useCallback((key: string, value: any) => {
    setActiveFilters((prev) => {
      if (value === undefined || value === null || value === '') {
        const { [key]: removed, ...rest } = prev;
        return rest;
      }
      return { ...prev, [key]: value };
    });
  }, []);

  // Clear all filters
  const clearAllFilters = useCallback(() => {
    setActiveFilters({});
    setQuery('');
    setSortField('');
  }, []);

  // Handle outside clicks
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (filterPanelRef.current && !filterPanelRef.current.contains(event.target as Node)) {
        setShowFilterPanel(false);
      }
      if (sortMenuRef.current && !sortMenuRef.current.contains(event.target as Node)) {
        setShowSortMenu(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Count active filters
  const activeFilterCount = useMemo(() => {
    return Object.keys(activeFilters).length;
  }, [activeFilters]);

  // Get entity-specific placeholder
  const searchPlaceholder = useMemo(() => {
    if (placeholder) return placeholder;

    const entityPlaceholders: Record<EntityType, string> = {
      customer: 'Search customers by name, email, or phone...',
      tenant: 'Search tenants by name or domain...',
      user: 'Search users by name or email...',
      device: 'Search devices by name, model, or serial number...',
      service: 'Search services by name or plan...',
      reseller: 'Search resellers by name or territory...',
      technician: 'Search technicians by name or ID...',
      'work-order': 'Search work orders by ID or customer...',
      invoice: 'Search invoices by number or customer...',
      ticket: 'Search tickets by ID or subject...',
    };

    return entityPlaceholders[entityType] || 'Search...';
  }, [placeholder, entityType]);

  return (
    <div className={cn('space-y-4', className)}>
      {/* Main Search Bar */}
      <div className='flex gap-3'>
        {/* Search Input */}
        <div className='relative flex-1'>
          <div className='absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none'>
            <Search className='h-5 w-5 text-gray-400' />
          </div>

          <input
            type='text'
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={searchPlaceholder}
            className={cn(
              'block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md',
              'placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-primary-500',
              'focus:border-primary-500 sm:text-sm',
              theme.components.input
            )}
          />

          {query && (
            <button
              onClick={() => setQuery('')}
              className='absolute inset-y-0 right-0 pr-3 flex items-center'
            >
              <X className='h-4 w-4 text-gray-400 hover:text-gray-600' />
            </button>
          )}
        </div>

        {/* Filter Button */}
        {showFilters && filters.length > 0 && (
          <div className='relative' ref={filterPanelRef}>
            <button
              onClick={() => setShowFilterPanel(!showFilterPanel)}
              className={cn(
                'inline-flex items-center px-4 py-2 border border-gray-300 rounded-md',
                'text-sm font-medium text-gray-700 bg-white hover:bg-gray-50',
                'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500',
                activeFilterCount > 0 && 'bg-primary-50 border-primary-300 text-primary-700',
                theme.components.button
              )}
            >
              <Filter className='h-4 w-4 mr-2' />
              Filters
              {activeFilterCount > 0 && (
                <span className='ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800'>
                  {activeFilterCount}
                </span>
              )}
            </button>

            {/* Filter Panel */}
            {showFilterPanel && (
              <FilterPanel
                filters={filters}
                activeFilters={activeFilters}
                onUpdateFilter={updateFilter}
                onClearAll={clearAllFilters}
                theme={theme}
              />
            )}
          </div>
        )}

        {/* Sort Button */}
        {showSort && sortOptions.length > 0 && (
          <div className='relative' ref={sortMenuRef}>
            <button
              onClick={() => setShowSortMenu(!showSortMenu)}
              className={cn(
                'inline-flex items-center px-4 py-2 border border-gray-300 rounded-md',
                'text-sm font-medium text-gray-700 bg-white hover:bg-gray-50',
                'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500',
                sortField && 'bg-primary-50 border-primary-300 text-primary-700',
                theme.components.button
              )}
            >
              Sort
              <ChevronDown className='h-4 w-4 ml-2' />
            </button>

            {/* Sort Menu */}
            {showSortMenu && (
              <SortMenu
                options={sortOptions}
                currentField={sortField}
                currentDirection={sortDirection}
                onSort={(field, direction) => {
                  setSortField(field);
                  setSortDirection(direction);
                  setShowSortMenu(false);
                }}
                theme={theme}
              />
            )}
          </div>
        )}

        {/* Save Search Button */}
        {onSaveSearch && (query || activeFilterCount > 0) && (
          <button
            onClick={() => {
              const name = prompt('Save search as:');
              if (name) {
                onSaveSearch(name, {
                  query: query || undefined,
                  filters: activeFilters,
                  sort: sortField ? { field: sortField, direction: sortDirection } : undefined,
                });
              }
            }}
            className={cn(
              'inline-flex items-center px-4 py-2 border border-gray-300 rounded-md',
              'text-sm font-medium text-gray-700 bg-white hover:bg-gray-50',
              'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500',
              theme.components.button
            )}
          >
            Save
          </button>
        )}
      </div>

      {/* Saved Searches */}
      {savedSearches.length > 0 && (
        <div className='flex flex-wrap gap-2'>
          {savedSearches.map((search) => (
            <button
              key={search.id}
              onClick={() => {
                setQuery(search.query.query || '');
                setActiveFilters(search.query.filters);
                if (search.query.sort) {
                  setSortField(search.query.sort.field);
                  setSortDirection(search.query.sort.direction);
                }
              }}
              className={cn(
                'inline-flex items-center px-3 py-1 text-xs font-medium',
                'bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200',
                'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500'
              )}
            >
              {search.name}
            </button>
          ))}
        </div>
      )}

      {/* Active Filters Display */}
      {activeFilterCount > 0 && (
        <div className='flex flex-wrap gap-2'>
          {Object.entries(activeFilters).map(([key, value]) => {
            const filter = filters.find((f) => f.key === key);
            if (!filter || !value) return null;

            const displayValue = Array.isArray(value) ? value.join(', ') : value;

            return (
              <span
                key={key}
                className='inline-flex items-center px-3 py-1 text-sm bg-primary-100 text-primary-800 rounded-full'
              >
                <span className='font-medium'>{filter.label}:</span>
                <span className='ml-1'>{displayValue}</span>
                <button
                  onClick={() => updateFilter(key, undefined)}
                  className='ml-2 hover:text-primary-600'
                >
                  <X className='h-3 w-3' />
                </button>
              </span>
            );
          })}

          {activeFilterCount > 1 && (
            <button
              onClick={clearAllFilters}
              className='inline-flex items-center px-3 py-1 text-sm text-gray-600 hover:text-gray-800'
            >
              Clear all
              <X className='h-3 w-3 ml-1' />
            </button>
          )}
        </div>
      )}
    </div>
  );
}

// Filter Panel Component
interface FilterPanelProps {
  filters: FilterConfig[];
  activeFilters: Record<string, any>;
  onUpdateFilter: (key: string, value: any) => void;
  onClearAll: () => void;
  theme: any;
}

function FilterPanel({
  filters,
  activeFilters,
  onUpdateFilter,
  onClearAll,
  theme,
}: FilterPanelProps) {
  return (
    <div
      className={cn(
        'absolute right-0 z-10 mt-2 w-80 bg-white rounded-md shadow-lg',
        'border border-gray-200 divide-y divide-gray-100'
      )}
    >
      <div className='px-4 py-3'>
        <div className='flex items-center justify-between'>
          <h3 className='text-sm font-medium text-gray-900'>Filters</h3>
          <button onClick={onClearAll} className='text-sm text-gray-500 hover:text-gray-700'>
            Clear all
          </button>
        </div>
      </div>

      <div className='px-4 py-3 space-y-4 max-h-96 overflow-y-auto'>
        {filters.map((filter) => (
          <FilterField
            key={filter.key}
            config={filter}
            value={activeFilters[filter.key]}
            onChange={(value) => onUpdateFilter(filter.key, value)}
            theme={theme}
          />
        ))}
      </div>
    </div>
  );
}

// Individual Filter Field Component
interface FilterFieldProps {
  config: FilterConfig;
  value: any;
  onChange: (value: any) => void;
  theme: any;
}

function FilterField({ config, value, onChange, theme }: FilterFieldProps) {
  const renderField = () => {
    switch (config.type) {
      case 'text':
        return (
          <input
            type='text'
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            placeholder={config.placeholder}
            className={cn(
              'block w-full rounded-md border-gray-300 shadow-sm',
              'focus:border-primary-500 focus:ring-primary-500 sm:text-sm',
              theme.components.input
            )}
          />
        );

      case 'select':
        return (
          <select
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            className={cn(
              'block w-full rounded-md border-gray-300 shadow-sm',
              'focus:border-primary-500 focus:ring-primary-500 sm:text-sm',
              theme.components.input
            )}
          >
            <option value=''>All {config.label}</option>
            {config.options?.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        );

      case 'multiselect':
        const selectedValues = Array.isArray(value) ? value : [];
        return (
          <div className='space-y-2 max-h-32 overflow-y-auto'>
            {config.options?.map((option) => (
              <label key={option.value} className='flex items-center'>
                <input
                  type='checkbox'
                  checked={selectedValues.includes(option.value)}
                  onChange={(e) => {
                    const newValues = e.target.checked
                      ? [...selectedValues, option.value]
                      : selectedValues.filter((v) => v !== option.value);
                    onChange(newValues.length > 0 ? newValues : undefined);
                  }}
                  className='h-4 w-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500'
                />
                <span className='ml-2 text-sm text-gray-700'>{option.label}</span>
              </label>
            ))}
          </div>
        );

      case 'date':
        return (
          <input
            type='date'
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            className={cn(
              'block w-full rounded-md border-gray-300 shadow-sm',
              'focus:border-primary-500 focus:ring-primary-500 sm:text-sm',
              theme.components.input
            )}
          />
        );

      case 'number':
        return (
          <input
            type='number'
            value={value || ''}
            onChange={(e) => onChange(e.target.value ? Number(e.target.value) : undefined)}
            placeholder={config.placeholder}
            className={cn(
              'block w-full rounded-md border-gray-300 shadow-sm',
              'focus:border-primary-500 focus:ring-primary-500 sm:text-sm',
              theme.components.input
            )}
          />
        );

      case 'boolean':
        return (
          <select
            value={value === undefined ? '' : value.toString()}
            onChange={(e) => {
              const val = e.target.value;
              onChange(val === '' ? undefined : val === 'true');
            }}
            className={cn(
              'block w-full rounded-md border-gray-300 shadow-sm',
              'focus:border-primary-500 focus:ring-primary-500 sm:text-sm',
              theme.components.input
            )}
          >
            <option value=''>All</option>
            <option value='true'>Yes</option>
            <option value='false'>No</option>
          </select>
        );

      default:
        return null;
    }
  };

  return (
    <div>
      <label className='block text-sm font-medium text-gray-700 mb-1'>{config.label}</label>
      {renderField()}
    </div>
  );
}

// Sort Menu Component
interface SortMenuProps {
  options: Array<{ field: string; label: string }>;
  currentField: string;
  currentDirection: 'asc' | 'desc';
  onSort: (field: string, direction: 'asc' | 'desc') => void;
  theme: any;
}

function SortMenu({ options, currentField, currentDirection, onSort, theme }: SortMenuProps) {
  return (
    <div
      className={cn(
        'absolute right-0 z-10 mt-2 w-48 bg-white rounded-md shadow-lg',
        'border border-gray-200 divide-y divide-gray-100'
      )}
    >
      <div className='py-1'>
        {options.map((option) => (
          <div key={option.field}>
            <button
              onClick={() => onSort(option.field, 'asc')}
              className={cn(
                'flex w-full px-4 py-2 text-sm text-left hover:bg-gray-100',
                currentField === option.field &&
                  currentDirection === 'asc' &&
                  'bg-primary-50 text-primary-700'
              )}
            >
              {option.label} (A-Z)
            </button>
            <button
              onClick={() => onSort(option.field, 'desc')}
              className={cn(
                'flex w-full px-4 py-2 text-sm text-left hover:bg-gray-100',
                currentField === option.field &&
                  currentDirection === 'desc' &&
                  'bg-primary-50 text-primary-700'
              )}
            >
              {option.label} (Z-A)
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
