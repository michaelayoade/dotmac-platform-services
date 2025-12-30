"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  listPayments,
  getPayment,
  recordOfflinePayment,
  getFailedPaymentsSummary,
  type ListPaymentsParams,
  type RecordPaymentRequest,
} from "@/lib/api/payments";

// Query keys
export const paymentKeys = {
  all: ["payments"] as const,
  lists: () => [...paymentKeys.all, "list"] as const,
  list: (params?: ListPaymentsParams) => [...paymentKeys.lists(), params] as const,
  details: () => [...paymentKeys.all, "detail"] as const,
  detail: (id: string) => [...paymentKeys.details(), id] as const,
  failed: () => [...paymentKeys.all, "failed"] as const,
};

// Hooks
export function usePayments(params?: ListPaymentsParams) {
  return useQuery({
    queryKey: paymentKeys.list(params),
    queryFn: () => listPayments(params),
    placeholderData: (previousData) => previousData,
  });
}

export function usePayment(id: string) {
  return useQuery({
    queryKey: paymentKeys.detail(id),
    queryFn: () => getPayment(id),
    enabled: !!id,
  });
}

export function useFailedPaymentsSummary() {
  return useQuery({
    queryKey: paymentKeys.failed(),
    queryFn: getFailedPaymentsSummary,
  });
}

export function useRecordPayment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: RecordPaymentRequest) => recordOfflinePayment(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: paymentKeys.all });
    },
  });
}
