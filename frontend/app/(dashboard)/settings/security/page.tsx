"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import {
  ArrowLeft,
  Lock,
  Shield,
  Smartphone,
  Eye,
  EyeOff,
  CheckCircle,
  XCircle,
  Monitor,
  Globe,
  Clock,
  AlertTriangle,
  Key,
  Copy,
  RefreshCcw,
  Loader2,
} from "lucide-react";
import { Form, FormField, FormSubmitButton } from "@dotmac/forms";
import { Input, Button, Card, useToast } from "@dotmac/core";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { format } from "date-fns";

import { cn } from "@/lib/utils";
import { ConfirmDialog, useConfirmDialog } from "@/components/shared/confirm-dialog";
import {
  useCurrentUser,
  useChangePassword,
  useSessions,
  useRevokeSession,
  useRevokeAllSessions,
  useSetupMfa,
  useEnableMfa,
  useDisableMfa,
  useRegenerateBackupCodes,
  useLoginHistory,
} from "@/lib/hooks/api/use-auth";

// Password Schema
const passwordSchema = z
  .object({
    currentPassword: z.string().min(1, "Current password is required"),
    newPassword: z
      .string()
      .min(8, "Password must be at least 8 characters")
      .regex(/[A-Z]/, "Password must contain at least one uppercase letter")
      .regex(/[a-z]/, "Password must contain at least one lowercase letter")
      .regex(/[0-9]/, "Password must contain at least one number"),
    confirmPassword: z.string(),
  })
  .refine((data) => data.newPassword === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });

type PasswordFormData = z.infer<typeof passwordSchema>;

const passwordRequirements = [
  { label: "At least 8 characters", regex: /.{8,}/ },
  { label: "One uppercase letter", regex: /[A-Z]/ },
  { label: "One lowercase letter", regex: /[a-z]/ },
  { label: "One number", regex: /[0-9]/ },
];

export default function SecuritySettingsPage() {
  const { toast } = useToast();
  const { confirm, dialog } = useConfirmDialog();
  const { data: user } = useCurrentUser();

  return (
    <div className="max-w-3xl space-y-6">
      {dialog}

      {/* Back link */}
      <Link
        href="/settings"
        className="inline-flex items-center gap-2 text-sm text-text-muted hover:text-text-secondary transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Settings
      </Link>

      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-semibold text-text-primary">Security Settings</h1>
        <p className="text-text-muted mt-1">
          Manage your password, two-factor authentication, and sessions
        </p>
      </div>

      {/* Password Section */}
      <PasswordSection />

      {/* Two-Factor Authentication Section */}
      <TwoFactorSection mfaEnabled={user?.mfaEnabled ?? false} />

      {/* Active Sessions Section */}
      <SessionsSection />

      {/* Login History Section */}
      <LoginHistorySection />
    </div>
  );
}

// Password Change Section
function PasswordSection() {
  const { toast } = useToast();
  const changePassword = useChangePassword();
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);

  const form = useForm<PasswordFormData>({
    resolver: zodResolver(passwordSchema),
    defaultValues: {
      currentPassword: "",
      newPassword: "",
      confirmPassword: "",
    },
    mode: "onChange",
  });

  const newPassword = form.watch("newPassword");

  const onSubmit = async (data: PasswordFormData) => {
    try {
      await changePassword.mutateAsync({
        currentPassword: data.currentPassword,
        newPassword: data.newPassword,
      });
      toast({
        title: "Password updated",
        description: "Your password has been changed successfully.",
        variant: "success",
      });
      form.reset();
    } catch {
      toast({
        title: "Error",
        description: "Failed to update password. Please check your current password.",
        variant: "error",
      });
    }
  };

  return (
    <Card className="p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
          <Lock className="w-5 h-5 text-accent" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-text-primary">Password</h2>
          <p className="text-sm text-text-muted">Update your password to keep your account secure</p>
        </div>
      </div>

      <Form form={form} onSubmit={onSubmit} className="space-y-4">
        <FormField name="currentPassword" label="Current Password" required>
          <div className="relative">
            <Input
              {...form.register("currentPassword")}
              type={showCurrentPassword ? "text" : "password"}
              placeholder="Enter current password"
              className="pr-10"
            />
            <button
              type="button"
              onClick={() => setShowCurrentPassword(!showCurrentPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-secondary"
            >
              {showCurrentPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
        </FormField>

        <FormField name="newPassword" label="New Password" required>
          <div className="relative">
            <Input
              {...form.register("newPassword")}
              type={showNewPassword ? "text" : "password"}
              placeholder="Enter new password"
              className="pr-10"
            />
            <button
              type="button"
              onClick={() => setShowNewPassword(!showNewPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-secondary"
            >
              {showNewPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
        </FormField>

        {/* Password Requirements */}
        <div className="grid grid-cols-2 gap-2">
          {passwordRequirements.map((req) => {
            const met = req.regex.test(newPassword || "");
            return (
              <div
                key={req.label}
                className={cn(
                  "flex items-center gap-2 text-sm",
                  met ? "text-status-success" : "text-text-muted"
                )}
              >
                <CheckCircle className={cn("w-4 h-4", met ? "opacity-100" : "opacity-30")} />
                <span>{req.label}</span>
              </div>
            );
          })}
        </div>

        <FormField name="confirmPassword" label="Confirm New Password" required>
          <Input
            {...form.register("confirmPassword")}
            type="password"
            placeholder="Confirm new password"
          />
        </FormField>

        <div className="pt-2">
          <FormSubmitButton loadingText="Updating...">Update Password</FormSubmitButton>
        </div>
      </Form>
    </Card>
  );
}

// Two-Factor Authentication Section
function TwoFactorSection({ mfaEnabled }: { mfaEnabled: boolean }) {
  const { toast } = useToast();
  const { confirm, dialog } = useConfirmDialog();
  const [setupMode, setSetupMode] = useState(false);
  const [qrData, setQrData] = useState<{ secret: string; qrCodeUrl: string; backupCodes: string[] } | null>(null);
  const [verificationCode, setVerificationCode] = useState("");
  const [showBackupCodes, setShowBackupCodes] = useState(false);

  const setupMfa = useSetupMfa();
  const enableMfa = useEnableMfa();
  const disableMfa = useDisableMfa();
  const regenerateBackupCodes = useRegenerateBackupCodes();

  const handleSetup = async () => {
    try {
      const result = await setupMfa.mutateAsync();
      setQrData(result);
      setSetupMode(true);
    } catch {
      toast({
        title: "Error",
        description: "Failed to setup 2FA. Please try again.",
        variant: "error",
      });
    }
  };

  const handleEnable = async () => {
    if (!verificationCode || verificationCode.length !== 6) {
      toast({
        title: "Invalid code",
        description: "Please enter a 6-digit verification code.",
        variant: "error",
      });
      return;
    }

    try {
      await enableMfa.mutateAsync(verificationCode);
      toast({
        title: "2FA Enabled",
        description: "Two-factor authentication has been enabled.",
        variant: "success",
      });
      setShowBackupCodes(true);
    } catch {
      toast({
        title: "Error",
        description: "Invalid verification code. Please try again.",
        variant: "error",
      });
    }
  };

  const handleDisable = async () => {
    const code = await new Promise<string | null>((resolve) => {
      const input = prompt("Enter your 2FA code to disable:");
      resolve(input);
    });

    if (!code) return;

    try {
      await disableMfa.mutateAsync(code);
      toast({
        title: "2FA Disabled",
        description: "Two-factor authentication has been disabled.",
        variant: "success",
      });
      setSetupMode(false);
      setQrData(null);
    } catch {
      toast({
        title: "Error",
        description: "Invalid code. Please try again.",
        variant: "error",
      });
    }
  };

  const handleRegenerateBackupCodes = async () => {
    const confirmed = await confirm({
      title: "Regenerate Backup Codes",
      description: "This will invalidate all existing backup codes. Are you sure?",
      variant: "danger",
    });

    if (confirmed) {
      try {
        const result = await regenerateBackupCodes.mutateAsync();
        setQrData((prev) => prev ? { ...prev, backupCodes: result.backupCodes } : null);
        setShowBackupCodes(true);
        toast({
          title: "Backup codes regenerated",
          description: "New backup codes have been generated.",
          variant: "success",
        });
      } catch {
        toast({
          title: "Error",
          description: "Failed to regenerate backup codes.",
          variant: "error",
        });
      }
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({ title: "Copied to clipboard" });
  };

  return (
    <>
      {dialog}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-status-success/15 flex items-center justify-center">
              <Shield className="w-5 h-5 text-status-success" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-text-primary">Two-Factor Authentication</h2>
              <p className="text-sm text-text-muted">Add an extra layer of security to your account</p>
            </div>
          </div>
          <span
            className={cn(
              "px-3 py-1 rounded-full text-xs font-medium",
              mfaEnabled
                ? "bg-status-success/15 text-status-success"
                : "bg-surface-overlay text-text-muted"
            )}
          >
            {mfaEnabled ? "Enabled" : "Disabled"}
          </span>
        </div>

        {!mfaEnabled && !setupMode && (
          <div className="text-center py-6">
            <Smartphone className="w-12 h-12 mx-auto text-text-muted mb-4" />
            <p className="text-text-secondary mb-4">
              Protect your account with an authenticator app like Google Authenticator or Authy
            </p>
            <Button onClick={handleSetup} disabled={setupMfa.isPending}>
              {setupMfa.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Setting up...
                </>
              ) : (
                "Enable 2FA"
              )}
            </Button>
          </div>
        )}

        {setupMode && qrData && !showBackupCodes && (
          <div className="space-y-6">
            <div className="text-center">
              <p className="text-sm text-text-secondary mb-4">
                Scan this QR code with your authenticator app
              </p>
              <div className="inline-block p-4 bg-white rounded-lg">
                <Image
                  src={qrData.qrCodeUrl}
                  alt="QR Code"
                  width={192}
                  height={192}
                  unoptimized
                />
              </div>
            </div>

            <div className="text-center">
              <p className="text-sm text-text-muted mb-2">Or enter this code manually:</p>
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-surface-overlay rounded-lg">
                <code className="font-mono text-sm text-text-primary">{qrData.secret}</code>
                <button
                  onClick={() => copyToClipboard(qrData.secret)}
                  className="text-text-muted hover:text-text-secondary"
                >
                  <Copy className="w-4 h-4" />
                </button>
              </div>
            </div>

            <div className="max-w-xs mx-auto">
              <label className="block text-sm font-medium text-text-primary mb-2">
                Enter verification code
              </label>
              <Input
                type="text"
                value={verificationCode}
                onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                placeholder="000000"
                className="text-center font-mono text-lg tracking-widest"
                maxLength={6}
              />
            </div>

            <div className="flex justify-center gap-3">
              <Button variant="outline" onClick={() => setSetupMode(false)}>
                Cancel
              </Button>
              <Button
                onClick={handleEnable}
                disabled={enableMfa.isPending || verificationCode.length !== 6}
              >
                {enableMfa.isPending ? "Verifying..." : "Verify & Enable"}
              </Button>
            </div>
          </div>
        )}

        {showBackupCodes && qrData?.backupCodes && (
          <div className="space-y-4">
            <div className="flex items-center gap-2 p-4 bg-status-warning/10 border border-status-warning/20 rounded-lg">
              <AlertTriangle className="w-5 h-5 text-status-warning flex-shrink-0" />
              <p className="text-sm text-text-secondary">
                Save these backup codes in a safe place. You&apos;ll need them if you lose access to your authenticator app.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-2 p-4 bg-surface-overlay rounded-lg">
              {qrData.backupCodes.map((code, i) => (
                <code key={i} className="font-mono text-sm text-text-primary">
                  {code}
                </code>
              ))}
            </div>

            <div className="flex justify-center gap-3">
              <Button
                variant="outline"
                onClick={() => copyToClipboard(qrData.backupCodes.join("\n"))}
              >
                <Copy className="w-4 h-4 mr-2" />
                Copy All
              </Button>
              <Button onClick={() => setShowBackupCodes(false)}>Done</Button>
            </div>
          </div>
        )}

        {mfaEnabled && !setupMode && (
          <div className="space-y-4">
            <div className="flex items-center gap-3 p-4 bg-surface-overlay rounded-lg">
              <CheckCircle className="w-5 h-5 text-status-success" />
              <div>
                <p className="text-sm font-medium text-text-primary">2FA is active</p>
                <p className="text-xs text-text-muted">
                  Your account is protected with two-factor authentication
                </p>
              </div>
            </div>

            <div className="flex gap-3">
              <Button variant="outline" onClick={handleRegenerateBackupCodes}>
                <Key className="w-4 h-4 mr-2" />
                Regenerate Backup Codes
              </Button>
              <Button variant="destructive" onClick={handleDisable}>
                Disable 2FA
              </Button>
            </div>
          </div>
        )}
      </Card>
    </>
  );
}

// Active Sessions Section
function SessionsSection() {
  const { toast } = useToast();
  const { confirm, dialog } = useConfirmDialog();
  const { data: sessions, isLoading } = useSessions();
  const revokeSession = useRevokeSession();
  const revokeAllSessions = useRevokeAllSessions();

  const handleRevokeSession = async (sessionId: string) => {
    const confirmed = await confirm({
      title: "Revoke Session",
      description: "This will sign out the device. Continue?",
    });

    if (confirmed) {
      try {
        await revokeSession.mutateAsync(sessionId);
        toast({ title: "Session revoked" });
      } catch {
        toast({ title: "Failed to revoke session", variant: "error" });
      }
    }
  };

  const handleRevokeAll = async () => {
    const confirmed = await confirm({
      title: "Revoke All Sessions",
      description: "This will sign you out of all devices except the current one. Continue?",
      variant: "danger",
    });

    if (confirmed) {
      try {
        await revokeAllSessions.mutateAsync();
        toast({ title: "All sessions revoked" });
      } catch {
        toast({ title: "Failed to revoke sessions", variant: "error" });
      }
    }
  };

  return (
    <>
      {dialog}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-status-info/15 flex items-center justify-center">
              <Monitor className="w-5 h-5 text-status-info" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-text-primary">Active Sessions</h2>
              <p className="text-sm text-text-muted">Manage your active login sessions</p>
            </div>
          </div>
          <Button variant="outline" size="sm" onClick={handleRevokeAll}>
            <XCircle className="w-4 h-4 mr-2" />
            Revoke All
          </Button>
        </div>

        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex items-center gap-4 p-4 bg-surface-overlay rounded-lg animate-pulse">
                <div className="w-10 h-10 bg-surface rounded-lg" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 w-48 bg-surface rounded" />
                  <div className="h-3 w-32 bg-surface rounded" />
                </div>
              </div>
            ))}
          </div>
        ) : sessions && sessions.length > 0 ? (
          <div className="space-y-3">
            {sessions.map((session) => (
              <div
                key={session.id}
                className="flex items-center justify-between p-4 bg-surface-overlay rounded-lg"
              >
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-lg bg-surface flex items-center justify-center">
                    <Monitor className="w-5 h-5 text-text-muted" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-medium text-text-primary">
                        {session.device || "Unknown Device"}
                      </p>
                      {session.current && (
                        <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-status-success/15 text-status-success">
                          Current
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-3 text-xs text-text-muted mt-1">
                      <span className="flex items-center gap-1">
                        <Globe className="w-3 h-3" />
                        {session.ip}
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {session.lastActive
                          ? format(new Date(session.lastActive), "MMM d, h:mm a")
                          : "Unknown"}
                      </span>
                    </div>
                  </div>
                </div>
                {!session.current && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleRevokeSession(session.id)}
                    className="text-status-error hover:text-status-error"
                  >
                    Revoke
                  </Button>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-center text-text-muted py-8">No active sessions found</p>
        )}
      </Card>
    </>
  );
}

// Login History Section
function LoginHistorySection() {
  const { data: history, isLoading } = useLoginHistory({ pageSize: 10 });

  return (
    <Card className="p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-lg bg-highlight-subtle flex items-center justify-center">
          <Clock className="w-5 h-5 text-highlight" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-text-primary">Login History</h2>
          <p className="text-sm text-text-muted">Recent sign-in activity on your account</p>
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="flex items-center justify-between py-3 animate-pulse">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-surface-overlay rounded" />
                <div className="space-y-1">
                  <div className="h-4 w-32 bg-surface-overlay rounded" />
                  <div className="h-3 w-24 bg-surface-overlay rounded" />
                </div>
              </div>
              <div className="h-6 w-16 bg-surface-overlay rounded-full" />
            </div>
          ))}
        </div>
      ) : history?.entries && history.entries.length > 0 ? (
        <div className="divide-y divide-border">
          {history.entries.map((entry) => (
            <div key={entry.id} className="flex items-center justify-between py-3">
              <div className="flex items-center gap-3">
                <div
                  className={cn(
                    "w-8 h-8 rounded-lg flex items-center justify-center",
                    entry.status === "success" ? "bg-status-success/15" : "bg-status-error/15"
                  )}
                >
                  {entry.status === "success" ? (
                    <CheckCircle className="w-4 h-4 text-status-success" />
                  ) : (
                    <XCircle className="w-4 h-4 text-status-error" />
                  )}
                </div>
                <div>
                  <p className="text-sm text-text-primary">
                    {entry.browser} on {entry.os}
                  </p>
                  <div className="flex items-center gap-2 text-xs text-text-muted">
                    <span>{entry.ipAddress}</span>
                    {entry.location && (
                      <>
                        <span>·</span>
                        <span>{entry.location}</span>
                      </>
                    )}
                  </div>
                </div>
              </div>
              <div className="text-right">
                <span
                  className={cn(
                    "px-2 py-1 rounded-full text-xs font-medium",
                    entry.status === "success"
                      ? "bg-status-success/15 text-status-success"
                      : "bg-status-error/15 text-status-error"
                  )}
                >
                  {entry.status === "success" ? "Success" : "Failed"}
                </span>
                <p className="text-xs text-text-muted mt-1">
                  {format(new Date(entry.timestamp), "MMM d, h:mm a")}
                </p>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-center text-text-muted py-8">No login history available</p>
      )}
    </Card>
  );
}
