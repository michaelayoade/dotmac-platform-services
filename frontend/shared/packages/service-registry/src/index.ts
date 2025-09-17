/**
 * @dotmac/service-registry
 *
 * Service discovery and health monitoring for DotMac Framework
 * Provides React hooks and components for interacting with the backend service registry
 */

// Main hooks
export { useServiceRegistry } from './hooks/useServiceRegistry';
export { useServiceHealth } from './hooks/useServiceHealth';
export { useServiceDiscovery } from './hooks/useServiceDiscovery';

// Components
export { ServiceHealthIndicator } from './components/ServiceHealthIndicator';
export { ServiceList } from './components/ServiceList';
export { ServiceMonitorDashboard } from './components/ServiceMonitorDashboard';

// Context and providers
export { ServiceRegistryProvider, useServiceRegistryContext } from './providers/ServiceRegistryProvider';

// Types
export type {
  ServiceInfo,
  ServiceStatus,
  HealthCheck,
  ServiceMetrics,
  ServiceRegistryConfig,
  LoadBalancingStrategy,
  ServiceTag,
} from './types';

// Utilities
export { createServiceClient } from './utils/serviceClient';
export { formatServiceUptime, formatServiceHealth } from './utils/formatters';