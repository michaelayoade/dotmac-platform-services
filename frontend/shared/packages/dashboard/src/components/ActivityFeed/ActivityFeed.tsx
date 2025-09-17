/**
 * Universal ActivityFeed Component
 * Production-ready, portal-agnostic activity display
 * DRY pattern: Same component, different activities across all portals
 */

import React, { useState, useMemo } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Clock,
  Filter,
  RefreshCw,
  ChevronDown,
  AlertCircle,
  CheckCircle,
  InfoIcon,
  AlertTriangle,
  User,
} from 'lucide-react';
import { Card, Button, Input } from '@dotmac/primitives';
import type { Activity, PortalVariant, ActivityFeedConfig } from '../../types';
import { cn } from '../../utils/cn';
import { formatDistanceToNow } from 'date-fns';

const activityFeedVariants = cva('w-full', {
  variants: {
    variant: {
      admin: 'border-blue-200',
      customer: 'border-green-200',
      reseller: 'border-purple-200',
      technician: 'border-orange-200',
      management: 'border-indigo-200',
    },
  },
});

const activityItemVariants = cva(
  'flex items-start gap-3 p-4 border-b border-gray-100 last:border-b-0 transition-colors hover:bg-gray-50/50',
  {
    variants: {
      type: {
        info: 'hover:bg-blue-50/30',
        success: 'hover:bg-green-50/30',
        warning: 'hover:bg-yellow-50/30',
        error: 'hover:bg-red-50/30',
      },
    },
  }
);

const getActivityIcon = (type: Activity['type']) => {
  const iconMap = {
    info: InfoIcon,
    success: CheckCircle,
    warning: AlertTriangle,
    error: AlertCircle,
  };

  return iconMap[type] || InfoIcon;
};

const getActivityColor = (type: Activity['type'], variant: PortalVariant) => {
  const baseColors = {
    info: 'text-blue-600 bg-blue-100',
    success: 'text-green-600 bg-green-100',
    warning: 'text-yellow-600 bg-yellow-100',
    error: 'text-red-600 bg-red-100',
  };

  const variantColors = {
    admin: {
      info: 'text-blue-700 bg-blue-200',
      success: 'text-green-700 bg-green-200',
      warning: 'text-yellow-700 bg-yellow-200',
      error: 'text-red-700 bg-red-200',
    },
    customer: {
      info: 'text-blue-600 bg-blue-100',
      success: 'text-green-600 bg-green-100',
      warning: 'text-yellow-600 bg-yellow-100',
      error: 'text-red-600 bg-red-100',
    },
    reseller: {
      info: 'text-purple-600 bg-purple-100',
      success: 'text-green-600 bg-green-100',
      warning: 'text-yellow-600 bg-yellow-100',
      error: 'text-red-600 bg-red-100',
    },
    technician: {
      info: 'text-orange-600 bg-orange-100',
      success: 'text-green-600 bg-green-100',
      warning: 'text-yellow-600 bg-yellow-100',
      error: 'text-red-600 bg-red-100',
    },
    management: {
      info: 'text-indigo-600 bg-indigo-100',
      success: 'text-green-600 bg-green-100',
      warning: 'text-yellow-600 bg-yellow-100',
      error: 'text-red-600 bg-red-100',
    },
  };

  return variantColors[variant]?.[type] || baseColors[type];
};

export interface ActivityFeedProps extends VariantProps<typeof activityFeedVariants> {
  activities: Activity[];
  variant: PortalVariant;
  config?: Partial<ActivityFeedConfig>;
  className?: string;
  loading?: boolean;
  onRefresh?: () => void;
  onActivityClick?: (activity: Activity) => void;
}

export const ActivityFeed: React.FC<ActivityFeedProps> = ({
  activities,
  variant,
  config = {},
  className,
  loading = false,
  onRefresh,
  onActivityClick,
  ...props
}) => {
  const [filterType, setFilterType] = useState<Activity['type'] | 'all'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [expanded, setExpanded] = useState(false);

  const finalConfig: ActivityFeedConfig = {
    showFilters: true,
    showUserAvatars: true,
    maxItems: 10,
    ...config,
  };

  const filteredActivities = useMemo(() => {
    let filtered = activities;

    // Filter by type
    if (filterType !== 'all') {
      filtered = filtered.filter((activity) => activity.type === filterType);
    }

    // Filter by search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (activity) =>
          activity.title.toLowerCase().includes(query) ||
          activity.description.toLowerCase().includes(query) ||
          activity.userName?.toLowerCase().includes(query)
      );
    }

    // Sort by timestamp (newest first)
    filtered.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

    // Limit results
    const limit = expanded ? filtered.length : finalConfig.maxItems;
    return filtered.slice(0, limit);
  }, [activities, filterType, searchQuery, expanded, finalConfig.maxItems]);

  const ActivityItem: React.FC<{ activity: Activity; index: number }> = ({ activity, index }) => {
    const IconComponent = getActivityIcon(activity.type);
    const iconColorClass = getActivityColor(activity.type, variant);

    return (
      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.3, delay: index * 0.05 }}
        className={cn(activityItemVariants({ type: activity.type }))}
        onClick={() => onActivityClick?.(activity)}
        role={onActivityClick ? 'button' : undefined}
        tabIndex={onActivityClick ? 0 : undefined}
      >
        {/* Activity Icon */}
        <div
          className={cn(
            'flex items-center justify-center w-8 h-8 rounded-full flex-shrink-0',
            iconColorClass
          )}
        >
          <IconComponent size={14} />
        </div>

        {/* Activity Content */}
        <div className='flex-1 min-w-0'>
          <div className='flex items-start justify-between mb-1'>
            <h4 className='text-sm font-medium text-gray-900 leading-tight'>{activity.title}</h4>
            <time className='text-xs text-gray-500 flex-shrink-0 ml-2'>
              {formatDistanceToNow(new Date(activity.timestamp), { addSuffix: true })}
            </time>
          </div>

          <p className='text-sm text-gray-600 leading-relaxed mb-2'>{activity.description}</p>

          {/* User Info */}
          {activity.userName && finalConfig.showUserAvatars && (
            <div className='flex items-center gap-2'>
              <div className='flex items-center justify-center w-5 h-5 rounded-full bg-gray-200'>
                <User size={10} className='text-gray-600' />
              </div>
              <span className='text-xs text-gray-500'>{activity.userName}</span>
            </div>
          )}

          {/* Metadata */}
          {activity.metadata && Object.keys(activity.metadata).length > 0 && (
            <div className='mt-2 flex flex-wrap gap-1'>
              {Object.entries(activity.metadata)
                .slice(0, 3)
                .map(([key, value]) => (
                  <span
                    key={key}
                    className='inline-flex items-center px-2 py-1 rounded text-xs bg-gray-100 text-gray-600'
                  >
                    {key}: {String(value)}
                  </span>
                ))}
            </div>
          )}
        </div>
      </motion.div>
    );
  };

  if (loading) {
    return (
      <Card className={cn(activityFeedVariants({ variant }), className)}>
        <div className='p-6'>
          <div className='animate-pulse space-y-4'>
            <div className='flex justify-between items-center'>
              <div className='h-6 bg-gray-200 rounded w-32'></div>
              <div className='h-8 w-8 bg-gray-200 rounded'></div>
            </div>
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className='flex items-start gap-3'>
                <div className='h-8 w-8 bg-gray-200 rounded-full'></div>
                <div className='flex-1 space-y-2'>
                  <div className='h-4 bg-gray-200 rounded w-3/4'></div>
                  <div className='h-3 bg-gray-200 rounded w-1/2'></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </Card>
    );
  }

  return (
    <Card className={cn(activityFeedVariants({ variant }), className)} {...props}>
      {/* Header */}
      <div className='p-4 border-b border-gray-200'>
        <div className='flex items-center justify-between mb-3'>
          <h3 className='text-lg font-semibold text-gray-900'>Recent Activity</h3>
          <div className='flex items-center gap-2'>
            {onRefresh && (
              <Button
                variant='ghost'
                size='sm'
                onClick={onRefresh}
                className='h-8 w-8 p-0'
                disabled={loading}
              >
                <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
              </Button>
            )}
          </div>
        </div>

        {/* Filters */}
        {finalConfig.showFilters && (
          <div className='flex items-center gap-3'>
            <div className='flex-1'>
              <Input
                placeholder='Search activities...'
                value={searchQuery}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setSearchQuery(e.target.value)
                }
                className='h-8 text-sm'
              />
            </div>

            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value as Activity['type'] | 'all')}
              className='h-8 px-3 text-sm border border-gray-300 rounded-md bg-white'
            >
              <option value='all'>All Types</option>
              <option value='info'>Info</option>
              <option value='success'>Success</option>
              <option value='warning'>Warning</option>
              <option value='error'>Error</option>
            </select>
          </div>
        )}
      </div>

      {/* Activity List */}
      <div className='max-h-96 overflow-y-auto'>
        {filteredActivities.length === 0 ? (
          <div className='p-8 text-center'>
            <Clock size={24} className='mx-auto mb-2 text-gray-400' />
            <p className='text-sm text-gray-500'>
              {searchQuery || filterType !== 'all'
                ? 'No activities match your filters'
                : 'No recent activities'}
            </p>
          </div>
        ) : (
          <AnimatePresence>
            {filteredActivities.map((activity, index) => (
              <ActivityItem
                key={`${activity.id}-${activity.timestamp}`}
                activity={activity}
                index={index}
              />
            ))}
          </AnimatePresence>
        )}
      </div>

      {/* Expand/Collapse */}
      {activities.length > finalConfig.maxItems && (
        <div className='p-3 border-t border-gray-200 text-center'>
          <Button
            variant='ghost'
            size='sm'
            onClick={() => setExpanded(!expanded)}
            className='text-sm'
          >
            {expanded ? (
              <>
                Show Less
                <ChevronDown size={14} className='ml-1 rotate-180' />
              </>
            ) : (
              <>
                Show {activities.length - finalConfig.maxItems} More
                <ChevronDown size={14} className='ml-1' />
              </>
            )}
          </Button>
        </div>
      )}
    </Card>
  );
};

// DRY Activity Factory - Single function handles all activity types
export const createActivity = (
  activityType: string,
  options: {
    title: string;
    description: string;
    type?: Activity['type'];
    userName?: string;
    metadata?: Record<string, any>;
  }
): Activity => ({
  id: `${activityType}-${Date.now()}`,
  type: options.type || 'info',
  title: options.title,
  description: options.description,
  timestamp: new Date(),
  userName: options.userName || undefined,
  metadata: { activityType, ...options.metadata },
});

// Common activity templates (DRY approach)
export const ACTIVITY_TEMPLATES = {
  tenantCreated: (tenantName: string, userName: string) =>
    createActivity('tenant-created', {
      title: 'New Tenant Created',
      description: `Tenant "${tenantName}" was successfully created and configured`,
      type: 'success',
      userName,
      metadata: { tenantName, action: 'create' },
    }),

  customerSignup: (customerEmail: string, plan: string) =>
    createActivity('customer-signup', {
      title: 'New Customer Signup',
      description: `${customerEmail} signed up for ${plan} plan`,
      type: 'success',
      metadata: { customerEmail, plan, action: 'signup' },
    }),

  systemAlert: (message: string, severity: 'warning' | 'error') =>
    createActivity('system-alert', {
      title: 'System Alert',
      description: message,
      type: severity,
      metadata: { severity, source: 'system' },
    }),

  networkOutage: (location: string) =>
    createActivity('network-outage', {
      title: 'Network Outage',
      description: `Service disruption reported in ${location}`,
      type: 'error',
      metadata: { location, source: 'network' },
    }),

  billGenerated: (customerId: string, amount: number) =>
    createActivity('bill-generated', {
      title: 'Bill Generated',
      description: `Monthly bill of $${amount} generated for customer ${customerId}`,
      type: 'info',
      metadata: { customerId, amount },
    }),

  paymentProcessed: (customerId: string, amount: number) =>
    createActivity('payment-processed', {
      title: 'Payment Processed',
      description: `Payment of $${amount} received from customer ${customerId}`,
      type: 'success',
      metadata: { customerId, amount },
    }),

  commissionEarned: (resellerId: string, amount: number) =>
    createActivity('commission-earned', {
      title: 'Commission Earned',
      description: `Commission of $${amount} earned by reseller ${resellerId}`,
      type: 'success',
      metadata: { resellerId, amount },
    }),

  leadConverted: (leadId: string, plan: string) =>
    createActivity('lead-converted', {
      title: 'Lead Converted',
      description: `Lead ${leadId} converted to ${plan} plan`,
      type: 'success',
      metadata: { leadId, plan },
    }),
} as const;

// Portal-specific preset aliases (leverages existing templates)
export const ActivityFeedPresets = {
  management: ACTIVITY_TEMPLATES,
  admin: ACTIVITY_TEMPLATES,
  customer: ACTIVITY_TEMPLATES,
  reseller: ACTIVITY_TEMPLATES,
  technician: ACTIVITY_TEMPLATES,
} as const;
