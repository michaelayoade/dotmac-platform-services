"use client";

import { useState } from "react";
import { Bell, Mail, MessageSquare, Smartphone, Webhook, Check } from "lucide-react";
import { Button, Card } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import {
  useNotificationPreferences,
  useUpdateNotificationPreferences,
} from "@/lib/hooks/api/use-notifications";

interface NotificationChannel {
  id: string;
  name: string;
  description: string;
  icon: React.ElementType;
  enabled: boolean;
}

interface NotificationType {
  id: string;
  name: string;
  description: string;
  channels: {
    email: boolean;
    push: boolean;
    slack: boolean;
  };
}

export default function NotificationSettingsPage() {
  const { toast } = useToast();
  const { data: preferences, isLoading } = useNotificationPreferences();
  const updatePreferences = useUpdateNotificationPreferences();

  const [localPreferences, setLocalPreferences] = useState<Record<string, boolean>>({});
  const [hasChanges, setHasChanges] = useState(false);

  const notificationTypes: NotificationType[] = [
    {
      id: "billing",
      name: "Billing & Payments",
      description: "Invoice generated, payment received, payment failed",
      channels: { email: true, push: true, slack: false },
    },
    {
      id: "deployments",
      name: "Deployments",
      description: "Deployment started, completed, failed",
      channels: { email: true, push: true, slack: true },
    },
    {
      id: "alerts",
      name: "System Alerts",
      description: "Service outages, performance issues, security alerts",
      channels: { email: true, push: true, slack: true },
    },
    {
      id: "tickets",
      name: "Support Tickets",
      description: "New ticket, response received, ticket resolved",
      channels: { email: true, push: false, slack: false },
    },
    {
      id: "users",
      name: "User Activity",
      description: "New user signup, user invited, role changes",
      channels: { email: true, push: false, slack: true },
    },
    {
      id: "security",
      name: "Security Events",
      description: "Login from new device, password changes, 2FA updates",
      channels: { email: true, push: true, slack: false },
    },
  ];

  const storedTypePreferences =
    (preferences?.typePreferences as {
      events?: Record<string, Record<string, boolean>>;
      channels?: Record<string, boolean>;
    }) || {};
  const storedEventPreferences = storedTypePreferences.events || {};
  const storedChannelPreferences = storedTypePreferences.channels || {};

  const channelDefaults: Record<string, boolean> = {
    email: true,
    push: false,
    slack: false,
    webhook: false,
  };

  const resolveChannelEnabled = (channelId: string) => {
    const key = `${channelId}Enabled`;
    if (localPreferences[key] !== undefined) {
      return localPreferences[key];
    }

    if (channelId === "email") {
      return preferences?.emailEnabled ?? channelDefaults.email;
    }
    if (channelId === "push") {
      return preferences?.pushEnabled ?? channelDefaults.push;
    }
    if (channelId === "sms") {
      return preferences?.smsEnabled ?? false;
    }

    const stored = storedChannelPreferences[key];
    if (typeof stored === "boolean") {
      return stored;
    }
    return channelDefaults[channelId] ?? false;
  };

  const resolveTypeChannelEnabled = (typeId: string, channel: "email" | "push" | "slack") => {
    const key = `${typeId}_${channel}`;
    if (localPreferences[key] !== undefined) {
      return localPreferences[key];
    }

    const stored = storedEventPreferences[typeId]?.[channel];
    if (typeof stored === "boolean") {
      return stored;
    }

    const fallback = notificationTypes.find((type) => type.id === typeId)?.channels[channel];
    return fallback ?? false;
  };

  const channels: NotificationChannel[] = [
    {
      id: "email",
      name: "Email",
      description: "Receive notifications via email",
      icon: Mail,
      enabled: resolveChannelEnabled("email"),
    },
    {
      id: "push",
      name: "Push Notifications",
      description: "Browser and mobile push notifications",
      icon: Smartphone,
      enabled: resolveChannelEnabled("push"),
    },
    {
      id: "slack",
      name: "Slack",
      description: "Get notified in your Slack workspace",
      icon: MessageSquare,
      enabled: resolveChannelEnabled("slack"),
    },
    {
      id: "webhook",
      name: "Webhooks",
      description: "Send events to your endpoints",
      icon: Webhook,
      enabled: resolveChannelEnabled("webhook"),
    },
  ];

  const handleToggleChannel = (channelId: string) => {
    const current = resolveChannelEnabled(channelId);
    setLocalPreferences((prev) => ({
      ...prev,
      [`${channelId}Enabled`]: !current,
    }));
    setHasChanges(true);
  };

  const handleToggleNotificationType = (typeId: string, channel: "email" | "push" | "slack") => {
    const current = resolveTypeChannelEnabled(typeId, channel);
    setLocalPreferences((prev) => ({
      ...prev,
      [`${typeId}_${channel}`]: !current,
    }));
    setHasChanges(true);
  };

  const handleSave = async () => {
    try {
      if (!preferences) {
        toast({
          title: "Error",
          description: "Notification preferences are not loaded yet.",
          variant: "error",
        });
        return;
      }

      const nextChannelPreferences = {
        ...storedChannelPreferences,
        slackEnabled: resolveChannelEnabled("slack"),
        webhookEnabled: resolveChannelEnabled("webhook"),
      };

      const nextEventPreferences: Record<string, Record<string, boolean>> = {};
      for (const type of notificationTypes) {
        nextEventPreferences[type.id] = {
          email: resolveTypeChannelEnabled(type.id, "email"),
          push: resolveTypeChannelEnabled(type.id, "push"),
          slack: resolveTypeChannelEnabled(type.id, "slack"),
        };
      }

      const nextTypePreferences = {
        ...(preferences.typePreferences as Record<string, unknown>),
        channels: nextChannelPreferences,
        events: {
          ...storedEventPreferences,
          ...nextEventPreferences,
        },
      };

      await updatePreferences.mutateAsync({
        emailEnabled: resolveChannelEnabled("email"),
        pushEnabled: resolveChannelEnabled("push"),
        typePreferences: nextTypePreferences,
      });
      toast({
        title: "Preferences saved",
        description: "Your notification preferences have been updated.",
      });
      setHasChanges(false);
    } catch {
      toast({
        title: "Error",
        description: "Failed to save preferences. Please try again.",
        variant: "error",
      });
    }
  };

  if (isLoading) {
    return <NotificationsSkeleton />;
  }

  return (
    <div className="max-w-4xl space-y-8 animate-fade-up">
      <PageHeader
        title="Notifications"
        description="Configure how and when you receive notifications"
        breadcrumbs={[
          { label: "Settings", href: "/settings" },
          { label: "Notifications" },
        ]}
        actions={
          hasChanges && (
            <Button onClick={handleSave} disabled={updatePreferences.isPending}>
              {updatePreferences.isPending ? "Saving..." : "Save Changes"}
            </Button>
          )
        }
      />

      {/* Notification Channels */}
      <Card className="p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
            <Bell className="w-5 h-5 text-accent" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-text-primary">Notification Channels</h3>
            <p className="text-sm text-text-muted">Choose how you want to receive notifications</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {channels.map((channel) => {
            const Icon = channel.icon;
            const isEnabled = channel.enabled;

            return (
              <button
                key={channel.id}
                onClick={() => handleToggleChannel(channel.id)}
                className={cn(
                  "flex items-center gap-4 p-4 rounded-lg border transition-all text-left",
                  isEnabled
                    ? "border-accent bg-accent-subtle"
                    : "border-border-subtle hover:border-border-default"
                )}
              >
                <div
                  className={cn(
                    "w-10 h-10 rounded-lg flex items-center justify-center",
                    isEnabled ? "bg-accent text-text-inverse" : "bg-surface-overlay"
                  )}
                >
                  <Icon className="w-5 h-5" />
                </div>
                <div className="flex-1">
                  <p className={cn("font-medium", isEnabled ? "text-accent" : "text-text-primary")}>
                    {channel.name}
                  </p>
                  <p className="text-sm text-text-muted">{channel.description}</p>
                </div>
                {isEnabled && (
                  <Check className="w-5 h-5 text-accent" />
                )}
              </button>
            );
          })}
        </div>
      </Card>

      {/* Notification Types */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-text-primary mb-2">Notification Types</h3>
        <p className="text-sm text-text-muted mb-6">
          Customize which notifications you receive for each event type
        </p>

        <div className="space-y-4">
          {/* Header */}
          <div className="grid grid-cols-[1fr,80px,80px,80px] gap-4 px-4 pb-2 border-b border-border-subtle">
            <span className="text-sm font-medium text-text-muted">Event Type</span>
            <span className="text-sm font-medium text-text-muted text-center">Email</span>
            <span className="text-sm font-medium text-text-muted text-center">Push</span>
            <span className="text-sm font-medium text-text-muted text-center">Slack</span>
          </div>

          {/* Rows */}
          {notificationTypes.map((type) => (
            <div
              key={type.id}
              className="grid grid-cols-[1fr,80px,80px,80px] gap-4 items-center p-4 rounded-lg hover:bg-surface-overlay transition-colors"
            >
              <div>
                <p className="font-medium text-text-primary">{type.name}</p>
                <p className="text-sm text-text-muted">{type.description}</p>
              </div>
              {(["email", "push", "slack"] as const).map((channel) => (
                <div key={channel} className="flex justify-center">
                  <button
                    onClick={() => handleToggleNotificationType(type.id, channel)}
                    className={cn(
                      "w-10 h-10 rounded-lg flex items-center justify-center transition-all",
                      resolveTypeChannelEnabled(type.id, channel)
                        ? "bg-accent text-text-inverse"
                        : "bg-surface-overlay text-text-muted hover:bg-surface-overlay/70"
                    )}
                  >
                    <Check className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          ))}
        </div>
      </Card>

      {/* Quiet Hours */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-text-primary mb-2">Quiet Hours</h3>
        <p className="text-sm text-text-muted mb-6">
          Pause non-critical notifications during specified hours
        </p>

        <div className="flex items-center gap-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-text-primary mb-1.5">Start Time</label>
            <select className="w-full px-3 py-2 bg-surface-primary border border-border-subtle rounded-md text-sm">
              {Array.from({ length: 24 }, (_, i) => (
                <option key={i} value={i}>
                  {i.toString().padStart(2, "0")}:00
                </option>
              ))}
            </select>
          </div>
          <div className="flex-1">
            <label className="block text-sm font-medium text-text-primary mb-1.5">End Time</label>
            <select className="w-full px-3 py-2 bg-surface-primary border border-border-subtle rounded-md text-sm">
              {Array.from({ length: 24 }, (_, i) => (
                <option key={i} value={i}>
                  {i.toString().padStart(2, "0")}:00
                </option>
              ))}
            </select>
          </div>
          <div className="flex-1">
            <label className="block text-sm font-medium text-text-primary mb-1.5">Timezone</label>
            <select className="w-full px-3 py-2 bg-surface-primary border border-border-subtle rounded-md text-sm">
              <option>UTC</option>
              <option>America/New_York</option>
              <option>America/Los_Angeles</option>
              <option>Europe/London</option>
            </select>
          </div>
        </div>
      </Card>
    </div>
  );
}

function NotificationsSkeleton() {
  return (
    <div className="max-w-4xl space-y-8 animate-pulse">
      <div className="h-8 w-48 bg-surface-overlay rounded" />
      <div className="card p-6">
        <div className="h-6 w-40 bg-surface-overlay rounded mb-4" />
        <div className="grid grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-20 bg-surface-overlay rounded-lg" />
          ))}
        </div>
      </div>
    </div>
  );
}
