/**
 * Button Primitive
 *
 * Unstyled, accessible button component with variant support
 */

"use client";

import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { forwardRef, type ButtonHTMLAttributes } from "react";

import { cn } from "../utils/cn";

// ============================================================================
// Button Variants
// ============================================================================

export const buttonVariants = cva(
  // Base styles
  [
    "inline-flex items-center justify-center",
    "font-medium text-sm",
    "transition-colors duration-200",
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-surface",
    "disabled:pointer-events-none disabled:opacity-50",
    "whitespace-nowrap",
  ],
  {
    variants: {
      variant: {
        default: "",
        primary: "",
        secondary: "",
        destructive: "",
        outline: "",
        ghost: "",
        link: "underline-offset-4 hover:underline",
      },
      size: {
        xs: "h-7 px-2 text-xs rounded",
        sm: "h-8 px-3 text-xs rounded-md",
        md: "h-10 px-4 text-sm rounded-md",
        lg: "h-11 px-6 text-base rounded-md",
        xl: "h-12 px-8 text-base rounded-lg",
        icon: "h-10 w-10 rounded-md",
        "icon-sm": "h-8 w-8 rounded-md",
        "icon-lg": "h-12 w-12 rounded-lg",
        // Density-aware sizes (use CSS variables from theme)
        "density-sm": "h-[var(--height-button,2rem)] px-3 text-xs rounded-md",
        "density-md": "h-[var(--height-button,2.5rem)] px-4 text-sm rounded-md",
        "density-lg": "h-[var(--height-button,2.75rem)] px-6 text-base rounded-md",
      },
      fullWidth: {
        true: "w-full",
      },
      density: {
        compact: "",
        comfortable: "",
        spacious: "",
      },
    },
    compoundVariants: [
      // Compact density reduces sizes
      { density: "compact", size: "xs", className: "h-6 px-1.5 text-xs" },
      { density: "compact", size: "sm", className: "h-7 px-2 text-xs" },
      { density: "compact", size: "md", className: "h-8 px-3 text-sm" },
      { density: "compact", size: "lg", className: "h-9 px-4 text-sm" },
      { density: "compact", size: "xl", className: "h-10 px-6 text-base" },
      { density: "compact", size: "icon", className: "h-8 w-8" },
      { density: "compact", size: "icon-sm", className: "h-6 w-6" },
      { density: "compact", size: "icon-lg", className: "h-10 w-10" },
      // Spacious density increases sizes
      { density: "spacious", size: "xs", className: "h-8 px-3 text-xs" },
      { density: "spacious", size: "sm", className: "h-9 px-4 text-sm" },
      { density: "spacious", size: "md", className: "h-12 px-5 text-sm" },
      { density: "spacious", size: "lg", className: "h-14 px-8 text-base" },
      { density: "spacious", size: "xl", className: "h-16 px-10 text-lg" },
      { density: "spacious", size: "icon", className: "h-12 w-12" },
      { density: "spacious", size: "icon-sm", className: "h-10 w-10" },
      { density: "spacious", size: "icon-lg", className: "h-14 w-14" },
    ],
    defaultVariants: {
      variant: "default",
      size: "md",
    },
  }
);

// ============================================================================
// Button Props
// ============================================================================

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  /**
   * Render as a different element using Radix Slot
   */
  asChild?: boolean;
  /**
   * Show loading state
   */
  loading?: boolean;
  /**
   * Icon to show before children
   */
  leftIcon?: React.ReactNode;
  /**
   * Icon to show after children
   */
  rightIcon?: React.ReactNode;
  /**
   * Density mode for spacing adjustments
   * - compact: Reduced padding and height
   * - comfortable: Default spacing (default)
   * - spacious: Increased padding and height
   */
  density?: "compact" | "comfortable" | "spacious";
}

// ============================================================================
// Button Component
// ============================================================================

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant,
      size,
      fullWidth,
      density,
      asChild = false,
      loading = false,
      leftIcon,
      rightIcon,
      disabled,
      children,
      ...props
    },
    ref
  ) => {
    const Comp = asChild ? Slot : "button";
    const isDisabled = disabled || loading;

    return (
      <Comp
        ref={ref}
        className={cn(buttonVariants({ variant, size, fullWidth, density }), className)}
        disabled={isDisabled}
        aria-busy={loading}
        {...props}
      >
        {loading ? (
          <>
            <LoadingSpinner className="mr-2" />
            {children}
          </>
        ) : (
          <>
            {leftIcon && <span className="mr-2 -ml-1">{leftIcon}</span>}
            {children}
            {rightIcon && <span className="ml-2 -mr-1">{rightIcon}</span>}
          </>
        )}
      </Comp>
    );
  }
);

Button.displayName = "Button";

// ============================================================================
// Loading Spinner
// ============================================================================

function LoadingSpinner({ className }: { className?: string }) {
  return (
    <svg
      className={cn("h-4 w-4 animate-spin", className)}
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  );
}

// ============================================================================
// Button Group
// ============================================================================

export interface ButtonGroupProps {
  children: React.ReactNode;
  className?: string;
  orientation?: "horizontal" | "vertical";
  attached?: boolean;
}

export function ButtonGroup({
  children,
  className,
  orientation = "horizontal",
  attached = false,
}: ButtonGroupProps) {
  return (
    <div
      className={cn(
        "inline-flex",
        orientation === "vertical" ? "flex-col" : "flex-row",
        attached && orientation === "horizontal" && "[&>*:not(:first-child)]:-ml-px [&>*:first-child]:rounded-r-none [&>*:last-child]:rounded-l-none [&>*:not(:first-child):not(:last-child)]:rounded-none",
        attached && orientation === "vertical" && "[&>*:not(:first-child)]:-mt-px [&>*:first-child]:rounded-b-none [&>*:last-child]:rounded-t-none [&>*:not(:first-child):not(:last-child)]:rounded-none",
        !attached && "gap-2",
        className
      )}
      role="group"
    >
      {children}
    </div>
  );
}

export default Button;
