/**
 * Test data factories for generating realistic test data
 * Provides factory functions for creating mock data for collaboration and network packages
 */

import { faker } from '@faker-js/faker';
import type {
  CollaborativeDocument,
  DocumentComment,
  DocumentSuggestion,
  User,
  UserPresence,
  DocumentConflict,
  ConflictStatus,
} from '@dotmac/collaboration/src/types';

import type {
  NetworkNode,
  NetworkLink,
  ServiceArea,
  CoverageGap,
  PerformanceMetric,
  NetworkAlert,
  NodeType,
  NodeStatus,
  LinkType,
} from '@dotmac/network/src/types';

// Collaboration Data Factories

export const UserFactory = {
  build: (overrides?: Partial<User>): User => ({
    id: faker.string.uuid(),
    name: faker.person.fullName(),
    email: faker.internet.email(),
    avatar_url: faker.image.avatar(),
    role: faker.helpers.arrayElement(['admin', 'editor', 'reviewer', 'contributor']),
    permissions: faker.helpers.arrayElements(
      ['read', 'write', 'comment', 'suggest', 'resolve_conflicts'],
      { min: 1, max: 5 }
    ),
    ...overrides,
  }),

  buildMany: (count: number, overrides?: Partial<User>): User[] =>
    Array.from({ length: count }, () => UserFactory.build(overrides)),
};

export const DocumentFactory = {
  build: (overrides?: Partial<CollaborativeDocument>): CollaborativeDocument => {
    const userId = faker.string.uuid();
    return {
      id: faker.string.uuid(),
      tenant_id: faker.string.uuid(),
      title: faker.lorem.sentence({ min: 3, max: 8 }),
      content: faker.lorem.paragraphs(3, '\n\n'),
      document_type: faker.helpers.arrayElement(['markdown', 'plaintext', 'json', 'yaml']),
      version: faker.number.int({ min: 1, max: 10 }),
      created_by: userId,
      created_at: faker.date.recent().toISOString(),
      updated_at: faker.date.recent().toISOString(),
      updated_by: faker.helpers.maybe(() => faker.string.uuid()) || userId,
      status: faker.helpers.arrayElement(['active', 'draft', 'archived', 'deleted']),
      permissions: {
        read: Array.from({ length: faker.number.int({ min: 1, max: 5 }) }, () =>
          faker.string.uuid()
        ),
        write: Array.from({ length: faker.number.int({ min: 1, max: 3 }) }, () =>
          faker.string.uuid()
        ),
        comment: Array.from({ length: faker.number.int({ min: 1, max: 4 }) }, () =>
          faker.string.uuid()
        ),
        admin: [userId],
      },
      metadata: {
        category: faker.helpers.arrayElement([
          'planning',
          'procedures',
          'documentation',
          'specifications',
        ]),
        tags: faker.helpers.arrayElements(
          ['network', 'infrastructure', 'planning', 'support', 'billing'],
          { min: 1, max: 4 }
        ),
        priority: faker.helpers.arrayElement(['low', 'medium', 'high', 'critical']),
        department: faker.helpers.arrayElement(['engineering', 'support', 'sales', 'management']),
      },
      lock_status: {
        is_locked: faker.datatype.boolean(),
        locked_by: faker.helpers.maybe(() => faker.string.uuid()) || null,
        locked_at: faker.helpers.maybe(() => faker.date.recent().toISOString()) || null,
        lock_expires_at: faker.helpers.maybe(() => faker.date.future().toISOString()) || null,
      },
      ...overrides,
    };
  },

  buildMany: (count: number, overrides?: Partial<CollaborativeDocument>): CollaborativeDocument[] =>
    Array.from({ length: count }, () => DocumentFactory.build(overrides)),
};

export const CommentFactory = {
  build: (overrides?: Partial<DocumentComment>): DocumentComment => ({
    id: faker.string.uuid(),
    document_id: faker.string.uuid(),
    user_id: faker.string.uuid(),
    content: faker.lorem.sentence({ min: 5, max: 20 }),
    position: {
      line: faker.number.int({ min: 1, max: 50 }),
      column: faker.number.int({ min: 0, max: 80 }),
      selection_start: faker.number.int({ min: 0, max: 1000 }),
      selection_end: faker.number.int({ min: 0, max: 1000 }),
    },
    thread_id: faker.string.uuid(),
    parent_comment_id: faker.helpers.maybe(() => faker.string.uuid()) || null,
    status: faker.helpers.arrayElement(['active', 'resolved', 'deleted']),
    created_at: faker.date.recent().toISOString(),
    updated_at: faker.date.recent().toISOString(),
    ...overrides,
  }),

  buildMany: (count: number, overrides?: Partial<DocumentComment>): DocumentComment[] =>
    Array.from({ length: count }, () => CommentFactory.build(overrides)),
};

export const SuggestionFactory = {
  build: (overrides?: Partial<DocumentSuggestion>): DocumentSuggestion => ({
    id: faker.string.uuid(),
    document_id: faker.string.uuid(),
    user_id: faker.string.uuid(),
    suggested_change: {
      operation: faker.helpers.arrayElement(['insert', 'replace', 'delete']),
      position: {
        line: faker.number.int({ min: 1, max: 50 }),
        column: faker.number.int({ min: 0, max: 80 }),
        selection_start: faker.number.int({ min: 0, max: 1000 }),
        selection_end: faker.number.int({ min: 0, max: 1000 }),
      },
      original_content: faker.lorem.sentence(),
      suggested_content: faker.lorem.sentence(),
    },
    reason: faker.lorem.sentence({ min: 3, max: 10 }),
    status: faker.helpers.arrayElement(['pending', 'approved', 'rejected']),
    approved_by: faker.helpers.maybe(() => faker.string.uuid()),
    approved_at: faker.helpers.maybe(() => faker.date.recent().toISOString()),
    rejected_by: faker.helpers.maybe(() => faker.string.uuid()),
    rejected_at: faker.helpers.maybe(() => faker.date.recent().toISOString()),
    rejection_reason: faker.helpers.maybe(() => faker.lorem.sentence()),
    created_at: faker.date.recent().toISOString(),
    updated_at: faker.date.recent().toISOString(),
    ...overrides,
  }),

  buildMany: (count: number, overrides?: Partial<DocumentSuggestion>): DocumentSuggestion[] =>
    Array.from({ length: count }, () => SuggestionFactory.build(overrides)),
};

export const ConflictFactory = {
  build: (overrides?: Partial<DocumentConflict>): DocumentConflict => ({
    id: faker.string.uuid(),
    document_id: faker.string.uuid(),
    position: {
      line: faker.number.int({ min: 1, max: 50 }),
      column: faker.number.int({ min: 0, max: 80 }),
      selection_start: faker.number.int({ min: 0, max: 1000 }),
      selection_end: faker.number.int({ min: 0, max: 1000 }),
    },
    conflicting_operations: Array.from({ length: 2 }, () => ({
      id: faker.string.uuid(),
      user_id: faker.string.uuid(),
      operation: faker.helpers.arrayElement(['insert', 'replace', 'delete']),
      content: faker.lorem.sentence(),
      timestamp: faker.date.recent().toISOString(),
    })),
    status: faker.helpers.enumValue(ConflictStatus),
    detected_at: faker.date.recent().toISOString(),
    resolved_at: faker.helpers.maybe(() => faker.date.recent().toISOString()) || null,
    resolved_by: faker.helpers.maybe(() => faker.string.uuid()) || null,
    resolution_strategy:
      faker.helpers.maybe(() =>
        faker.helpers.arrayElement(['manual_merge', 'accept_local', 'accept_remote', 'custom'])
      ) || null,
    ...overrides,
  }),

  buildMany: (count: number, overrides?: Partial<DocumentConflict>): DocumentConflict[] =>
    Array.from({ length: count }, () => ConflictFactory.build(overrides)),
};

export const UserPresenceFactory = {
  build: (overrides?: Partial<UserPresence>): UserPresence => ({
    user_id: faker.string.uuid(),
    document_id: faker.string.uuid(),
    status: faker.helpers.arrayElement(['active', 'idle', 'busy', 'away']),
    cursor_position: {
      line: faker.number.int({ min: 1, max: 50 }),
      column: faker.number.int({ min: 0, max: 80 }),
    },
    selection:
      faker.helpers.maybe(() => ({
        start: {
          line: faker.number.int({ min: 1, max: 50 }),
          column: faker.number.int({ min: 0, max: 80 }),
        },
        end: {
          line: faker.number.int({ min: 1, max: 50 }),
          column: faker.number.int({ min: 0, max: 80 }),
        },
      })) || null,
    last_seen: faker.date.recent().toISOString(),
    viewport: {
      start_line: faker.number.int({ min: 1, max: 20 }),
      end_line: faker.number.int({ min: 21, max: 50 }),
    },
    ...overrides,
  }),

  buildMany: (count: number, overrides?: Partial<UserPresence>): UserPresence[] =>
    Array.from({ length: count }, () => UserPresenceFactory.build(overrides)),
};

// Network Data Factories

export const NetworkNodeFactory = {
  build: (overrides?: Partial<NetworkNode>): NetworkNode => ({
    node_id: `node_${faker.string.alphanumeric(8)}`,
    node_type: faker.helpers.enumValue(NodeType),
    device_id: faker.helpers.maybe(() => `device_${faker.string.alphanumeric(6)}`),
    site_id: faker.helpers.maybe(() => `site_${faker.string.alphanumeric(6)}`),
    latitude: faker.helpers.maybe(() =>
      faker.location.latitude({ min: 35, max: 45, precision: 6 })
    ),
    longitude: faker.helpers.maybe(() =>
      faker.location.longitude({ min: -125, max: -65, precision: 6 })
    ),
    elevation: faker.helpers.maybe(() => faker.number.int({ min: 0, max: 200 })),
    ip_address: faker.helpers.maybe(() => faker.internet.ip()),
    mac_address: faker.helpers.maybe(() => faker.internet.mac()),
    hostname: faker.helpers.maybe(
      () => `${faker.string.alphanumeric(8)}.${faker.internet.domainName()}`
    ),
    manufacturer: faker.helpers.maybe(() =>
      faker.helpers.arrayElement(['Cisco', 'Juniper', 'Arista', 'HP', 'Dell', 'Ubiquiti'])
    ),
    model: faker.helpers.maybe(() => faker.string.alphanumeric(10)),
    firmware_version: faker.helpers.maybe(() => faker.system.semver()),
    bandwidth_mbps: faker.helpers.maybe(() => faker.number.int({ min: 10, max: 100000 })),
    coverage_radius_km: faker.helpers.maybe(() =>
      faker.number.float({ min: 0.1, max: 50, precision: 0.1 })
    ),
    port_count: faker.helpers.maybe(() => faker.number.int({ min: 8, max: 48 })),
    status: faker.helpers.enumValue(NodeStatus),
    last_seen_at: faker.helpers.maybe(() => faker.date.recent().toISOString()),
    uptime_percentage: faker.helpers.maybe(() =>
      faker.number.float({ min: 85, max: 100, precision: 0.1 })
    ),
    cpu_usage: faker.helpers.maybe(() => faker.number.int({ min: 0, max: 100 })),
    memory_usage: faker.helpers.maybe(() => faker.number.int({ min: 0, max: 100 })),
    temperature: faker.helpers.maybe(() => faker.number.int({ min: 20, max: 80 })),
    power_consumption: faker.helpers.maybe(() =>
      faker.number.float({ min: 5, max: 1000, precision: 0.1 })
    ),
    connected_links: Array.from(
      { length: faker.number.int({ min: 0, max: 5 }) },
      () => `link_${faker.string.alphanumeric(6)}`
    ),
    neighbor_count: faker.number.int({ min: 0, max: 10 }),
    ...overrides,
  }),

  buildMany: (count: number, overrides?: Partial<NetworkNode>): NetworkNode[] =>
    Array.from({ length: count }, () => NetworkNodeFactory.build(overrides)),
};

export const NetworkLinkFactory = {
  build: (overrides?: Partial<NetworkLink>): NetworkLink => ({
    link_id: `link_${faker.string.alphanumeric(8)}`,
    source_node_id: `node_${faker.string.alphanumeric(8)}`,
    target_node_id: `node_${faker.string.alphanumeric(8)}`,
    link_type: faker.helpers.enumValue(LinkType),
    source_port: faker.helpers.maybe(() => faker.string.alphanumeric(12)),
    target_port: faker.helpers.maybe(() => faker.string.alphanumeric(12)),
    bandwidth_mbps: faker.helpers.maybe(() => faker.number.int({ min: 10, max: 10000 })),
    latency_ms: faker.helpers.maybe(() =>
      faker.number.float({ min: 0.1, max: 100, precision: 0.1 })
    ),
    length_km: faker.helpers.maybe(() =>
      faker.number.float({ min: 0.1, max: 100, precision: 0.1 })
    ),
    cost: faker.number.int({ min: 1, max: 100 }),
    utilization_percentage: faker.helpers.maybe(() => faker.number.int({ min: 0, max: 100 })),
    packet_loss: faker.helpers.maybe(() =>
      faker.number.float({ min: 0, max: 5, precision: 0.001 })
    ),
    error_rate: faker.helpers.maybe(() =>
      faker.number.float({ min: 0, max: 1, precision: 0.0001 })
    ),
    status: faker.helpers.enumValue(NodeStatus),
    operational_status: faker.helpers.maybe(() =>
      faker.helpers.arrayElement(['up/up', 'up/down', 'down/down', 'admin-down'])
    ),
    ...overrides,
  }),

  buildMany: (count: number, overrides?: Partial<NetworkLink>): NetworkLink[] =>
    Array.from({ length: count }, () => NetworkLinkFactory.build(overrides)),
};

export const ServiceAreaFactory = {
  build: (overrides?: Partial<ServiceArea>): ServiceArea => {
    const centerLat = faker.location.latitude({ min: 35, max: 45, precision: 6 });
    const centerLng = faker.location.longitude({ min: -125, max: -65, precision: 6 });
    const offset = 0.01;

    return {
      id: faker.string.uuid(),
      tenant_id: faker.string.uuid(),
      name: `${faker.location.city()} ${faker.helpers.arrayElement(['District', 'Zone', 'Area', 'Sector'])}`,
      polygon_coordinates: {
        type: 'Polygon',
        coordinates: [
          [
            [centerLng - offset, centerLat - offset],
            [centerLng + offset, centerLat - offset],
            [centerLng + offset, centerLat + offset],
            [centerLng - offset, centerLat + offset],
            [centerLng - offset, centerLat - offset],
          ],
        ],
      },
      population: faker.number.int({ min: 1000, max: 100000 }),
      households: faker.number.int({ min: 400, max: 40000 }),
      businesses: faker.number.int({ min: 10, max: 2000 }),
      coverage_percentage: faker.number.int({ min: 60, max: 100 }),
      service_types: faker.helpers.arrayElements(
        ['fiber', 'wireless', 'dsl', 'cable', 'satellite'],
        { min: 1, max: 4 }
      ),
      created_at: faker.date.past().toISOString(),
      updated_at: faker.date.recent().toISOString(),
      ...overrides,
    };
  },

  buildMany: (count: number, overrides?: Partial<ServiceArea>): ServiceArea[] =>
    Array.from({ length: count }, () => ServiceAreaFactory.build(overrides)),
};

export const CoverageGapFactory = {
  build: (overrides?: Partial<CoverageGap>): CoverageGap => {
    const centerLat = faker.location.latitude({ min: 35, max: 45, precision: 6 });
    const centerLng = faker.location.longitude({ min: -125, max: -65, precision: 6 });
    const offset = 0.005;

    return {
      id: faker.string.uuid(),
      tenant_id: faker.string.uuid(),
      polygon_coordinates: {
        type: 'Polygon',
        coordinates: [
          [
            [centerLng - offset, centerLat - offset],
            [centerLng + offset, centerLat - offset],
            [centerLng + offset, centerLat + offset],
            [centerLng - offset, centerLat + offset],
            [centerLng - offset, centerLat - offset],
          ],
        ],
      },
      gap_type: faker.helpers.arrayElement([
        'rural_underserved',
        'urban_dead_zone',
        'signal_weak_area',
        'infrastructure_gap',
      ]),
      severity: faker.helpers.arrayElement(['low', 'medium', 'high', 'critical']),
      affected_customers: faker.number.int({ min: 50, max: 5000 }),
      potential_revenue: faker.number.int({ min: 50000, max: 2000000 }),
      buildout_cost: faker.number.int({ min: 100000, max: 5000000 }),
      priority_score: faker.number.int({ min: 1, max: 100 }),
      recommendations: Array.from({ length: faker.number.int({ min: 1, max: 4 }) }, () =>
        faker.lorem.sentence({ min: 5, max: 15 })
      ),
      status: faker.helpers.arrayElement([
        'identified',
        'analysis_complete',
        'pending_approval',
        'approved',
        'in_progress',
        'completed',
      ]),
      created_at: faker.date.past().toISOString(),
      ...overrides,
    };
  },

  buildMany: (count: number, overrides?: Partial<CoverageGap>): CoverageGap[] =>
    Array.from({ length: count }, () => CoverageGapFactory.build(overrides)),
};

export const PerformanceMetricFactory = {
  build: (overrides?: Partial<PerformanceMetric>): PerformanceMetric => ({
    timestamp: faker.date.recent().toISOString(),
    metric_name: faker.helpers.arrayElement([
      'cpu_usage',
      'memory_usage',
      'disk_usage',
      'network_utilization',
      'link_utilization',
      'temperature',
      'power_consumption',
    ]),
    entity_id: `entity_${faker.string.alphanumeric(8)}`,
    entity_type: faker.helpers.arrayElement(['node', 'link']),
    value: faker.number.float({ min: 0, max: 100, precision: 0.1 }),
    unit: faker.helpers.arrayElement(['percentage', 'celsius', 'watts', 'mbps', 'ms']),
    ...overrides,
  }),

  buildMany: (count: number, overrides?: Partial<PerformanceMetric>): PerformanceMetric[] =>
    Array.from({ length: count }, () => PerformanceMetricFactory.build(overrides)),
};

export const NetworkAlertFactory = {
  build: (overrides?: Partial<NetworkAlert>): NetworkAlert => ({
    id: faker.string.uuid(),
    device_id: faker.helpers.maybe(() => `device_${faker.string.alphanumeric(6)}`),
    interface_id: faker.helpers.maybe(() => faker.string.alphanumeric(12)),
    type: faker.helpers.arrayElement([
      'high_cpu',
      'high_memory',
      'link_down',
      'high_temperature',
      'power_failure',
      'authentication_failed',
    ]),
    severity: faker.helpers.arrayElement(['info', 'warning', 'critical', 'emergency']),
    title: faker.lorem.sentence({ min: 3, max: 8 }),
    message: faker.lorem.sentence({ min: 8, max: 20 }),
    status: faker.helpers.arrayElement(['active', 'acknowledged', 'resolved', 'suppressed']),
    created_at: faker.date.recent().toISOString(),
    updated_at: faker.helpers.maybe(() => faker.date.recent().toISOString()),
    acknowledged_at: faker.helpers.maybe(() => faker.date.recent().toISOString()),
    acknowledged_by: faker.helpers.maybe(() => faker.person.fullName()),
    resolved_at: faker.helpers.maybe(() => faker.date.recent().toISOString()),
    resolved_by: faker.helpers.maybe(() => faker.person.fullName()),
    ...overrides,
  }),

  buildMany: (count: number, overrides?: Partial<NetworkAlert>): NetworkAlert[] =>
    Array.from({ length: count }, () => NetworkAlertFactory.build(overrides)),
};

// Test scenario builders
export const TestScenarios = {
  // Create a complete collaboration scenario
  createCollaborationScenario: () => {
    const users = UserFactory.buildMany(4);
    const document = DocumentFactory.build({
      permissions: {
        read: users.map((u) => u.id),
        write: users.slice(0, 3).map((u) => u.id),
        comment: users.map((u) => u.id),
        admin: [users[0].id],
      },
    });

    const comments = CommentFactory.buildMany(3, { document_id: document.id });
    const suggestions = SuggestionFactory.buildMany(2, { document_id: document.id });
    const conflicts = ConflictFactory.buildMany(1, { document_id: document.id });
    const presence = UserPresenceFactory.buildMany(2, { document_id: document.id });

    return {
      users,
      document,
      comments,
      suggestions,
      conflicts,
      presence,
    };
  },

  // Create a complete network scenario
  createNetworkScenario: () => {
    const nodes = NetworkNodeFactory.buildMany(6);
    const links = NetworkLinkFactory.buildMany(8, {
      source_node_id: nodes[0].node_id,
      target_node_id: nodes[1].node_id,
    });
    const serviceAreas = ServiceAreaFactory.buildMany(3);
    const coverageGaps = CoverageGapFactory.buildMany(2);
    const performanceMetrics = PerformanceMetricFactory.buildMany(20);
    const alerts = NetworkAlertFactory.buildMany(5);

    return {
      nodes,
      links,
      serviceAreas,
      coverageGaps,
      performanceMetrics,
      alerts,
    };
  },

  // Create mixed scenario for integration testing
  createIntegrationScenario: () => ({
    collaboration: TestScenarios.createCollaborationScenario(),
    network: TestScenarios.createNetworkScenario(),
  }),
};
