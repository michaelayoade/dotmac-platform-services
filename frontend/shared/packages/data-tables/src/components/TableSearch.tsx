/**
 * TableSearch Component
 * Universal search component with fuzzy matching and debounced input
 */

import React, { useMemo, useRef, useEffect } from 'react';
import { Search, X } from 'lucide-react';
import { Button, Input } from '@dotmac/primitives';
import { cva } from 'class-variance-authority';
import { clsx } from 'clsx';
import { useHotkeys } from 'react-hotkeys-hook';
import Fuse from 'fuse.js';
import type { SearchConfig, PortalVariant } from '../types';

const searchVariants = cva('relative flex items-center gap-2', {
  variants: {
    portal: {
      admin: 'text-blue-600',
      customer: 'text-green-600',
      reseller: 'text-purple-600',
      technician: 'text-orange-600',
      management: 'text-red-600',
    },
    size: {
      sm: 'text-sm',
      md: 'text-base',
      lg: 'text-lg',
    },
  },
  defaultVariants: {
    portal: 'admin',
    size: 'md',
  },
});

interface TableSearchProps {
  searchConfig: SearchConfig;
  value: string;
  onChange: (value: string) => void;
  data?: any[];
  portal?: PortalVariant;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  onFocus?: () => void;
  onBlur?: () => void;
}

export const TableSearch: React.FC<TableSearchProps> = ({
  searchConfig,
  value,
  onChange,
  data = [],
  portal = 'admin',
  size = 'md',
  className,
  onFocus,
  onBlur,
}) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const debounceRef = useRef<NodeJS.Timeout>();
  const fuseRef = useRef<Fuse<any> | null>(null);

  // Initialize Fuse.js for fuzzy search
  const fuseOptions = useMemo(
    () => ({
      keys: searchConfig.searchableColumns || [],
      threshold: 0.4, // Fuzzy matching threshold
      includeScore: true,
      includeMatches: searchConfig.highlightMatches,
      minMatchCharLength: searchConfig.minSearchLength || 2,
    }),
    [searchConfig]
  );

  useEffect(() => {
    if (searchConfig.fuzzySearch && data.length > 0 && searchConfig.searchableColumns) {
      fuseRef.current = new Fuse(data, fuseOptions);
    }
  }, [data, fuseOptions, searchConfig.fuzzySearch, searchConfig.searchableColumns]);

  // Debounced search handler
  const handleSearchChange = (searchValue: string) => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    debounceRef.current = setTimeout(() => {
      onChange(searchValue);
    }, searchConfig.debounceMs || 300);
  };

  // Clear search
  const handleClear = () => {
    onChange('');
    if (inputRef.current) {
      inputRef.current.focus();
    }
  };

  // Keyboard shortcuts
  useHotkeys(
    'cmd+f,ctrl+f',
    (e) => {
      e.preventDefault();
      if (inputRef.current) {
        inputRef.current.focus();
        inputRef.current.select();
      }
    },
    { enableOnFormTags: ['INPUT'] }
  );

  useHotkeys(
    'escape',
    () => {
      if (value) {
        handleClear();
      } else if (inputRef.current) {
        inputRef.current.blur();
      }
    },
    { enableOnFormTags: ['INPUT'] }
  );

  if (!searchConfig.enabled) {
    return null;
  }

  return (
    <div className={clsx(searchVariants({ portal, size }), className)}>
      <div className='relative flex-1 max-w-md'>
        <Search className='absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4 pointer-events-none' />
        <Input
          ref={inputRef}
          type='text'
          placeholder={searchConfig.placeholder || 'Search...'}
          value={value}
          onChange={(e) => handleSearchChange(e.target.value)}
          onFocus={onFocus}
          onBlur={onBlur}
          className='pl-10 pr-10'
          data-testid='table-search-input'
        />
        {value && (
          <Button
            variant='ghost'
            size='sm'
            onClick={handleClear}
            className='absolute right-1 top-1/2 transform -translate-y-1/2 h-8 w-8 p-0 hover:bg-gray-100'
            data-testid='table-search-clear'
          >
            <X className='w-4 h-4' />
          </Button>
        )}
      </div>

      {value && searchConfig.fuzzySearch && fuseRef.current && (
        <div className='text-xs text-gray-500'>
          {(() => {
            const results = fuseRef.current!.search(value);
            const exactMatches = results.filter((r) => r.score! < 0.1).length;
            const fuzzyMatches = results.length - exactMatches;

            if (exactMatches > 0 && fuzzyMatches > 0) {
              return `${exactMatches} exact, ${fuzzyMatches} similar`;
            } else if (exactMatches > 0) {
              return `${exactMatches} exact matches`;
            } else if (fuzzyMatches > 0) {
              return `${fuzzyMatches} similar matches`;
            }
            return 'No matches';
          })()}
        </div>
      )}
    </div>
  );
};

export default TableSearch;
