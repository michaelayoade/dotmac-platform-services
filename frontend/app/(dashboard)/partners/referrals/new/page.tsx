"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  Users,
  Building2,
  Mail,
  Phone,
  DollarSign,
  FileText,
  Check,
  RefreshCw,
} from "lucide-react";
import { Button, useToast } from "@/lib/dotmac/core";
import { useCreateReferral } from "@/lib/hooks/api/use-partner-portal";
import type { CreateReferralRequest } from "@/types/partner-portal";

export default function NewReferralPage() {
  const router = useRouter();
  const { toast } = useToast();
  const createReferral = useCreateReferral();

  const [formData, setFormData] = useState<CreateReferralRequest>({
    companyName: "",
    contactName: "",
    contactEmail: "",
    contactPhone: "",
    notes: "",
    estimatedValue: undefined,
  });

  const [errors, setErrors] = useState<Partial<Record<keyof CreateReferralRequest, string>>>({});

  const validateForm = (): boolean => {
    const newErrors: Partial<Record<keyof CreateReferralRequest, string>> = {};

    if (!formData.companyName.trim()) {
      newErrors.companyName = "Company name is required";
    }
    if (!formData.contactName.trim()) {
      newErrors.contactName = "Contact name is required";
    }
    if (!formData.contactEmail.trim()) {
      newErrors.contactEmail = "Email is required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.contactEmail)) {
      newErrors.contactEmail = "Please enter a valid email address";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleInputChange = (field: keyof CreateReferralRequest, value: string | number | undefined) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) return;

    try {
      await createReferral.mutateAsync({
        ...formData,
        estimatedValue: formData.estimatedValue ? Number(formData.estimatedValue) : undefined,
      });

      toast({
        title: "Referral created",
        description: "Your referral has been submitted successfully.",
        variant: "success",
      });

      router.push("/partners");
    } catch {
      toast({
        title: "Error",
        description: "Failed to create referral. Please try again.",
        variant: "error",
      });
    }
  };

  return (
    <div className="max-w-2xl space-y-6">
      {/* Back link */}
      <Link
        href="/partners"
        className="inline-flex items-center gap-2 text-sm text-text-muted hover:text-text-secondary transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Partner Portal
      </Link>

      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-semibold text-text-primary">
          Create New Referral
        </h1>
        <p className="text-text-muted mt-1">
          Submit a new tenant referral to earn commissions
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Company Information */}
        <div className="card p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
              <Building2 className="w-5 h-5 text-accent" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-text-primary">
                Company Information
              </h2>
              <p className="text-xs text-text-muted">
                Details about the referred company
              </p>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-2">
                Company Name <span className="text-status-error">*</span>
              </label>
              <input
                type="text"
                value={formData.companyName}
                onChange={(e) => handleInputChange("companyName", e.target.value)}
                placeholder="Acme Corporation"
                className={`w-full px-3 py-2 bg-surface-overlay border rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent ${
                  errors.companyName ? "border-status-error" : "border-border"
                }`}
              />
              {errors.companyName && (
                <p className="text-xs text-status-error mt-1">{errors.companyName}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-text-secondary mb-2">
                Estimated Deal Value
              </label>
              <div className="relative">
                <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                <input
                  type="number"
                  value={formData.estimatedValue || ""}
                  onChange={(e) =>
                    handleInputChange(
                      "estimatedValue",
                      e.target.value ? Number(e.target.value) : undefined
                    )
                  }
                  placeholder="10000"
                  className="w-full pl-10 pr-3 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent"
                />
              </div>
              <p className="text-xs text-text-muted mt-1">
                Optional - helps prioritize follow-up
              </p>
            </div>
          </div>
        </div>

        {/* Contact Information */}
        <div className="card p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
              <Users className="w-5 h-5 text-accent" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-text-primary">
                Contact Information
              </h2>
              <p className="text-xs text-text-muted">
                Primary contact at the referred company
              </p>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-2">
                Contact Name <span className="text-status-error">*</span>
              </label>
              <input
                type="text"
                value={formData.contactName}
                onChange={(e) => handleInputChange("contactName", e.target.value)}
                placeholder="John Smith"
                className={`w-full px-3 py-2 bg-surface-overlay border rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent ${
                  errors.contactName ? "border-status-error" : "border-border"
                }`}
              />
              {errors.contactName && (
                <p className="text-xs text-status-error mt-1">{errors.contactName}</p>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Email <span className="text-status-error">*</span>
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                  <input
                    type="email"
                    value={formData.contactEmail}
                    onChange={(e) => handleInputChange("contactEmail", e.target.value)}
                    placeholder="john@acme.com"
                    className={`w-full pl-10 pr-3 py-2 bg-surface-overlay border rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent ${
                      errors.contactEmail ? "border-status-error" : "border-border"
                    }`}
                  />
                </div>
                {errors.contactEmail && (
                  <p className="text-xs text-status-error mt-1">{errors.contactEmail}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Phone
                </label>
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                  <input
                    type="tel"
                    value={formData.contactPhone || ""}
                    onChange={(e) => handleInputChange("contactPhone", e.target.value)}
                    placeholder="+1 (555) 123-4567"
                    className="w-full pl-10 pr-3 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Additional Notes */}
        <div className="card p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
              <FileText className="w-5 h-5 text-accent" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-text-primary">
                Additional Information
              </h2>
              <p className="text-xs text-text-muted">
                Any context that may help with follow-up
              </p>
            </div>
          </div>

          <textarea
            value={formData.notes || ""}
            onChange={(e) => handleInputChange("notes", e.target.value)}
            rows={4}
            placeholder="Describe how you met this prospect, their specific needs, timeline, etc..."
            className="w-full px-3 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent resize-none"
          />
        </div>

        {/* Actions */}
        <div className="flex items-center justify-end gap-3">
          <Link href="/partners">
            <Button variant="outline">Cancel</Button>
          </Link>
          <Button
            type="submit"
            disabled={createReferral.isPending}
            className="shadow-glow-sm hover:shadow-glow"
          >
            {createReferral.isPending ? (
              <>
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                Creating...
              </>
            ) : (
              <>
                <Check className="w-4 h-4 mr-2" />
                Create Referral
              </>
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}
