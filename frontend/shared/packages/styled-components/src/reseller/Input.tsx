/**
 * Reseller Portal Input Component
 *
 * Professional input controls optimized for partner/reseller interfaces.
 * Balances functionality with business-appropriate styling.
 */

import {
  Input as PrimitiveInput,
  type InputProps as PrimitiveInputProps,
} from '@dotmac/primitives';
import { cva, type VariantProps } from 'class-variance-authority';
import * as React from 'react';

import { cn } from '../lib/utils';

/**
 * Reseller input variants for different use cases
 */
const resellerInputVariants = cva(
  'flex h-9 w-full rounded-md border border-reseller-border bg-reseller-background px-3 py-2 text-sm ring-offset-reseller-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-reseller-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-reseller-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 transition-colors',
  {
    variants: {
      variant: {
        default: 'shadow-sm',
        filled: 'bg-reseller-muted/20 border-transparent',
        underlined:
          'border-0 border-b-2 border-reseller-border bg-transparent rounded-none px-0 focus-visible:ring-0 focus-visible:border-reseller-primary',
        branded: 'border-reseller-primary/30 focus-visible:ring-reseller-primary/30',
      },
      state: {
        default: '',
        error: 'border-reseller-destructive focus-visible:ring-reseller-destructive',
        success: 'border-success focus-visible:ring-success',
        warning: 'border-warning focus-visible:ring-warning',
      },
      size: {
        sm: 'h-8 px-2 text-xs',
        default: 'h-9 px-3 text-sm',
        lg: 'h-10 px-4 text-sm',
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
 * Reseller Input component props
 */
export interface ResellerInputProps
  extends Omit<PrimitiveInputProps, 'variant' | 'size' | 'state'>,
    VariantProps<typeof resellerInputVariants> {
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
   * Business category for enhanced styling
   */
  category?: 'financial' | 'customer' | 'technical' | 'marketing';
}

/**
 * Reseller Portal Input Component
 *
 * Professional input component optimized for partner interfaces. Features
 * business-appropriate styling with optional category-based enhancements.
 *
 * @example
 * ```tsx
 * // Basic professional input
 * <ResellerInput
 *   label="Company Name"
 *   placeholder="Enter your company name"
 *   required
 * />
 *
 * // Financial category input with validation
 * <ResellerInput
 *   label="Commission Rate"
 *   type="number"
 *   category="financial"
 *   state="success"
 *   helperText="Commission rate updated successfully"
 *   rightIcon={<CheckIcon />}
 * />
 *
 * // Branded input for partner identification
 * <ResellerInput
 *   variant="branded"
 *   placeholder="Partner ID or Company Code..."
 *   leftIcon={<BuildingIcon />}
 * />
 *
 * // Technical category with filled style
 * <ResellerInput
 *   variant="filled"
 *   category="technical"
 *   label="API Endpoint"
 *   placeholder="https://api.example.com"
 * />
 * ```
 */
const ResellerInput = React.forwardRef<HTMLInputElement, ResellerInputProps>(
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
      category,
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
          <div
            className={cn('-translate-y-1/2 absolute top-1/2 left-2.5 h-4 w-4', {
              'text-reseller-muted-foreground': !category,
              'text-success': category === 'financial',
              'text-reseller-primary': category === 'customer',
              'text-info': category === 'technical',
              'text-reseller-accent': category === 'marketing',
            })}
          >
            {leftIcon}
          </div>
        )}

        <PrimitiveInput
          id={inputId}
          ref={ref}
          className={cn(
            resellerInputVariants({ variant, state, size }),
            {
              'pl-9': leftIcon && variant !== 'underlined',
              'pr-9': rightIcon && variant !== 'underlined',
              // Category-specific styling
              'border-success/30 focus-visible:ring-success/20':
                category === 'financial' && state === 'default',
              'border-reseller-primary/30 focus-visible:ring-reseller-primary/20':
                category === 'customer' && state === 'default',
              'border-info/30 focus-visible:ring-info/20':
                category === 'technical' && state === 'default',
              'border-reseller-accent/30 focus-visible:ring-reseller-accent/20':
                category === 'marketing' && state === 'default',
            },
            className
          )}
          aria-describedby={helperText ? helperTextId : undefined}
          aria-invalid={state === 'error'}
          aria-required={required}
          {...props}
        />

        {rightIcon && (
          <div
            className={cn('-translate-y-1/2 absolute top-1/2 right-2.5 h-4 w-4', {
              'text-reseller-muted-foreground': !category,
              'text-success': category === 'financial',
              'text-reseller-primary': category === 'customer',
              'text-info': category === 'technical',
              'text-reseller-accent': category === 'marketing',
            })}
          >
            {rightIcon}
          </div>
        )}
      </div>
    );

    if (label || helperText) {
      return (
        <div className='space-y-1.5'>
          {label && (
            <label
              htmlFor={inputId}
              className={cn('font-medium text-reseller-foreground text-sm', {
                'text-success': category === 'financial',
                'text-reseller-primary': category === 'customer',
                'text-info': category === 'technical',
                'text-reseller-accent': category === 'marketing',
              })}
            >
              {label}
              {required && <span className='ml-1 text-reseller-destructive'>*</span>}
            </label>
          )}

          {inputElement}

          {helperText && (
            <p
              id={helperTextId}
              className={cn('text-xs', {
                'text-reseller-muted-foreground': state === 'default',
                'text-reseller-destructive': state === 'error',
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

ResellerInput.displayName = 'ResellerInput';

export { ResellerInput, resellerInputVariants };
export type { ResellerInputProps };
