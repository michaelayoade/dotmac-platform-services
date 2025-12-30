"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
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
} from "lucide-react";
import { Button, Card, Input, Select } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import { useCreateWorkflow } from "@/lib/hooks/api/use-workflows";
import {
  createWorkflowSchema,
  triggerTypes,
  type CreateWorkflowData,
  type WorkflowTrigger,
} from "@/lib/schemas/workflows";

type TriggerType = "manual" | "scheduled" | "webhook" | "event";

const triggerIcons: Record<TriggerType, React.ReactNode> = {
  manual: <Play className="w-4 h-4" />,
  scheduled: <Clock className="w-4 h-4" />,
  webhook: <Webhook className="w-4 h-4" />,
  event: <Bell className="w-4 h-4" />,
};

export default function NewWorkflowPage() {
  const router = useRouter();
  const { toast } = useToast();
  const createWorkflow = useCreateWorkflow();

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<CreateWorkflowData>({
    resolver: zodResolver(createWorkflowSchema),
    defaultValues: {
      name: "",
      description: "",
      triggers: [{ type: "manual" }],
      steps: [],
      tags: [],
      isActive: false,
    },
  });

  const triggers = watch("triggers") || [];
  const tags = watch("tags") || [];
  const [tagInput, setTagInput] = useState("");

  const handleAddTrigger = (type: TriggerType) => {
    if (triggers.some((t) => t.type === type)) {
      toast({ title: "Trigger already added", variant: "error" });
      return;
    }
    setValue("triggers", [...triggers, { type }]);
  };

  const handleRemoveTrigger = (index: number) => {
    if (triggers.length <= 1) {
      toast({ title: "At least one trigger is required", variant: "error" });
      return;
    }
    setValue("triggers", triggers.filter((_, i) => i !== index));
  };

  const handleAddTag = () => {
    if (!tagInput.trim() || tags.includes(tagInput.trim())) return;
    setValue("tags", [...tags, tagInput.trim()]);
    setTagInput("");
  };

  const handleRemoveTag = (tag: string) => {
    setValue("tags", tags.filter((t) => t !== tag));
  };

  const onSubmit = async (data: CreateWorkflowData) => {
    try {
      const result = await createWorkflow.mutateAsync({
        name: data.name,
        description: data.description || undefined,
        triggers: data.triggers,
        steps: [],
        tags: data.tags && data.tags.length > 0 ? data.tags : undefined,
        isActive: data.isActive,
      });

      toast({
        title: "Workflow created",
        description: `${data.name} has been created successfully.`,
      });

      router.push(`/workflows/${result.id}`);
    } catch {
      toast({
        title: "Failed to create workflow",
        description: "Please try again.",
        variant: "error",
      });
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8 animate-fade-up">
      <PageHeader
        title="New Workflow"
        breadcrumbs={[
          { label: "Workflows", href: "/workflows" },
          { label: "New Workflow" },
        ]}
        actions={
          <Button variant="ghost" onClick={() => router.back()}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        }
      />

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Basic Information */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
              <Workflow className="w-5 h-5 text-accent" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">Workflow Details</h3>
              <p className="text-sm text-text-muted">Basic workflow information</p>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Name <span className="text-status-error">*</span>
              </label>
              <Input
                {...register("name")}
                placeholder="My Workflow"
                aria-invalid={!!errors.name}
              />
              {errors.name && (
                <p className="text-xs text-status-error mt-1">{errors.name.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Description
              </label>
              <textarea
                {...register("description")}
                placeholder="Describe what this workflow does..."
                className="w-full p-3 bg-surface-primary border border-border-subtle rounded-lg text-sm resize-none min-h-[100px]"
              />
            </div>

            <div>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  {...register("isActive")}
                  className="rounded"
                />
                <span className="text-sm font-medium text-text-primary">
                  Activate workflow immediately
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

            {errors.triggers && (
              <p className="text-xs text-status-error mt-2">{errors.triggers.message}</p>
            )}
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
        <div className="flex items-center justify-end gap-3 pt-4">
          <Button type="button" variant="ghost" onClick={() => router.back()}>
            Cancel
          </Button>
          <Button type="submit" disabled={createWorkflow.isPending}>
            {createWorkflow.isPending ? "Creating..." : "Create Workflow"}
          </Button>
        </div>
      </form>
    </div>
  );
}
