/**
 * Filter Bar Component
 *
 * Configurable filter bar for dashboards
 */

"use client";

import { Search, X, Filter, Calendar, ChevronDown, Check } from "lucide-react";
import { useState, useRef, useEffect, type ReactNode } from "react";

import { cn } from "../utils/cn";

// ============================================================================
// Types
// ============================================================================

export interface FilterOption {
  value: string;
  label: string;
}

export interface FilterConfig {
  id: string;
  label: string;
  type: "select" | "multiselect" | "date" | "daterange" | "search";
  options?: FilterOption[];
  placeholder?: string;
  defaultValue?: string | string[];
}

export interface FilterValues {
  [key: string]: string | string[] | undefined;
}

export interface FilterBarProps {
  /** Filter configurations */
  filters: FilterConfig[];
  /** Current filter values */
  values?: FilterValues;
  /** On filter change */
  onChange?: (values: FilterValues) => void;
  /** Show search input */
  showSearch?: boolean;
  /** Search placeholder */
  searchPlaceholder?: string;
  /** Search value */
  searchValue?: string;
  /** On search change */
  onSearchChange?: (value: string) => void;
  /** Additional actions */
  actions?: ReactNode;
  /** Show clear all button */
  showClear?: boolean;
  /** CSS class name */
  className?: string;
}

// ============================================================================
// Component
// ============================================================================

export function FilterBar({
  filters,
  values = {},
  onChange,
  showSearch = true,
  searchPlaceholder = "Search...",
  searchValue = "",
  onSearchChange,
  actions,
  showClear = true,
  className,
}: FilterBarProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const handleFilterChange = (id: string, value: string | string[]) => {
    onChange?.({ ...values, [id]: value });
  };

  const handleClearAll = () => {
    const clearedValues: FilterValues = {};
    filters.forEach((f) => {
      clearedValues[f.id] = undefined;
    });
    onChange?.(clearedValues);
    onSearchChange?.("");
  };

  const hasActiveFilters =
    Object.values(values).some((v) => v !== undefined && v !== "" && (Array.isArray(v) ? v.length > 0 : true)) ||
    searchValue !== "";

  return (
    <div className={cn("space-y-3", className)}>
      {/* Main Filter Row */}
      <div className="flex flex-wrap items-center gap-3">
        {/* Search */}
        {showSearch && (
          <div className="relative flex-1 min-w-[200px] max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              value={searchValue}
              onChange={(e) => onSearchChange?.(e.target.value)}
              placeholder={searchPlaceholder}
              className={cn(
                "w-full h-9 pl-9 pr-3 rounded-md border border-gray-300",
                "text-sm placeholder:text-gray-400",
                "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              )}
            />
          </div>
        )}

        {/* Quick Filters (first 3) */}
        {filters.slice(0, 3).map((filter) => (
          <FilterControl
            key={filter.id}
            filter={filter}
            value={values[filter.id]}
            onChange={(value) => handleFilterChange(filter.id, value)}
          />
        ))}

        {/* More Filters Toggle */}
        {filters.length > 3 && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className={cn(
              "inline-flex items-center gap-2 h-9 px-3 rounded-md border text-sm font-medium",
              isExpanded
                ? "bg-blue-50 border-blue-200 text-blue-700"
                : "bg-white border-gray-300 text-gray-700 hover:bg-gray-50"
            )}
          >
            <Filter className="h-4 w-4" />
            More Filters
            {filters.length > 3 && (
              <span className="bg-gray-200 text-gray-600 px-1.5 py-0.5 rounded text-xs">
                {filters.length - 3}
              </span>
            )}
          </button>
        )}

        {/* Clear All */}
        {showClear && hasActiveFilters && (
          <button
            onClick={handleClearAll}
            className="inline-flex items-center gap-1 h-9 px-3 text-sm text-gray-500 hover:text-gray-700"
          >
            <X className="h-4 w-4" />
            Clear all
          </button>
        )}

        {/* Additional Actions */}
        {actions && <div className="flex items-center gap-2 ml-auto">{actions}</div>}
      </div>

      {/* Expanded Filters */}
      {isExpanded && filters.length > 3 && (
        <div className="flex flex-wrap items-center gap-3 p-3 bg-gray-50 rounded-md">
          {filters.slice(3).map((filter) => (
            <FilterControl
              key={filter.id}
              filter={filter}
              value={values[filter.id]}
              onChange={(value) => handleFilterChange(filter.id, value)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Filter Control
// ============================================================================

interface FilterControlProps {
  filter: FilterConfig;
  value?: string | string[];
  onChange: (value: string | string[]) => void;
}

function FilterControl({ filter, value, onChange }: FilterControlProps) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [isOpen]);

  switch (filter.type) {
    case "select":
      return (
        <select
          value={(value as string) ?? ""}
          onChange={(e) => onChange(e.target.value)}
          className={cn(
            "h-9 px-3 rounded-md border border-gray-300 bg-white text-sm",
            "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          )}
        >
          <option value="">{filter.placeholder ?? filter.label}</option>
          {filter.options?.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      );

    case "multiselect": {
      const selectedValues = Array.isArray(value) ? value : [];
      const selectedLabels = selectedValues
        .map((v) => filter.options?.find((o) => o.value === v)?.label)
        .filter(Boolean);

      const toggleOption = (optValue: string) => {
        const newValues = selectedValues.includes(optValue)
          ? selectedValues.filter((v) => v !== optValue)
          : [...selectedValues, optValue];
        onChange(newValues);
      };

      return (
        <div className="relative" ref={dropdownRef}>
          <button
            type="button"
            onClick={() => setIsOpen(!isOpen)}
            className={cn(
              "h-9 px-3 rounded-md border border-gray-300 bg-white text-sm",
              "flex items-center gap-2 min-w-[120px]",
              "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            )}
          >
            <span className="flex-1 text-left truncate">
              {selectedLabels.length > 0
                ? selectedLabels.length === 1
                  ? selectedLabels[0]
                  : `${selectedLabels.length} selected`
                : filter.placeholder ?? filter.label}
            </span>
            <ChevronDown className={cn("h-4 w-4 text-gray-400 transition-transform", isOpen && "rotate-180")} />
          </button>
          {isOpen && (
            <div className="absolute z-50 mt-1 w-full min-w-[180px] rounded-md border border-gray-200 bg-white shadow-lg">
              <div className="max-h-60 overflow-y-auto py-1">
                {filter.options?.map((opt) => {
                  const isSelected = selectedValues.includes(opt.value);
                  return (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => toggleOption(opt.value)}
                      className={cn(
                        "flex items-center gap-2 w-full px-3 py-2 text-sm text-left",
                        "hover:bg-gray-100",
                        isSelected && "bg-blue-50"
                      )}
                    >
                      <div
                        className={cn(
                          "h-4 w-4 rounded border flex items-center justify-center",
                          isSelected ? "bg-blue-600 border-blue-600" : "border-gray-300"
                        )}
                      >
                        {isSelected && <Check className="h-3 w-3 text-white" />}
                      </div>
                      {opt.label}
                    </button>
                  );
                })}
              </div>
              {selectedValues.length > 0 && (
                <div className="border-t border-gray-100 px-3 py-2">
                  <button
                    type="button"
                    onClick={() => onChange([])}
                    className="text-sm text-gray-500 hover:text-gray-700"
                  >
                    Clear selection
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      );
    }

    case "date":
      return (
        <div className="relative">
          <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="date"
            value={(value as string) ?? ""}
            onChange={(e) => onChange(e.target.value)}
            className={cn(
              "h-9 pl-9 pr-3 rounded-md border border-gray-300 text-sm",
              "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            )}
          />
        </div>
      );

    case "daterange": {
      const rangeValue = Array.isArray(value) ? value : ["", ""];
      const [startDate, endDate] = rangeValue;

      const handleStartChange = (newStart: string) => {
        onChange([newStart, endDate || ""]);
      };

      const handleEndChange = (newEnd: string) => {
        onChange([startDate || "", newEnd]);
      };

      return (
        <div className="flex items-center gap-2">
          <div className="relative">
            <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="date"
              value={startDate || ""}
              onChange={(e) => handleStartChange(e.target.value)}
              placeholder="Start date"
              className={cn(
                "h-9 pl-9 pr-3 rounded-md border border-gray-300 text-sm",
                "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              )}
            />
          </div>
          <span className="text-gray-400">to</span>
          <div className="relative">
            <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="date"
              value={endDate || ""}
              onChange={(e) => handleEndChange(e.target.value)}
              placeholder="End date"
              className={cn(
                "h-9 pl-9 pr-3 rounded-md border border-gray-300 text-sm",
                "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              )}
            />
          </div>
        </div>
      );
    }

    case "search":
    default:
      return (
        <input
          type="text"
          value={(value as string) ?? ""}
          onChange={(e) => onChange(e.target.value)}
          placeholder={filter.placeholder ?? filter.label}
          className={cn(
            "h-9 px-3 rounded-md border border-gray-300 text-sm",
            "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          )}
        />
      );
  }
}

export default FilterBar;
