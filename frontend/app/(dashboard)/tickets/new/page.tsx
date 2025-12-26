"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  ArrowLeft,
  MessageSquare,
  User,
  AlertCircle,
  Tag,
  Folder,
} from "lucide-react";
import { Button, Card, Input } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import { useCreateTicket } from "@/lib/hooks/api/use-ticketing";
import {
  createTicketSchema,
  ticketCategories,
  ticketPriorities,
  type CreateTicketData,
} from "@/lib/schemas/tickets";
import type { TicketCategory, TicketPriority } from "@/lib/api/ticketing";

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

export default function NewTicketPage() {
  const router = useRouter();
  const { toast } = useToast();
  const createTicket = useCreateTicket();

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<CreateTicketData>({
    resolver: zodResolver(createTicketSchema),
    defaultValues: {
      subject: "",
      description: "",
      category: "support",
      priority: "normal",
      customerId: "",
      tags: [],
    },
  });

  const tags = watch("tags") || [];
  const priority = watch("priority");
  const [tagInput, setTagInput] = useState("");

  const handleAddTag = () => {
    if (!tagInput.trim() || tags.includes(tagInput.trim())) return;
    setValue("tags", [...tags, tagInput.trim()]);
    setTagInput("");
  };

  const handleRemoveTag = (tag: string) => {
    setValue("tags", tags.filter((t) => t !== tag));
  };

  const onSubmit = async (data: CreateTicketData) => {
    try {
      const result = await createTicket.mutateAsync({
        subject: data.subject,
        description: data.description,
        category: data.category,
        priority: data.priority,
        customerId: data.customerId || undefined,
        tags: data.tags && data.tags.length > 0 ? data.tags : undefined,
      });

      toast({
        title: "Ticket created",
        description: `Ticket #${result.id.slice(0, 8)} has been created.`,
      });

      router.push(`/tickets/${result.id}`);
    } catch {
      toast({
        title: "Failed to create ticket",
        description: "Please try again.",
        variant: "error",
      });
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8 animate-fade-up">
      <PageHeader
        title="New Ticket"
        breadcrumbs={[
          { label: "Tickets", href: "/tickets" },
          { label: "New Ticket" },
        ]}
        actions={
          <Button variant="ghost" onClick={() => router.back()}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        }
      />

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Subject */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
              <MessageSquare className="w-5 h-5 text-accent" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">Ticket Details</h3>
              <p className="text-sm text-text-muted">Describe the issue or request</p>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Subject <span className="text-status-error">*</span>
              </label>
              <Input
                {...register("subject")}
                placeholder="Brief summary of the issue"
                aria-invalid={!!errors.subject}
              />
              {errors.subject && (
                <p className="text-xs text-status-error mt-1">{errors.subject.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Description <span className="text-status-error">*</span>
              </label>
              <textarea
                {...register("description")}
                placeholder="Provide detailed information about the issue..."
                className={cn(
                  "w-full p-3 bg-surface-primary border border-border-subtle rounded-lg text-sm resize-none min-h-[150px]",
                  errors.description && "border-status-error"
                )}
                aria-invalid={!!errors.description}
              />
              {errors.description && (
                <p className="text-xs text-status-error mt-1">{errors.description.message}</p>
              )}
            </div>
          </div>
        </Card>

        {/* Category & Priority */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-status-info/15 flex items-center justify-center">
              <Folder className="w-5 h-5 text-status-info" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">Classification</h3>
              <p className="text-sm text-text-muted">Categorize and prioritize the ticket</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">Category</label>
              <select
                {...register("category")}
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
                {...register("priority")}
                className="w-full px-3 py-2 bg-surface-primary border border-border-subtle rounded-md text-sm"
              >
                {priorities.map((p) => (
                  <option key={p.value} value={p.value}>
                    {p.label} - {p.description}
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

        {/* Tenant & Tags */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-highlight-subtle flex items-center justify-center">
              <User className="w-5 h-5 text-highlight" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">Additional Info</h3>
              <p className="text-sm text-text-muted">Optional tenant and tag information</p>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Tenant ID
              </label>
              <Input
                {...register("customerId")}
                placeholder="Enter tenant ID (optional)"
              />
              {errors.customerId && (
                <p className="text-xs text-status-error mt-1">{errors.customerId.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">Tags</label>
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
          </div>
        </Card>

        {/* Actions */}
        <div className="flex items-center justify-end gap-3 pt-4">
          <Button type="button" variant="ghost" onClick={() => router.back()}>
            Cancel
          </Button>
          <Button type="submit" disabled={createTicket.isPending}>
            {createTicket.isPending ? "Creating..." : "Create Ticket"}
          </Button>
        </div>
      </form>
    </div>
  );
}
