/**
 * MSW API Mock Handlers
 * Provides mock responses for API endpoints used in tests
 */

import { http, HttpResponse } from 'msw';

// Mock data for plugins
export const mockAvailablePlugins = [
  {
    name: "WhatsApp Business",
    type: "notification",
    version: "1.0.0",
    description: "Send WhatsApp messages via WhatsApp Business API",
    author: "DotMac Platform",
    supports_health_check: true,
    supports_test_connection: true,
    fields: [
      {
        key: "api_token",
        label: "API Token",
        type: "secret",
        required: true,
      }
    ]
  },
  {
    name: "Slack Integration",
    type: "notification",
    version: "2.0.0",
    description: "Send notifications to Slack channels",
    author: "DotMac Platform",
    supports_health_check: true,
    supports_test_connection: false,
    fields: []
  },
  {
    name: "Payment Gateway",
    type: "payment",
    version: "1.5.0",
    description: "Process payments securely",
    author: "Third Party",
    supports_health_check: false,
    supports_test_connection: true,
    fields: []
  }
];

export const mockPluginInstances = [
  {
    id: "550e8400-e29b-41d4-a716-446655440000",
    plugin_name: "WhatsApp Business",
    instance_name: "Production WhatsApp",
    status: "active",
    has_configuration: true,
    created_at: "2024-01-15T10:00:00Z"
  },
  {
    id: "550e8400-e29b-41d4-a716-446655440001",
    plugin_name: "Slack Integration",
    instance_name: "Team Notifications",
    status: "error",
    has_configuration: true,
    last_error: "Authentication failed"
  }
];

export const mockHealthChecks = [
  {
    plugin_instance_id: "550e8400-e29b-41d4-a716-446655440000",
    status: "healthy",
    message: "All systems operational",
    details: {},
    response_time_ms: 200,
    timestamp: "2024-01-20T15:30:00Z"
  },
  {
    plugin_instance_id: "550e8400-e29b-41d4-a716-446655440001",
    status: "error",
    message: "Authentication failed",
    details: { error_code: 401 },
    response_time_ms: 1000,
    timestamp: "2024-01-20T15:30:00Z"
  }
];

// Default handlers for common API endpoints
export const handlers = [
  // Get available plugins
  http.get('*/api/v1/plugins/', () => {
    return HttpResponse.json(mockAvailablePlugins);
  }),

  // Get plugin instances
  http.get('*/api/v1/plugins/instances', () => {
    return HttpResponse.json({ plugins: mockPluginInstances });
  }),

  // Health check
  http.post('*/api/v1/plugins/instances/health-check', () => {
    return HttpResponse.json(mockHealthChecks);
  }),

  // Refresh plugins
  http.post('*/api/v1/plugins/refresh', () => {
    return HttpResponse.json({ message: 'Plugins refreshed' });
  }),

  // Create plugin instance
  http.post('*/api/v1/plugins/instances', async ({ request }) => {
    const body = await request.json() as any;
    return HttpResponse.json({
      id: "new-instance-id",
      plugin_name: body.plugin_name,
      instance_name: body.instance_name,
      status: "active",
      has_configuration: true,
      created_at: new Date().toISOString()
    });
  }),

  // Test connection
  http.post('*/api/v1/plugins/instances/:id/test', () => {
    return HttpResponse.json({
      success: true,
      message: 'Connection successful'
    });
  }),

  // Delete plugin instance
  http.delete('*/api/v1/plugins/instances/:id', () => {
    return HttpResponse.json({ success: true });
  }),
];
