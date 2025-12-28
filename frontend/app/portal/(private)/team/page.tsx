"use client";

import { useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import {
  Plus,
  Users,
  Mail,
  MoreVertical,
  Shield,
  Clock,
  UserX,
  RefreshCw,
  X,
} from "lucide-react";

import { PageHeader, StatusBadge, EmptyState, Avatar, SearchInput } from "@/components/shared";
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
  tenant_admin: "bg-status-info/15 text-status-info",
  member: "bg-status-success/15 text-status-success",
  viewer: "bg-surface-overlay text-text-muted",
};

const emptyMembers: TeamMember[] = [];
const emptyInvitations: Invitation[] = [];

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
            aria-haspopup="menu"
            aria-expanded={showMenu}
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
              <div
                role="menu"
                aria-label="Member actions"
                className="absolute right-0 mt-1 w-48 bg-surface-elevated rounded-lg border border-border shadow-lg z-20 py-1"
              >
                <button
                  onClick={() => {
                    setShowRoleMenu(true);
                    setShowMenu(false);
                  }}
                  role="menuitem"
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
                  role="menuitem"
                  className="w-full px-4 py-2 text-left text-sm text-status-error hover:bg-status-error/15 transition-colors flex items-center gap-2"
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
              <div
                role="menu"
                aria-label="Role selection"
                className="absolute right-0 mt-1 w-48 bg-surface-elevated rounded-lg border border-border shadow-lg z-20 py-1"
              >
                {(["tenant_admin", "member", "viewer"] as MemberRole[]).map(
                  (role) => (
                    <button
                      key={role}
                      onClick={() => {
                        onRoleChange(member.id, role);
                        setShowRoleMenu(false);
                      }}
                      role="menuitem"
                      className={cn(
                        "w-full px-4 py-2 text-left text-sm transition-colors flex items-center justify-between",
                        member.role === role
                          ? "bg-accent/15 text-accent"
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
            className="p-2 rounded-md text-text-muted hover:text-accent hover:bg-accent/15 transition-colors"
            title="Resend invitation"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <button
            onClick={() => onCancel(invitation.id)}
            className="p-2 rounded-md text-text-muted hover:text-status-error hover:bg-status-error/15 transition-colors"
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

  const members = membersData?.members ?? emptyMembers;
  const invitations = invitationsData?.invitations ?? emptyInvitations;
  const membersCount = membersData ? members.length : null;
  const adminsCount = membersData
    ? members.filter((m) => m.role === "tenant_admin").length
    : null;
  const pendingInvitesCount = invitationsData
    ? invitations.filter((i) => i.status === "PENDING").length
    : null;

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
            className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-accent text-text-inverse hover:bg-accent-hover transition-colors"
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
            <div className="p-2 rounded-lg bg-accent/15 text-accent">
              <Users className="w-5 h-5" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Total Members</p>
              <p className="text-xl font-semibold text-text-primary">
                {membersCount ?? "—"}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-surface-elevated rounded-lg border border-border p-5">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-status-info/15 text-status-info">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Admins</p>
              <p className="text-xl font-semibold text-text-primary">
                {adminsCount ?? "—"}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-surface-elevated rounded-lg border border-border p-5">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-status-warning/15 text-status-warning">
              <Clock className="w-5 h-5" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Pending Invites</p>
              <p className="text-xl font-semibold text-text-primary">
                {pendingInvitesCount ?? "—"}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Search */}
      <SearchInput
        value={searchQuery}
        onChange={setSearchQuery}
        placeholder="Search members..."
        className="max-w-md"
      />

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
