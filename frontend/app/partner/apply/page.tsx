"use client";

import { useState } from "react";
import Link from "next/link";
import { Building2, Mail, Phone, Globe, FileText, CheckCircle } from "lucide-react";
import { Button, Input } from "@/lib/dotmac/core";
import { api } from "@/lib/api/client";

interface ApplicationForm {
  companyName: string;
  contactName: string;
  contactEmail: string;
  phone: string;
  website: string;
  businessDescription: string;
  expectedReferralsMonthly: string;
}

export default function PartnerApplyPage() {
  const [form, setForm] = useState<ApplicationForm>({
    companyName: "",
    contactName: "",
    contactEmail: "",
    phone: "",
    website: "",
    businessDescription: "",
    expectedReferralsMonthly: "",
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await api.post("/api/v1/partners/apply", {
        company_name: form.companyName,
        contact_name: form.contactName,
        contact_email: form.contactEmail,
        phone: form.phone || null,
        website: form.website || null,
        business_description: form.businessDescription || null,
        expected_referrals_monthly: form.expectedReferralsMonthly
          ? parseInt(form.expectedReferralsMonthly, 10)
          : null,
      });
      setIsSubmitted(true);
    } catch (err: unknown) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to submit application";
      setError(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isSubmitted) {
    return (
      <div className="min-h-screen bg-surface flex items-center justify-center p-4">
        <div className="max-w-md w-full text-center">
          <div className="card p-8">
            <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-status-success/10 flex items-center justify-center">
              <CheckCircle className="w-8 h-8 text-status-success" />
            </div>
            <h1 className="text-2xl font-semibold text-text-primary mb-2">
              Application Submitted
            </h1>
            <p className="text-text-muted mb-6">
              Thank you for your interest in our partner program. We will review
              your application and get back to you within 2-3 business days.
            </p>
            <Link href="/partner/login">
              <Button variant="outline">Go to Partner Login</Button>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-surface py-12 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-text-primary mb-2">
            Partner Program Application
          </h1>
          <p className="text-text-muted">
            Join our partner program and grow your business with us
          </p>
        </div>

        {/* Form */}
        <div className="card">
          <form onSubmit={handleSubmit} className="p-6 space-y-6">
            {error && (
              <div className="p-3 rounded-md bg-status-error/10 text-status-error text-sm">
                {error}
              </div>
            )}

            {/* Company Information */}
            <div>
              <h2 className="text-lg font-medium text-text-primary mb-4 flex items-center gap-2">
                <Building2 className="w-5 h-5" />
                Company Information
              </h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">
                    Company Name *
                  </label>
                  <Input
                    type="text"
                    name="companyName"
                    value={form.companyName}
                    onChange={handleChange}
                    placeholder="Your company name"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">
                    Website
                  </label>
                  <div className="relative">
                    <Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                    <Input
                      type="url"
                      name="website"
                      value={form.website}
                      onChange={handleChange}
                      placeholder="https://example.com"
                      className="pl-10"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Contact Information */}
            <div>
              <h2 className="text-lg font-medium text-text-primary mb-4 flex items-center gap-2">
                <Mail className="w-5 h-5" />
                Contact Information
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">
                    Contact Name *
                  </label>
                  <Input
                    type="text"
                    name="contactName"
                    value={form.contactName}
                    onChange={handleChange}
                    placeholder="John Doe"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">
                    Email Address *
                  </label>
                  <Input
                    type="email"
                    name="contactEmail"
                    value={form.contactEmail}
                    onChange={handleChange}
                    placeholder="john@example.com"
                    required
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-text-secondary mb-1">
                    Phone Number
                  </label>
                  <div className="relative">
                    <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                    <Input
                      type="tel"
                      name="phone"
                      value={form.phone}
                      onChange={handleChange}
                      placeholder="+1 (555) 123-4567"
                      className="pl-10"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Business Details */}
            <div>
              <h2 className="text-lg font-medium text-text-primary mb-4 flex items-center gap-2">
                <FileText className="w-5 h-5" />
                Business Details
              </h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">
                    Tell us about your business
                  </label>
                  <textarea
                    name="businessDescription"
                    value={form.businessDescription}
                    onChange={handleChange}
                    rows={4}
                    className="w-full px-3 py-2 bg-surface border border-border rounded-md text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-brand-primary/50"
                    placeholder="Describe your business and how you plan to work with us..."
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">
                    Expected monthly referrals
                  </label>
                  <Input
                    type="number"
                    name="expectedReferralsMonthly"
                    value={form.expectedReferralsMonthly}
                    onChange={handleChange}
                    placeholder="e.g., 10"
                    min="0"
                  />
                </div>
              </div>
            </div>

            {/* Submit */}
            <div className="pt-4 border-t border-border">
              <Button
                type="submit"
                className="w-full"
                disabled={isSubmitting}
              >
                {isSubmitting ? "Submitting..." : "Submit Application"}
              </Button>
              <p className="text-xs text-text-muted text-center mt-4">
                By submitting this application, you agree to our{" "}
                <Link href="/terms" className="text-brand-primary hover:underline">
                  Terms of Service
                </Link>{" "}
                and{" "}
                <Link href="/privacy" className="text-brand-primary hover:underline">
                  Privacy Policy
                </Link>
                .
              </p>
            </div>
          </form>
        </div>

        {/* Already a partner? */}
        <div className="text-center mt-6">
          <p className="text-text-muted">
            Already a partner?{" "}
            <Link href="/partner/login" className="text-brand-primary hover:underline">
              Sign in to your account
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
