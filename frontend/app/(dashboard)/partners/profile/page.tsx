"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Building2,
  User,
  MapPin,
  CreditCard,
  Bell,
  Check,
  RefreshCw,
  Award,
} from "lucide-react";
import { Button, useToast } from "@/lib/dotmac/core";
import { cn } from "@/lib/utils";
import {
  usePartnerProfile,
  useUpdatePartnerProfile,
} from "@/lib/hooks/api/use-partner-portal";
import type { UpdatePartnerProfileRequest, PartnerProfile } from "@/types/partner-portal";

export default function PartnerProfilePage() {
  const { toast } = useToast();
  const { data: profile, isLoading } = usePartnerProfile();
  const updateProfile = useUpdatePartnerProfile();

  const [formData, setFormData] = useState<UpdatePartnerProfileRequest>({});
  const [isEditing, setIsEditing] = useState(false);

  useEffect(() => {
    if (profile) {
      setFormData({
        companyName: profile.companyName,
        contactName: profile.contactName,
        contactPhone: profile.contactPhone,
        address: profile.address,
        payoutPreferences: profile.payoutPreferences,
        notificationSettings: profile.notificationSettings,
      });
    }
  }, [profile]);

  const handleSave = async () => {
    try {
      await updateProfile.mutateAsync(formData);
      toast({
        title: "Profile updated",
        description: "Your profile has been saved successfully.",
        variant: "success",
      });
      setIsEditing(false);
    } catch {
      toast({
        title: "Error",
        description: "Failed to update profile. Please try again.",
        variant: "error",
      });
    }
  };

  const handleCancel = () => {
    if (profile) {
      setFormData({
        companyName: profile.companyName,
        contactName: profile.contactName,
        contactPhone: profile.contactPhone,
        address: profile.address,
        payoutPreferences: profile.payoutPreferences,
        notificationSettings: profile.notificationSettings,
      });
    }
    setIsEditing(false);
  };

  const updateField = (path: string, value: unknown) => {
    setFormData((prev) => {
      const keys = path.split(".");
      const newData = { ...prev };
      let current: Record<string, unknown> = newData;

      for (let i = 0; i < keys.length - 1; i++) {
        current[keys[i]] = { ...(current[keys[i]] as Record<string, unknown> || {}) };
        current = current[keys[i]] as Record<string, unknown>;
      }
      current[keys[keys.length - 1]] = value;

      return newData;
    });
  };

  const tierColors: Record<PartnerProfile["tier"], string> = {
    BRONZE: "bg-status-warning/15 text-status-warning",
    SILVER: "bg-surface-overlay text-text-secondary",
    GOLD: "bg-highlight/15 text-highlight",
    PLATINUM: "bg-status-info/15 text-status-info",
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent"></div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl space-y-6">
      {/* Back link */}
      <Link
        href="/partners"
        className="inline-flex items-center gap-2 text-sm text-text-muted hover:text-text-secondary transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Partner Portal
      </Link>

      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-text-primary">
            Partner Profile
          </h1>
          <p className="text-text-muted mt-1">
            Manage your partner account settings
          </p>
        </div>
        {!isEditing ? (
          <Button onClick={() => setIsEditing(true)}>Edit Profile</Button>
        ) : (
          <div className="flex items-center gap-3">
            <Button variant="outline" onClick={handleCancel}>
              Cancel
            </Button>
            <Button
              onClick={handleSave}
              disabled={updateProfile.isPending}
              className="shadow-glow-sm"
            >
              {updateProfile.isPending ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Check className="w-4 h-4 mr-2" />
                  Save Changes
                </>
              )}
            </Button>
          </div>
        )}
      </div>

      {/* Partner Status Card */}
      <div className="card p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-accent to-highlight flex items-center justify-center text-xl font-bold text-text-inverse">
              {profile?.companyName?.charAt(0) || "P"}
            </div>
            <div>
              <h2 className="text-lg font-semibold text-text-primary">
                {profile?.companyName}
              </h2>
              <p className="text-sm text-text-muted">
                Partner since{" "}
                {profile?.joinedAt
                  ? new Date(profile.joinedAt).toLocaleDateString("en-US", {
                      month: "long",
                      year: "numeric",
                    })
                  : "—"}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span
              className={cn(
                "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium",
                tierColors[profile?.tier || "BRONZE"]
              )}
            >
              <Award className="w-4 h-4" />
              {profile?.tier}
            </span>
            <div className="text-right">
              <p className="text-sm text-text-muted">Commission Rate</p>
              <p className="text-lg font-semibold text-accent">
                {profile?.commissionRate}%
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Company Information */}
      <div className="card p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
            <Building2 className="w-5 h-5 text-accent" />
          </div>
          <h2 className="text-sm font-semibold text-text-primary">
            Company Information
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">
              Company Name
            </label>
            {isEditing ? (
              <input
                type="text"
                value={formData.companyName || ""}
                onChange={(e) => updateField("companyName", e.target.value)}
                className="w-full px-3 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-accent"
              />
            ) : (
              <p className="text-text-primary">{profile?.companyName}</p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">
              Contact Email
            </label>
            <p className="text-text-muted">{profile?.contactEmail}</p>
            <p className="text-xs text-text-muted mt-1">
              Contact support to change email
            </p>
          </div>
        </div>
      </div>

      {/* Contact Information */}
      <div className="card p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
            <User className="w-5 h-5 text-accent" />
          </div>
          <h2 className="text-sm font-semibold text-text-primary">
            Contact Information
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">
              Contact Name
            </label>
            {isEditing ? (
              <input
                type="text"
                value={formData.contactName || ""}
                onChange={(e) => updateField("contactName", e.target.value)}
                className="w-full px-3 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-accent"
              />
            ) : (
              <p className="text-text-primary">{profile?.contactName}</p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">
              Phone
            </label>
            {isEditing ? (
              <input
                type="tel"
                value={formData.contactPhone || ""}
                onChange={(e) => updateField("contactPhone", e.target.value)}
                className="w-full px-3 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-accent"
              />
            ) : (
              <p className="text-text-primary">
                {profile?.contactPhone || "—"}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Address */}
      <div className="card p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
            <MapPin className="w-5 h-5 text-accent" />
          </div>
          <h2 className="text-sm font-semibold text-text-primary">
            Business Address
          </h2>
        </div>

        {isEditing ? (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-2">
                Street Address
              </label>
              <input
                type="text"
                value={formData.address?.street || ""}
                onChange={(e) => updateField("address.street", e.target.value)}
                className="w-full px-3 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-accent"
              />
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="col-span-2">
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  City
                </label>
                <input
                  type="text"
                  value={formData.address?.city || ""}
                  onChange={(e) => updateField("address.city", e.target.value)}
                  className="w-full px-3 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-accent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  State
                </label>
                <input
                  type="text"
                  value={formData.address?.state || ""}
                  onChange={(e) => updateField("address.state", e.target.value)}
                  className="w-full px-3 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-accent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Postal Code
                </label>
                <input
                  type="text"
                  value={formData.address?.postalCode || ""}
                  onChange={(e) =>
                    updateField("address.postalCode", e.target.value)
                  }
                  className="w-full px-3 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-accent"
                />
              </div>
            </div>
          </div>
        ) : (
          <p className="text-text-primary">
            {profile?.address ? (
              <>
                {profile.address.street}
                <br />
                {profile.address.city}, {profile.address.state}{" "}
                {profile.address.postalCode}
                <br />
                {profile.address.country}
              </>
            ) : (
              <span className="text-text-muted">No address on file</span>
            )}
          </p>
        )}
      </div>

      {/* Payout Preferences */}
      <div className="card p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
            <CreditCard className="w-5 h-5 text-accent" />
          </div>
          <h2 className="text-sm font-semibold text-text-primary">
            Payout Preferences
          </h2>
        </div>

        {isEditing ? (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-2">
                Payout Method
              </label>
              <select
                value={formData.payoutPreferences?.method || "BANK_TRANSFER"}
                onChange={(e) =>
                  updateField(
                    "payoutPreferences.method",
                    e.target.value as PartnerProfile["payoutPreferences"]["method"]
                  )
                }
                className="w-full px-3 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-accent"
              >
                <option value="BANK_TRANSFER">Bank Transfer (ACH)</option>
                <option value="CHECK">Check</option>
                <option value="PAYPAL">PayPal</option>
              </select>
            </div>

            {formData.payoutPreferences?.method === "PAYPAL" && (
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  PayPal Email
                </label>
                <input
                  type="email"
                  value={formData.payoutPreferences?.paypalEmail || ""}
                  onChange={(e) =>
                    updateField("payoutPreferences.paypalEmail", e.target.value)
                  }
                  className="w-full px-3 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-accent"
                />
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-2">
            <p className="text-text-primary">
              {profile?.payoutPreferences?.method === "BANK_TRANSFER"
                ? "Bank Transfer (ACH)"
                : profile?.payoutPreferences?.method === "CHECK"
                  ? "Check"
                  : "PayPal"}
            </p>
            {profile?.payoutPreferences?.method === "PAYPAL" &&
              profile?.payoutPreferences?.paypalEmail && (
                <p className="text-sm text-text-muted">
                  {profile.payoutPreferences.paypalEmail}
                </p>
              )}
          </div>
        )}
      </div>

      {/* Notification Settings */}
      <div className="card p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
            <Bell className="w-5 h-5 text-accent" />
          </div>
          <h2 className="text-sm font-semibold text-text-primary">
            Notification Settings
          </h2>
        </div>

        <div className="space-y-3">
          {[
            { key: "emailNewReferral", label: "New referral updates" },
            { key: "emailCommissionApproved", label: "Commission approvals" },
            { key: "emailPayoutProcessed", label: "Payout processed" },
            { key: "emailMonthlyStatement", label: "Monthly statements" },
          ].map((setting) => (
            <label
              key={setting.key}
              className={cn(
                "flex items-center justify-between p-3 rounded-lg border",
                isEditing
                  ? "border-border hover:bg-surface-hover cursor-pointer"
                  : "border-transparent"
              )}
            >
              <span className="text-sm text-text-primary">{setting.label}</span>
              {isEditing ? (
                <input
                  type="checkbox"
                  checked={
                    formData.notificationSettings?.[
                      setting.key as keyof typeof formData.notificationSettings
                    ] ?? false
                  }
                  onChange={(e) =>
                    updateField(
                      `notificationSettings.${setting.key}`,
                      e.target.checked
                    )
                  }
                  className="w-4 h-4 rounded border-border text-accent focus:ring-accent"
                />
              ) : (
                <span
                  className={cn(
                    "text-xs px-2 py-0.5 rounded",
                    profile?.notificationSettings?.[
                      setting.key as keyof PartnerProfile["notificationSettings"]
                    ]
                      ? "bg-status-success/15 text-status-success"
                      : "bg-surface-overlay text-text-muted"
                  )}
                >
                  {profile?.notificationSettings?.[
                    setting.key as keyof PartnerProfile["notificationSettings"]
                  ]
                    ? "Enabled"
                    : "Disabled"}
                </span>
              )}
            </label>
          ))}
        </div>
      </div>
    </div>
  );
}
