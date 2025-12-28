"use client";

import { useState } from "react";
import { X, Mail, UserPlus } from "lucide-react";
import { Button, Input, Select, Modal } from "@/lib/dotmac/core";
import { useAddPartnerUser } from "@/lib/hooks/api/use-partners";

interface InvitePartnerUserModalProps {
  partnerId: string;
  isOpen: boolean;
  onClose: () => void;
}

const PARTNER_ROLES = [
  { value: "partner_owner", label: "Partner Owner" },
  { value: "partner_admin", label: "Partner Admin" },
  { value: "account_manager", label: "Account Manager" },
  { value: "finance", label: "Finance" },
];

export function InvitePartnerUserModal({
  partnerId,
  isOpen,
  onClose,
}: InvitePartnerUserModalProps) {
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("account_manager");
  const [phone, setPhone] = useState("");
  const [isPrimaryContact, setIsPrimaryContact] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const addUser = useAddPartnerUser();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!firstName.trim() || !lastName.trim() || !email.trim()) {
      setError("Please fill in all required fields");
      return;
    }

    try {
      await addUser.mutateAsync({
        partnerId,
        firstName: firstName.trim(),
        lastName: lastName.trim(),
        email: email.trim(),
        role,
        phone: phone.trim() || undefined,
        isPrimaryContact,
      });

      // Reset form and close
      resetForm();
      onClose();
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : "Failed to add user";
      setError(errorMessage);
    }
  };

  const resetForm = () => {
    setFirstName("");
    setLastName("");
    setEmail("");
    setRole("account_manager");
    setPhone("");
    setIsPrimaryContact(false);
    setError(null);
  };

  const handleClose = () => {
    resetForm();
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
      title="Add Partner User"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="p-3 rounded-md bg-status-error/10 text-status-error text-sm">
            {error}
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1">
              First Name *
            </label>
            <Input
              type="text"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              placeholder="John"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1">
              Last Name *
            </label>
            <Input
              type="text"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              placeholder="Doe"
              required
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-text-secondary mb-1">
            Email Address *
          </label>
          <Input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="john@example.com"
            required
          />
        </div>

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
            Phone (Optional)
          </label>
          <Input
            type="tel"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="+1 (555) 123-4567"
          />
        </div>

        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="isPrimaryContact"
            checked={isPrimaryContact}
            onChange={(e) => setIsPrimaryContact(e.target.checked)}
            className="rounded border-border text-brand-primary focus:ring-brand-primary"
          />
          <label htmlFor="isPrimaryContact" className="text-sm text-text-secondary">
            Set as primary contact
          </label>
        </div>

        <div className="flex justify-end gap-3 pt-4 border-t border-border">
          <Button type="button" variant="outline" onClick={handleClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={addUser.isPending}>
            <UserPlus className="w-4 h-4 mr-2" />
            {addUser.isPending ? "Adding..." : "Add User"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
