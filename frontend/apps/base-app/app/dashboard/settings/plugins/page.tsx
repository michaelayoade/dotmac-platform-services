'use client';

import { useState, useEffect } from 'react';
import {
  Puzzle,
  Plus,
  Settings,
  CheckCircle,
  XCircle,
  AlertTriangle,
  RefreshCw,
  Trash2,
  Edit,
  Eye,
  TestTube,
  Activity,
  Search,
  Filter
} from 'lucide-react';
import { apiClient } from '@/lib/api/client';
import { PluginForm } from './components/PluginForm';
import { PluginCard } from './components/PluginCard';
import { PluginHealthDashboard } from './components/PluginHealthDashboard';

// Plugin types matching backend schema
interface PluginConfig {
  name: string;
  type: 'notification' | 'integration' | 'payment' | 'storage';
  version: string;
  description: string;
  author?: string;
  homepage?: string;
  tags?: string[];
  dependencies?: string[];
  supports_health_check: boolean;
  supports_test_connection: boolean;
  fields: FieldSpec[];
}

interface FieldSpec {
  key: string;
  label: string;
  type: 'string' | 'secret' | 'boolean' | 'integer' | 'float' | 'select' | 'json' | 'url' | 'email' | 'phone' | 'date' | 'datetime' | 'file';
  description?: string;
  required?: boolean;
  is_secret?: boolean;
  default?: unknown;
  min_value?: number;
  max_value?: number;
  min_length?: number;
  max_length?: number;
  pattern?: string;
  validation_rules?: string[];
  options?: Array<{ value: string; label: string }>;
  group?: string;
  order?: number;
}

interface PluginInstance {
  id: string;
  plugin_name: string;
  instance_name: string;
  config_schema: PluginConfig;
  status: 'active' | 'inactive' | 'error' | 'configured';
  has_configuration: boolean;
  created_at?: string;
  updated_at?: string;
  last_health_check?: string;
  last_error?: string;
}

interface PluginHealthCheck {
  plugin_instance_id: string;
  status: 'healthy' | 'unhealthy' | 'error' | 'unknown';
  message: string;
  details: Record<string, unknown>;
  response_time_ms?: number;
  timestamp: string;
}

type ViewMode = 'grid' | 'list' | 'health';

export default function PluginsPage() {
  // State management
  const [availablePlugins, setAvailablePlugins] = useState<PluginConfig[]>([]);
  const [pluginInstances, setPluginInstances] = useState<PluginInstance[]>([]);
  const [healthChecks, setHealthChecks] = useState<PluginHealthCheck[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [viewMode, setViewMode] = useState<ViewMode>('grid');

  // Modal states
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingInstance, setEditingInstance] = useState<PluginInstance | null>(null);
  const [selectedPlugin, setSelectedPlugin] = useState<PluginConfig | null>(null);

  // Load data on mount
  useEffect(() => {
    loadPluginData();
  }, []);

  const loadPluginData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Load available plugins, instances, and health status in parallel
      const [availableResponse, instancesResponse, healthResponse] = await Promise.all([
        fetch('/api/v1/plugins/', { credentials: 'include' }).then(r => r.json()),
        fetch('/api/v1/plugins/instances', { credentials: 'include' }).then(r => r.json()),
        fetch('/api/v1/plugins/instances/health-check', { method: 'POST', credentials: 'include' }).then(r => r.json())
      ]);

      setAvailablePlugins(availableResponse);
      setPluginInstances(instancesResponse.plugins || []);
      setHealthChecks(healthResponse || []);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load plugin data';
      setError(errorMessage);
      console.error('Failed to load plugin data:', err);
    } finally {
      setLoading(false);
    }
  };

  const refreshPluginRegistry = async () => {
    try {
      setLoading(true);
      await fetch('/api/v1/plugins/refresh', { method: 'POST', credentials: 'include' });
      await loadPluginData();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to refresh plugins';
      setError(errorMessage);
    }
  };

  const handleCreateInstance = async (data: { plugin_name: string; instance_name: string; configuration: Record<string, unknown> }) => {
    try {
      const response = await fetch('/api/v1/plugins/instances', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(data)
      });
      const responseData = await response.json();
      setPluginInstances(prev => [...prev, responseData]);
      setShowCreateForm(false);
      setSelectedPlugin(null);
      // Refresh health checks
      await loadPluginData();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create plugin instance';
      throw new Error(errorMessage);
    }
  };

  const handleUpdateInstance = async (instanceId: string, configuration: Record<string, unknown>) => {
    try {
      await fetch(`/api/v1/plugins/instances/${instanceId}/configuration`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ configuration })
      });
      await loadPluginData();
      setEditingInstance(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update plugin configuration';
      throw new Error(errorMessage);
    }
  };

  const handleDeleteInstance = async (instanceId: string) => {
    if (!confirm('Are you sure you want to delete this plugin instance? This cannot be undone.')) {
      return;
    }

    try {
      await fetch(`/api/v1/plugins/instances/${instanceId}`, {
        method: 'DELETE',
        credentials: 'include'
      });
      setPluginInstances(prev => prev.filter(instance => instance.id !== instanceId));
      setHealthChecks(prev => prev.filter(health => health.plugin_instance_id !== instanceId));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete plugin instance';
      setError(errorMessage);
    }
  };

  const handleTestConnection = async (instanceId: string, testConfig?: Record<string, unknown>) => {
    try {
      const response = await fetch(`/api/v1/plugins/instances/${instanceId}/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ configuration: testConfig })
      });
      const responseData = await response.json();
      return responseData;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Connection test failed';
      throw new Error(errorMessage);
    }
  };

  // Filter functions
  const filteredPlugins = availablePlugins.filter(plugin => {
    const matchesSearch = plugin.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         plugin.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = filterType === 'all' || plugin.type === filterType;
    return matchesSearch && matchesType;
  });

  const filteredInstances = pluginInstances.filter(instance => {
    const matchesSearch = instance.plugin_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         instance.instance_name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = filterStatus === 'all' || instance.status === filterStatus;
    return matchesSearch && matchesStatus;
  });

  const getHealthStatus = (instanceId: string) => {
    return healthChecks.find(health => health.plugin_instance_id === instanceId);
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center py-12">
            <RefreshCw className="h-8 w-8 text-sky-500 animate-spin" />
            <span className="ml-2 text-muted-foreground">Loading plugins...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="max-w-7xl mx-auto">
          <div className="bg-rose-500/10 border border-rose-500/20 text-rose-400 p-4 rounded-lg">
            <div className="flex items-center gap-2">
              <XCircle className="h-5 w-5" />
              <span>{error}</span>
            </div>
            <button
              onClick={loadPluginData}
              className="mt-2 px-3 py-1 text-sm bg-rose-500/20 hover:bg-rose-500/30 rounded-md transition-colors"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto">
        {/* Page Header */}
        <div className="mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-semibold text-foreground flex items-center gap-2">
                <Puzzle className="h-6 w-6 text-sky-500" />
                Plugin Management
              </h1>
              <p className="text-muted-foreground mt-1">
                Configure and manage plugins for extended functionality
              </p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={refreshPluginRegistry}
                className="px-3 py-2 text-sm border border-border text-muted-foreground rounded-lg hover:bg-accent transition-colors flex items-center gap-2"
              >
                <RefreshCw className="h-4 w-4" />
                Refresh
              </button>
              <button
                onClick={() => setShowCreateForm(true)}
                className="px-4 py-2 bg-sky-500 hover:bg-sky-600 text-white rounded-lg transition-colors flex items-center gap-2"
              >
                <Plus className="h-4 w-4" />
                Add Plugin
              </button>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-card/50 border border-border rounded-lg p-4">
            <div className="flex items-center gap-3">
              <Puzzle className="h-8 w-8 text-sky-500" />
              <div>
                <div className="text-2xl font-semibold text-foreground">{availablePlugins.length}</div>
                <div className="text-sm text-muted-foreground">Available Plugins</div>
              </div>
            </div>
          </div>
          <div className="bg-card/50 border border-border rounded-lg p-4">
            <div className="flex items-center gap-3">
              <Settings className="h-8 w-8 text-emerald-500" />
              <div>
                <div className="text-2xl font-semibold text-foreground">{pluginInstances.length}</div>
                <div className="text-sm text-muted-foreground">Active Instances</div>
              </div>
            </div>
          </div>
          <div className="bg-card/50 border border-border rounded-lg p-4">
            <div className="flex items-center gap-3">
              <CheckCircle className="h-8 w-8 text-emerald-500" />
              <div>
                <div className="text-2xl font-semibold text-foreground">
                  {healthChecks.filter(h => h.status === 'healthy').length}
                </div>
                <div className="text-sm text-muted-foreground">Healthy</div>
              </div>
            </div>
          </div>
          <div className="bg-card/50 border border-border rounded-lg p-4">
            <div className="flex items-center gap-3">
              <AlertTriangle className="h-8 w-8 text-amber-500" />
              <div>
                <div className="text-2xl font-semibold text-foreground">
                  {healthChecks.filter(h => h.status !== 'healthy').length}
                </div>
                <div className="text-sm text-muted-foreground">Issues</div>
              </div>
            </div>
          </div>
        </div>

        {/* Filters and Controls */}
        <div className="mb-6 flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
          <div className="flex items-center gap-4 flex-1">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search plugins..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-card border border-border rounded-lg text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-sky-500"
              />
            </div>
            <select
              value={viewMode === 'grid' ? filterType : filterStatus}
              onChange={(e) => viewMode === 'grid' ? setFilterType(e.target.value) : setFilterStatus(e.target.value)}
              className="px-3 py-2 bg-card border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-sky-500"
            >
              {viewMode === 'grid' ? (
                <>
                  <option value="all">All Types</option>
                  <option value="notification">Notification</option>
                  <option value="integration">Integration</option>
                  <option value="payment">Payment</option>
                  <option value="storage">Storage</option>
                </>
              ) : (
                <>
                  <option value="all">All Status</option>
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                  <option value="error">Error</option>
                </>
              )}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 rounded-md transition-colors ${
                viewMode === 'grid' ? 'bg-sky-500 text-white' : 'bg-accent text-muted-foreground hover:text-foreground'
              }`}
            >
              <div className="grid grid-cols-2 gap-0.5 w-4 h-4">
                <div className="bg-current rounded-sm"></div>
                <div className="bg-current rounded-sm"></div>
                <div className="bg-current rounded-sm"></div>
                <div className="bg-current rounded-sm"></div>
              </div>
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 rounded-md transition-colors ${
                viewMode === 'list' ? 'bg-sky-500 text-white' : 'bg-accent text-muted-foreground hover:text-foreground'
              }`}
            >
              <div className="space-y-1 w-4 h-4">
                <div className="bg-current h-0.5 rounded"></div>
                <div className="bg-current h-0.5 rounded"></div>
                <div className="bg-current h-0.5 rounded"></div>
              </div>
            </button>
            <button
              onClick={() => setViewMode('health')}
              className={`p-2 rounded-md transition-colors ${
                viewMode === 'health' ? 'bg-sky-500 text-white' : 'bg-accent text-muted-foreground hover:text-foreground'
              }`}
            >
              <Activity className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Content based on view mode */}
        {viewMode === 'health' ? (
          <PluginHealthDashboard
            instances={pluginInstances}
            healthChecks={healthChecks}
            onRefresh={loadPluginData}
          />
        ) : viewMode === 'grid' && !showCreateForm ? (
          <div>
            <h2 className="text-lg font-semibold text-foreground mb-4">Available Plugins</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredPlugins.map((plugin) => (
                <PluginCard
                  key={plugin.name}
                  plugin={plugin}
                  instances={pluginInstances.filter(inst => inst.plugin_name === plugin.name)}
                  onInstall={(plugin) => {
                    setSelectedPlugin(plugin as any);
                    setShowCreateForm(true);
                  }}
                />
              ))}
            </div>
          </div>
        ) : (
          <div>
            <h2 className="text-lg font-semibold text-foreground mb-4">Plugin Instances</h2>
            <div className="space-y-4">
              {filteredInstances.map((instance) => {
                const healthStatus = getHealthStatus(instance.id);
                return (
                  <div key={instance.id} className="bg-card/50 border border-border rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`w-3 h-3 rounded-full ${
                          healthStatus?.status === 'healthy' ? 'bg-emerald-500' :
                          healthStatus?.status === 'unhealthy' ? 'bg-rose-500' :
                          'bg-amber-500'
                        }`} />
                        <div>
                          <h3 className="font-medium text-foreground">{instance.instance_name}</h3>
                          <p className="text-sm text-muted-foreground">{instance.plugin_name} • {instance.status}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => setEditingInstance(instance)}
                          className="p-2 text-muted-foreground hover:text-foreground transition-colors"
                        >
                          <Edit className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteInstance(instance.id)}
                          className="p-2 text-muted-foreground hover:text-rose-400 transition-colors"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                    {instance.last_error && (
                      <div className="mt-2 text-sm text-rose-400 bg-rose-500/10 px-2 py-1 rounded">
                        {instance.last_error}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Create Plugin Modal */}
        {showCreateForm && (
          <PluginForm
            plugin={selectedPlugin}
            onSubmit={handleCreateInstance}
            onCancel={() => {
              setShowCreateForm(false);
              setSelectedPlugin(null);
            }}
            onTestConnection={handleTestConnection}
            availablePlugins={availablePlugins}
          />
        )}

        {/* Edit Plugin Modal */}
        {editingInstance && (
          <PluginForm
            plugin={editingInstance.config_schema}
            instance={editingInstance}
            onSubmit={(data) => handleUpdateInstance(editingInstance.id, data.configuration)}
            onCancel={() => setEditingInstance(null)}
            onTestConnection={(_, testConfig) => handleTestConnection(editingInstance.id, testConfig)}
            availablePlugins={availablePlugins}
          />
        )}
      </div>
    </div>
  );
}