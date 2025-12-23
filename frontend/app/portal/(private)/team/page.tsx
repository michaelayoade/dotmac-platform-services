"use client";

import { useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import {
  Plus,
  Search,
  Users,
  Mail,
  MoreVertical,
  Shield,
  Clock,
  UserX,
  RefreshCw,
  X,
} from "lucide-react";

import { PageHeader, StatusBadge, EmptyState, Avatar } from "@/components/shared";
import { InviteMemberModal } from "@/components/features/tenant/invite-member-modal";
import {
  useTenantMembers,
  useTenantInvitations,
  useUpdateMemberRole,
  useRemoveMember,
  useCancelInvitation,
  useResendInvitation,
} from "@/lib/hooks/api/use-tenant-portal";
import { useConfirmDialog } from "@/components/shared/confirm-dialog";
import { cn } from "@/lib/utils";
import type { Invitation, MemberRole, MemberStatus, TeamMember } from "@/types/tenant-portal";

const roleLabels: Record<MemberRole, string> = {
  tenant_admin: "Admin",
  member: "Member",
  viewer: "Viewer",
};

const roleColors: Record<MemberRole, string> = {
  tenant_admin: "bg-purple-500/10 text-purple-500",
  member: "bg-blue-500/10 text-blue-500",
  viewer: "bg-gray-500/10 text-gray-500",
};

// Demo data
const demoMembers = [
  {
    id: "1",
    userId: "u1",
    email: "admin@company.com",
    fullName: "John Admin",
    role: "tenant_admin" as MemberRole,
    status: "ACTIVE" as MemberStatus,
    lastActiveAt: "2024-12-23T10:30:00Z",
    joinedAt: "2024-01-15T00:00:00Z",
  },
  {
    id: "2",
    userId: "u2",
    email: "sarah@company.com",
    fullName: "Sarah Johnson",
    role: "member" as MemberRole,
    status: "ACTIVE" as MemberStatus,
    lastActiveAt: "2024-12-22T14:30:00Z",
    joinedAt: "2024-03-01T00:00:00Z",
  },
  {
    id: "3",
    userId: "u3",
    email: "michael@company.com",
    fullName: "Michael Chen",
    role: "member" as MemberRole,
    status: "ACTIVE" as MemberStatus,
    lastActiveAt: "2024-12-21T09:15:00Z",
    joinedAt: "2024-06-15T00:00:00Z",
  },
  {
    id: "4",
    userId: "u4",
    email: "emily@company.com",
    fullName: "Emily Rodriguez",
    role: "viewer" as MemberRole,
    status: "ACTIVE" as MemberStatus,
    lastActiveAt: "2024-12-20T16:45:00Z",
    joinedAt: "2024-09-01T00:00:00Z",
  },
];

const demoInvitations = [
  {
    id: "inv1",
    email: "newuser@company.com",
    role: "member" as MemberRole,
    status: "PENDING" as const,
    invitedBy: "u1",
    invitedByName: "John Admin",
    expiresAt: "2024-12-30T00:00:00Z",
    createdAt: "2024-12-20T10:00:00Z",
  },
];

function MemberCard({
  member,
  onRoleChange,
  onRemove,
}: {
  member: TeamMember;
  onRoleChange: (id: string, role: MemberRole) => void;
  onRemove: (id: string) => void;
}) {
  const [showMenu, setShowMenu] = useState(false);
  const [showRoleMenu, setShowRoleMenu] = useState(false);

  const formatTimeAgo = (dateString?: string) => {
    if (!dateString) return "Never";
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));

    if (diffInHours < 1) return "Just now";
    if (diffInHours < 24) return `${diffInHours}h ago`;
    if (diffInHours < 168) return `${Math.floor(diffInHours / 24)}d ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="bg-surface-elevated rounded-lg border border-border p-5 hover:border-border-hover transition-colors">
      <div className="flex items-start gap-4">
        <Avatar name={member.fullName} size="lg" />

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-semibold text-text-primary truncate">
              {member.fullName}
            </h3>
            <span className={cn("text-xs px-2 py-0.5 rounded-full font-medium", roleColors[member.role])}>
              {roleLabels[member.role]}
            </span>
          </div>
          <p className="text-sm text-text-muted truncate">{member.email}</p>
          <p className="text-xs text-text-muted mt-2">
            Last active {formatTimeAgo(member.lastActiveAt)}
          </p>
        </div>

        <div className="relative">
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="p-2 rounded-md text-text-muted hover:text-text-secondary hover:bg-surface-overlay transition-colors"
          >
            <MoreVertical className="w-4 h-4" />
          </button>

          {showMenu && (
            <>
              <div
                className="fixed inset-0 z-10"
                onClick={() => setShowMenu(false)}
              />
              <div className="absolute right-0 mt-1 w-48 bg-surface-elevated rounded-lg border border-border shadow-lg z-20 py-1">
                <button
                  onClick={() => {
                    setShowRoleMenu(true);
                    setShowMenu(false);
                  }}
                  className="w-full px-4 py-2 text-left text-sm text-text-secondary hover:bg-surface-overlay transition-colors flex items-center gap-2"
                >
                  <Shield className="w-4 h-4" />
                  Change Role
                </button>
                <button
                  onClick={() => {
                    onRemove(member.id);
                    setShowMenu(false);
                  }}
                  className="w-full px-4 py-2 text-left text-sm text-status-error hover:bg-status-error/10 transition-colors flex items-center gap-2"
                >
                  <UserX className="w-4 h-4" />
                  Remove Member
                </button>
              </div>
            </>
          )}

          {showRoleMenu && (
            <>
              <div
                className="fixed inset-0 z-10"
                onClick={() => setShowRoleMenu(false)}
              />
              <div className="absolute right-0 mt-1 w-48 bg-surface-elevated rounded-lg border border-border shadow-lg z-20 py-1">
                {(["tenant_admin", "member", "viewer"] as MemberRole[]).map(
                  (role) => (
                    <button
                      key={role}
                      onClick={() => {
                        onRoleChange(member.id, role);
                        setShowRoleMenu(false);
                      }}
                      className={cn(
                        "w-full px-4 py-2 text-left text-sm transition-colors flex items-center justify-between",
                        member.role === role
                          ? "bg-accent/10 text-accent"
                          : "text-text-secondary hover:bg-surface-overlay"
                      )}
                    >
                      <span className="capitalize">{role.replace("_", " ")}</span>
                      {member.role === role && (
                        <span className="text-xs">Current</span>
                      )}
                    </button>
                  )
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function InvitationCard({
  invitation,
  onCancel,
  onResend,
}: {
  invitation: Invitation;
  onCancel: (id: string) => void;
  onResend: (id: string) => void;
}) {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    });
  };

  const isExpired = new Date(invitation.expiresAt) < new Date();

  return (
    <div className="bg-surface-elevated rounded-lg border border-border p-5">
      <div className="flex items-start gap-4">
        <div className="p-3 rounded-full bg-surface-overlay">
          <Mail className="w-5 h-5 text-text-muted" />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-medium text-text-primary truncate">
              {invitation.email}
            </h3>
            <StatusBadge
              status={isExpired ? "error" : "pending"}
              label={isExpired ? "Expired" : "Pending"}
            />
          </div>
          <p className="text-sm text-text-muted">
            Invited as {roleLabels[invitation.role]} by {invitation.invitedByName}
          </p>
          <p className="text-xs text-text-muted mt-1">
            {isExpired ? "Expired" : "Expires"} {formatDate(invitation.expiresAt)}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => onResend(invitation.id)}
            className="p-2 rounded-md text-text-muted hover:text-accent hover:bg-accent/10 transition-colors"
            title="Resend invitation"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <button
            onClick={() => onCancel(invitation.id)}
            className="p-2 rounded-md text-text-muted hover:text-status-error hover:bg-status-error/10 transition-colors"
            title="Cancel invitation"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

function TeamSkeleton() {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 animate-pulse">
      {[1, 2, 3, 4].map((i) => (
        <div
          key={i}
          className="bg-surface-elevated rounded-lg border border-border p-5 h-32"
        >
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-full bg-surface-overlay" />
            <div className="flex-1">
              <div className="h-5 w-32 bg-surface-overlay rounded mb-2" />
              <div className="h-4 w-40 bg-surface-overlay rounded" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

export default function TeamPage() {
  const searchParams = useSearchParams();
  const [isInviteOpen, setIsInviteOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  const { data: membersData, isLoading: membersLoading, refetch: refetchMembers } = useTenantMembers();
  const { data: invitationsData, refetch: refetchInvitations } = useTenantInvitations();
  const updateRole = useUpdateMemberRole();
  const removeMember = useRemoveMember();
  const cancelInvitation = useCancelInvitation();
  const resendInvitation = useResendInvitation();

  const confirmDialog = useConfirmDialog();

  useEffect(() => {
    if (searchParams.get("action") === "invite") {
      setIsInviteOpen(true);
    }
  }, [searchParams]);

  const members = membersData?.members || demoMembers;
  const invitations = invitationsData?.invitations || demoInvitations;

  const filteredMembers = searchQuery
    ? members.filter(
        (m) =>
          m.fullName.toLowerCase().includes(searchQuery.toLowerCase()) ||
          m.email.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : members;

  const handleRoleChange = async (id: string, role: MemberRole) => {
    try {
      await updateRole.mutateAsync({ id, data: { role } });
    } catch (error) {
      console.error("Failed to update role:", error);
    }
  };

  const handleRemoveMember = async (id: string) => {
    const member = members.find((m) => m.id === id);
    const confirmed = await confirmDialog.confirm({
      title: "Remove Team Member",
      description: `Are you sure you want to remove ${member?.fullName} from the team? They will lose access to this organization.`,
      variant: "danger",
    });

    if (confirmed) {
      try {
        await removeMember.mutateAsync(id);
      } catch (error) {
        console.error("Failed to remove member:", error);
      }
    }
  };

  const handleCancelInvitation = async (id: string) => {
    try {
      await cancelInvitation.mutateAsync(id);
    } catch (error) {
      console.error("Failed to cancel invitation:", error);
    }
  };

  const handleResendInvitation = async (id: string) => {
    try {
      await resendInvitation.mutateAsync(id);
    } catch (error) {
      console.error("Failed to resend invitation:", error);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Team Members"
        description="Manage your organization's team"
        actions={
          <button
            onClick={() => setIsInviteOpen(true)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-accent text-white hover:bg-accent-hover transition-colors"
          >
            <Plus className="w-4 h-4" />
            Invite Member
          </button>
        }
      />

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-3">
        <div className="bg-surface-elevated rounded-lg border border-border p-5">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-accent/10 text-accent">
              <Users className="w-5 h-5" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Total Members</p>
              <p className="text-xl font-semibold text-text-primary">
                {members.length}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-surface-elevated rounded-lg border border-border p-5">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-purple-500/10 text-purple-500">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Admins</p>
              <p className="text-xl font-semibold text-text-primary">
                {members.filter((m) => m.role === "tenant_admin").length}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-surface-elevated rounded-lg border border-border p-5">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-status-warning/10 text-status-warning">
              <Clock className="w-5 h-5" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Pending Invites</p>
              <p className="text-xl font-semibold text-text-primary">
                {invitations.filter((i) => i.status === "PENDING").length}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
        <input
          type="text"
          placeholder="Search members..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-2 rounded-md border border-border bg-surface text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent"
        />
      </div>

      {/* Pending Invitations */}
      {invitations.length > 0 && (
        <div>
          <h2 className="text-sm font-semibold text-text-muted uppercase tracking-wider mb-3">
            Pending Invitations
          </h2>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {invitations.map((invitation) => (
              <InvitationCard
                key={invitation.id}
                invitation={invitation}
                onCancel={handleCancelInvitation}
                onResend={handleResendInvitation}
              />
            ))}
          </div>
        </div>
      )}

      {/* Team Members */}
      <div>
        <h2 className="text-sm font-semibold text-text-muted uppercase tracking-wider mb-3">
          Team Members ({filteredMembers.length})
        </h2>
        {membersLoading ? (
          <TeamSkeleton />
        ) : filteredMembers.length === 0 ? (
          <EmptyState
            icon={Users}
            title="No members found"
            description={
              searchQuery
                ? "Try adjusting your search"
                : "Invite team members to get started"
            }
            action={
              searchQuery
                ? undefined
                : {
                    label: "Invite Member",
                    onClick: () => setIsInviteOpen(true),
                  }
            }
          />
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {filteredMembers.map((member) => (
              <MemberCard
                key={member.id}
                member={member}
                onRoleChange={handleRoleChange}
                onRemove={handleRemoveMember}
              />
            ))}
          </div>
        )}
      </div>

      {/* Invite Modal */}
      <InviteMemberModal
        isOpen={isInviteOpen}
        onClose={() => setIsInviteOpen(false)}
        onSuccess={() => {
          refetchMembers();
          refetchInvitations();
        }}
      />

      {/* Confirm Dialog */}
      {confirmDialog.dialog}
    </div>
  );
}
