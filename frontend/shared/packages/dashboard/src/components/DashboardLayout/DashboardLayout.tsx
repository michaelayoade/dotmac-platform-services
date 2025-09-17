/**
 * Enhanced Dashboard Layout Component
 * Leverages existing @dotmac/primitives UniversalLayout for DRY compliance
 * Adds real-time integration, metrics, and portal-specific dashboard functionality
 */

import React, { useState, useEffect, useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  Bell,
  Settings,
  Search,
  Grid as GridIcon,
  BarChart3,
  Users,
  Activity,
  AlertTriangle,
  CheckCircle,
  TrendingUp,
  Wifi,
} from 'lucide-react';
import { UniversalLayout, Container, Grid, GridItem } from '@dotmac/primitives';
import { useWebSocket } from '@dotmac/headless';
import { useNotifications } from '@dotmac/notifications';
import { RealTimeMetricsCard } from '../RealTimeMetricsCard/RealTimeMetricsCard';
import { RealTimeActivityFeed } from '../RealTimeActivityFeed/RealTimeActivityFeed';
import { EnhancedChart, getDefaultChartConfig } from '../EnhancedChart/EnhancedChart';
import type { PortalVariant, MetricsCardData } from '../../types';
import { cn } from '../../utils/cn';

interface DashboardQuickAction {
  id: string;
  label: string;
  icon: React.ComponentType<any>;
  onClick: () => void;
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'danger';
  badge?: number;
}

interface DashboardWidget {
  id: string;
  title: string;
  component: React.ComponentType<any>;
  props?: any;
  gridSpan?: { cols: number; rows: number };
  order?: number;
  required?: boolean;
}

interface DashboardSystemStatus {
  overall: 'operational' | 'degraded' | 'outage';
  services: Array<{
    name: string;
    status: 'operational' | 'degraded' | 'outage';
    uptime: number;
  }>;
  alerts: number;
  lastUpdate: Date;
}

export interface DashboardLayoutProps {
  variant: PortalVariant;
  user?: {
    id: string;
    name: string;
    email: string;
    avatar?: string;
    role: string;
  };
  tenant?: {
    id: string;
    name: string;
  };
  branding?: {
    logo?: string;
    companyName: string;
    primaryColor: string;
    secondaryColor?: string;
  };

  // Dashboard-specific props
  showSystemStatus?: boolean;
  showQuickActions?: boolean;
  quickActions?: DashboardQuickAction[];
  widgets?: DashboardWidget[];
  enableRealTime?: boolean;
  refreshInterval?: number;

  // Layout customization
  compactMode?: boolean;
  showSidebar?: boolean;
  children?: React.ReactNode;

  // Event handlers
  onLogout: () => void;
  onSearch?: (query: string) => void;
  onNotificationClick?: () => void;
  onSettingsClick?: () => void;
}

// Default widgets for each portal variant
const getDefaultWidgets = (variant: PortalVariant): DashboardWidget[] => {
  const common = [
    {
      id: 'activity-feed',
      title: 'Recent Activity',
      component: RealTimeActivityFeed,
      props: { variant },
      gridSpan: { cols: 2, rows: 2 },
      order: 100,
    },
  ];

  switch (variant) {
    case 'admin':
      return [
        {
          id: 'network-status',
          title: 'Network Status',
          component: RealTimeMetricsCard,
          props: {
            variant,
            eventType: 'network_status_update',
            showConnectionStatus: true,
            enableNotifications: true,
          },
          gridSpan: { cols: 1, rows: 1 },
          order: 1,
        },
        {
          id: 'customer-count',
          title: 'Total Customers',
          component: RealTimeMetricsCard,
          props: {
            variant,
            eventType: 'customer_count_update',
            enableNotifications: false,
          },
          gridSpan: { cols: 1, rows: 1 },
          order: 2,
        },
        {
          id: 'revenue-chart',
          title: 'Revenue Trend',
          component: EnhancedChart,
          props: {
            variant,
            eventType: 'revenue_chart_update',
            ...getDefaultChartConfig('line', true),
          },
          gridSpan: { cols: 2, rows: 1 },
          order: 3,
        },
        ...common,
      ];

    case 'customer':
      return [
        {
          id: 'service-status',
          title: 'Service Status',
          component: RealTimeMetricsCard,
          props: {
            variant,
            eventType: 'service_status_update',
            showConnectionStatus: true,
            enableNotifications: true,
          },
          gridSpan: { cols: 1, rows: 1 },
          order: 1,
        },
        {
          id: 'current-bill',
          title: 'Current Bill',
          component: RealTimeMetricsCard,
          props: {
            variant,
            eventType: 'billing_update',
            enableNotifications: false,
          },
          gridSpan: { cols: 1, rows: 1 },
          order: 2,
        },
        {
          id: 'usage-chart',
          title: 'Data Usage',
          component: EnhancedChart,
          props: {
            variant,
            eventType: 'usage_chart_update',
            ...getDefaultChartConfig('area', true),
          },
          gridSpan: { cols: 2, rows: 1 },
          order: 3,
        },
        ...common,
      ];

    case 'reseller':
      return [
        {
          id: 'commission-total',
          title: 'Total Commission',
          component: RealTimeMetricsCard,
          props: {
            variant,
            eventType: 'commission_total_update',
            showConnectionStatus: true,
            enableNotifications: true,
          },
          gridSpan: { cols: 1, rows: 1 },
          order: 1,
        },
        {
          id: 'active-customers',
          title: 'Active Customers',
          component: RealTimeMetricsCard,
          props: {
            variant,
            eventType: 'reseller_customer_count',
            enableNotifications: false,
          },
          gridSpan: { cols: 1, rows: 1 },
          order: 2,
        },
        {
          id: 'sales-chart',
          title: 'Sales Performance',
          component: EnhancedChart,
          props: {
            variant,
            eventType: 'sales_chart_update',
            ...getDefaultChartConfig('bar', true),
          },
          gridSpan: { cols: 2, rows: 1 },
          order: 3,
        },
        ...common,
      ];

    case 'management':
      return [
        {
          id: 'tenant-count',
          title: 'Active Tenants',
          component: RealTimeMetricsCard,
          props: {
            variant,
            eventType: 'tenant_count_update',
            showConnectionStatus: true,
            enableNotifications: true,
          },
          gridSpan: { cols: 1, rows: 1 },
          order: 1,
        },
        {
          id: 'system-health',
          title: 'System Health',
          component: RealTimeMetricsCard,
          props: {
            variant,
            eventType: 'system_health_update',
            enableNotifications: true,
          },
          gridSpan: { cols: 1, rows: 1 },
          order: 2,
        },
        {
          id: 'platform-metrics',
          title: 'Platform Metrics',
          component: EnhancedChart,
          props: {
            variant,
            eventType: 'platform_metrics_update',
            ...getDefaultChartConfig('line', true),
          },
          gridSpan: { cols: 2, rows: 1 },
          order: 3,
        },
        ...common,
      ];

    case 'technician':
      return [
        {
          id: 'work-orders',
          title: 'Pending Work Orders',
          component: RealTimeMetricsCard,
          props: {
            variant,
            eventType: 'work_order_count_update',
            showConnectionStatus: true,
            enableNotifications: true,
          },
          gridSpan: { cols: 1, rows: 1 },
          order: 1,
        },
        {
          id: 'completion-rate',
          title: 'Completion Rate',
          component: RealTimeMetricsCard,
          props: {
            variant,
            eventType: 'completion_rate_update',
            enableNotifications: false,
          },
          gridSpan: { cols: 1, rows: 1 },
          order: 2,
        },
        {
          id: 'location-map',
          title: 'Service Locations',
          component: EnhancedChart,
          props: {
            variant,
            eventType: 'location_update',
            ...getDefaultChartConfig('line', true), // Would be a map component in real implementation
          },
          gridSpan: { cols: 2, rows: 1 },
          order: 3,
        },
        ...common,
      ];

    default:
      return common;
  }
};

// Default quick actions for each portal variant
const getDefaultQuickActions = (variant: PortalVariant): DashboardQuickAction[] => {
  const common = [
    {
      id: 'search',
      label: 'Search',
      icon: Search,
      onClick: () => {},
      variant: 'secondary' as const,
    },
  ];

  switch (variant) {
    case 'admin':
      return [
        {
          id: 'add-customer',
          label: 'Add Customer',
          icon: Users,
          onClick: () => {},
          variant: 'primary' as const,
        },
        {
          id: 'network-tools',
          label: 'Network Tools',
          icon: Activity,
          onClick: () => {},
          variant: 'secondary' as const,
        },
        ...common,
      ];

    case 'customer':
      return [
        {
          id: 'pay-bill',
          label: 'Pay Bill',
          icon: CheckCircle,
          onClick: () => {},
          variant: 'primary' as const,
        },
        {
          id: 'view-usage',
          label: 'View Usage',
          icon: BarChart3,
          onClick: () => {},
          variant: 'secondary' as const,
        },
        ...common,
      ];

    case 'reseller':
      return [
        {
          id: 'add-lead',
          label: 'Add Lead',
          icon: Users,
          onClick: () => {},
          variant: 'primary' as const,
        },
        {
          id: 'view-commissions',
          label: 'Commissions',
          icon: TrendingUp,
          onClick: () => {},
          variant: 'secondary' as const,
        },
        ...common,
      ];

    case 'management':
      return [
        {
          id: 'create-tenant',
          label: 'Create Tenant',
          icon: GridIcon,
          onClick: () => {},
          variant: 'primary' as const,
        },
        {
          id: 'system-status',
          label: 'System Status',
          icon: Activity,
          onClick: () => {},
          variant: 'secondary' as const,
        },
        ...common,
      ];

    case 'technician':
      return [
        {
          id: 'create-work-order',
          label: 'New Work Order',
          icon: GridIcon,
          onClick: () => {},
          variant: 'primary' as const,
        },
        {
          id: 'check-equipment',
          label: 'Equipment Check',
          icon: Settings,
          onClick: () => {},
          variant: 'secondary' as const,
        },
        ...common,
      ];

    default:
      return common;
  }
};

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({
  variant,
  user,
  tenant,
  branding,
  showSystemStatus = true,
  showQuickActions = true,
  quickActions,
  widgets,
  enableRealTime = true,
  refreshInterval = 30000,
  compactMode = false,
  showSidebar = true,
  children,
  onLogout,
  onSearch,
  onNotificationClick,
  onSettingsClick,
}) => {
  const [systemStatus, setSystemStatus] = useState<DashboardSystemStatus>({
    overall: 'operational',
    services: [],
    alerts: 0,
    lastUpdate: new Date(),
  });

  // Use existing WebSocket system for real-time updates
  const { isConnected, connectionQuality } = useWebSocket({
    reconnectInterval: 3000,
    maxReconnectAttempts: 5,
  });

  // Use existing notification system
  const { showToast } = useNotifications();

  // Prepare final widgets and actions
  const finalWidgets = useMemo(() => {
    const defaultWidgets = getDefaultWidgets(variant);
    const customWidgets = widgets || [];

    // Merge and sort widgets
    const allWidgets = [...defaultWidgets, ...customWidgets];
    return allWidgets.sort((a, b) => (a.order || 0) - (b.order || 0));
  }, [variant, widgets]);

  const finalQuickActions = useMemo(() => {
    return quickActions || getDefaultQuickActions(variant);
  }, [variant, quickActions]);

  // Header actions for UniversalLayout
  const headerActions = useMemo(() => {
    const actions = [];

    if (onNotificationClick) {
      actions.push({
        id: 'notifications',
        label: 'Notifications',
        icon: Bell,
        onClick: onNotificationClick,
        badge: systemStatus.alerts,
      });
    }

    if (onSettingsClick) {
      actions.push({
        id: 'settings',
        label: 'Settings',
        icon: Settings,
        onClick: onSettingsClick,
      });
    }

    return actions;
  }, [onNotificationClick, onSettingsClick, systemStatus.alerts]);

  // System status indicator
  const SystemStatusIndicator = () => {
    if (!showSystemStatus) return null;

    const statusConfig = {
      operational: {
        color: 'text-green-600 bg-green-100',
        icon: CheckCircle,
        label: 'All Systems Operational',
      },
      degraded: {
        color: 'text-yellow-600 bg-yellow-100',
        icon: AlertTriangle,
        label: 'Some Systems Degraded',
      },
      outage: {
        color: 'text-red-600 bg-red-100',
        icon: AlertTriangle,
        label: 'System Outage',
      },
    };

    const config = statusConfig[systemStatus.overall];
    const StatusIcon = config.icon;

    return (
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className='mb-6'>
        <div className='flex items-center justify-between bg-white rounded-lg border border-gray-200 px-4 py-3 shadow-sm'>
          <div className='flex items-center gap-3'>
            <div
              className={cn('flex items-center justify-center w-8 h-8 rounded-full', config.color)}
            >
              <StatusIcon className='w-3.5 h-3.5' />
            </div>
            <div>
              <p className='text-sm font-medium text-gray-900'>{config.label}</p>
              <p className='text-xs text-gray-500'>
                Last updated: {systemStatus.lastUpdate.toLocaleTimeString()}
              </p>
            </div>
          </div>

          {/* Connection quality indicator */}
          {enableRealTime && (
            <div className='flex items-center gap-2 text-xs'>
              <Wifi
                className={cn(
                  'w-3 h-3',
                  connectionQuality === 'excellent'
                    ? 'text-green-500'
                    : connectionQuality === 'good'
                      ? 'text-blue-500'
                      : connectionQuality === 'poor'
                        ? 'text-orange-500'
                        : 'text-gray-400'
                )}
              />
              <span className='text-gray-600 capitalize'>{connectionQuality}</span>
            </div>
          )}
        </div>
      </motion.div>
    );
  };

  // Quick actions section
  const QuickActions = () => {
    if (!showQuickActions || !finalQuickActions.length) return null;

    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className='mb-6'
      >
        <div className='flex flex-wrap gap-3'>
          {finalQuickActions.map((action) => {
            const IconComponent = action.icon;
            const variantStyles = {
              primary: 'bg-blue-600 hover:bg-blue-700 text-white border-blue-600',
              secondary: 'bg-white hover:bg-gray-50 text-gray-700 border-gray-300',
              success: 'bg-green-600 hover:bg-green-700 text-white border-green-600',
              warning: 'bg-yellow-600 hover:bg-yellow-700 text-white border-yellow-600',
              danger: 'bg-red-600 hover:bg-red-700 text-white border-red-600',
            };

            return (
              <motion.button
                key={action.id}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={action.onClick}
                className={cn(
                  'relative flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm transition-colors border',
                  variantStyles[action.variant || 'secondary']
                )}
              >
                <IconComponent className='w-4 h-4' />
                {action.label}
                {action.badge && action.badge > 0 && (
                  <span className='absolute -top-1 -right-1 flex items-center justify-center w-5 h-5 bg-red-500 text-white text-xs font-bold rounded-full'>
                    {action.badge > 99 ? '99+' : action.badge}
                  </span>
                )}
              </motion.button>
            );
          })}
        </div>
      </motion.div>
    );
  };

  // Widget grid
  const WidgetGrid = () => {
    if (!finalWidgets.length) return null;

    return (
      <div
        className={cn(
          'grid gap-6',
          compactMode
            ? 'grid-cols-1 lg:grid-cols-3'
            : 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4'
        )}
      >
        {finalWidgets.map((widget) => {
          const WidgetComponent = widget.component;
          const gridSpan = widget.gridSpan || { cols: 1, rows: 1 };

          const spanClasses = compactMode
            ? ''
            : `${gridSpan.cols > 1 ? `md:col-span-${Math.min(gridSpan.cols, 2)} lg:col-span-${Math.min(gridSpan.cols, 3)} xl:col-span-${gridSpan.cols}` : ''}
             ${gridSpan.rows > 1 ? `row-span-${gridSpan.rows}` : ''}`;

          return (
            <motion.div
              key={widget.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 + (widget.order || 0) * 0.05 }}
              className={spanClasses}
            >
              <WidgetComponent title={widget.title} {...(widget.props || {})} />
            </motion.div>
          );
        })}
      </div>
    );
  };

  return (
    <UniversalLayout
      variant={variant}
      {...(user && { user })}
      {...(branding && { branding })}
      {...(tenant && { tenant })}
      onLogout={onLogout}
      layoutType='dashboard'
      showSidebar={showSidebar}
      showHeader={true}
      headerActions={headerActions as any}
      maxWidth='7xl'
      padding='lg'
    >
      <div className='space-y-6'>
        <SystemStatusIndicator />
        <QuickActions />
        <WidgetGrid />
        {children}
      </div>
    </UniversalLayout>
  );
};
