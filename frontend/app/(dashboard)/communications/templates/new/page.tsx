"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Save, Eye, Loader2 } from "lucide-react";
import { Button, Card, Input } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { PageHeader } from "@/components/shared/page-header";
import { useCreateEmailTemplate, usePreviewEmailTemplate } from "@/lib/hooks/api/use-communications";

export default function NewTemplatePage() {
  const router = useRouter();
  const { toast } = useToast();
  const createTemplate = useCreateEmailTemplate();
  const previewTemplate = usePreviewEmailTemplate();

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [channel, setChannel] = useState("email");
  const [subject, setSubject] = useState("");
  const [bodyHtml, setBodyHtml] = useState("");
  const [bodyText, setBodyText] = useState("");
  const [isActive, setIsActive] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [previewHtml, setPreviewHtml] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!name.trim()) {
      toast({ title: "Name is required", variant: "error" });
      return;
    }

    try {
      const template = await createTemplate.mutateAsync({
        name: name.trim(),
        description: description.trim() || undefined,
        channel,
        subject: subject.trim() || undefined,
        subjectTemplate: subject.trim() || undefined,
        bodyHtml: bodyHtml.trim() || undefined,
        bodyText: bodyText.trim() || undefined,
        isActive,
      });

      toast({ title: "Template created successfully" });
      router.push(`/communications/templates/${template.id}/edit`);
    } catch {
      toast({ title: "Failed to create template", variant: "error" });
    }
  };

  const handlePreview = () => {
    setPreviewHtml(bodyHtml);
    setShowPreview(true);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-4xl animate-fade-up">
      <PageHeader
        title="Create Email Template"
        breadcrumbs={[
          { label: "Communications", href: "/communications" },
          { label: "New Template" },
        ]}
        actions={
          <div className="flex items-center gap-3">
            <Button type="button" variant="ghost" onClick={() => router.back()}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
            <Button
              type="submit"
              disabled={createTemplate.isPending}
              className="shadow-glow-sm hover:shadow-glow"
            >
              {createTemplate.isPending ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Save className="w-4 h-4 mr-2" />
              )}
              Save Template
            </Button>
          </div>
        }
      />

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
          <Button type="button" variant="outline" onClick={handlePreview}>
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
              {previewHtml ? (
                <div dangerouslySetInnerHTML={{ __html: previewHtml }} />
              ) : (
                <p className="text-text-muted text-center py-8">
                  No HTML content to preview
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </form>
  );
}
