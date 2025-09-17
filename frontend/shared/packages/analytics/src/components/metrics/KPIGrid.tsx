import React from 'react';
import { cn } from '@dotmac/primitives/utils/cn';
import { MetricCard } from './MetricCard';
import type { KPIMetric } from '../../types';

interface KPIGridProps {
  metrics: KPIMetric[];
  columns?: 1 | 2 | 3 | 4 | 6;
  size?: 'sm' | 'md' | 'lg';
  showTrend?: boolean;
  showTarget?: boolean;
  onMetricClick?: (metric: KPIMetric) => void;
  className?: string;
  loading?: boolean;
  error?: string | null;
  emptyMessage?: string;
}

export const KPIGrid: React.FC<KPIGridProps> = ({
  metrics,
  columns = 3,
  size = 'md',
  showTrend = true,
  showTarget = true,
  onMetricClick,
  className,
  loading = false,
  error = null,
  emptyMessage = 'No metrics available',
}) => {
  const gridClasses = {
    1: 'grid-cols-1',
    2: 'grid-cols-1 md:grid-cols-2',
    3: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3',
    4: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-4',
    6: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6',
  };

  if (loading) {
    return (
      <div className={cn('grid gap-4', gridClasses[columns], className)}>
        {Array.from({ length: 6 }).map((_, index) => (
          <div key={index} className='bg-white rounded-lg border shadow-sm p-4 animate-pulse'>
            <div className='space-y-3'>
              <div className='h-4 bg-gray-200 rounded w-3/4'></div>
              <div className='h-8 bg-gray-200 rounded w-1/2'></div>
              <div className='h-3 bg-gray-200 rounded w-1/4'></div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className='text-center p-8'>
        <div className='text-red-600 mb-2'>
          <svg className='w-12 h-12 mx-auto mb-4' fill='currentColor' viewBox='0 0 20 20'>
            <path
              fillRule='evenodd'
              d='M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z'
              clipRule='evenodd'
            />
          </svg>
        </div>
        <p className='text-gray-600'>{error}</p>
      </div>
    );
  }

  if (metrics.length === 0) {
    return (
      <div className='text-center p-8'>
        <div className='text-gray-400 mb-2'>
          <svg className='w-12 h-12 mx-auto mb-4' fill='currentColor' viewBox='0 0 20 20'>
            <path
              fillRule='evenodd'
              d='M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zm0 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V8zm0 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1v-2z'
              clipRule='evenodd'
            />
          </svg>
        </div>
        <p className='text-gray-500'>{emptyMessage}</p>
      </div>
    );
  }

  // Group metrics by category for better organization
  const groupedMetrics = metrics.reduce(
    (groups, metric) => {
      const category = metric.category || 'other';
      if (!groups[category]) {
        groups[category] = [];
      }
      groups[category].push(metric);
      return groups;
    },
    {} as Record<string, KPIMetric[]>
  );

  const categoryOrder = ['revenue', 'growth', 'efficiency', 'satisfaction', 'operational', 'other'];
  const orderedCategories = categoryOrder.filter((cat) => groupedMetrics[cat]);

  return (
    <div className={cn('space-y-6', className)}>
      {orderedCategories.map((category) => (
        <div key={category} className='space-y-4'>
          {orderedCategories.length > 1 && (
            <div className='flex items-center space-x-4'>
              <h3 className='text-lg font-semibold text-gray-900 capitalize'>
                {category === 'other' ? 'Other Metrics' : `${category} Metrics`}
              </h3>
              <div className='flex-1 h-px bg-gray-200'></div>
            </div>
          )}

          <div className={cn('grid gap-4', gridClasses[columns])}>
            {groupedMetrics[category].map((metric) => (
              <MetricCard
                key={metric.id}
                metric={metric}
                size={size}
                showTrend={showTrend}
                showTarget={showTarget}
                onClick={onMetricClick}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};
