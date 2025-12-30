"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Mail,
  Send,
  FileText,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Plus,
  Search,
  Filter,
  RefreshCcw,
  Eye,
  Edit,
  Trash2,
  Play,
  Copy,
} from "lucide-react";
import { format, formatDistanceToNow } from "date-fns";
import { Button, Card, Input, Modal } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import { ConfirmDialog, useConfirmDialog } from "@/components/shared/confirm-dialog";
import {
  useEmailTemplates,
  useEmailLogs,
  useCommunicationsDashboard,
  useCommunicationStats,
  useDeleteEmailTemplate,
  useResendEmail,
  useTestEmailTemplate,
} from "@/lib/hooks/api/use-communications";
import type { CommunicationStatus } from "@/lib/api/communications";
import { DashboardAlerts } from "@/components/features/dashboard";

type EmailStatus = "delivered" | "sent" | "pending" | "failed" | "bounced";

const statusConfig: Record<EmailStatus, { label: string; color: string; icon: React.ElementType }> = {
  delivered: { label: "Delivered", color: "bg-status-success/15 text-status-success", icon: CheckCircle2 },
  sent: { label: "Sent", color: "bg-status-info/15 text-status-info", icon: Send },
  pending: { label: "Pending", color: "bg-status-warning/15 text-status-warning", icon: Clock },
  failed: { label: "Failed", color: "bg-status-error/15 text-status-error", icon: XCircle },
  bounced: { label: "Bounced", color: "bg-status-error/15 text-status-error", icon: AlertCircle },
};

export default function CommunicationsPage() {
  const { toast } = useToast();
  const { confirm, dialog } = useConfirmDialog();

  const [activeTab, setActiveTab] = useState<"logs" | "templates">("logs");
  const [logsPage, setLogsPage] = useState(1);
  const [templatesPage, setTemplatesPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<CommunicationStatus | "all">("all");
  const [showTestModal, setShowTestModal] = useState(false);
  const [testTemplateId, setTestTemplateId] = useState<string | null>(null);
  const [testEmail, setTestEmail] = useState("");

  const { data: dashboardData } = useCommunicationsDashboard();
  const { data: stats, refetch: refetchStats } = useCommunicationStats();
  const { data: logsData, refetch: refetchLogs } = useEmailLogs({
    page: logsPage,
    pageSize: 20,
    recipientEmail: searchQuery || undefined,
    status: statusFilter !== "all" ? statusFilter : undefined,
  });
  const { data: templatesData, refetch: refetchTemplates } = useEmailTemplates({
    page: templatesPage,
    pageSize: 20,
  });

  const deleteTemplate = useDeleteEmailTemplate();
  const resendEmail = useResendEmail();
  const testTemplate = useTestEmailTemplate();

  const logs = logsData?.logs || [];
  const logsTotalPages = logsData?.pageCount || 1;
  const templates = templatesData?.templates || [];
  const templatesTotalPages = templatesData?.pageCount || 1;

  const handleDeleteTemplate = async (id: string, name: string) => {
    const confirmed = await confirm({
      title: "Delete Template",
      description: `Are you sure you want to delete "${name}"? This action cannot be undone.`,
      variant: "danger",
    });

    if (confirmed) {
      try {
        await deleteTemplate.mutateAsync(id);
        toast({ title: "Template deleted" });
      } catch {
        toast({ title: "Failed to delete template", variant: "error" });
      }
    }
  };

  const handleResend = async (id: string) => {
    try {
      await resendEmail.mutateAsync(id);
      toast({ title: "Email resent" });
    } catch {
      toast({ title: "Failed to resend email", variant: "error" });
    }
  };

  const handleTest = async () => {
    if (!testTemplateId || !testEmail) return;

    try {
      await testTemplate.mutateAsync({
        templateId: testTemplateId,
        testEmail,
      });
      toast({ title: "Test email sent" });
      setShowTestModal(false);
      setTestTemplateId(null);
      setTestEmail("");
    } catch {
      toast({ title: "Failed to send test email", variant: "error" });
    }
  };

  const openTestModal = (templateId: string) => {
    setTestTemplateId(templateId);
    setShowTestModal(true);
  };

  const refreshAll = () => {
    refetchStats();
    refetchLogs();
    refetchTemplates();
  };

  return (
    <div className="space-y-6 animate-fade-up">
      {dialog}

      <PageHeader
        title="Communications"
        description="Email templates, logs, and messaging"
        actions={
          <div className="flex items-center gap-2">
            <Button variant="ghost" onClick={refreshAll}>
              <RefreshCcw className="w-4 h-4" />
            </Button>
            <Link href="/communications/compose">
              <Button variant="outline">
                <Send className="w-4 h-4 mr-2" />
                Compose
              </Button>
            </Link>
            <Link href="/communications/templates/new">
              <Button>
                <Plus className="w-4 h-4 mr-2" />
                New Template
              </Button>
            </Link>
          </div>
        }
      />

      {/* Dashboard Alerts */}
      {dashboardData?.alerts && dashboardData.alerts.length > 0 && (
        <DashboardAlerts alerts={dashboardData.alerts} />
      )}

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card className="p-4">
          <p className="text-sm text-text-muted mb-1">Sent (24h)</p>
          <p className="text-2xl font-semibold text-text-primary">
            {stats?.sentLast24h?.toLocaleString() || 0}
          </p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-text-muted mb-1">Delivered</p>
          <p className="text-2xl font-semibold text-status-success">
            {stats?.deliveredLast24h?.toLocaleString() || 0}
          </p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-text-muted mb-1">Failed</p>
          <p className="text-2xl font-semibold text-status-error">
            {stats?.failedLast24h?.toLocaleString() || 0}
          </p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-text-muted mb-1">Open Rate</p>
          <p className="text-2xl font-semibold text-accent">
            {stats?.openRate ? `${(stats.openRate * 100).toFixed(1)}%` : "N/A"}
          </p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-text-muted mb-1">Click Rate</p>
          <p className="text-2xl font-semibold text-text-primary">
            {stats?.clickRate ? `${(stats.clickRate * 100).toFixed(1)}%` : "N/A"}
          </p>
        </Card>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 p-1 bg-surface-overlay rounded-lg w-fit">
        {[
          { id: "logs", label: "Email Logs", icon: Mail },
          { id: "templates", label: "Templates", icon: FileText },
        ].map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as typeof activeTab)}
              className={cn(
                "flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors",
                activeTab === tab.id
                  ? "bg-surface-primary text-text-primary shadow-sm"
                  : "text-text-muted hover:text-text-secondary"
              )}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Email Logs Tab */}
      {activeTab === "logs" && (
        <div className="space-y-4">
          {/* Filters */}
          <div className="flex items-center gap-4 flex-wrap">
            <div className="relative flex-1 min-w-[200px] max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
              <Input
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setLogsPage(1);
                }}
                placeholder="Search by recipient email..."
                className="pl-10"
              />
            </div>

            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-text-muted" />
              <select
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value as CommunicationStatus | "all");
                  setLogsPage(1);
                }}
                className="px-3 py-2 bg-surface-primary border border-border-subtle rounded-md text-sm"
              >
                <option value="all">All Status</option>
                <option value="delivered">Delivered</option>
                <option value="sent">Sent</option>
                <option value="pending">Pending</option>
                <option value="failed">Failed</option>
                <option value="bounced">Bounced</option>
              </select>
            </div>
          </div>

          {/* Logs Table */}
          {logs.length === 0 ? (
            <Card className="p-12 text-center">
              <Mail className="w-12 h-12 text-text-muted mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-text-primary mb-2">No emails found</h3>
              <p className="text-text-muted">
                {searchQuery || statusFilter !== "all"
                  ? "Try adjusting your filters"
                  : "Sent emails will appear here"}
              </p>
            </Card>
          ) : (
            <Card>
              <div className="overflow-x-auto">
                <table className="data-table" aria-label="Email logs"><caption className="sr-only">Email logs</caption>
                  <thead>
                    <tr className="border-b border-border-subtle">
                      <th className="text-left text-sm font-medium text-text-muted px-4 py-3">Recipient</th>
                      <th className="text-left text-sm font-medium text-text-muted px-4 py-3">Subject</th>
                      <th className="text-left text-sm font-medium text-text-muted px-4 py-3">Status</th>
                      <th className="text-left text-sm font-medium text-text-muted px-4 py-3">Sent</th>
                      <th className="text-left text-sm font-medium text-text-muted px-4 py-3">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {logs.map((log) => {
                      const status = statusConfig[log.status as EmailStatus] || statusConfig.pending;
                      const StatusIcon = status.icon;
                      const recipient =
                        log.recipientName || log.recipientEmail || "Unknown recipient";
                      const sentAt = log.sentAt ?? log.createdAt;

                      return (
                        <tr key={log.id} className="border-b border-border-subtle hover:bg-surface-overlay/50">
                          <td className="px-4 py-3">
                            <span className="text-sm text-text-primary">{recipient}</span>
                          </td>
                          <td className="px-4 py-3">
                            <span className="text-sm text-text-secondary truncate max-w-[300px] block">
                              {log.subject}
                            </span>
                          </td>
                          <td className="px-4 py-3">
                            <span className={cn("inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium", status.color)}>
                              <StatusIcon className="w-3 h-3" />
                              {status.label}
                            </span>
                          </td>
                          <td className="px-4 py-3">
                            <span className="text-sm text-text-muted">
                              {formatDistanceToNow(new Date(sentAt), { addSuffix: true })}
                            </span>
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-1">
                              <Link href={`/communications/logs/${log.id}`}>
                                <Button variant="ghost" size="sm">
                                  <Eye className="w-4 h-4" />
                                </Button>
                              </Link>
                              {(log.status === "failed" || log.status === "bounced") && (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleResend(log.id)}
                                >
                                  <RefreshCcw className="w-4 h-4" />
                                </Button>
                              )}
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {logsTotalPages > 1 && (
                <div className="flex items-center justify-between px-4 py-3 border-t border-border-subtle">
                  <p className="text-sm text-text-muted">
                    Page {logsPage} of {logsTotalPages}
                  </p>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setLogsPage((p) => Math.max(1, p - 1))}
                      disabled={logsPage === 1}
                    >
                      Previous
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setLogsPage((p) => Math.min(logsTotalPages, p + 1))}
                      disabled={logsPage === logsTotalPages}
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

      {/* Templates Tab */}
      {activeTab === "templates" && (
        <div className="space-y-4">
          {templates.length === 0 ? (
            <Card className="p-12 text-center">
              <FileText className="w-12 h-12 text-text-muted mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-text-primary mb-2">No templates yet</h3>
              <p className="text-text-muted mb-6">Create your first email template to get started</p>
              <Link href="/communications/templates/new">
                <Button>
                  <Plus className="w-4 h-4 mr-2" />
                  Create Template
                </Button>
              </Link>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {templates.map((template) => (
                <Card key={template.id} className="p-6 hover:border-border-strong transition-colors">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
                        <FileText className="w-5 h-5 text-accent" />
                      </div>
                      <div>
                        <h4 className="font-semibold text-text-primary">{template.name}</h4>
                        <p className="text-xs text-text-muted">{template.channel || "General"}</p>
                      </div>
                    </div>
                    {template.isActive ? (
                      <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-status-success/15 text-status-success">
                        Active
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-surface-overlay text-text-muted">
                        Draft
                      </span>
                    )}
                  </div>

                  <p className="text-sm text-text-muted mb-4 line-clamp-2">
                    {template.subject}
                  </p>

                  <div className="flex items-center gap-4 text-xs text-text-muted mb-4">
                    <span>
                      Updated{" "}
                      {formatDistanceToNow(new Date(template.updatedAt ?? template.createdAt), {
                        addSuffix: true,
                      })}
                    </span>
                    {template.usageCount !== undefined && (
                      <span>{template.usageCount} uses</span>
                    )}
                  </div>

                  <div className="flex items-center gap-2 pt-4 border-t border-border-subtle">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => openTestModal(template.id)}
                    >
                      <Play className="w-3.5 h-3.5 mr-1" />
                      Test
                    </Button>
                    <Link href={`/communications/templates/${template.id}/edit`}>
                      <Button variant="ghost" size="sm">
                        <Edit className="w-4 h-4" />
                      </Button>
                    </Link>
                    <Button variant="ghost" size="sm">
                      <Copy className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDeleteTemplate(template.id, template.name)}
                      className="text-status-error hover:text-status-error"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </Card>
              ))}
            </div>
          )}

          {templatesTotalPages > 1 && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-text-muted">
                Page {templatesPage} of {templatesTotalPages}
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setTemplatesPage((p) => Math.max(1, p - 1))}
                  disabled={templatesPage === 1}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setTemplatesPage((p) => Math.min(templatesTotalPages, p + 1))}
                  disabled={templatesPage === templatesTotalPages}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Test Email Modal */}
      <Modal open={showTestModal} onOpenChange={setShowTestModal}>
        <div className="p-6 max-w-md">
          <h2 className="text-xl font-semibold text-text-primary mb-2">Send Test Email</h2>
          <p className="text-text-muted mb-6">
            Send a test email using this template
          </p>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Test Email Address
              </label>
              <Input
                type="email"
                value={testEmail}
                onChange={(e) => setTestEmail(e.target.value)}
                placeholder="test@example.com"
              />
            </div>
            <div className="flex justify-end gap-3 pt-4">
              <Button variant="ghost" onClick={() => setShowTestModal(false)}>
                Cancel
              </Button>
              <Button onClick={handleTest} disabled={!testEmail || testTemplate.isPending}>
                {testTemplate.isPending ? "Sending..." : "Send Test"}
              </Button>
            </div>
          </div>
        </div>
      </Modal>
    </div>
  );
}
