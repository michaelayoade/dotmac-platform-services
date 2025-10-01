'use client';

import { useState } from 'react';
import { useToast } from '@/components/ui/use-toast';
import { logger } from '@/lib/utils/logger';
import { PluginForm } from '../dashboard/settings/plugins/components/PluginForm';
import { PluginCard } from '../dashboard/settings/plugins/components/PluginCard';
import { PluginHealthDashboard } from '../dashboard/settings/plugins/components/PluginHealthDashboard';

// Migrated from sonner to useToast hook
// Note: toast options have changed:
// - sonner: toast.success('msg') -> useToast: toast({ title: 'Success', description: 'msg' })
// - sonner: toast.error('msg') -> useToast: toast({ title: 'Error', description: 'msg', variant: 'destructive' })
// - For complex options, refer to useToast documentation

// Mock data matching our WhatsApp plugin schema
const mockWhatsAppPlugin = {
  name: "WhatsApp Business",
  type: "notification" as const,
  version: "1.0.0",
  description: "Send WhatsApp messages via WhatsApp Business API",
  author: "DotMac Platform",
  homepage: "https://developers.facebook.com/docs/whatsapp",
  tags: ["messaging", "notification", "whatsapp"],
  dependencies: ["httpx"],
  supports_health_check: true,
  supports_test_connection: true,
  fields: [
    {
      key: "phone_number",
      label: "Phone Number",
      type: "phone" as const,
      description: "WhatsApp Business phone number in E.164 format",
      required: true,
      pattern: "^\\+[1-9]\\d{1,14}$",
      group: "Basic Configuration",
      order: 1
    },
    {
      key: "api_token",
      label: "API Token",
      type: "secret" as const,
      description: "WhatsApp Business API access token",
      required: true,
      is_secret: true,
      min_length: 50,
      group: "Basic Configuration",
      order: 2
    },
    {
      key: "business_account_id",
      label: "Business Account ID",
      type: "string" as const,
      description: "WhatsApp Business Account ID",
      required: true,
      group: "Basic Configuration",
      order: 3
    },
    {
      key: "api_version",
      label: "API Version",
      type: "select" as const,
      description: "WhatsApp Business API version",
      default: "v18.0",
      options: [
        { value: "v18.0", label: "v18.0 (Latest)" },
        { value: "v17.0", label: "v17.0" },
        { value: "v16.0", label: "v16.0" }
      ],
      group: "Environment",
      order: 1
    },
    {
      key: "sandbox_mode",
      label: "Sandbox Mode",
      type: "boolean" as const,
      description: "Enable sandbox mode for testing",
      default: false,
      group: "Environment",
      order: 2
    },
    {
      key: "webhook_url",
      label: "Webhook URL",
      type: "url" as const,
      description: "URL to receive webhook notifications",
      group: "Webhooks",
      order: 1
    },
    {
      key: "webhook_token",
      label: "Webhook Verification Token",
      type: "secret" as const,
      description: "Token for webhook verification",
      is_secret: true,
      group: "Webhooks",
      order: 2
    },
    {
      key: "message_retry_count",
      label: "Message Retry Count",
      type: "integer" as const,
      description: "Number of retry attempts for failed messages",
      default: 3,
      min_value: 0,
      max_value: 5,
      group: "Advanced",
      order: 1
    },
    {
      key: "timeout_seconds",
      label: "Request Timeout",
      type: "integer" as const,
      description: "HTTP request timeout in seconds",
      default: 30,
      min_value: 5,
      max_value: 300,
      group: "Advanced",
      order: 2
    },
    {
      key: "custom_headers",
      label: "Custom Headers",
      type: "json" as const,
      description: "Additional HTTP headers as JSON object",
      group: "Advanced",
      order: 3
    }
  ]
};

const mockInstances = [
  {
    id: "550e8400-e29b-41d4-a716-446655440000",
    plugin_name: "WhatsApp Business",
    instance_name: "Production WhatsApp",
    config_schema: mockWhatsAppPlugin,
    status: "active" as const,
    has_configuration: true,
    created_at: "2024-01-15T10:00:00Z",
    last_health_check: "2024-01-20T15:30:00Z"
  },
  {
    id: "550e8400-e29b-41d4-a716-446655440001",
    plugin_name: "WhatsApp Business",
    instance_name: "Test WhatsApp",
    config_schema: mockWhatsAppPlugin,
    status: "error" as const,
    has_configuration: true,
    created_at: "2024-01-10T08:00:00Z",
    last_error: "Authentication failed: Invalid API token"
  }
];

const mockHealthChecks = [
  {
    plugin_instance_id: "550e8400-e29b-41d4-a716-446655440000",
    status: "healthy" as const,
    message: "WhatsApp Business API is accessible and responding normally",
    details: {
      api_accessible: true,
      business_name: "DotMac Corp",
      phone_number_verified: true,
      webhook_configured: true,
      last_message_sent: "2024-01-20T15:25:00Z"
    },
    response_time_ms: 245,
    timestamp: "2024-01-20T15:30:00Z"
  },
  {
    plugin_instance_id: "550e8400-e29b-41d4-a716-446655440001",
    status: "error" as const,
    message: "Authentication failed: Invalid or expired API token",
    details: {
      api_accessible: false,
      error: "Token validation failed",
      status_code: 401
    },
    response_time_ms: 120,
    timestamp: "2024-01-20T15:30:00Z"
  }
];

const mockAvailablePlugins = [mockWhatsAppPlugin];

export default function TestPluginsPage() {
  const { toast } = useToast();

  const [showForm, setShowForm] = useState(false);
  const [selectedPlugin, setSelectedPlugin] = useState<Record<string, unknown> | null>(null);
  const [view, setView] = useState<'card' | 'form' | 'health'>('card');

  const handleSubmit = async (data: Record<string, unknown>) => {
    logger.info('Form submitted', { pluginData: data });
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    setShowForm(false);
    toast({ title: 'Success', description: `Plugin instance "${data.instance_name}" created successfully!` });
  };

  const handleTestConnection = async (instanceId: string, testConfig?: Record<string, unknown>) => {
    logger.info('Testing connection', { instanceId, testConfig });
    // Simulate connection test
    await new Promise(resolve => setTimeout(resolve, 2000));
    return {
      success: true,
      message: "Connection test successful! WhatsApp Business API is accessible.",
      details: {
        business_name: "Test Business",
        api_version: testConfig?.api_version || "v18.0"
      }
    };
  };

  const handleRefresh = async () => {
    logger.info('Refreshing health data');
    await new Promise(resolve => setTimeout(resolve, 1000));
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-100 mb-2">Plugin UI Test Page</h1>
          <p className="text-slate-400">
            Testing the dynamic plugin system with WhatsApp Business API example
          </p>
        </div>

        {/* View Selector */}
        <div className="mb-6 flex items-center gap-4">
          <button
            onClick={() => setView('card')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              view === 'card'
                ? 'bg-sky-500 text-white'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            Plugin Card
          </button>
          <button
            onClick={() => setView('form')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              view === 'form'
                ? 'bg-sky-500 text-white'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            Plugin Form
          </button>
          <button
            onClick={() => setView('health')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              view === 'health'
                ? 'bg-sky-500 text-white'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            Health Dashboard
          </button>
        </div>

        {/* Content */}
        {view === 'card' && (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold">Plugin Card Component</h2>
            <div className="max-w-md">
              <PluginCard
                plugin={mockWhatsAppPlugin}
                instances={mockInstances}
                onInstall={(plugin) => {
                  setSelectedPlugin(plugin as unknown as Record<string, unknown>);
                  setShowForm(true);
                }}
              />
            </div>
          </div>
        )}

        {view === 'form' && (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold">Plugin Form Component</h2>
            <button
              onClick={() => setShowForm(true)}
              className="px-4 py-2 bg-sky-500 hover:bg-sky-600 text-white rounded-lg transition-colors"
            >
              Open Plugin Form
            </button>
          </div>
        )}

        {view === 'health' && (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold">Plugin Health Dashboard</h2>
            <PluginHealthDashboard
              instances={mockInstances}
              healthChecks={mockHealthChecks}
              onRefresh={handleRefresh}
            />
          </div>
        )}

        {/* Form Modal */}
        {showForm && (
          <PluginForm
            plugin={selectedPlugin as any}
            availablePlugins={mockAvailablePlugins}
            onSubmit={handleSubmit}
            onCancel={() => {
              setShowForm(false);
              setSelectedPlugin(null);
            }}
            onTestConnection={handleTestConnection}
          />
        )}

        {/* Field Types Demo */}
        <div className="mt-12 p-6 bg-slate-900/50 border border-slate-800 rounded-lg">
          <h3 className="text-lg font-semibold mb-4">Supported Field Types in WhatsApp Plugin</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-sm">
            <div className="space-y-1">
              <span className="font-medium text-sky-400">String Fields:</span>
              <p className="text-slate-400">Business Account ID</p>
            </div>
            <div className="space-y-1">
              <span className="font-medium text-amber-400">Secret Fields:</span>
              <p className="text-slate-400">API Token, Webhook Token</p>
            </div>
            <div className="space-y-1">
              <span className="font-medium text-emerald-400">Phone Fields:</span>
              <p className="text-slate-400">Phone Number (E.164 format)</p>
            </div>
            <div className="space-y-1">
              <span className="font-medium text-purple-400">Select Fields:</span>
              <p className="text-slate-400">API Version options</p>
            </div>
            <div className="space-y-1">
              <span className="font-medium text-rose-400">Boolean Fields:</span>
              <p className="text-slate-400">Sandbox Mode toggle</p>
            </div>
            <div className="space-y-1">
              <span className="font-medium text-indigo-400">URL Fields:</span>
              <p className="text-slate-400">Webhook URL</p>
            </div>
            <div className="space-y-1">
              <span className="font-medium text-orange-400">Integer Fields:</span>
              <p className="text-slate-400">Retry Count, Timeout</p>
            </div>
            <div className="space-y-1">
              <span className="font-medium text-teal-400">JSON Fields:</span>
              <p className="text-slate-400">Custom Headers</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}