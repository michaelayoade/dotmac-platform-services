"use client";

import { use, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { format } from "date-fns";
import {
  ArrowLeft,
  Webhook,
  Link2,
  Bell,
  Settings2,
  Plus,
  X,
  Power,
  PowerOff,
  Send,
  RefreshCcw,
  Trash2,
  CheckCircle2,
  XCircle,
  Clock,
  Copy,
  Eye,
  EyeOff,
  Loader2,
} from "lucide-react";
import { Button, Card, Input } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import { useConfirmDialog } from "@/components/shared/confirm-dialog";
import {
  useWebhook,
  useUpdateWebhook,
  useDeleteWebhook,
  useEnableWebhook,
  useDisableWebhook,
  useTestWebhook,
  useRotateWebhookSecret,
  useWebhookDeliveries,
  useWebhookEvents,
} from "@/lib/hooks/api/use-webhooks";

interface WebhookDetailPageProps {
  params: Promise<{ id: string }>;
}

export default function WebhookDetailPage({ params }: WebhookDetailPageProps) {
  const { id } = use(params);
  const router = useRouter();
  const { toast } = useToast();
  const { confirm, dialog } = useConfirmDialog();

  const { data: webhook, isLoading } = useWebhook(id);
  const { data: deliveriesData } = useWebhookDeliveries(id);
  const { data: availableEvents } = useWebhookEvents();

  const updateWebhook = useUpdateWebhook();
  const deleteWebhook = useDeleteWebhook();
  const enableWebhook = useEnableWebhook();
  const disableWebhook = useDisableWebhook();
  const testWebhook = useTestWebhook();
  const rotateSecret = useRotateWebhookSecret();

  const [isEditing, setIsEditing] = useState(false);
  const [showSecret, setShowSecret] = useState(false);
  const [editedUrl, setEditedUrl] = useState("");
  const [editedDescription, setEditedDescription] = useState("");
  const [editedEvents, setEditedEvents] = useState<string[]>([]);
  const [isDirty, setIsDirty] = useState(false);

  // Populate edit form when webhook loads
  useEffect(() => {
    if (webhook) {
      setEditedUrl(webhook.url);
      setEditedDescription(webhook.description || "");
      setEditedEvents(webhook.events || []);
    }
  }, [webhook]);

  const handleToggle = async () => {
    if (!webhook) return;
    try {
      if (webhook.isActive) {
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

  const handleTest = async () => {
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

  const handleRotateSecret = async () => {
    const confirmed = await confirm({
      title: "Rotate Secret",
      description: "This will generate a new signing secret. You'll need to update your endpoint.",
      variant: "warning",
    });

    if (confirmed) {
      try {
        await rotateSecret.mutateAsync(id);
        toast({ title: "Secret rotated" });
      } catch {
        toast({ title: "Failed to rotate secret", variant: "error" });
      }
    }
  };

  const handleDelete = async () => {
    const confirmed = await confirm({
      title: "Delete Webhook",
      description: "Are you sure you want to delete this webhook? This action cannot be undone.",
      variant: "danger",
    });

    if (confirmed) {
      try {
        await deleteWebhook.mutateAsync(id);
        toast({ title: "Webhook deleted" });
        router.push("/settings/webhooks");
      } catch {
        toast({ title: "Failed to delete webhook", variant: "error" });
      }
    }
  };

  const handleToggleEvent = (eventType: string) => {
    const updated = editedEvents.includes(eventType)
      ? editedEvents.filter((e) => e !== eventType)
      : [...editedEvents, eventType];
    setEditedEvents(updated);
    setIsDirty(true);
  };

  const handleSaveChanges = async () => {
    if (editedEvents.length === 0) {
      toast({ title: "Select at least one event", variant: "error" });
      return;
    }

    try {
      await updateWebhook.mutateAsync({
        id,
        data: {
          url: editedUrl,
          description: editedDescription || undefined,
          events: editedEvents,
        },
      });
      toast({ title: "Webhook updated" });
      setIsEditing(false);
      setIsDirty(false);
    } catch {
      toast({ title: "Failed to update webhook", variant: "error" });
    }
  };

  const handleCancelEdit = () => {
    if (webhook) {
      setEditedUrl(webhook.url);
      setEditedDescription(webhook.description || "");
      setEditedEvents(webhook.events || []);
    }
    setIsEditing(false);
    setIsDirty(false);
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({ title: "Copied to clipboard" });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="w-8 h-8 animate-spin text-accent" />
      </div>
    );
  }

  if (!webhook) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <h2 className="text-xl font-semibold text-text-primary mb-2">Webhook not found</h2>
        <p className="text-text-muted mb-6">
          The webhook you&apos;re looking for doesn&apos;t exist.
        </p>
        <Button onClick={() => router.push("/settings/webhooks")}>Back to Webhooks</Button>
      </div>
    );
  }

  const deliveries = deliveriesData?.deliveries || [];
  const successRate =
    webhook.successCount + webhook.failureCount > 0
      ? (webhook.successCount / (webhook.successCount + webhook.failureCount)) * 100
      : 0;

  return (
    <div className="space-y-8 animate-fade-up">
      {dialog}

      <PageHeader
        title={webhook.description || new URL(webhook.url).hostname}
        breadcrumbs={[
          { label: "Settings", href: "/settings" },
          { label: "Webhooks", href: "/settings/webhooks" },
          { label: webhook.description || "Details" },
        ]}
        actions={
          <div className="flex items-center gap-2">
            <Button variant="ghost" onClick={() => router.back()}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
            {isEditing ? (
              <>
                <Button variant="ghost" onClick={handleCancelEdit}>
                  Cancel
                </Button>
                <Button onClick={handleSaveChanges} disabled={!isDirty || updateWebhook.isPending}>
                  {updateWebhook.isPending ? "Saving..." : "Save Changes"}
                </Button>
              </>
            ) : (
              <Button variant="outline" onClick={() => setIsEditing(true)}>
                Edit
              </Button>
            )}
          </div>
        }
      />

      {/* Status & Quick Actions */}
      <div className="flex items-center gap-4 flex-wrap">
        <span
          className={cn(
            "inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium",
            webhook.isActive
              ? "bg-status-success/15 text-status-success"
              : "bg-surface-overlay text-text-muted"
          )}
        >
          {webhook.isActive ? <CheckCircle2 className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
          {webhook.isActive ? "Active" : "Disabled"}
        </span>
        <Button variant="outline" size="sm" onClick={handleToggle}>
          {webhook.isActive ? <PowerOff className="w-4 h-4 mr-1" /> : <Power className="w-4 h-4 mr-1" />}
          {webhook.isActive ? "Disable" : "Enable"}
        </Button>
        <Button variant="outline" size="sm" onClick={handleTest} disabled={!webhook.isActive}>
          <Send className="w-4 h-4 mr-1" />
          Test
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleDelete}
          className="text-status-error hover:text-status-error"
        >
          <Trash2 className="w-4 h-4 mr-1" />
          Delete
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <p className="text-sm text-text-muted mb-1">Success Rate</p>
          <p className="text-2xl font-semibold text-status-success">{successRate.toFixed(1)}%</p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-text-muted mb-1">Successful</p>
          <p className="text-2xl font-semibold text-text-primary">{webhook.successCount}</p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-text-muted mb-1">Failed</p>
          <p className="text-2xl font-semibold text-status-error">{webhook.failureCount}</p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-text-muted mb-1">Last Triggered</p>
          <p className="text-lg font-semibold text-text-primary">
            {webhook.lastTriggeredAt
              ? format(new Date(webhook.lastTriggeredAt), "MMM d, HH:mm")
              : "Never"}
          </p>
        </Card>
      </div>

      {/* Endpoint Details */}
      <Card className="p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
            <Link2 className="w-5 h-5 text-accent" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-text-primary">Endpoint</h3>
            <p className="text-sm text-text-muted">Webhook endpoint configuration</p>
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-text-muted mb-1.5">URL</label>
            {isEditing ? (
              <Input
                value={editedUrl}
                onChange={(e) => {
                  setEditedUrl(e.target.value);
                  setIsDirty(true);
                }}
                placeholder="https://example.com/webhooks"
              />
            ) : (
              <div className="flex items-center gap-2">
                <code className="text-sm text-accent bg-surface-overlay px-3 py-2 rounded-lg flex-1">
                  {webhook.url}
                </code>
                <Button variant="ghost" size="sm" onClick={() => copyToClipboard(webhook.url)}>
                  <Copy className="w-4 h-4" />
                </Button>
              </div>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-text-muted mb-1.5">Description</label>
            {isEditing ? (
              <Input
                value={editedDescription}
                onChange={(e) => {
                  setEditedDescription(e.target.value);
                  setIsDirty(true);
                }}
                placeholder="Webhook description"
              />
            ) : (
              <p className="text-sm text-text-primary">
                {webhook.description || "No description"}
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-text-muted mb-1.5">Secret</label>
            <div className="flex items-center gap-2">
              <code className="text-sm bg-surface-overlay px-3 py-2 rounded-lg">
                {showSecret ? webhook.secret || "No secret" : "••••••••••••••••"}
              </code>
              <Button variant="ghost" size="sm" onClick={() => setShowSecret(!showSecret)}>
                {showSecret ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </Button>
              {webhook.secret && (
                <Button variant="ghost" size="sm" onClick={() => copyToClipboard(webhook.secret!)}>
                  <Copy className="w-4 h-4" />
                </Button>
              )}
              <Button variant="outline" size="sm" onClick={handleRotateSecret}>
                <RefreshCcw className="w-4 h-4 mr-1" />
                Rotate
              </Button>
            </div>
          </div>
        </div>
      </Card>

      {/* Events */}
      <Card className="p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-lg bg-highlight-subtle flex items-center justify-center">
            <Bell className="w-5 h-5 text-highlight" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-text-primary">Subscribed Events</h3>
            <p className="text-sm text-text-muted">Events this webhook receives</p>
          </div>
        </div>

        {isEditing ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-64 overflow-auto p-1">
            {(availableEvents || []).map((event) => (
              <label
                key={event.eventType}
                className={cn(
                  "flex items-start gap-3 p-3 rounded-lg cursor-pointer transition-colors",
                  editedEvents.includes(event.eventType)
                    ? "bg-accent-subtle"
                    : "bg-surface-overlay hover:bg-surface-elevated"
                )}
              >
                <input
                  type="checkbox"
                  checked={editedEvents.includes(event.eventType)}
                  onChange={() => handleToggleEvent(event.eventType)}
                  className="rounded mt-0.5"
                />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-text-primary">{event.eventType}</p>
                  <p className="text-xs text-text-muted truncate">{event.description}</p>
                </div>
              </label>
            ))}
          </div>
        ) : (
          <div className="flex flex-wrap gap-2">
            {webhook.events.map((event) => (
              <span
                key={event}
                className="inline-flex items-center px-3 py-1.5 rounded-full text-sm bg-surface-overlay text-text-secondary"
              >
                {event}
              </span>
            ))}
          </div>
        )}
      </Card>

      {/* Configuration */}
      <Card className="p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-lg bg-status-info/15 flex items-center justify-center">
            <Settings2 className="w-5 h-5 text-status-info" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-text-primary">Configuration</h3>
            <p className="text-sm text-text-muted">Retry and timeout settings</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <p className="text-sm text-text-muted mb-1">Retries</p>
            <p className="text-lg font-medium text-text-primary">
              {webhook.retryEnabled ? `${webhook.maxRetries} attempts` : "Disabled"}
            </p>
          </div>
          <div>
            <p className="text-sm text-text-muted mb-1">Timeout</p>
            <p className="text-lg font-medium text-text-primary">{webhook.timeoutSeconds}s</p>
          </div>
          <div>
            <p className="text-sm text-text-muted mb-1">Created</p>
            <p className="text-lg font-medium text-text-primary">
              {format(new Date(webhook.createdAt), "MMM d, yyyy")}
            </p>
          </div>
        </div>
      </Card>

      {/* Recent Deliveries */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-status-warning/15 flex items-center justify-center">
              <Clock className="w-5 h-5 text-status-warning" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">Recent Deliveries</h3>
              <p className="text-sm text-text-muted">Last webhook delivery attempts</p>
            </div>
          </div>
        </div>

        {deliveries.length === 0 ? (
          <div className="text-center py-8">
            <Clock className="w-8 h-8 text-text-muted mx-auto mb-2" />
            <p className="text-text-muted">No deliveries yet</p>
          </div>
        ) : (
          <div className="space-y-2">
            {deliveries.slice(0, 10).map((delivery) => (
              <div
                key={delivery.id}
                className="flex items-center justify-between p-3 bg-surface-overlay rounded-lg"
              >
                <div className="flex items-center gap-3">
                  {delivery.status === "success" ? (
                    <CheckCircle2 className="w-5 h-5 text-status-success" />
                  ) : delivery.status === "failed" ? (
                    <XCircle className="w-5 h-5 text-status-error" />
                  ) : (
                    <Clock className="w-5 h-5 text-status-warning" />
                  )}
                  <div>
                    <p className="text-sm font-medium text-text-primary">{delivery.eventType}</p>
                    <p className="text-xs text-text-muted">
                      {format(new Date(delivery.createdAt), "MMM d, HH:mm:ss")}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  {delivery.responseCode && (
                    <span
                      className={cn(
                        "text-sm font-mono",
                        delivery.responseCode >= 200 && delivery.responseCode < 300
                          ? "text-status-success"
                          : "text-status-error"
                      )}
                    >
                      {delivery.responseCode}
                    </span>
                  )}
                  {delivery.durationMs && (
                    <p className="text-xs text-text-muted">{delivery.durationMs}ms</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
