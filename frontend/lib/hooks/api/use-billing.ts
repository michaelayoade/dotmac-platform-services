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

// Additional subscription actions
async function pauseSubscription(id: string): Promise<Subscription> {
  return api.post<Subscription>(`/api/v1/billing/subscriptions/${id}/pause`);
}

async function resumeSubscription(id: string): Promise<Subscription> {
  return api.post<Subscription>(`/api/v1/billing/subscriptions/${id}/resume`);
}

async function changePlan(id: string, newPlanId: string): Promise<Subscription> {
  return api.post<Subscription>(`/api/v1/billing/subscriptions/${id}/change-plan`, {
    plan_id: newPlanId,
  });
}

async function getProrationPreview(id: string, newPlanId: string): Promise<{
  currentPlan: { name: string; price: number };
  newPlan: { name: string; price: number };
  proratedAmount: number;
  effectiveDate: string;
}> {
  return api.post(`/api/v1/billing/subscriptions/${id}/proration-preview`, {
    plan_id: newPlanId,
  });
}

export function usePauseSubscription() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: pauseSubscription,
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

export function useResumeSubscription() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: resumeSubscription,
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

export function useChangePlan() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, newPlanId }: { id: string; newPlanId: string }) =>
      changePlan(id, newPlanId),
    onSuccess: (data) => {
      queryClient.setQueryData(
        queryKeys.billing.subscriptions.detail(data.id),
        data
      );
      queryClient.invalidateQueries({
        queryKey: queryKeys.billing.subscriptions.all(),
      });
      queryClient.invalidateQueries({ queryKey: queryKeys.billing.metrics() });
    },
  });
}

export function useProrationPreview() {
  return useMutation({
    mutationFn: ({ id, newPlanId }: { id: string; newPlanId: string }) =>
      getProrationPreview(id, newPlanId),
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

// ============================================
// Receipts API and Hooks
// ============================================

import type { Receipt, ReceiptStatus } from "@/types/models";

export interface ListReceiptsParams extends ListQueryParams {
  status?: ReceiptStatus;
  customerId?: string;
  dateRange?: DateRange;
}

type ReceiptsResponse = PaginatedResponse<Receipt>;

async function getReceipts(params?: ListReceiptsParams): Promise<ReceiptsResponse> {
  const response = await api.get<unknown>("/api/v1/billing/receipts", {
    params: {
      page: params?.page ?? 1,
      page_size: params?.pageSize ?? 10,
      sort_by: params?.sort?.[0]?.field,
      sort_order: params?.sort?.[0]?.direction,
      status: params?.status,
      customer_id: params?.customerId,
      date_from: params?.dateRange?.start,
      date_to: params?.dateRange?.end,
    },
  });
  return normalizePaginatedResponse<Receipt>(response);
}

async function getReceipt(id: string): Promise<Receipt> {
  return api.get<Receipt>(`/api/v1/billing/receipts/${id}`);
}

async function downloadReceiptPdf(id: string): Promise<Blob> {
  return api.getBlob(`/api/v1/billing/receipts/${id}/pdf`, {
    headers: {
      Accept: "application/pdf",
    },
  });
}

async function emailReceipt(id: string, email?: string): Promise<void> {
  return api.post(`/api/v1/billing/receipts/${id}/email`, { email });
}

export function useReceipts(params?: ListReceiptsParams) {
  return useQuery({
    queryKey: [...queryKeys.billing.all, "receipts", params],
    queryFn: () => getReceipts(params),
    placeholderData: (previousData) => previousData,
  });
}

export function useReceipt(id: string) {
  return useQuery({
    queryKey: [...queryKeys.billing.all, "receipts", id],
    queryFn: () => getReceipt(id),
    enabled: !!id,
  });
}

export function useDownloadReceiptPdf() {
  return useMutation({
    mutationFn: downloadReceiptPdf,
  });
}

export function useEmailReceipt() {
  return useMutation({
    mutationFn: ({ id, email }: { id: string; email?: string }) =>
      emailReceipt(id, email),
  });
}

// ============================================
// Usage Billing API and Hooks
// ============================================

export interface UsageMetrics {
  currentPeriod: {
    apiCalls: number;
    storage: number; // bytes
    bandwidth: number; // bytes
    users: number;
  };
  limits: {
    apiCalls: number;
    storage: number;
    bandwidth: number;
    users: number;
  };
  forecast: {
    apiCalls: number;
    storage: number;
    cost: number;
  };
  costToDate: number;
}

export interface UsageRecord {
  id: string;
  date: string;
  type: "api_calls" | "storage" | "bandwidth" | "users";
  quantity: number;
  unitPrice: number;
  total: number;
}

export interface ListUsageParams extends ListQueryParams {
  type?: UsageRecord["type"];
  dateRange?: DateRange;
}

async function getUsageMetrics(): Promise<UsageMetrics> {
  return api.get<UsageMetrics>("/api/v1/billing/usage/metrics");
}

async function getUsageRecords(params?: ListUsageParams): Promise<PaginatedResponse<UsageRecord>> {
  const response = await api.get<unknown>("/api/v1/billing/usage/records", {
    params: {
      page: params?.page ?? 1,
      page_size: params?.pageSize ?? 20,
      type: params?.type,
      date_from: params?.dateRange?.start,
      date_to: params?.dateRange?.end,
    },
  });
  return normalizePaginatedResponse<UsageRecord>(response);
}

async function getUsageChart(period: "day" | "week" | "month"): Promise<{
  labels: string[];
  datasets: {
    label: string;
    data: number[];
  }[];
}> {
  return api.get("/api/v1/billing/usage/chart", { params: { period } });
}

export function useUsageMetrics() {
  return useQuery({
    queryKey: [...queryKeys.billing.all, "usage", "metrics"],
    queryFn: getUsageMetrics,
    staleTime: 60 * 1000, // 1 minute
  });
}

export function useUsageRecords(params?: ListUsageParams) {
  return useQuery({
    queryKey: [...queryKeys.billing.all, "usage", "records", params],
    queryFn: () => getUsageRecords(params),
    placeholderData: (previousData) => previousData,
  });
}

export function useUsageChart(period: "day" | "week" | "month" = "week") {
  return useQuery({
    queryKey: [...queryKeys.billing.all, "usage", "chart", period],
    queryFn: () => getUsageChart(period),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}
