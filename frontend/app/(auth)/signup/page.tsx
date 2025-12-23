"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import { Zap } from "lucide-react";

import { SignupWizard, type SignupData } from "@/components/features/auth/signup-wizard";
import { createPublicTenantOnboarding } from "@/lib/api/signup";

export default function SignupPage() {
  const router = useRouter();

  const handleSignupComplete = async (data: SignupData) => {
    const localPart = data.account.email.split("@")[0] || "";
    const sanitizedLocalPart = localPart.replace(/[^a-zA-Z0-9._-]/g, "");
    const fallbackUsername = `${data.organization.companySlug}-admin`;
    const username =
      sanitizedLocalPart.length >= 3 ? sanitizedLocalPart : fallbackUsername;

    // Create the tenant and admin user
    await createPublicTenantOnboarding({
      tenant: {
        name: data.organization.companyName,
        slug: data.organization.companySlug,
        industry: data.organization.industry,
        companySize: data.organization.companySize,
        country: data.organization.country,
        planType: data.plan,
      },
      adminUser: {
        username,
        email: data.account.email,
        password: data.account.password,
        fullName: data.account.fullName,
      },
    });

    // Redirect to email verification page
    router.push(`/verify-email?email=${encodeURIComponent(data.account.email)}`);
  };

  return (
    <div className="min-h-screen flex">
      {/* Left side - Form */}
      <div className="flex-1 flex flex-col items-center justify-center p-8 overflow-auto">
        <div className="w-full max-w-2xl space-y-8">
          {/* Logo */}
          <div className="flex items-center gap-3 justify-center">
            <div className="relative w-10 h-10 flex items-center justify-center">
              <Zap className="w-7 h-7 text-accent" />
              <div className="absolute inset-0 bg-accent/20 rounded-lg blur-md" />
            </div>
            <span className="font-semibold text-xl tracking-tight text-text-primary">
              DotMac Platform
            </span>
          </div>

          {/* Signup Wizard */}
          <SignupWizard onComplete={handleSignupComplete} />

          {/* Login link */}
          <p className="text-center text-sm text-text-muted">
            Already have an account?{" "}
            <Link
              href="/login"
              className="text-accent hover:text-accent-hover font-medium"
            >
              Sign in
            </Link>
          </p>

          {/* Terms */}
          <p className="text-center text-xs text-text-muted">
            By signing up, you agree to our{" "}
            <a href="/terms" className="text-accent hover:underline">
              Terms of Service
            </a>{" "}
            and{" "}
            <a href="/privacy" className="text-accent hover:underline">
              Privacy Policy
            </a>
          </p>
        </div>
      </div>

      {/* Right side - Decorative (hidden on mobile) */}
      <div className="hidden lg:flex flex-1 bg-surface-elevated border-l border-border relative overflow-hidden">
        {/* Background pattern */}
        <div className="absolute inset-0 bg-grid opacity-[0.03]" />

        {/* Gradient orbs */}
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-accent/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-highlight/10 rounded-full blur-3xl" />

        {/* Content */}
        <div className="relative z-10 flex flex-col justify-center p-16">
          <div className="space-y-8 max-w-lg">
            <div className="space-y-4">
              <h2 className="text-4xl font-semibold tracking-tight text-text-primary">
                Start building today
              </h2>
              <p className="text-lg text-text-secondary">
                Join thousands of teams using DotMac Platform to manage their SaaS infrastructure.
              </p>
            </div>

            {/* Benefits */}
            <div className="space-y-4">
              {[
                "Free tier with generous limits",
                "No credit card required to start",
                "Full API access from day one",
                "14-day trial of Professional features",
              ].map((benefit, i) => (
                <div
                  key={i}
                  className="flex items-center gap-3 text-text-secondary"
                >
                  <div className="w-1.5 h-1.5 rounded-full bg-accent" />
                  <span>{benefit}</span>
                </div>
              ))}
            </div>

            {/* Social proof */}
            <div className="pt-8 border-t border-border">
              <p className="text-sm text-text-muted">
                Trusted by 500+ companies worldwide
              </p>
              <div className="flex items-center gap-4 mt-4 opacity-50">
                {/* Placeholder for company logos */}
                <div className="w-24 h-8 bg-surface-overlay rounded" />
                <div className="w-20 h-8 bg-surface-overlay rounded" />
                <div className="w-28 h-8 bg-surface-overlay rounded" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
