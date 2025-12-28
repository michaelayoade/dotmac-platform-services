"use client";

import { useState, type ReactNode } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  ArrowRight,
  AlertCircle,
  Eye,
  EyeOff,
  Lock,
  Mail,
  type LucideIcon,
} from "lucide-react";
import { Form, FormField, FormSubmitButton, useForm } from "@dotmac/forms";
import { Input } from "@dotmac/core";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useTenant } from "@/lib/hooks/use-tenant";
import { cn } from "@/lib/utils";

const loginSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
  password: z.string().min(1, "Password is required"),
});

type LoginFormData = z.infer<typeof loginSchema>;

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type AccentVariant = "accent" | "highlight";

interface LoginBranding {
  icon: LucideIcon;
  label: string;
  accent: AccentVariant;
}

interface LoginScreenProps {
  callbackDefault: string;
  unauthorizedMessage?: string;
  branding: LoginBranding;
  heading: string;
  subheading: string;
  emailPlaceholder: string;
  passwordPlaceholder: string;
  submitLabel: string;
  submitIcon?: boolean;
  forgotHref?: string;
  footer?: ReactNode;
  rightPanel?: ReactNode;
  leftPanelClassName?: string;
}

const accentStyles = {
  accent: {
    icon: "text-accent",
    iconGlow: "bg-accent/20",
    button:
      "bg-accent text-text-inverse shadow-glow-sm hover:shadow-glow",
    link: "text-accent hover:text-accent-hover",
    checkbox: "text-accent focus:ring-accent",
  },
  highlight: {
    icon: "text-highlight",
    iconGlow: "bg-highlight/20",
    button: "bg-highlight text-text-inverse hover:bg-highlight/90",
    link: "text-highlight hover:text-highlight/80",
    checkbox: "text-highlight focus:ring-highlight",
  },
} as const;

export function LoginScreen({
  callbackDefault,
  unauthorizedMessage,
  branding,
  heading,
  subheading,
  emailPlaceholder,
  passwordPlaceholder,
  submitLabel,
  submitIcon = true,
  forgotHref = "/forgot-password",
  footer,
  rightPanel,
  leftPanelClassName,
}: LoginScreenProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const callbackUrl = searchParams.get("callbackUrl") || callbackDefault;
  const errorParam = searchParams.get("error");
  const tenantParam = searchParams.get("tenant") || searchParams.get("tenant_id");
  const [error, setError] = useState<string | null>(
    errorParam === "unauthorized" ? unauthorizedMessage ?? null : null
  );
  const [pending2faUserId, setPending2faUserId] = useState<string | null>(null);
  const [twoFactorCode, setTwoFactorCode] = useState("");
  const [isBackupCode, setIsBackupCode] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [isVerifying2fa, setIsVerifying2fa] = useState(false);
  const { currentTenant } = useTenant();

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
      const tenantId = currentTenant?.id || tenantParam;
      const response = await fetch(`${API_URL}/api/v1/auth/login/cookie`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(tenantId ? { "X-Tenant-ID": tenantId } : {}),
        },
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
        let message = "Invalid email or password. Please try again.";
        try {
          const payload = (await response.json()) as { detail?: string; message?: string; error?: string };
          if (payload?.detail) {
            message = payload.detail;
          } else if (payload?.message) {
            message = payload.message;
          } else if (payload?.error) {
            message = payload.error;
          }
        } catch {
          // Keep the default message when the response isn't JSON.
        }
        setError(message);
        return;
      }

      router.push(callbackUrl);
    } catch (err) {
      setError("Unable to sign in. Please try again.");
    }
  };

  const onVerify2fa = async () => {
    if (isVerifying2fa) return;

    if (!pending2faUserId || !twoFactorCode.trim()) {
      setError("Enter your verification code to continue.");
      return;
    }

    setError(null);
    setIsVerifying2fa(true);

    try {
      const tenantId = currentTenant?.id || tenantParam;
      const response = await fetch(`${API_URL}/api/v1/auth/login/verify-2fa`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(tenantId ? { "X-Tenant-ID": tenantId } : {}),
        },
        credentials: "include",
        body: JSON.stringify({
          user_id: pending2faUserId,
          code: twoFactorCode.trim(),
          is_backup_code: isBackupCode,
        }),
      });

      if (!response.ok) {
        setError("Invalid verification code. Please try again.");
        setTwoFactorCode("");
        return;
      }

      router.push(callbackUrl);
    } catch (err) {
      setError("Unable to verify your code. Please try again.");
    } finally {
      setIsVerifying2fa(false);
    }
  };

  const accent = accentStyles[branding.accent];
  const BrandingIcon = branding.icon;

  return (
    <main className="min-h-screen flex" id="main-content">
      <div className={cn("flex-1 flex items-center justify-center p-8", leftPanelClassName)}>
        <div className="w-full max-w-md space-y-8">
          <div className="flex items-center gap-3">
            <div className="relative w-10 h-10 flex items-center justify-center">
              <BrandingIcon className={cn("w-7 h-7", accent.icon)} />
              <div className={cn("absolute inset-0 rounded-lg blur-md", accent.iconGlow)} />
            </div>
            <span className="font-semibold text-xl tracking-tight text-text-primary">
              {branding.label}
            </span>
          </div>

          <div className="space-y-2">
            <h1 className="text-3xl font-semibold tracking-tight text-text-primary">
              {heading}
            </h1>
            <p className="text-text-secondary">{subheading}</p>
          </div>

          {error && (
            <div className="flex items-center gap-3 p-4 rounded-lg bg-status-error/15 border border-status-error/20 text-status-error">
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
                    id="email"
                    {...form.register("email")}
                    type="email"
                    placeholder={emailPlaceholder}
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
                    id="password"
                    {...form.register("password")}
                    type={showPassword ? "text" : "password"}
                    placeholder={passwordPlaceholder}
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
                <label htmlFor="remember-me" className="flex items-center gap-2 cursor-pointer">
                  <input
                    id="remember-me"
                    name="rememberMe"
                    type="checkbox"
                    className={cn(
                      "w-4 h-4 rounded border-border bg-surface-overlay",
                      accent.checkbox
                    )}
                  />
                  <span className="text-sm text-text-secondary">Remember me</span>
                </label>
                <Link href={forgotHref} className={cn("text-sm font-medium", accent.link)}>
                  Forgot password?
                </Link>
              </div>

              <FormSubmitButton
                className={cn("w-full", accent.button)}
                loadingText="Signing in..."
              >
                {submitLabel}
                {submitIcon && <ArrowRight className="w-4 h-4 ml-2" />}
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
                  id="two-factor-code"
                  name="twoFactorCode"
                  value={twoFactorCode}
                  onChange={(event) => setTwoFactorCode(event.target.value)}
                  placeholder="123456 or XXXX-XXXX"
                  autoComplete="one-time-code"
                />

                <label htmlFor="use-backup-code" className="flex items-center gap-2 text-sm text-text-secondary">
                  <input
                    id="use-backup-code"
                    name="useBackupCode"
                    type="checkbox"
                    checked={isBackupCode}
                    onChange={(event) => setIsBackupCode(event.target.checked)}
                    className={cn(
                      "w-4 h-4 rounded border-border bg-surface-overlay",
                      accent.checkbox
                    )}
                  />
                  Use a backup code
                </label>
              </div>

              <button
                onClick={onVerify2fa}
                disabled={isVerifying2fa || !twoFactorCode.trim()}
                className={cn(
                  "w-full inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed",
                  accent.button
                )}
              >
                {isVerifying2fa ? "Verifying..." : "Verify and continue"}
                {!isVerifying2fa && submitIcon && <ArrowRight className="w-4 h-4 ml-2" />}
              </button>
            </div>
          )}

          {footer}
        </div>
      </div>

      {rightPanel}
    </main>
  );
}
