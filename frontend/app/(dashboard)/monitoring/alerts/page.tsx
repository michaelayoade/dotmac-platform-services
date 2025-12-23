"use client";

import { useState } from "react";
import {
  Bell,
  AlertTriangle,
  Plus,
  Settings,
  RefreshCcw,
  CheckCircle2,
  Mail,
  MessageSquare,
  Webhook,
  Trash2,
  Play,
  Pause,
  Eye,
  Check,
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { Button, Card } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import { useConfirmDialog } from "@/components/shared/confirm-dialog";
import {
  useAlertRules,
  useAlertChannels,
  useAlertHistory,
  useAlertStats,
  useEnableAlertRule,
  useDisableAlertRule,
  useDeleteAlertRule,
  useAcknowledgeAlert,
  useResolveAlert,
  useTestAlertChannel,
  useEnableAlertChannel,
  useDisableAlertChannel,
} from "@/lib/hooks/api/use-alerts";

type AlertSeverity = "critical" | "warning" | "info";
type AlertStatus = "firing" | "resolved";

const severityConfig: Record<AlertSeverity, { label: string; color: string }> = {
  critical: { label: "Critical", color: "bg-status-error/15 text-status-error" },
  warning: { label: "Warning", color: "bg-status-warning/15 text-status-warning" },
  info: { label: "Info", color: "bg-status-info/15 text-status-info" },
};

const statusConfig: Record<AlertStatus, { label: string; color: string; icon: React.ElementType }> = {
  firing: { label: "Firing", color: "bg-status-error/15 text-status-error", icon: AlertTriangle },
  resolved: { label: "Resolved", color: "bg-status-success/15 text-status-success", icon: CheckCircle2 },
};

const channelTypeConfig: Record<string, { label: string; icon: React.ElementType }> = {
  email: { label: "Email", icon: Mail },
  slack: { label: "Slack", icon: MessageSquare },
  discord: { label: "Discord", icon: MessageSquare },
  teams: { label: "Microsoft Teams", icon: Bell },
  webhook: { label: "Webhook", icon: Webhook },
  sms: { label: "SMS", icon: Bell },
};

export default function AlertsPage() {
  const { toast } = useToast();
  const { confirm, dialog } = useConfirmDialog();

  const [activeTab, setActiveTab] = useState<"history" | "rules" | "channels">("history");
  const [historyPage, setHistoryPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<AlertStatus | "all">("all");

  const { data: stats, refetch: refetchStats } = useAlertStats();
  const { data: rulesData, refetch: refetchRules } = useAlertRules();
  const { data: channelsData, refetch: refetchChannels } = useAlertChannels();
  const { data: historyData, refetch: refetchHistory } = useAlertHistory({
    page: historyPage,
    pageSize: 20,
    status: statusFilter !== "all" ? statusFilter : undefined,
  });

  const enableRule = useEnableAlertRule();
  const disableRule = useDisableAlertRule();
  const deleteRule = useDeleteAlertRule();
  const acknowledgeAlert = useAcknowledgeAlert();
  const resolveAlert = useResolveAlert();
  const testChannel = useTestAlertChannel();
  const enableChannel = useEnableAlertChannel();
  const disableChannel = useDisableAlertChannel();

  const rules = rulesData || [];
  const channels = channelsData || [];
  const alerts = historyData?.events || [];
  const historyTotalPages = historyData?.pageCount || 1;

  const handleToggleRule = async (id: string, isEnabled: boolean) => {
    try {
      if (isEnabled) {
        await disableRule.mutateAsync(id);
        toast({ title: "Rule disabled" });
      } else {
        await enableRule.mutateAsync(id);
        toast({ title: "Rule enabled" });
      }
    } catch {
      toast({ title: "Failed to update rule", variant: "error" });
    }
  };

  const handleDeleteRule = async (id: string, name: string) => {
    const confirmed = await confirm({
      title: "Delete Alert Rule",
      description: `Are you sure you want to delete "${name}"? This action cannot be undone.`,
      variant: "danger",
    });

    if (confirmed) {
      try {
        await deleteRule.mutateAsync(id);
        toast({ title: "Rule deleted" });
      } catch {
        toast({ title: "Failed to delete rule", variant: "error" });
      }
    }
  };

  const handleAcknowledge = async (alertId: string) => {
    try {
      await acknowledgeAlert.mutateAsync({ alertId });
      toast({ title: "Alert acknowledged" });
    } catch {
      toast({ title: "Failed to acknowledge alert", variant: "error" });
    }
  };

  const handleResolve = async (alertId: string) => {
    try {
      await resolveAlert.mutateAsync({ alertId });
      toast({ title: "Alert resolved" });
    } catch {
      toast({ title: "Failed to resolve alert", variant: "error" });
    }
  };

  const handleTestChannel = async (id: string) => {
    try {
      await testChannel.mutateAsync(id);
      toast({ title: "Test notification sent" });
    } catch {
      toast({ title: "Failed to send test notification", variant: "error" });
    }
  };

  const handleToggleChannel = async (channel: (typeof channels)[number]) => {
    const payload = {
      id: channel.id,
      name: channel.name,
      channelType: channel.channelType,
      webhookUrl: "",
      enabled: !channel.enabled,
      tenantId: channel.tenantId ?? undefined,
      severities: channel.severities ?? undefined,
      alertNames: channel.alertNames ?? undefined,
      alertCategories: channel.alertCategories ?? undefined,
    };

    try {
      if (channel.enabled) {
        await disableChannel.mutateAsync(payload);
        toast({ title: "Channel disabled" });
      } else {
        await enableChannel.mutateAsync(payload);
        toast({ title: "Channel enabled" });
      }
    } catch {
      toast({ title: "Failed to update channel", variant: "error" });
    }
  };

  const refreshAll = () => {
    refetchStats();
    refetchRules();
    refetchChannels();
    refetchHistory();
  };

  return (
    <div className="space-y-6 animate-fade-up">
      {dialog}

      <PageHeader
        title="Alert Management"
        description="Configure alert rules, channels, and view alert history"
        breadcrumbs={[
          { label: "Monitoring", href: "/monitoring" },
          { label: "Alerts" },
        ]}
        actions={
          <div className="flex items-center gap-2">
            <Button variant="ghost" onClick={refreshAll}>
              <RefreshCcw className="w-4 h-4" />
            </Button>
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              New Rule
            </Button>
          </div>
        }
      />

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <p className="text-sm text-text-muted mb-1">Total Alerts</p>
          <p className="text-2xl font-semibold text-text-primary">
            {stats?.total || 0}
          </p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-text-muted mb-1">Firing</p>
          <p className="text-2xl font-semibold text-status-error">
            {stats?.firing || 0}
          </p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-text-muted mb-1">Resolved</p>
          <p className="text-2xl font-semibold text-status-success">
            {stats?.resolved || 0}
          </p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-text-muted mb-1">Critical</p>
          <p className="text-2xl font-semibold text-status-error">
            {stats?.bySeverity?.critical || 0}
          </p>
        </Card>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 p-1 bg-surface-overlay rounded-lg w-fit">
        {[
          { id: "history", label: "Alert History" },
          { id: "rules", label: "Alert Rules" },
          { id: "channels", label: "Notification Channels" },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as typeof activeTab)}
            className={cn(
              "px-4 py-2 rounded-md text-sm font-medium transition-colors",
              activeTab === tab.id
                ? "bg-surface-primary text-text-primary shadow-sm"
                : "text-text-muted hover:text-text-secondary"
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Alert History Tab */}
      {activeTab === "history" && (
        <div className="space-y-4">
          {/* Filters */}
          <div className="flex items-center gap-4">
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value as AlertStatus | "all");
                setHistoryPage(1);
              }}
              className="px-3 py-2 bg-surface-primary border border-border-subtle rounded-md text-sm"
            >
              <option value="all">All Status</option>
              <option value="firing">Firing</option>
              <option value="resolved">Resolved</option>
            </select>
          </div>

          {/* Alerts List */}
          {alerts.length === 0 ? (
            <Card className="p-12 text-center">
              <CheckCircle2 className="w-12 h-12 text-status-success mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-text-primary mb-2">No alerts</h3>
              <p className="text-text-muted">
                {statusFilter !== "all"
                  ? "No alerts match the current filter"
                  : "All systems operational"}
              </p>
            </Card>
          ) : (
            <Card>
              <div className="divide-y divide-border-subtle">
                {alerts.map((alert) => {
                  const severity = severityConfig[alert.severity as AlertSeverity] || severityConfig.warning;
                  const status = statusConfig[alert.status as AlertStatus] || statusConfig.firing;
                  const StatusIcon = status.icon;

                  return (
                    <div key={alert.id} className="p-4">
                      <div className="flex items-start gap-4">
                        <div className={cn("w-10 h-10 rounded-lg flex items-center justify-center", status.color.split(" ")[0])}>
                          <StatusIcon className={cn("w-5 h-5", status.color.split(" ")[1])} />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <h4 className="font-semibold text-text-primary">{alert.alertName}</h4>
                            <span className={cn("px-2 py-0.5 rounded-full text-xs font-medium", severity.color)}>
                              {severity.label}
                            </span>
                            <span className={cn("px-2 py-0.5 rounded-full text-xs font-medium", status.color)}>
                              {status.label}
                            </span>
                          </div>
                          <p className="text-sm text-text-muted mb-2">{alert.message}</p>
                          <div className="flex items-center gap-4 text-xs text-text-muted">
                            <span>
                              Triggered {formatDistanceToNow(new Date(alert.createdAt), { addSuffix: true })}
                            </span>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {alert.status === "firing" && (
                            <>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleAcknowledge(alert.id)}
                              >
                                <Eye className="w-4 h-4 mr-1" />
                                Acknowledge
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleResolve(alert.id)}
                              >
                                <Check className="w-4 h-4 mr-1" />
                                Resolve
                              </Button>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              {historyTotalPages > 1 && (
                <div className="flex items-center justify-between px-4 py-3 border-t border-border-subtle">
                  <p className="text-sm text-text-muted">
                    Page {historyPage} of {historyTotalPages}
                  </p>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setHistoryPage((p) => Math.max(1, p - 1))}
                      disabled={historyPage === 1}
                    >
                      Previous
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setHistoryPage((p) => Math.min(historyTotalPages, p + 1))}
                      disabled={historyPage === historyTotalPages}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </Card>
          )}
        </div>
      )}

      {/* Alert Rules Tab */}
      {activeTab === "rules" && (
        <div className="space-y-4">
          {rules.length === 0 ? (
            <Card className="p-12 text-center">
              <Settings className="w-12 h-12 text-text-muted mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-text-primary mb-2">No alert rules</h3>
              <p className="text-text-muted mb-6">Create your first alert rule to start monitoring</p>
              <Button>
                <Plus className="w-4 h-4 mr-2" />
                Create Rule
              </Button>
            </Card>
          ) : (
            <div className="space-y-4">
              {rules.map((rule) => {
                const severity = severityConfig[rule.severity as AlertSeverity] || severityConfig.warning;

                return (
                  <Card key={rule.id} className="p-6">
                    <div className="flex items-start gap-4">
                      <div
                        className={cn(
                          "w-10 h-10 rounded-lg flex items-center justify-center",
                          rule.enabled ? "bg-status-success/15" : "bg-surface-overlay"
                        )}
                      >
                        <Bell
                          className={cn(
                            "w-5 h-5",
                            rule.enabled ? "text-status-success" : "text-text-muted"
                          )}
                        />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="font-semibold text-text-primary">{rule.name}</h4>
                          <span className={cn("px-2 py-0.5 rounded-full text-xs font-medium", severity.color)}>
                            {severity.label}
                          </span>
                          <span
                            className={cn(
                              "px-2 py-0.5 rounded-full text-xs font-medium",
                              rule.enabled
                                ? "bg-status-success/15 text-status-success"
                                : "bg-surface-overlay text-text-muted"
                            )}
                          >
                            {rule.enabled ? "Enabled" : "Disabled"}
                          </span>
                        </div>
                        {rule.description && (
                          <p className="text-sm text-text-muted mb-2">{rule.description}</p>
                        )}
                        <div className="flex items-center gap-4 text-sm text-text-muted">
                          <span>
                            Condition: {rule.condition.metric} {rule.condition.operator} {rule.condition.threshold}
                            {rule.condition.duration ? ` for ${rule.condition.duration}` : ""}
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleToggleRule(rule.id, rule.enabled)}
                        >
                          {rule.enabled ? (
                            <Pause className="w-4 h-4" />
                          ) : (
                            <Play className="w-4 h-4" />
                          )}
                        </Button>
                        <Button variant="ghost" size="sm">
                          <Settings className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteRule(rule.id, rule.name)}
                          className="text-status-error hover:text-status-error"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </Card>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Notification Channels Tab */}
      {activeTab === "channels" && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              Add Channel
            </Button>
          </div>

          {channels.length === 0 ? (
            <Card className="p-12 text-center">
              <Bell className="w-12 h-12 text-text-muted mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-text-primary mb-2">No notification channels</h3>
              <p className="text-text-muted mb-6">Add a channel to receive alert notifications</p>
              <Button>
                <Plus className="w-4 h-4 mr-2" />
                Add Channel
              </Button>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {channels.map((channel) => {
                const typeConfig = channelTypeConfig[channel.channelType] || channelTypeConfig.webhook;
                const TypeIcon = typeConfig.icon;
                const alertNames = channel.alertNames ?? [];
                const alertCategories = channel.alertCategories ?? [];
                const severities = channel.severities ?? [];
                const channelSummary = alertNames.length
                  ? `Alerts: ${alertNames.join(", ")}`
                  : alertCategories.length
                  ? `Categories: ${alertCategories.join(", ")}`
                  : severities.length
                  ? `Severities: ${severities.join(", ")}`
                  : "All alerts";

                return (
                  <Card key={channel.id} className="p-6">
                    <div className="flex items-start gap-4">
                      <div
                        className={cn(
                          "w-10 h-10 rounded-lg flex items-center justify-center",
                          channel.enabled ? "bg-accent-subtle" : "bg-surface-overlay"
                        )}
                      >
                        <TypeIcon
                          className={cn(
                            "w-5 h-5",
                            channel.enabled ? "text-accent" : "text-text-muted"
                          )}
                        />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="font-semibold text-text-primary">{channel.name}</h4>
                          <span className="text-xs text-text-muted">{typeConfig.label}</span>
                        </div>
                        <p className="text-sm text-text-muted mb-2">
                          {channelSummary}
                        </p>
                        <span
                          className={cn(
                            "px-2 py-0.5 rounded-full text-xs font-medium",
                            channel.enabled
                              ? "bg-status-success/15 text-status-success"
                              : "bg-surface-overlay text-text-muted"
                          )}
                        >
                          {channel.enabled ? "Enabled" : "Disabled"}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 mt-4 pt-4 border-t border-border-subtle">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleTestChannel(channel.id)}
                      >
                        Test
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleToggleChannel(channel)}
                      >
                        {channel.enabled ? "Disable" : "Enable"}
                      </Button>
                      <Button variant="ghost" size="sm">
                        <Settings className="w-4 h-4" />
                      </Button>
                    </div>
                  </Card>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
