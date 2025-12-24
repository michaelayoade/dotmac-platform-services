/**
 * Select Primitive (Radix-based)
 *
 * Styled select/combobox with support for helper text and error state.
 */

"use client";

import * as SelectPrimitive from "@radix-ui/react-select";
import { Check, ChevronDown, ChevronUp, Loader2 } from "lucide-react";
import React, { forwardRef } from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "../utils/cn";

// ============================================================================//
// Variants
// ============================================================================//

const triggerVariants = cva(
  [
    "inline-flex items-center justify-between",
    "w-full rounded-md border bg-white text-sm",
    "px-3 py-2",
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2",
    "disabled:cursor-not-allowed disabled:opacity-50",
    "transition-colors duration-150",
  ],
  {
    variants: {
      size: {
        sm: "h-9 text-xs",
        md: "h-10 text-sm",
        lg: "h-11 text-base",
      },
      error: {
        true: "border-red-500",
        false: "border-gray-300",
      },
    },
    defaultVariants: {
      size: "md",
      error: false,
    },
  }
);

// ============================================================================//
// Types
// ============================================================================//

export interface SelectOption {
  value: string;
  label: string;
  description?: string;
  disabled?: boolean;
}

export interface SelectProps
  extends SelectPrimitive.SelectProps,
    VariantProps<typeof triggerVariants> {
  label?: string;
  placeholder?: string;
  helperText?: string;
  errorText?: string;
  options: SelectOption[];
  loading?: boolean;
  className?: string;
}

// ============================================================================//
// Component
// ============================================================================//

export const Select = forwardRef<HTMLButtonElement, SelectProps>(
  (
    {
      label,
      placeholder = "Select an option",
      helperText,
      errorText,
      options,
      size,
      error,
      loading = false,
      className,
      children,
      ...props
    },
    _ref
  ) => {
    const hasError = !!errorText || error;

    return (
      <div className={cn("space-y-1", className)}>
        {label && (
          <label className="text-sm font-medium text-gray-800 dark:text-gray-100">
            {label}
          </label>
        )}

        <SelectPrimitive.Root {...props}>
          <SelectPrimitive.Trigger
            className={cn(
              triggerVariants({ size, error: hasError }),
              "text-left"
            )}
            aria-invalid={hasError || undefined}
          >
            <div className="flex items-center gap-2 truncate">
              {loading && <Loader2 className="h-4 w-4 animate-spin text-gray-400" />}
              <SelectPrimitive.Value placeholder={placeholder}>
                {children}
              </SelectPrimitive.Value>
            </div>
            <SelectPrimitive.Icon>
              <ChevronDown className="h-4 w-4 text-gray-500" aria-hidden />
            </SelectPrimitive.Icon>
          </SelectPrimitive.Trigger>

          <SelectPrimitive.Portal>
            <SelectPrimitive.Content
              className={cn(
                "z-50 overflow-hidden rounded-md border border-gray-200 bg-white shadow-lg",
                "data-[state=open]:animate-in data-[state=closed]:animate-out",
                "data-[state=open]:fade-in data-[state=closed]:fade-out"
              )}
              position="popper"
              sideOffset={6}
            >
              <SelectPrimitive.ScrollUpButton className="flex items-center justify-center py-2 text-gray-500">
                <ChevronUp className="h-4 w-4" />
              </SelectPrimitive.ScrollUpButton>
              <SelectPrimitive.Viewport className="p-1">
                {options.map((option) => (
                  <SelectItem
                    key={option.value}
                    value={option.value}
                    disabled={option.disabled}
                    description={option.description}
                  >
                    {option.label}
                  </SelectItem>
                ))}
              </SelectPrimitive.Viewport>
              <SelectPrimitive.ScrollDownButton className="flex items-center justify-center py-2 text-gray-500">
                <ChevronDown className="h-4 w-4" />
              </SelectPrimitive.ScrollDownButton>
            </SelectPrimitive.Content>
          </SelectPrimitive.Portal>
        </SelectPrimitive.Root>

        {helperText && !hasError && (
          <p className="text-xs text-gray-500">{helperText}</p>
        )}
        {hasError && (
          <p className="text-xs text-red-600">{errorText}</p>
        )}
      </div>
    );
  }
);

Select.displayName = "Select";

// ============================================================================//
// Item
// ============================================================================//

interface SelectItemProps extends SelectPrimitive.SelectItemProps {
  children: React.ReactNode;
  description?: string;
}

export function SelectItem({
  children,
  className,
  description,
  ...props
}: SelectItemProps) {
  return (
    <SelectPrimitive.Item
      className={cn(
        "relative flex w-full cursor-pointer select-none items-center justify-between gap-2",
        "rounded-md px-3 py-2 text-sm text-gray-800",
        "focus:bg-blue-50 focus:text-blue-700 outline-none",
        "data-[disabled]:pointer-events-none data-[disabled]:opacity-50",
        className
      )}
      {...props}
    >
      <div className="flex flex-col">
        <span>{children}</span>
        {description && (
          <span className="text-xs text-gray-500">{description}</span>
        )}
      </div>
      <SelectPrimitive.ItemIndicator>
        <Check className="h-4 w-4 text-blue-600" aria-hidden />
      </SelectPrimitive.ItemIndicator>
    </SelectPrimitive.Item>
  );
}

SelectItem.displayName = "SelectItem";
