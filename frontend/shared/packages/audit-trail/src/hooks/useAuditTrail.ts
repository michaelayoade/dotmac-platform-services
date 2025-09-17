import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useCallback } from 'react';
import type { AuditEvent, AuditEventFilter, ComplianceReport, ExportFormat } from '../types';
import { useAuditTrailContext } from '../providers/AuditTrailProvider';

export interface UseAuditTrailOptions {
  autoRefresh?: boolean;
  refreshInterval?: number;
  pageSize?: number;
}

export function useAuditTrail({
  autoRefresh = true,
  refreshInterval = 30000, // 30 seconds
  pageSize = 50,
}: UseAuditTrailOptions = {}) {
  const { apiClient, config } = useAuditTrailContext();
  const queryClient = useQueryClient();

  // Fetch audit events with filtering
  const {
    data: auditData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['audit-events'],
    queryFn: async () => {
      const response = await apiClient.get('/api/audit/events', {
        params: { limit: pageSize }
      });
      return response.data;
    },
    refetchInterval: autoRefresh ? refreshInterval : undefined,
    staleTime: refreshInterval / 2,
  });

  // Search audit events
  const searchEvents = useCallback(
    async (filter: AuditEventFilter): Promise<AuditEvent[]> => {
      const response = await apiClient.post('/api/audit/search', filter);
      return response.data.events;
    },
    [apiClient]
  );

  // Get compliance report
  const {
    data: complianceReport,
    isLoading: isLoadingCompliance,
    refetch: refetchCompliance,
  } = useQuery({
    queryKey: ['compliance-report'],
    queryFn: async (): Promise<ComplianceReport> => {
      const response = await apiClient.get('/api/audit/compliance-report');
      return response.data;
    },
    refetchInterval: autoRefresh ? refreshInterval * 2 : undefined, // Less frequent
  });

  // Create audit event
  const createAuditEvent = useMutation({
    mutationFn: async (event: Omit<AuditEvent, 'id' | 'timestamp'>) => {
      const response = await apiClient.post('/api/audit/events', event);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['audit-events'] });
      queryClient.invalidateQueries({ queryKey: ['compliance-report'] });
    },
  });

  // Export audit data
  const exportAuditData = useMutation({
    mutationFn: async ({
      format,
      filter,
      dateRange,
    }: {
      format: ExportFormat;
      filter?: AuditEventFilter;
      dateRange?: { start: string; end: string };
    }) => {
      const response = await apiClient.post('/api/audit/export', {
        format,
        filter,
        dateRange,
      }, {
        responseType: 'blob',
      });
      return response.data;
    },
  });

  // Get audit statistics
  const {
    data: auditStats,
    isLoading: isLoadingStats,
  } = useQuery({
    queryKey: ['audit-stats'],
    queryFn: async () => {
      const response = await apiClient.get('/api/audit/statistics');
      return response.data;
    },
    refetchInterval: autoRefresh ? refreshInterval : undefined,
  });

  // Log user action (convenience method)
  const logUserAction = useCallback(
    (action: string, resource: string, details?: Record<string, any>) => {
      createAuditEvent.mutate({
        category: 'user_action',
        level: 'info',
        action,
        resource,
        actor: config.currentUserId || 'anonymous',
        details: details || {},
        source: 'frontend',
      });
    },
    [createAuditEvent, config.currentUserId]
  );

  // Log security event
  const logSecurityEvent = useCallback(
    (event: string, severity: 'low' | 'medium' | 'high' | 'critical', details?: Record<string, any>) => {
      createAuditEvent.mutate({
        category: 'security',
        level: severity === 'critical' ? 'error' : severity === 'high' ? 'warn' : 'info',
        action: event,
        resource: 'system',
        actor: config.currentUserId || 'system',
        details: {
          severity,
          ...details,
        },
        source: 'security_monitor',
      });
    },
    [createAuditEvent, config.currentUserId]
  );

  // Get events by user
  const getEventsByUser = useCallback(
    async (userId: string, limit = 50): Promise<AuditEvent[]> => {
      const response = await apiClient.get(`/api/audit/users/${userId}/events`, {
        params: { limit }
      });
      return response.data.events;
    },
    [apiClient]
  );

  // Get events by resource
  const getEventsByResource = useCallback(
    async (resource: string, limit = 50): Promise<AuditEvent[]> => {
      const response = await apiClient.get(`/api/audit/resources/${resource}/events`, {
        params: { limit }
      });
      return response.data.events;
    },
    [apiClient]
  );

  // Detect anomalies
  const {
    data: anomalies,
    isLoading: isLoadingAnomalies,
  } = useQuery({
    queryKey: ['audit-anomalies'],
    queryFn: async () => {
      const response = await apiClient.get('/api/audit/anomalies');
      return response.data;
    },
    refetchInterval: autoRefresh ? refreshInterval * 3 : undefined, // Even less frequent
  });

  return {
    // Data
    events: auditData?.events || [],
    totalEvents: auditData?.total || 0,
    complianceReport,
    auditStats,
    anomalies: anomalies?.alerts || [],

    // Loading states
    isLoading,
    isLoadingCompliance,
    isLoadingStats,
    isLoadingAnomalies,
    isCreating: createAuditEvent.isPending,
    isExporting: exportAuditData.isPending,

    // Error states
    error,
    createError: createAuditEvent.error,
    exportError: exportAuditData.error,

    // Actions
    refetch,
    refetchCompliance,
    searchEvents,
    createAuditEvent: createAuditEvent.mutate,
    exportAuditData: exportAuditData.mutate,

    // Convenience methods
    logUserAction,
    logSecurityEvent,
    getEventsByUser,
    getEventsByResource,

    // Computed values
    recentEvents: auditData?.events?.slice(0, 10) || [],
    criticalEvents: auditData?.events?.filter((e: AuditEvent) => e.level === 'error') || [],
    securityEvents: auditData?.events?.filter((e: AuditEvent) => e.category === 'security') || [],
    userActionEvents: auditData?.events?.filter((e: AuditEvent) => e.category === 'user_action') || [],

    // Compliance metrics
    complianceScore: complianceReport?.score || 0,
    complianceIssues: complianceReport?.issues || [],
    lastAuditDate: complianceReport?.lastAuditDate,

    // Statistics
    eventsToday: auditStats?.eventsToday || 0,
    eventsThisWeek: auditStats?.eventsThisWeek || 0,
    eventsThisMonth: auditStats?.eventsThisMonth || 0,
    topUsers: auditStats?.topUsers || [],
    topResources: auditStats?.topResources || [],
    eventsByCategory: auditStats?.eventsByCategory || {},
  };
}