"use client";

import { useState } from "react";
import {
  Webhook,
  Plus,
  Search,
  Power,
  PowerOff,
  RefreshCcw,
  Trash2,
  Eye,
  EyeOff,
  Copy,
  CheckCircle2,
  XCircle,
  Clock,
  Send,
} from "lucide-react";
import { format } from "date-fns";
import { Button, Card, Input, Modal } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import { useConfirmDialog } from "@/components/shared/confirm-dialog";
import {
  useWebhooks,
  useWebhookEvents,
  useEnableWebhook,
  useDisableWebhook,
  useDeleteWebhook,
  useTestWebhook,
  useRotateWebhookSecret,
} from "@/lib/hooks/api/use-webhooks";

export default function WebhooksPage() {
  const { toast } = useToast();
  const { confirm, dialog } = useConfirmDialog();

  const [searchQuery, setSearchQuery] = useState("");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showSecrets, setShowSecrets] = useState<Record<string, boolean>>({});

  const { data: webhooks, isLoading } = useWebhooks();
  const { data: availableEvents } = useWebhookEvents();

  const enableWebhook = useEnableWebhook();
  const disableWebhook = useDisableWebhook();
  const deleteWebhook = useDeleteWebhook();
  const testWebhook = useTestWebhook();
  const rotateSecret = useRotateWebhookSecret();

  const webhookList = webhooks || [];

  const getWebhookLabel = (webhook: { description?: string | null; url: string }) => {
    const description = webhook.description?.trim();
    if (description) {
      return description;
    }

    try {
      return new URL(webhook.url).hostname;
    } catch {
      return webhook.url;
    }
  };

  const filteredWebhooks = webhookList.filter((webhook) => {
    const label = getWebhookLabel(webhook).toLowerCase();
    const query = searchQuery.toLowerCase();
    return label.includes(query) || webhook.url.toLowerCase().includes(query);
  });

  const totals = webhookList.reduce(
    (acc, webhook) => {
      acc.success += webhook.successCount || 0;
      acc.failed += webhook.failureCount || 0;
      return acc;
    },
    { success: 0, failed: 0 }
  );
  const totalDeliveries = totals.success + totals.failed;
  const successRate = totalDeliveries > 0 ? (totals.success / totalDeliveries) * 100 : 0;
  const activeCount = webhookList.filter((webhook) => webhook.isActive).length;

  const handleToggle = async (id: string, enabled: boolean) => {
    try {
      if (enabled) {
        await disableWebhook.mutateAsync(id);
        toast({ title: "Webhook disabled" });
      } else {
        await enableWebhook.mutateAsync(id);
        toast({ title: "Webhook enabled" });
      }
    } catch {
      toast({ title: "Failed to update webhook", variant: "error" });
    }
  };

  const handleDelete = async (id: string, name: string) => {
    const confirmed = await confirm({
      title: "Delete Webhook",
      description: `Are you sure you want to delete "${name}"? This will stop all event deliveries.`,
      variant: "danger",
    });

    if (confirmed) {
      try {
        await deleteWebhook.mutateAsync(id);
        toast({ title: "Webhook deleted" });
      } catch {
        toast({ title: "Failed to delete webhook", variant: "error" });
      }
    }
  };

  const handleTest = async (id: string) => {
    try {
      const result = await testWebhook.mutateAsync(id);
      if (result.success) {
        toast({
          title: "Test successful",
          description: result.statusCode ? `Response: ${result.statusCode}` : "Webhook delivered",
        });
      } else {
        toast({
          title: "Test failed",
          description: result.errorMessage || "Webhook test failed",
          variant: "error",
        });
      }
    } catch {
      toast({ title: "Test failed", variant: "error" });
    }
  };

  const handleRotateSecret = async (id: string) => {
    const confirmed = await confirm({
      title: "Rotate Secret",
      description: "This will generate a new signing secret. You'll need to update your endpoint to use the new secret.",
      variant: "warning",
    });

    if (confirmed) {
      try {
        await rotateSecret.mutateAsync(id);
        toast({ title: "Secret rotated", description: "Don't forget to update your endpoint." });
      } catch {
        toast({ title: "Failed to rotate secret", variant: "error" });
      }
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({ title: "Copied to clipboard" });
  };

  if (isLoading) {
    return <WebhooksSkeleton />;
  }

  return (
    <div className="space-y-8 animate-fade-up">
      {dialog}

      <PageHeader
        title="Webhooks"
        description="Send real-time event notifications to your endpoints"
        breadcrumbs={[
          { label: "Settings", href: "/settings" },
          { label: "Webhooks" },
        ]}
        actions={
          <Button onClick={() => setShowCreateModal(true)}>
            <Plus className="w-4 h-4 mr-2" />
            Create Webhook
          </Button>
        }
      />

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <p className="text-sm text-text-muted mb-1">Total Deliveries</p>
          <p className="text-2xl font-semibold text-text-primary">{totalDeliveries.toLocaleString()}</p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-text-muted mb-1">Success Rate</p>
          <p className="text-2xl font-semibold text-status-success">{successRate.toFixed(1)}%</p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-text-muted mb-1">Active Webhooks</p>
          <p className="text-2xl font-semibold text-text-primary">{activeCount}</p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-text-muted mb-1">Failed Deliveries</p>
          <p className="text-2xl font-semibold text-status-error">{totals.failed}</p>
        </Card>
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
        <Input
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search webhooks..."
          className="pl-10"
        />
      </div>

      {/* Webhooks List */}
      {filteredWebhooks.length === 0 ? (
        <Card className="p-12 text-center">
          <Webhook className="w-12 h-12 text-text-muted mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-text-primary mb-2">No webhooks</h3>
          <p className="text-text-muted mb-6">
            {searchQuery ? "No webhooks match your search" : "Create your first webhook to receive events"}
          </p>
          <Button onClick={() => setShowCreateModal(true)}>
            <Plus className="w-4 h-4 mr-2" />
            Create Webhook
          </Button>
        </Card>
      ) : (
        <div className="space-y-4">
          {filteredWebhooks.map((webhook) => (
            <Card key={webhook.id} className="p-6">
              <div className="flex items-start gap-6">
                {/* Status Indicator */}
                <div
                  className={cn(
                    "w-12 h-12 rounded-lg flex items-center justify-center",
                    webhook.isActive
                      ? "bg-status-success/15"
                      : "bg-surface-overlay"
                  )}
                >
                  <Webhook
                    className={cn(
                      "w-6 h-6",
                      webhook.isActive ? "text-status-success" : "text-text-muted"
                    )}
                  />
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-1">
                    <h4 className="font-semibold text-text-primary">{getWebhookLabel(webhook)}</h4>
                    <span
                      className={cn(
                        "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium",
                        webhook.isActive
                          ? "bg-status-success/15 text-status-success"
                          : "bg-surface-overlay text-text-muted"
                      )}
                    >
                      {webhook.isActive ? <CheckCircle2 className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
                      {webhook.isActive ? "Active" : "Disabled"}
                    </span>
                  </div>

                  <code className="text-sm text-accent">{webhook.url}</code>

                  <div className="flex items-center gap-4 mt-3 text-sm text-text-muted">
                    <span className="flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      Last delivery: {webhook.lastTriggeredAt ? format(new Date(webhook.lastTriggeredAt), "MMM d, HH:mm") : "Never"}
                    </span>
                    <span>Events: {webhook.events?.length || 0}</span>
                  </div>

                  {/* Secret */}
                  <div className="flex items-center gap-2 mt-3">
                    <span className="text-sm text-text-muted">Secret:</span>
                    <code className="text-sm bg-surface-overlay px-2 py-0.5 rounded">
                      {showSecrets[webhook.id]
                        ? webhook.secret || "No secret available"
                        : "••••••••••••••••"}
                    </code>
                    <button
                      onClick={() => setShowSecrets((s) => ({ ...s, [webhook.id]: !s[webhook.id] }))}
                      className="p-1 hover:text-accent transition-colors"
                    >
                      {showSecrets[webhook.id] ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                    <button
                      onClick={() => webhook.secret && copyToClipboard(webhook.secret)}
                      className="p-1 hover:text-accent transition-colors"
                      disabled={!webhook.secret}
                    >
                      <Copy className="w-4 h-4" />
                    </button>
                    <Button variant="ghost" size="sm" onClick={() => handleRotateSecret(webhook.id)}>
                      <RefreshCcw className="w-4 h-4 mr-1" />
                      Rotate
                    </Button>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleTest(webhook.id)}
                    disabled={!webhook.isActive}
                  >
                    <Send className="w-4 h-4 mr-1" />
                    Test
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleToggle(webhook.id, webhook.isActive)}
                  >
                    {webhook.isActive ? <PowerOff className="w-4 h-4" /> : <Power className="w-4 h-4" />}
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDelete(webhook.id, getWebhookLabel(webhook))}
                    className="text-status-error hover:text-status-error"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Create Modal - Simplified */}
      <Modal open={showCreateModal} onOpenChange={setShowCreateModal}>
        <div className="p-6 max-w-lg">
          <h2 className="text-xl font-semibold text-text-primary mb-6">Create Webhook</h2>
          <form className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">Description</label>
              <Input placeholder="Payment processor hook" />
            </div>
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">Endpoint URL</label>
              <Input placeholder="https://example.com/webhooks" />
            </div>
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">Events</label>
              <div className="grid grid-cols-2 gap-2 max-h-48 overflow-auto p-2 border border-border-subtle rounded-lg">
                {(availableEvents || []).map((event) => (
                  <label
                    key={event.eventType}
                    className="flex items-center gap-2 text-sm cursor-pointer"
                    title={event.description}
                  >
                    <input type="checkbox" className="rounded" />
                    <span>{event.eventType}</span>
                  </label>
                ))}
              </div>
            </div>
            <div className="flex justify-end gap-3 pt-4">
              <Button variant="ghost" onClick={() => setShowCreateModal(false)}>
                Cancel
              </Button>
              <Button>Create Webhook</Button>
            </div>
          </form>
        </div>
      </Modal>
    </div>
  );
}

function WebhooksSkeleton() {
  return (
    <div className="space-y-8 animate-pulse">
      <div className="h-8 w-48 bg-surface-overlay rounded" />
      <div className="grid grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="card p-4 h-20" />
        ))}
      </div>
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="card p-6 h-32" />
        ))}
      </div>
    </div>
  );
}
