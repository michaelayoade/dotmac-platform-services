"use client";

import { use, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Building2,
  Users,
  CreditCard,
  Calendar,
  Trash2,
  RefreshCcw,
  FileText,
  Ban,
  CheckCircle,
  Edit3,
  Check,
  X,
  Loader2,
  Globe,
  HardDrive,
  Activity,
  Settings,
} from "lucide-react";
import { format } from "date-fns";
import { Button, Card, Input, Select } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn, getPlanName } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import { ConfirmDialog, useConfirmDialog } from "@/components/shared/confirm-dialog";
import {
  useTenant,
  useUpdateTenant,
  useDeleteTenant,
  useSuspendTenant,
  useActivateTenant,
  useTenantStats,
} from "@/lib/hooks/api/use-tenants";
import { useTenantMembers } from "@/lib/hooks/api/use-tenant-portal";
import { tenantPlans, tenantStatuses } from "@/lib/schemas/tenants";

interface TenantDetailPageProps {
  params: Promise<{ id: string }>;
}

const statusColors: Record<string, { bg: string; text: string; dot: string }> = {
  active: { bg: "bg-status-success/15", text: "text-status-success", dot: "bg-status-success" },
  trial: { bg: "bg-status-info/15", text: "text-status-info", dot: "bg-status-info" },
  suspended: { bg: "bg-status-error/15", text: "text-status-error", dot: "bg-status-error" },
  inactive: { bg: "bg-surface-overlay", text: "text-text-muted", dot: "bg-text-muted" },
};

const planColors: Record<string, { bg: string; text: string }> = {
  Enterprise: { bg: "bg-accent-subtle", text: "text-accent" },
  Professional: { bg: "bg-highlight-subtle", text: "text-highlight" },
  Starter: { bg: "bg-status-info/15", text: "text-status-info" },
  Free: { bg: "bg-surface-overlay", text: "text-text-secondary" },
};

export default function TenantDetailPage({ params }: TenantDetailPageProps) {
  const { id } = use(params);
  const router = useRouter();
  const { toast } = useToast();
  const { confirm, dialog } = useConfirmDialog();

  const [isEditing, setIsEditing] = useState(false);
  const [editName, setEditName] = useState("");
  const [editPlan, setEditPlan] = useState<string>("");

  // Data fetching
  const { data: tenant, isLoading, error, refetch } = useTenant(id);
  const { data: stats } = useTenantStats(id);
  // Note: useTenantMembers is for tenant portal context, not admin view
  // TODO: Create admin-specific hook to fetch members for any tenant
  const { data: members } = useTenantMembers();

  // Mutations
  const updateTenant = useUpdateTenant();
  const deleteTenant = useDeleteTenant();
  const suspendTenant = useSuspendTenant();
  const activateTenant = useActivateTenant();

  const handleDelete = async () => {
    const confirmed = await confirm({
      title: "Delete Tenant",
      description: `Are you sure you want to delete "${tenant?.name}"? This will permanently delete all data associated with this tenant. This action cannot be undone.`,
      variant: "danger",
    });

    if (confirmed) {
      try {
        await deleteTenant.mutateAsync(id);
        toast({
          title: "Tenant deleted",
          description: "The tenant has been permanently deleted.",
        });
        router.push("/tenants");
      } catch {
        toast({
          title: "Error",
          description: "Failed to delete tenant. Please try again.",
          variant: "error",
        });
      }
    }
  };

  const handleSuspend = async () => {
    const confirmed = await confirm({
      title: "Suspend Tenant",
      description: `Are you sure you want to suspend "${tenant?.name}"? All users will lose access immediately.`,
      variant: "danger",
    });

    if (confirmed) {
      try {
        await suspendTenant.mutateAsync(id);
        toast({ title: "Tenant suspended" });
      } catch {
        toast({ title: "Failed to suspend tenant", variant: "error" });
      }
    }
  };

  const handleActivate = async () => {
    try {
      await activateTenant.mutateAsync(id);
      toast({ title: "Tenant activated" });
    } catch {
      toast({ title: "Failed to activate tenant", variant: "error" });
    }
  };

  const startEditing = () => {
    if (tenant) {
      setEditName(tenant.name);
      setEditPlan(getPlanName(tenant.plan));
      setIsEditing(true);
    }
  };

  const cancelEditing = () => {
    setIsEditing(false);
    setEditName("");
    setEditPlan("");
  };

  const saveChanges = async () => {
    try {
      await updateTenant.mutateAsync({
        id,
        data: {
          name: editName,
          // Note: Plan changes require a separate subscription update
        },
      });
      toast({ title: "Tenant updated" });
      setIsEditing(false);
    } catch {
      toast({ title: "Failed to update tenant", variant: "error" });
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="w-8 h-8 animate-spin text-accent" />
      </div>
    );
  }

  // Error state
  if (error || !tenant) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <div className="text-status-error mb-4">
          <FileText className="w-12 h-12" />
        </div>
        <h2 className="text-xl font-semibold text-text-primary mb-2">Tenant not found</h2>
        <p className="text-text-muted mb-6">
          The tenant you&apos;re looking for doesn&apos;t exist or you don&apos;t have access.
        </p>
        <Button onClick={() => router.push("/tenants")}>Back to Tenants</Button>
      </div>
    );
  }

  const status = statusColors[tenant.status] || statusColors.inactive;
  const planName = getPlanName(tenant.plan);
  const plan = planColors[planName as keyof typeof planColors] || planColors.Free;

  return (
    <div className="space-y-8 animate-fade-up">
      {dialog}

      {/* Page Header */}
      <PageHeader
        title={tenant.name}
        breadcrumbs={[{ label: "Tenants", href: "/tenants" }, { label: tenant.name }]}
        badge={
          <div className="flex items-center gap-2">
            <span
              className={cn(
                "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium",
                status.bg,
                status.text
              )}
            >
              <span className={cn("w-1.5 h-1.5 rounded-full", status.dot)} />
              {tenantStatuses.find((s) => s.value === tenant.status)?.label || tenant.status}
            </span>
            <span
              className={cn(
                "inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium",
                plan.bg,
                plan.text
              )}
            >
              {planName}
            </span>
          </div>
        }
        actions={
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={() => refetch()}>
              <RefreshCcw className="w-4 h-4" />
            </Button>
            {!isEditing && (
              <Button variant="outline" onClick={startEditing}>
                <Edit3 className="w-4 h-4 mr-2" />
                Edit
              </Button>
            )}
            <Button variant="destructive" onClick={handleDelete}>
              <Trash2 className="w-4 h-4 mr-2" />
              Delete
            </Button>
          </div>
        }
      />

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Tenant Information */}
          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-text-primary">Tenant Information</h3>
              {isEditing && (
                <div className="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={cancelEditing}
                    disabled={updateTenant.isPending}
                  >
                    <X className="w-4 h-4" />
                  </Button>
                  <Button size="sm" onClick={saveChanges} disabled={updateTenant.isPending}>
                    {updateTenant.isPending ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Check className="w-4 h-4" />
                    )}
                  </Button>
                </div>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {isEditing ? (
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
                    <Building2 className="w-5 h-5 text-accent" />
                  </div>
                  <div className="flex-1">
                    <p className="text-xs text-text-muted mb-1">Name</p>
                    <Input
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                      placeholder="Tenant name"
                    />
                  </div>
                </div>
              ) : (
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
                    <Building2 className="w-5 h-5 text-accent" />
                  </div>
                  <div>
                    <p className="text-xs text-text-muted">Name</p>
                    <p className="text-sm text-text-primary">{tenant.name}</p>
                  </div>
                </div>
              )}

              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-surface-overlay flex items-center justify-center">
                  <Globe className="w-5 h-5 text-text-muted" />
                </div>
                <div>
                  <p className="text-xs text-text-muted">Slug</p>
                  <p className="text-sm text-text-primary font-mono">{tenant.slug}</p>
                </div>
              </div>

              {isEditing ? (
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-status-success/15 flex items-center justify-center">
                    <CreditCard className="w-5 h-5 text-status-success" />
                  </div>
                  <div className="flex-1">
                    <p className="text-xs text-text-muted mb-1">Plan</p>
                    <Select
                      value={editPlan}
                      onValueChange={setEditPlan}
                      options={tenantPlans.map((p) => ({ value: p.value, label: p.label }))}
                    />
                  </div>
                </div>
              ) : (
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-status-success/15 flex items-center justify-center">
                    <CreditCard className="w-5 h-5 text-status-success" />
                  </div>
                  <div>
                    <p className="text-xs text-text-muted">Plan</p>
                    <p className="text-sm text-text-primary">{planName}</p>
                  </div>
                </div>
              )}

              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-surface-overlay flex items-center justify-center">
                  <Calendar className="w-5 h-5 text-text-muted" />
                </div>
                <div>
                  <p className="text-xs text-text-muted">Created</p>
                  <p className="text-sm text-text-primary">
                    {format(new Date(tenant.createdAt), "MMM d, yyyy")}
                  </p>
                </div>
              </div>

              {tenant.domain && (
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-highlight-subtle flex items-center justify-center">
                    <Globe className="w-5 h-5 text-highlight" />
                  </div>
                  <div>
                    <p className="text-xs text-text-muted">Custom Domain</p>
                    <p className="text-sm text-text-primary">{tenant.domain}</p>
                  </div>
                </div>
              )}
            </div>
          </Card>

          {/* Usage Stats */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-text-primary mb-4">Usage Statistics</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 rounded-lg bg-surface-secondary border border-border-default">
                <div className="flex items-center gap-2 mb-2">
                  <Users className="w-4 h-4 text-accent" />
                  <span className="text-xs text-text-muted">Users</span>
                </div>
                <p className="text-2xl font-semibold text-text-primary">
                  {stats?.userCount ?? tenant.userCount}
                </p>
              </div>

              <div className="p-4 rounded-lg bg-surface-secondary border border-border-default">
                <div className="flex items-center gap-2 mb-2">
                  <Activity className="w-4 h-4 text-highlight" />
                  <span className="text-xs text-text-muted">Deployments</span>
                </div>
                <p className="text-2xl font-semibold text-text-primary">
                  {stats?.deploymentsActive ?? 0}
                </p>
              </div>

              <div className="p-4 rounded-lg bg-surface-secondary border border-border-default">
                <div className="flex items-center gap-2 mb-2">
                  <HardDrive className="w-4 h-4 text-status-info" />
                  <span className="text-xs text-text-muted">Storage</span>
                </div>
                <p className="text-2xl font-semibold text-text-primary">
                  {stats?.storageUsed
                    ? `${(stats.storageUsed / 1024 / 1024 / 1024).toFixed(1)}GB`
                    : "0GB"}
                </p>
                {stats?.storageLimit && (
                  <p className="text-xs text-text-muted mt-1">
                    of {(stats.storageLimit / 1024 / 1024 / 1024).toFixed(0)}GB
                  </p>
                )}
              </div>

              <div className="p-4 rounded-lg bg-surface-secondary border border-border-default">
                <div className="flex items-center gap-2 mb-2">
                  <CreditCard className="w-4 h-4 text-status-success" />
                  <span className="text-xs text-text-muted">MRR</span>
                </div>
                <p className="text-2xl font-semibold text-text-primary">
                  ${((stats?.mrr || 0) / 100).toLocaleString()}
                </p>
              </div>
            </div>
          </Card>

          {/* Members */}
          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-text-primary">Members</h3>
              <Button variant="ghost" size="sm">
                View All
              </Button>
            </div>
            {members?.members && members.members.length > 0 ? (
              <div className="space-y-3">
                {members.members.slice(0, 5).map((member) => (
                  <div
                    key={member.id}
                    className="flex items-center justify-between p-3 rounded-lg bg-surface-secondary"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-accent-subtle flex items-center justify-center">
                        <span className="text-xs font-medium text-accent">
                          {member.fullName.charAt(0).toUpperCase()}
                        </span>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-text-primary">{member.fullName}</p>
                        <p className="text-xs text-text-muted">{member.email}</p>
                      </div>
                    </div>
                    <span className="text-xs font-medium text-text-secondary capitalize">
                      {member.role}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-text-muted">No members found</p>
            )}
          </Card>
        </div>

        {/* Right Column - Actions */}
        <div className="space-y-6">
          {/* Quick Actions */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-text-primary mb-4">Quick Actions</h3>
            <div className="space-y-2">
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => router.push(`/tenants/${id}/settings`)}
              >
                <Settings className="w-4 h-4 mr-2" />
                Settings
              </Button>

              {tenant.status === "active" || tenant.status === "trial" ? (
                <Button
                  variant="outline"
                  className="w-full justify-start text-status-warning hover:text-status-warning"
                  onClick={handleSuspend}
                  disabled={suspendTenant.isPending}
                >
                  <Ban className="w-4 h-4 mr-2" />
                  Suspend Tenant
                </Button>
              ) : tenant.status === "suspended" ? (
                <Button
                  variant="outline"
                  className="w-full justify-start text-status-success hover:text-status-success"
                  onClick={handleActivate}
                  disabled={activateTenant.isPending}
                >
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Activate Tenant
                </Button>
              ) : null}
            </div>
          </Card>

          {/* Plan Features */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-text-primary mb-4">Plan Features</h3>
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-status-success" />
                <span className="text-sm text-text-secondary">API Access</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-status-success" />
                <span className="text-sm text-text-secondary">Webhooks</span>
              </div>
              {(planName === "Professional" || planName === "Enterprise") && (
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-status-success" />
                  <span className="text-sm text-text-secondary">SSO</span>
                </div>
              )}
              {planName === "Enterprise" && (
                <>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-status-success" />
                    <span className="text-sm text-text-secondary">Custom Domain</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-status-success" />
                    <span className="text-sm text-text-secondary">Audit Logs</span>
                  </div>
                </>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
