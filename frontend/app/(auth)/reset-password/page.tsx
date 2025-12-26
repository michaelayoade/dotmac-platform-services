"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  Zap,
  Lock,
  Eye,
  EyeOff,
  CheckCircle,
  XCircle,
  Loader2,
  ArrowRight,
  AlertCircle,
} from "lucide-react";
import { Form, FormField, FormSubmitButton } from "@dotmac/forms";
import { Input, Button } from "@dotmac/core";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { validateResetToken, confirmPasswordReset } from "@/lib/api/auth";
import { cn } from "@/lib/utils";

const passwordSchema = z
  .object({
    password: z
      .string()
      .min(8, "Password must be at least 8 characters")
      .regex(/[A-Z]/, "Password must contain at least one uppercase letter")
      .regex(/[a-z]/, "Password must contain at least one lowercase letter")
      .regex(/[0-9]/, "Password must contain at least one number"),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });

type PasswordFormData = z.infer<typeof passwordSchema>;

type ResetState = "validating" | "valid" | "invalid" | "expired" | "success";

const passwordRequirements = [
  { label: "At least 8 characters", regex: /.{8,}/ },
  { label: "One uppercase letter", regex: /[A-Z]/ },
  { label: "One lowercase letter", regex: /[a-z]/ },
  { label: "One number", regex: /[0-9]/ },
];

function ResetPasswordContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  const [state, setState] = useState<ResetState>("validating");
  const [email, setEmail] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const form = useForm<PasswordFormData>({
    resolver: zodResolver(passwordSchema),
    defaultValues: {
      password: "",
      confirmPassword: "",
    },
    mode: "onChange",
  });

  const password = form.watch("password");

  const validateToken = useCallback(async (resetToken: string) => {
    setState("validating");
    setError(null);

    try {
      const response = await validateResetToken(resetToken);
      if (response.valid) {
        setState("valid");
        setEmail(response.email || null);
      } else {
        setState("invalid");
        setError("This reset link is invalid or has already been used.");
      }
    } catch {
      setState("invalid");
      setError("This reset link is invalid or has expired.");
    }
  }, []);

  useEffect(() => {
    if (!token) {
      setState("invalid");
      setError("No reset token provided.");
      return;
    }
    void validateToken(token);
  }, [token, validateToken]);

  const onSubmit = async (data: PasswordFormData) => {
    if (!token) return;

    setError(null);

    try {
      await confirmPasswordReset({
        token,
        newPassword: data.password,
      });
      setState("success");
      setTimeout(() => {
        router.push("/login?reset=true");
      }, 3000);
    } catch (err) {
      if (err instanceof Error && err.message.includes("expired")) {
        setState("expired");
        setError("This reset link has expired. Please request a new one.");
      } else {
        setError("Failed to reset password. Please try again.");
      }
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-8 bg-surface">
      <div className="w-full max-w-md space-y-8">
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

        {/* Content */}
        <div className="bg-surface-elevated rounded-xl border border-border p-8 space-y-6">
          {/* Validating State */}
          {state === "validating" && (
            <div className="text-center space-y-4">
              <div className="w-16 h-16 mx-auto bg-accent/15 rounded-full flex items-center justify-center">
                <Loader2 className="w-8 h-8 text-accent animate-spin" />
              </div>
              <div className="space-y-2">
                <h1 className="text-2xl font-semibold text-text-primary">
                  Verifying reset link
                </h1>
                <p className="text-text-secondary">
                  Please wait while we verify your reset link...
                </p>
              </div>
            </div>
          )}

          {/* Invalid/Expired State */}
          {(state === "invalid" || state === "expired") && (
            <div className="text-center space-y-6">
              <div className="w-16 h-16 mx-auto bg-status-error/15 rounded-full flex items-center justify-center">
                <XCircle className="w-8 h-8 text-status-error" />
              </div>
              <div className="space-y-2">
                <h1 className="text-2xl font-semibold text-text-primary">
                  {state === "expired" ? "Link expired" : "Invalid link"}
                </h1>
                <p className="text-text-secondary">
                  {error || "This password reset link is no longer valid."}
                </p>
              </div>
              <div className="space-y-3">
                <Link href="/forgot-password" className="block">
                  <Button className="w-full shadow-glow-sm hover:shadow-glow">
                    Request new reset link
                  </Button>
                </Link>
                <Link href="/login" className="block">
                  <Button variant="outline" className="w-full">
                    Back to sign in
                  </Button>
                </Link>
              </div>
            </div>
          )}

          {/* Valid State - Show Form */}
          {state === "valid" && (
            <>
              <div className="space-y-2 text-center">
                <h1 className="text-2xl font-semibold text-text-primary">
                  Set new password
                </h1>
                <p className="text-text-secondary">
                  {email ? (
                    <>
                      Create a new password for{" "}
                      <span className="font-medium text-text-primary">{email}</span>
                    </>
                  ) : (
                    "Enter your new password below"
                  )}
                </p>
              </div>

              {error && (
                <div className="flex items-center gap-3 p-4 rounded-lg bg-status-error/15 border border-status-error/20 text-status-error">
                  <AlertCircle className="w-5 h-5 flex-shrink-0" />
                  <p className="text-sm">{error}</p>
                </div>
              )}

              <Form form={form} onSubmit={onSubmit} className="space-y-6">
                <FormField name="password" label="New password" required>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
                    <Input
                      {...form.register("password")}
                      type={showPassword ? "text" : "password"}
                      placeholder="Enter new password"
                      className="pl-10 pr-10"
                      autoComplete="new-password"
                      autoFocus
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-secondary"
                    >
                      {showPassword ? (
                        <EyeOff className="w-5 h-5" />
                      ) : (
                        <Eye className="w-5 h-5" />
                      )}
                    </button>
                  </div>
                </FormField>

                {/* Password Requirements */}
                <div className="space-y-2">
                  <p className="text-sm text-text-muted">Password requirements:</p>
                  <div className="grid grid-cols-2 gap-2">
                    {passwordRequirements.map((req) => {
                      const met = req.regex.test(password || "");
                      return (
                        <div
                          key={req.label}
                          className={cn(
                            "flex items-center gap-2 text-sm",
                            met ? "text-status-success" : "text-text-muted"
                          )}
                        >
                          <CheckCircle
                            className={cn(
                              "w-4 h-4",
                              met ? "opacity-100" : "opacity-30"
                            )}
                          />
                          <span>{req.label}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>

                <FormField name="confirmPassword" label="Confirm password" required>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
                    <Input
                      {...form.register("confirmPassword")}
                      type={showConfirmPassword ? "text" : "password"}
                      placeholder="Confirm new password"
                      className="pl-10 pr-10"
                      autoComplete="new-password"
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-secondary"
                    >
                      {showConfirmPassword ? (
                        <EyeOff className="w-5 h-5" />
                      ) : (
                        <Eye className="w-5 h-5" />
                      )}
                    </button>
                  </div>
                </FormField>

                <FormSubmitButton
                  className="w-full shadow-glow-sm hover:shadow-glow"
                  loadingText="Resetting password..."
                >
                  Reset password
                  <ArrowRight className="w-4 h-4 ml-2" />
                </FormSubmitButton>
              </Form>
            </>
          )}

          {/* Success State */}
          {state === "success" && (
            <div className="text-center space-y-6">
              <div className="w-16 h-16 mx-auto bg-status-success/15 rounded-full flex items-center justify-center">
                <CheckCircle className="w-8 h-8 text-status-success" />
              </div>
              <div className="space-y-2">
                <h1 className="text-2xl font-semibold text-text-primary">
                  Password reset successful
                </h1>
                <p className="text-text-secondary">
                  Your password has been updated. Redirecting you to login...
                </p>
              </div>
              <Link href="/login" className="block">
                <Button className="w-full">Continue to sign in</Button>
              </Link>
            </div>
          )}
        </div>

        {/* Help text */}
        <p className="text-center text-sm text-text-muted">
          Need help?{" "}
          <a
            href="mailto:support@dotmac.com"
            className="text-accent hover:underline"
          >
            Contact support
          </a>
        </p>
      </div>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center">
          <Loader2 className="w-8 h-8 animate-spin text-accent" />
        </div>
      }
    >
      <ResetPasswordContent />
    </Suspense>
  );
}
