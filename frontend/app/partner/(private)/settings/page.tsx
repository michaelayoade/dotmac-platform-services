"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  Building2,
  User,
  CreditCard,
  Bell,
  Save,
  Loader2,
  Award,
} from "lucide-react";

import { PageHeader } from "@/components/shared";
import {
  usePartnerProfile,
  useUpdatePartnerProfile,
} from "@/lib/hooks/api/use-partner-portal";
import { cn } from "@/lib/utils";

const profileSchema = z.object({
  companyName: z.string().min(2, "Company name is required"),
  contactName: z.string().min(2, "Contact name is required"),
  contactPhone: z.string().optional(),
  street: z.string().optional(),
  city: z.string().optional(),
  state: z.string().optional(),
  postalCode: z.string().optional(),
  country: z.string().optional(),
});

type ProfileFormData = z.infer<typeof profileSchema>;

const payoutSchema = z.object({
  method: z.enum(["BANK_TRANSFER", "CHECK", "PAYPAL"]),
  bankAccountNumber: z.string().optional(),
  bankRoutingNumber: z.string().optional(),
  paypalEmail: z.string().email().optional(),
});

type PayoutFormData = z.infer<typeof payoutSchema>;

const notificationSchema = z.object({
  emailNewReferral: z.boolean(),
  emailCommissionApproved: z.boolean(),
  emailPayoutProcessed: z.boolean(),
  emailMonthlyStatement: z.boolean(),
});

type NotificationFormData = z.infer<typeof notificationSchema>;

// Demo data
const demoProfile = {
  id: "p1",
  companyName: "Partner Solutions Inc.",
  contactName: "John Partner",
  contactEmail: "john@partnersolutions.com",
  contactPhone: "+1 (555) 123-4567",
  address: {
    street: "123 Partner Street",
    city: "San Francisco",
    state: "CA",
    postalCode: "94102",
    country: "USA",
  },
  payoutPreferences: {
    method: "BANK_TRANSFER" as const,
    bankAccountNumber: "****4567",
    bankRoutingNumber: "****8901",
  },
  notificationSettings: {
    emailNewReferral: true,
    emailCommissionApproved: true,
    emailPayoutProcessed: true,
    emailMonthlyStatement: true,
  },
  commissionRate: 15,
  tier: "SILVER" as const,
  joinedAt: "2024-01-15T00:00:00Z",
};

const tierColors = {
  BRONZE: "text-amber-600 bg-amber-100",
  SILVER: "text-gray-600 bg-gray-100",
  GOLD: "text-yellow-600 bg-yellow-100",
  PLATINUM: "text-purple-600 bg-purple-100",
};

function ProfileSection() {
  const { data: profile } = usePartnerProfile();
  const updateProfile = useUpdatePartnerProfile();
  const [isEditing, setIsEditing] = useState(false);

  const currentProfile = profile || demoProfile;

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ProfileFormData>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      companyName: currentProfile.companyName,
      contactName: currentProfile.contactName,
      contactPhone: currentProfile.contactPhone || "",
      street: currentProfile.address?.street || "",
      city: currentProfile.address?.city || "",
      state: currentProfile.address?.state || "",
      postalCode: currentProfile.address?.postalCode || "",
      country: currentProfile.address?.country || "",
    },
  });

  const onSubmit = async (data: ProfileFormData) => {
    try {
      await updateProfile.mutateAsync({
        companyName: data.companyName,
        contactName: data.contactName,
        contactPhone: data.contactPhone,
        address: {
          street: data.street,
          city: data.city,
          state: data.state,
          postalCode: data.postalCode,
          country: data.country,
        },
      });
      setIsEditing(false);
    } catch (error) {
      console.error("Failed to update profile:", error);
    }
  };

  return (
    <div className="bg-surface-elevated rounded-lg border border-border">
      <div className="p-6 border-b border-border flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-accent/10 text-accent">
            <Building2 className="w-5 h-5" />
          </div>
          <div>
            <h2 className="font-semibold text-text-primary">Company Profile</h2>
            <p className="text-sm text-text-muted">Your partner organization details</p>
          </div>
        </div>
        {!isEditing && (
          <button
            onClick={() => setIsEditing(true)}
            className="px-4 py-2 rounded-md text-sm font-medium text-accent hover:bg-accent/10 transition-colors"
          >
            Edit
          </button>
        )}
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-4">
        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <label className="text-sm font-medium text-text-secondary">
              Company Name
            </label>
            <input
              {...register("companyName")}
              disabled={!isEditing}
              className={cn(
                "w-full px-3 py-2 rounded-md border bg-surface text-text-primary",
                "focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent",
                "disabled:bg-surface-overlay disabled:cursor-not-allowed",
                errors.companyName ? "border-status-error" : "border-border"
              )}
            />
            {errors.companyName && (
              <p className="text-xs text-status-error">{errors.companyName.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-text-secondary">
              Contact Name
            </label>
            <input
              {...register("contactName")}
              disabled={!isEditing}
              className={cn(
                "w-full px-3 py-2 rounded-md border bg-surface text-text-primary",
                "focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent",
                "disabled:bg-surface-overlay disabled:cursor-not-allowed",
                errors.contactName ? "border-status-error" : "border-border"
              )}
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-text-secondary">
              Email
            </label>
            <input
              value={currentProfile.contactEmail}
              disabled
              className="w-full px-3 py-2 rounded-md border border-border bg-surface-overlay text-text-muted cursor-not-allowed"
            />
            <p className="text-xs text-text-muted">Contact support to change email</p>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-text-secondary">
              Phone
            </label>
            <input
              {...register("contactPhone")}
              disabled={!isEditing}
              className="w-full px-3 py-2 rounded-md border border-border bg-surface text-text-primary focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent disabled:bg-surface-overlay disabled:cursor-not-allowed"
            />
          </div>
        </div>

        <div className="pt-4 border-t border-border">
          <h3 className="text-sm font-semibold text-text-primary mb-4">Address</h3>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="md:col-span-2 space-y-2">
              <label className="text-sm font-medium text-text-secondary">Street</label>
              <input
                {...register("street")}
                disabled={!isEditing}
                className="w-full px-3 py-2 rounded-md border border-border bg-surface text-text-primary focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent disabled:bg-surface-overlay disabled:cursor-not-allowed"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-text-secondary">City</label>
              <input
                {...register("city")}
                disabled={!isEditing}
                className="w-full px-3 py-2 rounded-md border border-border bg-surface text-text-primary focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent disabled:bg-surface-overlay disabled:cursor-not-allowed"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-text-secondary">State</label>
              <input
                {...register("state")}
                disabled={!isEditing}
                className="w-full px-3 py-2 rounded-md border border-border bg-surface text-text-primary focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent disabled:bg-surface-overlay disabled:cursor-not-allowed"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-text-secondary">Postal Code</label>
              <input
                {...register("postalCode")}
                disabled={!isEditing}
                className="w-full px-3 py-2 rounded-md border border-border bg-surface text-text-primary focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent disabled:bg-surface-overlay disabled:cursor-not-allowed"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-text-secondary">Country</label>
              <input
                {...register("country")}
                disabled={!isEditing}
                className="w-full px-3 py-2 rounded-md border border-border bg-surface text-text-primary focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent disabled:bg-surface-overlay disabled:cursor-not-allowed"
              />
            </div>
          </div>
        </div>

        {isEditing && (
          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={() => setIsEditing(false)}
              className="px-4 py-2 rounded-md text-text-secondary hover:text-text-primary hover:bg-surface-overlay transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 rounded-md bg-accent text-white hover:bg-accent-hover disabled:opacity-50 inline-flex items-center gap-2"
            >
              {isSubmitting ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Save className="w-4 h-4" />
              )}
              Save Changes
            </button>
          </div>
        )}
      </form>
    </div>
  );
}

function PartnerTierSection() {
  const { data: profile } = usePartnerProfile();
  const currentProfile = profile || demoProfile;

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "long",
      day: "numeric",
      year: "numeric",
    });
  };

  return (
    <div className="bg-surface-elevated rounded-lg border border-border">
      <div className="p-6 border-b border-border flex items-center gap-3">
        <div className="p-2 rounded-lg bg-highlight/10 text-highlight">
          <Award className="w-5 h-5" />
        </div>
        <div>
          <h2 className="font-semibold text-text-primary">Partner Status</h2>
          <p className="text-sm text-text-muted">Your partnership tier and benefits</p>
        </div>
      </div>

      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <span
              className={cn(
                "inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-semibold",
                tierColors[currentProfile.tier]
              )}
            >
              <Award className="w-4 h-4" />
              {currentProfile.tier} Partner
            </span>
          </div>
          <div className="text-right">
            <p className="text-2xl font-semibold text-text-primary">
              {currentProfile.commissionRate}%
            </p>
            <p className="text-sm text-text-muted">Commission Rate</p>
          </div>
        </div>

        <div className="text-sm text-text-muted">
          Partner since {formatDate(currentProfile.joinedAt)}
        </div>
      </div>
    </div>
  );
}

function NotificationSection() {
  const { data: profile } = usePartnerProfile();
  const updateProfile = useUpdatePartnerProfile();
  const currentProfile = profile || demoProfile;

  const [settings, setSettings] = useState(currentProfile.notificationSettings);
  const [isSaving, setIsSaving] = useState(false);

  const handleToggle = async (key: keyof typeof settings) => {
    const newSettings = { ...settings, [key]: !settings[key] };
    setSettings(newSettings);
    setIsSaving(true);

    try {
      await updateProfile.mutateAsync({
        notificationSettings: newSettings,
      });
    } catch (error) {
      // Revert on error
      setSettings(settings);
    } finally {
      setIsSaving(false);
    }
  };

  const notificationOptions = [
    {
      key: "emailNewReferral" as const,
      label: "New Referral Updates",
      description: "Get notified when referral status changes",
    },
    {
      key: "emailCommissionApproved" as const,
      label: "Commission Approved",
      description: "Get notified when commissions are approved",
    },
    {
      key: "emailPayoutProcessed" as const,
      label: "Payout Processed",
      description: "Get notified when payouts are completed",
    },
    {
      key: "emailMonthlyStatement" as const,
      label: "Monthly Statement",
      description: "Receive monthly commission statements",
    },
  ];

  return (
    <div className="bg-surface-elevated rounded-lg border border-border">
      <div className="p-6 border-b border-border flex items-center gap-3">
        <div className="p-2 rounded-lg bg-status-success/10 text-status-success">
          <Bell className="w-5 h-5" />
        </div>
        <div>
          <h2 className="font-semibold text-text-primary">Notifications</h2>
          <p className="text-sm text-text-muted">Manage your email preferences</p>
        </div>
      </div>

      <div className="divide-y divide-border">
        {notificationOptions.map((option) => (
          <div
            key={option.key}
            className="p-6 flex items-center justify-between"
          >
            <div>
              <p className="font-medium text-text-primary">{option.label}</p>
              <p className="text-sm text-text-muted">{option.description}</p>
            </div>
            <button
              onClick={() => handleToggle(option.key)}
              disabled={isSaving}
              className={cn(
                "relative w-11 h-6 rounded-full transition-colors",
                settings[option.key] ? "bg-accent" : "bg-surface-overlay"
              )}
            >
              <span
                className={cn(
                  "absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform",
                  settings[option.key] && "translate-x-5"
                )}
              />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Settings"
        description="Manage your partner account settings"
      />

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          <ProfileSection />
          <NotificationSection />
        </div>
        <div>
          <PartnerTierSection />
        </div>
      </div>
    </div>
  );
}
