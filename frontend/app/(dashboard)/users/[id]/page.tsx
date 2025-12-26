"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Mail,
  Shield,
  Calendar,
  Clock,
  Trash2,
  RefreshCcw,
  FileText,
  UserX,
  UserCheck,
  KeyRound,
  Send,
  Edit3,
  Check,
  X,
  Loader2,
} from "lucide-react";
import { format } from "date-fns";
import { Button, Card, Input, Select } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import { ConfirmDialog, useConfirmDialog } from "@/components/shared/confirm-dialog";
import {
  useUser,
  useUpdateUser,
  useDeleteUser,
  useSuspendUser,
  useActivateUser,
  useResendInvite,
  useResetPassword,
} from "@/lib/hooks/api/use-users";
import { userRoles, userStatuses } from "@/lib/schemas/users";

interface UserDetailPageProps {
  params: { id: string };
}

const statusColors: Record<string, { bg: string; text: string; dot: string }> = {
  active: { bg: "bg-status-success/15", text: "text-status-success", dot: "bg-status-success" },
  pending: { bg: "bg-status-warning/15", text: "text-status-warning", dot: "bg-status-warning" },
  suspended: { bg: "bg-status-error/15", text: "text-status-error", dot: "bg-status-error" },
  inactive: { bg: "bg-surface-overlay", text: "text-text-muted", dot: "bg-text-muted" },
};

const roleColors: Record<string, { bg: string; text: string }> = {
  owner: { bg: "bg-accent-subtle", text: "text-accent" },
  admin: { bg: "bg-highlight-subtle", text: "text-highlight" },
  member: { bg: "bg-status-info/15", text: "text-status-info" },
  viewer: { bg: "bg-surface-overlay", text: "text-text-secondary" },
};

export default function UserDetailPage({ params }: UserDetailPageProps) {
  const { id } = params;
  const router = useRouter();
  const { toast } = useToast();
  const { confirm, dialog } = useConfirmDialog();

  const [isEditing, setIsEditing] = useState(false);
  const [editName, setEditName] = useState("");
  const [editRole, setEditRole] = useState<string>("");

  // Data fetching
  const { data: user, isLoading, error, refetch } = useUser(id);

  // Mutations
  const updateUser = useUpdateUser();
  const deleteUser = useDeleteUser();
  const suspendUser = useSuspendUser();
  const activateUser = useActivateUser();
  const resendInvite = useResendInvite();
  const resetPassword = useResetPassword();

  const handleDelete = async () => {
    const confirmed = await confirm({
      title: "Delete User",
      description: `Are you sure you want to delete "${user?.name}"? This action cannot be undone.`,
      variant: "danger",
    });

    if (confirmed) {
      try {
        await deleteUser.mutateAsync(id);
        toast({
          title: "User deleted",
          description: "The user has been successfully deleted.",
        });
        router.push("/users");
      } catch {
        toast({
          title: "Error",
          description: "Failed to delete user. Please try again.",
          variant: "error",
        });
      }
    }
  };

  const handleSuspend = async () => {
    const confirmed = await confirm({
      title: "Suspend User",
      description: `Are you sure you want to suspend "${user?.name}"? They will lose access immediately.`,
      variant: "danger",
    });

    if (confirmed) {
      try {
        await suspendUser.mutateAsync(id);
        toast({ title: "User suspended" });
      } catch {
        toast({ title: "Failed to suspend user", variant: "error" });
      }
    }
  };

  const handleActivate = async () => {
    try {
      await activateUser.mutateAsync(id);
      toast({ title: "User activated" });
    } catch {
      toast({ title: "Failed to activate user", variant: "error" });
    }
  };

  const handleResendInvite = async () => {
    try {
      await resendInvite.mutateAsync(id);
      toast({ title: "Invitation sent", description: `A new invitation has been sent to ${user?.email}` });
    } catch {
      toast({ title: "Failed to send invitation", variant: "error" });
    }
  };

  const handleResetPassword = async () => {
    const confirmed = await confirm({
      title: "Reset Password",
      description: `Send a password reset email to "${user?.email}"?`,
    });

    if (confirmed) {
      try {
        await resetPassword.mutateAsync(id);
        toast({ title: "Password reset email sent" });
      } catch {
        toast({ title: "Failed to send reset email", variant: "error" });
      }
    }
  };

  const startEditing = () => {
    if (user) {
      setEditName(user.name);
      setEditRole(user.role);
      setIsEditing(true);
    }
  };

  const cancelEditing = () => {
    setIsEditing(false);
    setEditName("");
    setEditRole("");
  };

  const saveChanges = async () => {
    try {
      await updateUser.mutateAsync({
        id,
        data: {
          name: editName,
          role: editRole as "owner" | "admin" | "member" | "viewer",
        },
      });
      toast({ title: "User updated" });
      setIsEditing(false);
    } catch {
      toast({ title: "Failed to update user", variant: "error" });
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
  if (error || !user) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <div className="text-status-error mb-4">
          <FileText className="w-12 h-12" />
        </div>
        <h2 className="text-xl font-semibold text-text-primary mb-2">User not found</h2>
        <p className="text-text-muted mb-6">
          The user you&apos;re looking for doesn&apos;t exist or you don&apos;t have access.
        </p>
        <Button onClick={() => router.push("/users")}>Back to Users</Button>
      </div>
    );
  }

  const status = statusColors[user.status] || statusColors.inactive;
  const role = roleColors[user.role] || roleColors.viewer;

  return (
    <div className="space-y-8 animate-fade-up">
      {dialog}

      {/* Page Header */}
      <PageHeader
        title={user.name}
        breadcrumbs={[{ label: "Users", href: "/users" }, { label: user.name }]}
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
              {userStatuses.find((s) => s.value === user.status)?.label || user.status}
            </span>
            <span
              className={cn(
                "inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium",
                role.bg,
                role.text
              )}
            >
              {userRoles.find((r) => r.value === user.role)?.label || user.role}
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
          {/* User Information */}
          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-text-primary">User Information</h3>
              {isEditing && (
                <div className="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={cancelEditing}
                    disabled={updateUser.isPending}
                  >
                    <X className="w-4 h-4" />
                  </Button>
                  <Button size="sm" onClick={saveChanges} disabled={updateUser.isPending}>
                    {updateUser.isPending ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Check className="w-4 h-4" />
                    )}
                  </Button>
                </div>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
                  <Mail className="w-5 h-5 text-accent" />
                </div>
                <div className="flex-1">
                  <p className="text-xs text-text-muted">Email</p>
                  <a href={`mailto:${user.email}`} className="text-sm text-accent hover:underline">
                    {user.email}
                  </a>
                </div>
              </div>

              {isEditing ? (
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-highlight-subtle flex items-center justify-center">
                    <Shield className="w-5 h-5 text-highlight" />
                  </div>
                  <div className="flex-1">
                    <p className="text-xs text-text-muted mb-1">Name</p>
                    <Input
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                      placeholder="User name"
                    />
                  </div>
                </div>
              ) : (
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-highlight-subtle flex items-center justify-center">
                    <Shield className="w-5 h-5 text-highlight" />
                  </div>
                  <div>
                    <p className="text-xs text-text-muted">Name</p>
                    <p className="text-sm text-text-primary">{user.name}</p>
                  </div>
                </div>
              )}

              {isEditing ? (
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-status-info/15 flex items-center justify-center">
                    <Shield className="w-5 h-5 text-status-info" />
                  </div>
                  <div className="flex-1">
                    <p className="text-xs text-text-muted mb-1">Role</p>
                    <Select
                      value={editRole}
                      onValueChange={setEditRole}
                      options={userRoles.map((r) => ({ value: r.value, label: r.label }))}
                    />
                  </div>
                </div>
              ) : (
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-status-info/15 flex items-center justify-center">
                    <Shield className="w-5 h-5 text-status-info" />
                  </div>
                  <div>
                    <p className="text-xs text-text-muted">Role</p>
                    <p className="text-sm text-text-primary">
                      {userRoles.find((r) => r.value === user.role)?.label || user.role}
                    </p>
                  </div>
                </div>
              )}

              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-surface-overlay flex items-center justify-center">
                  <Calendar className="w-5 h-5 text-text-muted" />
                </div>
                <div>
                  <p className="text-xs text-text-muted">Joined</p>
                  <p className="text-sm text-text-primary">
                    {format(new Date(user.createdAt), "MMM d, yyyy")}
                  </p>
                </div>
              </div>

              {user.lastLogin && (
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-status-success/15 flex items-center justify-center">
                    <Clock className="w-5 h-5 text-status-success" />
                  </div>
                  <div>
                    <p className="text-xs text-text-muted">Last Login</p>
                    <p className="text-sm text-text-primary">
                      {format(new Date(user.lastLogin), "MMM d, yyyy 'at' h:mm a")}
                    </p>
                  </div>
                </div>
              )}

              {user.tenantId && (
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-surface-overlay flex items-center justify-center">
                    <Shield className="w-5 h-5 text-text-muted" />
                  </div>
                  <div>
                    <p className="text-xs text-text-muted">Tenant ID</p>
                    <p className="text-sm text-text-primary font-mono">{user.tenantId}</p>
                  </div>
                </div>
              )}
            </div>
          </Card>

          {/* Security */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-text-primary mb-4">Security</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 rounded-lg border border-border-default bg-surface-secondary">
                <div className="flex items-center gap-3 mb-2">
                  <KeyRound className="w-5 h-5 text-text-muted" />
                  <span className="text-sm font-medium text-text-primary">
                    Two-Factor Authentication
                  </span>
                </div>
                <p className="text-xs text-text-muted">
                  {user.mfaEnabled ? (
                    <span className="text-status-success">Enabled</span>
                  ) : (
                    <span className="text-status-warning">Not enabled</span>
                  )}
                </p>
              </div>

              <div className="p-4 rounded-lg border border-border-default bg-surface-secondary">
                <div className="flex items-center gap-3 mb-2">
                  <Mail className="w-5 h-5 text-text-muted" />
                  <span className="text-sm font-medium text-text-primary">Email Verified</span>
                </div>
                <p className="text-xs text-text-muted">
                  {user.status !== "pending" ? (
                    <span className="text-status-success">Verified</span>
                  ) : (
                    <span className="text-status-warning">Pending verification</span>
                  )}
                </p>
              </div>
            </div>
          </Card>
        </div>

        {/* Right Column - Actions */}
        <div className="space-y-6">
          {/* Quick Actions */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-text-primary mb-4">Quick Actions</h3>
            <div className="space-y-2">
              {user.status === "pending" && (
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={handleResendInvite}
                  disabled={resendInvite.isPending}
                >
                  <Send className="w-4 h-4 mr-2" />
                  Resend Invitation
                </Button>
              )}

              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={handleResetPassword}
                disabled={resetPassword.isPending}
              >
                <KeyRound className="w-4 h-4 mr-2" />
                Reset Password
              </Button>

              {user.status === "active" ? (
                <Button
                  variant="outline"
                  className="w-full justify-start text-status-warning hover:text-status-warning"
                  onClick={handleSuspend}
                  disabled={suspendUser.isPending}
                >
                  <UserX className="w-4 h-4 mr-2" />
                  Suspend User
                </Button>
              ) : user.status === "suspended" ? (
                <Button
                  variant="outline"
                  className="w-full justify-start text-status-success hover:text-status-success"
                  onClick={handleActivate}
                  disabled={activateUser.isPending}
                >
                  <UserCheck className="w-4 h-4 mr-2" />
                  Activate User
                </Button>
              ) : null}
            </div>
          </Card>

          {/* Role Permissions */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-text-primary mb-4">Role Permissions</h3>
            <div className="text-sm text-text-muted space-y-2">
              {user.role === "owner" && (
                <>
                  <p>Full access to all features and settings</p>
                  <p>Can manage billing, users, and organization settings</p>
                  <p>Can delete the organization</p>
                </>
              )}
              {user.role === "admin" && (
                <>
                  <p>Full access to all features</p>
                  <p>Can manage users and most settings</p>
                  <p>Cannot access billing or delete organization</p>
                </>
              )}
              {user.role === "member" && (
                <>
                  <p>Can view and edit most resources</p>
                  <p>Can create and manage own content</p>
                  <p>Cannot manage users or settings</p>
                </>
              )}
              {user.role === "viewer" && (
                <>
                  <p>Read-only access to resources</p>
                  <p>Cannot create, edit, or delete content</p>
                  <p>Can view reports and dashboards</p>
                </>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
