/**
 * Real-Time Metrics Card Component
 * Leverages existing @dotmac/headless WebSocket system for DRY compliance
 * Integrates with existing MetricsCard and notification systems
 */

import React, { useMemo, useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Wifi, WifiOff, RefreshCw, AlertCircle } from 'lucide-react';
import { MetricsCard, type MetricsCardProps } from '../MetricsCard/MetricsCard';
import { useWebSocket } from '@dotmac/headless';
import { useNotifications } from '@dotmac/notifications';
import type { PortalVariant, MetricsCardData } from '../../types';
import { cn } from '../../utils/cn';

export interface RealTimeMetricsCardProps extends Omit<MetricsCardProps, 'data' | 'loading'> {
  /** Portal variant for WebSocket connection */
  variant: PortalVariant;
  /** WebSocket event to subscribe to */
  eventType: string;
  /** Static fallback data if real-time fails */
  fallbackData?: MetricsCardData;
  /** Show connection status indicator */
  showConnectionStatus?: boolean;
  /** Custom data transformer function */
  transformData?: (rawData: any) => MetricsCardData;
  /** Error handler for connection issues */
  onError?: (error: string) => void;
  /** Enable notifications for data updates */
  enableNotifications?: boolean;
}

export const RealTimeMetricsCard: React.FC<RealTimeMetricsCardProps> = ({
  variant,
  eventType,
  fallbackData,
  showConnectionStatus = true,
  transformData,
  onError,
  enableNotifications = false,
  className,
  ...props
}) => {
  const [metricsData, setMetricsData] = useState<MetricsCardData | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  // Use existing WebSocket system from @dotmac/headless
  const { isConnected, isConnecting, error, connectionQuality, subscribe, lastMessage } =
    useWebSocket({
      reconnectInterval: 3000,
      maxReconnectAttempts: 5,
      heartbeatInterval: 30000,
    });

  // Use existing notification system from @dotmac/notifications
  const { showToast } = useNotifications();

  // Subscribe to metrics updates
  useEffect(() => {
    const unsubscribe = subscribe(eventType, (data: any) => {
      try {
        let transformedData: MetricsCardData;

        if (transformData) {
          transformedData = transformData(data);
        } else if (data && typeof data === 'object' && data.title && data.value !== undefined) {
          transformedData = data as MetricsCardData;
        } else {
          throw new Error('Invalid data format');
        }

        setMetricsData(transformedData);
        setLastUpdate(new Date());

        // Show notification for significant changes
        if (enableNotifications && metricsData && transformedData.value !== metricsData.value) {
          showToast({
            type: 'info',
            title: `${transformedData.title} Updated`,
            message: `New value: ${transformedData.value}`,
            duration: 3000,
          });
        }
      } catch (err) {
        const errorMessage = `Failed to process ${eventType} data: ${err}`;
        console.error('[RealTimeMetricsCard]', errorMessage);
        onError?.(errorMessage);

        if (enableNotifications) {
          showToast({
            type: 'error',
            title: 'Data Processing Error',
            message: errorMessage,
            duration: 5000,
          });
        }
      }
    });

    return unsubscribe;
  }, [eventType, subscribe, transformData, onError, enableNotifications, showToast, metricsData]);

  // Handle WebSocket errors
  useEffect(() => {
    if (error && onError) {
      onError(error);
    }
  }, [error, onError]);

  // Use fallback data if no real-time data available
  const displayData = useMemo((): MetricsCardData => {
    if (metricsData) {
      // Enhance with real-time status
      return {
        ...metricsData,
        description:
          isConnected && lastUpdate
            ? `${metricsData.description || ''} • Last updated ${lastUpdate.toLocaleTimeString()}`
            : metricsData.description || 'Real-time data unavailable',
      };
    }

    if (fallbackData) {
      return {
        ...fallbackData,
        description: `${fallbackData.description || ''} • Using cached data`,
      };
    }

    // Default loading state
    return {
      title: 'Loading...',
      value: '--',
      description: 'Connecting to real-time data...',
    };
  }, [metricsData, fallbackData, isConnected, lastUpdate]);

  // Connection status indicator using existing design patterns
  const ConnectionStatus = () => {
    if (!showConnectionStatus) return null;

    const getStatusConfig = () => {
      if (error) {
        return {
          icon: AlertCircle,
          color: 'text-red-500',
          bgColor: 'bg-red-100',
          label: 'Error',
          tooltip: error,
        };
      }

      if (isConnecting) {
        return {
          icon: RefreshCw,
          color: 'text-yellow-500',
          bgColor: 'bg-yellow-100',
          label: 'Connecting',
          tooltip: 'Establishing connection...',
        };
      }

      if (isConnected) {
        const qualityColors: Record<string, string> = {
          excellent: 'text-green-500 bg-green-100',
          good: 'text-blue-500 bg-blue-100',
          poor: 'text-orange-500 bg-orange-100',
          offline: 'text-gray-500 bg-gray-100',
        };
        const qualityColor =
          qualityColors[connectionQuality] || qualityColors.offline || 'text-gray-500 bg-gray-100';
        const parts = qualityColor.split(' ');
        const textColor = parts[0] || 'text-gray-500';
        const backgroundColor = parts[1] || 'bg-gray-100';

        return {
          icon: Wifi,
          color: textColor,
          bgColor: backgroundColor,
          label: 'Live',
          tooltip: `Connection quality: ${connectionQuality}`,
        };
      }

      return {
        icon: WifiOff,
        color: 'text-gray-500',
        bgColor: 'bg-gray-100',
        label: 'Offline',
        tooltip: 'Using cached data',
      };
    };

    const { icon: StatusIcon, color, bgColor, label, tooltip } = getStatusConfig();

    return (
      <div className='absolute top-2 right-2 z-10' title={tooltip}>
        <motion.div
          initial={{ scale: 0, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className={cn(
            'flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium',
            bgColor,
            color
          )}
        >
          <StatusIcon className={cn('w-2.5 h-2.5', isConnecting ? 'animate-spin' : '')} />
          <span className='hidden sm:inline'>{label}</span>
        </motion.div>
      </div>
    );
  };

  // Animation for data updates
  const dataUpdateAnimation = {
    initial: { opacity: 0.7, scale: 0.98 },
    animate: { opacity: 1, scale: 1 },
    transition: { duration: 0.3, ease: 'easeOut' },
  };

  return (
    <div className={cn('relative', className)}>
      <ConnectionStatus />

      <AnimatePresence mode='wait'>
        <motion.div key={`${displayData.value}-${lastUpdate?.getTime()}`} {...dataUpdateAnimation}>
          <MetricsCard
            data={displayData}
            variant={variant}
            loading={isConnecting && !fallbackData && !metricsData}
            {...props}
          />
        </motion.div>
      </AnimatePresence>

      {/* Real-time pulse indicator */}
      {isConnected && connectionQuality === 'excellent' && (
        <motion.div
          className={cn(
            'absolute -top-1 -right-1 w-3 h-3 rounded-full',
            variant === 'admin' && 'bg-blue-500',
            variant === 'customer' && 'bg-green-500',
            variant === 'reseller' && 'bg-purple-500',
            variant === 'technician' && 'bg-orange-500',
            variant === 'management' && 'bg-indigo-500'
          )}
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.7, 1, 0.7],
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />
      )}
    </div>
  );
};

// Configuration helpers for common metrics transformations (DRY approach)
export const getMetricsTransformer = (type: 'network' | 'customers' | 'revenue') => {
  const transformers = {
    network: (data: any) => ({
      title: 'Network Status',
      value: `${data.uptime || 0}%`,
      trend: (data.uptime || 0) >= 99.5 ? 'up' : (data.uptime || 0) >= 99 ? 'stable' : 'down',
      change: data.uptime >= 99.5 ? 'Excellent' : data.uptime >= 99 ? 'Good' : 'Poor',
      description: `${data.activeConnections || 0} active connections`,
    }),
    customers: (data: any) => ({
      title: 'Active Customers',
      value: data.total || 0,
      change: data.change || '0',
      trend: data.trend || 'stable',
      description: `${data.newToday || 0} new today`,
    }),
    revenue: (data: any) => ({
      title: 'Monthly Revenue',
      value: `$${(data.monthly || 0).toLocaleString()}`,
      change: data.monthlyChange || '0%',
      trend: data.trend || 'stable',
      description: `$${(data.daily || 0).toLocaleString()} today`,
    }),
  };
  return transformers[type];
};

export const METRICS_CONFIGS = {
  network: { eventType: 'device_status_update', transformData: getMetricsTransformer('network') },
  customers: { eventType: 'customer_update', transformData: getMetricsTransformer('customers') },
  revenue: { eventType: 'revenue_update', transformData: getMetricsTransformer('revenue') },
} as const;
