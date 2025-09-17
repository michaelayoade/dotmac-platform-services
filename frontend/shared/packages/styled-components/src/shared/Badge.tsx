/**
 * Shared Badge Component
 *
 * Universal badge component that adapts to portal themes while maintaining
 * consistent semantic meaning across all interfaces.
 */

import { cva, type VariantProps } from 'class-variance-authority';
import * as React from 'react';

import { cn } from '../lib/utils';

/**
 * Badge variants that adapt to portal themes
 */
const badgeVariants = cva(
  'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
  {
    variants: {
      variant: {
        default: 'border-transparent bg-primary text-primary-foreground hover:bg-primary/80',
        secondary:
          'border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80',
        destructive:
          'border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/80',
        outline: 'text-foreground',
        success: 'border-transparent bg-success text-success-foreground',
        warning: 'border-transparent bg-warning text-warning-foreground',
        info: 'border-transparent bg-info text-info-foreground',
      },
      size: {
        sm: 'px-2 py-0.5 text-xs',
        default: 'px-2.5 py-0.5 text-xs',
        lg: 'px-3 py-1 text-sm',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);

/**
 * Badge component props
 */
export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {
  /**
   * Icon to display before the badge text
   */
  icon?: React.ReactNode;
  /**
   * Whether the badge should pulse to indicate activity
   */
  pulse?: boolean;
  /**
   * Portal theme context (automatically detected)
   */
  portal?: 'admin' | 'customer' | 'reseller';
}

/**
 * Shared Badge Component
 *
 * Versatile badge component that works across all portals while adapting
 * to their respective color schemes and design languages.
 *
 * @example
 * ```tsx
 * // Status badges
 * <Badge variant="success">Active</Badge>
 * <Badge variant="warning">Pending</Badge>
 * <Badge variant="destructive">Suspended</Badge>
 *
 * // With icons
 * <Badge variant="info" icon={<InfoIcon />}>
 *   New Feature
 * </Badge>
 *
 * // Pulsing activity indicator
 * <Badge variant="success" pulse>
 *   Live
 * </Badge>
 *
 * // Different sizes
 * <Badge size="sm" variant="outline">Small</Badge>
 * <Badge size="lg" variant="default">Large</Badge>
 *
 * // Portal-specific styling (auto-detected)
 * <Badge variant="default">Adapts to portal theme</Badge>
 * ```
 */
const Badge = React.forwardRef<HTMLDivElement, BadgeProps>(
  ({ className, variant, size, icon, pulse = false, portal, ...props }, ref) => {
    const [detectedPortal, setDetectedPortal] = React.useState<string | undefined>(portal);

    // Auto-detect portal context from CSS classes
    React.useEffect(() => {
      if (!portal && typeof document !== 'undefined') {
        const body = document.body;
        if (body.classList.contains('admin-portal')) {
          setDetectedPortal('admin');
        } else if (body.classList.contains('customer-portal')) {
          setDetectedPortal('customer');
        } else if (body.classList.contains('reseller-portal')) {
          setDetectedPortal('reseller');
        } else {
          setDetectedPortal(undefined);
        }
      } else {
        setDetectedPortal(portal);
      }
    }, [portal]);

    const activePortal = portal || detectedPortal;

    return (
      <div
        ref={ref}
        className={cn(
          badgeVariants({ variant, size }),
          {
            'animate-pulse': pulse,
            // Portal-specific adaptations
            'admin-badge': activePortal === 'admin',
            'customer-badge': activePortal === 'customer',
            'reseller-badge': activePortal === 'reseller',
          },
          className
        )}
        {...props}
      >
        {icon && <span className='mr-1 h-3 w-3 flex-shrink-0'>{icon}</span>}
        {props.children}
      </div>
    );
  }
);

Badge.displayName = 'Badge';

export { Badge, badgeVariants };
export type { BadgeProps };
