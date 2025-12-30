"use client";

import { useState, useRef, useEffect, KeyboardEvent, ClipboardEvent } from "react";
import {
  Shield,
  Loader2,
  AlertCircle,
  ArrowRight,
  Key,
  Smartphone,
} from "lucide-react";
import { Button } from "@dotmac/core";
import { cn } from "@/lib/utils";
import { verifyMfaCode } from "@/lib/api/auth";

interface MfaVerificationProps {
  sessionToken: string;
  onSuccess: (tokens: {
    accessToken: string;
    refreshToken: string;
    tokenType: string;
    expiresIn: number;
  }) => void;
  onCancel?: () => void;
  className?: string;
}

export function MfaVerification({
  sessionToken,
  onSuccess,
  onCancel,
  className,
}: MfaVerificationProps) {
  const [code, setCode] = useState<string[]>(Array(6).fill(""));
  const [isBackupCode, setIsBackupCode] = useState(false);
  const [backupCode, setBackupCode] = useState("");
  const [isVerifying, setIsVerifying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  // Focus first input on mount
  useEffect(() => {
    if (!isBackupCode) {
      inputRefs.current[0]?.focus();
    }
  }, [isBackupCode]);

  const handleOtpChange = (index: number, value: string) => {
    // Only allow digits
    const digit = value.replace(/\D/g, "").slice(-1);

    const newCode = [...code];
    newCode[index] = digit;
    setCode(newCode);
    setError(null);

    // Auto-focus next input
    if (digit && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }

    // Auto-submit when complete (guard against duplicate submissions)
    if (digit && index === 5 && newCode.every((c) => c) && !isVerifying) {
      handleVerify(newCode.join(""));
    }
  };

  const handleKeyDown = (index: number, e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Backspace" && !code[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
    if (e.key === "ArrowLeft" && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
    if (e.key === "ArrowRight" && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handlePaste = (e: ClipboardEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (isVerifying) return; // Guard against paste during verification

    const pastedData = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, 6);

    if (pastedData.length > 0) {
      const newCode = [...code];
      pastedData.split("").forEach((char, i) => {
        if (i < 6) newCode[i] = char;
      });
      setCode(newCode);

      // Focus last filled input (not after it)
      const focusIndex = Math.min(pastedData.length - 1, 5);
      inputRefs.current[focusIndex >= 0 ? focusIndex : 0]?.focus();

      // Auto-submit if complete (guard against duplicate submissions)
      if (pastedData.length === 6 && !isVerifying) {
        handleVerify(pastedData);
      }
    }
  };

  const handleVerify = async (codeString?: string) => {
    const verificationCode = codeString || (isBackupCode ? backupCode : code.join(""));

    if (isBackupCode && !backupCode.trim()) {
      setError("Please enter a backup code");
      return;
    }
    if (!isBackupCode && verificationCode.length !== 6) {
      setError("Please enter a complete 6-digit code");
      return;
    }

    setIsVerifying(true);
    setError(null);

    try {
      const result = await verifyMfaCode({
        code: verificationCode,
        sessionToken,
        isBackupCode,
      });
      onSuccess(result);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : isBackupCode
            ? "Invalid backup code. Please try again."
            : "Invalid verification code. Please try again."
      );
      // Reset code on error
      if (!isBackupCode) {
        setCode(Array(6).fill(""));
        inputRefs.current[0]?.focus();
      }
    } finally {
      setIsVerifying(false);
    }
  };

  const toggleMode = () => {
    setIsBackupCode(!isBackupCode);
    setError(null);
    setCode(Array(6).fill(""));
    setBackupCode("");
  };

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header */}
      <div className="text-center space-y-4">
        <div className="w-16 h-16 mx-auto bg-accent/15 rounded-full flex items-center justify-center">
          <Shield className="w-8 h-8 text-accent" />
        </div>
        <div className="space-y-2">
          <h2 className="text-2xl font-semibold text-text-primary">
            Two-factor authentication
          </h2>
          <p className="text-text-secondary">
            {isBackupCode
              ? "Enter one of your backup codes"
              : "Enter the 6-digit code from your authenticator app"}
          </p>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-3 p-4 rounded-lg bg-status-error/15 border border-status-error/20 text-status-error">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <p className="text-sm">{error}</p>
        </div>
      )}

      {/* OTP Input or Backup Code Input */}
      {isBackupCode ? (
        <div className="space-y-4">
          <div className="relative">
            <Key className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
            <input
              type="text"
              value={backupCode}
              onChange={(e) => {
                setBackupCode(e.target.value.toUpperCase());
                setError(null);
              }}
              placeholder="XXXX-XXXX-XXXX"
              className="w-full pl-10 pr-4 py-3 bg-surface-overlay border border-border rounded-lg text-text-primary placeholder:text-text-muted font-mono text-center tracking-wider focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-surface focus-visible:border-transparent"
              autoFocus
            />
          </div>
          <p className="text-sm text-text-muted text-center">
            Backup codes are 12 characters long and were provided when you set up 2FA
          </p>
        </div>
      ) : (
        <div className="flex justify-center gap-2">
          {code.map((digit, index) => (
            <input
              key={index}
              ref={(el) => {
                inputRefs.current[index] = el;
              }}
              type="text"
              inputMode="numeric"
              maxLength={1}
              value={digit}
              onChange={(e) => handleOtpChange(index, e.target.value)}
              onKeyDown={(e) => handleKeyDown(index, e)}
              onPaste={handlePaste}
              className={cn(
                "w-12 h-14 text-center text-xl font-semibold rounded-lg border",
                "bg-surface-overlay text-text-primary",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-surface focus-visible:border-transparent",
                "transition-colors",
                digit ? "border-accent" : "border-border"
              )}
              disabled={isVerifying}
            />
          ))}
        </div>
      )}

      {/* Verify Button */}
      <Button
        onClick={() => handleVerify()}
        disabled={isVerifying || (!isBackupCode && code.some((c) => !c))}
        className="w-full shadow-glow-sm hover:shadow-glow"
      >
        {isVerifying ? (
          <>
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            Verifying...
          </>
        ) : (
          <>
            Verify
            <ArrowRight className="w-4 h-4 ml-2" />
          </>
        )}
      </Button>

      {/* Toggle Mode */}
      <div className="text-center">
        <button
          type="button"
          onClick={toggleMode}
          className="text-sm text-accent hover:text-accent-hover inline-flex items-center gap-2"
          disabled={isVerifying}
        >
          {isBackupCode ? (
            <>
              <Smartphone className="w-4 h-4" />
              Use authenticator app instead
            </>
          ) : (
            <>
              <Key className="w-4 h-4" />
              Use a backup code instead
            </>
          )}
        </button>
      </div>

      {/* Cancel */}
      {onCancel && (
        <div className="text-center pt-4 border-t border-border">
          <button
            type="button"
            onClick={onCancel}
            className="text-sm text-text-muted hover:text-text-secondary"
            disabled={isVerifying}
          >
            Cancel and try different sign-in method
          </button>
        </div>
      )}
    </div>
  );
}

export default MfaVerification;
