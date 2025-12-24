/**
 * Input Primitive
 *
 * Accessible text input with support for various types and states
 */

"use client";

import { cva, type VariantProps } from "class-variance-authority";
import { forwardRef, type InputHTMLAttributes, type ReactNode } from "react";

import { cn } from "../utils/cn";

// ============================================================================
// Input Variants
// ============================================================================

export const inputVariants = cva(
  // Base styles
  [
    "flex w-full rounded-md border bg-transparent",
    "text-sm placeholder:text-muted-foreground",
    "transition-colors duration-200",
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-0",
    "disabled:cursor-not-allowed disabled:opacity-50",
    "file:border-0 file:bg-transparent file:text-sm file:font-medium",
  ],
  {
    variants: {
      size: {
        sm: "h-8 px-2 text-xs",
        md: "h-10 px-3 text-sm",
        lg: "h-12 px-4 text-base",
      },
      variant: {
        default: "",
        filled: "bg-muted/50",
        flushed: "border-0 border-b rounded-none px-0",
      },
      hasError: {
        true: "border-destructive focus-visible:ring-destructive",
      },
    },
    defaultVariants: {
      size: "md",
      variant: "default",
    },
  }
);

// ============================================================================
// Input Props
// ============================================================================

export interface InputProps
  extends Omit<InputHTMLAttributes<HTMLInputElement>, "size">,
    VariantProps<typeof inputVariants> {
  /**
   * Error message or error state
   */
  error?: string | boolean;
  /**
   * Helper text below input
   */
  helperText?: string;
  /**
   * Left addon/icon
   */
  leftAddon?: ReactNode;
  /**
   * Right addon/icon
   */
  rightAddon?: ReactNode;
  /**
   * Container class name
   */
  containerClassName?: string;
}

// ============================================================================
// Input Component
// ============================================================================

export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      className,
      containerClassName,
      size,
      variant,
      type = "text",
      error,
      helperText,
      leftAddon,
      rightAddon,
      disabled,
      ...props
    },
    ref
  ) => {
    const hasError = Boolean(error);
    const errorMessage = typeof error === "string" ? error : undefined;

    return (
      <div className={cn("relative", containerClassName)}>
        {/* Input wrapper for addons */}
        <div className="relative">
          {leftAddon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
              {leftAddon}
            </div>
          )}
          <input
            ref={ref}
            type={type}
            className={cn(
              inputVariants({ size, variant, hasError }),
              leftAddon && "pl-10",
              rightAddon && "pr-10",
              className
            )}
            disabled={disabled}
            aria-invalid={hasError}
            aria-describedby={
              errorMessage ? `${props.id}-error` : helperText ? `${props.id}-helper` : undefined
            }
            {...props}
          />
          {rightAddon && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground">
              {rightAddon}
            </div>
          )}
        </div>

        {/* Helper text or error message */}
        {(errorMessage || helperText) && (
          <p
            id={errorMessage ? `${props.id}-error` : `${props.id}-helper`}
            className={cn(
              "mt-1 text-xs",
              hasError ? "text-destructive" : "text-muted-foreground"
            )}
          >
            {errorMessage || helperText}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";

// ============================================================================
// Input Group (for combining inputs with buttons/addons)
// ============================================================================

export interface InputGroupProps {
  children: ReactNode;
  className?: string;
}

export function InputGroup({ children, className }: InputGroupProps) {
  return (
    <div
      className={cn(
        "flex",
        "[&>input]:rounded-none [&>input:first-child]:rounded-l-md [&>input:last-child]:rounded-r-md",
        "[&>button]:rounded-none [&>button:first-child]:rounded-l-md [&>button:last-child]:rounded-r-md",
        "[&>*:not(:first-child)]:-ml-px",
        className
      )}
    >
      {children}
    </div>
  );
}

export default Input;
