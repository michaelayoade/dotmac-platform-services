"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { signIn } from "next-auth/react";
import Link from "next/link";
import { Building2, Mail, Lock, ArrowRight, AlertCircle } from "lucide-react";
import { Form, FormField, FormSubmitButton, useForm } from "@dotmac/forms";
import { Input, Button } from "@dotmac/core";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

const loginSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
  password: z.string().min(1, "Password is required"),
});

type LoginFormData = z.infer<typeof loginSchema>;

function TenantLoginContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const callbackUrl = searchParams.get("callbackUrl") || "/portal";
  const errorParam = searchParams.get("error");
  const [error, setError] = useState<string | null>(
    errorParam === "unauthorized"
      ? "Your account does not have access to the Tenant Portal."
      : null
  );

  const ssoProviders = [
    {
      id: "google",
      label: "Google",
      enabled: process.env.NEXT_PUBLIC_GOOGLE_SSO_ENABLED === "true",
      icon: (
        <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
          <path
            fill="currentColor"
            d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
          />
          <path
            fill="currentColor"
            d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
          />
          <path
            fill="currentColor"
            d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
          />
          <path
            fill="currentColor"
            d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
          />
        </svg>
      ),
    },
    {
      id: "azure-ad",
      label: "Microsoft",
      enabled: process.env.NEXT_PUBLIC_AZURE_AD_SSO_ENABLED === "true",
      icon: (
        <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
          <path fill="currentColor" d="M11.4 24H0V12.6L11.4 0z" />
          <path fill="currentColor" d="M24 24H12.6V12.6L24 0z" opacity="0.8" />
          <path fill="currentColor" d="M11.4 24V12.6H0z" opacity="0.6" />
          <path fill="currentColor" d="M24 24V12.6H12.6z" opacity="0.6" />
        </svg>
      ),
    },
  ].filter((provider) => provider.enabled);

  const form = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  const onSubmit = async (data: LoginFormData) => {
    setError(null);

    const result = await signIn("credentials", {
      email: data.email,
      password: data.password,
      redirect: false,
    });

    if (result?.error) {
      setError("Invalid email or password. Please try again.");
      return;
    }

    router.push(callbackUrl);
  };

  return (
    <div className="min-h-screen flex">
      {/* Left side - Form */}
      <div className="flex-1 flex items-center justify-center p-8 bg-surface">
        <div className="w-full max-w-md space-y-8">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="relative w-10 h-10 flex items-center justify-center">
              <Building2 className="w-7 h-7 text-accent" />
              <div className="absolute inset-0 bg-accent/20 rounded-lg blur-md" />
            </div>
            <span className="font-semibold text-xl tracking-tight text-text-primary">
              Organization Portal
            </span>
          </div>

          {/* Header */}
          <div className="space-y-2">
            <h1 className="text-3xl font-semibold tracking-tight text-text-primary">
              Sign in to your organization
            </h1>
            <p className="text-text-secondary">
              Manage your team, billing, and usage from your organization dashboard
            </p>
          </div>

          {/* Error message */}
          {error && (
            <div className="flex items-center gap-3 p-4 rounded-lg bg-status-error/10 border border-status-error/20 text-status-error">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <p className="text-sm">{error}</p>
            </div>
          )}

          {/* Login Form */}
          <Form form={form} onSubmit={onSubmit} className="space-y-6">
            <FormField name="email" label="Email address" required>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
                <Input
                  {...form.register("email")}
                  type="email"
                  placeholder="you@yourcompany.com"
                  className="pl-10"
                  autoComplete="email"
                  autoFocus
                />
              </div>
            </FormField>

            <FormField name="password" label="Password" required>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
                <Input
                  {...form.register("password")}
                  type="password"
                  placeholder="Enter your password"
                  className="pl-10"
                  autoComplete="current-password"
                />
              </div>
            </FormField>

            {/* Remember me & Forgot password */}
            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  className="w-4 h-4 rounded border-border bg-surface-overlay text-accent focus:ring-accent"
                />
                <span className="text-sm text-text-secondary">Remember me</span>
              </label>
              <Link
                href="/forgot-password"
                className="text-sm text-accent hover:text-accent-hover"
              >
                Forgot password?
              </Link>
            </div>

            {/* Submit button */}
            <FormSubmitButton
              className="w-full shadow-glow-sm hover:shadow-glow"
              loadingText="Signing in..."
            >
              Sign in
              <ArrowRight className="w-4 h-4 ml-2" />
            </FormSubmitButton>
          </Form>

          {ssoProviders.length > 0 && (
            <>
              {/* Divider */}
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-border" />
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-4 bg-surface text-text-muted">Or continue with</span>
                </div>
              </div>

              {/* SSO Options */}
              <div
                className={`grid gap-4 ${ssoProviders.length > 1 ? "grid-cols-2" : "grid-cols-1"}`}
              >
                {ssoProviders.map((provider) => (
                  <Button
                    key={provider.id}
                    variant="outline"
                    className="w-full"
                    onClick={() => signIn(provider.id, { callbackUrl })}
                  >
                    {provider.icon}
                    {provider.label}
                  </Button>
                ))}
              </div>
            </>
          )}

          {/* Sign up link */}
          <div className="text-center space-y-2">
            <p className="text-sm text-text-muted">
              Don&apos;t have an organization?{" "}
              <Link href="/signup" className="text-accent hover:text-accent-hover font-medium">
                Create one
              </Link>
            </p>
            <p className="text-sm text-text-muted">
              Looking for the{" "}
              <Link href="/partner/login" className="text-highlight hover:text-highlight/80 font-medium">
                Partner Portal
              </Link>
              ?
            </p>
          </div>
        </div>
      </div>

      {/* Right side - Decorative */}
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
                Your organization, your way
              </h2>
              <p className="text-lg text-text-secondary">
                Take control of your team, monitor usage, and manage your subscription all in one
                place.
              </p>
            </div>

            {/* Feature highlights */}
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
    </div>
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
