"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getPartners,
  getPartner,
  createPartner,
  updatePartner,
  deletePartner,
  activatePartner,
  deactivatePartner,
  getPartnerUsers,
  getPartnerUser,
  addPartnerUser,
  updatePartnerUser,
  removePartnerUser,
  getPartnerAccounts,
  addPartnerAccount,
  removePartnerAccount,
  getPartnerCommissions,
  createCommissionEvent,
  processCommissionPayout,
  getPartnerPayouts,
  createReferral,
  getReferrals,
  convertReferral,
  getPartnerDashboard,
  getPartnerStats,
  getPartnersDashboard,
  type GetPartnersParams,
  type Partner,
  type CreatePartnerData,
  type PartnerUser,
  type PartnerAccount,
  type CommissionEvent,
  type PartnerPayout,
  type ReferralLead,
  type PartnerDashboard,
  type PartnerStats,
  type UpdatePartnerUserData,
} from "@/lib/api/partners";
import { queryKeys } from "@/lib/api/query-keys";
import type { DashboardQueryParams } from "@/lib/api/types/dashboard";

type PartnerCommissionsParams = Parameters<typeof getPartnerCommissions> extends [
  string,
  infer P,
]
  ? P
  : undefined;
type PartnerReferralsParams = Parameters<typeof getReferrals> extends [string, infer P]
  ? P
  : undefined;

// ============================================================================
// Partners Hooks
// ============================================================================

export function usePartnersDashboard(params?: DashboardQueryParams) {
  return useQuery({
    queryKey: queryKeys.partners.dashboard(),
    queryFn: () => getPartnersDashboard(params),
    staleTime: 60 * 1000, // 1 minute
  });
}

export function usePartners(params?: GetPartnersParams) {
  return useQuery({
    queryKey: queryKeys.partners.list(params),
    queryFn: () => getPartners(params),
    placeholderData: (previousData) => previousData,
  });
}

export function usePartner(id: string) {
  return useQuery({
    queryKey: queryKeys.partners.detail(id),
    queryFn: () => getPartner(id),
    enabled: !!id,
  });
}

export function useCreatePartner() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createPartner,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.partners.all,
      });
    },
  });
}

export function useUpdatePartner() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CreatePartnerData> }) =>
      updatePartner(id, data),
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.partners.detail(data.id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.partners.all,
      });
    },
  });
}

export function useDeletePartner() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deletePartner,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.partners.all,
      });
    },
  });
}

export function useActivatePartner() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: activatePartner,
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.partners.detail(data.id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.partners.all,
      });
    },
  });
}

export function useDeactivatePartner() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deactivatePartner,
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.partners.detail(data.id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.partners.all,
      });
    },
  });
}

// ============================================================================
// Partner Users Hooks
// ============================================================================

export function usePartnerUsers(partnerId: string) {
  return useQuery({
    queryKey: queryKeys.partners.users(partnerId),
    queryFn: () => getPartnerUsers(partnerId),
    enabled: !!partnerId,
  });
}

export function usePartnerUser(partnerId: string, userId: string) {
  return useQuery({
    queryKey: [...queryKeys.partners.users(partnerId), userId],
    queryFn: () => getPartnerUser(partnerId, userId),
    enabled: !!partnerId && !!userId,
  });
}

export function useAddPartnerUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      partnerId,
      firstName,
      lastName,
      email,
      role,
      phone,
      userId,
      isPrimaryContact,
    }: {
      partnerId: string;
      firstName: string;
      lastName: string;
      email: string;
      role: string;
      phone?: string;
      userId?: string;
      isPrimaryContact?: boolean;
    }) =>
      addPartnerUser(partnerId, {
        firstName,
        lastName,
        email,
        role,
        phone,
        userId,
        isPrimaryContact,
      }),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.partners.users(variables.partnerId),
      });
    },
  });
}

export function useUpdatePartnerUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      partnerId,
      userId,
      data,
    }: {
      partnerId: string;
      userId: string;
      data: UpdatePartnerUserData;
    }) => updatePartnerUser(partnerId, userId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.partners.users(variables.partnerId),
      });
    },
  });
}

export function useRemovePartnerUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ partnerId, userId }: { partnerId: string; userId: string }) =>
      removePartnerUser(partnerId, userId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.partners.users(variables.partnerId),
      });
    },
  });
}

// ============================================================================
// Partner Accounts Hooks
// ============================================================================

export function usePartnerAccounts(partnerId: string) {
  return useQuery({
    queryKey: queryKeys.partners.accounts(partnerId),
    queryFn: () => getPartnerAccounts(partnerId),
    enabled: !!partnerId,
  });
}

export function useAddPartnerAccount() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ partnerId, customerId }: { partnerId: string; customerId: string }) =>
      addPartnerAccount(partnerId, customerId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.partners.accounts(variables.partnerId),
      });
    },
  });
}

export function useRemovePartnerAccount() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ partnerId, customerId }: { partnerId: string; customerId: string }) =>
      removePartnerAccount(partnerId, customerId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.partners.accounts(variables.partnerId),
      });
    },
  });
}

// ============================================================================
// Partner Commissions Hooks
// ============================================================================

export function usePartnerCommissions(
  partnerId: string,
  params?: PartnerCommissionsParams
) {
  return useQuery({
    queryKey: queryKeys.partners.commissions.list(partnerId, params),
    queryFn: () => getPartnerCommissions(partnerId, params),
    enabled: !!partnerId,
    placeholderData: (previousData) => previousData,
  });
}

export function useCreateCommissionEvent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createCommissionEvent,
    onSuccess: (data) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.partners.commissions.all(data.partnerId),
      });
    },
  });
}

export function useProcessCommissionPayout() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      partnerId,
      commissionIds,
      paymentMethod,
    }: {
      partnerId: string;
      commissionIds: string[];
      paymentMethod: string;
    }) => processCommissionPayout(partnerId, commissionIds, paymentMethod),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.partners.commissions.all(variables.partnerId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.partners.payouts(variables.partnerId),
      });
    },
  });
}

export function usePartnerPayouts(partnerId: string, params?: { page?: number; pageSize?: number }) {
  return useQuery({
    queryKey: queryKeys.partners.payouts(partnerId, params),
    queryFn: () => getPartnerPayouts(partnerId, params),
    enabled: !!partnerId,
    placeholderData: (previousData) => previousData,
  });
}

// ============================================================================
// Referrals Hooks
// ============================================================================

export function useReferrals(
  partnerId: string,
  params?: PartnerReferralsParams
) {
  return useQuery({
    queryKey: queryKeys.partners.referrals.list(partnerId, params),
    queryFn: () => getReferrals(partnerId, params),
    enabled: !!partnerId,
    placeholderData: (previousData) => previousData,
  });
}

export function useCreateReferral() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createReferral,
    onSuccess: (data) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.partners.referrals.all(data.partnerId),
      });
    },
  });
}

export function useConvertReferral() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      partnerId,
      referralId,
      customerId,
    }: {
      partnerId: string;
      referralId: string;
      customerId: string;
    }) => convertReferral(partnerId, referralId, customerId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.partners.referrals.all(data.partnerId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.partners.accounts(data.partnerId),
      });
    },
  });
}

// ============================================================================
// Partner Dashboard & Stats Hooks
// ============================================================================

export function usePartnerDashboard() {
  return useQuery({
    queryKey: queryKeys.partners.dashboard(),
    queryFn: getPartnerDashboard,
    staleTime: 5 * 60 * 1000,
  });
}

export function usePartnerStats(params?: { periodDays?: number }) {
  return useQuery({
    queryKey: queryKeys.partners.stats(params),
    queryFn: () => getPartnerStats(params),
    staleTime: 5 * 60 * 1000,
  });
}

// ============================================================================
// Re-export types
// ============================================================================

export type {
  GetPartnersParams,
  Partner,
  CreatePartnerData,
  PartnerUser,
  PartnerAccount,
  CommissionEvent,
  PartnerPayout,
  ReferralLead,
  PartnerDashboard,
  PartnerStats,
  UpdatePartnerUserData,
};
