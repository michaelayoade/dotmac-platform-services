/**
 * Real-Time ActivityFeed Component
 * Leverages existing @dotmac/headless WebSocket system and ActivityFeed component for DRY compliance
 * Extends ActivityFeed with live updates, notifications, and real-time status indicators
 */

import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Wifi, WifiOff, RefreshCw, Bell, BellOff, AlertCircle } from 'lucide-react';
import {
  ActivityFeed,
  type ActivityFeedProps,
  ActivityFeedPresets,
} from '../ActivityFeed/ActivityFeed';
import { useWebSocket } from '@dotmac/headless';
import { useNotifications } from '@dotmac/notifications';
import type { PortalVariant, Activity } from '../../types';
import { cn } from '../../utils/cn';

export interface RealTimeActivityFeedProps
  extends Omit<ActivityFeedProps, 'activities' | 'onRefresh'> {
  /** Portal variant for WebSocket connection */
  variant: PortalVariant;
  /** WebSocket events to subscribe to for activity updates */
  eventTypes: string[];
  /** Static fallback activities if real-time fails */
  fallbackActivities?: Activity[];
  /** Show connection status indicator */
  showConnectionStatus?: boolean;
  /** Show notification controls */
  showNotificationControls?: boolean;
  /** Custom activity transformer function */
  transformActivity?: (eventType: string, rawData: any) => Activity | null;
  /** Maximum number of activities to keep in memory */
  maxActivities?: number;
  /** Error handler for connection issues */
  onError?: (error: string) => void;
  /** Enable toast notifications for new activities */
  enableActivityNotifications?: boolean;
}

export const RealTimeActivityFeed: React.FC<RealTimeActivityFeedProps> = ({
  variant,
  eventTypes,
  fallbackActivities = [],
  showConnectionStatus = true,
  showNotificationControls = false,
  transformActivity,
  maxActivities = 50,
  onError,
  enableActivityNotifications = false,
  className,
  ...props
}) => {
  const [activities, setActivities] = useState<Activity[]>(fallbackActivities);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [notificationsEnabled, setNotificationsEnabled] = useState(enableActivityNotifications);
  const [activityCounts, setActivityCounts] = useState({ total: 0, new: 0 });

  // Use existing WebSocket system from @dotmac/headless
  const { isConnected, isConnecting, error, connectionQuality, subscribe, lastMessage } =
    useWebSocket({
      reconnectInterval: 3000,
      maxReconnectAttempts: 5,
      heartbeatInterval: 30000,
    });

  // Use existing notification system from @dotmac/notifications
  const { showToast } = useNotifications();

  // Default activity transformer based on portal type
  const defaultTransformActivity = useCallback(
    (eventType: string, rawData: any): Activity | null => {
      const timestamp = new Date(rawData.timestamp || Date.now());

      // Portal-specific activity transformations
      switch (variant) {
        case 'admin':
          if (eventType === 'customer_signup') {
            return ActivityFeedPresets.admin.customerSignup(
              rawData.customer_email || 'Unknown',
              rawData.plan || 'Basic'
            );
          }
          if (eventType === 'network_alert' && rawData.severity === 'error') {
            return ActivityFeedPresets.admin.networkOutage(rawData.location || 'Unknown Location');
          }
          break;

        case 'customer':
          if (eventType === 'bill_generated') {
            return ActivityFeedPresets.customer.billGenerated(
              rawData.customerId || 'unknown',
              parseFloat(rawData.amount) || 0
            );
          }
          if (eventType === 'payment_processed') {
            return ActivityFeedPresets.customer.paymentProcessed(
              rawData.customerId || 'unknown',
              parseFloat(rawData.amount) || 0
            );
          }
          break;

        case 'reseller':
          if (eventType === 'commission_earned') {
            return ActivityFeedPresets.reseller.commissionEarned(
              rawData.resellerId || 'unknown',
              parseFloat(rawData.amount) || 0
            );
          }
          if (eventType === 'lead_converted') {
            return ActivityFeedPresets.reseller.leadConverted(
              rawData.leadId || 'unknown',
              rawData.plan || 'Basic'
            );
          }
          break;

        case 'management':
          if (eventType === 'tenant_created') {
            return ActivityFeedPresets.management.tenantCreated(
              rawData.tenant_name || 'Unknown',
              rawData.user_name || 'System'
            );
          }
          if (eventType === 'system_alert') {
            return ActivityFeedPresets.management.systemAlert(
              rawData.message || 'Unknown alert',
              rawData.severity || 'warning'
            );
          }
          break;

        default:
          // Generic activity for technician and other portals
          return {
            id: `${eventType}-${timestamp.getTime()}`,
            type: rawData.type || 'info',
            title: rawData.title || 'Activity Update',
            description: rawData.description || rawData.message || 'New activity recorded',
            timestamp,
            userName: rawData.user_name || rawData.userName,
            metadata: {
              eventType,
              source: variant,
              ...rawData.metadata,
            },
          };
      }

      return null;
    },
    [variant]
  );

  // Subscribe to activity events
  useEffect(() => {
    const unsubscribeFunctions = eventTypes.map((eventType) => {
      return subscribe(eventType, (rawData: any) => {
        try {
          let newActivity: Activity | null = null;

          if (transformActivity) {
            newActivity = transformActivity(eventType, rawData);
          } else {
            newActivity = defaultTransformActivity(eventType, rawData);
          }

          if (newActivity) {
            setActivities((prev) => {
              // Remove duplicate activities (same ID)
              const filtered = prev.filter((activity) => activity.id !== newActivity!.id);
              const updated = [newActivity!, ...filtered].slice(0, maxActivities);
              return updated;
            });

            setLastUpdate(new Date());
            setActivityCounts((prev) => ({
              total: prev.total + 1,
              new: prev.new + 1,
            }));

            // Show toast notification for new activity
            if (notificationsEnabled && isConnected) {
              showToast({
                type:
                  newActivity.type === 'error'
                    ? 'error'
                    : newActivity.type === 'warning'
                      ? 'warning'
                      : newActivity.type === 'success'
                        ? 'success'
                        : 'info',
                title: 'New Activity',
                message: newActivity.title,
                duration: 4000,
              });
            }
          }
        } catch (err) {
          const errorMessage = `Failed to process ${eventType} activity: ${err}`;
          console.error('[RealTimeActivityFeed]', errorMessage);
          onError?.(errorMessage);

          if (notificationsEnabled) {
            showToast({
              type: 'error',
              title: 'Activity Processing Error',
              message: errorMessage,
              duration: 5000,
            });
          }
        }
      });
    });

    return () => {
      unsubscribeFunctions.forEach((unsubscribe) => unsubscribe());
    };
  }, [
    eventTypes,
    subscribe,
    transformActivity,
    defaultTransformActivity,
    maxActivities,
    onError,
    notificationsEnabled,
    showToast,
    isConnected,
  ]);

  // Handle WebSocket errors
  useEffect(() => {
    if (error && onError) {
      onError(error);
    }
  }, [error, onError]);

  // Manual refresh function
  const handleRefresh = useCallback(() => {
    if (isConnected) {
      // Clear new activity counter
      setActivityCounts((prev) => ({ ...prev, new: 0 }));

      // Request fresh data for all event types
      eventTypes.forEach((eventType) => {
        // This would be sent to the WebSocket server to request fresh data
        // Implementation depends on the backend WebSocket protocol
      });

      showToast({
        type: 'info',
        title: 'Activity Feed',
        message: 'Refreshing activities...',
        duration: 2000,
      });
    }
  }, [isConnected, eventTypes, showToast]);

  // Connection status indicator
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
          tooltip: `Connection quality: ${connectionQuality} • ${eventTypes.length} events monitored`,
        };
      }

      return {
        icon: WifiOff,
        color: 'text-gray-500',
        bgColor: 'bg-gray-100',
        label: 'Offline',
        tooltip: 'Using cached activities',
      };
    };

    const { icon: StatusIcon, color, bgColor, label, tooltip } = getStatusConfig();

    return (
      <div className='absolute top-3 right-3 z-10' title={tooltip}>
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
          {/* New activity indicator */}
          {activityCounts.new > 0 && isConnected && (
            <span className='ml-1 px-1 py-0.5 bg-red-500 text-white rounded text-[10px] leading-none'>
              {activityCounts.new > 99 ? '99+' : activityCounts.new}
            </span>
          )}
        </motion.div>
      </div>
    );
  };

  // Notification controls
  const NotificationControls = () => {
    if (!showNotificationControls) return null;

    return (
      <div className='absolute top-3 right-16 z-10'>
        <motion.button
          initial={{ scale: 0, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          onClick={() => setNotificationsEnabled(!notificationsEnabled)}
          className={cn(
            'flex items-center justify-center w-7 h-7 rounded-full text-xs font-medium transition-colors',
            notificationsEnabled
              ? 'bg-blue-100 text-blue-600 hover:bg-blue-200'
              : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
          )}
          title={`${notificationsEnabled ? 'Disable' : 'Enable'} activity notifications`}
        >
          {notificationsEnabled ? <Bell className='w-3 h-3' /> : <BellOff className='w-3 h-3' />}
        </motion.button>
      </div>
    );
  };

  // Enhanced title with activity stats
  const enhancedConfig = useMemo(
    () => ({
      ...props.config,
      showFilters: props.config?.showFilters ?? true,
      showUserAvatars: props.config?.showUserAvatars ?? true,
      maxItems: props.config?.maxItems ?? 10,
    }),
    [props.config]
  );

  return (
    <div className={cn('relative', className)}>
      <ConnectionStatus />
      <NotificationControls />

      {/* Real-time pulse indicator for new activities */}
      {isConnected && connectionQuality === 'excellent' && activityCounts.new > 0 && (
        <motion.div
          className={cn(
            'absolute -top-1 -right-1 w-3 h-3 rounded-full z-20',
            variant === 'admin' && 'bg-blue-500',
            variant === 'customer' && 'bg-green-500',
            variant === 'reseller' && 'bg-purple-500',
            variant === 'technician' && 'bg-orange-500',
            variant === 'management' && 'bg-indigo-500'
          )}
          animate={{
            scale: [1, 1.3, 1],
            opacity: [0.7, 1, 0.7],
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />
      )}

      <ActivityFeed
        activities={activities}
        variant={variant}
        config={enhancedConfig}
        loading={isConnecting && activities.length === 0}
        onRefresh={handleRefresh}
        {...props}
      />
    </div>
  );
};

// Configuration helpers for portal-specific event types (DRY approach)
export const getPortalEventTypes = (variant: PortalVariant): string[] => {
  const eventTypeMap: Record<PortalVariant, string[]> = {
    admin: ['customer_signup', 'network_alert', 'service_outage', 'system_maintenance'],
    customer: ['bill_generated', 'payment_processed', 'service_update', 'support_ticket_update'],
    reseller: ['commission_earned', 'lead_converted', 'customer_signup', 'payout_processed'],
    management: ['tenant_created', 'system_alert', 'tenant_status_change', 'platform_update'],
    technician: ['work_order_assigned', 'work_order_completed', 'equipment_alert', 'route_update'],
  };
  return eventTypeMap[variant] || [];
};

export const getPortalActivityConfig = (variant: PortalVariant) => ({
  variant,
  eventTypes: getPortalEventTypes(variant),
  enableActivityNotifications: true,
  showNotificationControls: variant === 'management',
});
