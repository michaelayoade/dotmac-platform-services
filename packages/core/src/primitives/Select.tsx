/**
 * Select Primitive
 *
 * Supports two modes:
 * 1. Radix-based (options prop) - For styled dropdowns with custom rendering
 * 2. Native HTML (children + onChange) - For simple selects with option elements
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
    "w-full rounded-md border bg-background text-sm",
    "px-3 py-2",
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2",
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
        true: "border-destructive",
        false: "border-input",
      },
    },
    defaultVariants: {
      size: "md",
      error: false,
    },
  }
);

const nativeSelectVariants = cva(
  [
    "w-full rounded-md border bg-background text-sm",
    "px-3 py-2 pr-8",
    "text-foreground",
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2",
    "disabled:cursor-not-allowed disabled:opacity-50",
    "transition-colors duration-150",
    "appearance-none",
    "bg-[url('data:image/svg+xml;charset=UTF-8,%3csvg%20xmlns%3d%22http%3a%2f%2fwww.w3.org%2f2000%2fsvg%22%20width%3d%2224%22%20height%3d%2224%22%20viewBox%3d%220%200%2024%2024%22%20fill%3d%22none%22%20stroke%3d%22currentColor%22%20stroke-width%3d%222%22%20stroke-linecap%3d%22round%22%20stroke-linejoin%3d%22round%22%3e%3cpath%20d%3d%22m6%209%206%206%206-6%22%2f%3e%3c%2fsvg%3e')]",
    "bg-[length:1rem] bg-[right_0.5rem_center] bg-no-repeat",
  ],
  {
    variants: {
      size: {
        sm: "h-9 text-xs",
        md: "h-10 text-sm",
        lg: "h-11 text-base",
      },
      error: {
        true: "border-destructive",
        false: "border-input",
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

// Base props shared by both modes
interface BaseSelectProps extends VariantProps<typeof triggerVariants> {
  label?: string;
  placeholder?: string;
  helperText?: string;
  errorText?: string;
  loading?: boolean;
  className?: string;
}

// Radix mode props (options array)
interface RadixSelectProps extends BaseSelectProps, SelectPrimitive.SelectProps {
  options: SelectOption[];
  onChange?: never;
  children?: React.ReactNode;
}

// Native mode props (onChange + children)
interface NativeSelectProps extends BaseSelectProps {
  options?: never;
  value?: string;
  onChange?: React.ChangeEventHandler<HTMLSelectElement>;
  onValueChange?: (value: string) => void;
  children: React.ReactNode;
  disabled?: boolean;
  name?: string;
  required?: boolean;
}

export type SelectProps = RadixSelectProps | NativeSelectProps;

// Type guard to check if using native mode
function isNativeMode(props: SelectProps): props is NativeSelectProps {
  return !('options' in props) || props.options === undefined;
}

// ============================================================================//
// Native Select Component
// ============================================================================//

const NativeSelect = forwardRef<HTMLSelectElement, NativeSelectProps>(
  (
    {
      label,
      placeholder,
      helperText,
      errorText,
      size,
      error,
      loading = false,
      className,
      children,
      onChange,
      onValueChange,
      ...props
    },
    ref
  ) => {
    const hasError = !!errorText || error;

    const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
      if (onChange) {
        onChange(e);
      }
      if (onValueChange) {
        onValueChange(e.target.value);
      }
    };

    return (
      <div className={cn("space-y-1", className)}>
        {label && (
          <label className="text-sm font-medium text-foreground">
            {label}
          </label>
        )}

        <div className="relative">
          {loading && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2">
              <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
            </div>
          )}
          <select
            ref={ref}
            className={cn(
              nativeSelectVariants({ size, error: hasError }),
              loading && "pl-9"
            )}
            onChange={handleChange}
            aria-invalid={hasError || undefined}
            {...props}
          >
            {placeholder && (
              <option value="" disabled>
                {placeholder}
              </option>
            )}
            {children}
          </select>
        </div>

        {helperText && !hasError && (
          <p className="text-xs text-muted-foreground">{helperText}</p>
        )}
        {hasError && (
          <p className="text-xs text-destructive">{errorText}</p>
        )}
      </div>
    );
  }
);

NativeSelect.displayName = "NativeSelect";

// ============================================================================//
// Radix Select Component
// ============================================================================//

const RadixSelect = forwardRef<HTMLButtonElement, RadixSelectProps>(
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
          <label className="text-sm font-medium text-foreground">
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
              {loading && <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />}
              <SelectPrimitive.Value placeholder={placeholder}>
                {children}
              </SelectPrimitive.Value>
            </div>
            <SelectPrimitive.Icon>
              <ChevronDown className="h-4 w-4 text-muted-foreground" aria-hidden />
            </SelectPrimitive.Icon>
          </SelectPrimitive.Trigger>

          <SelectPrimitive.Portal>
            <SelectPrimitive.Content
              className={cn(
                "z-50 overflow-hidden rounded-md border border-border bg-popover shadow-lg",
                "data-[state=open]:animate-in data-[state=closed]:animate-out",
                "data-[state=open]:fade-in data-[state=closed]:fade-out"
              )}
              position="popper"
              sideOffset={6}
            >
              <SelectPrimitive.ScrollUpButton className="flex items-center justify-center py-2 text-muted-foreground">
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
              <SelectPrimitive.ScrollDownButton className="flex items-center justify-center py-2 text-muted-foreground">
                <ChevronDown className="h-4 w-4" />
              </SelectPrimitive.ScrollDownButton>
            </SelectPrimitive.Content>
          </SelectPrimitive.Portal>
        </SelectPrimitive.Root>

        {helperText && !hasError && (
          <p className="text-xs text-muted-foreground">{helperText}</p>
        )}
        {hasError && (
          <p className="text-xs text-destructive">{errorText}</p>
        )}
      </div>
    );
  }
);

RadixSelect.displayName = "RadixSelect";

// ============================================================================//
// Main Select Component (Auto-detects mode)
// ============================================================================//

export const Select = forwardRef<HTMLButtonElement | HTMLSelectElement, SelectProps>(
  (props, ref) => {
    if (isNativeMode(props)) {
      return <NativeSelect ref={ref as React.Ref<HTMLSelectElement>} {...props} />;
    }
    return <RadixSelect ref={ref as React.Ref<HTMLButtonElement>} {...props} />;
  }
) as React.ForwardRefExoticComponent<SelectProps & React.RefAttributes<HTMLButtonElement | HTMLSelectElement>>;

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
        "rounded-md px-3 py-2 text-sm text-popover-foreground",
        "focus:bg-accent focus:text-accent-foreground outline-none",
        "data-[disabled]:pointer-events-none data-[disabled]:opacity-50",
        className
      )}
      {...props}
    >
      <div className="flex flex-col">
        <span>{children}</span>
        {description && (
          <span className="text-xs text-muted-foreground">{description}</span>
        )}
      </div>
      <SelectPrimitive.ItemIndicator>
        <Check className="h-4 w-4 text-primary" aria-hidden />
      </SelectPrimitive.ItemIndicator>
    </SelectPrimitive.Item>
  );
}

SelectItem.displayName = "SelectItem";
