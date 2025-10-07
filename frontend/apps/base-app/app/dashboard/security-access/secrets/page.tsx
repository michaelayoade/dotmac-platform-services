'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  Shield,
  Plus,
  Search,
  Filter,
  MoreHorizontal,
  Edit,
  Trash2,
  Eye,
  EyeOff,
  Copy,
  Calendar,
  Key,
  Lock,
  AlertTriangle
} from 'lucide-react';
import { platformConfig } from '@/lib/config';
import { RouteGuard } from '@/components/auth/PermissionGuard';
import { logger } from '@/lib/logger';

interface Secret {
  path: string;
  version?: number;
  created_at: string;
  updated_at: string;
  metadata?: {
    created_by?: string;
    description?: string;
    tags?: string[];
  };
}

function SecretsPageContent() {
  const [secrets, setSecrets] = useState<Secret[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSecret, setSelectedSecret] = useState<string | null>(null);
  const [secretValue, setSecretValue] = useState<string>('');
  const [showValue, setShowValue] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newSecretData, setNewSecretData] = useState({
    path: '',
    value: '',
    description: '',
    tags: ''
  });
  const [toast, setToast] = useState<{ show: boolean; message: string; type: 'success' | 'error' }>({
    show: false,
    message: '',
    type: 'success'
  });

  const fetchSecrets = useCallback(async () => {
    try {
      const response = await fetch(`${platformConfig.apiBaseUrl}/api/v1/secrets`, {
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setSecrets(data.secrets || data);
      } else if (response.status === 401) {
        window.location.href = '/login';
      } else {
        logger.error('Failed to fetch secrets', { status: response.status });
      }
    } catch (error) {
      logger.error('Error fetching secrets', { error });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSecrets();
  }, [fetchSecrets]);

  useEffect(() => {
    if (toast.show) {
      const timer = setTimeout(() => {
        setToast(t => ({ ...t, show: false }));
      }, 3000);
      return () => clearTimeout(timer);
    }
    return undefined;
  }, [toast.show]);

  const fetchSecretValue = async (path: string) => {
    try {
      const response = await fetch(`${platformConfig.apiBaseUrl}/api/v1/secrets/${encodeURIComponent(path)}`, {
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setSecretValue(data.data || data.value || 'N/A');
        setSelectedSecret(path);
      } else if (response.status === 401) {
        window.location.href = '/login';
      }
    } catch (error) {
      logger.error('Error fetching secret value', { path, error });
    }
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setToast({ show: true, message: 'Copied to clipboard!', type: 'success' });
    } catch (error) {
      setToast({ show: true, message: 'Failed to copy to clipboard', type: 'error' });
    }
  };

  const showToast = (message: string, type: 'success' | 'error' = 'success') => {
    setToast({ show: true, message, type });
  };

  const handleCreateSecret = async () => {
    try {
      const response = await fetch(`${platformConfig.apiBaseUrl}/api/v1/secrets`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          path: newSecretData.path,
          data: newSecretData.value,
          metadata: {
            description: newSecretData.description,
            tags: newSecretData.tags ? newSecretData.tags.split(',').map(t => t.trim()) : []
          }
        })
      });

      if (response.ok) {
        showToast('Secret created successfully!', 'success');
        setShowCreateModal(false);
        setNewSecretData({ path: '', value: '', description: '', tags: '' });
        await fetchSecrets();
      } else if (response.status === 401) {
        window.location.href = '/login';
      } else {
        showToast('Failed to create secret', 'error');
      }
    } catch (error) {
      logger.error('Error creating secret', { path: newSecretData.path, error });
      showToast('Error creating secret', 'error');
    }
  };

  const filteredSecrets = secrets.filter(secret =>
    secret.path.toLowerCase().includes(searchQuery.toLowerCase()) ||
    secret.metadata?.description?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Secrets Management</h1>
          <p className="text-muted-foreground">Securely store and manage application secrets</p>
        </div>
        <button
          className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
          onClick={() => setShowCreateModal(true)}
        >
          <Plus className="h-4 w-4 mr-2" />
          Add Secret
        </button>
      </div>

      {/* Security Warning */}
      <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
        <div className="flex">
          <AlertTriangle className="h-5 w-5 text-yellow-400" />
          <div className="ml-3">
            <p className="text-sm text-yellow-700">
              <strong>Security Notice:</strong> Secret values are encrypted and only revealed when explicitly requested.
              Always follow security best practices when handling sensitive data.
            </p>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-card rounded-lg shadow p-6">
          <div className="flex items-center">
            <Shield className="h-8 w-8 text-blue-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-muted-foreground">Total Secrets</p>
              <p className="text-2xl font-bold text-foreground">{secrets.length}</p>
            </div>
          </div>
        </div>
        <div className="bg-card rounded-lg shadow p-6">
          <div className="flex items-center">
            <Key className="h-8 w-8 text-green-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-muted-foreground">API Keys</p>
              <p className="text-2xl font-bold text-foreground">
                {secrets.filter(s => s.path.includes('api') || s.path.includes('key')).length}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-card rounded-lg shadow p-6">
          <div className="flex items-center">
            <Lock className="h-8 w-8 text-purple-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-muted-foreground">Databases</p>
              <p className="text-2xl font-bold text-foreground">
                {secrets.filter(s => s.path.includes('db') || s.path.includes('database')).length}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-card rounded-lg shadow p-6">
          <div className="flex items-center">
            <Calendar className="h-8 w-8 text-yellow-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-muted-foreground">Updated Today</p>
              <p className="text-2xl font-bold text-foreground">
                {secrets.filter(s => {
                  const updated = new Date(s.updated_at);
                  const today = new Date();
                  return updated.toDateString() === today.toDateString();
                }).length}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-card rounded-lg shadow">
        <div className="p-6 border-b border-border">
          <div className="flex items-center space-x-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
              <input
                type="text"
                placeholder="Search secrets by path or description..."
                className="pl-10 pr-4 py-2 w-full border border-border rounded-md focus:ring-blue-500 focus:border-blue-500"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
          </div>
        </div>

        {/* Secrets Table */}
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-border">
            <thead className="bg-accent">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Secret Path
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Description
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Version
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Last Updated
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Created By
                </th>
                <th className="relative px-6 py-3">
                  <span className="sr-only">Actions</span>
                </th>
              </tr>
            </thead>
            <tbody className="bg-card divide-y divide-border">
              {filteredSecrets.map((secret) => (
                <tr key={secret.path} className="hover:bg-accent">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="flex-shrink-0 h-10 w-10">
                        <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">
                          <Shield className="h-6 w-6 text-blue-600" />
                        </div>
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-foreground font-mono">
                          {secret.path}
                        </div>
                        {secret.metadata?.tags && (
                          <div className="flex flex-wrap gap-1 mt-1">
                            {secret.metadata.tags.map((tag) => (
                              <span
                                key={tag}
                                className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-muted text-muted-foreground"
                              >
                                {tag}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-muted-foreground">
                    {secret.metadata?.description || 'No description'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-muted-foreground">
                    v{secret.version || 1}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-muted-foreground">
                    <div className="flex items-center">
                      <Calendar className="h-4 w-4 mr-1" />
                      {new Date(secret.updated_at).toLocaleDateString()}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-muted-foreground">
                    {secret.metadata?.created_by || 'System'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex items-center space-x-2">
                      <button
                        className="text-blue-600 hover:text-blue-900"
                        onClick={() => fetchSecretValue(secret.path)}
                        title="View secret"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                      <button className="text-green-600 hover:text-green-900" title="Edit secret">
                        <Edit className="h-4 w-4" />
                      </button>
                      <button className="text-red-600 hover:text-red-900" title="Delete secret">
                        <Trash2 className="h-4 w-4" />
                      </button>
                      <button className="text-muted-foreground hover:text-foreground">
                        <MoreHorizontal className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {filteredSecrets.length === 0 && (
            <div className="text-center py-12">
              <Shield className="mx-auto h-12 w-12 text-muted-foreground" />
              <h3 className="mt-2 text-sm font-medium text-foreground">No secrets found</h3>
              <p className="mt-1 text-sm text-muted-foreground">
                {searchQuery
                  ? 'Try adjusting your search criteria'
                  : 'Get started by adding your first secret'
                }
              </p>
              {!searchQuery && (
                <div className="mt-6">
                  <button
                    className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                    onClick={() => setShowCreateModal(true)}
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Add Secret
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Secret Value Modal */}
      {selectedSecret && (
        <div className="fixed inset-0 bg-gray-600/50 dark:bg-black/50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border border-border w-96 shadow-lg rounded-md bg-card">
            <div className="mt-3">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-foreground">Secret Value</h3>
                <button
                  onClick={() => setSelectedSecret(null)}
                  className="text-muted-foreground hover:text-muted-foreground"
                >
                  ✕
                </button>
              </div>
              <p className="text-sm text-muted-foreground mb-4 font-mono">{selectedSecret}</p>

              <div className="bg-accent p-4 rounded-md">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-foreground">Value:</span>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setShowValue(!showValue)}
                      className="text-muted-foreground hover:text-foreground"
                    >
                      {showValue ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                    <button
                      onClick={() => copyToClipboard(secretValue)}
                      className="text-muted-foreground hover:text-foreground"
                    >
                      <Copy className="h-4 w-4" />
                    </button>
                  </div>
                </div>
                <div className="font-mono text-sm bg-background p-2 rounded border">
                  {showValue ? secretValue : '••••••••••••••••'}
                </div>
              </div>

              <div className="mt-6 flex justify-end space-x-3">
                <button
                  onClick={() => setSelectedSecret(null)}
                  className="px-4 py-2 text-sm font-medium text-foreground bg-muted rounded-md hover:bg-accent"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Create Secret Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-gray-600/50 dark:bg-black/50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border border-border w-full max-w-md shadow-lg rounded-md bg-card">
            <div className="mt-3">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-foreground">Create New Secret</h3>
                <button
                  onClick={() => {
                    setShowCreateModal(false);
                    setNewSecretData({ path: '', value: '', description: '', tags: '' });
                  }}
                  className="text-muted-foreground hover:text-muted-foreground"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    Secret Path
                  </label>
                  <input
                    type="text"
                    placeholder="e.g., database/password"
                    value={newSecretData.path}
                    onChange={(e) => setNewSecretData({ ...newSecretData, path: e.target.value })}
                    className="w-full px-3 py-2 border border-border rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    Secret Value
                  </label>
                  <textarea
                    placeholder="Enter the secret value"
                    value={newSecretData.value}
                    onChange={(e) => setNewSecretData({ ...newSecretData, value: e.target.value })}
                    rows={3}
                    className="w-full px-3 py-2 border border-border rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    Description (optional)
                  </label>
                  <input
                    type="text"
                    placeholder="Brief description of this secret"
                    value={newSecretData.description}
                    onChange={(e) => setNewSecretData({ ...newSecretData, description: e.target.value })}
                    className="w-full px-3 py-2 border border-border rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    Tags (optional, comma-separated)
                  </label>
                  <input
                    type="text"
                    placeholder="e.g., production, sensitive"
                    value={newSecretData.tags}
                    onChange={(e) => setNewSecretData({ ...newSecretData, tags: e.target.value })}
                    className="w-full px-3 py-2 border border-border rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>

              <div className="mt-6 flex justify-end space-x-3">
                <button
                  onClick={() => {
                    setShowCreateModal(false);
                    setNewSecretData({ path: '', value: '', description: '', tags: '' });
                  }}
                  className="px-4 py-2 text-sm font-medium text-foreground bg-muted rounded-md hover:bg-accent"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateSecret}
                  disabled={!newSecretData.path || !newSecretData.value}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:bg-blue-300 disabled:cursor-not-allowed"
                >
                  Create Secret
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Toast Notification */}
      {toast.show && (
        <div className="fixed bottom-4 right-4 z-50">
          <div className={`flex items-center p-4 rounded-md shadow-lg ${
            toast.type === 'success' ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
          } border`}>
            <div className={`flex-shrink-0 ${
              toast.type === 'success' ? 'text-green-400' : 'text-red-400'
            }`}>
              {toast.type === 'success' ? (
                <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              ) : (
                <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              )}
            </div>
            <div className="ml-3">
              <p className={`text-sm font-medium ${
                toast.type === 'success' ? 'text-green-800' : 'text-red-800'
              }`}>
                {toast.message}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function SecretsPage() {
  return (
    <RouteGuard permission="secrets.read">
      <SecretsPageContent />
    </RouteGuard>
  );
}