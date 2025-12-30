"use client";

import { use, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Save, Eye, Loader2, Trash2, Play } from "lucide-react";
import { Button, Card, Input, Modal } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { PageHeader } from "@/components/shared/page-header";
import { ConfirmDialog, useConfirmDialog } from "@/components/shared/confirm-dialog";
import {
  useEmailTemplate,
  useUpdateEmailTemplate,
  useDeleteEmailTemplate,
  useTestEmailTemplate,
} from "@/lib/hooks/api/use-communications";

interface EditTemplatePageProps {
  params: Promise<{ id: string }>;
}

export default function EditTemplatePage({ params }: EditTemplatePageProps) {
  const { id } = use(params);
  const router = useRouter();
  const { toast } = useToast();
  const { confirm, dialog } = useConfirmDialog();

  const { data: template, isLoading } = useEmailTemplate(id);
  const updateTemplate = useUpdateEmailTemplate();
  const deleteTemplate = useDeleteEmailTemplate();
  const testTemplate = useTestEmailTemplate();

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [channel, setChannel] = useState("email");
  const [subject, setSubject] = useState("");
  const [bodyHtml, setBodyHtml] = useState("");
  const [bodyText, setBodyText] = useState("");
  const [isActive, setIsActive] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [showTestModal, setShowTestModal] = useState(false);
  const [testEmail, setTestEmail] = useState("");

  // Load template data
  useEffect(() => {
    if (template) {
      setName(template.name);
      setDescription(template.description || "");
      setChannel(template.channel || "email");
      setSubject(template.subject || template.subjectTemplate || "");
      setBodyHtml(template.bodyHtml || "");
      setBodyText(template.bodyText || "");
      setIsActive(template.isActive);
    }
  }, [template]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!name.trim()) {
      toast({ title: "Name is required", variant: "error" });
      return;
    }

    try {
      await updateTemplate.mutateAsync({
        id,
        data: {
          name: name.trim(),
          description: description.trim() || undefined,
          channel,
          subject: subject.trim() || undefined,
          subjectTemplate: subject.trim() || undefined,
          bodyHtml: bodyHtml.trim() || undefined,
          bodyText: bodyText.trim() || undefined,
          isActive,
        },
      });

      toast({ title: "Template saved successfully" });
    } catch {
      toast({ title: "Failed to save template", variant: "error" });
    }
  };

  const handleDelete = async () => {
    const confirmed = await confirm({
      title: "Delete Template",
      description: `Are you sure you want to delete "${name}"? This action cannot be undone.`,
      variant: "danger",
    });

    if (confirmed) {
      try {
        await deleteTemplate.mutateAsync(id);
        toast({ title: "Template deleted" });
        router.push("/communications");
      } catch {
        toast({ title: "Failed to delete template", variant: "error" });
      }
    }
  };

  const handleTest = async () => {
    if (!testEmail) return;

    try {
      await testTemplate.mutateAsync({
        templateId: id,
        testEmail,
      });
      toast({ title: "Test email sent successfully" });
      setShowTestModal(false);
      setTestEmail("");
    } catch {
      toast({ title: "Failed to send test email", variant: "error" });
    }
  };

  if (isLoading) {
    return <TemplateEditorSkeleton />;
  }

  if (!template) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <h2 className="text-xl font-semibold text-text-primary mb-2">Template not found</h2>
        <Button onClick={() => router.push("/communications")}>Back to Communications</Button>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-4xl animate-fade-up">
      {dialog}

      <PageHeader
        title={template.name}
        breadcrumbs={[
          { label: "Communications", href: "/communications" },
          { label: "Edit Template" },
        ]}
        actions={
          <div className="flex items-center gap-3">
            <Button
              type="button"
              variant="ghost"
              onClick={handleDelete}
              className="text-status-error hover:text-status-error"
            >
              <Trash2 className="w-4 h-4" />
            </Button>
            <Button type="button" variant="outline" onClick={() => setShowTestModal(true)}>
              <Play className="w-4 h-4 mr-2" />
              Test
            </Button>
            <Button type="button" variant="ghost" onClick={() => router.back()}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
            <Button
              type="submit"
              disabled={updateTemplate.isPending}
              className="shadow-glow-sm hover:shadow-glow"
            >
              {updateTemplate.isPending ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Save className="w-4 h-4 mr-2" />
              )}
              Save Changes
            </Button>
          </div>
        }
      />

      {/* Stats */}
      {template.usageCount !== undefined && (
        <div className="flex items-center gap-6 text-sm text-text-muted">
          <span>Used {template.usageCount} times</span>
          {template.lastUsedAt && (
            <span>
              Last used {new Date(template.lastUsedAt).toLocaleDateString()}
            </span>
          )}
        </div>
      )}

      {/* Basic Info */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-text-primary mb-6">Template Details</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-text-primary mb-1.5">
              Template Name <span className="text-status-error">*</span>
            </label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Welcome Email"
              required
            />
          </div>

          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-text-primary mb-1.5">
              Description
            </label>
            <Input
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Brief description of this template"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-text-primary mb-1.5">
              Channel
            </label>
            <select
              value={channel}
              onChange={(e) => setChannel(e.target.value)}
              className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent"
            >
              <option value="email">Email</option>
              <option value="transactional">Transactional</option>
              <option value="marketing">Marketing</option>
              <option value="notification">Notification</option>
            </select>
          </div>

          <div className="flex items-center">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={isActive}
                onChange={(e) => setIsActive(e.target.checked)}
                className="w-4 h-4 rounded border-border accent-accent"
              />
              <div>
                <span className="text-sm font-medium text-text-primary">Active</span>
                <p className="text-xs text-text-muted">Template can be used for sending</p>
              </div>
            </label>
          </div>
        </div>
      </Card>

      {/* Email Content */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-text-primary">Email Content</h3>
          <Button type="button" variant="outline" onClick={() => setShowPreview(true)}>
            <Eye className="w-4 h-4 mr-2" />
            Preview
          </Button>
        </div>

        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-text-primary mb-1.5">
              Subject Line
            </label>
            <Input
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="e.g., Welcome to {{company_name}}!"
            />
            <p className="text-xs text-text-muted mt-1">
              Use {"{{variable_name}}"} for dynamic content
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-text-primary mb-1.5">
              HTML Body
            </label>
            <textarea
              value={bodyHtml}
              onChange={(e) => setBodyHtml(e.target.value)}
              placeholder="<html>&#10;  <body>&#10;    <h1>Hello {{name}}</h1>&#10;    <p>Welcome to our platform!</p>&#10;  </body>&#10;</html>"
              rows={12}
              className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent font-mono text-sm resize-none"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-text-primary mb-1.5">
              Plain Text Body
            </label>
            <textarea
              value={bodyText}
              onChange={(e) => setBodyText(e.target.value)}
              placeholder="Hello {{name}},&#10;&#10;Welcome to our platform!&#10;&#10;Best regards,&#10;The Team"
              rows={6}
              className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent font-mono text-sm resize-none"
            />
            <p className="text-xs text-text-muted mt-1">
              Fallback for email clients that don&apos;t support HTML
            </p>
          </div>
        </div>
      </Card>

      {/* Preview Modal */}
      {showPreview && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-overlay/50 backdrop-blur-sm"
            onClick={() => setShowPreview(false)}
          />
          <div className="relative w-full max-w-3xl max-h-[80vh] mx-4 bg-surface-elevated rounded-xl border border-border shadow-xl overflow-hidden">
            <div className="flex items-center justify-between p-4 border-b border-border">
              <h3 className="font-semibold text-text-primary">Email Preview</h3>
              <Button variant="ghost" size="sm" onClick={() => setShowPreview(false)}>
                Close
              </Button>
            </div>
            <div className="p-4 bg-white overflow-auto" style={{ maxHeight: "calc(80vh - 60px)" }}>
              {bodyHtml ? (
                <div dangerouslySetInnerHTML={{ __html: bodyHtml }} />
              ) : (
                <p className="text-text-muted text-center py-8">
                  No HTML content to preview
                </p>
              )}
            </div>
          </div>
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
    </form>
  );
}

function TemplateEditorSkeleton() {
  return (
    <div className="space-y-6 max-w-4xl animate-pulse">
      <div className="flex items-center justify-between">
        <div>
          <div className="h-4 w-48 bg-surface-overlay rounded mb-2" />
          <div className="h-8 w-64 bg-surface-overlay rounded" />
        </div>
        <div className="flex gap-3">
          <div className="h-10 w-20 bg-surface-overlay rounded" />
          <div className="h-10 w-32 bg-surface-overlay rounded" />
        </div>
      </div>

      <div className="card p-6">
        <div className="h-6 w-40 bg-surface-overlay rounded mb-6" />
        <div className="grid grid-cols-2 gap-6">
          <div className="col-span-2 h-10 bg-surface-overlay rounded" />
          <div className="col-span-2 h-10 bg-surface-overlay rounded" />
          <div className="h-10 bg-surface-overlay rounded" />
        </div>
      </div>

      <div className="card p-6">
        <div className="h-6 w-40 bg-surface-overlay rounded mb-6" />
        <div className="space-y-6">
          <div className="h-10 bg-surface-overlay rounded" />
          <div className="h-64 bg-surface-overlay rounded" />
          <div className="h-32 bg-surface-overlay rounded" />
        </div>
      </div>
    </div>
  );
}
