"use client";

import { use, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Plus,
  Trash2,
  Mail,
  MessageSquare,
  Bell,
  Webhook,
  AlertTriangle,
  GripVertical,
  Save,
  Play,
  Pause,
  Loader2,
  Copy,
} from "lucide-react";
import { Button, Card, Input, Select } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import {
  useDunningCampaign,
  useUpdateDunningCampaign,
  useActivateDunningCampaign,
  usePauseDunningCampaign,
  useCloneDunningCampaign,
  type DunningStepAction,
  type UpdateDunningCampaignData,
} from "@/lib/hooks/api/use-billing";

const actionConfig: Record<
  DunningStepAction,
  { icon: typeof Mail; label: string; description: string }
> = {
  email: { icon: Mail, label: "Email", description: "Send an email reminder" },
  sms: { icon: MessageSquare, label: "SMS", description: "Send an SMS message" },
  in_app: { icon: Bell, label: "In-App", description: "Send in-app notification" },
  webhook: { icon: Webhook, label: "Webhook", description: "Trigger a webhook" },
  suspend_service: {
    icon: AlertTriangle,
    label: "Suspend Service",
    description: "Suspend customer's service",
  },
};

interface StepFormData {
  id: string;
  delayDays: number;
  action: DunningStepAction;
  subject?: string;
  message?: string;
  webhookUrl?: string;
}

interface CampaignDetailPageProps {
  params: Promise<{ id: string }>;
}

export default function CampaignDetailPage({ params }: CampaignDetailPageProps) {
  const { id } = use(params);
  const router = useRouter();
  const { toast } = useToast();

  const { data: campaign, isLoading } = useDunningCampaign(id);
  const updateCampaign = useUpdateDunningCampaign();
  const activateCampaign = useActivateDunningCampaign();
  const pauseCampaign = usePauseDunningCampaign();
  const cloneCampaign = useCloneDunningCampaign();

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [triggerDaysAfterDue, setTriggerDaysAfterDue] = useState(1);
  const [steps, setSteps] = useState<StepFormData[]>([]);
  const [autoSuspendAfterDays, setAutoSuspendAfterDays] = useState<number | undefined>();
  const [autoWriteOffAfterDays, setAutoWriteOffAfterDays] = useState<number | undefined>();
  const [excludeVipCustomers, setExcludeVipCustomers] = useState(false);
  const [excludeAmountBelow, setExcludeAmountBelow] = useState<number | undefined>();

  // Load campaign data
  useEffect(() => {
    if (campaign) {
      setName(campaign.name);
      setDescription(campaign.description || "");
      setTriggerDaysAfterDue(campaign.triggerDaysAfterDue);
      setSteps(
        campaign.steps.map((s) => ({
          id: s.id,
          delayDays: s.delayDays,
          action: s.action,
          subject: s.subject,
          message: s.message,
          webhookUrl: s.webhookUrl,
        }))
      );
      setAutoSuspendAfterDays(campaign.autoSuspendAfterDays);
      setAutoWriteOffAfterDays(campaign.autoWriteOffAfterDays);
      setExcludeVipCustomers(campaign.excludeVipCustomers);
      setExcludeAmountBelow(campaign.excludeAmountBelow ? campaign.excludeAmountBelow / 100 : undefined);
    }
  }, [campaign]);

  const addStep = () => {
    const lastStep = steps[steps.length - 1];
    const newStep: StepFormData = {
      id: Date.now().toString(),
      delayDays: (lastStep?.delayDays ?? 0) + 3,
      action: "email",
      subject: "",
      message: "",
    };
    setSteps([...steps, newStep]);
  };

  const removeStep = (id: string) => {
    if (steps.length <= 1) return;
    setSteps(steps.filter((s) => s.id !== id));
  };

  const updateStep = (id: string, updates: Partial<StepFormData>) => {
    setSteps(steps.map((s) => (s.id === id ? { ...s, ...updates } : s)));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!name.trim()) {
      toast({
        title: "Validation Error",
        description: "Campaign name is required.",
        variant: "error",
      });
      return;
    }

    const data: UpdateDunningCampaignData = {
      name: name.trim(),
      description: description.trim() || undefined,
      triggerDaysAfterDue,
      steps: steps.map((step, index) => ({
        order: index + 1,
        delayDays: step.delayDays,
        action: step.action,
        subject: step.subject || undefined,
        message: step.message || undefined,
        webhookUrl: step.webhookUrl || undefined,
      })),
      autoSuspendAfterDays,
      autoWriteOffAfterDays,
      excludeVipCustomers,
      excludeAmountBelow: excludeAmountBelow ? excludeAmountBelow * 100 : undefined,
    };

    try {
      await updateCampaign.mutateAsync({ id, data });
      toast({
        title: "Campaign updated",
        description: "Your changes have been saved.",
      });
    } catch {
      toast({
        title: "Error",
        description: "Failed to update campaign. Please try again.",
        variant: "error",
      });
    }
  };

  const handleActivate = async () => {
    try {
      await activateCampaign.mutateAsync(id);
      toast({
        title: "Campaign activated",
        description: "The campaign is now running.",
      });
    } catch {
      toast({
        title: "Error",
        description: "Failed to activate campaign.",
        variant: "error",
      });
    }
  };

  const handlePause = async () => {
    try {
      await pauseCampaign.mutateAsync(id);
      toast({
        title: "Campaign paused",
        description: "The campaign has been paused.",
      });
    } catch {
      toast({
        title: "Error",
        description: "Failed to pause campaign.",
        variant: "error",
      });
    }
  };

  const handleClone = async () => {
    try {
      const cloned = await cloneCampaign.mutateAsync(id);
      toast({
        title: "Campaign cloned",
        description: "A copy of the campaign has been created.",
      });
      router.push(`/billing/dunning/campaigns/${cloned.id}`);
    } catch {
      toast({
        title: "Error",
        description: "Failed to clone campaign.",
        variant: "error",
      });
    }
  };

  if (isLoading) {
    return <CampaignDetailSkeleton />;
  }

  if (!campaign) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <AlertTriangle className="w-12 h-12 text-text-muted mb-4" />
        <h2 className="text-xl font-semibold text-text-primary mb-2">Campaign not found</h2>
        <Button onClick={() => router.push("/billing/dunning/campaigns")}>Back to Campaigns</Button>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-8 animate-fade-up">
      {/* Page Header */}
      <PageHeader
        title={campaign.name}
        breadcrumbs={[
          { label: "Billing", href: "/billing" },
          { label: "Dunning", href: "/billing/dunning" },
          { label: "Campaigns", href: "/billing/dunning/campaigns" },
          { label: campaign.name },
        ]}
        actions={
          <div className="flex items-center gap-3">
            <Button
              type="button"
              variant="outline"
              onClick={handleClone}
              disabled={cloneCampaign.isPending}
            >
              {cloneCampaign.isPending ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Copy className="w-4 h-4 mr-2" />
              )}
              Clone
            </Button>
            {campaign.status === "active" ? (
              <Button
                type="button"
                variant="outline"
                onClick={handlePause}
                disabled={pauseCampaign.isPending}
              >
                {pauseCampaign.isPending ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Pause className="w-4 h-4 mr-2" />
                )}
                Pause
              </Button>
            ) : campaign.status !== "archived" ? (
              <Button
                type="button"
                variant="outline"
                onClick={handleActivate}
                disabled={activateCampaign.isPending}
              >
                {activateCampaign.isPending ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Play className="w-4 h-4 mr-2" />
                )}
                Activate
              </Button>
            ) : null}
            <Button variant="ghost" type="button" onClick={() => router.back()}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
          </div>
        }
      />

      {/* Status Banner */}
      {campaign.status === "active" && (
        <div className="bg-status-success/15 border border-status-success/20 rounded-lg p-4 flex items-center gap-3">
          <div className="w-2 h-2 rounded-full bg-status-success animate-pulse" />
          <span className="text-status-success font-medium">Campaign is active and running</span>
          {campaign.stats && (
            <span className="text-text-muted ml-auto">
              {campaign.stats.activeExecutions} active executions | $
              {(campaign.stats.recoveredAmount / 100).toLocaleString()} recovered
            </span>
          )}
        </div>
      )}

      {/* Basic Info */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-text-primary mb-6">Campaign Details</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-text-primary mb-1.5">
              Campaign Name <span className="text-status-error">*</span>
            </label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Standard Payment Recovery"
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
              placeholder="Brief description of this campaign"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-text-primary mb-1.5">
              Trigger After (Days Overdue) <span className="text-status-error">*</span>
            </label>
            <Input
              type="number"
              min={1}
              value={triggerDaysAfterDue}
              onChange={(e) => setTriggerDaysAfterDue(parseInt(e.target.value) || 1)}
              required
            />
            <p className="text-xs text-text-muted mt-1">
              Campaign starts when invoice is this many days past due
            </p>
          </div>
        </div>
      </Card>

      {/* Steps */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-lg font-semibold text-text-primary">Campaign Steps</h3>
            <p className="text-sm text-text-muted">Define the sequence of actions</p>
          </div>
          <Button type="button" variant="outline" onClick={addStep}>
            <Plus className="w-4 h-4 mr-2" />
            Add Step
          </Button>
        </div>

        <div className="space-y-4">
          {steps.map((step, index) => (
            <StepEditor
              key={step.id}
              step={step}
              index={index}
              onUpdate={(updates) => updateStep(step.id, updates)}
              onRemove={() => removeStep(step.id)}
              canRemove={steps.length > 1}
            />
          ))}
        </div>
      </Card>

      {/* Advanced Settings */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-text-primary mb-6">Advanced Settings</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-text-primary mb-1.5">
              Auto-Suspend After (Days)
            </label>
            <Input
              type="number"
              min={1}
              value={autoSuspendAfterDays || ""}
              onChange={(e) =>
                setAutoSuspendAfterDays(e.target.value ? parseInt(e.target.value) : undefined)
              }
              placeholder="Leave empty to disable"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-text-primary mb-1.5">
              Auto Write-Off After (Days)
            </label>
            <Input
              type="number"
              min={1}
              value={autoWriteOffAfterDays || ""}
              onChange={(e) =>
                setAutoWriteOffAfterDays(e.target.value ? parseInt(e.target.value) : undefined)
              }
              placeholder="Leave empty to disable"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-text-primary mb-1.5">
              Exclude Amounts Below
            </label>
            <Input
              type="number"
              min={0}
              step={0.01}
              value={excludeAmountBelow || ""}
              onChange={(e) =>
                setExcludeAmountBelow(e.target.value ? parseFloat(e.target.value) : undefined)
              }
              placeholder="0.00"
            />
          </div>
          <div className="flex items-center">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={excludeVipCustomers}
                onChange={(e) => setExcludeVipCustomers(e.target.checked)}
                className="w-4 h-4 rounded border-border"
              />
              <div>
                <span className="text-sm font-medium text-text-primary">Exclude VIP Customers</span>
                <p className="text-xs text-text-muted">Skip customers marked as VIP</p>
              </div>
            </label>
          </div>
        </div>
      </Card>

      {/* Actions */}
      <Card className="p-6">
        <div className="flex items-center justify-end gap-3">
          <Button type="button" variant="ghost" onClick={() => router.back()}>
            Cancel
          </Button>
          <Button
            type="submit"
            disabled={updateCampaign.isPending}
            className="shadow-glow-sm hover:shadow-glow"
          >
            {updateCampaign.isPending ? (
              "Saving..."
            ) : (
              <>
                <Save className="w-4 h-4 mr-2" />
                Save Changes
              </>
            )}
          </Button>
        </div>
      </Card>
    </form>
  );
}

function StepEditor({
  step,
  index,
  onUpdate,
  onRemove,
  canRemove,
}: {
  step: StepFormData;
  index: number;
  onUpdate: (updates: Partial<StepFormData>) => void;
  onRemove: () => void;
  canRemove: boolean;
}) {
  return (
    <div className="p-4 bg-surface-overlay rounded-lg border border-border">
      <div className="flex items-start gap-4">
        <div className="flex items-center gap-2 pt-2">
          <GripVertical className="w-4 h-4 text-text-muted cursor-move" />
          <div className="w-8 h-8 rounded-full bg-accent-subtle flex items-center justify-center">
            <span className="text-sm font-semibold text-accent">{index + 1}</span>
          </div>
        </div>

        <div className="flex-1 grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs text-text-muted mb-1">Delay (Days)</label>
            <Input
              type="number"
              min={0}
              value={step.delayDays}
              onChange={(e) => onUpdate({ delayDays: parseInt(e.target.value) || 0 })}
            />
          </div>
          <div>
            <label className="block text-xs text-text-muted mb-1">Action</label>
            <Select
              value={step.action}
              onChange={(e) => onUpdate({ action: e.target.value as DunningStepAction })}
            >
              {Object.entries(actionConfig).map(([key, config]) => (
                <option key={key} value={key}>
                  {config.label}
                </option>
              ))}
            </Select>
          </div>

          {(step.action === "email" || step.action === "sms" || step.action === "in_app") && (
            <div className="md:col-span-2">
              <label className="block text-xs text-text-muted mb-1">
                {step.action === "email" ? "Subject" : "Title"}
              </label>
              <Input
                value={step.subject || ""}
                onChange={(e) => onUpdate({ subject: e.target.value })}
                placeholder={step.action === "email" ? "Email subject" : "Notification title"}
              />
            </div>
          )}

          {step.action === "webhook" && (
            <div className="md:col-span-2">
              <label className="block text-xs text-text-muted mb-1">Webhook URL</label>
              <Input
                type="url"
                value={step.webhookUrl || ""}
                onChange={(e) => onUpdate({ webhookUrl: e.target.value })}
                placeholder="https://..."
              />
            </div>
          )}
        </div>

        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={onRemove}
          disabled={!canRemove}
          className="text-status-error hover:text-status-error"
        >
          <Trash2 className="w-4 h-4" />
        </Button>
      </div>

      {(step.action === "email" || step.action === "sms" || step.action === "in_app") && (
        <div className="mt-4 ml-14">
          <label className="block text-xs text-text-muted mb-1">Message</label>
          <textarea
            value={step.message || ""}
            onChange={(e) => onUpdate({ message: e.target.value })}
            placeholder="Enter your message..."
            rows={3}
            className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent resize-none"
          />
        </div>
      )}
    </div>
  );
}

function CampaignDetailSkeleton() {
  return (
    <div className="space-y-8 animate-pulse">
      <div className="flex items-center justify-between">
        <div>
          <div className="h-4 w-48 bg-surface-overlay rounded mb-2" />
          <div className="h-8 w-64 bg-surface-overlay rounded" />
        </div>
        <div className="flex gap-3">
          <div className="h-10 w-24 bg-surface-overlay rounded" />
          <div className="h-10 w-24 bg-surface-overlay rounded" />
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
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-24 bg-surface-overlay rounded-lg" />
          ))}
        </div>
      </div>
    </div>
  );
}
