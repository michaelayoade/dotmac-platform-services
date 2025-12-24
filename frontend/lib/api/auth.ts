/**
 * Auth API Client
 *
 * Handles authentication-related API calls including:
 * - Password reset flows
 * - MFA verification
 * - Session management
 * - Login history
 */

import { api } from "./client";

// Types
export interface PasswordResetRequestData {
  email: string;
}

export interface PasswordResetConfirmData {
  token: string;
  newPassword: string;
}

export interface MfaVerifyData {
  code: string;
  sessionToken: string;
  isBackupCode?: boolean;
}

export interface LoginHistoryEntry {
  id: string;
  timestamp: string;
  ipAddress: string;
  userAgent: string;
  device: string;
  browser: string;
  os: string;
  location?: string;
  status: "success" | "failed";
  failureReason?: string;
}

export interface LoginHistoryResponse {
  entries: LoginHistoryEntry[];
  total: number;
  page: number;
  pageSize: number;
}

export interface LoginHistoryParams {
  page?: number;
  pageSize?: number;
  status?: "success" | "failed";
}

// Password Reset API
export async function requestPasswordReset(
  data: PasswordResetRequestData
): Promise<{ message: string }> {
  return api.post<{ message: string }>("/api/v1/auth/password-reset", data, {
    requiresAuth: false,
  });
}

export async function validateResetToken(
  token: string
): Promise<{ valid: boolean; email?: string; expiresAt?: string }> {
  return api.get<{ valid: boolean; email?: string; expiresAt?: string }>(
    "/api/v1/auth/password-reset/validate",
    {
      params: { token },
      requiresAuth: false,
    }
  );
}

export async function confirmPasswordReset(
  data: PasswordResetConfirmData
): Promise<{ message: string }> {
  return api.post<{ message: string }>(
    "/api/v1/auth/password-reset/confirm",
    data,
    {
      requiresAuth: false,
    }
  );
}

// MFA Verification API (for login flow)
export async function verifyMfaCode(
  data: MfaVerifyData
): Promise<{
  accessToken: string;
  refreshToken: string;
  tokenType: string;
  expiresIn: number;
}> {
  return api.post("/api/v1/auth/login/verify-2fa", data, {
    requiresAuth: false,
  });
}

// MFA Management API
export async function regenerateBackupCodes(): Promise<{
  backupCodes: string[];
}> {
  return api.post<{ backupCodes: string[] }>(
    "/api/v1/auth/2fa/regenerate-backup-codes"
  );
}

// Session Management API
export async function revokeAllSessions(): Promise<{ message: string }> {
  return api.delete<{ message: string }>("/api/v1/auth/me/sessions");
}

// Login History API
export async function getLoginHistory(
  params?: LoginHistoryParams
): Promise<LoginHistoryResponse> {
  const response = await api.get<LoginHistoryResponse>(
    "/api/v1/auth/me/login-history",
    {
      params: params
        ? {
            page: params.page,
            page_size: params.pageSize,
            status: params.status,
          }
        : undefined,
    }
  );

  // Normalize response if needed
  return {
    entries: response.entries || [],
    total: response.total || 0,
    page: response.page || 1,
    pageSize: response.pageSize || 20,
  };
}
