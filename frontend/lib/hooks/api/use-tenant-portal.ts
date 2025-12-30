"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "@/lib/api/query-keys";
import {
  getTenantDashboard,
  getTenantMembers,
  getMemberById,
  updateMemberRole,
  removeMember,
  getInvitations,
  inviteMember,
  cancelInvitation,
  resendInvitation,
  getTenantBilling,
  getTenantInvoices,
  downloadInvoice,
  getTenantUsage,
  getTenantUsageBreakdown,
  getTenantSettings,
  updateTenantSettings,
  getApiKeys,
  createApiKey,
  deleteApiKey,
  type GetMembersParams,
  type GetInvoicesParams,
  type GetUsageParams,
} from "@/lib/api/tenant-portal";
import type {
  InviteMemberRequest,
  UpdateMemberRoleRequest,
  UpdateTenantSettingsRequest,
  CreateApiKeyRequest,
} from "@/types/tenant-portal";

// Dashboard
export function useTenantDashboard() {
  return useQuery({
    queryKey: queryKeys.tenantPortal.dashboard(),
    queryFn: getTenantDashboard,
  });
}

// Team Members
export function useTenantMembers(params?: GetMembersParams) {
  return useQuery({
    queryKey: queryKeys.tenantPortal.members.list(params),
    queryFn: () => getTenantMembers(params),
    placeholderData: (previousData) => previousData,
  });
}

export function useTenantMember(id: string) {
  return useQuery({
    queryKey: [...queryKeys.tenantPortal.members.all(), "detail", id],
    queryFn: () => getMemberById(id),
    enabled: !!id,
  });
}

export function useUpdateMemberRole() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateMemberRoleRequest }) =>
      updateMemberRole(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.tenantPortal.members.all(),
      });
    },
  });
}

export function useRemoveMember() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: removeMember,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.tenantPortal.members.all(),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.tenantPortal.dashboard(),
      });
    },
  });
}

// Invitations
export function useTenantInvitations() {
  return useQuery({
    queryKey: queryKeys.tenantPortal.invitations.list(),
    queryFn: getInvitations,
  });
}

export function useInviteMember() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: InviteMemberRequest) => inviteMember(data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.tenantPortal.invitations.all(),
      });
    },
  });
}

export function useCancelInvitation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: cancelInvitation,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.tenantPortal.invitations.all(),
      });
    },
  });
}

export function useResendInvitation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: resendInvitation,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.tenantPortal.invitations.all(),
      });
    },
  });
}

// Billing
export function useTenantBilling() {
  return useQuery({
    queryKey: queryKeys.tenantPortal.billing(),
    queryFn: getTenantBilling,
  });
}

export function useTenantInvoices(params?: GetInvoicesParams) {
  return useQuery({
    queryKey: [...queryKeys.tenantPortal.billing(), "invoices", params],
    queryFn: () => getTenantInvoices(params),
    placeholderData: (previousData) => previousData,
  });
}

export function useDownloadInvoice() {
  return useMutation({
    mutationFn: downloadInvoice,
  });
}

// Usage
export function useTenantUsage(params?: GetUsageParams) {
  return useQuery({
    queryKey: queryKeys.tenantPortal.usage(params),
    queryFn: () => getTenantUsage(params),
  });
}

export function useTenantUsageBreakdown(params?: GetUsageParams) {
  return useQuery({
    queryKey: [...queryKeys.tenantPortal.usage(params), "breakdown"],
    queryFn: () => getTenantUsageBreakdown(params),
  });
}

// Settings
export function useTenantSettings() {
  return useQuery({
    queryKey: queryKeys.tenantPortal.settings(),
    queryFn: getTenantSettings,
  });
}

export function useUpdateTenantSettings() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: UpdateTenantSettingsRequest) => updateTenantSettings(data),
    onSuccess: (updatedSettings) => {
      queryClient.setQueryData(queryKeys.tenantPortal.settings(), updatedSettings);
    },
  });
}

// API Keys
export function useApiKeys() {
  return useQuery({
    queryKey: [...queryKeys.tenantPortal.settings(), "api-keys"],
    queryFn: getApiKeys,
  });
}

export function useCreateApiKey() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateApiKeyRequest) => createApiKey(data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: [...queryKeys.tenantPortal.settings(), "api-keys"],
      });
    },
  });
}

export function useDeleteApiKey() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteApiKey,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: [...queryKeys.tenantPortal.settings(), "api-keys"],
      });
    },
  });
}

// Logo Upload
export function useUploadTenantLogo() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ file, type }: { file: File; type: "logo" | "favicon" }) => {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("type", type);

      const response = await fetch("/api/portal/settings/branding/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Failed to upload logo");
      }

      return response.json() as Promise<{ url: string }>;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.tenantPortal.settings(),
      });
    },
  });
}
