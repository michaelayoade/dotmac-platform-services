/**
 * Shared Tooltip Component
 *
 * Universal tooltip component using Radix UI that adapts to portal themes
 * while maintaining consistent behavior and accessibility.
 */

import * as TooltipPrimitive from '@radix-ui/react-tooltip';
import { cva, type VariantProps } from 'class-variance-authority';
import * as React from 'react';

import { cn } from '../lib/utils';

/**
 * Tooltip content variants
 */
const tooltipVariants = cva(
  'z-50 overflow-hidden rounded-md border px-3 py-1.5 text-xs shadow-md animate-in fade-in-0 zoom-in-95 data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2',
  {
    variants: {
      variant: {
        default: 'bg-primary text-primary-foreground',
        secondary: 'bg-secondary text-secondary-foreground',
        success: 'bg-success text-success-foreground',
        warning: 'bg-warning text-warning-foreground',
        destructive: 'bg-destructive text-destructive-foreground',
        info: 'bg-info text-info-foreground',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
);

/**
 * Tooltip Provider component
 */
export interface TooltipProviderProps
  extends React.ComponentProps<typeof TooltipPrimitive.Provider> {
  /**
   * Portal theme context
   */
  portal?: 'admin' | 'customer' | 'reseller';
}

const TooltipProvider = (props: Omit<TooltipProviderProps, '_portal'>) => (
  <TooltipPrimitive.Provider {...props} />
);

/**
 * Tooltip Root component
 */
const Tooltip = TooltipPrimitive.Root;

/**
 * Tooltip Trigger component
 */
const TooltipTrigger = TooltipPrimitive.Trigger;

/**
 * Tooltip Content component props
 */
export interface TooltipContentProps
  extends React.ComponentPropsWithoutRef<typeof TooltipPrimitive.Content>,
    VariantProps<typeof tooltipVariants> {
  /**
   * Portal theme context
   */
  portal?: 'admin' | 'customer' | 'reseller';
}

/**
 * Tooltip Content component
 */
const TooltipContent = React.forwardRef<
  React.ElementRef<typeof TooltipPrimitive.Content>,
  TooltipContentProps
>(({ className, variant, portal, sideOffset = 4, ...props }, ref) => (
  <TooltipPrimitive.Content
    ref={ref}
    sideOffset={sideOffset}
    className={cn(
      tooltipVariants({ variant }),
      {
        // Portal-specific styling
        'admin-tooltip': portal === 'admin',
        'customer-tooltip': portal === 'customer',
        'reseller-tooltip': portal === 'reseller',
      },
      className
    )}
    {...props}
  />
));

/**
 * Tooltip Portal component
 */
const TooltipPortal = TooltipPrimitive.Portal;

/**
 * Quick Tooltip component for simple use cases
 */
export interface QuickTooltipProps {
  /**
   * Tooltip content
   */
  content: React.ReactNode;
  /**
   * Children to wrap with tooltip
   */
  children: React.ReactNode;
  /**
   * Tooltip variant
   */
  variant?: VariantProps<typeof tooltipVariants>['variant'];
  /**
   * Side to position tooltip
   */
  side?: 'top' | 'right' | 'bottom' | 'left';
  /**
   * Delay before showing tooltip (in ms)
   */
  delayDuration?: number;
  /**
   * Whether tooltip is disabled
   */
  disabled?: boolean;
  /**
   * Portal theme context
   */
  portal?: 'admin' | 'customer' | 'reseller';
}

/**
 * Quick Tooltip Component
 *
 * Simplified tooltip component for common use cases. Wraps children
 * with a tooltip that appears on hover.
 *
 * @example
 * ```tsx
 * // Basic tooltip
 * <QuickTooltip content="Click to edit">
 *   <Button>Edit</Button>
 * </QuickTooltip>
 *
 * // Warning tooltip
 * <QuickTooltip
 *   content="This action cannot be undone"
 *   variant="warning"
 *   side="top"
 * >
 *   <Button variant="destructive">Delete</Button>
 * </QuickTooltip>
 *
 * // Info tooltip with delay
 * <QuickTooltip
 *   content="Additional information about this feature"
 *   variant="info"
 *   delayDuration={500}
 * >
 *   <InfoIcon />
 * </QuickTooltip>
 * ```
 */
const QuickTooltip = React.forwardRef<HTMLButtonElement, QuickTooltipProps>(
  (
    {
      content,
      children,
      variant = 'default',
      side = 'top',
      delayDuration = 200,
      disabled = false,
      portal,
      ...props
    },
    ref
  ) => {
    if (disabled || !content) {
      return <>{children}</>;
    }

    return (
      <TooltipProvider portal={portal}>
        <Tooltip delayDuration={delayDuration}>
          <TooltipTrigger asChild ref={ref} {...props}>
            {children}
          </TooltipTrigger>
          <TooltipContent variant={variant} side={side} portal={portal}>
            {content}
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }
);

/**
 * Tooltip with Icon component for informational tooltips
 */
export interface TooltipWithIconProps extends QuickTooltipProps {
  /**
   * Icon to display as trigger
   */
  icon?: React.ReactNode;
  /**
   * Size of the icon
   */
  iconSize?: 'sm' | 'md' | 'lg';
}

/**
 * Tooltip with Icon Component
 *
 * Pre-built tooltip with an icon trigger, commonly used for help text
 * and additional information.
 *
 * @example
 * ```tsx
 * <TooltipWithIcon
 *   content="This field is required for account verification"
 *   icon={<InfoIcon />}
 *   variant="info"
 * />
 * ```
 */
const TooltipWithIcon = React.forwardRef<HTMLButtonElement, TooltipWithIconProps>(
  (
    {
      icon = (
        <svg
          aria-label='icon'
          className='h-4 w-4'
          fill='none'
          stroke='currentColor'
          viewBox='0 0 24 24'
        >
          <title>Icon</title>
          <path
            strokeLinecap='round'
            strokeLinejoin='round'
            strokeWidth={2}
            d='M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
          />
        </svg>
      ),
      iconSize = 'md',
      ...props
    },
    ref
  ) => {
    return (
      <QuickTooltip {...props}>
        <button
          ref={ref}
          type='button'
          className={cn(
            'inline-flex items-center justify-center rounded-full text-muted-foreground transition-colors hover:text-foreground',
            {
              'h-4 w-4': iconSize === 'sm',
              'h-5 w-5': iconSize === 'md',
              'h-6 w-6': iconSize === 'lg',
            }
          )}
        >
          {icon}
        </button>
      </QuickTooltip>
    );
  }
);

// Set display names
TooltipProvider.displayName = 'TooltipProvider';
TooltipContent.displayName = 'TooltipContent';
QuickTooltip.displayName = 'QuickTooltip';
TooltipWithIcon.displayName = 'TooltipWithIcon';

export {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
  TooltipProvider,
  TooltipPortal,
  QuickTooltip,
  TooltipWithIcon,
  tooltipVariants,
};

export type { TooltipContentProps, QuickTooltipProps, TooltipWithIconProps };
