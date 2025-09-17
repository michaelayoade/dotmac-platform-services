export interface ServiceInfo {
  id: string;
  name: string;
  version: string;
  host: string;
  port: number;
  status: ServiceStatus;
  health_score: number;
  tags: string[];
  metadata: Record<string, any>;
  registered_at: string;
  last_health_check: string;
  health_check_url?: string;
  uptime: number;
}

export type ServiceStatus = 'healthy' | 'unhealthy' | 'unknown' | 'degraded';

export interface HealthCheck {
  service_id: string;
  status: ServiceStatus;
  health_score: number;
  response_time: number;
  checked_at: string;
  details?: Record<string, any>;
}

export interface ServiceMetrics {
  service_id: string;
  requests_per_second: number;
  average_response_time: number;
  error_rate: number;
  cpu_usage?: number;
  memory_usage?: number;
  uptime: number;
  collected_at: string;
}

export interface ServiceRegistryConfig {
  apiBaseUrl: string;
  websocketUrl?: string;
  refreshInterval: number;
  healthCheckInterval: number;
  enableRealTimeUpdates: boolean;
}

export type LoadBalancingStrategy = 'round_robin' | 'least_connections' | 'random' | 'health_weighted';

export interface ServiceTag {
  key: string;
  value: string;
}

export interface ServiceDiscoveryFilter {
  name?: string;
  tags?: string[];
  status?: ServiceStatus[];
  version?: string;
}

export interface ServiceHealthHistory {
  service_id: string;
  health_checks: HealthCheck[];
  timespan: 'hour' | 'day' | 'week';
}

export interface ServiceAlert {
  id: string;
  service_id: string;
  service_name: string;
  alert_type: 'health' | 'performance' | 'availability';
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  created_at: string;
  resolved_at?: string;
}