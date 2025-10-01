"use client";

import { useState } from "react";
import { usePartnerProfile, useUpdatePartnerProfile } from "@/hooks/usePartnerPortal";
import { Save, Building2, Mail, Phone, Globe, AlertCircle } from "lucide-react";

export default function PartnerSettingsPage() {
  const { data: profile, isLoading, error } = usePartnerProfile();
  const updateProfile = useUpdatePartnerProfile();
  const [formData, setFormData] = useState({
    company_name: "",
    legal_name: "",
    website: "",
    billing_email: "",
    phone: "",
  });
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Update form when profile loads
  useState(() => {
    if (profile) {
      setFormData({
        company_name: profile.company_name || "",
        legal_name: profile.legal_name || "",
        website: profile.website || "",
        billing_email: profile.billing_email || "",
        phone: profile.phone || "",
      });
    }
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setSaveSuccess(false);

    try {
      await updateProfile.mutateAsync(formData);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      console.error("Failed to update profile:", err);
      alert("Failed to update profile");
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="text-center py-12">
          <div className="text-slate-400">Loading settings...</div>
        </div>
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div className="p-6">
        <div className="text-center py-12">
          <div className="text-red-400">Failed to load profile</div>
          <div className="text-sm text-slate-500 mt-2">
            {error?.message || "Please try again"}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-white">Settings</h1>
        <p className="text-slate-400 mt-1">Manage your partner account settings</p>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Sidebar - Partner Info */}
        <div className="space-y-6">
          <div className="bg-slate-900 p-6 rounded-lg border border-slate-800">
            <h2 className="text-lg font-semibold text-white mb-4">
              Partner Information
            </h2>
            <div className="space-y-3 text-sm">
              <div>
                <div className="text-slate-400">Partner Number</div>
                <div className="text-white font-medium">
                  {profile.partner_number}
                </div>
              </div>
              <div>
                <div className="text-slate-400">Status</div>
                <div className="text-white font-medium capitalize">
                  {profile.status}
                </div>
              </div>
              <div>
                <div className="text-slate-400">Tier</div>
                <div className="text-white font-medium capitalize">
                  {profile.tier}
                </div>
              </div>
              <div>
                <div className="text-slate-400">Commission Model</div>
                <div className="text-white font-medium capitalize">
                  {profile.commission_model.replace("_", " ")}
                </div>
              </div>
              {profile.default_commission_rate && (
                <div>
                  <div className="text-slate-400">Default Commission Rate</div>
                  <div className="text-white font-medium">
                    {(profile.default_commission_rate * 100).toFixed(2)}%
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="bg-slate-900 p-6 rounded-lg border border-slate-800">
            <h2 className="text-lg font-semibold text-white mb-4">
              Account Dates
            </h2>
            <div className="space-y-3 text-sm">
              <div>
                <div className="text-slate-400">Created</div>
                <div className="text-white">
                  {new Date(profile.created_at).toLocaleDateString()}
                </div>
              </div>
              <div>
                <div className="text-slate-400">Last Updated</div>
                <div className="text-white">
                  {new Date(profile.updated_at).toLocaleDateString()}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content - Profile Form */}
        <div className="lg:col-span-2">
          {saveSuccess && (
            <div className="mb-4 p-4 bg-green-500/10 border border-green-500/20 rounded-lg flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-green-400" />
              <div className="text-sm text-green-400">
                Profile updated successfully!
              </div>
            </div>
          )}

          <div className="bg-slate-900 p-6 rounded-lg border border-slate-800">
            <h2 className="text-xl font-semibold text-white mb-6">
              Profile Information
            </h2>

            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Company Name <span className="text-red-400">*</span>
                </label>
                <div className="relative">
                  <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                  <input
                    type="text"
                    required
                    value={formData.company_name}
                    onChange={(e) =>
                      setFormData({ ...formData, company_name: e.target.value })
                    }
                    className="w-full pl-10 pr-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
                    placeholder="Your Company Inc."
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Legal Name
                </label>
                <div className="relative">
                  <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                  <input
                    type="text"
                    value={formData.legal_name}
                    onChange={(e) =>
                      setFormData({ ...formData, legal_name: e.target.value })
                    }
                    className="w-full pl-10 pr-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
                    placeholder="Your Company Legal Name LLC"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Website
                </label>
                <div className="relative">
                  <Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                  <input
                    type="url"
                    value={formData.website}
                    onChange={(e) =>
                      setFormData({ ...formData, website: e.target.value })
                    }
                    className="w-full pl-10 pr-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
                    placeholder="https://yourcompany.com"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Billing Email
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                  <input
                    type="email"
                    value={formData.billing_email}
                    onChange={(e) =>
                      setFormData({ ...formData, billing_email: e.target.value })
                    }
                    className="w-full pl-10 pr-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
                    placeholder="billing@yourcompany.com"
                  />
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  Commission payments and invoices will be sent to this email
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Phone Number
                </label>
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                  <input
                    type="tel"
                    value={formData.phone}
                    onChange={(e) =>
                      setFormData({ ...formData, phone: e.target.value })
                    }
                    className="w-full pl-10 pr-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
                    placeholder="+1 (555) 123-4567"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => {
                    if (profile) {
                      setFormData({
                        company_name: profile.company_name || "",
                        legal_name: profile.legal_name || "",
                        website: profile.website || "",
                        billing_email: profile.billing_email || "",
                        phone: profile.phone || "",
                      });
                    }
                  }}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition-colors"
                >
                  Reset
                </button>
                <button
                  type="submit"
                  disabled={isSaving}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors disabled:opacity-50 flex items-center gap-2"
                >
                  <Save className="w-4 h-4" />
                  {isSaving ? "Saving..." : "Save Changes"}
                </button>
              </div>
            </form>
          </div>

          {/* Read-Only Section */}
          <div className="bg-slate-900 p-6 rounded-lg border border-slate-800 mt-6">
            <h2 className="text-xl font-semibold text-white mb-4">
              Contact Information
            </h2>
            <div className="space-y-3 text-sm">
              <div>
                <div className="text-slate-400">Primary Email</div>
                <div className="text-white">{profile.primary_email}</div>
                <p className="text-xs text-slate-500 mt-1">
                  This is your login email and cannot be changed from the portal
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
