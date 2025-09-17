/**
 * Refactored Avatar Component using composition pattern
 * Separated concerns for better testability and maintainability
 */

import { OptimizedImage } from '@dotmac/primitives';
import { cva, type VariantProps } from 'class-variance-authority';
import * as React from 'react';
import { cn } from '../lib/utils';

/**
 * Avatar variants that adapt to portal themes
 */
const avatarVariants = cva('relative flex shrink-0 overflow-hidden rounded-full', {
  variants: {
    size: {
      sm: 'h-8 w-8',
      default: 'h-10 w-10',
      lg: 'h-12 w-12',
      xl: 'h-16 w-16',
      '2xl': 'h-20 w-20',
    },
  },
  defaultVariants: {
    size: 'default',
  },
});

/**
 * Composable Avatar utilities
 */
export const AvatarUtils = {
  //  // Removed - can't use hooks in objects
  getTextSize: (size: string) => {
    const sizeMap = {
      sm: 'text-xs',
      default: 'text-sm',
      lg: 'text-base',
      xl: 'text-lg',
      '2xl': 'text-xl',
    };
    return sizeMap[size as keyof typeof sizeMap] || 'text-sm';
  },

  getStatusSize: (size: string) => {
    const sizeMap = {
      sm: { class: 'h-2 w-2', position: '-bottom-0 -right-0' },
      default: { class: 'h-3 w-3', position: '-bottom-0.5 -right-0.5' },
      lg: { class: 'h-3.5 w-3.5', position: '-bottom-0.5 -right-0.5' },
      xl: { class: 'h-4 w-4', position: '-bottom-1 -right-1' },
      '2xl': { class: 'h-5 w-5', position: '-bottom-1 -right-1' },
    };
    return sizeMap[size as keyof typeof sizeMap] || sizeMap.default;
  },

  getStatusColor: (status: string) => {
    const colorMap = {
      online: 'bg-green-500',
      offline: 'bg-gray-400',
      busy: 'bg-red-500',
      away: 'bg-yellow-500',
    };
    return colorMap[status as keyof typeof colorMap] || 'bg-gray-400';
  },

  getPortalStyles: (portal?: string) => {
    const portalMap = {
      admin: 'bg-admin-muted text-admin-muted-foreground',
      customer: 'bg-customer-muted text-customer-muted-foreground',
      reseller: 'bg-reseller-muted text-reseller-muted-foreground',
    };
    return portalMap[portal as keyof typeof portalMap] || 'bg-muted text-muted-foreground';
  },
};

/**
 * Composable Avatar Image component
 */
export interface AvatarImageProps extends React.ImgHTMLAttributes<HTMLImageElement> {
  src: string;
  alt?: string;
  onLoad?: () => void;
  onError?: () => void;
}

export const AvatarImage = React.forwardRef<HTMLImageElement, AvatarImageProps>(
  ({ className, src, alt = 'Avatar', onLoad, onError, ...props }, ref) => {
    const id = React.useId();
    return (
      <OptimizedImage
        ref={ref}
        src={src}
        alt={alt}
        className={cn('aspect-square h-full w-full object-cover', className)}
        onLoad={onLoad}
        onError={onError}
        data-testid={`${id}-avatar-image`}
        {...props}
      />
    );
  }
);

/**
 * Composable Avatar Fallback component
 */
export interface AvatarFallbackProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  size?: string;
  portal?: string;
}

export const AvatarFallback = React.forwardRef<HTMLDivElement, AvatarFallbackProps>(
  ({ className, children, size = 'default', portal, ...props }, ref) => {
    const id = React.useId();
    const textSize = AvatarUtils.getTextSize(size);
    const portalStyles = AvatarUtils.getPortalStyles(portal);

    return (
      <div
        ref={ref}
        className={cn(
          'flex h-full w-full items-center justify-center font-medium',
          portalStyles,
          textSize,
          className
        )}
        data-testid={`${id}-avatar-fallback`}
        {...props}
      >
        {children}
      </div>
    );
  }
);

/**
 * Composable Avatar Status component
 */
export interface AvatarStatusProps extends React.HTMLAttributes<HTMLDivElement> {
  status: 'online' | 'offline' | 'busy' | 'away';
  size?: string;
}

export const AvatarStatus = React.forwardRef<HTMLDivElement, AvatarStatusProps>(
  ({ className, status, size = 'default', ...props }, ref) => {
    const id = React.useId();
    const statusConfig = AvatarUtils.getStatusSize(size);
    const statusColor = AvatarUtils.getStatusColor(status);

    return (
      <div
        ref={ref}
        className={cn(
          'absolute rounded-full border-2 border-background',
          statusConfig.class,
          statusConfig.position,
          statusColor,
          className
        )}
        data-testid={`${id}-avatar-status`}
        {...props}
      >
        {status === 'online' && (
          <div className='absolute inset-0 animate-ping rounded-full bg-green-500 opacity-75' />
        )}
      </div>
    );
  }
);

/**
 * Main Avatar component using composition
 */
export interface AvatarProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof avatarVariants> {
  src?: string;
  alt?: string;
  fallback?: string;
  status?: 'online' | 'offline' | 'busy' | 'away';
  portal?: 'admin' | 'customer' | 'reseller';
}

export const Avatar = React.forwardRef<HTMLDivElement, AvatarProps>(
  ({ className, size, src, alt, fallback, status, portal, children, ...props }, ref) => {
    const id = React.useId();
    const [imageLoaded, setImageLoaded] = React.useState(false);
    const [imageError, setImageError] = React.useState(false);

    const showImage = src && imageLoaded && !imageError;
    const showFallback = !src || imageError || !imageLoaded;

    return (
      <div
        ref={ref}
        className={cn(avatarVariants({ size }), className)}
        data-testid={`${id}-avatar`}
        {...props}
      >
        {/* Render custom children if provided */}
        {children}

        {/* Default behavior if no custom children */}
        {!children && (
          <>
            {/* Avatar Image */}
            {src && (
              <AvatarImage
                src={src}
                alt={alt}
                className={cn({
                  'opacity-0': !showImage,
                  'opacity-100': showImage,
                })}
                onLoad={() => setImageLoaded(true)}
                onError={() => setImageError(true)}
              />
            )}

            {/* Fallback */}
            {showFallback && fallback && (
              <AvatarFallback size={size} portal={portal}>
                {fallback}
              </AvatarFallback>
            )}

            {/* Status Indicator */}
            {status && <AvatarStatus status={status} size={size} />}
          </>
        )}
      </div>
    );
  }
);

/**
 * Avatar Group component for displaying multiple avatars
 */
export interface AvatarGroupProps extends React.HTMLAttributes<HTMLDivElement> {
  max?: number;
  size?: VariantProps<typeof avatarVariants>['size'];
  portal?: 'admin' | 'customer' | 'reseller';
}

export const AvatarGroup = React.forwardRef<HTMLDivElement, AvatarGroupProps>(
  ({ className, max = 3, size = 'default', portal, children, ...props }, ref) => {
    const id = React.useId();
    const childrenArray = React.Children.toArray(children);
    const visibleAvatars = childrenArray.slice(0, max);
    const remainingCount = Math.max(0, childrenArray.length - max);

    return (
      <div
        ref={ref}
        className={cn('-space-x-2 flex', className)}
        data-testid={`${id}-avatar-group`}
        {...props}
      >
        {visibleAvatars.map((child, index) => (
          <div key={`item-${index}`} className='rounded-full ring-2 ring-background'>
            {React.cloneElement(child as React.ReactElement, { size, portal })}
          </div>
        ))}

        {remainingCount > 0 && (
          <div className='rounded-full ring-2 ring-background'>
            <Avatar
              size={size}
              fallback={`+${remainingCount}`}
              portal={portal}
              className='bg-muted text-muted-foreground'
            />
          </div>
        )}
      </div>
    );
  }
);

// Display names
Avatar.displayName = 'Avatar';
AvatarImage.displayName = 'AvatarImage';
AvatarFallback.displayName = 'AvatarFallback';
AvatarStatus.displayName = 'AvatarStatus';
AvatarGroup.displayName = 'AvatarGroup';

export { avatarVariants };
export type { AvatarGroupProps };
