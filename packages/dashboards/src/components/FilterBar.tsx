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
          <div className="relative flex-1 min-w-0 sm:min-w-[200px] max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted" />
            <input
              type="text"
              value={searchValue}
              onChange={(e) => onSearchChange?.(e.target.value)}
              placeholder={searchPlaceholder}
              className={cn(
                "w-full h-10 pl-9 pr-3 rounded-md border border-border bg-surface",
                "text-sm text-text-primary placeholder:text-text-muted",
                "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 focus:border-transparent"
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
              "inline-flex items-center gap-2 h-10 px-3 rounded-md border text-sm font-medium",
              "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
              isExpanded
                ? "bg-accent/10 border-accent/30 text-accent"
                : "bg-surface border-border text-text-primary hover:bg-surface-overlay"
            )}
          >
            <Filter className="h-4 w-4" />
            More Filters
            {filters.length > 3 && (
              <span className="bg-surface-overlay text-text-muted px-1.5 py-0.5 rounded text-xs">
                {filters.length - 3}
              </span>
            )}
          </button>
        )}

        {/* Clear All */}
        {showClear && hasActiveFilters && (
          <button
            onClick={handleClearAll}
            className={cn(
              "inline-flex items-center gap-1 h-10 px-3 text-sm text-text-muted hover:text-text-primary",
              "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 rounded-md"
            )}
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
        <div className="flex flex-wrap items-center gap-3 p-3 bg-surface-overlay rounded-md border border-border">
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

  // Close dropdown on click outside or ESC key
  useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen]);

  switch (filter.type) {
    case "select":
      return (
        <select
          value={(value as string) ?? ""}
          onChange={(e) => onChange(e.target.value)}
          className={cn(
            "h-10 px-3 rounded-md border border-border bg-surface text-sm text-text-primary",
            "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 focus:border-transparent"
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
            aria-expanded={isOpen}
            aria-haspopup="listbox"
            className={cn(
              "h-10 px-3 rounded-md border border-border bg-surface text-sm text-text-primary",
              "flex items-center gap-2 min-w-[120px]",
              "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 focus:border-transparent"
            )}
          >
            <span className="flex-1 text-left truncate">
              {selectedLabels.length > 0
                ? selectedLabels.length === 1
                  ? selectedLabels[0]
                  : `${selectedLabels.length} selected`
                : filter.placeholder ?? filter.label}
            </span>
            <ChevronDown className={cn("h-4 w-4 text-text-muted transition-transform", isOpen && "rotate-180")} />
          </button>
          {isOpen && (
            <div
              className="absolute z-50 mt-1 w-full min-w-[180px] rounded-md border border-border bg-surface shadow-lg"
              role="listbox"
            >
              <div className="max-h-60 overflow-y-auto py-1">
                {filter.options?.map((opt) => {
                  const isSelected = selectedValues.includes(opt.value);
                  return (
                    <button
                      key={opt.value}
                      type="button"
                      role="option"
                      aria-selected={isSelected}
                      onClick={() => toggleOption(opt.value)}
                      className={cn(
                        "flex items-center gap-2 w-full px-3 py-2 text-sm text-left text-text-primary",
                        "hover:bg-surface-overlay",
                        isSelected && "bg-accent/10"
                      )}
                    >
                      <div
                        className={cn(
                          "h-4 w-4 rounded border flex items-center justify-center",
                          isSelected ? "bg-accent border-accent" : "border-border"
                        )}
                      >
                        {isSelected && <Check className="h-3 w-3 text-text-inverse" />}
                      </div>
                      {opt.label}
                    </button>
                  );
                })}
              </div>
              {selectedValues.length > 0 && (
                <div className="border-t border-border px-3 py-2">
                  <button
                    type="button"
                    onClick={() => onChange([])}
                    className="text-sm text-text-muted hover:text-text-primary"
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
          <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted" />
          <input
            type="date"
            value={(value as string) ?? ""}
            onChange={(e) => onChange(e.target.value)}
            className={cn(
              "h-10 pl-9 pr-3 rounded-md border border-border bg-surface text-sm text-text-primary",
              "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 focus:border-transparent"
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
            <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted" />
            <input
              type="date"
              value={startDate || ""}
              onChange={(e) => handleStartChange(e.target.value)}
              placeholder="Start date"
              className={cn(
                "h-10 pl-9 pr-3 rounded-md border border-border bg-surface text-sm text-text-primary",
                "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 focus:border-transparent"
              )}
            />
          </div>
          <span className="text-text-muted">to</span>
          <div className="relative">
            <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted" />
            <input
              type="date"
              value={endDate || ""}
              onChange={(e) => handleEndChange(e.target.value)}
              placeholder="End date"
              className={cn(
                "h-10 pl-9 pr-3 rounded-md border border-border bg-surface text-sm text-text-primary",
                "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 focus:border-transparent"
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
            "h-10 px-3 rounded-md border border-border bg-surface text-sm text-text-primary",
            "placeholder:text-text-muted",
            "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 focus:border-transparent"
          )}
        />
      );
  }
}

export default FilterBar;
