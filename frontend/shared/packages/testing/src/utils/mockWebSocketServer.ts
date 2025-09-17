/**
 * Mock WebSocket server for testing real-time features
 * Simulates Socket.io server behavior for collaboration and network monitoring
 */

import { EventEmitter } from 'events';
import { mockCollaborationWebSocketEvents } from '@dotmac/collaboration/src/__tests__/mocks/collaborationApiMocks';
import { mockWebSocketEvents } from '@dotmac/network/src/__tests__/mocks/networkApiMocks';

export type MockSocketNamespace =
  | 'collaboration'
  | 'network-topology'
  | 'network-monitoring'
  | 'network-alerts'
  | 'geographic-data';

export interface MockSocketConnection {
  id: string;
  namespace: MockSocketNamespace;
  auth?: Record<string, any>;
  subscriptions: Set<string>;
  emit: (event: string, data?: any) => void;
  on: (event: string, handler: (data?: any) => void) => void;
  disconnect: () => void;
}

export class MockWebSocketServer extends EventEmitter {
  private connections = new Map<string, MockSocketConnection>();
  private namespaces = new Set<MockSocketNamespace>();
  private eventSimulationIntervals = new Map<string, NodeJS.Timeout>();

  constructor() {
    super();
    this.setupNamespaces();
  }

  private setupNamespaces() {
    const namespaces: MockSocketNamespace[] = [
      'collaboration',
      'network-topology',
      'network-monitoring',
      'network-alerts',
      'geographic-data',
    ];

    namespaces.forEach((namespace) => {
      this.namespaces.add(namespace);
    });
  }

  // Simulate client connection
  connect(namespace: MockSocketNamespace, auth?: Record<string, any>): MockSocketConnection {
    const connectionId = `conn_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    const connection: MockSocketConnection = {
      id: connectionId,
      namespace,
      auth,
      subscriptions: new Set(),
      emit: (event: string, data?: any) => {
        this.handleClientEvent(connectionId, event, data);
      },
      on: (event: string, handler: (data?: any) => void) => {
        this.on(`${connectionId}:${event}`, handler);
      },
      disconnect: () => {
        this.disconnect(connectionId);
      },
    };

    this.connections.set(connectionId, connection);

    // Simulate connection established
    setTimeout(() => {
      this.emitToConnection(connectionId, 'connect');
      this.emit('client_connected', { connectionId, namespace, auth });
    }, 10);

    return connection;
  }

  // Handle events from client
  private handleClientEvent(connectionId: string, event: string, data?: any) {
    const connection = this.connections.get(connectionId);
    if (!connection) return;

    console.log(`[MockWebSocket] Client ${connectionId} emitted: ${event}`, data);

    switch (connection.namespace) {
      case 'collaboration':
        this.handleCollaborationEvent(connectionId, event, data);
        break;
      case 'network-topology':
        this.handleNetworkTopologyEvent(connectionId, event, data);
        break;
      case 'network-monitoring':
        this.handleNetworkMonitoringEvent(connectionId, event, data);
        break;
      case 'network-alerts':
        this.handleNetworkAlertsEvent(connectionId, event, data);
        break;
      case 'geographic-data':
        this.handleGeographicDataEvent(connectionId, event, data);
        break;
    }
  }

  // Collaboration namespace event handlers
  private handleCollaborationEvent(connectionId: string, event: string, data?: any) {
    switch (event) {
      case 'join_document':
        this.subscribeToDocument(connectionId, data?.document_id);
        this.emitToConnection(connectionId, 'document_joined', {
          document_id: data?.document_id,
          user_count: this.getDocumentUserCount(data?.document_id),
        });
        this.broadcastToDocument(
          data?.document_id,
          'user_joined',
          {
            user_id: data?.user_id,
            document_id: data?.document_id,
            joined_at: new Date().toISOString(),
          },
          connectionId
        );
        break;

      case 'leave_document':
        this.unsubscribeFromDocument(connectionId, data?.document_id);
        this.broadcastToDocument(
          data?.document_id,
          'user_left',
          {
            user_id: data?.user_id,
            document_id: data?.document_id,
            left_at: new Date().toISOString(),
          },
          connectionId
        );
        break;

      case 'apply_operation':
        this.simulateOperationTransform(connectionId, data);
        break;

      case 'update_cursor':
        this.broadcastToDocument(
          data?.document_id,
          'cursor_moved',
          {
            user_id: data?.user_id,
            document_id: data?.document_id,
            cursor_position: data?.cursor_position,
            timestamp: new Date().toISOString(),
          },
          connectionId
        );
        break;

      case 'update_selection':
        this.broadcastToDocument(
          data?.document_id,
          'selection_changed',
          {
            user_id: data?.user_id,
            document_id: data?.document_id,
            selection: data?.selection,
            timestamp: new Date().toISOString(),
          },
          connectionId
        );
        break;
    }
  }

  // Network topology namespace event handlers
  private handleNetworkTopologyEvent(connectionId: string, event: string, data?: any) {
    switch (event) {
      case 'subscribe':
        this.subscribeToTenant(connectionId, data?.tenant_id);
        this.emitToConnection(connectionId, 'subscribed', {
          tenant_id: data?.tenant_id,
          include_metrics: data?.include_metrics,
        });
        this.startTopologySimulation(connectionId, data?.tenant_id);
        break;

      case 'unsubscribe':
        this.unsubscribeFromTenant(connectionId, data?.tenant_id);
        this.stopEventSimulation(`topology_${connectionId}`);
        break;
    }
  }

  // Network monitoring namespace event handlers
  private handleNetworkMonitoringEvent(connectionId: string, event: string, data?: any) {
    switch (event) {
      case 'subscribe_monitoring':
        this.subscribeToTenant(connectionId, data?.tenant_id);
        this.emitToConnection(connectionId, 'monitoring_subscribed', {
          tenant_id: data?.tenant_id,
          alert_thresholds: data?.alert_thresholds,
        });
        this.startMonitoringSimulation(connectionId, data?.tenant_id);
        break;

      case 'unsubscribe_monitoring':
        this.unsubscribeFromTenant(connectionId, data?.tenant_id);
        this.stopEventSimulation(`monitoring_${connectionId}`);
        break;
    }
  }

  // Network alerts namespace event handlers
  private handleNetworkAlertsEvent(connectionId: string, event: string, data?: any) {
    switch (event) {
      case 'subscribe_alerts':
        this.subscribeToTenant(connectionId, data?.tenant_id);
        this.startAlertsSimulation(connectionId, data?.tenant_id);
        break;
    }
  }

  // Geographic data namespace event handlers
  private handleGeographicDataEvent(connectionId: string, event: string, data?: any) {
    switch (event) {
      case 'subscribe_geographic':
        this.subscribeToTenant(connectionId, data?.tenant_id);
        this.startGeographicSimulation(connectionId, data?.tenant_id);
        break;
    }
  }

  // Subscription management
  private subscribeToDocument(connectionId: string, documentId: string) {
    const connection = this.connections.get(connectionId);
    if (connection) {
      connection.subscriptions.add(`document:${documentId}`);
    }
  }

  private unsubscribeFromDocument(connectionId: string, documentId: string) {
    const connection = this.connections.get(connectionId);
    if (connection) {
      connection.subscriptions.delete(`document:${documentId}`);
    }
  }

  private subscribeToTenant(connectionId: string, tenantId: string) {
    const connection = this.connections.get(connectionId);
    if (connection) {
      connection.subscriptions.add(`tenant:${tenantId}`);
    }
  }

  private unsubscribeFromTenant(connectionId: string, tenantId: string) {
    const connection = this.connections.get(connectionId);
    if (connection) {
      connection.subscriptions.delete(`tenant:${tenantId}`);
    }
  }

  // Event simulation
  private simulateOperationTransform(connectionId: string, operationData: any) {
    // Simulate small processing delay
    setTimeout(
      () => {
        this.emitToConnection(connectionId, 'operation_applied', {
          operation_id: `op_${Date.now()}`,
          applied: true,
          sequence_number: Math.floor(Math.random() * 10000),
          transformed_operation: {
            ...operationData.operation,
            timestamp: new Date().toISOString(),
          },
        });

        // Broadcast to other users in the same document
        this.broadcastToDocument(
          operationData.document_id,
          'operation_applied',
          {
            document_id: operationData.document_id,
            operation: operationData.operation,
            sequence_number: Math.floor(Math.random() * 10000),
            timestamp: new Date().toISOString(),
          },
          connectionId
        );

        // Simulate occasional conflicts (10% chance)
        if (Math.random() < 0.1) {
          setTimeout(() => {
            this.broadcastToDocument(
              operationData.document_id,
              'conflict_detected',
              mockCollaborationWebSocketEvents['conflict_detected'](operationData.document_id)
            );
          }, 100);
        }
      },
      50 + Math.random() * 100
    ); // 50-150ms delay
  }

  private startTopologySimulation(connectionId: string, tenantId: string) {
    const intervalId = setInterval(
      () => {
        const events = ['node_updated', 'link_updated', 'topology_metrics_updated'];
        const randomEvent = events[Math.floor(Math.random() * events.length)];

        let eventData;
        switch (randomEvent) {
          case 'node_updated':
            eventData = mockWebSocketEvents['node_updated']('core-01');
            break;
          case 'link_updated':
            eventData = mockWebSocketEvents['link_updated']('link-01');
            break;
          case 'topology_metrics_updated':
            eventData = {
              total_nodes: 4 + Math.floor(Math.random() * 3),
              total_links: 3 + Math.floor(Math.random() * 2),
              network_diameter: 3,
              average_path_length: 2.1 + Math.random(),
              clustering_coefficient: Math.random(),
              redundancy_score: Math.random(),
            };
            break;
        }

        this.broadcastToTenant(tenantId, randomEvent, eventData);
      },
      3000 + Math.random() * 7000
    ); // Every 3-10 seconds

    this.eventSimulationIntervals.set(`topology_${connectionId}`, intervalId);
  }

  private startMonitoringSimulation(connectionId: string, tenantId: string) {
    const intervalId = setInterval(
      () => {
        const events = [
          'performance_data',
          'alert_created',
          'node_status_changed',
          'link_utilization_updated',
        ];
        const randomEvent = events[Math.floor(Math.random() * events.length)];

        let eventData;
        switch (randomEvent) {
          case 'performance_data':
            eventData = mockWebSocketEvents['performance_data']();
            break;
          case 'alert_created':
            eventData = mockWebSocketEvents['alert_created']();
            break;
          case 'node_status_changed':
            eventData = mockWebSocketEvents['node_status_changed']('core-01');
            break;
          case 'link_utilization_updated':
            eventData = mockWebSocketEvents['link_utilization_updated']('link-01');
            break;
        }

        this.broadcastToTenant(tenantId, randomEvent, eventData);
      },
      2000 + Math.random() * 3000
    ); // Every 2-5 seconds

    this.eventSimulationIntervals.set(`monitoring_${connectionId}`, intervalId);
  }

  private startAlertsSimulation(connectionId: string, tenantId: string) {
    const intervalId = setInterval(
      () => {
        const events = ['alert_created', 'alert_updated', 'alert_resolved'];
        const randomEvent = events[Math.floor(Math.random() * events.length)];
        const eventData = mockWebSocketEvents[randomEvent as keyof typeof mockWebSocketEvents]();

        this.broadcastToTenant(tenantId, randomEvent, eventData);
      },
      15000 + Math.random() * 45000
    ); // Every 15-60 seconds

    this.eventSimulationIntervals.set(`alerts_${connectionId}`, intervalId);
  }

  private startGeographicSimulation(connectionId: string, tenantId: string) {
    const intervalId = setInterval(
      () => {
        const events = ['coverage_updated', 'service_area_changed', 'route_optimized'];
        const randomEvent = events[Math.floor(Math.random() * events.length)];

        const eventData = {
          tenant_id: tenantId,
          event_type: randomEvent,
          timestamp: new Date().toISOString(),
          data: {},
        };

        this.broadcastToTenant(tenantId, randomEvent, eventData);
      },
      30000 + Math.random() * 30000
    ); // Every 30-60 seconds

    this.eventSimulationIntervals.set(`geographic_${connectionId}`, intervalId);
  }

  private stopEventSimulation(simulationKey: string) {
    const intervalId = this.eventSimulationIntervals.get(simulationKey);
    if (intervalId) {
      clearInterval(intervalId);
      this.eventSimulationIntervals.delete(simulationKey);
    }
  }

  // Broadcasting methods
  private emitToConnection(connectionId: string, event: string, data?: any) {
    this.emit(`${connectionId}:${event}`, data);
  }

  private broadcastToDocument(
    documentId: string,
    event: string,
    data?: any,
    excludeConnectionId?: string
  ) {
    this.connections.forEach((connection, connectionId) => {
      if (connectionId === excludeConnectionId) return;
      if (connection.subscriptions.has(`document:${documentId}`)) {
        this.emitToConnection(connectionId, event, data);
      }
    });
  }

  private broadcastToTenant(
    tenantId: string,
    event: string,
    data?: any,
    excludeConnectionId?: string
  ) {
    this.connections.forEach((connection, connectionId) => {
      if (connectionId === excludeConnectionId) return;
      if (connection.subscriptions.has(`tenant:${tenantId}`)) {
        this.emitToConnection(connectionId, event, data);
      }
    });
  }

  // Utility methods
  private getDocumentUserCount(documentId: string): number {
    let count = 0;
    this.connections.forEach((connection) => {
      if (connection.subscriptions.has(`document:${documentId}`)) {
        count++;
      }
    });
    return count;
  }

  // Disconnect a client
  disconnect(connectionId: string) {
    const connection = this.connections.get(connectionId);
    if (!connection) return;

    // Stop any running simulations
    this.stopEventSimulation(`topology_${connectionId}`);
    this.stopEventSimulation(`monitoring_${connectionId}`);
    this.stopEventSimulation(`alerts_${connectionId}`);
    this.stopEventSimulation(`geographic_${connectionId}`);

    // Emit disconnect event
    this.emitToConnection(connectionId, 'disconnect');

    // Clean up
    this.connections.delete(connectionId);
    this.emit('client_disconnected', { connectionId });
  }

  // Cleanup all connections
  cleanup() {
    this.connections.forEach((_, connectionId) => {
      this.disconnect(connectionId);
    });
    this.eventSimulationIntervals.forEach((interval) => {
      clearInterval(interval);
    });
    this.eventSimulationIntervals.clear();
  }

  // Get connection info
  getConnectionInfo() {
    return {
      total_connections: this.connections.size,
      namespaces: Array.from(this.namespaces),
      connections: Array.from(this.connections.entries()).map(([id, conn]) => ({
        id,
        namespace: conn.namespace,
        subscriptions: Array.from(conn.subscriptions),
        auth: conn.auth,
      })),
    };
  }
}

// Singleton instance for testing
export const mockWebSocketServer = new MockWebSocketServer();

// Helper function to create mock Socket.io client
export function createMockSocketClient(namespace: MockSocketNamespace, auth?: Record<string, any>) {
  return mockWebSocketServer.connect(namespace, auth);
}
