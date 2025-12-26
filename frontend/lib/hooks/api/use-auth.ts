"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import { queryKeys } from "@/lib/api/query-keys";
import {
  requestPasswordReset,
  confirmPasswordReset,
  regenerateBackupCodes,
  revokeAllSessions,
  getLoginHistory,
  type PasswordResetRequestData,
  type PasswordResetConfirmData,
  type LoginHistoryParams,
} from "@/lib/api/auth";
import type { PlatformUser, SessionInfo } from "@/types/auth";

// Types
interface UpdateProfileData {
  name?: string;
  phone?: string;
  timezone?: string;
  language?: string;
  avatar?: string;
}

interface ChangePasswordData {
  currentPassword: string;
  newPassword: string;
}

interface MfaSetupResponse {
  secret: string;
  qrCodeUrl: string;
  backupCodes: string[];
}

// API functions
async function getCurrentUser(): Promise<PlatformUser> {
  return api.get<PlatformUser>("/api/v1/auth/me");
}

async function updateProfile(data: UpdateProfileData): Promise<PlatformUser> {
  return api.patch<PlatformUser>("/api/v1/auth/me", data);
}

async function changePassword(data: ChangePasswordData): Promise<void> {
  return api.post<void>("/api/v1/auth/change-password", data);
}

async function getSessions(): Promise<SessionInfo[]> {
  return api.get<SessionInfo[]>("/api/v1/auth/me/sessions");
}

async function revokeSession(sessionId: string): Promise<void> {
  return api.delete<void>(`/api/v1/auth/me/sessions/${sessionId}`);
}

async function setupMfa(): Promise<MfaSetupResponse> {
  return api.post<MfaSetupResponse>("/api/v1/auth/2fa/setup");
}

async function enableMfa(code: string): Promise<void> {
  return api.post<void>("/api/v1/auth/2fa/enable", { code });
}

async function disableMfa(code: string): Promise<void> {
  return api.post<void>("/api/v1/auth/2fa/disable", { code });
}

// Hooks
export function useCurrentUser(options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: queryKeys.auth.me(),
    queryFn: getCurrentUser,
    staleTime: 5 * 60 * 1000, // 5 minutes
    enabled: options?.enabled ?? true,
  });
}

export function useUpdateProfile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: updateProfile,
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.auth.me(), data);
    },
  });
}

export function useChangePassword() {
  return useMutation({
    mutationFn: changePassword,
  });
}

export function useSessions() {
  return useQuery({
    queryKey: queryKeys.auth.sessions(),
    queryFn: getSessions,
  });
}

export function useRevokeSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: revokeSession,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.auth.sessions() });
    },
  });
}

export function useSetupMfa() {
  return useMutation({
    mutationFn: setupMfa,
  });
}

export function useEnableMfa() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: enableMfa,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.auth.me() });
    },
  });
}

export function useDisableMfa() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: disableMfa,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.auth.me() });
    },
  });
}

// Password Reset Hooks
export function useRequestPasswordReset() {
  return useMutation({
    mutationFn: (data: PasswordResetRequestData) => requestPasswordReset(data),
  });
}

export function useConfirmPasswordReset() {
  return useMutation({
    mutationFn: (data: PasswordResetConfirmData) => confirmPasswordReset(data),
  });
}

// Session Management Hooks
export function useRevokeAllSessions() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: revokeAllSessions,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.auth.sessions() });
    },
  });
}

export function useRegenerateBackupCodes() {
  return useMutation({
    mutationFn: regenerateBackupCodes,
  });
}

// Login History Hook
export function useLoginHistory(params?: LoginHistoryParams) {
  return useQuery({
    queryKey: queryKeys.auth.loginHistory(params),
    queryFn: () => getLoginHistory(params),
  });
}
