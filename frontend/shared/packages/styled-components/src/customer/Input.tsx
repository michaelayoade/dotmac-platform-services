/**
 * Customer Portal Input Component
 *
 * User-friendly input controls optimized for customer interfaces.
 * Emphasizes clarity, accessibility, and ease of use.
 */

import {
  Input as PrimitiveInput,
  type InputProps as PrimitiveInputProps,
} from '@dotmac/primitives';
import { cva, type VariantProps } from 'class-variance-authority';
import * as React from 'react';

import { cn } from '../lib/utils';

/**
 * Customer input variants for different use cases
 */
const customerInputVariants = cva(
  'flex w-full rounded-lg border border-customer-border bg-customer-background px-4 py-3 text-sm ring-offset-customer-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-customer-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-customer-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 transition-all duration-200',
  {
    variants: {
      variant: {
        default: 'shadow-sm hover:border-customer-border/80',
        filled: 'bg-customer-muted/20 border-transparent hover:bg-customer-muted/30',
        underlined:
          'border-0 border-b-2 border-customer-border bg-transparent rounded-none px-0 pb-2 focus-visible:ring-0 focus-visible:border-customer-primary',
      },
      state: {
        default: '',
        error:
          'border-customer-destructive focus-visible:ring-customer-destructive bg-customer-destructive/5',
        success: 'border-success focus-visible:ring-success bg-success/5',
        warning: 'border-warning focus-visible:ring-warning bg-warning/5',
      },
      size: {
        sm: 'h-9 px-3 py-2 text-sm',
        default: 'h-11 px-4 py-3 text-sm',
        lg: 'h-12 px-4 py-3 text-base',
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
 * Customer Input component props
 */
export interface CustomerInputProps
  extends Omit<PrimitiveInputProps, 'variant' | 'size' | 'state'>,
    VariantProps<typeof customerInputVariants> {
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
  /**
   * Full width input
   */
  fullWidth?: boolean;
}

/**
 * Customer Portal Input Component
 *
 * Friendly input component optimized for customer interfaces. Features
 * comfortable spacing, clear validation states, and helpful guidance text.
 *
 * @example
 * ```tsx
 * // Basic input with label
 * <CustomerInput
 *   label="Email Address"
 *   type="email"
 *   placeholder="Enter your email"
 *   required
 *   fullWidth
 * />
 *
 * // Input with validation state
 * <CustomerInput
 *   label="Account Number"
 *   state="error"
 *   helperText="Please check your account number and try again"
 *   leftIcon={<AccountIcon />}
 * />
 *
 * // Comfortable filled input
 * <CustomerInput
 *   variant="filled"
 *   placeholder="Search your bills..."
 *   leftIcon={<SearchIcon />}
 * />
 *
 * // Success state with confirmation
 * <CustomerInput
 *   label="Phone Number"
 *   state="success"
 *   helperText="Phone number verified successfully"
 *   rightIcon={<CheckIcon />}
 * />
 * ```
 */
const CustomerInput = React.forwardRef<HTMLInputElement, CustomerInputProps>(
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
      fullWidth = false,
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
          <div className='-translate-y-1/2 absolute top-1/2 left-3 h-5 w-5 text-customer-muted-foreground'>
            {leftIcon}
          </div>
        )}

        <PrimitiveInput
          id={inputId}
          ref={ref}
          className={cn(
            customerInputVariants({ variant, state, size }),
            {
              'pl-10': leftIcon && variant !== 'underlined',
              'pr-10': rightIcon && variant !== 'underlined',
              'w-full': fullWidth,
            },
            className
          )}
          aria-describedby={helperText ? helperTextId : undefined}
          aria-invalid={state === 'error'}
          aria-required={required}
          {...props}
        />

        {rightIcon && (
          <div className='-translate-y-1/2 absolute top-1/2 right-3 h-5 w-5 text-customer-muted-foreground'>
            {rightIcon}
          </div>
        )}
      </div>
    );

    if (label || helperText) {
      return (
        <div className={cn('space-y-2', { 'w-full': fullWidth })}>
          {label && (
            <label
              htmlFor={inputId}
              className='font-medium text-customer-foreground text-sm leading-relaxed'
            >
              {label}
              {required && <span className='ml-1 text-customer-destructive'>*</span>}
            </label>
          )}

          {inputElement}

          {helperText && (
            <p
              id={helperTextId}
              className={cn('text-sm leading-relaxed', {
                'text-customer-muted-foreground': state === 'default',
                'text-customer-destructive': state === 'error',
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

CustomerInput.displayName = 'CustomerInput';

export { CustomerInput, customerInputVariants };
export type { CustomerInputProps };
