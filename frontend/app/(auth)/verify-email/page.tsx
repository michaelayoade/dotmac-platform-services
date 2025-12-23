"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  Zap,
  Mail,
  CheckCircle,
  XCircle,
  Loader2,
  RefreshCw,
} from "lucide-react";
import { Button } from "@dotmac/core";

import { verifyEmail, resendVerificationEmail } from "@/lib/api/signup";

type VerificationState = "pending" | "verifying" | "success" | "error";

function VerifyEmailContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const email = searchParams.get("email");
  const token = searchParams.get("token");

  const [state, setState] = useState<VerificationState>(
    token ? "verifying" : "pending"
  );
  const [error, setError] = useState<string | null>(null);
  const [resendCooldown, setResendCooldown] = useState(0);
  const [isResending, setIsResending] = useState(false);

  // Verify token if present
  useEffect(() => {
    if (token) {
      verifyToken(token);
    }
  }, [token]);

  // Resend cooldown timer
  useEffect(() => {
    if (resendCooldown > 0) {
      const timer = setTimeout(() => setResendCooldown((c) => c - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [resendCooldown]);

  const verifyToken = async (verificationToken: string) => {
    setState("verifying");
    setError(null);

    try {
      const response = await verifyEmail({ token: verificationToken });
      if (response.success) {
        setState("success");
        // Redirect to login after 3 seconds
        setTimeout(() => {
          router.push("/login?verified=true");
        }, 3000);
      } else {
        setState("error");
        setError(response.message || "Verification failed");
      }
    } catch (err) {
      setState("error");
      setError(
        err instanceof Error
          ? err.message
          : "Failed to verify email. The link may have expired."
      );
    }
  };

  const handleResendEmail = async () => {
    if (!email || resendCooldown > 0) return;

    setIsResending(true);
    setError(null);

    try {
      await resendVerificationEmail({ email });
      setResendCooldown(60); // 60 second cooldown
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to resend verification email"
      );
    } finally {
      setIsResending(false);
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
        <div className="bg-surface-elevated rounded-xl border border-border p-8 text-center space-y-6">
          {/* Pending State - Waiting for user to check email */}
          {state === "pending" && (
            <>
              <div className="w-16 h-16 mx-auto bg-accent/10 rounded-full flex items-center justify-center">
                <Mail className="w-8 h-8 text-accent" />
              </div>

              <div className="space-y-2">
                <h1 className="text-2xl font-semibold text-text-primary">
                  Check your email
                </h1>
                <p className="text-text-secondary">
                  We've sent a verification link to{" "}
                  {email ? (
                    <span className="font-medium text-text-primary">{email}</span>
                  ) : (
                    "your email address"
                  )}
                </p>
              </div>

              <div className="pt-4 space-y-4">
                <p className="text-sm text-text-muted">
                  Click the link in the email to verify your account and complete
                  registration.
                </p>

                {/* Resend button */}
                <div className="pt-4">
                  <Button
                    variant="outline"
                    onClick={handleResendEmail}
                    disabled={isResending || resendCooldown > 0}
                    className="w-full"
                  >
                    {isResending ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Sending...
                      </>
                    ) : resendCooldown > 0 ? (
                      <>
                        <RefreshCw className="w-4 h-4 mr-2" />
                        Resend in {resendCooldown}s
                      </>
                    ) : (
                      <>
                        <RefreshCw className="w-4 h-4 mr-2" />
                        Resend verification email
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </>
          )}

          {/* Verifying State */}
          {state === "verifying" && (
            <>
              <div className="w-16 h-16 mx-auto bg-accent/10 rounded-full flex items-center justify-center">
                <Loader2 className="w-8 h-8 text-accent animate-spin" />
              </div>

              <div className="space-y-2">
                <h1 className="text-2xl font-semibold text-text-primary">
                  Verifying your email
                </h1>
                <p className="text-text-secondary">
                  Please wait while we verify your email address...
                </p>
              </div>
            </>
          )}

          {/* Success State */}
          {state === "success" && (
            <>
              <div className="w-16 h-16 mx-auto bg-status-success/10 rounded-full flex items-center justify-center">
                <CheckCircle className="w-8 h-8 text-status-success" />
              </div>

              <div className="space-y-2">
                <h1 className="text-2xl font-semibold text-text-primary">
                  Email verified!
                </h1>
                <p className="text-text-secondary">
                  Your account is now active. Redirecting you to login...
                </p>
              </div>

              <div className="pt-4">
                <Link href="/login">
                  <Button className="w-full">Continue to Login</Button>
                </Link>
              </div>
            </>
          )}

          {/* Error State */}
          {state === "error" && (
            <>
              <div className="w-16 h-16 mx-auto bg-status-error/10 rounded-full flex items-center justify-center">
                <XCircle className="w-8 h-8 text-status-error" />
              </div>

              <div className="space-y-2">
                <h1 className="text-2xl font-semibold text-text-primary">
                  Verification failed
                </h1>
                <p className="text-text-secondary">
                  {error || "The verification link is invalid or has expired."}
                </p>
              </div>

              <div className="pt-4 space-y-3">
                {email && (
                  <Button
                    variant="outline"
                    onClick={handleResendEmail}
                    disabled={isResending || resendCooldown > 0}
                    className="w-full"
                  >
                    {isResending ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Sending...
                      </>
                    ) : resendCooldown > 0 ? (
                      <>Resend in {resendCooldown}s</>
                    ) : (
                      "Request new verification link"
                    )}
                  </Button>
                )}

                <Link href="/signup" className="block">
                  <Button variant="ghost" className="w-full">
                    Start over
                  </Button>
                </Link>
              </div>
            </>
          )}

          {/* Error message */}
          {error && state === "pending" && (
            <div className="p-3 rounded-lg bg-status-error/10 border border-status-error/20 text-status-error text-sm">
              {error}
            </div>
          )}
        </div>

        {/* Help text */}
        <p className="text-center text-sm text-text-muted">
          Didn't receive the email? Check your spam folder or{" "}
          <a
            href="mailto:support@dotmac.com"
            className="text-accent hover:underline"
          >
            contact support
          </a>
        </p>
      </div>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center">
          <Loader2 className="w-8 h-8 animate-spin text-accent" />
        </div>
      }
    >
      <VerifyEmailContent />
    </Suspense>
  );
}
