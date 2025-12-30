"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  ArrowLeft,
  Webhook,
  Link2,
  Bell,
  Settings2,
  Plus,
  X,
} from "lucide-react";
import { Button, Card, Input } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import { useCreateWebhook, useWebhookEvents } from "@/lib/hooks/api/use-webhooks";
import { createWebhookSchema, type CreateWebhookData } from "@/lib/schemas/webhooks";

export default function NewWebhookPage() {
  const router = useRouter();
  const { toast } = useToast();

  const createWebhook = useCreateWebhook();
  const { data: availableEvents } = useWebhookEvents();

  const [headers, setHeaders] = useState<Array<{ key: string; value: string }>>([]);
  const [newHeaderKey, setNewHeaderKey] = useState("");
  const [newHeaderValue, setNewHeaderValue] = useState("");

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setValue,
    watch,
  } = useForm<CreateWebhookData>({
    resolver: zodResolver(createWebhookSchema),
    defaultValues: {
      url: "",
      description: "",
      events: [],
      isActive: true,
      retryEnabled: true,
      maxRetries: 3,
      timeoutSeconds: 30,
    },
  });

  const selectedEvents = watch("events") || [];
  const isActive = watch("isActive");
  const retryEnabled = watch("retryEnabled");

  const handleToggleEvent = (eventType: string) => {
    const current = selectedEvents;
    const updated = current.includes(eventType)
      ? current.filter((e) => e !== eventType)
      : [...current, eventType];
    setValue("events", updated, { shouldValidate: true });
  };

  const handleAddHeader = () => {
    if (!newHeaderKey.trim()) return;
    setHeaders([...headers, { key: newHeaderKey.trim(), value: newHeaderValue }]);
    setNewHeaderKey("");
    setNewHeaderValue("");
  };

  const handleRemoveHeader = (index: number) => {
    setHeaders(headers.filter((_, i) => i !== index));
  };

  const onSubmit = async (data: CreateWebhookData) => {
    try {
      // Convert headers array to record
      const headersRecord = headers.reduce(
        (acc, { key, value }) => {
          acc[key] = value;
          return acc;
        },
        {} as Record<string, string>
      );

      const result = await createWebhook.mutateAsync({
        ...data,
        headers: Object.keys(headersRecord).length > 0 ? headersRecord : undefined,
      });

      toast({
        title: "Webhook created",
        description: "Your webhook has been configured successfully.",
      });

      router.push(`/settings/webhooks/${result.id}`);
    } catch {
      toast({
        title: "Failed to create webhook",
        description: "Please check your configuration and try again.",
        variant: "error",
      });
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8 animate-fade-up">
      <PageHeader
        title="New Webhook"
        breadcrumbs={[
          { label: "Settings", href: "/settings" },
          { label: "Webhooks", href: "/settings/webhooks" },
          { label: "New" },
        ]}
        actions={
          <Button variant="ghost" onClick={() => router.back()}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        }
      />

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Endpoint Configuration */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
              <Link2 className="w-5 h-5 text-accent" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">Endpoint</h3>
              <p className="text-sm text-text-muted">Configure your webhook endpoint</p>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Endpoint URL <span className="text-status-error">*</span>
              </label>
              <Input
                {...register("url")}
                placeholder="https://example.com/webhooks"
                className={cn(errors.url && "border-status-error")}
              />
              {errors.url && (
                <p className="text-xs text-status-error mt-1">{errors.url.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Description
              </label>
              <Input
                {...register("description")}
                placeholder="Payment processor webhook"
              />
            </div>

            <div>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={isActive}
                  onChange={(e) => setValue("isActive", e.target.checked)}
                  className="rounded"
                />
                <span className="text-sm font-medium text-text-primary">
                  Enable webhook immediately
                </span>
              </label>
              <p className="text-xs text-text-muted mt-1 ml-6">
                Disabled webhooks won&apos;t receive any events
              </p>
            </div>
          </div>
        </Card>

        {/* Event Selection */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-highlight-subtle flex items-center justify-center">
              <Bell className="w-5 h-5 text-highlight" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">Events</h3>
              <p className="text-sm text-text-muted">Select which events to subscribe to</p>
            </div>
          </div>

          {errors.events && (
            <p className="text-sm text-status-error mb-4">{errors.events.message}</p>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-64 overflow-auto p-1">
            {(availableEvents || []).map((event) => (
              <label
                key={event.eventType}
                className={cn(
                  "flex items-start gap-3 p-3 rounded-lg cursor-pointer transition-colors",
                  selectedEvents.includes(event.eventType)
                    ? "bg-accent-subtle"
                    : "bg-surface-overlay hover:bg-surface-elevated"
                )}
              >
                <input
                  type="checkbox"
                  checked={selectedEvents.includes(event.eventType)}
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

          {selectedEvents.length > 0 && (
            <p className="text-sm text-text-muted mt-4">
              {selectedEvents.length} event{selectedEvents.length !== 1 ? "s" : ""} selected
            </p>
          )}
        </Card>

        {/* Advanced Settings */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-status-info/15 flex items-center justify-center">
              <Settings2 className="w-5 h-5 text-status-info" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">Advanced Settings</h3>
              <p className="text-sm text-text-muted">Retry and timeout configuration</p>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="flex items-center gap-2 cursor-pointer mb-4">
                <input
                  type="checkbox"
                  checked={retryEnabled}
                  onChange={(e) => setValue("retryEnabled", e.target.checked)}
                  className="rounded"
                />
                <span className="text-sm font-medium text-text-primary">
                  Enable automatic retries
                </span>
              </label>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-text-primary mb-1.5">
                  Max Retries
                </label>
                <Input
                  {...register("maxRetries", { valueAsNumber: true })}
                  type="number"
                  min={0}
                  max={10}
                  disabled={!retryEnabled}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-text-primary mb-1.5">
                  Timeout (seconds)
                </label>
                <Input
                  {...register("timeoutSeconds", { valueAsNumber: true })}
                  type="number"
                  min={5}
                  max={60}
                />
              </div>
            </div>
          </div>
        </Card>

        {/* Custom Headers */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-status-warning/15 flex items-center justify-center">
              <Webhook className="w-5 h-5 text-status-warning" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">Custom Headers</h3>
              <p className="text-sm text-text-muted">Add custom HTTP headers to requests</p>
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Input
                value={newHeaderKey}
                onChange={(e) => setNewHeaderKey(e.target.value)}
                placeholder="Header name"
                className="flex-1"
              />
              <Input
                value={newHeaderValue}
                onChange={(e) => setNewHeaderValue(e.target.value)}
                placeholder="Header value"
                className="flex-1"
              />
              <Button type="button" variant="outline" onClick={handleAddHeader}>
                <Plus className="w-4 h-4" />
              </Button>
            </div>

            {headers.length > 0 && (
              <div className="space-y-2">
                {headers.map((header, index) => (
                  <div
                    key={index}
                    className="flex items-center gap-2 p-3 bg-surface-overlay rounded-lg"
                  >
                    <code className="text-sm font-mono text-accent flex-1">{header.key}</code>
                    <code className="text-sm font-mono text-text-secondary flex-1 truncate">
                      {header.value || "(empty)"}
                    </code>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => handleRemoveHeader(index)}
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </Card>

        {/* Actions */}
        <div className="flex items-center justify-end gap-3 pt-4">
          <Button type="button" variant="ghost" onClick={() => router.back()}>
            Cancel
          </Button>
          <Button type="submit" disabled={isSubmitting || createWebhook.isPending}>
            {isSubmitting || createWebhook.isPending ? "Creating..." : "Create Webhook"}
          </Button>
        </div>
      </form>
    </div>
  );
}
