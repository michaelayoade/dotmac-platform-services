import React from 'react';
import { cn } from '@dotmac/primitives/utils/cn';

interface RealTimeIndicatorProps {
  isConnected: boolean;
  lastUpdate?: Date;
  className?: string;
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export const RealTimeIndicator: React.FC<RealTimeIndicatorProps> = ({
  isConnected,
  lastUpdate,
  className,
  showLabel = true,
  size = 'md',
}) => {
  const sizeClasses = {
    sm: 'w-2 h-2',
    md: 'w-3 h-3',
    lg: 'w-4 h-4',
  };

  const textSizeClasses = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
  };

  const formatLastUpdate = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();

    if (diff < 60000) {
      // Less than 1 minute
      return 'Just now';
    } else if (diff < 3600000) {
      // Less than 1 hour
      const minutes = Math.floor(diff / 60000);
      return `${minutes}m ago`;
    } else if (diff < 86400000) {
      // Less than 1 day
      const hours = Math.floor(diff / 3600000);
      return `${hours}h ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  return (
    <div className={cn('flex items-center space-x-2', className)}>
      {/* Status Indicator */}
      <div className='relative'>
        <div
          className={cn(
            'rounded-full',
            sizeClasses[size],
            isConnected ? 'bg-green-500' : 'bg-red-500'
          )}
        />
        {isConnected && (
          <div
            className={cn(
              'absolute -inset-1 rounded-full animate-ping',
              sizeClasses[size],
              'bg-green-400 opacity-75'
            )}
          />
        )}
      </div>

      {/* Status Text */}
      {showLabel && (
        <div className={cn('flex flex-col', textSizeClasses[size])}>
          <span className={cn('font-medium', isConnected ? 'text-green-600' : 'text-red-600')}>
            {isConnected ? 'Live' : 'Disconnected'}
          </span>
          {lastUpdate && <span className='text-gray-500'>{formatLastUpdate(lastUpdate)}</span>}
        </div>
      )}
    </div>
  );
};
