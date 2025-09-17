/**
 * Admin Portal Card Component
 *
 * Dense, minimal card design for displaying data and controls in admin interfaces.
 * Optimized for information density with clear content hierarchy.
 */

import {
  Card as PrimitiveCard,
  CardContent as PrimitiveCardContent,
  type CardContentProps as PrimitiveCardContentProps,
  CardFooter as PrimitiveCardFooter,
  type CardFooterProps as PrimitiveCardFooterProps,
  CardHeader as PrimitiveCardHeader,
  type CardHeaderProps as PrimitiveCardHeaderProps,
  type CardProps as PrimitiveCardProps,
} from '@dotmac/primitives';
import * as React from 'react';

import { cn } from '../lib/utils';

/**
 * Admin Card wrapper component
 */
export interface AdminCardProps extends PrimitiveCardProps {
  /**
   * Visual variant of the card
   */
  variant?: 'default' | 'outlined' | 'elevated' | 'danger' | 'warning';
  /**
   * Whether the card is interactive (clickable)
   */
  interactive?: boolean;
  /**
   * Compact padding for dense layouts
   */
  compact?: boolean;
}

/**
 * Admin Portal Card Component
 *
 * Compact card component optimized for admin interfaces. Provides clear
 * content boundaries with minimal visual distraction.
 *
 * @example
 * ```tsx
 * <AdminCard variant="outlined" compact>
 *   <AdminCardHeader>
 *     <AdminCardTitle>Customer Overview</AdminCardTitle>
 *     <AdminCardDescription>
 *       Key metrics for customer management
 *     </AdminCardDescription>
 *   </AdminCardHeader>
 *   <AdminCardContent>
 *     <MetricGrid />
 *   </AdminCardContent>
 *   <AdminCardFooter>
 *     <AdminButton variant="outline" size="sm">
 *       View Details
 *     </AdminButton>
 *   </AdminCardFooter>
 * </AdminCard>
 * ```
 */
const AdminCard = React.forwardRef<HTMLDivElement, AdminCardProps>(
  ({ className, variant = 'default', interactive = false, compact = false, ...props }, ref) => (
    <PrimitiveCard
      ref={ref}
      className={cn(
        'rounded-lg border border-admin-border bg-admin-card text-admin-card-foreground shadow-sm',
        {
          'border-admin-destructive/50 bg-admin-destructive/5': variant === 'danger',
          'border-warning/50 bg-warning/5': variant === 'warning',
          'border-admin-border/50 shadow-none': variant === 'outlined',
          'border-admin-border/30 shadow-md': variant === 'elevated',
          'cursor-pointer transition-colors hover:bg-admin-accent/5': interactive,
          'p-3': compact,
        },
        className
      )}
      {...props}
    />
  )
);

/**
 * Admin Card Header component
 */
export interface AdminCardHeaderProps extends PrimitiveCardHeaderProps {
  /**
   * Compact spacing for dense layouts
   */
  compact?: boolean;
  /**
   * Action buttons or controls for the header
   */
  actions?: React.ReactNode;
}

const AdminCardHeader = React.forwardRef<HTMLDivElement, AdminCardHeaderProps>(
  ({ className, compact = false, actions, children, ...props }, ref) => (
    <PrimitiveCardHeader
      ref={ref}
      className={cn(
        'flex flex-row items-center justify-between space-y-0',
        {
          'p-4': !compact,
          'p-3': compact,
        },
        className
      )}
      {...props}
    >
      <div className='space-y-1'>{children}</div>
      {actions && <div className='flex items-center space-x-2'>{actions}</div>}
    </PrimitiveCardHeader>
  )
);

/**
 * Admin Card Title component
 */
export interface AdminCardTitleProps extends React.HTMLAttributes<HTMLHeadingElement> {
  /**
   * Size variant for the title
   */
  size?: 'sm' | 'md' | 'lg';
}

const AdminCardTitle = React.forwardRef<HTMLHeadingElement, AdminCardTitleProps>(
  ({ className, size = 'md', ...props }, ref) => (
    <h3
      ref={ref}
      className={cn(
        'font-semibold text-admin-foreground leading-none tracking-tight',
        {
          'text-sm': size === 'sm',
          'text-base': size === 'md',
          'text-lg': size === 'lg',
        },
        className
      )}
      {...props}
    />
  )
);

/**
 * Admin Card Description component
 */
const AdminCardDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p ref={ref} className={cn('text-admin-muted-foreground text-xs', className)} {...props} />
));

/**
 * Admin Card Content component
 */
export interface AdminCardContentProps extends PrimitiveCardContentProps {
  /**
   * Compact padding for dense layouts
   */
  compact?: boolean;
}

const AdminCardContent = React.forwardRef<HTMLDivElement, AdminCardContentProps>(
  ({ className, compact = false, ...props }, ref) => (
    <PrimitiveCardContent
      ref={ref}
      className={cn(
        {
          'p-4 pt-0': !compact,
          'p-3 pt-0': compact,
        },
        className
      )}
      {...props}
    />
  )
);

/**
 * Admin Card Footer component
 */
export interface AdminCardFooterProps extends PrimitiveCardFooterProps {
  /**
   * Compact padding for dense layouts
   */
  compact?: boolean;
}

const AdminCardFooter = React.forwardRef<HTMLDivElement, AdminCardFooterProps>(
  ({ className, compact = false, ...props }, ref) => (
    <PrimitiveCardFooter
      ref={ref}
      className={cn(
        'flex items-center border-admin-border/50 border-t bg-admin-muted/20',
        {
          'p-4 pt-3': !compact,
          'p-3 pt-2': compact,
        },
        className
      )}
      {...props}
    />
  )
);

// Set display names
AdminCard.displayName = 'AdminCard';
AdminCardHeader.displayName = 'AdminCardHeader';
AdminCardTitle.displayName = 'AdminCardTitle';
AdminCardDescription.displayName = 'AdminCardDescription';
AdminCardContent.displayName = 'AdminCardContent';
AdminCardFooter.displayName = 'AdminCardFooter';

export {
  AdminCard,
  AdminCardHeader,
  AdminCardTitle,
  AdminCardDescription,
  AdminCardContent,
  AdminCardFooter,
};
