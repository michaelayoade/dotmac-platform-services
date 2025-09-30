'use client';

import { useState } from 'react';
import {
  Puzzle,
  Plus,
  Settings,
  CheckCircle,
  XCircle,
  AlertTriangle,
  ExternalLink,
  Tag,
  Users,
  Clock,
  Activity,
  Shield,
  Zap
} from 'lucide-react';

interface FieldSpec {
  key: string;
  label: string;
  type: string;
  description?: string;
  required?: boolean;
  is_secret?: boolean;
  group?: string;
}

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

interface PluginInstance {
  id: string;
  plugin_name: string;
  instance_name: string;
  status: 'active' | 'inactive' | 'error' | 'configured';
  has_configuration: boolean;
  created_at?: string;
  last_error?: string;
}

interface PluginCardProps {
  plugin: PluginConfig;
  instances: PluginInstance[];
  onInstall: (plugin: PluginConfig) => void;
}

const getTypeIcon = (type: string) => {
  switch (type) {
    case 'notification':
      return <Activity className="h-5 w-5 text-sky-400" />;
    case 'integration':
      return <Zap className="h-5 w-5 text-amber-400" />;
    case 'payment':
      return <Shield className="h-5 w-5 text-emerald-400" />;
    case 'storage':
      return <Settings className="h-5 w-5 text-purple-400" />;
    default:
      return <Puzzle className="h-5 w-5 text-slate-400" />;
  }
};

const getTypeColor = (type: string) => {
  switch (type) {
    case 'notification':
      return 'bg-sky-500/10 text-sky-400 border-sky-500/20';
    case 'integration':
      return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
    case 'payment':
      return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
    case 'storage':
      return 'bg-purple-500/10 text-purple-400 border-purple-500/20';
    default:
      return 'bg-slate-500/10 text-slate-400 border-slate-500/20';
  }
};

const getStatusColor = (status: string) => {
  switch (status) {
    case 'active':
      return 'bg-emerald-500/10 text-emerald-400';
    case 'inactive':
      return 'bg-slate-500/10 text-slate-400';
    case 'error':
      return 'bg-rose-500/10 text-rose-400';
    case 'configured':
      return 'bg-sky-500/10 text-sky-400';
    default:
      return 'bg-slate-500/10 text-slate-400';
  }
};

export const PluginCard = ({ plugin, instances, onInstall }: PluginCardProps) => {
  const [showDetails, setShowDetails] = useState(false);

  const activeInstances = instances.filter(i => i.status === 'active');
  const errorInstances = instances.filter(i => i.status === 'error');
  const totalInstances = instances.length;

  const fieldGroups = plugin.fields.reduce((groups, field) => {
    const group = field.group || 'Configuration';
    groups[group] = (groups[group] || 0) + 1;
    return groups;
  }, {} as Record<string, number>);

  const requiredFields = plugin.fields.filter(f => f.required).length;
  const secretFields = plugin.fields.filter(f => f.is_secret).length;

  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-lg hover:border-slate-700 transition-colors">
      {/* Card Header */}
      <div className="p-4 border-b border-slate-800">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0">
            {getTypeIcon(plugin.type)}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="font-medium text-slate-100 truncate">{plugin.name}</h3>
                <p className="text-sm text-slate-400 mt-1 line-clamp-2">{plugin.description}</p>
              </div>
              <div className={`px-2 py-1 rounded-full text-xs font-medium border ${getTypeColor(plugin.type)}`}>
                {plugin.type}
              </div>
            </div>
          </div>
        </div>

        {/* Plugin Metadata */}
        <div className="flex items-center gap-4 mt-3 text-xs text-slate-500">
          <span>v{plugin.version}</span>
          {plugin.author && <span>by {plugin.author}</span>}
          <span>{plugin.fields.length} fields</span>
        </div>

        {/* Tags */}
        {plugin.tags && plugin.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {plugin.tags.slice(0, 3).map(tag => (
              <span key={tag} className="px-2 py-0.5 bg-slate-800 text-xs rounded-full text-slate-400">
                {tag}
              </span>
            ))}
            {plugin.tags.length > 3 && (
              <span className="px-2 py-0.5 bg-slate-800 text-xs rounded-full text-slate-400">
                +{plugin.tags.length - 3} more
              </span>
            )}
          </div>
        )}
      </div>

      {/* Instances Status */}
      {totalInstances > 0 && (
        <div className="p-4 border-b border-slate-800">
          <div className="flex items-center justify-between text-sm">
            <span className="text-slate-400">Instances</span>
            <div className="flex items-center gap-2">
              {activeInstances.length > 0 && (
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-emerald-500 rounded-full"></div>
                  <span className="text-emerald-400">{activeInstances.length}</span>
                </div>
              )}
              {errorInstances.length > 0 && (
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-rose-500 rounded-full"></div>
                  <span className="text-rose-400">{errorInstances.length}</span>
                </div>
              )}
              <span className="text-slate-500">of {totalInstances}</span>
            </div>
          </div>

          {/* Recent Instances */}
          <div className="mt-2 space-y-1">
            {instances.slice(0, 2).map(instance => (
              <div key={instance.id} className="flex items-center justify-between text-xs">
                <span className="text-slate-300 truncate">{instance.instance_name}</span>
                <span className={`px-2 py-0.5 rounded-full ${getStatusColor(instance.status)}`}>
                  {instance.status}
                </span>
              </div>
            ))}
            {instances.length > 2 && (
              <div className="text-xs text-slate-500 text-center">
                +{instances.length - 2} more instances
              </div>
            )}
          </div>
        </div>
      )}

      {/* Plugin Details (Expandable) */}
      {showDetails && (
        <div className="p-4 border-b border-slate-800 space-y-3">
          {/* Configuration Overview */}
          <div>
            <h4 className="text-sm font-medium text-slate-200 mb-2">Configuration</h4>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Total Fields</span>
                <span className="text-slate-200">{plugin.fields.length}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Required</span>
                <span className="text-slate-200">{requiredFields}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Secrets</span>
                <span className="text-slate-200">{secretFields}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Groups</span>
                <span className="text-slate-200">{Object.keys(fieldGroups).length}</span>
              </div>
            </div>
          </div>

          {/* Field Groups */}
          {Object.keys(fieldGroups).length > 1 && (
            <div>
              <h4 className="text-sm font-medium text-slate-200 mb-2">Field Groups</h4>
              <div className="space-y-1">
                {Object.entries(fieldGroups).map(([group, count]) => (
                  <div key={group} className="flex items-center justify-between text-xs">
                    <span className="text-slate-400">{group}</span>
                    <span className="text-slate-200">{count} fields</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Features */}
          <div>
            <h4 className="text-sm font-medium text-slate-200 mb-2">Features</h4>
            <div className="flex flex-wrap gap-2">
              {plugin.supports_health_check && (
                <div className="flex items-center gap-1 px-2 py-1 bg-emerald-500/10 text-emerald-400 rounded-full text-xs">
                  <Activity className="h-3 w-3" />
                  Health Check
                </div>
              )}
              {plugin.supports_test_connection && (
                <div className="flex items-center gap-1 px-2 py-1 bg-sky-500/10 text-sky-400 rounded-full text-xs">
                  <Zap className="h-3 w-3" />
                  Test Connection
                </div>
              )}
              {secretFields > 0 && (
                <div className="flex items-center gap-1 px-2 py-1 bg-amber-500/10 text-amber-400 rounded-full text-xs">
                  <Shield className="h-3 w-3" />
                  Secure Config
                </div>
              )}
            </div>
          </div>

          {/* Dependencies */}
          {plugin.dependencies && plugin.dependencies.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-slate-200 mb-2">Dependencies</h4>
              <div className="flex flex-wrap gap-1">
                {plugin.dependencies.slice(0, 4).map(dep => (
                  <span key={dep} className="px-2 py-0.5 bg-slate-800 text-xs rounded text-slate-400">
                    {dep}
                  </span>
                ))}
                {plugin.dependencies.length > 4 && (
                  <span className="px-2 py-0.5 bg-slate-800 text-xs rounded text-slate-400">
                    +{plugin.dependencies.length - 4} more
                  </span>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Card Footer */}
      <div className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="text-xs text-slate-400 hover:text-slate-200 transition-colors"
            >
              {showDetails ? 'Hide Details' : 'Show Details'}
            </button>
            {plugin.homepage && (
              <a
                href={plugin.homepage}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-slate-400 hover:text-slate-200 transition-colors flex items-center gap-1"
              >
                <ExternalLink className="h-3 w-3" />
                Docs
              </a>
            )}
          </div>

          <button
            onClick={() => onInstall(plugin)}
            className="px-3 py-1.5 bg-sky-500 hover:bg-sky-600 text-white text-sm rounded-lg transition-colors flex items-center gap-1.5"
          >
            <Plus className="h-4 w-4" />
            Add Instance
          </button>
        </div>
      </div>
    </div>
  );
};