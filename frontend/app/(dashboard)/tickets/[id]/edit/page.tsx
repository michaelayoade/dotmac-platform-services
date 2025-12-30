"use client";

import { use, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  MessageSquare,
  User,
  AlertCircle,
  Tag,
  Folder,
  Loader2,
} from "lucide-react";
import { Button, Card, Input } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import { useTicket, useUpdateTicket } from "@/lib/hooks/api/use-ticketing";
import type { TicketCategory, TicketPriority, TicketStatus } from "@/lib/api/ticketing";

interface EditTicketPageProps {
  params: Promise<{ id: string }>;
}

const categories: Array<{ value: TicketCategory; label: string }> = [
  { value: "support", label: "General Support" },
  { value: "billing", label: "Billing & Payments" },
  { value: "technical", label: "Technical Support" },
  { value: "feature_request", label: "Feature Request" },
  { value: "bug", label: "Bug Report" },
  { value: "other", label: "Other" },
];

const priorities: Array<{ value: TicketPriority; label: string; description: string }> = [
  { value: "low", label: "Low", description: "General questions, minor issues" },
  { value: "normal", label: "Normal", description: "Standard issues affecting work" },
  { value: "high", label: "High", description: "Urgent issues needing quick resolution" },
  { value: "urgent", label: "Urgent", description: "Critical issues requiring immediate attention" },
];

const statuses: Array<{ value: TicketStatus; label: string }> = [
  { value: "open", label: "Open" },
  { value: "in_progress", label: "In Progress" },
  { value: "waiting", label: "Waiting" },
  { value: "resolved", label: "Resolved" },
  { value: "closed", label: "Closed" },
];

export default function EditTicketPage({ params }: EditTicketPageProps) {
  const { id } = use(params);
  const router = useRouter();
  const { toast } = useToast();

  const { data: ticket, isLoading } = useTicket(id);
  const updateTicket = useUpdateTicket();

  const [subject, setSubject] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState<TicketCategory>("support");
  const [priority, setPriority] = useState<TicketPriority>("normal");
  const [status, setStatus] = useState<TicketStatus>("open");
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState("");
  const [isDirty, setIsDirty] = useState(false);

  // Populate form when ticket loads
  useEffect(() => {
    if (ticket) {
      setSubject(ticket.subject || "");
      setDescription(ticket.description || "");
      setCategory(ticket.category || "support");
      setPriority(ticket.priority || "normal");
      setStatus(ticket.status || "open");
      setTags(ticket.tags || []);
    }
  }, [ticket]);

  const handleAddTag = () => {
    if (!tagInput.trim() || tags.includes(tagInput.trim())) return;
    setTags([...tags, tagInput.trim()]);
    setTagInput("");
    setIsDirty(true);
  };

  const handleRemoveTag = (tag: string) => {
    setTags(tags.filter((t) => t !== tag));
    setIsDirty(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!subject.trim()) {
      toast({ title: "Subject is required", variant: "error" });
      return;
    }

    try {
      await updateTicket.mutateAsync({
        id,
        data: {
          subject,
          description,
          category,
          priority,
          status,
          tags: tags.length > 0 ? tags : undefined,
        },
      });

      toast({
        title: "Ticket updated",
        description: "Changes have been saved successfully.",
      });

      router.push(`/tickets/${id}`);
    } catch {
      toast({
        title: "Failed to update ticket",
        description: "Please try again.",
        variant: "error",
      });
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="w-8 h-8 animate-spin text-accent" />
      </div>
    );
  }

  if (!ticket) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <h2 className="text-xl font-semibold text-text-primary mb-2">Ticket not found</h2>
        <p className="text-text-muted mb-6">
          The ticket you&apos;re looking for doesn&apos;t exist.
        </p>
        <Button onClick={() => router.push("/tickets")}>Back to Tickets</Button>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-8 animate-fade-up">
      <PageHeader
        title={`Edit Ticket #${id.slice(0, 8)}`}
        breadcrumbs={[
          { label: "Tickets", href: "/tickets" },
          { label: `#${id.slice(0, 8)}`, href: `/tickets/${id}` },
          { label: "Edit" },
        ]}
        actions={
          <Button variant="ghost" onClick={() => router.back()}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        }
      />

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Subject & Description */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
              <MessageSquare className="w-5 h-5 text-accent" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">Ticket Details</h3>
              <p className="text-sm text-text-muted">Update the ticket information</p>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Subject <span className="text-status-error">*</span>
              </label>
              <Input
                value={subject}
                onChange={(e) => { setSubject(e.target.value); setIsDirty(true); }}
                placeholder="Brief summary of the issue"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Description
              </label>
              <textarea
                value={description}
                onChange={(e) => { setDescription(e.target.value); setIsDirty(true); }}
                placeholder="Provide detailed information about the issue..."
                className="w-full p-3 bg-surface-primary border border-border-subtle rounded-lg text-sm resize-none min-h-[150px]"
              />
            </div>
          </div>
        </Card>

        {/* Status, Category & Priority */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-status-info/15 flex items-center justify-center">
              <Folder className="w-5 h-5 text-status-info" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">Classification</h3>
              <p className="text-sm text-text-muted">Update status, category and priority</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">Status</label>
              <select
                value={status}
                onChange={(e) => { setStatus(e.target.value as TicketStatus); setIsDirty(true); }}
                className="w-full px-3 py-2 bg-surface-primary border border-border-subtle rounded-md text-sm"
              >
                {statuses.map((s) => (
                  <option key={s.value} value={s.value}>
                    {s.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">Category</label>
              <select
                value={category}
                onChange={(e) => { setCategory(e.target.value as TicketCategory); setIsDirty(true); }}
                className="w-full px-3 py-2 bg-surface-primary border border-border-subtle rounded-md text-sm"
              >
                {categories.map((cat) => (
                  <option key={cat.value} value={cat.value}>
                    {cat.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">Priority</label>
              <select
                value={priority}
                onChange={(e) => { setPriority(e.target.value as TicketPriority); setIsDirty(true); }}
                className="w-full px-3 py-2 bg-surface-primary border border-border-subtle rounded-md text-sm"
              >
                {priorities.map((p) => (
                  <option key={p.value} value={p.value}>
                    {p.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="mt-4 p-4 bg-surface-overlay rounded-lg">
            <div className="flex items-start gap-3">
              <AlertCircle className={cn(
                "w-5 h-5 mt-0.5",
                priority === "urgent" ? "text-status-error" :
                priority === "high" ? "text-status-warning" :
                priority === "normal" ? "text-status-info" : "text-text-muted"
              )} />
              <div>
                <p className="text-sm font-medium text-text-primary">
                  {priorities.find(p => p.value === priority)?.label} Priority
                </p>
                <p className="text-sm text-text-muted">
                  {priorities.find(p => p.value === priority)?.description}
                </p>
              </div>
            </div>
          </div>
        </Card>

        {/* Tags */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-highlight-subtle flex items-center justify-center">
              <User className="w-5 h-5 text-highlight" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">Tags</h3>
              <p className="text-sm text-text-muted">Organize with custom labels</p>
            </div>
          </div>

          <div>
            <div className="flex items-center gap-2 mb-2">
              <Input
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                placeholder="Add a tag..."
                onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), handleAddTag())}
              />
              <Button type="button" variant="outline" onClick={handleAddTag}>
                Add
              </Button>
            </div>
            {tags.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {tags.map((tag) => (
                  <span
                    key={tag}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-sm bg-surface-overlay text-text-secondary"
                  >
                    <Tag className="w-3 h-3" />
                    {tag}
                    <button
                      type="button"
                      onClick={() => handleRemoveTag(tag)}
                      className="hover:text-status-error transition-colors"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>
        </Card>

        {/* Actions */}
        <div className="flex items-center justify-between pt-4">
          <p className="text-sm text-text-muted">
            {isDirty ? "You have unsaved changes" : "No changes made"}
          </p>
          <div className="flex items-center gap-3">
            <Button type="button" variant="ghost" onClick={() => router.back()}>
              Cancel
            </Button>
            <Button type="submit" disabled={!isDirty || updateTicket.isPending}>
              {updateTicket.isPending ? "Saving..." : "Save Changes"}
            </Button>
          </div>
        </div>
      </form>
    </div>
  );
}
