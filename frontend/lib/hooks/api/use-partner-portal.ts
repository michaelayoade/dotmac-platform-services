"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "@/lib/api/query-keys";
import {
  getPartnerDashboard,
  getPartnerReferrals,
  getReferralById,
  createReferral,
  updateReferral,
  getPartnerCustomers,
  getPartnerCommissions,
  getPartnerStatements,
  getStatementById,
  downloadStatement,
  getPartnerPayouts,
  getPartnerProfile,
  updatePartnerProfile,
  type GetReferralsParams,
  type GetCustomersParams,
  type GetCommissionsParams,
  type GetStatementsParams,
} from "@/lib/api/partner-portal";
import type {
  CreateReferralRequest,
  UpdatePartnerProfileRequest,
} from "@/types/partner-portal";

// Dashboard
export function usePartnerDashboard() {
  return useQuery({
    queryKey: queryKeys.partnerPortal.dashboard(),
    queryFn: getPartnerDashboard,
  });
}

// Referrals
export function usePartnerReferrals(params?: GetReferralsParams) {
  return useQuery({
    queryKey: queryKeys.partnerPortal.referrals.list(params),
    queryFn: () => getPartnerReferrals(params),
    placeholderData: (previousData) => previousData,
  });
}

export function useReferral(id: string) {
  return useQuery({
    queryKey: queryKeys.partnerPortal.referrals.detail(id),
    queryFn: () => getReferralById(id),
    enabled: !!id,
  });
}

export function useCreateReferral() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateReferralRequest) => createReferral(data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.partnerPortal.referrals.all(),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.partnerPortal.dashboard(),
      });
    },
  });
}

export function useUpdateReferral() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CreateReferralRequest> }) =>
      updateReferral(id, data),
    onSuccess: (updatedReferral, { id }) => {
      queryClient.setQueryData(
        queryKeys.partnerPortal.referrals.detail(id),
        updatedReferral
      );
      queryClient.invalidateQueries({
        queryKey: queryKeys.partnerPortal.referrals.all(),
      });
    },
  });
}

// Customers
export function usePartnerCustomers(params?: GetCustomersParams) {
  return useQuery({
    queryKey: queryKeys.partnerPortal.customers.list(params),
    queryFn: () => getPartnerCustomers(params),
    placeholderData: (previousData) => previousData,
  });
}

// Commissions
export function usePartnerCommissions(params?: GetCommissionsParams) {
  return useQuery({
    queryKey: queryKeys.partnerPortal.commissions.list(params),
    queryFn: () => getPartnerCommissions(params),
    placeholderData: (previousData) => previousData,
  });
}

// Statements & Payouts
export function usePartnerStatements(params?: GetStatementsParams) {
  return useQuery({
    queryKey: queryKeys.partnerPortal.statements.list(params),
    queryFn: () => getPartnerStatements(params),
    placeholderData: (previousData) => previousData,
  });
}

export function useStatement(id: string) {
  return useQuery({
    queryKey: queryKeys.partnerPortal.statements.detail(id),
    queryFn: () => getStatementById(id),
    enabled: !!id,
  });
}

export function useDownloadStatement() {
  return useMutation({
    mutationFn: downloadStatement,
  });
}

export function usePartnerPayouts() {
  return useQuery({
    queryKey: queryKeys.partnerPortal.payouts(),
    queryFn: getPartnerPayouts,
  });
}

// Profile
export function usePartnerProfile() {
  return useQuery({
    queryKey: queryKeys.partnerPortal.profile(),
    queryFn: getPartnerProfile,
  });
}

export function useUpdatePartnerProfile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: UpdatePartnerProfileRequest) => updatePartnerProfile(data),
    onSuccess: (updatedProfile) => {
      queryClient.setQueryData(queryKeys.partnerPortal.profile(), updatedProfile);
    },
  });
}
