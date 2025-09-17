import React from 'react';
import { cn } from '@dotmac/primitives/utils/cn';
import type { MetricCardProps, KPIMetric } from '../../types';

const formatValue = (value: number, unit: string, format?: any): string => {
  if (format?.currency) {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: format.currency,
      minimumFractionDigits: format.decimals || 0,
      maximumFractionDigits: format.decimals || 2,
    }).format(value);
  }

  if (format?.percentage) {
    return `${(value * 100).toFixed(format.decimals || 1)}%`;
  }

  let formatted = value.toLocaleString('en-US', {
    minimumFractionDigits: format?.decimals || 0,
    maximumFractionDigits: format?.decimals || 2,
  });

  if (format?.prefix) formatted = format.prefix + formatted;
  if (format?.suffix) formatted = formatted + format.suffix;
  if (unit && !format?.prefix && !format?.suffix) formatted = formatted + ' ' + unit;

  return formatted;
};

const getTrendIcon = (trend: KPIMetric['trend']) => {
  switch (trend) {
    case 'up':
      return '↗️';
    case 'down':
      return '↘️';
    default:
      return '→';
  }
};

const getStatusColor = (status: KPIMetric['status']) => {
  switch (status) {
    case 'good':
      return 'text-green-600';
    case 'warning':
      return 'text-yellow-600';
    case 'critical':
      return 'text-red-600';
    default:
      return 'text-gray-600';
  }
};

export const MetricCard: React.FC<MetricCardProps> = ({
  metric,
  size = 'md',
  showTrend = true,
  showTarget = true,
  onClick,
  className,
}) => {
  const sizeClasses = {
    sm: 'p-3',
    md: 'p-4',
    lg: 'p-6',
  };

  const titleSizeClasses = {
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg',
  };

  const valueSizeClasses = {
    sm: 'text-lg',
    md: 'text-2xl',
    lg: 'text-3xl',
  };

  const handleClick = () => {
    if (onClick) {
      onClick(metric);
    }
  };

  const progressPercentage = metric.target
    ? Math.min((metric.value / metric.target) * 100, 100)
    : 0;

  return (
    <div
      className={cn(
        'bg-white rounded-lg border shadow-sm transition-all duration-200',
        onClick && 'cursor-pointer hover:shadow-md hover:border-blue-300',
        sizeClasses[size],
        className
      )}
      onClick={handleClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
    >
      {/* Header */}
      <div className='flex items-start justify-between mb-2'>
        <div className='flex-1'>
          <h3 className={cn('font-medium text-gray-900 truncate', titleSizeClasses[size])}>
            {metric.name}
          </h3>
          {metric.description && size !== 'sm' && (
            <p className='text-xs text-gray-500 mt-1 line-clamp-2'>{metric.description}</p>
          )}
        </div>

        <div className={cn('flex items-center space-x-1 ml-2', getStatusColor(metric.status))}>
          <div
            className={cn(
              'w-2 h-2 rounded-full',
              metric.status === 'good' && 'bg-green-500',
              metric.status === 'warning' && 'bg-yellow-500',
              metric.status === 'critical' && 'bg-red-500',
              metric.status === 'unknown' && 'bg-gray-400'
            )}
          />
        </div>
      </div>

      {/* Value */}
      <div className='mb-3'>
        <div className={cn('font-bold text-gray-900', valueSizeClasses[size])}>
          {formatValue(metric.value, metric.unit)}
        </div>

        {/* Trend */}
        {showTrend && metric.previousValue !== undefined && (
          <div className='flex items-center mt-1 text-sm'>
            <span className='mr-1'>{getTrendIcon(metric.trend)}</span>
            <span
              className={cn(
                'font-medium',
                metric.trend === 'up' && metric.trendPercentage > 0 && 'text-green-600',
                metric.trend === 'down' && metric.trendPercentage < 0 && 'text-red-600',
                metric.trend === 'stable' && 'text-gray-600'
              )}
            >
              {Math.abs(metric.trendPercentage).toFixed(1)}%
            </span>
            <span className='text-gray-500 ml-1'>vs previous</span>
          </div>
        )}
      </div>

      {/* Target Progress */}
      {showTarget && metric.target && size !== 'sm' && (
        <div className='space-y-1'>
          <div className='flex justify-between text-xs text-gray-500'>
            <span>Progress to target</span>
            <span>{formatValue(metric.target, metric.unit)}</span>
          </div>
          <div className='w-full bg-gray-200 rounded-full h-1.5'>
            <div
              className={cn(
                'h-1.5 rounded-full transition-all duration-300',
                progressPercentage >= 100
                  ? 'bg-green-500'
                  : progressPercentage >= 75
                    ? 'bg-blue-500'
                    : progressPercentage >= 50
                      ? 'bg-yellow-500'
                      : 'bg-red-500'
              )}
              style={{ width: `${Math.min(progressPercentage, 100)}%` }}
            />
          </div>
          <div className='text-xs text-gray-500'>{progressPercentage.toFixed(1)}% of target</div>
        </div>
      )}

      {/* Last Updated */}
      {size !== 'sm' && (
        <div className='mt-3 pt-2 border-t border-gray-100'>
          <div className='text-xs text-gray-400'>Updated {metric.updatedAt.toLocaleString()}</div>
        </div>
      )}
    </div>
  );
};
