"use client";

import { use, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  Workflow,
  Zap,
  Tag,
  Plus,
  X,
  Play,
  Clock,
  Webhook,
  Bell,
  Loader2,
} from "lucide-react";
import { Button, Card, Input } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { PageHeader } from "@/components/shared/page-header";
import { useWorkflow, useUpdateWorkflow } from "@/lib/hooks/api/use-workflows";
import { triggerTypes } from "@/lib/schemas/workflows";

type TriggerType = "manual" | "scheduled" | "webhook" | "event";

interface Trigger {
  type: TriggerType;
  config?: Record<string, unknown>;
}

interface EditWorkflowPageProps {
  params: Promise<{ id: string }>;
}

const triggerIcons: Record<TriggerType, React.ReactNode> = {
  manual: <Play className="w-4 h-4" />,
  scheduled: <Clock className="w-4 h-4" />,
  webhook: <Webhook className="w-4 h-4" />,
  event: <Bell className="w-4 h-4" />,
};

export default function EditWorkflowPage({ params }: EditWorkflowPageProps) {
  const { id } = use(params);
  const router = useRouter();
  const { toast } = useToast();

  const { data: workflow, isLoading } = useWorkflow(id);
  const updateWorkflow = useUpdateWorkflow();

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [triggers, setTriggers] = useState<Trigger[]>([{ type: "manual" }]);
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState("");
  const [isActive, setIsActive] = useState(false);
  const [isDirty, setIsDirty] = useState(false);

  // Populate form when workflow loads
  useEffect(() => {
    if (workflow) {
      setName(workflow.name || "");
      setDescription(workflow.description || "");
      setTriggers(
        (workflow.triggers as Trigger[]) || [{ type: "manual" }]
      );
      setTags(workflow.tags || []);
      setIsActive(workflow.isActive || false);
    }
  }, [workflow]);

  const handleAddTrigger = (type: TriggerType) => {
    if (triggers.some((t) => t.type === type)) {
      toast({ title: "Trigger already added", variant: "error" });
      return;
    }
    setTriggers([...triggers, { type }]);
    setIsDirty(true);
  };

  const handleRemoveTrigger = (index: number) => {
    if (triggers.length <= 1) {
      toast({ title: "At least one trigger is required", variant: "error" });
      return;
    }
    setTriggers(triggers.filter((_, i) => i !== index));
    setIsDirty(true);
  };

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

    if (!name.trim()) {
      toast({ title: "Name is required", variant: "error" });
      return;
    }

    if (triggers.length === 0) {
      toast({ title: "At least one trigger is required", variant: "error" });
      return;
    }

    try {
      await updateWorkflow.mutateAsync({
        id,
        data: {
          name,
          description: description || undefined,
          triggers,
          tags: tags.length > 0 ? tags : undefined,
          isActive,
        },
      });

      toast({
        title: "Workflow updated",
        description: "Changes have been saved successfully.",
      });

      router.push(`/workflows/${id}`);
    } catch {
      toast({
        title: "Failed to update workflow",
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

  if (!workflow) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <h2 className="text-xl font-semibold text-text-primary mb-2">Workflow not found</h2>
        <p className="text-text-muted mb-6">
          The workflow you&apos;re looking for doesn&apos;t exist.
        </p>
        <Button onClick={() => router.push("/workflows")}>Back to Workflows</Button>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-8 animate-fade-up">
      <PageHeader
        title={`Edit ${workflow.name}`}
        breadcrumbs={[
          { label: "Workflows", href: "/workflows" },
          { label: workflow.name, href: `/workflows/${id}` },
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
        {/* Basic Information */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
              <Workflow className="w-5 h-5 text-accent" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">Workflow Details</h3>
              <p className="text-sm text-text-muted">Update workflow information</p>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Name <span className="text-status-error">*</span>
              </label>
              <Input
                value={name}
                onChange={(e) => { setName(e.target.value); setIsDirty(true); }}
                placeholder="My Workflow"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Description
              </label>
              <textarea
                value={description}
                onChange={(e) => { setDescription(e.target.value); setIsDirty(true); }}
                placeholder="Describe what this workflow does..."
                className="w-full p-3 bg-surface-primary border border-border-subtle rounded-lg text-sm resize-none min-h-[100px]"
              />
            </div>

            <div>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={isActive}
                  onChange={(e) => { setIsActive(e.target.checked); setIsDirty(true); }}
                  className="rounded"
                />
                <span className="text-sm font-medium text-text-primary">
                  Workflow is active
                </span>
              </label>
              <p className="text-xs text-text-muted mt-1 ml-6">
                Active workflows will run when their triggers fire
              </p>
            </div>
          </div>
        </Card>

        {/* Triggers */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-highlight-subtle flex items-center justify-center">
              <Zap className="w-5 h-5 text-highlight" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">Triggers</h3>
              <p className="text-sm text-text-muted">What starts this workflow</p>
            </div>
          </div>

          <div className="space-y-4">
            {/* Current triggers */}
            <div className="space-y-2">
              {triggers.map((trigger, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 bg-surface-overlay rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-accent-subtle flex items-center justify-center">
                      {triggerIcons[trigger.type]}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-text-primary">
                        {triggerTypes.find((t) => t.value === trigger.type)?.label}
                      </p>
                      <p className="text-xs text-text-muted">
                        {trigger.type === "manual" && "Triggered manually by a user"}
                        {trigger.type === "scheduled" && "Runs on a schedule"}
                        {trigger.type === "webhook" && "Triggered by external webhook"}
                        {trigger.type === "event" && "Triggered by system events"}
                      </p>
                    </div>
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => handleRemoveTrigger(index)}
                    disabled={triggers.length <= 1}
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              ))}
            </div>

            {/* Add trigger */}
            <div className="flex flex-wrap gap-2">
              {triggerTypes.map((trigger) => (
                <Button
                  key={trigger.value}
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => handleAddTrigger(trigger.value as TriggerType)}
                  disabled={triggers.some((t) => t.type === trigger.value)}
                >
                  <Plus className="w-3 h-3 mr-1" />
                  {trigger.label}
                </Button>
              ))}
            </div>
          </div>
        </Card>

        {/* Tags */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-status-success/15 flex items-center justify-center">
              <Tag className="w-5 h-5 text-status-success" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">Tags</h3>
              <p className="text-sm text-text-muted">Organize with custom labels</p>
            </div>
          </div>

          <div className="flex items-center gap-2 mb-4">
            <Input
              value={tagInput}
              onChange={(e) => setTagInput(e.target.value)}
              placeholder="Add a tag..."
              onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), handleAddTag())}
            />
            <Button type="button" variant="outline" onClick={handleAddTag}>
              <Plus className="w-4 h-4" />
            </Button>
          </div>

          <div className="flex flex-wrap gap-2">
            {tags.length > 0 ? (
              tags.map((tag) => (
                <span
                  key={tag}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm bg-surface-overlay text-text-secondary"
                >
                  {tag}
                  <button
                    type="button"
                    onClick={() => handleRemoveTag(tag)}
                    className="hover:text-status-error transition-colors"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))
            ) : (
              <p className="text-sm text-text-muted">No tags added yet</p>
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
            <Button type="submit" disabled={!isDirty || updateWorkflow.isPending}>
              {updateWorkflow.isPending ? "Saving..." : "Save Changes"}
            </Button>
          </div>
        </div>
      </form>
    </div>
  );
}
