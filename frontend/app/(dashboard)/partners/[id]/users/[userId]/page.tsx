"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Save, KeyRound, UserX } from "lucide-react";
import { Button, Input, Select, useToast } from "@/lib/dotmac/core";
import {
  usePartner,
  usePartnerUser,
  useUpdatePartnerUser,
  useRemovePartnerUser,
} from "@/lib/hooks/api/use-partners";
import { resetPassword } from "@/lib/api/users";

const PARTNER_ROLES = [
  { value: "partner_owner", label: "Partner Owner" },
  { value: "partner_admin", label: "Partner Admin" },
  { value: "account_manager", label: "Account Manager" },
  { value: "finance", label: "Finance" },
];

export default function PartnerUserDetailPage() {
  const params = useParams<{ id: string; userId: string }>();
  const router = useRouter();
  const partnerId = params.id;
  const userId = params.userId;
  const { toast } = useToast();

  const { data: partner } = usePartner(partnerId);
  const { data: user, isLoading } = usePartnerUser(partnerId, userId);
  const updateUser = useUpdatePartnerUser();
  const removeUser = useRemovePartnerUser();

  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("");
  const [phone, setPhone] = useState("");
  const [isPrimaryContact, setIsPrimaryContact] = useState(false);
  const [isActive, setIsActive] = useState(true);
  const [isResetting, setIsResetting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (user) {
      setFirstName(user.firstName || "");
      setLastName(user.lastName || "");
      setEmail(user.email || "");
      setRole(user.role || "account_manager");
      setPhone(user.phone || "");
      setIsPrimaryContact(user.isPrimaryContact || false);
      setIsActive(user.isActive);
    }
  }, [user]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    try {
      await updateUser.mutateAsync({
        partnerId,
        userId,
        data: {
          firstName: firstName.trim(),
          lastName: lastName.trim(),
          email: email.trim(),
          role,
          phone: phone.trim() || undefined,
          isPrimaryContact,
          isActive,
        },
      });
      setSuccess("User updated successfully");
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : "Failed to update user";
      setError(errorMessage);
    }
  };

  const handleRemove = async () => {
    if (!confirm("Are you sure you want to remove this user? This action cannot be undone.")) {
      return;
    }

    try {
      await removeUser.mutateAsync({ partnerId, userId });
      router.push(`/partners/${partnerId}/users`);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : "Failed to remove user";
      setError(errorMessage);
    }
  };

  const handleResetPassword = async () => {
    if (!confirm("Send a password reset email to this user?")) {
      return;
    }
    setIsResetting(true);
    try {
      await resetPassword(userId);
      toast({ title: "Password reset email sent" });
    } catch {
      toast({ title: "Failed to send reset email", variant: "error" });
    } finally {
      setIsResetting(false);
    }
  };

  if (isLoading) {
    return <PageSkeleton />;
  }

  if (!user) {
    return (
      <div className="text-center py-12">
        <p className="text-text-muted">User not found</p>
        <Button
          variant="outline"
          className="mt-4"
          onClick={() => router.push(`/partners/${partnerId}/users`)}
        >
          Back to Users
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-3xl">
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
        <Link href={`/partners/${partnerId}/users`} className="hover:text-text-secondary">
          Users
        </Link>
        <span aria-hidden="true">/</span>
        <span className="text-text-primary">
          {user.firstName} {user.lastName}
        </span>
      </nav>

      {/* Page Header */}
      <div className="page-header">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => router.push(`/partners/${partnerId}/users`)}
          >
            <ArrowLeft className="w-4 h-4" />
          </Button>
          <div>
            <h1 className="page-title">
              {user.firstName} {user.lastName}
            </h1>
            <p className="page-description">{user.email}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" onClick={handleResetPassword} disabled={isResetting}>
            <KeyRound className="w-4 h-4 mr-2" />
            {isResetting ? "Sending..." : "Reset Password"}
          </Button>
          <Button variant="destructive" onClick={handleRemove}>
            <UserX className="w-4 h-4 mr-2" />
            Remove
          </Button>
        </div>
      </div>

      {/* Form */}
      <div className="card">
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {error && (
            <div className="p-3 rounded-md bg-status-error/10 text-status-error text-sm">
              {error}
            </div>
          )}
          {success && (
            <div className="p-3 rounded-md bg-status-success/10 text-status-success text-sm">
              {success}
            </div>
          )}

          <div className="grid grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-1">
                First Name
              </label>
              <Input
                type="text"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-1">
                Last Name
              </label>
              <Input
                type="text"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1">
              Email Address
            </label>
            <Input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-1">
                Role
              </label>
              <Select
                value={role}
                onValueChange={setRole}
                options={PARTNER_ROLES}
                placeholder="Select role"
                className="w-full"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-1">
                Phone
              </label>
              <Input
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+1 (555) 123-4567"
              />
            </div>
          </div>

          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="isPrimaryContact"
                checked={isPrimaryContact}
                onChange={(e) => setIsPrimaryContact(e.target.checked)}
                className="rounded border-border text-brand-primary focus:ring-brand-primary"
              />
              <label htmlFor="isPrimaryContact" className="text-sm text-text-secondary">
                Primary contact for this partner
              </label>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="isActive"
                checked={isActive}
                onChange={(e) => setIsActive(e.target.checked)}
                className="rounded border-border text-brand-primary focus:ring-brand-primary"
              />
              <label htmlFor="isActive" className="text-sm text-text-secondary">
                Account is active
              </label>
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-border">
            <Button
              type="button"
              variant="outline"
              onClick={() => router.push(`/partners/${partnerId}/users`)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={updateUser.isPending}>
              <Save className="w-4 h-4 mr-2" />
              {updateUser.isPending ? "Saving..." : "Save Changes"}
            </Button>
          </div>
        </form>
      </div>

      {/* Activity / Audit Log (placeholder) */}
      <div className="card">
        <div className="p-4 border-b border-border">
          <h2 className="font-medium text-text-primary">Activity Log</h2>
        </div>
        <div className="p-6 text-center text-text-muted">
          <p>Activity logging coming soon</p>
        </div>
      </div>
    </div>
  );
}

function PageSkeleton() {
  return (
    <div className="space-y-6 max-w-3xl">
      <div className="h-5 w-64 skeleton" />
      <div className="page-header">
        <div className="flex items-center gap-4">
          <div className="h-10 w-10 skeleton rounded" />
          <div className="space-y-2">
            <div className="h-8 w-48 skeleton" />
            <div className="h-4 w-32 skeleton" />
          </div>
        </div>
        <div className="flex gap-3">
          <div className="h-10 w-32 skeleton" />
          <div className="h-10 w-24 skeleton" />
        </div>
      </div>
      <div className="card p-6 space-y-6">
        <div className="grid grid-cols-2 gap-6">
          <div className="h-16 skeleton" />
          <div className="h-16 skeleton" />
        </div>
        <div className="h-16 skeleton" />
        <div className="grid grid-cols-2 gap-6">
          <div className="h-16 skeleton" />
          <div className="h-16 skeleton" />
        </div>
      </div>
    </div>
  );
}
