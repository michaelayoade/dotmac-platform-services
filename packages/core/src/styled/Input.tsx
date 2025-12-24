/**
 * Styled Input
 *
 * Pre-styled input component with DotMac design system
 */

"use client";

import { forwardRef } from "react";

import { Input as InputPrimitive, inputVariants, type InputProps } from "../primitives/Input";
import { cn } from "../utils/cn";

// ============================================================================
// Styled Variant Classes
// ============================================================================

const styledVariantClasses = {
  default:
    "border-input bg-background focus-visible:ring-ring",
  filled:
    "border-transparent bg-muted focus-visible:ring-ring",
  flushed:
    "border-b-input bg-transparent focus-visible:ring-0 focus-visible:border-b-primary",
};

// ============================================================================
// Styled Input Component
// ============================================================================

export const StyledInput = forwardRef<HTMLInputElement, InputProps>(
  ({ className, variant = "default", ...props }, ref) => {
    return (
      <InputPrimitive
        ref={ref}
        variant={variant}
        className={cn(
          styledVariantClasses[variant || "default"],
          className
        )}
        {...props}
      />
    );
  }
);

StyledInput.displayName = "StyledInput";

// ============================================================================
// Search Input
// ============================================================================

export interface SearchInputProps extends Omit<InputProps, "type" | "leftAddon"> {
  onSearch?: (value: string) => void;
  onClear?: () => void;
}

export const SearchInput = forwardRef<HTMLInputElement, SearchInputProps>(
  ({ className, onSearch, onClear, ...props }, ref) => {
    return (
      <StyledInput
        ref={ref}
        type="search"
        leftAddon={
          <svg
            className="h-4 w-4"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        }
        className={cn("pl-10", className)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && onSearch) {
            onSearch((e.target as HTMLInputElement).value);
          }
        }}
        {...props}
      />
    );
  }
);

SearchInput.displayName = "SearchInput";

// ============================================================================
// Password Input
// ============================================================================

import { useState } from "react";

export interface PasswordInputProps extends Omit<InputProps, "type" | "rightAddon"> {
  showToggle?: boolean;
}

export const PasswordInput = forwardRef<HTMLInputElement, PasswordInputProps>(
  ({ className, showToggle = true, ...props }, ref) => {
    const [showPassword, setShowPassword] = useState(false);

    return (
      <StyledInput
        ref={ref}
        type={showPassword ? "text" : "password"}
        rightAddon={
          showToggle ? (
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="focus:outline-none"
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? (
                <svg
                  className="h-4 w-4"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"
                  />
                </svg>
              ) : (
                <svg
                  className="h-4 w-4"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                  />
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                  />
                </svg>
              )}
            </button>
          ) : undefined
        }
        className={cn(showToggle && "pr-10", className)}
        {...props}
      />
    );
  }
);

PasswordInput.displayName = "PasswordInput";

export { inputVariants };
export type { InputProps };
export default StyledInput;
