/**
 * Universal Metrics Grid
 * Consolidates all metrics display patterns across portals
 */

import React from 'react';
import { LucideIcon } from 'lucide-react';

export interface MetricData {
  name: string;
  value: string;
  total?: string;
  icon: LucideIcon;
  trend?: {
    value: string;
    positive: boolean;
  };
  description?: string;
  color?: 'primary' | 'secondary' | 'success' | 'warning' | 'danger';
}

interface UniversalMetricsGridProps {
  metrics: MetricData[];
  isLoading?: boolean;
  columns?: 2 | 3 | 4 | 6;
  size?: 'sm' | 'md' | 'lg';
  portal?: 'admin' | 'customer' | 'reseller' | 'technician' | 'management';
}

const PORTAL_COLORS = {
  admin: {
    primary: 'text-blue-600',
    bg: 'bg-blue-50',
    border: 'border-blue-200',
  },
  customer: {
    primary: 'text-green-600',
    bg: 'bg-green-50',
    border: 'border-green-200',
  },
  reseller: {
    primary: 'text-purple-600',
    bg: 'bg-purple-50',
    border: 'border-purple-200',
  },
  technician: {
    primary: 'text-orange-600',
    bg: 'bg-orange-50',
    border: 'border-orange-200',
  },
  management: {
    primary: 'text-red-600',
    bg: 'bg-red-50',
    border: 'border-red-200',
  },
};

export function UniversalMetricsGrid({
  metrics,
  isLoading,
  columns = 4,
  size = 'md',
  portal = 'admin',
}: UniversalMetricsGridProps) {
  if (isLoading) {
    return <MetricsGridSkeleton columns={columns} />;
  }

  const colsClass = {
    2: 'grid-cols-1 lg:grid-cols-2',
    3: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3',
    4: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-4',
    6: 'grid-cols-2 md:grid-cols-3 lg:grid-cols-6',
  }[columns];

  const sizeClasses = {
    sm: 'p-4 gap-4',
    md: 'p-6 gap-6',
    lg: 'p-8 gap-8',
  }[size];

  return (
    <div className={`grid ${colsClass} ${sizeClasses}`}>
      {metrics.map((metric, index) => (
        <MetricCard key={`${metric.name}-${index}`} metric={metric} size={size} portal={portal} />
      ))}
    </div>
  );
}

function MetricCard({
  metric,
  size,
  portal,
}: {
  metric: MetricData;
  size: 'sm' | 'md' | 'lg';
  portal: string;
}) {
  const Icon = metric.icon;
  const colors = PORTAL_COLORS[portal as keyof typeof PORTAL_COLORS];

  const cardClasses = {
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
  }[size];

  const iconClasses = {
    sm: 'h-6 w-6',
    md: 'h-8 w-8',
    lg: 'h-10 w-10',
  }[size];

  const valueClasses = {
    sm: 'text-lg',
    md: 'text-2xl',
    lg: 'text-3xl',
  }[size];

  return (
    <div
      className={`bg-white ${cardClasses} rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-all duration-200 ${colors.bg} ${colors.border}`}
    >
      <div className='flex items-center justify-between'>
        <div className='flex items-center'>
          <Icon className={`${iconClasses} ${colors.primary}`} />
          <div className='ml-4'>
            <h3 className='text-sm font-medium text-gray-600'>{metric.name}</h3>
            <div className='flex items-baseline'>
              <p className={`${valueClasses} font-semibold text-gray-900`}>{metric.value}</p>
              {metric.total && <p className='ml-2 text-sm text-gray-500'>/{metric.total}</p>}
            </div>
          </div>
        </div>
      </div>

      {(metric.trend || metric.description) && (
        <div className='mt-4 flex items-center justify-between'>
          <div className='flex items-center'>
            {metric.trend && (
              <span
                className={`text-sm font-medium ${
                  metric.trend.positive ? 'text-green-600' : 'text-red-600'
                }`}
              >
                {metric.trend.value}
              </span>
            )}
            {metric.description && (
              <span className='ml-2 text-sm text-gray-500'>{metric.description}</span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function MetricsGridSkeleton({ columns }: { columns: number }) {
  const items = Array.from({ length: columns }, (_, i) => i);

  const colsClass = {
    2: 'grid-cols-1 lg:grid-cols-2',
    3: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3',
    4: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-4',
    6: 'grid-cols-2 md:grid-cols-3 lg:grid-cols-6',
  }[columns];

  return (
    <div className={`grid ${colsClass} gap-6`}>
      {items.map((i) => (
        <div key={i} className='bg-white p-6 rounded-lg shadow-sm border border-gray-200'>
          <div className='animate-pulse'>
            <div className='flex items-center'>
              <div className='h-8 w-8 bg-gray-300 rounded'></div>
              <div className='ml-4'>
                <div className='h-4 bg-gray-300 rounded w-20 mb-2'></div>
                <div className='h-6 bg-gray-300 rounded w-16'></div>
              </div>
            </div>
            <div className='mt-4'>
              <div className='h-3 bg-gray-300 rounded w-24'></div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
