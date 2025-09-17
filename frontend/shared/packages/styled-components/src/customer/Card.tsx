/**
 * Customer Portal Card Component
 *
 * Friendly, approachable card design for customer-facing interfaces.
 * Features generous spacing, soft shadows, and clear content hierarchy.
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
 * Customer Card wrapper component
 */
export interface CustomerCardProps extends PrimitiveCardProps {
  /**
   * Visual variant of the card
   */
  variant?: 'default' | 'outlined' | 'elevated' | 'success' | 'warning' | 'info';
  /**
   * Whether the card is interactive (clickable)
   */
  interactive?: boolean;
  /**
   * Whether to show a subtle background pattern
   */
  decorative?: boolean;
}

/**
 * Customer Portal Card Component
 *
 * Welcoming card component optimized for customer interfaces. Features
 * soft shadows, generous spacing, and friendly visual hierarchy.
 *
 * @example
 * ```tsx
 * <CustomerCard variant="elevated" interactive>
 *   <CustomerCardHeader>
 *     <CustomerCardTitle>Current Plan</CustomerCardTitle>
 *     <CustomerCardDescription>
 *       Your high-speed internet plan details
 *     </CustomerCardDescription>
 *   </CustomerCardHeader>
 *   <CustomerCardContent>
 *     <PlanDetails />
 *   </CustomerCardContent>
 *   <CustomerCardFooter>
 *     <CustomerButton variant="outline" fullWidth>
 *       Manage Plan
 *     </CustomerButton>
 *   </CustomerCardFooter>
 * </CustomerCard>
 * ```
 */
const CustomerCard = React.forwardRef<HTMLDivElement, CustomerCardProps>(
  ({ className, variant = 'default', interactive = false, decorative = false, ...props }, ref) => (
    <PrimitiveCard
      ref={ref}
      className={cn(
        'rounded-xl border border-customer-border bg-customer-card text-customer-card-foreground',
        {
          // Variants
          'shadow-lg': variant === 'default',
          'border-customer-border/60 shadow-sm': variant === 'outlined',
          'border-customer-border/30 shadow-xl': variant === 'elevated',
          'border-success/30 bg-success/5 shadow-sm': variant === 'success',
          'border-warning/30 bg-warning/5 shadow-sm': variant === 'warning',
          'border-info/30 bg-info/5 shadow-sm': variant === 'info',

          // Interactive states
          'cursor-pointer transition-all duration-200 hover:scale-[1.02] hover:shadow-xl':
            interactive,

          // Decorative background
          'relative overflow-hidden': decorative,
        },
        className
      )}
      {...props}
    >
      {decorative && (
        <div className='pointer-events-none absolute inset-0 bg-gradient-to-br from-customer-primary/5 to-transparent' />
      )}
      {props.children}
    </PrimitiveCard>
  )
);

/**
 * Customer Card Header component
 */
export interface CustomerCardHeaderProps extends PrimitiveCardHeaderProps {
  /**
   * Action buttons or controls for the header
   */
  actions?: React.ReactNode;
  /**
   * Show a decorative icon
   */
  icon?: React.ReactNode;
}

const CustomerCardHeader = React.forwardRef<HTMLDivElement, CustomerCardHeaderProps>(
  ({ className, actions, icon, children, ...props }, ref) => (
    <PrimitiveCardHeader
      ref={ref}
      className={cn('flex flex-row items-start justify-between space-y-0 p-6', className)}
      {...props}
    >
      <div className='flex items-start space-x-4'>
        {icon && (
          <div className='mt-1 flex-shrink-0'>
            <div className='flex h-10 w-10 items-center justify-center rounded-lg bg-customer-primary/10 text-customer-primary'>
              {icon}
            </div>
          </div>
        )}
        <div className='space-y-2'>{children}</div>
      </div>
      {actions && <div className='flex items-center space-x-2'>{actions}</div>}
    </PrimitiveCardHeader>
  )
);

/**
 * Customer Card Title component
 */
export interface CustomerCardTitleProps extends React.HTMLAttributes<HTMLHeadingElement> {
  /**
   * Size variant for the title
   */
  size?: 'sm' | 'md' | 'lg';
}

const CustomerCardTitle = React.forwardRef<HTMLHeadingElement, CustomerCardTitleProps>(
  ({ className, size = 'md', ...props }, ref) => (
    <h3
      ref={ref}
      className={cn(
        'font-semibold text-customer-foreground leading-none tracking-tight',
        {
          'text-base': size === 'sm',
          'text-lg': size === 'md',
          'text-xl': size === 'lg',
        },
        className
      )}
      {...props}
    />
  )
);

/**
 * Customer Card Description component
 */
const CustomerCardDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn('text-customer-muted-foreground text-sm leading-relaxed', className)}
    {...props}
  />
));

/**
 * Customer Card Content component
 */
export interface CustomerCardContentProps extends PrimitiveCardContentProps {
  /**
   * Whether to add extra padding for comfort
   */
  comfortable?: boolean;
}

const CustomerCardContent = React.forwardRef<HTMLDivElement, CustomerCardContentProps>(
  ({ className, comfortable = true, ...props }, ref) => (
    <PrimitiveCardContent
      ref={ref}
      className={cn(
        {
          'p-6 pt-0': comfortable,
          'p-4 pt-0': !comfortable,
        },
        className
      )}
      {...props}
    />
  )
);

/**
 * Customer Card Footer component
 */
export interface CustomerCardFooterProps extends PrimitiveCardFooterProps {
  /**
   * Whether to add a subtle border
   */
  bordered?: boolean;
}

const CustomerCardFooter = React.forwardRef<HTMLDivElement, CustomerCardFooterProps>(
  ({ className, bordered = false, ...props }, ref) => (
    <PrimitiveCardFooter
      ref={ref}
      className={cn(
        'flex items-center p-6 pt-4',
        {
          'border-customer-border/30 border-t bg-customer-muted/10': bordered,
        },
        className
      )}
      {...props}
    />
  )
);

// Set display names
CustomerCard.displayName = 'CustomerCard';
CustomerCardHeader.displayName = 'CustomerCardHeader';
CustomerCardTitle.displayName = 'CustomerCardTitle';
CustomerCardDescription.displayName = 'CustomerCardDescription';
CustomerCardContent.displayName = 'CustomerCardContent';
CustomerCardFooter.displayName = 'CustomerCardFooter';

export {
  CustomerCard,
  CustomerCardHeader,
  CustomerCardTitle,
  CustomerCardDescription,
  CustomerCardContent,
  CustomerCardFooter,
};
