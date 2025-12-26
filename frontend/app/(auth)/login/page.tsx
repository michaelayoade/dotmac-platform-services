"use client";

import { Suspense } from "react";
import Link from "next/link";
import { Zap } from "lucide-react";
import { LoginScreen } from "@/components/features/auth/login-screen";

function LoginContent() {
  return (
    <LoginScreen
      callbackDefault="/"
      branding={{
        icon: Zap,
        label: "DotMac Platform",
        accent: "accent",
      }}
      heading="Welcome back"
      subheading="Sign in to your account to continue"
      emailPlaceholder="you@company.com"
      passwordPlaceholder="••••••••"
      submitLabel="Sign in"
      footer={
        <p className="text-center text-sm text-text-muted">
          Don&apos;t have an account?{" "}
          <Link href="/signup" className="text-accent hover:text-accent-hover font-medium">
            Sign up
          </Link>
        </p>
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
                  Control your platform with confidence
                </h2>
                <p className="text-lg text-text-secondary">
                  Manage users, tenants, billing, and deployments from a single, powerful dashboard.
                </p>
              </div>
              <div className="space-y-4">
                {[
                  "Multi-tenant architecture with complete isolation",
                  "Role-based access control with fine-grained permissions",
                  "Real-time analytics and monitoring",
                  "Automated billing and subscription management",
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
    />
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center text-text-muted">
          Loading...
        </div>
      }
    >
      <LoginContent />
    </Suspense>
  );
}
