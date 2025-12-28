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
import { Button, Modal, Input, Select } from "@/lib/dotmac/core";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import { cn } from "@/lib/utils";

// Partner-specific role types
type PartnerMemberRole = "partner_owner" | "partner_admin" | "account_manager" | "finance";

interface PartnerTeamMember {
  id: string;
  partnerId: string;
  userId?: string | null;
  firstName: string;
  lastName: string;
  fullName: string;
  email: string;
  phone?: string | null;
  role: PartnerMemberRole;
  isPrimaryContact: boolean;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

interface PartnerInvitation {
  id: string;
  partnerId: string;
  email: string;
  role: PartnerMemberRole;
  status: "pending" | "accepted" | "expired" | "revoked";
  invitedBy: string;
  expiresAt: string;
  createdAt: string;
}

const roleLabels: Record<PartnerMemberRole, string> = {
  partner_owner: "Owner",
  partner_admin: "Admin",
  account_manager: "Account Manager",
  finance: "Finance",
};

const roleColors: Record<PartnerMemberRole, string> = {
  partner_owner: "bg-brand-primary/15 text-brand-primary",
  partner_admin: "bg-status-info/15 text-status-info",
  account_manager: "bg-status-success/15 text-status-success",
  finance: "bg-surface-overlay text-text-muted",
};

const partnerRoleOptions: { value: PartnerMemberRole; label: string }[] = [
  { value: "partner_owner", label: roleLabels.partner_owner },
  { value: "partner_admin", label: roleLabels.partner_admin },
  { value: "account_manager", label: roleLabels.account_manager },
  { value: "finance", label: roleLabels.finance },
];

function MemberCard({
  member,
  onRoleChange,
  onRemove,
}: {
  member: PartnerTeamMember;
  onRoleChange: (id: string, role: PartnerMemberRole) => void;
  onRemove: (id: string) => void;
}) {
  const [showMenu, setShowMenu] = useState(false);
  const [showRoleMenu, setShowRoleMenu] = useState(false);

  return (
    <div className="bg-surface-elevated rounded-lg border border-border p-5 hover:border-border-hover transition-colors">
      <div className="flex items-start gap-4">
        <Avatar name={member.fullName || `${member.firstName} ${member.lastName}`} size="lg" />

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-semibold text-text-primary truncate">
              {member.firstName} {member.lastName}
            </h3>
            <span className={cn("text-xs px-2 py-0.5 rounded-full font-medium", roleColors[member.role])}>
              {roleLabels[member.role]}
            </span>
            {member.isPrimaryContact && (
              <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-status-warning/15 text-status-warning">
                Primary
              </span>
            )}
          </div>
          <p className="text-sm text-text-muted truncate">{member.email}</p>
          {member.phone && (
            <p className="text-xs text-text-muted mt-1">{member.phone}</p>
          )}
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
                {(["partner_owner", "partner_admin", "account_manager", "finance"] as PartnerMemberRole[]).map(
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
                      <span>{roleLabels[role]}</span>
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
  invitation: PartnerInvitation;
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
            Invited as {roleLabels[invitation.role]}
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

function InviteTeamMemberModal({
  isOpen,
  onClose,
  onSuccess,
}: {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<PartnerMemberRole>("account_manager");
  const [error, setError] = useState<string | null>(null);

  const queryClient = useQueryClient();

  const inviteMutation = useMutation({
    mutationFn: async (data: { email: string; role: string }) => {
      return api.post("/api/v1/partners/portal/invitations", data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["partner-invitations"] });
      setEmail("");
      setRole("account_manager");
      setError(null);
      onSuccess();
    },
    onError: (err: unknown) => {
      const errorMessage = err instanceof Error ? err.message : "Failed to send invitation";
      setError(errorMessage);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return;
    inviteMutation.mutate({ email: email.trim(), role });
  };

  const handleClose = () => {
    setEmail("");
    setRole("account_manager");
    setError(null);
    onClose();
  };

  return (
    <Modal
      open={isOpen}
      onOpenChange={(open) => {
        if (!open) {
          handleClose();
        }
      }}
      title="Invite Team Member"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="p-3 rounded-md bg-status-error/10 text-status-error text-sm">
            {error}
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-text-secondary mb-1">
            Email Address
          </label>
          <Input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="colleague@example.com"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-text-secondary mb-1">
            Role
          </label>
          <Select
            value={role}
            onValueChange={(v) => setRole(v as PartnerMemberRole)}
            options={partnerRoleOptions}
            placeholder="Select role"
            className="w-full"
          />
        </div>

        <div className="flex justify-end gap-3 pt-4 border-t border-border">
          <Button type="button" variant="outline" onClick={handleClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={inviteMutation.isPending}>
            <Mail className="w-4 h-4 mr-2" />
            {inviteMutation.isPending ? "Sending..." : "Send Invitation"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}

export default function PartnerTeamPage() {
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();
  const [isInviteOpen, setIsInviteOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  // Fetch team members via portal endpoint
  const { data: membersData, isLoading: membersLoading, error: membersError } = useQuery({
    queryKey: ["partner-team-members"],
    queryFn: async () => {
      return api.get<{ users: PartnerTeamMember[] }>("/api/v1/partners/portal/users");
    },
  });

  // Fetch invitations via portal endpoint
  const { data: invitationsData, error: invitationsError } = useQuery({
    queryKey: ["partner-invitations"],
    queryFn: async () => {
      return api.get<{ invitations: PartnerInvitation[] }>("/api/v1/partners/portal/invitations");
    },
  });

  // Update role mutation
  const updateRoleMutation = useMutation({
    mutationFn: async ({ id, role }: { id: string; role: PartnerMemberRole }) => {
      return api.patch(`/api/v1/partners/portal/users/${id}`, { role });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["partner-team-members"] });
    },
  });

  // Remove member mutation
  const removeMemberMutation = useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/api/v1/partners/portal/users/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["partner-team-members"] });
    },
  });

  // Cancel invitation mutation
  const cancelInvitationMutation = useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/api/v1/partners/portal/invitations/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["partner-invitations"] });
    },
  });

  // Resend invitation mutation
  const resendInvitationMutation = useMutation({
    mutationFn: async (id: string) => {
      return api.post(`/api/v1/partners/portal/invitations/${id}/resend`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["partner-invitations"] });
    },
  });

  useEffect(() => {
    if (searchParams.get("action") === "invite") {
      setIsInviteOpen(true);
    }
  }, [searchParams]);

  const members = membersData?.users ?? [];
  const invitations = invitationsData?.invitations ?? [];
  const pendingInvitations = invitations.filter((i) => i.status === "pending");
  const errorMessage =
    membersError || invitationsError
      ? membersError instanceof Error
        ? membersError.message
        : invitationsError instanceof Error
          ? invitationsError.message
          : "Failed to load team data."
      : null;

  const filteredMembers = searchQuery
    ? members.filter(
        (m) =>
          `${m.firstName} ${m.lastName}`.toLowerCase().includes(searchQuery.toLowerCase()) ||
          m.email.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : members;

  const handleRoleChange = async (id: string, role: PartnerMemberRole) => {
    try {
      await updateRoleMutation.mutateAsync({ id, role });
    } catch (error) {
      console.error("Failed to update role:", error);
    }
  };

  const handleRemoveMember = async (id: string) => {
    if (!confirm("Are you sure you want to remove this team member?")) return;
    try {
      await removeMemberMutation.mutateAsync(id);
    } catch (error) {
      console.error("Failed to remove member:", error);
    }
  };

  const handleCancelInvitation = async (id: string) => {
    if (!confirm("Are you sure you want to cancel this invitation?")) return;
    try {
      await cancelInvitationMutation.mutateAsync(id);
    } catch (error) {
      console.error("Failed to cancel invitation:", error);
    }
  };

  const handleResendInvitation = async (id: string) => {
    try {
      await resendInvitationMutation.mutateAsync(id);
    } catch (error) {
      console.error("Failed to resend invitation:", error);
    }
  };

  return (
    <div className="space-y-8">
      <PageHeader
        title="Team"
        description="Manage your partner team members"
        actions={
          <Button onClick={() => setIsInviteOpen(true)}>
            <Plus className="w-4 h-4 mr-2" />
            Invite Member
          </Button>
        }
      />

      {errorMessage && (
        <div className="p-3 rounded-md bg-status-error/10 text-status-error text-sm">
          {errorMessage}
        </div>
      )}

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-3">
        <div className="stat-card">
          <Users className="w-5 h-5 text-text-muted" />
          <div>
            <p className="text-sm text-text-muted">Total Members</p>
            <p className="text-2xl font-semibold text-text-primary">
              {membersLoading ? "..." : members.length}
            </p>
          </div>
        </div>
        <div className="stat-card">
          <Shield className="w-5 h-5 text-text-muted" />
          <div>
            <p className="text-sm text-text-muted">Admins</p>
            <p className="text-2xl font-semibold text-text-primary">
              {membersLoading
                ? "..."
                : members.filter((m) => m.role === "partner_owner" || m.role === "partner_admin").length}
            </p>
          </div>
        </div>
        <div className="stat-card">
          <Clock className="w-5 h-5 text-text-muted" />
          <div>
            <p className="text-sm text-text-muted">Pending Invites</p>
            <p className="text-2xl font-semibold text-text-primary">
              {pendingInvitations.length}
            </p>
          </div>
        </div>
      </div>

      {/* Search */}
      <SearchInput
        value={searchQuery}
        onChange={setSearchQuery}
        placeholder="Search team members..."
      />

      {/* Pending Invitations */}
      {pendingInvitations.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold text-text-primary mb-4">
            Pending Invitations ({pendingInvitations.length})
          </h2>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {pendingInvitations.map((invitation) => (
              <InvitationCard
                key={invitation.id}
                invitation={invitation}
                onCancel={handleCancelInvitation}
                onResend={handleResendInvitation}
              />
            ))}
          </div>
        </section>
      )}

      {/* Team Members */}
      <section>
        <h2 className="text-lg font-semibold text-text-primary mb-4">
          Team Members ({members.length})
        </h2>

        {membersLoading ? (
          <TeamSkeleton />
        ) : filteredMembers.length === 0 ? (
          <EmptyState
            icon={Users}
            title={searchQuery ? "No members found" : "No team members yet"}
            description={
              searchQuery
                ? "Try adjusting your search"
                : "Invite team members to collaborate"
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
      </section>

      {/* Invite Modal */}
      <InviteTeamMemberModal
        isOpen={isInviteOpen}
        onClose={() => setIsInviteOpen(false)}
        onSuccess={() => setIsInviteOpen(false)}
      />
    </div>
  );
}
