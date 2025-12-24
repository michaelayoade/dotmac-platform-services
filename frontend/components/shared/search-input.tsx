"use client";

import { useState, useRef, useEffect, type ChangeEvent } from "react";
import { Search, X, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { useDebounce } from "@/lib/hooks/use-debounce";

interface SearchInputProps {
  value?: string;
  onChange?: (value: string) => void;
  onSearch?: (value: string) => void;
  placeholder?: string;
  debounceMs?: number;
  loading?: boolean;
  className?: string;
  autoFocus?: boolean;
  showClear?: boolean;
  size?: "sm" | "md" | "lg";
}

export function SearchInput({
  value: controlledValue,
  onChange,
  onSearch,
  placeholder = "Search...",
  debounceMs = 300,
  loading = false,
  className,
  autoFocus = false,
  showClear = true,
  size = "md",
}: SearchInputProps) {
  const [internalValue, setInternalValue] = useState(controlledValue || "");
  const inputRef = useRef<HTMLInputElement>(null);

  const value = controlledValue !== undefined ? controlledValue : internalValue;
  const debouncedValue = useDebounce(value, debounceMs);

  useEffect(() => {
    if (onSearch && debouncedValue !== undefined) {
      onSearch(debouncedValue);
    }
  }, [debouncedValue, onSearch]);

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    if (controlledValue === undefined) {
      setInternalValue(newValue);
    }
    onChange?.(newValue);
  };

  const handleClear = () => {
    if (controlledValue === undefined) {
      setInternalValue("");
    }
    onChange?.("");
    onSearch?.("");
    inputRef.current?.focus();
  };

  const sizeClasses = {
    sm: "h-8 text-sm pl-8 pr-8",
    md: "h-10 text-sm pl-10 pr-10",
    lg: "h-12 text-base pl-12 pr-12",
  };

  const iconSizeClasses = {
    sm: "w-4 h-4",
    md: "w-4 h-4",
    lg: "w-5 h-5",
  };

  const iconPositionClasses = {
    sm: "left-2",
    md: "left-3",
    lg: "left-4",
  };

  return (
    <div className={cn("relative", className)}>
      <Search
        className={cn(
          "absolute top-1/2 -translate-y-1/2 text-text-muted pointer-events-none",
          iconSizeClasses[size],
          iconPositionClasses[size]
        )}
      />
      <input
        ref={inputRef}
        type="text"
        value={value}
        onChange={handleChange}
        placeholder={placeholder}
        autoFocus={autoFocus}
        className={cn(
          "w-full rounded-md bg-surface-overlay border border-border text-text-primary placeholder:text-text-muted",
          "focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent",
          "transition-all duration-200",
          sizeClasses[size]
        )}
      />
      <div
        className={cn(
          "absolute top-1/2 -translate-y-1/2 right-3 flex items-center gap-1"
        )}
      >
        {loading && (
          <Loader2
            className={cn("animate-spin text-text-muted", iconSizeClasses[size])}
          />
        )}
        {showClear && value && !loading && (
          <button
            type="button"
            onClick={handleClear}
            className="p-0.5 rounded hover:bg-surface-overlay text-text-muted hover:text-text-secondary transition-colors"
          >
            <X className={iconSizeClasses[size]} />
          </button>
        )}
      </div>
    </div>
  );
}
