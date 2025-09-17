import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useCallback } from 'react';
import type { ServiceInfo, ServiceDiscoveryFilter } from '../types';
import { useServiceRegistryContext } from '../providers/ServiceRegistryProvider';

export function useServiceRegistry() {
  const { apiClient, config } = useServiceRegistryContext();
  const queryClient = useQueryClient();

  // Fetch all services
  const {
    data: services,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['services'],
    queryFn: async (): Promise<ServiceInfo[]> => {
      const response = await apiClient.get('/api/service-registry/services');
      return response.data;
    },
    refetchInterval: config.refreshInterval,
    staleTime: config.refreshInterval / 2,
  });

  // Discover services with filters
  const discoverServices = useCallback(
    async (filter: ServiceDiscoveryFilter): Promise<ServiceInfo[]> => {
      const response = await apiClient.post('/api/service-registry/discover', filter);
      return response.data;
    },
    [apiClient]
  );

  // Get specific service
  const getService = useCallback(
    async (serviceName: string, strategy?: string): Promise<ServiceInfo | null> => {
      try {
        const response = await apiClient.get(`/api/service-registry/services/${serviceName}`, {
          params: { strategy },
        });
        return response.data;
      } catch (error: any) {
        if (error.response?.status === 404) {
          return null;
        }
        throw error;
      }
    },
    [apiClient]
  );

  // Register a service (for self-registration)
  const registerService = useMutation({
    mutationFn: async (serviceData: Partial<ServiceInfo>) => {
      const response = await apiClient.post('/api/service-registry/register', serviceData);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['services'] });
    },
  });

  // Deregister a service
  const deregisterService = useMutation({
    mutationFn: async (serviceId: string) => {
      await apiClient.delete(`/api/service-registry/services/${serviceId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['services'] });
    },
  });

  // Update service metadata
  const updateService = useMutation({
    mutationFn: async ({ serviceId, metadata }: { serviceId: string; metadata: Record<string, any> }) => {
      const response = await apiClient.patch(`/api/service-registry/services/${serviceId}`, {
        metadata,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['services'] });
    },
  });

  // Service statistics
  const { data: stats } = useQuery({
    queryKey: ['service-stats'],
    queryFn: async () => {
      const response = await apiClient.get('/api/service-registry/stats');
      return response.data;
    },
    refetchInterval: 30000, // Refresh stats every 30 seconds
  });

  return {
    // Data
    services: services || [],
    stats,

    // Loading states
    isLoading,
    isRegistering: registerService.isPending,
    isDeregistering: deregisterService.isPending,
    isUpdating: updateService.isPending,

    // Error states
    error,
    registerError: registerService.error,
    deregisterError: deregisterService.error,
    updateError: updateService.error,

    // Actions
    refetch,
    discoverServices,
    getService,
    registerService: registerService.mutate,
    deregisterService: deregisterService.mutate,
    updateService: updateService.mutate,

    // Computed values
    healthyServices: services?.filter(s => s.status === 'healthy') || [],
    unhealthyServices: services?.filter(s => s.status === 'unhealthy') || [],
    totalServices: services?.length || 0,
    healthPercentage: services?.length
      ? Math.round((services.filter(s => s.status === 'healthy').length / services.length) * 100)
      : 0,
  };
}