/**
 * Customer Portal Button Component
 *
 * Friendly, accessible button optimized for end-users. Emphasizes clarity
 * and ease of use with generous spacing and clear visual feedback.
 */

import {
  Button as PrimitiveButton,
  type ButtonProps as PrimitiveButtonProps,
} from '@dotmac/primitives';
import { cva, type VariantProps } from 'class-variance-authority';
import * as React from 'react';

import { cn } from '../lib/utils';

/**
 * Customer button variants optimized for accessibility and friendliness
 */
const customerButtonVariants = cva(
  'inline-flex items-center justify-center whitespace-nowrap rounded-lg text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-customer-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 duration-200',
  {
    variants: {
      variant: {
        default:
          'bg-customer-primary text-customer-primary-foreground hover:bg-customer-primary/90 shadow-sm hover:shadow-md',
        destructive:
          'bg-customer-destructive text-customer-destructive-foreground hover:bg-customer-destructive/90 shadow-sm',
        outline:
          'border border-customer-border bg-customer-background hover:bg-customer-accent hover:text-customer-accent-foreground shadow-sm',
        secondary:
          'bg-customer-secondary text-customer-secondary-foreground hover:bg-customer-secondary/80 shadow-sm',
        ghost: 'hover:bg-customer-accent hover:text-customer-accent-foreground',
        link: 'text-customer-primary underline-offset-4 hover:underline',
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-8 rounded-md px-3 text-xs',
        lg: 'h-12 rounded-lg px-8 text-base',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);

/**
 * Customer Button component props
 */
export interface CustomerButtonProps
  extends Omit<PrimitiveButtonProps, 'variant' | 'size'>,
    VariantProps<typeof customerButtonVariants> {
  /**
   * Loading state - shows spinner and disables interaction
   */
  loading?: boolean;
  /**
   * Icon to display before the button text
   */
  leftIcon?: React.ReactNode;
  /**
   * Icon to display after the button text
   */
  rightIcon?: React.ReactNode;
  /**
   * Full width button
   */
  fullWidth?: boolean;
  /**
   * Render as child component (using Slot)
   */
  asChild?: boolean;
}

/**
 * Customer Portal Button Component
 *
 * User-friendly button designed for customer interfaces. Features generous
 * spacing, clear visual feedback, and smooth animations for an approachable feel.
 *
 * @example
 * ```tsx
 * // Primary action button
 * <CustomerButton variant="default" size="lg" fullWidth>
 *   Pay My Bill
 * </CustomerButton>
 *
 * // Secondary action with icon
 * <CustomerButton variant="outline" leftIcon={<DownloadIcon />}>
 *   Download Invoice
 * </CustomerButton>
 *
 * // Loading state
 * <CustomerButton loading disabled>
 *   Processing Payment...
 * </CustomerButton>
 *
 * // Friendly destructive action
 * <CustomerButton variant="destructive" size="sm">
 *   Cancel Subscription
 * </CustomerButton>
 * ```
 */
const CustomerButton = React.forwardRef<HTMLButtonElement, CustomerButtonProps>(
  (
    {
      className,
      variant,
      size,
      loading = false,
      leftIcon,
      rightIcon,
      fullWidth = false,
      children,
      disabled,
      asChild = false,
      ...props
    },
    ref
  ) => {
    const isDisabled = disabled || loading;

    // When asChild is true, pass through children directly for Slot
    if (asChild) {
      return (
        <PrimitiveButton
          className={cn(
            customerButtonVariants({ variant, size }),
            {
              'w-full': fullWidth,
            },
            className
          )}
          ref={ref}
          disabled={isDisabled}
          asChild={asChild}
          {...props}
        >
          {children}
        </PrimitiveButton>
      );
    }

    return (
      <PrimitiveButton
        className={cn(
          customerButtonVariants({ variant, size }),
          {
            'w-full': fullWidth,
          },
          className
        )}
        ref={ref}
        disabled={isDisabled}
        asChild={asChild}
        {...props}
      >
        {loading && (
          <svg
            className='mr-2 h-4 w-4 animate-spin'
            xmlns='http://www.w3.org/2000/svg'
            fill='none'
            viewBox='0 0 24 24'
            aria-label='Loading'
            data-testid='loading-spinner'
          >
            <title>Icon</title>
            <circle
              className='opacity-25'
              cx='12'
              cy='12'
              r='10'
              stroke='currentColor'
              strokeWidth='4'
            />
            <path
              className='opacity-75'
              fill='currentColor'
              d='M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z'
            />
          </svg>
        )}

        {!loading && leftIcon && <span className='mr-2 h-4 w-4 flex-shrink-0'>{leftIcon}</span>}

        {children}

        {!loading && rightIcon && <span className='ml-2 h-4 w-4 flex-shrink-0'>{rightIcon}</span>}
      </PrimitiveButton>
    );
  }
);

CustomerButton.displayName = 'CustomerButton';

export { CustomerButton, customerButtonVariants };
export type { CustomerButtonProps };
