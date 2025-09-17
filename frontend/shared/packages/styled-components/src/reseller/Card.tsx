/**
 * Reseller Portal Card Component
 *
 * Professional, brandable card design for partner/reseller interfaces.
 * Balances business aesthetics with customization flexibility.
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
 * Reseller Card wrapper component
 */
export interface ResellerCardProps extends PrimitiveCardProps {
  /**
   * Visual variant of the card
   */
  variant?: 'default' | 'outlined' | 'elevated' | 'branded' | 'feature' | 'metric';
  /**
   * Whether the card is interactive (clickable)
   */
  interactive?: boolean;
  /**
   * Whether to show a subtle brand accent
   */
  branded?: boolean;
}

/**
 * Reseller Portal Card Component
 *
 * Professional card component optimized for partner interfaces. Features
 * clean design with optional brand accents and business-focused styling.
 *
 * @example
 * ```tsx
 * <ResellerCard variant="branded" interactive>
 *   <ResellerCardHeader>
 *     <ResellerCardTitle>Commission Overview</ResellerCardTitle>
 *     <ResellerCardDescription>
 *       Your earnings and performance metrics
 *     </ResellerCardDescription>
 *   </ResellerCardHeader>
 *   <ResellerCardContent>
 *     <CommissionMetrics />
 *   </ResellerCardContent>
 *   <ResellerCardFooter>
 *     <ResellerButton variant="brand" size="sm" fullWidth>
 *       View Detailed Report
 *     </ResellerButton>
 *   </ResellerCardFooter>
 * </ResellerCard>
 * ```
 */
const ResellerCard = React.forwardRef<HTMLDivElement, ResellerCardProps>(
  ({ className, variant = 'default', interactive = false, branded = false, ...props }, ref) => (
    <PrimitiveCard
      ref={ref}
      className={cn(
        'rounded-lg border border-reseller-border bg-reseller-card text-reseller-card-foreground',
        {
          // Variants
          'shadow-md': variant === 'default',
          'border-reseller-border/60 shadow-sm': variant === 'outlined',
          'border-reseller-border/30 shadow-lg': variant === 'elevated',
          'border-l-4 border-l-reseller-primary shadow-md': variant === 'branded',
          'border-reseller-primary/20 bg-gradient-to-br from-reseller-background to-reseller-accent/5 shadow-xl':
            variant === 'feature',
          'border-reseller-border bg-gradient-to-r from-reseller-background to-reseller-muted/20':
            variant === 'metric',

          // Interactive states
          'hover:-translate-y-0.5 cursor-pointer transition-all duration-200 hover:shadow-lg':
            interactive,

          // Brand accent
          'border-l-4 border-l-reseller-primary': branded && variant === 'default',
        },
        className
      )}
      {...props}
    />
  )
);

/**
 * Reseller Card Header component
 */
export interface ResellerCardHeaderProps extends PrimitiveCardHeaderProps {
  /**
   * Action buttons or controls for the header
   */
  actions?: React.ReactNode;
  /**
   * Show a brand status indicator
   */
  status?: 'active' | 'pending' | 'inactive';
  /**
   * Category or tag for the card
   */
  category?: string;
}

const ResellerCardHeader = React.forwardRef<HTMLDivElement, ResellerCardHeaderProps>(
  ({ className, actions, status, category, children, ...props }, ref) => (
    <PrimitiveCardHeader
      ref={ref}
      className={cn('flex flex-row items-start justify-between space-y-0 p-5', className)}
      {...props}
    >
      <div className='space-y-2'>
        {category && (
          <div className='font-medium text-reseller-muted-foreground text-xs uppercase tracking-wide'>
            {category}
          </div>
        )}
        {children}
        {status && (
          <div className='flex items-center space-x-2'>
            <div
              className={cn('h-2 w-2 rounded-full', {
                'bg-success': status === 'active',
                'bg-warning': status === 'pending',
                'bg-reseller-muted-foreground': status === 'inactive',
              })}
            />
            <span className='text-reseller-muted-foreground text-xs capitalize'>{status}</span>
          </div>
        )}
      </div>
      {actions && <div className='flex items-center space-x-2'>{actions}</div>}
    </PrimitiveCardHeader>
  )
);

/**
 * Reseller Card Title component
 */
export interface ResellerCardTitleProps extends React.HTMLAttributes<HTMLHeadingElement> {
  /**
   * Size variant for the title
   */
  size?: 'sm' | 'md' | 'lg';
}

const ResellerCardTitle = React.forwardRef<HTMLHeadingElement, ResellerCardTitleProps>(
  ({ className, size = 'md', ...props }, ref) => (
    <h3
      ref={ref}
      className={cn(
        'font-semibold text-reseller-foreground leading-none tracking-tight',
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
 * Reseller Card Description component
 */
const ResellerCardDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p ref={ref} className={cn('text-reseller-muted-foreground text-sm', className)} {...props} />
));

/**
 * Reseller Card Content component
 */
export interface ResellerCardContentProps extends PrimitiveCardContentProps {
  /**
   * Whether to add padding for metrics display
   */
  metrics?: boolean;
}

const ResellerCardContent = React.forwardRef<HTMLDivElement, ResellerCardContentProps>(
  ({ className, metrics = false, ...props }, ref) => (
    <PrimitiveCardContent
      ref={ref}
      className={cn(
        {
          'p-5 pt-0': !metrics,
          'p-5 pt-2': metrics,
        },
        className
      )}
      {...props}
    />
  )
);

/**
 * Reseller Card Footer component
 */
export interface ResellerCardFooterProps extends PrimitiveCardFooterProps {
  /**
   * Whether to add a subtle border
   */
  bordered?: boolean;
  /**
   * Whether to use brand background
   */
  branded?: boolean;
}

const ResellerCardFooter = React.forwardRef<HTMLDivElement, ResellerCardFooterProps>(
  ({ className, bordered = false, branded = false, ...props }, ref) => (
    <PrimitiveCardFooter
      ref={ref}
      className={cn(
        'flex items-center p-5 pt-3',
        {
          'border-reseller-border/50 border-t': bordered,
          'border-reseller-primary/20 border-t bg-reseller-primary/5': branded,
        },
        className
      )}
      {...props}
    />
  )
);

// Set display names
ResellerCard.displayName = 'ResellerCard';
ResellerCardHeader.displayName = 'ResellerCardHeader';
ResellerCardTitle.displayName = 'ResellerCardTitle';
ResellerCardDescription.displayName = 'ResellerCardDescription';
ResellerCardContent.displayName = 'ResellerCardContent';
ResellerCardFooter.displayName = 'ResellerCardFooter';

export {
  ResellerCard,
  ResellerCardHeader,
  ResellerCardTitle,
  ResellerCardDescription,
  ResellerCardContent,
  ResellerCardFooter,
};
