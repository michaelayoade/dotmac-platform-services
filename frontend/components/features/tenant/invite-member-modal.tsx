"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { X, Loader2, Mail } from "lucide-react";

import { cn } from "@/lib/utils";
import { useInviteMember } from "@/lib/hooks/api/use-tenant-portal";
import type { MemberRole } from "@/types/tenant-portal";

const inviteSchema = z.object({
  email: z.string().email("Valid email is required"),
  role: z.enum(["tenant_admin", "member", "viewer"]),
  sendEmail: z.boolean(),
});

type InviteFormData = z.infer<typeof inviteSchema>;

interface InviteMemberModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

const roleDescriptions: Record<MemberRole, string> = {
  tenant_admin: "Full access to all settings and team management",
  member: "Can access most features but cannot manage team",
  viewer: "Read-only access to dashboards and reports",
};

export function InviteMemberModal({
  isOpen,
  onClose,
  onSuccess,
}: InviteMemberModalProps) {
  const inviteMember = useInviteMember();

  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<InviteFormData>({
    resolver: zodResolver(inviteSchema),
    defaultValues: {
      email: "",
      role: "member",
      sendEmail: true,
    },
  });

  const selectedRole = watch("role");

  const onSubmit = async (data: InviteFormData) => {
    try {
      await inviteMember.mutateAsync(data);
      reset();
      onSuccess?.();
      onClose();
    } catch (error) {
      console.error("Failed to invite member:", error);
    }
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-overlay/50 backdrop-blur-sm"
        onClick={handleClose}
      />

      {/* Modal */}
      <div className="relative w-full max-w-md mx-4 bg-surface-elevated rounded-xl border border-border shadow-xl animate-scale-in">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border">
          <div>
            <h2 className="text-lg font-semibold text-text-primary">
              Invite Team Member
            </h2>
            <p className="text-sm text-text-muted mt-1">
              Send an invitation to join your organization
            </p>
          </div>
          <button
            onClick={handleClose}
            className="p-2 rounded-md text-text-muted hover:text-text-secondary hover:bg-surface-overlay transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-5">
          {/* Email */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-text-secondary">
              Email Address <span className="text-status-error">*</span>
            </label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
              <input
                {...register("email")}
                type="email"
                placeholder="colleague@company.com"
                className={cn(
                  "w-full pl-10 pr-3 py-2 rounded-md border bg-surface text-text-primary placeholder:text-text-muted",
                  "focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent",
                  errors.email ? "border-status-error" : "border-border"
                )}
              />
            </div>
            {errors.email && (
              <p className="text-xs text-status-error">{errors.email.message}</p>
            )}
          </div>

          {/* Role */}
          <div className="space-y-3">
            <label className="text-sm font-medium text-text-secondary">
              Role <span className="text-status-error">*</span>
            </label>
            <div className="space-y-2">
              {(["tenant_admin", "member", "viewer"] as MemberRole[]).map((role) => (
                <label
                  key={role}
                  className={cn(
                    "flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors",
                    selectedRole === role
                      ? "border-accent bg-accent/5"
                      : "border-border hover:border-border-hover"
                  )}
                >
                  <input
                    {...register("role")}
                    type="radio"
                    value={role}
                    className="mt-0.5 w-4 h-4 text-accent focus:ring-accent"
                  />
                  <div>
                    <p className="text-sm font-medium text-text-primary capitalize">
                      {role.replace("_", " ")}
                    </p>
                    <p className="text-xs text-text-muted">
                      {roleDescriptions[role]}
                    </p>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Send Email Toggle */}
          <label className="flex items-center justify-between p-3 rounded-lg bg-surface-overlay">
            <div>
              <p className="text-sm font-medium text-text-primary">
                Send invitation email
              </p>
              <p className="text-xs text-text-muted">
                Notify them immediately via email
              </p>
            </div>
            <input
              {...register("sendEmail")}
              type="checkbox"
              className="w-4 h-4 text-accent rounded focus:ring-accent"
            />
          </label>

          {/* Error Message */}
          {inviteMember.isError && (
            <div className="p-3 rounded-lg bg-status-error/15 border border-status-error/20 text-status-error text-sm">
              Failed to send invitation. Please try again.
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={handleClose}
              className="px-4 py-2 rounded-md text-text-secondary hover:text-text-primary hover:bg-surface-overlay transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || inviteMember.isPending}
              className="px-4 py-2 rounded-md bg-accent text-text-inverse hover:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors inline-flex items-center gap-2"
            >
              {(isSubmitting || inviteMember.isPending) && (
                <Loader2 className="w-4 h-4 animate-spin" />
              )}
              Send Invitation
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
