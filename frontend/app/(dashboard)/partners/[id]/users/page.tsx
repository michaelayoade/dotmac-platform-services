"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  Plus,
  MoreHorizontal,
  Mail,
  KeyRound,
  UserX,
  Pencil,
  ArrowLeft,
} from "lucide-react";
import { Button, useToast } from "@/lib/dotmac/core";
import { usePartner, usePartnerUsers, useRemovePartnerUser } from "@/lib/hooks/api/use-partners";
import { InvitePartnerUserModal } from "@/components/features/partner/invite-partner-user-modal";
import { resetPassword } from "@/lib/api/users";

export default function PartnerUsersPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const partnerId = params.id;
  const { toast } = useToast();

  const [isInviteModalOpen, setIsInviteModalOpen] = useState(false);
  const [openDropdownId, setOpenDropdownId] = useState<string | null>(null);

  const { data: partner, isLoading: partnerLoading } = usePartner(partnerId);
  const { data: users, isLoading: usersLoading } = usePartnerUsers(partnerId);
  const removeUser = useRemovePartnerUser();

  const isLoading = partnerLoading || usersLoading;

  const handleRemoveUser = async (userId: string) => {
    if (!confirm("Are you sure you want to remove this user?")) return;
    try {
      await removeUser.mutateAsync({ partnerId, userId });
    } catch (error) {
      console.error("Failed to remove user:", error);
    }
    setOpenDropdownId(null);
  };

  const handleResetPassword = async (userId: string) => {
    if (!confirm("Send a password reset email to this user?")) return;
    try {
      await resetPassword(userId);
      toast({ title: "Password reset email sent" });
    } catch {
      toast({ title: "Failed to send reset email", variant: "error" });
    }
    setOpenDropdownId(null);
  };

  if (isLoading) {
    return <PageSkeleton />;
  }

  const activeUsers = users?.filter((u) => u.isActive) ?? [];
  const inactiveUsers = users?.filter((u) => !u.isActive) ?? [];

  return (
    <div className="space-y-6">
      {/* Breadcrumbs */}
      <nav aria-label="Breadcrumb" className="flex items-center gap-2 text-sm text-text-muted">
        <Link href="/" className="hover:text-text-secondary">
          Dashboard
        </Link>
        <span aria-hidden="true">/</span>
        <Link href="/partners" className="hover:text-text-secondary">
          Partners
        </Link>
        <span aria-hidden="true">/</span>
        <Link href={`/partners/${partnerId}`} className="hover:text-text-secondary">
          {partner?.companyName ?? "Partner"}
        </Link>
        <span aria-hidden="true">/</span>
        <span className="text-text-primary">Users</span>
      </nav>

      {/* Page Header */}
      <div className="page-header">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => router.back()}>
            <ArrowLeft className="w-4 h-4" />
          </Button>
          <div>
            <h1 className="page-title">Partner Users</h1>
            <p className="page-description">
              Manage users for {partner?.companyName}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Button
            className="shadow-glow-sm hover:shadow-glow"
            onClick={() => setIsInviteModalOpen(true)}
          >
            <Plus className="w-4 h-4 mr-2" />
            Invite User
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="quick-stats">
        <div className="quick-stat">
          <p className="metric-label">Total Users</p>
          <p className="metric-value text-2xl">{users?.length ?? 0}</p>
        </div>
        <div className="quick-stat">
          <p className="metric-label">Active</p>
          <p className="metric-value text-2xl text-status-success">
            {activeUsers.length}
          </p>
        </div>
        <div className="quick-stat">
          <p className="metric-label">Inactive</p>
          <p className="metric-value text-2xl text-status-warning">
            {inactiveUsers.length}
          </p>
        </div>
        <div className="quick-stat">
          <p className="metric-label">Primary Contact</p>
          <p className="metric-value text-2xl">
            {users?.filter((u) => u.isPrimaryContact).length ?? 0}
          </p>
        </div>
      </div>

      {/* Users Table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full" aria-label="Partner users"><caption className="sr-only">Partner users</caption>
            <thead className="bg-surface-raised border-b border-border">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-text-muted uppercase tracking-wider">
                  User
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-text-muted uppercase tracking-wider">
                  Role
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-text-muted uppercase tracking-wider">
                  Status
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-text-muted uppercase tracking-wider">
                  Phone
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-text-muted uppercase tracking-wider">
                  Created
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-text-muted uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-subtle">
              {users?.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center text-text-muted">
                    No users found. Click &quot;Invite User&quot; to add team members.
                  </td>
                </tr>
              ) : (
                users?.map((user) => (
                  <tr key={user.id} className="hover:bg-surface-raised/50">
                    <td className="px-4 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-brand-primary/10 flex items-center justify-center text-brand-primary font-medium">
                          {user.firstName?.[0]}
                          {user.lastName?.[0]}
                        </div>
                        <div>
                          <div className="font-medium text-text-primary flex items-center gap-2">
                            {user.firstName} {user.lastName}
                            {user.isPrimaryContact && (
                              <span className="badge badge-info text-xs">Primary</span>
                            )}
                          </div>
                          <div className="text-sm text-text-muted">{user.email}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      <span className="badge badge-default capitalize">
                        {user.role?.replace("_", " ")}
                      </span>
                    </td>
                    <td className="px-4 py-4">
                      <span
                        className={`badge ${user.isActive ? "badge-success" : "badge-warning"}`}
                      >
                        {user.isActive ? "Active" : "Inactive"}
                      </span>
                    </td>
                    <td className="px-4 py-4 text-text-secondary">
                      {user.phone || "—"}
                    </td>
                    <td className="px-4 py-4 text-text-secondary text-sm">
                      {new Date(user.createdAt).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-4 text-right">
                      <div className="relative inline-block">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() =>
                            setOpenDropdownId(openDropdownId === user.id ? null : user.id)
                          }
                        >
                          <MoreHorizontal className="w-4 h-4" />
                        </Button>
                        {openDropdownId === user.id && (
                          <div className="absolute right-0 mt-2 w-48 rounded-md shadow-lg bg-surface-overlay border border-border z-10">
                            <div className="py-1">
                              <Link
                                href={`/partners/${partnerId}/users/${user.id}`}
                                className="flex items-center gap-2 px-4 py-2 text-sm text-text-secondary hover:bg-surface-raised"
                              >
                                <Pencil className="w-4 h-4" />
                                Edit
                              </Link>
                              <button
                                className="flex items-center gap-2 px-4 py-2 text-sm text-text-secondary hover:bg-surface-raised w-full text-left"
                                onClick={() => handleResetPassword(user.id)}
                              >
                                <KeyRound className="w-4 h-4" />
                                Reset Password
                              </button>
                              <button
                                className="flex items-center gap-2 px-4 py-2 text-sm text-status-error hover:bg-surface-raised w-full text-left"
                                onClick={() => handleRemoveUser(user.id)}
                              >
                                <UserX className="w-4 h-4" />
                                Remove User
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Invite Modal */}
      <InvitePartnerUserModal
        partnerId={partnerId}
        isOpen={isInviteModalOpen}
        onClose={() => setIsInviteModalOpen(false)}
      />
    </div>
  );
}

function PageSkeleton() {
  return (
    <div className="space-y-6">
      <div className="h-5 w-48 skeleton" />
      <div className="page-header">
        <div className="space-y-2">
          <div className="h-8 w-48 skeleton" />
          <div className="h-4 w-64 skeleton" />
        </div>
        <div className="h-10 w-32 skeleton" />
      </div>
      <div className="quick-stats">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="quick-stat">
            <div className="h-4 w-24 skeleton mb-2" />
            <div className="h-8 w-12 skeleton" />
          </div>
        ))}
      </div>
      <div className="card overflow-hidden">
        <div className="divide-y divide-border-subtle">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="px-4 py-4 flex items-center gap-4">
              <div className="w-10 h-10 rounded-full skeleton" />
              <div className="flex-1 space-y-2">
                <div className="h-4 w-48 skeleton" />
                <div className="h-3 w-32 skeleton" />
              </div>
              <div className="h-6 w-20 skeleton rounded-full" />
              <div className="h-4 w-24 skeleton" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
