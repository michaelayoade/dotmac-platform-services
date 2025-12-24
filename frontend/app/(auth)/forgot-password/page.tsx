"use client";

import { useState } from "react";
import Link from "next/link";
import { Zap, Mail, ArrowRight, ArrowLeft, AlertCircle, CheckCircle } from "lucide-react";
import { Form, FormField, FormSubmitButton } from "@dotmac/forms";
import { Input, Button } from "@dotmac/core";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { useRequestPasswordReset } from "@/lib/hooks/api/use-auth";

const forgotPasswordSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
});

type ForgotPasswordFormData = z.infer<typeof forgotPasswordSchema>;

export default function ForgotPasswordPage() {
  const [submitted, setSubmitted] = useState(false);
  const [submittedEmail, setSubmittedEmail] = useState("");
  const requestReset = useRequestPasswordReset();

  const form = useForm<ForgotPasswordFormData>({
    resolver: zodResolver(forgotPasswordSchema),
    defaultValues: {
      email: "",
    },
  });

  const onSubmit = async (data: ForgotPasswordFormData) => {
    try {
      await requestReset.mutateAsync({ email: data.email });
      setSubmittedEmail(data.email);
      setSubmitted(true);
    } catch {
      // Even on error, show success to prevent email enumeration
      setSubmittedEmail(data.email);
      setSubmitted(true);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left side - Form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-md space-y-8">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="relative w-10 h-10 flex items-center justify-center">
              <Zap className="w-7 h-7 text-accent" />
              <div className="absolute inset-0 bg-accent/20 rounded-lg blur-md" />
            </div>
            <span className="font-semibold text-xl tracking-tight text-text-primary">
              DotMac Platform
            </span>
          </div>

          {submitted ? (
            // Success state
            <div className="space-y-6">
              <div className="flex items-center justify-center w-16 h-16 mx-auto rounded-full bg-status-success/10">
                <CheckCircle className="w-8 h-8 text-status-success" />
              </div>

              <div className="space-y-2 text-center">
                <h1 className="text-3xl font-semibold tracking-tight text-text-primary">
                  Check your email
                </h1>
                <p className="text-text-secondary">
                  We sent a password reset link to{" "}
                  <span className="font-medium text-text-primary">{submittedEmail}</span>
                </p>
              </div>

              <div className="p-4 rounded-lg bg-surface-overlay border border-border">
                <p className="text-sm text-text-secondary">
                  Didn&apos;t receive the email? Check your spam folder, or{" "}
                  <button
                    onClick={() => {
                      setSubmitted(false);
                      form.reset();
                    }}
                    className="text-accent hover:text-accent-hover font-medium"
                  >
                    try another email address
                  </button>
                </p>
              </div>

              <Link href="/login" className="block">
                <Button variant="outline" className="w-full">
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back to sign in
                </Button>
              </Link>
            </div>
          ) : (
            // Form state
            <>
              {/* Header */}
              <div className="space-y-2">
                <h1 className="text-3xl font-semibold tracking-tight text-text-primary">
                  Forgot password?
                </h1>
                <p className="text-text-secondary">
                  No worries, we&apos;ll send you reset instructions.
                </p>
              </div>

              {/* Error message */}
              {requestReset.error && (
                <div className="flex items-center gap-3 p-4 rounded-lg bg-status-error/10 border border-status-error/20 text-status-error">
                  <AlertCircle className="w-5 h-5 flex-shrink-0" />
                  <p className="text-sm">Something went wrong. Please try again.</p>
                </div>
              )}

              {/* Form */}
              <Form form={form} onSubmit={onSubmit} className="space-y-6">
                <FormField name="email" label="Email address" required>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
                    <Input
                      {...form.register("email")}
                      type="email"
                      placeholder="you@company.com"
                      className="pl-10"
                      autoComplete="email"
                      autoFocus
                    />
                  </div>
                </FormField>

                <FormSubmitButton
                  className="w-full shadow-glow-sm hover:shadow-glow"
                  loadingText="Sending..."
                >
                  Send reset link
                  <ArrowRight className="w-4 h-4 ml-2" />
                </FormSubmitButton>
              </Form>

              {/* Back to login */}
              <Link
                href="/login"
                className="flex items-center justify-center gap-2 text-sm text-text-secondary hover:text-text-primary"
              >
                <ArrowLeft className="w-4 h-4" />
                Back to sign in
              </Link>
            </>
          )}
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
                Secure password recovery
              </h2>
              <p className="text-lg text-text-secondary">
                We&apos;ll send you a secure link to reset your password. The link expires in 1 hour for your security.
              </p>
            </div>

            {/* Security tips */}
            <div className="space-y-4">
              {[
                "Reset links expire after 1 hour",
                "Links can only be used once",
                "We'll notify you of any password changes",
                "Contact support if you need assistance",
              ].map((tip, i) => (
                <div
                  key={i}
                  className="flex items-center gap-3 text-text-secondary"
                >
                  <div className="w-1.5 h-1.5 rounded-full bg-accent" />
                  <span>{tip}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
