/**
 * API Mock Setup for Testing
 * Configures MSW (Mock Service Worker) handlers for all package API endpoints
 */

import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { collaborationApiMocks } from '@dotmac/collaboration/src/__tests__/mocks/collaborationApiMocks';
import { networkApiMocks } from '@dotmac/network/src/__tests__/mocks/networkApiMocks';
import { TestScenarios } from '../factories/testDataFactories';

// Mock data scenarios
const collaborationScenario = TestScenarios.createCollaborationScenario();
const networkScenario = TestScenarios.createNetworkScenario();

// API Mock Handlers
const collaborationHandlers = [
  // Document endpoints
  http.get('/api/collaboration/documents', () => {
    return HttpResponse.json({ data: collaborationScenario.document });
  }),

  http.get('/api/collaboration/documents/:documentId', ({ params }) => {
    const documentId = params.documentId as string;
    const document =
      documentId === collaborationScenario.document.id
        ? collaborationScenario.document
        : collaborationScenario.document;
    return HttpResponse.json({ data: document });
  }),

  http.post('/api/collaboration/documents', async ({ request }) => {
    const body = (await request.json()) as any;
    return collaborationApiMocks.createDocument(body);
  }),

  http.patch('/api/collaboration/documents/:documentId', async ({ params, request }) => {
    const documentId = params.documentId as string;
    const updates = (await request.json()) as any;
    return collaborationApiMocks.updateDocument(documentId, updates);
  }),

  http.delete('/api/collaboration/documents/:documentId', ({ params }) => {
    const documentId = params.documentId as string;
    return collaborationApiMocks.deleteDocument(documentId);
  }),

  // Document operations
  http.post('/api/collaboration/documents/:documentId/operations', async ({ params, request }) => {
    const documentId = params.documentId as string;
    const operation = (await request.json()) as any;
    return collaborationApiMocks.applyOperation(documentId, operation);
  }),

  // Document locking
  http.post('/api/collaboration/documents/:documentId/lock', ({ params }) => {
    const documentId = params.documentId as string;
    return collaborationApiMocks.lockDocument(documentId);
  }),

  http.delete('/api/collaboration/documents/:documentId/lock', ({ params }) => {
    const documentId = params.documentId as string;
    return collaborationApiMocks.unlockDocument(documentId);
  }),

  // Comments
  http.get('/api/collaboration/documents/:documentId/comments', ({ params }) => {
    const documentId = params.documentId as string;
    return collaborationApiMocks.getDocumentComments(documentId);
  }),

  http.post('/api/collaboration/documents/:documentId/comments', async ({ params, request }) => {
    const documentId = params.documentId as string;
    const commentData = (await request.json()) as any;
    return collaborationApiMocks.createComment(documentId, commentData);
  }),

  http.patch('/api/collaboration/comments/:commentId', async ({ params, request }) => {
    const commentId = params.commentId as string;
    const updates = (await request.json()) as any;
    return collaborationApiMocks.updateComment(commentId, updates);
  }),

  http.delete('/api/collaboration/comments/:commentId', ({ params }) => {
    const commentId = params.commentId as string;
    return collaborationApiMocks.deleteComment(commentId);
  }),

  // Suggestions
  http.get('/api/collaboration/documents/:documentId/suggestions', ({ params }) => {
    const documentId = params.documentId as string;
    return collaborationApiMocks.getDocumentSuggestions(documentId);
  }),

  http.post('/api/collaboration/documents/:documentId/suggestions', async ({ params, request }) => {
    const documentId = params.documentId as string;
    const suggestionData = (await request.json()) as any;
    return collaborationApiMocks.createSuggestion(documentId, suggestionData);
  }),

  http.post('/api/collaboration/suggestions/:suggestionId/approve', ({ params }) => {
    const suggestionId = params.suggestionId as string;
    return collaborationApiMocks.approveSuggestion(suggestionId);
  }),

  http.post('/api/collaboration/suggestions/:suggestionId/reject', async ({ params, request }) => {
    const suggestionId = params.suggestionId as string;
    const body = (await request.json()) as any;
    return collaborationApiMocks.rejectSuggestion(suggestionId, body?.reason);
  }),

  // Conflicts
  http.get('/api/collaboration/documents/:documentId/conflicts', ({ params }) => {
    const documentId = params.documentId as string;
    return collaborationApiMocks.getDocumentConflicts(documentId);
  }),

  http.post('/api/collaboration/conflicts/:conflictId/resolve', async ({ params, request }) => {
    const conflictId = params.conflictId as string;
    const resolution = (await request.json()) as any;
    return collaborationApiMocks.resolveConflict(conflictId, resolution);
  }),

  // Document versions
  http.get('/api/collaboration/documents/:documentId/versions', ({ params }) => {
    const documentId = params.documentId as string;
    return collaborationApiMocks.getDocumentVersions(documentId);
  }),

  http.get('/api/collaboration/documents/:documentId/versions/:version', ({ params }) => {
    const documentId = params.documentId as string;
    const version = parseInt(params.version as string);
    return collaborationApiMocks.getDocumentVersion(documentId, version);
  }),

  // User presence
  http.get('/api/collaboration/documents/:documentId/presence', ({ params }) => {
    const documentId = params.documentId as string;
    return collaborationApiMocks.getUserPresence(documentId);
  }),

  http.post('/api/collaboration/documents/:documentId/presence', async ({ params, request }) => {
    const documentId = params.documentId as string;
    const presenceData = (await request.json()) as any;
    return collaborationApiMocks.updateUserPresence(documentId, presenceData);
  }),
];

const networkHandlers = [
  // Network topology endpoints
  http.get('/api/network/topology/nodes', ({ request }) => {
    const url = new URL(request.url);
    const tenantId = url.searchParams.get('tenant_id');
    // Filter by tenant if provided
    return networkApiMocks.getTopologyNodes();
  }),

  http.get('/api/network/topology/links', ({ request }) => {
    const url = new URL(request.url);
    const tenantId = url.searchParams.get('tenant_id');
    return networkApiMocks.getTopologyLinks();
  }),

  http.get('/api/network/topology/metrics', ({ request }) => {
    const url = new URL(request.url);
    const tenantId = url.searchParams.get('tenant_id');
    return networkApiMocks.getTopologyMetrics();
  }),

  http.get('/api/network/topology/critical-nodes', ({ request }) => {
    const url = new URL(request.url);
    const tenantId = url.searchParams.get('tenant_id');
    return networkApiMocks.getCriticalNodes();
  }),

  http.post('/api/network/topology/analyze-path', async ({ request }) => {
    const body = (await request.json()) as any;
    return networkApiMocks.analyzeNetworkPath(body.source_device, body.target_device);
  }),

  http.get('/api/network/topology/nodes/:nodeId/connectivity', ({ params, request }) => {
    const nodeId = params.nodeId as string;
    const url = new URL(request.url);
    const tenantId = url.searchParams.get('tenant_id');
    return networkApiMocks.getNodeConnectivity(nodeId);
  }),

  // Geographic/GIS endpoints
  http.get('/api/gis/service-areas', ({ request }) => {
    const url = new URL(request.url);
    const tenantId = url.searchParams.get('tenant_id');
    return networkApiMocks.getServiceAreas();
  }),

  http.get('/api/gis/coverage-gaps', ({ request }) => {
    const url = new URL(request.url);
    const tenantId = url.searchParams.get('tenant_id');
    const status = url.searchParams.get('status');
    return networkApiMocks.getCoverageGaps();
  }),

  http.get('/api/gis/service-areas/:serviceAreaId', ({ params }) => {
    const serviceAreaId = params.serviceAreaId as string;
    return HttpResponse.json({
      data:
        networkScenario.serviceAreas.find((area) => area.id === serviceAreaId) ||
        networkScenario.serviceAreas[0],
    });
  }),

  http.patch('/api/gis/service-areas/:serviceAreaId', async ({ params, request }) => {
    const serviceAreaId = params.serviceAreaId as string;
    const updates = (await request.json()) as any;
    return HttpResponse.json({
      data: {
        ...networkScenario.serviceAreas[0],
        ...updates,
        updated_at: new Date().toISOString(),
      },
    });
  }),

  http.patch('/api/gis/coverage-gaps/:gapId', async ({ params, request }) => {
    const gapId = params.gapId as string;
    const updates = (await request.json()) as any;
    return HttpResponse.json({
      data: {
        ...networkScenario.coverageGaps[0],
        ...updates,
        updated_at: new Date().toISOString(),
      },
    });
  }),

  http.post('/api/gis/analyze-coverage', async ({ request }) => {
    const body = (await request.json()) as any;
    return networkApiMocks.analyzeCoverage();
  }),

  http.post('/api/gis/optimize-route', async ({ request }) => {
    const body = (await request.json()) as any;
    return networkApiMocks.optimizeRoute(body);
  }),

  // Network monitoring endpoints
  http.get('/api/network/alerts', ({ request }) => {
    const url = new URL(request.url);
    const tenantId = url.searchParams.get('tenant_id');
    const status = url.searchParams.get('status');
    const limit = url.searchParams.get('limit');

    let alerts = networkScenario.alerts;
    if (status) {
      alerts = alerts.filter((alert) => alert.status === status);
    }
    if (limit) {
      alerts = alerts.slice(0, parseInt(limit));
    }

    return HttpResponse.json({ data: alerts });
  }),

  http.get('/api/network/performance', ({ request }) => {
    const url = new URL(request.url);
    const tenantId = url.searchParams.get('tenant_id');
    const limit = url.searchParams.get('limit');

    let metrics = networkScenario.performanceMetrics;
    if (limit) {
      metrics = metrics.slice(0, parseInt(limit));
    }

    return HttpResponse.json({ data: metrics });
  }),

  http.patch('/api/network/alerts/:alertId', async ({ params, request }) => {
    const alertId = params.alertId as string;
    const updates = (await request.json()) as any;
    return networkApiMocks.updateAlert(alertId, updates);
  }),

  http.get('/api/network/performance/entity/:entityId', ({ params, request }) => {
    const entityId = params.entityId as string;
    const url = new URL(request.url);
    const entityType = url.searchParams.get('entity_type');
    const metricName = url.searchParams.get('metric_name');

    return networkApiMocks.getEntityMetrics(
      entityId,
      entityType || 'node',
      metricName || undefined
    );
  }),
];

// Error simulation handlers (for testing error scenarios)
const errorHandlers = [
  // Simulate network errors
  http.get('/api/network/error/500', () => {
    return HttpResponse.json(
      { error: 'Internal Server Error', message: 'Simulated server error' },
      { status: 500 }
    );
  }),

  http.get('/api/collaboration/error/403', () => {
    return HttpResponse.json({ error: 'Forbidden', message: 'Access denied' }, { status: 403 });
  }),

  http.get('/api/collaboration/error/timeout', () => {
    return new Promise(() => {}); // Never resolves, simulating timeout
  }),
];

// Combine all handlers
const allHandlers = [...collaborationHandlers, ...networkHandlers, ...errorHandlers];

// Create the mock server
export const mockApiServer = setupServer(...allHandlers);

// Test utilities
export const apiMockUtils = {
  // Start/stop server
  startServer: () => mockApiServer.listen({ onUnhandledRequest: 'warn' }),
  stopServer: () => mockApiServer.close(),
  resetHandlers: () => mockApiServer.resetHandlers(),

  // Add custom handlers for specific tests
  addHandler: (handler: any) => mockApiServer.use(handler),

  // Simulate specific scenarios
  simulateNetworkError: (endpoint: string) => {
    mockApiServer.use(
      http.get(endpoint, () => {
        return HttpResponse.json(
          { error: 'Network Error', message: 'Connection failed' },
          { status: 503 }
        );
      })
    );
  },

  simulateSlowResponse: (endpoint: string, delay: number = 2000) => {
    mockApiServer.use(
      http.get(endpoint, async () => {
        await new Promise((resolve) => setTimeout(resolve, delay));
        return HttpResponse.json({ data: [] });
      })
    );
  },

  simulateAuthError: (endpoint: string) => {
    mockApiServer.use(
      http.get(endpoint, () => {
        return HttpResponse.json(
          { error: 'Unauthorized', message: 'Authentication required' },
          { status: 401 }
        );
      })
    );
  },

  // Restore default handlers
  restoreDefaultHandlers: () => {
    mockApiServer.resetHandlers(...allHandlers);
  },

  // Get mock data for assertions
  getMockData: () => ({
    collaboration: collaborationScenario,
    network: networkScenario,
  }),
};

// Export for use in test setup files
export { allHandlers as apiMockHandlers };
