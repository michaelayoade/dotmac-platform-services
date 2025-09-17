/**
 * Admin Portal Button Component
 *
 * High-contrast, compact button optimized for power users and data-dense interfaces.
 * Emphasizes functionality over visual flair with precise interactions.
 */

import {
  Button as PrimitiveButton,
  type ButtonProps as PrimitiveButtonProps,
} from '@dotmac/primitives';
import { cva, type VariantProps } from 'class-variance-authority';
import * as React from 'react';

import { cn } from '../lib/utils';

/**
 * Admin button variants optimized for professional interfaces
 */
const adminButtonVariants = cva(
  'inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-admin-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default: 'bg-admin-primary text-admin-primary-foreground hover:bg-admin-primary/90',
        destructive:
          'bg-admin-destructive text-admin-destructive-foreground hover:bg-admin-destructive/90',
        outline:
          'border border-admin-border bg-admin-background hover:bg-admin-accent hover:text-admin-accent-foreground',
        secondary: 'bg-admin-secondary text-admin-secondary-foreground hover:bg-admin-secondary/80',
        ghost: 'hover:bg-admin-accent hover:text-admin-accent-foreground',
        link: 'text-admin-primary underline-offset-4 hover:underline',
      },
      size: {
        default: 'h-8 px-3 py-1.5',
        sm: 'h-7 rounded-md px-2 text-xs',
        lg: 'h-9 rounded-md px-6',
        icon: 'h-8 w-8',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);

/**
 * Admin Button component props
 */
export interface AdminButtonProps
  extends Omit<PrimitiveButtonProps, 'variant' | 'size'>,
    VariantProps<typeof adminButtonVariants> {
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
   * Tooltip text for icon-only buttons
   */
  tooltip?: string;
  /**
   * Render as child component (using Slot)
   */
  asChild?: boolean;
}

/**
 * Admin Portal Button Component
 *
 * Compact, high-contrast button designed for power users. Optimized for dense
 * interfaces with precise click targets and clear visual hierarchy.
 *
 * @example
 * ```tsx
 * // Primary action button
 * <AdminButton variant="default" size="default">
 *   Save Changes
 * </AdminButton>
 *
 * // Destructive action with confirmation
 * <AdminButton variant="destructive" leftIcon={<TrashIcon />}>
 *   Delete Customer
 * </AdminButton>
 *
 * // Icon-only button
 * <AdminButton variant="ghost" size="icon" tooltip="Edit">
 *   <EditIcon />
 * </AdminButton>
 *
 * // Loading state
 * <AdminButton loading disabled>
 *   Processing...
 * </AdminButton>
 * ```
 */
const AdminButton = React.forwardRef<HTMLButtonElement, AdminButtonProps>(
  (
    {
      className,
      variant,
      size,
      loading = false,
      leftIcon,
      rightIcon,
      tooltip,
      children,
      disabled,
      asChild = false,
      ...props
    },
    ref
  ) => {
    const isDisabled = disabled || loading;

    // When asChild is true, pass through children directly for Slot
    // Note: loading, leftIcon, rightIcon are not supported with asChild
    if (asChild) {
      return (
        <PrimitiveButton
          className={cn(adminButtonVariants({ variant, size }), className)}
          ref={ref}
          disabled={disabled} // Don't modify disabled state for asChild
          title={tooltip}
          asChild={asChild}
          {...props}
        >
          {children}
        </PrimitiveButton>
      );
    }

    return (
      <PrimitiveButton
        className={cn(adminButtonVariants({ variant, size }), className)}
        ref={ref}
        disabled={isDisabled}
        title={tooltip}
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

AdminButton.displayName = 'AdminButton';

export { AdminButton, adminButtonVariants };
export type { AdminButtonProps };
