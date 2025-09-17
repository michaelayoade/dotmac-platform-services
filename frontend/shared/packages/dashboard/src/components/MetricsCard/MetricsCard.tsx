/**
 * Universal MetricsCard Component
 * Production-ready, portal-agnostic metrics display
 * DRY pattern: Same component, different data across all portals
 */

import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { Card } from '@dotmac/primitives';
import type { PortalVariant, MetricsCardData } from '../../types';
import { cn } from '../../utils/cn';

const metricsCardVariants = cva(
  'relative overflow-hidden transition-all duration-200 hover:shadow-lg',
  {
    variants: {
      variant: {
        admin:
          'border-blue-200 bg-gradient-to-br from-blue-50 to-blue-100/50 hover:border-blue-300',
        customer:
          'border-green-200 bg-gradient-to-br from-green-50 to-green-100/50 hover:border-green-300',
        reseller:
          'border-purple-200 bg-gradient-to-br from-purple-50 to-purple-100/50 hover:border-purple-300',
        technician:
          'border-orange-200 bg-gradient-to-br from-orange-50 to-orange-100/50 hover:border-orange-300',
        management:
          'border-indigo-200 bg-gradient-to-br from-indigo-50 to-indigo-100/50 hover:border-indigo-300',
      },
      size: {
        sm: 'p-4',
        md: 'p-6',
        lg: 'p-8',
      },
    },
    defaultVariants: {
      variant: 'admin',
      size: 'md',
    },
  }
);

const trendVariants = cva(
  'inline-flex items-center gap-1 rounded-full px-2 py-1 text-xs font-medium',
  {
    variants: {
      trend: {
        up: 'bg-green-100 text-green-700',
        down: 'bg-red-100 text-red-700',
        stable: 'bg-gray-100 text-gray-700',
      },
    },
  }
);

const valueVariants = cva('text-3xl font-bold leading-none', {
  variants: {
    variant: {
      admin: 'text-blue-900',
      customer: 'text-green-900',
      reseller: 'text-purple-900',
      technician: 'text-orange-900',
      management: 'text-indigo-900',
    },
  },
});

export interface MetricsCardProps extends VariantProps<typeof metricsCardVariants> {
  data: MetricsCardData;
  variant: PortalVariant;
  className?: string;
  loading?: boolean;
  animated?: boolean;
}

export const MetricsCard: React.FC<MetricsCardProps> = ({
  data,
  variant,
  size = 'md',
  className,
  loading = false,
  animated = true,
  ...props
}) => {
  const TrendIcon = data.trend === 'up' ? TrendingUp : data.trend === 'down' ? TrendingDown : Minus;
  const IconComponent = data.icon;

  const cardAnimation = animated
    ? {
        initial: { opacity: 0, y: 20 },
        animate: { opacity: 1, y: 0 },
        transition: { duration: 0.3 },
      }
    : {};

  const valueAnimation = animated
    ? {
        initial: { scale: 0.8 },
        animate: { scale: 1 },
        transition: { duration: 0.5, delay: 0.1 },
      }
    : {};

  if (loading) {
    return (
      <Card className={cn(metricsCardVariants({ variant, size }), 'animate-pulse', className)}>
        <div className='space-y-3'>
          <div className='flex justify-between items-start'>
            <div className='h-4 bg-gray-200 rounded w-24'></div>
            <div className='h-6 w-6 bg-gray-200 rounded'></div>
          </div>
          <div className='h-8 bg-gray-200 rounded w-32'></div>
          <div className='h-4 bg-gray-200 rounded w-16'></div>
        </div>
      </Card>
    );
  }

  return (
    <motion.div {...cardAnimation}>
      <Card className={cn(metricsCardVariants({ variant, size }), className)} {...props}>
        {/* Header */}
        <div className='flex justify-between items-start mb-4'>
          <h3 className='text-sm font-medium text-gray-600 leading-tight'>{data.title}</h3>
          {IconComponent && (
            <div
              className={cn(
                'flex items-center justify-center w-8 h-8 rounded-lg',
                variant === 'admin' && 'bg-blue-100 text-blue-600',
                variant === 'customer' && 'bg-green-100 text-green-600',
                variant === 'reseller' && 'bg-purple-100 text-purple-600',
                variant === 'technician' && 'bg-orange-100 text-orange-600',
                variant === 'management' && 'bg-indigo-100 text-indigo-600'
              )}
            >
              {React.createElement(IconComponent as any, { className: 'w-4 h-4' })}
            </div>
          )}
        </div>

        {/* Value */}
        <motion.div {...valueAnimation} className='mb-2'>
          <span className={cn(valueVariants({ variant }))}>
            {typeof data.value === 'number' ? data.value.toLocaleString() : data.value}
          </span>
        </motion.div>

        {/* Trend & Description */}
        <div className='flex items-center justify-between'>
          <div className='flex-1'>
            {data.change && data.trend && (
              <div className={cn(trendVariants({ trend: data.trend }))}>
                <TrendIcon size={12} />
                <span>{data.change}</span>
              </div>
            )}
            {data.description && (
              <p className='text-xs text-gray-500 mt-1 leading-relaxed'>{data.description}</p>
            )}
          </div>

          {data.onAction && data.actionLabel && (
            <button
              onClick={data.onAction}
              className={cn(
                'text-xs font-medium px-2 py-1 rounded-md transition-colors',
                variant === 'admin' && 'text-blue-700 hover:bg-blue-100',
                variant === 'customer' && 'text-green-700 hover:bg-green-100',
                variant === 'reseller' && 'text-purple-700 hover:bg-purple-100',
                variant === 'technician' && 'text-orange-700 hover:bg-orange-100',
                variant === 'management' && 'text-indigo-700 hover:bg-indigo-100'
              )}
            >
              {data.actionLabel}
            </button>
          )}
        </div>

        {/* Decorative accent */}
        <div
          className={cn(
            'absolute top-0 left-0 w-full h-1 opacity-60',
            variant === 'admin' && 'bg-blue-500',
            variant === 'customer' && 'bg-green-500',
            variant === 'reseller' && 'bg-purple-500',
            variant === 'technician' && 'bg-orange-500',
            variant === 'management' && 'bg-indigo-500'
          )}
        />
      </Card>
    </motion.div>
  );
};

// DRY Metrics Factory - Single function handles all metric types
export const createMetric = (
  title: string,
  value: string | number,
  options?: {
    description?: string;
    trend?: 'up' | 'down' | 'stable';
    change?: string;
  }
): MetricsCardData => ({
  title,
  value,
  ...(options?.description && { description: options.description }),
  ...(options?.trend && { trend: options.trend }),
  ...(options?.change && { change: options.change }),
});

// Helper functions for common metric patterns
export const createPercentageMetric = (
  title: string,
  percentage: number,
  description: string,
  thresholds = { excellent: 95, good: 85 }
) =>
  createMetric(title, `${percentage}%`, {
    description,
    trend:
      percentage >= thresholds.excellent ? 'up' : percentage >= thresholds.good ? 'stable' : 'down',
    change:
      percentage >= thresholds.excellent
        ? 'Excellent'
        : percentage >= thresholds.good
          ? 'Good'
          : 'Needs attention',
  });

export const createCountMetric = (title: string, count: number, description: string) =>
  createMetric(title, count, { description });

export const createCurrencyMetric = (
  title: string,
  amount: number,
  change?: string,
  description?: string
) =>
  createMetric(title, `$${amount.toLocaleString()}`, {
    ...(description && { description }),
    ...(change && { change }),
    trend: change?.startsWith('+') ? 'up' : change?.startsWith('-') ? 'down' : 'stable',
  });

// Common metric templates (DRY approach)
export const METRICS_TEMPLATES = {
  health: (percentage: number) =>
    createPercentageMetric('System Health', percentage, 'Overall platform health score'),
  uptime: (percentage: number) =>
    createPercentageMetric('Network Uptime', percentage, 'Network availability', {
      excellent: 99.5,
      good: 99,
    }),
  customers: (count: number) =>
    createCountMetric('Active Customers', count, 'Currently subscribed customers'),
  revenue: (amount: number, change?: string) =>
    createCurrencyMetric('Monthly Revenue', amount, change, 'Platform-wide revenue'),
} as const;

// Portal-specific preset aliases (leverages existing templates)
export const MetricsCardPresets = {
  management: {
    totalTenants: (count: number) => METRICS_TEMPLATES.customers(count),
    systemHealth: (percentage: number) => METRICS_TEMPLATES.health(percentage),
    platformRevenue: (amount: number, change?: string) => METRICS_TEMPLATES.revenue(amount, change),
  },
  admin: {
    activeCustomers: (count: number) => METRICS_TEMPLATES.customers(count),
    networkUptime: (percentage: number) => METRICS_TEMPLATES.uptime(percentage),
    monthlyRevenue: (amount: number, change?: string) => METRICS_TEMPLATES.revenue(amount, change),
  },
  customer: {
    dataUsage: (used: number, total: number) =>
      createMetric('Data Usage', `${used}GB / ${total}GB`, {
        description: 'Current month usage',
        trend: used < total * 0.8 ? 'stable' : used < total * 0.95 ? 'up' : 'down',
      }),
    currentBill: (amount: number) => METRICS_TEMPLATES.revenue(amount),
  },
  reseller: {
    totalCommission: (amount: number, change?: string) => METRICS_TEMPLATES.revenue(amount, change),
    activeCustomers: (count: number) => METRICS_TEMPLATES.customers(count),
  },
  technician: METRICS_TEMPLATES,
} as const;
