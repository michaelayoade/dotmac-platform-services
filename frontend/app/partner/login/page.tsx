"use client";

import { Suspense } from "react";
import Link from "next/link";
import { Users } from "lucide-react";
import { LoginScreen } from "@/components/features/auth/login-screen";

function PartnerLoginContent() {
  return (
    <LoginScreen
      callbackDefault="/partner"
      unauthorizedMessage="Your account does not have access to the Partner Portal."
      branding={{
        icon: Users,
        label: "Partner Portal",
        accent: "highlight",
      }}
      heading="Partner Sign In"
      subheading="Access your partner dashboard to manage referrals, commissions, and tenants"
      emailPlaceholder="partner@company.com"
      passwordPlaceholder="Enter your password"
      submitLabel="Sign in to Partner Portal"
      footer={
        <div className="text-center space-y-2">
          <p className="text-sm text-text-muted">
            Need a partner account?{" "}
            <a
              href="mailto:partners@dotmac.io"
              className="text-highlight hover:text-highlight/80 font-medium"
            >
              Contact us
            </a>
          </p>
          <p className="text-sm text-text-muted">
            Looking for the{" "}
            <Link href="/login" className="text-accent hover:text-accent-hover font-medium">
              main login
            </Link>
            ?
          </p>
          <p className="text-sm text-text-muted">
            Looking for the{" "}
            <Link
              href="/portal/login"
              className="text-highlight hover:text-highlight/80 font-medium"
            >
              Tenant Portal
            </Link>
            ?
          </p>
        </div>
      }
      rightPanel={
        <div className="hidden lg:flex flex-1 bg-highlight/5 border-l border-border relative overflow-hidden">
          <div className="absolute inset-0 bg-grid opacity-[0.03]" />
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-highlight/15 rounded-full blur-3xl" />
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-accent/15 rounded-full blur-3xl" />
          <div className="relative z-10 flex flex-col justify-center p-16">
            <div className="space-y-8 max-w-lg">
              <div className="space-y-4">
                <h2 className="text-4xl font-semibold tracking-tight text-text-primary">
                  Grow your business with us
                </h2>
                <p className="text-lg text-text-secondary">
                  Access powerful tools to manage your partner relationship, track commissions, and
                  grow your revenue.
                </p>
              </div>
              <div className="space-y-4">
                {[
                  "Track referrals and conversions in real-time",
                  "View commission earnings and payouts",
                  "Manage your tenant portfolio",
                  "Download revenue statements",
                ].map((feature, i) => (
                  <div key={i} className="flex items-center gap-3 text-text-secondary">
                    <div className="w-1.5 h-1.5 rounded-full bg-highlight" />
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

export default function PartnerLoginPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center text-text-muted">
          Loading...
        </div>
      }
    >
      <PartnerLoginContent />
    </Suspense>
  );
}
