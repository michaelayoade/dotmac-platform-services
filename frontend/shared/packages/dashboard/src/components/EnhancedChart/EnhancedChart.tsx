/**
 * Enhanced Chart Component
 * Leverages existing @dotmac/primitives UniversalChart for DRY compliance
 * Adds real-time data capabilities and portal-specific configurations
 */

import React, { useMemo, useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { RefreshCw, Download, Maximize2, TrendingUp } from 'lucide-react';
import { UniversalChart, type UniversalChartProps } from '@dotmac/primitives';
import { useWebSocket } from '@dotmac/headless';
import { useNotifications } from '@dotmac/notifications';
import type { PortalVariant } from '../../types';
import { cn } from '../../utils/cn';

// Map dashboard portal variants to primitives chart variants
const VARIANT_MAPPING: Record<
  PortalVariant,
  keyof (typeof import('@dotmac/primitives'))['UniversalChart']['prototype']
> = {
  admin: 'admin',
  customer: 'customer',
  reseller: 'reseller',
  technician: 'technician',
  management: 'management',
};

export interface EnhancedChartProps extends Omit<UniversalChartProps, 'variant'> {
  /** Dashboard portal variant */
  variant: PortalVariant;
  /** Enable real-time data updates */
  realTime?: boolean;
  /** WebSocket event type for real-time data */
  eventType?: string;
  /** Show chart controls (export, fullscreen, etc.) */
  showControls?: boolean;
  /** Enable automatic data refresh */
  autoRefresh?: boolean;
  /** Refresh interval in milliseconds */
  refreshInterval?: number;
  /** Custom data transformation for real-time updates */
  transformRealTimeData?: (rawData: any) => UniversalChartProps['data'];
  /** Error handler */
  onError?: (error: string) => void;
}

export const EnhancedChart: React.FC<EnhancedChartProps> = ({
  variant,
  data: initialData,
  realTime = false,
  eventType = 'chart_data_update',
  showControls = false,
  autoRefresh = false,
  refreshInterval = 30000,
  transformRealTimeData,
  onError,
  title,
  subtitle,
  className,
  ...chartProps
}) => {
  const [chartData, setChartData] = useState(initialData);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Use existing WebSocket system for real-time updates
  const { isConnected, subscribe, sendMessage } = useWebSocket({
    reconnectInterval: 3000,
    maxReconnectAttempts: 5,
  });

  // Use existing notification system
  const { showToast } = useNotifications();

  // Subscribe to real-time chart data updates
  useEffect(() => {
    if (!realTime || !eventType) return;

    const unsubscribe = subscribe(eventType, (rawData: any) => {
      try {
        const newData = transformRealTimeData ? transformRealTimeData(rawData) : rawData;

        setChartData(newData);
        setLastUpdate(new Date());

        showToast({
          type: 'success',
          title: 'Chart Updated',
          message: 'New data received',
          duration: 2000,
        });
      } catch (err) {
        const errorMessage = `Failed to update chart data: ${err}`;
        console.error('[EnhancedChart]', errorMessage);
        onError?.(errorMessage);
      }
    });

    return unsubscribe;
  }, [realTime, eventType, subscribe, transformRealTimeData, onError, showToast]);

  // Auto refresh functionality
  useEffect(() => {
    if (!autoRefresh || !refreshInterval) return;

    const interval = setInterval(() => {
      if (realTime && isConnected) {
        // Request fresh data via WebSocket
        sendMessage({
          type: 'request',
          event: eventType,
          data: { chart_id: title || 'chart', timestamp: new Date().toISOString() },
        });
      }
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, realTime, isConnected, sendMessage, eventType, title]);

  // Manual refresh function
  const handleRefresh = () => {
    setIsRefreshing(true);

    if (realTime && isConnected) {
      sendMessage({
        type: 'request',
        event: eventType,
        data: { chart_id: title || 'chart', force_refresh: true },
      });
    }

    setTimeout(() => setIsRefreshing(false), 1000);
  };

  // Export chart data
  const handleExport = () => {
    if (!chartData || !chartData.length) return;

    try {
      // Convert chart data to CSV format
      const headers = ['Label'];
      const firstDataPoint = chartData[0];
      Object.keys(firstDataPoint || {}).forEach((key) => {
        if (key !== 'name' && key !== 'x') {
          headers.push(key);
        }
      });

      const csvContent = [
        headers.join(','),
        ...chartData.map((row: any) => {
          const values = [row.name || row.x || ''];
          headers.slice(1).forEach((header) => {
            values.push(row[header] || '');
          });
          return values.join(',');
        }),
      ].join('\n');

      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${title || 'chart'}-data.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      showToast({
        type: 'success',
        title: 'Export Complete',
        message: 'Chart data exported successfully',
        duration: 3000,
      });
    } catch (err) {
      showToast({
        type: 'error',
        title: 'Export Failed',
        message: 'Failed to export chart data',
        duration: 3000,
      });
    }
  };

  // Enhanced title with real-time indicator
  const enhancedTitle = useMemo(() => {
    if (!realTime || !isConnected || !lastUpdate) return title;

    return (
      <div className='flex items-center justify-between'>
        <span>{title}</span>
        <div className='flex items-center gap-2 text-sm text-gray-500'>
          <div className='flex items-center gap-1'>
            <div className='w-2 h-2 bg-green-500 rounded-full animate-pulse' />
            <span>Live</span>
          </div>
          <span>•</span>
          <span>{lastUpdate.toLocaleTimeString()}</span>
        </div>
      </div>
    );
  }, [title, realTime, isConnected, lastUpdate]);

  // Control buttons
  const chartActions = useMemo(() => {
    if (!showControls) return [];

    const actions = [];

    // Refresh action
    if (realTime || autoRefresh) {
      actions.push({
        id: 'refresh',
        label: 'Refresh Data',
        icon: RefreshCw,
        onClick: handleRefresh,
      });
    }

    // Export action
    actions.push({
      id: 'export',
      label: 'Export CSV',
      icon: Download,
      onClick: handleExport,
    });

    // Fullscreen action (placeholder)
    actions.push({
      id: 'fullscreen',
      label: 'Fullscreen',
      icon: Maximize2,
      onClick: () => {
        showToast({
          type: 'info',
          title: 'Fullscreen',
          message: 'Fullscreen view coming soon',
          duration: 2000,
        });
      },
    });

    return actions;
  }, [showControls, realTime, autoRefresh, handleRefresh, handleExport, showToast]);

  // Enhanced subtitle with data stats
  const enhancedSubtitle = useMemo(() => {
    if (!chartData || !chartData.length) return subtitle;

    const dataPointCount = chartData.length;
    const seriesCount = Object.keys(chartData[0] || {}).filter(
      (key) => key !== 'name' && key !== 'x' && typeof (chartData[0] as any)?.[key] === 'number'
    ).length;

    const stats = `${dataPointCount} points • ${seriesCount} series`;

    return subtitle ? `${subtitle} • ${stats}` : stats;
  }, [subtitle, chartData]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={cn('relative', className)}
    >
      {/* Real-time status indicator */}
      {realTime && isConnected && (
        <div className='absolute top-4 right-4 z-10'>
          <motion.div
            className='flex items-center gap-1 px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium'
            animate={{
              scale: [1, 1.05, 1],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
          >
            <div className='w-2 h-2 bg-green-500 rounded-full' />
            <span>Live</span>
          </motion.div>
        </div>
      )}

      {/* Loading overlay for refresh */}
      {isRefreshing && (
        <div className='absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center z-20 rounded-lg'>
          <div className='flex items-center gap-2'>
            <RefreshCw className='w-5 h-5 text-blue-500 animate-spin' />
            <span className='text-sm text-gray-600'>Refreshing...</span>
          </div>
        </div>
      )}

      {/* Use existing UniversalChart from @dotmac/primitives */}
      <UniversalChart
        {...chartProps}
        data={chartData}
        variant={VARIANT_MAPPING[variant] as any}
        title={typeof enhancedTitle === 'string' ? enhancedTitle : String(enhancedTitle)}
        {...(typeof enhancedSubtitle === 'string' && { subtitle: enhancedSubtitle })}
        actions={chartActions as any}
        className={cn('transition-opacity duration-300', isRefreshing && 'opacity-50')}
      />
    </motion.div>
  );
};

// Configuration helpers for common chart setups (DRY approach)
export const getDefaultChartConfig = (type: 'line' | 'area' | 'bar' | 'pie', realTime = true) => ({
  type,
  realTime: type === 'pie' ? false : realTime,
  autoRefresh: realTime,
  showControls: true,
});

export const CHART_PRESETS = {
  realTimeMetrics: getDefaultChartConfig('line', true),
  usageTrends: getDefaultChartConfig('area', true),
  comparisons: getDefaultChartConfig('bar', true),
  distributions: getDefaultChartConfig('pie', false),
} as const;
