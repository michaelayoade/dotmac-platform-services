"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, normalizePaginatedResponse } from "@/lib/api/client";
import { queryKeys } from "@/lib/api/query-keys";
import type {
  Invoice,
  InvoiceStatus,
  Subscription,
  SubscriptionStatus,
  PaymentMethod,
} from "@/types/models";
import type { PaginatedResponse, ListQueryParams, DateRange } from "@/types/api";

// Types
export interface BillingMetrics {
  mrr: number;
  arr: number;
  mrrGrowth: number;
  totalRevenue: number;
  outstandingAmount: number;
  collectionRate: number;
  averageInvoiceValue: number;
  churnRate: number;
}

export interface ListInvoicesParams extends ListQueryParams {
  status?: InvoiceStatus;
  customerId?: string;
  dateRange?: DateRange;
  minAmount?: number;
  maxAmount?: number;
}

export interface ListSubscriptionsParams extends ListQueryParams {
  status?: SubscriptionStatus;
  planId?: string;
}

export interface CreateInvoiceData {
  customerId: string;
  items: Array<{
    description: string;
    quantity: number;
    unitPrice: number;
  }>;
  dueDate: string;
  notes?: string;
}

export interface PaymentData {
  invoiceId: string;
  amount: number;
  paymentMethodId: string;
}

type InvoicesResponse = PaginatedResponse<Invoice>;
type SubscriptionsResponse = PaginatedResponse<Subscription>;

// API functions
async function getBillingMetrics(): Promise<BillingMetrics> {
  return api.get<BillingMetrics>("/api/v1/billing/metrics");
}

async function getInvoices(params?: ListInvoicesParams): Promise<InvoicesResponse> {
  const response = await api.get<unknown>("/api/v1/billing/invoices", {
    params: {
      page: params?.page ?? 1,
      page_size: params?.pageSize ?? 10,
      sort_by: params?.sort?.[0]?.field,
      sort_order: params?.sort?.[0]?.direction,
      status: params?.status,
      customer_id: params?.customerId,
      date_from: params?.dateRange?.start,
      date_to: params?.dateRange?.end,
      min_amount: params?.minAmount,
      max_amount: params?.maxAmount,
    },
  });
  return normalizePaginatedResponse<Invoice>(response);
}

async function getInvoice(id: string): Promise<Invoice> {
  return api.get<Invoice>(`/api/v1/billing/invoices/${id}`);
}

async function createInvoice(data: CreateInvoiceData): Promise<Invoice> {
  return api.post<Invoice>("/api/v1/billing/invoices", data);
}

async function sendInvoice(id: string): Promise<Invoice> {
  return api.post<Invoice>(`/api/v1/billing/invoices/${id}/send`);
}

async function markInvoicePaid(id: string): Promise<Invoice> {
  return api.post<Invoice>(`/api/v1/billing/invoices/${id}/mark-paid`);
}

async function voidInvoice(id: string): Promise<Invoice> {
  return api.post<Invoice>(`/api/v1/billing/invoices/${id}/void`);
}

async function downloadInvoicePdf(id: string): Promise<Blob> {
  return api.getBlob(`/api/v1/billing/invoices/${id}/pdf`, {
    headers: {
      Accept: "application/pdf",
    },
  });
}

async function getSubscriptions(
  params?: ListSubscriptionsParams
): Promise<SubscriptionsResponse> {
  const response = await api.get<unknown>("/api/v1/billing/subscriptions", {
    params: {
      page: params?.page ?? 1,
      page_size: params?.pageSize ?? 10,
      status: params?.status,
      plan_id: params?.planId,
    },
  });
  return normalizePaginatedResponse<Subscription>(response);
}

async function getSubscription(id: string): Promise<Subscription> {
  return api.get<Subscription>(`/api/v1/billing/subscriptions/${id}`);
}

async function cancelSubscription(id: string): Promise<Subscription> {
  return api.post<Subscription>(`/api/v1/billing/subscriptions/${id}/cancel`);
}

async function getPaymentMethods(): Promise<PaymentMethod[]> {
  return api.get<PaymentMethod[]>("/api/v1/billing/payment-methods");
}

async function setDefaultPaymentMethod(id: string): Promise<PaymentMethod> {
  return api.post<PaymentMethod>(`/api/v1/billing/payment-methods/${id}/default`);
}

async function deletePaymentMethod(id: string): Promise<void> {
  return api.delete<void>(`/api/v1/billing/payment-methods/${id}`);
}

async function processPayment(data: PaymentData): Promise<{ success: boolean; transactionId: string }> {
  return api.post("/api/v1/billing/payments", data);
}

// Hooks
export function useBillingMetrics() {
  return useQuery({
    queryKey: queryKeys.billing.metrics(),
    queryFn: getBillingMetrics,
    staleTime: 60 * 1000, // 1 minute
  });
}

export function useInvoices(params?: ListInvoicesParams) {
  return useQuery({
    queryKey: queryKeys.billing.invoices.list(params),
    queryFn: () => getInvoices(params),
    placeholderData: (previousData) => previousData,
  });
}

export function useInvoice(id: string) {
  return useQuery({
    queryKey: queryKeys.billing.invoices.detail(id),
    queryFn: () => getInvoice(id),
    enabled: !!id,
  });
}

export function useCreateInvoice() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createInvoice,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.billing.invoices.all(),
      });
      queryClient.invalidateQueries({ queryKey: queryKeys.billing.metrics() });
    },
  });
}

export function useSendInvoice() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: sendInvoice,
    onSuccess: (data) => {
      queryClient.setQueryData(
        queryKeys.billing.invoices.detail(data.id),
        data
      );
      queryClient.invalidateQueries({
        queryKey: queryKeys.billing.invoices.all(),
      });
    },
  });
}

export function useMarkInvoicePaid() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: markInvoicePaid,
    onSuccess: (data) => {
      queryClient.setQueryData(
        queryKeys.billing.invoices.detail(data.id),
        data
      );
      queryClient.invalidateQueries({
        queryKey: queryKeys.billing.invoices.all(),
      });
      queryClient.invalidateQueries({ queryKey: queryKeys.billing.metrics() });
    },
  });
}

export function useVoidInvoice() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: voidInvoice,
    onSuccess: (data) => {
      queryClient.setQueryData(
        queryKeys.billing.invoices.detail(data.id),
        data
      );
      queryClient.invalidateQueries({
        queryKey: queryKeys.billing.invoices.all(),
      });
      queryClient.invalidateQueries({ queryKey: queryKeys.billing.metrics() });
    },
  });
}

export function useDownloadInvoicePdf() {
  return useMutation({
    mutationFn: downloadInvoicePdf,
  });
}

export function useSubscriptions(params?: ListSubscriptionsParams) {
  return useQuery({
    queryKey: queryKeys.billing.subscriptions.list(params),
    queryFn: () => getSubscriptions(params),
  });
}

export function useSubscription(id: string) {
  return useQuery({
    queryKey: queryKeys.billing.subscriptions.detail(id),
    queryFn: () => getSubscription(id),
    enabled: !!id,
  });
}

export function useCancelSubscription() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: cancelSubscription,
    onSuccess: (data) => {
      queryClient.setQueryData(
        queryKeys.billing.subscriptions.detail(data.id),
        data
      );
      queryClient.invalidateQueries({
        queryKey: queryKeys.billing.subscriptions.all(),
      });
    },
  });
}

export function usePaymentMethods() {
  return useQuery({
    queryKey: [...queryKeys.billing.all, "payment-methods"],
    queryFn: getPaymentMethods,
  });
}

export function useSetDefaultPaymentMethod() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: setDefaultPaymentMethod,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: [...queryKeys.billing.all, "payment-methods"],
      });
    },
  });
}

export function useDeletePaymentMethod() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deletePaymentMethod,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: [...queryKeys.billing.all, "payment-methods"],
      });
    },
  });
}

export function useProcessPayment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: processPayment,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.billing.invoices.all(),
      });
      queryClient.invalidateQueries({ queryKey: queryKeys.billing.metrics() });
    },
  });
}
