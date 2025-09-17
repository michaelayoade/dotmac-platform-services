# @dotmac/service-registry

Service discovery and health monitoring for DotMac Framework applications.

## Features

- **Service Discovery**: Find and connect to services dynamically
- **Health Monitoring**: Real-time health status tracking
- **Load Balancing**: Built-in load balancing strategies
- **React Integration**: Hooks and components for easy integration

## Installation

```bash
pnpm install @dotmac/service-registry
```

## Quick Start

### Provider Setup

```tsx
import { ServiceRegistryProvider } from '@dotmac/service-registry';
import { httpClient } from '@dotmac/http-client';

function App() {
  return (
    <ServiceRegistryProvider
      config={{
        apiClient: httpClient,
        refreshInterval: 30000, // 30 seconds
        defaultUserId: 'current-user-id',
      }}
    >
      <YourApp />
    </ServiceRegistryProvider>
  );
}
```

### Using Hooks

```tsx
import { useServiceRegistry, useServiceHealth } from '@dotmac/service-registry';

function ServiceDashboard() {
  const {
    services,
    isLoading,
    healthyServices,
    unhealthyServices,
    totalServices,
    healthPercentage,
    refetch,
  } = useServiceRegistry();

  const { getServiceHealth } = useServiceHealth();

  if (isLoading) {
    return <div>Loading services...</div>;
  }

  return (
    <div>
      <h2>Service Registry ({totalServices} services)</h2>
      <p>Health: {healthPercentage}%</p>

      <div>
        <h3>Healthy Services ({healthyServices.length})</h3>
        {healthyServices.map(service => (
          <div key={service.id}>
            {service.name} - {service.version}
          </div>
        ))}
      </div>

      <div>
        <h3>Unhealthy Services ({unhealthyServices.length})</h3>
        {unhealthyServices.map(service => (
          <div key={service.id}>
            {service.name} - {service.status}
          </div>
        ))}
      </div>
    </div>
  );
}
```

### Service Discovery

```tsx
import { useServiceDiscovery } from '@dotmac/service-registry';

function ApiConnector() {
  const { discoverService, getServiceEndpoint } = useServiceDiscovery();

  const handleApiCall = async () => {
    // Discover a service instance
    const userService = await discoverService('user-service', {
      version: '^2.0.0',
      region: 'us-east-1',
      strategy: 'round-robin',
    });

    if (userService) {
      const endpoint = getServiceEndpoint(userService);
      // Make API call to the discovered service
      const response = await fetch(`${endpoint}/api/users`);
    }
  };

  return (
    <button onClick={handleApiCall}>
      Call User Service
    </button>
  );
}
```

### Components

```tsx
import {
  ServiceHealthIndicator,
  ServiceList,
  ServiceMonitorDashboard,
} from '@dotmac/service-registry';

function MonitoringPage() {
  return (
    <div>
      {/* Individual service health indicator */}
      <ServiceHealthIndicator
        serviceName="user-service"
        showDetails={true}
      />

      {/* List of all services */}
      <ServiceList
        filter={{ status: 'healthy' }}
        sortBy="name"
        onServiceClick={(service) => console.log(service)}
      />

      {/* Complete monitoring dashboard */}
      <ServiceMonitorDashboard
        refreshInterval={10000}
        showMetrics={true}
        showLogs={false}
      />
    </div>
  );
}
```

## API Reference

### Hooks

#### `useServiceRegistry()`

Main hook for service registry operations.

**Returns:**
- `services`: Array of all registered services
- `stats`: Service registry statistics
- `isLoading`: Loading state
- `error`: Error state if any
- `refetch()`: Manually refresh services
- `registerService()`: Register a new service
- `deregisterService()`: Remove a service
- `updateService()`: Update service metadata

#### `useServiceHealth(serviceName?)`

Monitor health status of services.

**Parameters:**
- `serviceName` (optional): Specific service to monitor

**Returns:**
- `healthStatus`: Current health status
- `healthHistory`: Historical health data
- `isHealthy`: Boolean health state
- `lastHealthCheck`: Timestamp of last check
- `checkHealth()`: Manually trigger health check

#### `useServiceDiscovery()`

Discover and connect to services.

**Returns:**
- `discoverService()`: Find service instances
- `getServiceEndpoint()`: Get service URL
- `getLoadBalancer()`: Get load balancer for service
- `createServiceClient()`: Create HTTP client for service

### Components

#### `<ServiceHealthIndicator />`

**Props:**
- `serviceName`: Name of the service to monitor
- `showDetails`: Show detailed health information
- `size`: 'small' | 'medium' | 'large'
- `onStatusChange`: Callback when status changes

#### `<ServiceList />`

**Props:**
- `filter`: Filter criteria for services
- `sortBy`: Field to sort by
- `groupBy`: Field to group by
- `onServiceClick`: Callback when service is clicked
- `showHealth`: Display health indicators
- `showMetrics`: Display service metrics

#### `<ServiceMonitorDashboard />`

**Props:**
- `refreshInterval`: Auto-refresh interval (ms)
- `showMetrics`: Display performance metrics
- `showLogs`: Display service logs
- `showAlerts`: Display active alerts
- `layout`: 'grid' | 'list' | 'compact'

### Types

```typescript
interface ServiceInfo {
  id: string;
  name: string;
  version: string;
  status: ServiceStatus;
  endpoint: string;
  health: HealthCheck;
  metadata: Record<string, any>;
  tags: ServiceTag[];
  registeredAt: string;
  lastHeartbeat: string;
}

type ServiceStatus = 'healthy' | 'unhealthy' | 'unknown' | 'starting' | 'stopping';

interface HealthCheck {
  status: ServiceStatus;
  checks: Array<{
    name: string;
    status: ServiceStatus;
    message?: string;
    duration?: number;
  }>;
  timestamp: string;
}
```

## Configuration

```typescript
interface ServiceRegistryConfig {
  apiClient: any; // HTTP client instance
  refreshInterval?: number; // Auto-refresh interval (ms)
  defaultUserId?: string; // Current user ID
  loadBalancing?: {
    strategy: 'round-robin' | 'random' | 'least-connections';
    healthCheck: boolean;
  };
  caching?: {
    enabled: boolean;
    ttl: number; // Cache TTL in seconds
  };
}
```

## Load Balancing Strategies

- **Round Robin**: Distribute requests evenly across instances
- **Random**: Randomly select service instances
- **Least Connections**: Route to instance with fewest active connections
- **Health-Aware**: Only route to healthy instances

## Error Handling

```tsx
import { useServiceRegistry } from '@dotmac/service-registry';

function ServiceManager() {
  const { error, services, registerService } = useServiceRegistry();

  const handleRegister = async (serviceData) => {
    try {
      await registerService(serviceData);
    } catch (err) {
      console.error('Service registration failed:', err);
    }
  };

  if (error) {
    return <div>Error: {error.message}</div>;
  }

  return <div>Services: {services.length}</div>;
}
```