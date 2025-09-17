/**
 * Admin Portal Input Component
 *
 * Compact, precise input controls optimized for data entry in admin interfaces.
 * Emphasizes functionality and quick data manipulation.
 */

import {
  Input as PrimitiveInput,
  type InputProps as PrimitiveInputProps,
} from '@dotmac/primitives';
import { cva, type VariantProps } from 'class-variance-authority';
import * as React from 'react';

import { cn } from '../lib/utils';

/**
 * Admin input variants for different use cases
 */
const adminInputVariants = cva(
  'flex h-8 w-full rounded-md border border-admin-border bg-admin-background px-2 py-1 text-sm ring-offset-admin-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-admin-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-admin-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 transition-colors',
  {
    variants: {
      variant: {
        default: '',
        filled: 'bg-admin-muted/30 border-transparent',
        underlined:
          'border-0 border-b-2 border-admin-border bg-transparent rounded-none px-0 focus-visible:ring-0 focus-visible:border-admin-primary',
      },
      state: {
        default: '',
        error: 'border-admin-destructive focus-visible:ring-admin-destructive',
        success: 'border-success focus-visible:ring-success',
        warning: 'border-warning focus-visible:ring-warning',
      },
      size: {
        sm: 'h-7 px-2 text-xs',
        default: 'h-8 px-2 text-sm',
        lg: 'h-9 px-3 text-sm',
      },
    },
    defaultVariants: {
      variant: 'default',
      state: 'default',
      size: 'default',
    },
  }
);

/**
 * Admin Input component props
 */
export interface AdminInputProps
  extends Omit<PrimitiveInputProps, 'variant' | 'size' | 'state'>,
    VariantProps<typeof adminInputVariants> {
  /**
   * Icon to display at the start of the input
   */
  leftIcon?: React.ReactNode;
  /**
   * Icon to display at the end of the input
   */
  rightIcon?: React.ReactNode;
  /**
   * Label text for the input
   */
  label?: string;
  /**
   * Helper text or error message
   */
  helperText?: string;
  /**
   * Whether the field is required
   */
  required?: boolean;
}

/**
 * Admin Portal Input Component
 *
 * Compact input component optimized for admin interfaces. Designed for
 * efficient data entry with clear validation states and minimal visual overhead.
 *
 * @example
 * ```tsx
 * // Basic input
 * <AdminInput
 *   placeholder="Search customers..."
 *   leftIcon={<SearchIcon />}
 * />
 *
 * // Input with label and validation
 * <AdminInput
 *   label="Customer Email"
 *   type="email"
 *   state="error"
 *   helperText="Please enter a valid email address"
 *   required
 * />
 *
 * // Compact filled input
 * <AdminInput
 *   variant="filled"
 *   size="sm"
 *   placeholder="Quick filter..."
 * />
 *
 * // Underlined input for inline editing
 * <AdminInput
 *   variant="underlined"
 *   defaultValue="Customer Name"
 * />
 * ```
 */
const AdminInput = React.forwardRef<HTMLInputElement, AdminInputProps>(
  (
    {
      className,
      variant,
      state,
      size,
      leftIcon,
      rightIcon,
      label,
      helperText,
      required,
      id,
      ...props
    },
    ref
  ) => {
    const inputId = id || React.useId();
    const helperTextId = `${inputId}-helper`;

    const inputElement = (
      <div className='relative'>
        {leftIcon && (
          <div className='-translate-y-1/2 absolute top-1/2 left-2 h-4 w-4 text-admin-muted-foreground'>
            {leftIcon}
          </div>
        )}

        <PrimitiveInput
          id={inputId}
          ref={ref}
          className={cn(
            adminInputVariants({ variant, state, size }),
            {
              'pl-8': leftIcon && variant !== 'underlined',
              'pr-8': rightIcon && variant !== 'underlined',
            },
            className
          )}
          aria-describedby={helperText ? helperTextId : undefined}
          aria-invalid={state === 'error'}
          aria-required={required}
          {...props}
        />

        {rightIcon && (
          <div className='-translate-y-1/2 absolute top-1/2 right-2 h-4 w-4 text-admin-muted-foreground'>
            {rightIcon}
          </div>
        )}
      </div>
    );

    if (label || helperText) {
      return (
        <div className='space-y-1'>
          {label && (
            <label htmlFor={inputId} className='font-medium text-admin-foreground text-xs'>
              {label}
              {required && <span className='ml-1 text-admin-destructive'>*</span>}
            </label>
          )}

          {inputElement}

          {helperText && (
            <p
              id={helperTextId}
              className={cn('text-xs', {
                'text-admin-muted-foreground': state === 'default',
                'text-admin-destructive': state === 'error',
                'text-success': state === 'success',
                'text-warning': state === 'warning',
              })}
            >
              {helperText}
            </p>
          )}
        </div>
      );
    }

    return inputElement;
  }
);

AdminInput.displayName = 'AdminInput';

export { AdminInput, adminInputVariants };
export type { AdminInputProps };
