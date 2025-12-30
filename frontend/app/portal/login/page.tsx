"use client";

import { Suspense } from "react";
import Link from "next/link";
import { Building2 } from "lucide-react";
import { LoginScreen } from "@/components/features/auth/login-screen";

function TenantLoginContent() {
  return (
    <LoginScreen
      callbackDefault="/portal"
      unauthorizedMessage="Your account does not have access to the Tenant Portal."
      branding={{
        icon: Building2,
        label: "Organization Portal",
        accent: "accent",
      }}
      heading="Sign in to your organization"
      subheading="Manage your team, billing, and usage from your organization dashboard"
      emailPlaceholder="you@yourcompany.com"
      passwordPlaceholder="Enter your password"
      submitLabel="Sign in"
      footer={
        <div className="text-center space-y-2">
          <p className="text-sm text-text-muted">
            Don&apos;t have an organization?{" "}
            <Link href="/signup" className="text-accent hover:text-accent-hover font-medium">
              Create one
            </Link>
          </p>
          <p className="text-sm text-text-muted">
            Looking for the{" "}
            <Link
              href="/partner/login"
              className="text-highlight hover:text-highlight/80 font-medium"
            >
              Partner Portal
            </Link>
            ?
          </p>
        </div>
      }
      rightPanel={
        <div className="hidden lg:flex flex-1 bg-surface-elevated border-l border-border relative overflow-hidden">
          <div className="absolute inset-0 bg-grid opacity-[0.03]" />
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-accent/15 rounded-full blur-3xl" />
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-highlight/15 rounded-full blur-3xl" />
          <div className="relative z-10 flex flex-col justify-center p-16">
            <div className="space-y-8 max-w-lg">
              <div className="space-y-4">
                <h2 className="text-4xl font-semibold tracking-tight text-text-primary">
                  Your organization, your way
                </h2>
                <p className="text-lg text-text-secondary">
                  Take control of your team, monitor usage, and manage your subscription all in one
                  place.
                </p>
              </div>
              <div className="space-y-4">
                {[
                  "Invite and manage team members",
                  "Monitor API usage and storage",
                  "View and download invoices",
                  "Configure organization settings",
                ].map((feature, i) => (
                  <div key={i} className="flex items-center gap-3 text-text-secondary">
                    <div className="w-1.5 h-1.5 rounded-full bg-accent" />
                    <span>{feature}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      }
      leftPanelClassName="bg-surface"
    />
  );
}

export default function TenantLoginPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center text-text-muted">
          Loading...
        </div>
      }
    >
      <TenantLoginContent />
    </Suspense>
  );
}
