"use client";

import { useState, useEffect } from "react";
import {
  X,
  Mail,
  UserPlus,
  RefreshCw,
  AlertCircle,
} from "lucide-react";
import { Button, useToast } from "@/lib/dotmac/core";
import { cn } from "@/lib/utils";
import { useInviteMember } from "@/lib/hooks/api/use-tenant-portal";
import type { MemberRole } from "@/types/tenant-portal";

interface InviteTeamModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const roleOptions: { value: MemberRole; label: string; description: string }[] = [
  {
    value: "tenant_admin",
    label: "Admin",
    description: "Full access to all settings and members",
  },
  {
    value: "member",
    label: "Member",
    description: "Can use features and view data",
  },
  {
    value: "viewer",
    label: "Viewer",
    description: "Read-only access to data",
  },
];

export function InviteTeamModal({ isOpen, onClose }: InviteTeamModalProps) {
  const { toast } = useToast();
  const inviteMember = useInviteMember();

  const [email, setEmail] = useState("");
  const [role, setRole] = useState<MemberRole>("member");
  const [error, setError] = useState<string | null>(null);

  // Reset form when modal opens
  useEffect(() => {
    if (isOpen) {
      setEmail("");
      setRole("member");
      setError(null);
    }
  }, [isOpen]);

  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [isOpen, onClose]);

  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!email.trim()) {
      setError("Email is required");
      return;
    }

    if (!validateEmail(email)) {
      setError("Please enter a valid email address");
      return;
    }

    try {
      await inviteMember.mutateAsync({
        email: email.trim(),
        role,
        sendEmail: true,
      });

      toast({
        title: "Invitation sent",
        description: `An invitation has been sent to ${email}`,
        variant: "success",
      });

      onClose();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to send invitation";
      setError(message);
      toast({
        title: "Error",
        description: message,
        variant: "error",
      });
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      role="dialog"
      aria-modal="true"
      aria-labelledby="invite-team-modal-title"
      aria-describedby="invite-team-modal-description"
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-overlay/60 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal */}
      <div className="relative w-full max-w-md mx-4 bg-surface border border-border rounded-xl shadow-2xl animate-fade-up">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
              <UserPlus className="w-5 h-5 text-accent" aria-hidden="true" />
            </div>
            <div>
              <h2 id="invite-team-modal-title" className="text-lg font-semibold text-text-primary">
                Invite Team Member
              </h2>
              <p id="invite-team-modal-description" className="text-xs text-text-muted">
                Send an invitation to join your team
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-surface-hover transition-colors"
            aria-label="Close modal"
          >
            <X className="w-5 h-5 text-text-muted" aria-hidden="true" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          {/* Email Input */}
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">
              Email Address
            </label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
              <input
                type="email"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  setError(null);
                }}
                placeholder="colleague@company.com"
                className={cn(
                  "w-full pl-10 pr-3 py-2 bg-surface-overlay border rounded-lg text-text-primary placeholder:text-text-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-inset",
                  error ? "border-status-error" : "border-border"
                )}
                autoFocus
              />
            </div>
            {error && (
              <div className="flex items-center gap-1.5 mt-1.5 text-xs text-status-error">
                <AlertCircle className="w-3 h-3" />
                {error}
              </div>
            )}
          </div>

          {/* Role Selection */}
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">
              Role
            </label>
            <div className="space-y-2">
              {roleOptions.map((option) => (
                <label
                  key={option.value}
                  className={cn(
                    "flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-all",
                    role === option.value
                      ? "border-accent bg-accent-subtle"
                      : "border-border hover:border-accent/50"
                  )}
                >
                  <input
                    type="radio"
                    name="role"
                    value={option.value}
                    checked={role === option.value}
                    onChange={(e) => setRole(e.target.value as MemberRole)}
                    className="mt-1 w-4 h-4 text-accent border-border focus:ring-accent"
                  />
                  <div>
                    <p className="text-sm font-medium text-text-primary">
                      {option.label}
                    </p>
                    <p className="text-xs text-text-muted">
                      {option.description}
                    </p>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 pt-2">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={inviteMember.isPending}
              className="shadow-glow-sm"
            >
              {inviteMember.isPending ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  Sending...
                </>
              ) : (
                <>
                  <Mail className="w-4 h-4 mr-2" />
                  Send Invitation
                </>
              )}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default InviteTeamModal;
