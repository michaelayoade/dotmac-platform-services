"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Building2, Mail, Lock, ArrowRight, AlertCircle, Eye, EyeOff } from "lucide-react";
import { Form, FormField, FormSubmitButton, useForm } from "@dotmac/forms";
import { Input } from "@dotmac/core";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

const loginSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
  password: z.string().min(1, "Password is required"),
});

type LoginFormData = z.infer<typeof loginSchema>;

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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
  const [pending2faUserId, setPending2faUserId] = useState<string | null>(null);
  const [twoFactorCode, setTwoFactorCode] = useState("");
  const [isBackupCode, setIsBackupCode] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const form = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  const onSubmit = async (data: LoginFormData) => {
    setError(null);
    setPending2faUserId(null);

    try {
      const response = await fetch(`${API_URL}/api/v1/auth/login/cookie`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email: data.email, password: data.password }),
      });

      if (
        response.status === 403 &&
        response.headers.get("X-2FA-Required") === "true"
      ) {
        const userId = response.headers.get("X-User-ID");
        if (!userId) {
          setError("2FA required, but no user context was provided.");
          return;
        }
        setPending2faUserId(userId);
        return;
      }

      if (!response.ok) {
        setError("Invalid email or password. Please try again.");
        return;
      }

      router.push(callbackUrl);
    } catch (err) {
      setError("Unable to sign in. Please try again.");
    }
  };

  const onVerify2fa = async () => {
    if (!pending2faUserId || !twoFactorCode.trim()) {
      setError("Enter your verification code to continue.");
      return;
    }

    setError(null);

    try {
      const response = await fetch(`${API_URL}/api/v1/auth/login/verify-2fa`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          user_id: pending2faUserId,
          code: twoFactorCode.trim(),
          is_backup_code: isBackupCode,
        }),
      });

      if (!response.ok) {
        setError("Invalid verification code. Please try again.");
        return;
      }

      router.push(callbackUrl);
    } catch (err) {
      setError("Unable to verify your code. Please try again.");
    }
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

          {!pending2faUserId ? (
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
                  type={showPassword ? "text" : "password"}
                  placeholder="Enter your password"
                  className="pl-10 pr-10"
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((current) => !current)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-secondary"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </FormField>

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

            <FormSubmitButton
              className="w-full bg-accent text-white shadow-glow-sm hover:shadow-glow"
              loadingText="Signing in..."
            >
              Sign in
              <ArrowRight className="w-4 h-4 ml-2" />
            </FormSubmitButton>
            </Form>
          ) : (
            <div className="space-y-6">
              <div className="space-y-2">
                <h2 className="text-lg font-semibold text-text-primary">
                  Two-factor verification
                </h2>
                <p className="text-sm text-text-secondary">
                  Enter the code from your authenticator app or a backup code.
                </p>
              </div>

              <div className="space-y-4">
                <Input
                  value={twoFactorCode}
                  onChange={(event) => setTwoFactorCode(event.target.value)}
                  placeholder="123456 or XXXX-XXXX"
                  autoComplete="one-time-code"
                />

                <label className="flex items-center gap-2 text-sm text-text-secondary">
                  <input
                    type="checkbox"
                    checked={isBackupCode}
                    onChange={(event) => setIsBackupCode(event.target.checked)}
                    className="w-4 h-4 rounded border-border bg-surface-overlay text-accent focus:ring-accent"
                  />
                  Use a backup code
                </label>
              </div>

              <button
                onClick={onVerify2fa}
                className="w-full shadow-glow-sm hover:shadow-glow inline-flex items-center justify-center rounded-md bg-accent px-4 py-2 text-sm font-medium text-white"
              >
                Verify and continue
                <ArrowRight className="w-4 h-4 ml-2" />
              </button>
            </div>
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
