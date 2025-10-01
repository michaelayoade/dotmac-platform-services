'use client';

import { useState } from 'react';
import {
  Plus,
  Webhook,
  Search,
  Filter,
  MoreHorizontal,
  Edit,
  Trash2,
  Eye,
  TestTube,
  Activity,
  AlertTriangle,
  Calendar,
  Clock,
  CheckCircle,
  XCircle,
  Zap,
} from 'lucide-react';
import { useWebhooks, WebhookSubscription } from '@/hooks/useWebhooks';
import { CreateWebhookModal } from '@/components/webhooks/CreateWebhookModal';
import { WebhookDetailModal } from '@/components/webhooks/WebhookDetailModal';
import { DeleteConfirmModal } from '@/components/webhooks/DeleteConfirmModal';
import { TestWebhookModal } from '@/components/webhooks/TestWebhookModal';

export default function WebhooksPage() {
  const { webhooks, loading, error, deleteWebhook } = useWebhooks();
  const [searchQuery, setSearchQuery] = useState('');
  const [eventFilter, setEventFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedWebhook, setSelectedWebhook] = useState<WebhookSubscription | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [webhookToDelete, setWebhookToDelete] = useState<WebhookSubscription | null>(null);
  const [showTestModal, setShowTestModal] = useState(false);
  const [webhookToTest, setWebhookToTest] = useState<WebhookSubscription | null>(null);

  const handleCreateWebhook = () => {
    setShowCreateModal(true);
  };

  const handleWebhookCreated = () => {
    setShowCreateModal(false);
  };

  const handleViewWebhook = (webhook: WebhookSubscription) => {
    setSelectedWebhook(webhook);
    setShowDetailModal(true);
  };

  const handleEditWebhook = (webhook: WebhookSubscription) => {
    setSelectedWebhook(webhook);
    setShowCreateModal(true);
  };

  const handleDeleteWebhook = (webhook: WebhookSubscription) => {
    setWebhookToDelete(webhook);
    setShowDeleteModal(true);
  };

  const handleTestWebhook = (webhook: WebhookSubscription) => {
    setWebhookToTest(webhook);
    setShowTestModal(true);
  };

  const handleConfirmDelete = async () => {
    if (webhookToDelete) {
      try {
        await deleteWebhook(webhookToDelete.id);
        setShowDeleteModal(false);
        setWebhookToDelete(null);
      } catch (error) {
        console.error('Failed to delete webhook:', error);
      }
    }
  };

  // Filter webhooks based on search and filters
  const filteredWebhooks = webhooks.filter(webhook => {
    const matchesSearch = searchQuery === '' ||
      webhook.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      webhook.url.toLowerCase().includes(searchQuery.toLowerCase()) ||
      webhook.description?.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesEvent = eventFilter === 'all' ||
      webhook.events.includes(eventFilter);

    const matchesStatus = statusFilter === 'all' ||
      (statusFilter === 'active' && webhook.is_active) ||
      (statusFilter === 'inactive' && !webhook.is_active);

    return matchesSearch && matchesEvent && matchesStatus;
  });

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getStatusColor = (webhook: WebhookSubscription) => {
    if (!webhook.is_active) {
      return 'text-slate-400 bg-slate-500/20 border-slate-500/30';
    }

    const failureRate = webhook.total_deliveries > 0
      ? (webhook.failed_deliveries / webhook.total_deliveries) * 100
      : 0;

    if (failureRate > 20) {
      return 'text-red-400 bg-red-500/20 border-red-500/30';
    } else if (failureRate > 10) {
      return 'text-yellow-400 bg-yellow-500/20 border-yellow-500/30';
    } else {
      return 'text-green-400 bg-green-500/20 border-green-500/30';
    }
  };

  const getStatusText = (webhook: WebhookSubscription) => {
    if (!webhook.is_active) return 'Inactive';

    const failureRate = webhook.total_deliveries > 0
      ? (webhook.failed_deliveries / webhook.total_deliveries) * 100
      : 0;

    if (failureRate > 20) return 'Issues';
    if (failureRate > 10) return 'Warning';
    return 'Healthy';
  };

  const getStatusIcon = (webhook: WebhookSubscription) => {
    if (!webhook.is_active) return XCircle;

    const failureRate = webhook.total_deliveries > 0
      ? (webhook.failed_deliveries / webhook.total_deliveries) * 100
      : 0;

    if (failureRate > 20) return XCircle;
    if (failureRate > 10) return AlertTriangle;
    return CheckCircle;
  };

  // Get unique events for filter dropdown
  const availableEvents = [...new Set(webhooks.flatMap(webhook => webhook.events))];

  if (error) {
    return (
      <div className="min-h-screen bg-slate-950 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center py-12">
            <AlertTriangle className="mx-auto h-12 w-12 text-red-400 mb-4" />
            <h3 className="text-lg font-medium text-white mb-2">Failed to load webhooks</h3>
            <p className="text-slate-400">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-white flex items-center gap-3">
              <Webhook className="h-8 w-8 text-sky-400" />
              Webhooks
            </h1>
            <p className="text-slate-400 mt-1">
              Manage webhook subscriptions to receive real-time event notifications
            </p>
          </div>
          <button
            onClick={handleCreateWebhook}
            className="flex items-center gap-2 px-4 py-2 bg-sky-500 hover:bg-sky-600 text-white rounded-lg transition-colors"
          >
            <Plus className="h-4 w-4" />
            Create Webhook
          </button>
        </div>

        {/* Filters */}
        <div className="bg-slate-900 rounded-lg p-6 mb-6">
          <div className="flex flex-wrap gap-4">
            <div className="flex items-center gap-2 flex-1 min-w-0">
              <Search className="h-4 w-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search webhooks..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="flex-1 px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-500"
              />
            </div>

            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-slate-400" />
              <select
                value={eventFilter}
                onChange={(e) => setEventFilter(e.target.value)}
                className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-sky-500"
              >
                <option value="all">All Events</option>
                {availableEvents.map((event) => (
                  <option key={event} value={event}>{event}</option>
                ))}
              </select>
            </div>

            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-sky-500"
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>
        </div>

        {/* Webhooks List */}
        <div className="bg-slate-900 rounded-lg overflow-hidden">
          {loading ? (
            <div className="p-8 text-center">
              <div className="animate-spin w-8 h-8 border-2 border-sky-500 border-t-transparent rounded-full mx-auto mb-4"></div>
              <p className="text-slate-400">Loading webhooks...</p>
            </div>
          ) : filteredWebhooks.length === 0 ? (
            <div className="p-8 text-center">
              <Webhook className="mx-auto h-12 w-12 text-slate-400 mb-4" />
              <h3 className="text-lg font-medium text-white mb-2">
                {webhooks.length === 0 ? 'No webhooks yet' : 'No matching webhooks'}
              </h3>
              <p className="text-slate-400 mb-4">
                {webhooks.length === 0
                  ? 'Create your first webhook to start receiving event notifications.'
                  : 'Try adjusting your search criteria or filters.'
                }
              </p>
              {webhooks.length === 0 && (
                <button
                  onClick={handleCreateWebhook}
                  className="flex items-center gap-2 px-4 py-2 bg-sky-500 hover:bg-sky-600 text-white rounded-lg transition-colors mx-auto"
                >
                  <Plus className="h-4 w-4" />
                  Create First Webhook
                </button>
              )}
            </div>
          ) : (
            <div className="divide-y divide-slate-700">
              {filteredWebhooks.map((webhook) => {
                const StatusIcon = getStatusIcon(webhook);

                return (
                  <div
                    key={webhook.id}
                    className="p-6 hover:bg-slate-800/50 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="text-lg font-medium text-white">
                            {webhook.name}
                          </h3>
                          <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border ${getStatusColor(webhook)}`}>
                            <StatusIcon className="h-3 w-3" />
                            {getStatusText(webhook)}
                          </span>
                        </div>

                        {webhook.description && (
                          <p className="text-slate-400 mb-3">{webhook.description}</p>
                        )}

                        <div className="flex items-center gap-6 text-sm text-slate-400 mb-3">
                          <div className="flex items-center gap-2">
                            <Zap className="h-4 w-4" />
                            <span className="font-mono text-xs">{webhook.url}</span>
                          </div>

                          <div className="flex items-center gap-2">
                            <Activity className="h-4 w-4" />
                            <span>{webhook.events.length} events</span>
                          </div>

                          <div className="flex items-center gap-2">
                            <Calendar className="h-4 w-4" />
                            <span>Created {formatDate(webhook.created_at)}</span>
                          </div>

                          {webhook.last_delivery_at && (
                            <div className="flex items-center gap-2">
                              <Clock className="h-4 w-4" />
                              <span>Last delivery {formatDate(webhook.last_delivery_at)}</span>
                            </div>
                          )}
                        </div>

                        <div className="flex items-center justify-between">
                          <div className="flex flex-wrap gap-1">
                            {webhook.events.slice(0, 3).map((event) => (
                              <span
                                key={event}
                                className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-sky-500/20 text-sky-400 border border-sky-500/30"
                              >
                                {event}
                              </span>
                            ))}
                            {webhook.events.length > 3 && (
                              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-600/20 text-slate-400 border border-slate-600/30">
                                +{webhook.events.length - 3} more
                              </span>
                            )}
                          </div>

                          <div className="flex items-center gap-4 text-sm text-slate-400">
                            <div className="text-center">
                              <div className="font-medium text-white">{webhook.total_deliveries}</div>
                              <div className="text-xs">Total</div>
                            </div>
                            <div className="text-center">
                              <div className="font-medium text-red-400">{webhook.failed_deliveries}</div>
                              <div className="text-xs">Failed</div>
                            </div>
                            <div className="text-center">
                              <div className="font-medium text-green-400">
                                {webhook.total_deliveries > 0 ?
                                  Math.round(((webhook.total_deliveries - webhook.failed_deliveries) / webhook.total_deliveries) * 100) : 100}%
                              </div>
                              <div className="text-xs">Success</div>
                            </div>
                          </div>
                        </div>
                      </div>

                      <div className="relative">
                        <WebhookActions
                          webhook={webhook}
                          onView={handleViewWebhook}
                          onEdit={handleEditWebhook}
                          onDelete={handleDeleteWebhook}
                          onTest={handleTestWebhook}
                        />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Modals */}
        {showCreateModal && (
          <CreateWebhookModal
            onClose={() => {
              setShowCreateModal(false);
              setSelectedWebhook(null);
            }}
            onWebhookCreated={handleWebhookCreated}
            editingWebhook={selectedWebhook}
          />
        )}

        {showDetailModal && selectedWebhook && (
          <WebhookDetailModal
            webhook={selectedWebhook}
            onClose={() => {
              setShowDetailModal(false);
              setSelectedWebhook(null);
            }}
            onEdit={() => {
              setShowDetailModal(false);
              setShowCreateModal(true);
            }}
            onDelete={() => {
              setShowDetailModal(false);
              handleDeleteWebhook(selectedWebhook);
            }}
            onTest={() => {
              setShowDetailModal(false);
              handleTestWebhook(selectedWebhook);
            }}
          />
        )}

        {showDeleteModal && webhookToDelete && (
          <DeleteConfirmModal
            webhook={webhookToDelete}
            onClose={() => {
              setShowDeleteModal(false);
              setWebhookToDelete(null);
            }}
            onConfirm={handleConfirmDelete}
          />
        )}

        {showTestModal && webhookToTest && (
          <TestWebhookModal
            webhook={webhookToTest}
            onClose={() => {
              setShowTestModal(false);
              setWebhookToTest(null);
            }}
          />
        )}
      </div>
    </div>
  );
}

interface WebhookActionsProps {
  webhook: WebhookSubscription;
  onView: (webhook: WebhookSubscription) => void;
  onEdit: (webhook: WebhookSubscription) => void;
  onDelete: (webhook: WebhookSubscription) => void;
  onTest: (webhook: WebhookSubscription) => void;
}

function WebhookActions({ webhook, onView, onEdit, onDelete, onTest }: WebhookActionsProps) {
  const [showDropdown, setShowDropdown] = useState(false);

  return (
    <div className="relative">
      <button
        onClick={() => setShowDropdown(!showDropdown)}
        className="text-slate-400 hover:text-white transition-colors p-2"
      >
        <MoreHorizontal className="h-4 w-4" />
      </button>

      {showDropdown && (
        <div className="absolute right-0 mt-2 w-48 bg-slate-800 rounded-md shadow-lg ring-1 ring-black ring-opacity-5 z-10">
          <div className="py-1">
            <button
              onClick={() => {
                onView(webhook);
                setShowDropdown(false);
              }}
              className="flex items-center gap-2 px-4 py-2 text-sm text-slate-300 hover:bg-slate-700 w-full text-left"
            >
              <Eye className="h-4 w-4" />
              View Details
            </button>
            <button
              onClick={() => {
                onTest(webhook);
                setShowDropdown(false);
              }}
              className="flex items-center gap-2 px-4 py-2 text-sm text-slate-300 hover:bg-slate-700 w-full text-left"
            >
              <TestTube className="h-4 w-4" />
              Test Webhook
            </button>
            <button
              onClick={() => {
                onEdit(webhook);
                setShowDropdown(false);
              }}
              className="flex items-center gap-2 px-4 py-2 text-sm text-slate-300 hover:bg-slate-700 w-full text-left"
            >
              <Edit className="h-4 w-4" />
              Edit Webhook
            </button>
            <button
              onClick={() => {
                onDelete(webhook);
                setShowDropdown(false);
              }}
              className="flex items-center gap-2 px-4 py-2 text-sm text-red-400 hover:bg-slate-700 w-full text-left"
            >
              <Trash2 className="h-4 w-4" />
              Delete Webhook
            </button>
          </div>
        </div>
      )}
    </div>
  );
}