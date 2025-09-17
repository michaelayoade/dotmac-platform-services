/**
 * Reseller Portal Button Component
 *
 * Professional, brandable button optimized for partner interfaces.
 * Balances functionality with customization options for white-label use.
 */

import {
  Button as PrimitiveButton,
  type ButtonProps as PrimitiveButtonProps,
} from '@dotmac/primitives';
import { cva, type VariantProps } from 'class-variance-authority';
import * as React from 'react';

import { cn } from '../lib/utils';

/**
 * Reseller button variants optimized for professional partner interfaces
 */
const resellerButtonVariants = cva(
  'inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-reseller-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 duration-150',
  {
    variants: {
      variant: {
        default:
          'bg-reseller-primary text-reseller-primary-foreground hover:bg-reseller-primary/90 shadow-sm',
        destructive:
          'bg-reseller-destructive text-reseller-destructive-foreground hover:bg-reseller-destructive/90',
        outline:
          'border border-reseller-border bg-reseller-background hover:bg-reseller-accent hover:text-reseller-accent-foreground',
        secondary:
          'bg-reseller-secondary text-reseller-secondary-foreground hover:bg-reseller-secondary/80',
        ghost: 'hover:bg-reseller-accent hover:text-reseller-accent-foreground',
        link: 'text-reseller-primary underline-offset-4 hover:underline',
        brand:
          'bg-gradient-to-r from-reseller-primary to-reseller-accent text-reseller-primary-foreground hover:from-reseller-primary/90 hover:to-reseller-accent/90 shadow-md',
      },
      size: {
        default: 'h-9 px-4 py-2',
        sm: 'h-8 rounded-md px-3 text-xs',
        lg: 'h-11 rounded-md px-8 text-base',
        icon: 'h-9 w-9',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);

/**
 * Reseller Button component props
 */
export interface ResellerButtonProps
  extends Omit<PrimitiveButtonProps, 'variant' | 'size'>,
    VariantProps<typeof resellerButtonVariants> {
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
   * Whether to show a subtle glow effect for brand buttons
   */
  glow?: boolean;
  /**
   * Render as child component (using Slot)
   */
  asChild?: boolean;
}

/**
 * Reseller Portal Button Component
 *
 * Professional button designed for partner/reseller interfaces. Offers brand
 * customization options while maintaining a polished, business-appropriate appearance.
 *
 * @example
 * ```tsx
 * // Brand-focused primary button
 * <ResellerButton variant="brand" size="lg" glow>
 *   Launch Campaign
 * </ResellerButton>
 *
 * // Professional action with icon
 * <ResellerButton variant="default" leftIcon={<UsersIcon />}>
 *   Manage Customers
 * </ResellerButton>
 *
 * // Subtle secondary action
 * <ResellerButton variant="outline" size="sm">
 *   View Details
 * </ResellerButton>
 *
 * // Loading state for async operations
 * <ResellerButton variant="brand" loading disabled>
 *   Creating Account...
 * </ResellerButton>
 * ```
 */
const ResellerButton = React.forwardRef<HTMLButtonElement, ResellerButtonProps>(
  (
    {
      className,
      variant,
      size,
      loading = false,
      leftIcon,
      rightIcon,
      glow = false,
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
            resellerButtonVariants({ variant, size }),
            {
              'shadow-lg shadow-reseller-primary/25': glow && variant === 'brand',
              'hover:shadow-reseller-primary/30 hover:shadow-xl':
                glow && variant === 'brand' && !isDisabled,
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
          resellerButtonVariants({ variant, size }),
          {
            'shadow-lg shadow-reseller-primary/25': glow && variant === 'brand',
            'hover:shadow-reseller-primary/30 hover:shadow-xl':
              glow && variant === 'brand' && !isDisabled,
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

ResellerButton.displayName = 'ResellerButton';

export { ResellerButton, resellerButtonVariants };
export type { ResellerButtonProps };
