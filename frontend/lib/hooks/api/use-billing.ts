"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, normalizePaginatedResponse } from "@/lib/api/client";
import { queryKeys } from "@/lib/api/query-keys";
import { getBillingDashboard } from "@/lib/api/billing";
import type {
  Invoice,
  InvoiceStatus,
  Subscription,
  SubscriptionStatus,
  PaymentMethod,
} from "@/types/models";
import type { PaginatedResponse, ListQueryParams, DateRange } from "@/types/api";
import type { DashboardQueryParams } from "@/lib/api/types/dashboard";

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

export function useBillingDashboard(params?: DashboardQueryParams) {
  return useQuery({
    queryKey: queryKeys.billing.dashboard(params),
    queryFn: () => getBillingDashboard(params),
    staleTime: 60 * 1000, // 1 minute
  });
}

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

// ============================================
// Credit Notes API and Hooks
// ============================================

export type CreditNoteStatus = "draft" | "issued" | "applied" | "voided";

export interface CreditNote {
  id: string;
  number: string;
  customerId: string;
  customerName: string;
  invoiceId?: string;
  invoiceNumber?: string;
  amount: number;
  currency: string;
  status: CreditNoteStatus;
  reason: string;
  lineItems: CreditNoteLineItem[];
  appliedAmount: number;
  remainingAmount: number;
  issueDate?: string;
  voidedDate?: string;
  createdAt: string;
  updatedAt: string;
}

export interface CreditNoteLineItem {
  id: string;
  description: string;
  quantity: number;
  unitPrice: number;
  total: number;
}

export interface ListCreditNotesParams extends ListQueryParams {
  status?: CreditNoteStatus;
  customerId?: string;
  dateRange?: DateRange;
}

export interface CreateCreditNoteData {
  customerId: string;
  invoiceId?: string;
  reason: string;
  lineItems: Array<{
    description: string;
    quantity: number;
    unitPrice: number;
  }>;
}

export interface UpdateCreditNoteData {
  reason?: string;
  lineItems?: Array<{
    description: string;
    quantity: number;
    unitPrice: number;
  }>;
}

export interface ApplyCreditNoteData {
  invoiceId: string;
  amount: number;
}

type CreditNotesResponse = PaginatedResponse<CreditNote>;

async function getCreditNotes(params?: ListCreditNotesParams): Promise<CreditNotesResponse> {
  const response = await api.get<unknown>("/api/v1/billing/credit-notes", {
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
  return normalizePaginatedResponse<CreditNote>(response);
}

async function getCreditNote(id: string): Promise<CreditNote> {
  return api.get<CreditNote>(`/api/v1/billing/credit-notes/${id}`);
}

async function createCreditNote(data: CreateCreditNoteData): Promise<CreditNote> {
  return api.post<CreditNote>("/api/v1/billing/credit-notes", data);
}

async function updateCreditNote(id: string, data: UpdateCreditNoteData): Promise<CreditNote> {
  return api.put<CreditNote>(`/api/v1/billing/credit-notes/${id}`, data);
}

async function issueCreditNote(id: string): Promise<CreditNote> {
  return api.post<CreditNote>(`/api/v1/billing/credit-notes/${id}/issue`);
}

async function voidCreditNote(id: string): Promise<CreditNote> {
  return api.post<CreditNote>(`/api/v1/billing/credit-notes/${id}/void`);
}

async function applyCreditNote(id: string, data: ApplyCreditNoteData): Promise<CreditNote> {
  return api.post<CreditNote>(`/api/v1/billing/credit-notes/${id}/apply`, data);
}

async function downloadCreditNotePdf(id: string): Promise<Blob> {
  return api.getBlob(`/api/v1/billing/credit-notes/${id}/pdf`, {
    headers: {
      Accept: "application/pdf",
    },
  });
}

async function getCustomerOpenInvoices(customerId: string): Promise<Invoice[]> {
  return api.get<Invoice[]>(`/api/v1/billing/customers/${customerId}/invoices/open`);
}

export function useCreditNotes(params?: ListCreditNotesParams) {
  return useQuery({
    queryKey: queryKeys.billing.creditNotes.list(params),
    queryFn: () => getCreditNotes(params),
    placeholderData: (previousData) => previousData,
  });
}

export function useCreditNote(id: string) {
  return useQuery({
    queryKey: queryKeys.billing.creditNotes.detail(id),
    queryFn: () => getCreditNote(id),
    enabled: !!id,
  });
}

export function useCreateCreditNote() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createCreditNote,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.billing.creditNotes.all(),
      });
    },
  });
}

export function useUpdateCreditNote() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateCreditNoteData }) =>
      updateCreditNote(id, data),
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.billing.creditNotes.detail(data.id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.billing.creditNotes.all(),
      });
    },
  });
}

export function useIssueCreditNote() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: issueCreditNote,
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.billing.creditNotes.detail(data.id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.billing.creditNotes.all(),
      });
    },
  });
}

export function useVoidCreditNote() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: voidCreditNote,
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.billing.creditNotes.detail(data.id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.billing.creditNotes.all(),
      });
    },
  });
}

export function useApplyCreditNote() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ApplyCreditNoteData }) =>
      applyCreditNote(id, data),
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.billing.creditNotes.detail(data.id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.billing.creditNotes.all(),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.billing.invoices.all(),
      });
    },
  });
}

export function useDownloadCreditNotePdf() {
  return useMutation({
    mutationFn: downloadCreditNotePdf,
  });
}

export function useCustomerOpenInvoices(customerId: string) {
  return useQuery({
    queryKey: [...queryKeys.billing.invoices.all(), "open", customerId],
    queryFn: () => getCustomerOpenInvoices(customerId),
    enabled: !!customerId,
  });
}

// ============================================
// Dunning API and Hooks
// ============================================

export type DunningCampaignStatus = "active" | "paused" | "draft" | "archived";
export type DunningExecutionStatus = "pending" | "in_progress" | "completed" | "failed" | "cancelled";
export type DunningStepAction = "email" | "sms" | "in_app" | "webhook" | "suspend_service";

export interface DunningStep {
  id: string;
  order: number;
  delayDays: number;
  action: DunningStepAction;
  templateId?: string;
  subject?: string;
  message?: string;
  webhookUrl?: string;
}

export interface DunningCampaign {
  id: string;
  name: string;
  description?: string;
  status: DunningCampaignStatus;
  triggerDaysAfterDue: number;
  steps: DunningStep[];
  autoSuspendAfterDays?: number;
  autoWriteOffAfterDays?: number;
  excludeVipCustomers: boolean;
  excludeAmountBelow?: number;
  createdAt: string;
  updatedAt: string;
  stats?: {
    totalExecutions: number;
    activeExecutions: number;
    recoveredAmount: number;
    recoveryRate: number;
  };
}

export interface DunningExecution {
  id: string;
  campaignId: string;
  campaignName: string;
  invoiceId: string;
  invoiceNumber: string;
  customerId: string;
  customerName: string;
  customerEmail: string;
  amount: number;
  currency: string;
  status: DunningExecutionStatus;
  currentStep: number;
  totalSteps: number;
  startedAt: string;
  completedAt?: string;
  nextActionAt?: string;
  lastActionAt?: string;
  history: DunningExecutionEvent[];
}

export interface DunningExecutionEvent {
  id: string;
  stepNumber: number;
  action: DunningStepAction;
  status: "success" | "failed";
  executedAt: string;
  details?: string;
  error?: string;
}

export interface DunningAnalytics {
  summary: {
    totalActiveExecutions: number;
    totalRecoveredThisMonth: number;
    averageRecoveryDays: number;
    overallRecoveryRate: number;
  };
  byStatus: Record<DunningExecutionStatus, number>;
  byCampaign: Array<{
    campaignId: string;
    campaignName: string;
    executions: number;
    recovered: number;
    recoveryRate: number;
  }>;
  recentRecoveries: Array<{
    invoiceId: string;
    invoiceNumber: string;
    customerName: string;
    amount: number;
    recoveredAt: string;
  }>;
  performanceTrend: Array<{
    date: string;
    started: number;
    recovered: number;
    failed: number;
  }>;
}

export interface ListDunningCampaignsParams extends ListQueryParams {
  status?: DunningCampaignStatus;
}

export interface ListDunningExecutionsParams extends ListQueryParams {
  campaignId?: string;
  status?: DunningExecutionStatus;
  customerId?: string;
  dateRange?: DateRange;
}

export interface CreateDunningCampaignData {
  name: string;
  description?: string;
  triggerDaysAfterDue: number;
  steps: Omit<DunningStep, "id">[];
  autoSuspendAfterDays?: number;
  autoWriteOffAfterDays?: number;
  excludeVipCustomers?: boolean;
  excludeAmountBelow?: number;
}

export interface UpdateDunningCampaignData extends Partial<CreateDunningCampaignData> {
  status?: DunningCampaignStatus;
}

// Dunning API functions
async function getDunningCampaigns(params?: ListDunningCampaignsParams): Promise<PaginatedResponse<DunningCampaign>> {
  const response = await api.get<unknown>("/api/v1/billing/dunning/campaigns", {
    params: {
      page: params?.page ?? 1,
      page_size: params?.pageSize ?? 10,
      status: params?.status,
    },
  });
  return normalizePaginatedResponse<DunningCampaign>(response);
}

async function getDunningCampaign(id: string): Promise<DunningCampaign> {
  return api.get<DunningCampaign>(`/api/v1/billing/dunning/campaigns/${id}`);
}

async function createDunningCampaign(data: CreateDunningCampaignData): Promise<DunningCampaign> {
  return api.post<DunningCampaign>("/api/v1/billing/dunning/campaigns", data);
}

async function updateDunningCampaign(id: string, data: UpdateDunningCampaignData): Promise<DunningCampaign> {
  return api.put<DunningCampaign>(`/api/v1/billing/dunning/campaigns/${id}`, data);
}

async function deleteDunningCampaign(id: string): Promise<void> {
  return api.delete<void>(`/api/v1/billing/dunning/campaigns/${id}`);
}

async function activateDunningCampaign(id: string): Promise<DunningCampaign> {
  return api.post<DunningCampaign>(`/api/v1/billing/dunning/campaigns/${id}/activate`);
}

async function pauseDunningCampaign(id: string): Promise<DunningCampaign> {
  return api.post<DunningCampaign>(`/api/v1/billing/dunning/campaigns/${id}/pause`);
}

async function getDunningExecutions(params?: ListDunningExecutionsParams): Promise<PaginatedResponse<DunningExecution>> {
  const response = await api.get<unknown>("/api/v1/billing/dunning/executions", {
    params: {
      page: params?.page ?? 1,
      page_size: params?.pageSize ?? 10,
      campaign_id: params?.campaignId,
      status: params?.status,
      customer_id: params?.customerId,
      date_from: params?.dateRange?.start,
      date_to: params?.dateRange?.end,
    },
  });
  return normalizePaginatedResponse<DunningExecution>(response);
}

async function getDunningExecution(id: string): Promise<DunningExecution> {
  return api.get<DunningExecution>(`/api/v1/billing/dunning/executions/${id}`);
}

async function cancelDunningExecution(id: string): Promise<DunningExecution> {
  return api.post<DunningExecution>(`/api/v1/billing/dunning/executions/${id}/cancel`);
}

async function getDunningAnalytics(params?: { dateRange?: DateRange }): Promise<DunningAnalytics> {
  return api.get<DunningAnalytics>("/api/v1/billing/dunning/analytics", {
    params: {
      date_from: params?.dateRange?.start,
      date_to: params?.dateRange?.end,
    },
  });
}

// Dunning Hooks
export function useDunningCampaigns(params?: ListDunningCampaignsParams) {
  return useQuery({
    queryKey: queryKeys.billing.dunning.campaigns.list(params),
    queryFn: () => getDunningCampaigns(params),
    placeholderData: (previousData) => previousData,
  });
}

export function useDunningCampaign(id: string) {
  return useQuery({
    queryKey: queryKeys.billing.dunning.campaigns.detail(id),
    queryFn: () => getDunningCampaign(id),
    enabled: !!id,
  });
}

export function useCreateDunningCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createDunningCampaign,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.billing.dunning.campaigns.all(),
      });
    },
  });
}

export function useUpdateDunningCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateDunningCampaignData }) =>
      updateDunningCampaign(id, data),
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.billing.dunning.campaigns.detail(data.id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.billing.dunning.campaigns.all(),
      });
    },
  });
}

export function useDeleteDunningCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteDunningCampaign,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.billing.dunning.campaigns.all(),
      });
    },
  });
}

export function useCloneDunningCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      // Fetch the campaign to clone
      const campaign = await getDunningCampaign(id);
      // Create a new campaign with the same data
      const cloneData: CreateDunningCampaignData = {
        name: `${campaign.name} (Copy)`,
        description: campaign.description,
        triggerDaysAfterDue: campaign.triggerDaysAfterDue,
        steps: campaign.steps.map((step) => ({
          order: step.order,
          delayDays: step.delayDays,
          action: step.action,
          templateId: step.templateId,
          subject: step.subject,
          message: step.message,
          webhookUrl: step.webhookUrl,
        })),
        autoSuspendAfterDays: campaign.autoSuspendAfterDays,
        autoWriteOffAfterDays: campaign.autoWriteOffAfterDays,
        excludeVipCustomers: campaign.excludeVipCustomers,
        excludeAmountBelow: campaign.excludeAmountBelow,
      };
      return createDunningCampaign(cloneData);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.billing.dunning.campaigns.all(),
      });
    },
  });
}

export function useActivateDunningCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: activateDunningCampaign,
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.billing.dunning.campaigns.detail(data.id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.billing.dunning.campaigns.all(),
      });
    },
  });
}

export function usePauseDunningCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: pauseDunningCampaign,
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.billing.dunning.campaigns.detail(data.id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.billing.dunning.campaigns.all(),
      });
    },
  });
}

export function useDunningExecutions(params?: ListDunningExecutionsParams) {
  return useQuery({
    queryKey: queryKeys.billing.dunning.executions.list(params),
    queryFn: () => getDunningExecutions(params),
    placeholderData: (previousData) => previousData,
  });
}

export function useDunningExecution(id: string) {
  return useQuery({
    queryKey: queryKeys.billing.dunning.executions.detail(id),
    queryFn: () => getDunningExecution(id),
    enabled: !!id,
  });
}

export function useCancelDunningExecution() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: cancelDunningExecution,
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.billing.dunning.executions.detail(data.id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.billing.dunning.executions.all(),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.billing.dunning.analytics(),
      });
    },
  });
}

export function useDunningAnalytics(dateRange?: DateRange) {
  return useQuery({
    queryKey: queryKeys.billing.dunning.analytics({ dateRange }),
    queryFn: () => getDunningAnalytics({ dateRange }),
    staleTime: 60 * 1000, // 1 minute
  });
}

// ============================================
// Pricing Rules API and Hooks
// ============================================

export type PricingRuleType = "discount" | "markup" | "override" | "bundle" | "volume" | "tiered";
export type PricingRuleStatus = "active" | "inactive" | "scheduled" | "expired";
export type PricingConditionType = "customer_segment" | "product_category" | "quantity" | "date_range" | "coupon_code" | "subscription_tier";

export interface PricingCondition {
  id: string;
  type: PricingConditionType;
  operator: "equals" | "not_equals" | "greater_than" | "less_than" | "in" | "not_in" | "between";
  value: string | number | string[];
}

export interface PricingRule {
  id: string;
  name: string;
  description?: string;
  type: PricingRuleType;
  status: PricingRuleStatus;
  priority: number;
  conditions: PricingCondition[];
  discountType?: "percentage" | "fixed_amount";
  discountValue?: number;
  overridePrice?: number;
  volumeTiers?: Array<{
    minQuantity: number;
    maxQuantity?: number;
    discountPercent: number;
  }>;
  applicableProducts?: string[];
  applicableCategories?: string[];
  startDate?: string;
  endDate?: string;
  usageLimit?: number;
  usageCount: number;
  createdAt: string;
  updatedAt: string;
}

export interface PricingConflict {
  id: string;
  ruleIds: string[];
  ruleNames: string[];
  conflictType: "overlap" | "contradiction" | "priority";
  description: string;
  severity: "low" | "medium" | "high";
  suggestedResolution?: string;
}

export interface PricingCalculation {
  originalPrice: number;
  finalPrice: number;
  appliedRules: Array<{
    ruleId: string;
    ruleName: string;
    discountAmount: number;
  }>;
  savings: number;
  savingsPercent: number;
}

export interface ListPricingRulesParams extends ListQueryParams {
  type?: PricingRuleType;
  status?: PricingRuleStatus;
}

export interface CreatePricingRuleData {
  name: string;
  description?: string;
  type: PricingRuleType;
  priority: number;
  conditions: Omit<PricingCondition, "id">[];
  discountType?: "percentage" | "fixed_amount";
  discountValue?: number;
  overridePrice?: number;
  volumeTiers?: Array<{
    minQuantity: number;
    maxQuantity?: number;
    discountPercent: number;
  }>;
  applicableProducts?: string[];
  applicableCategories?: string[];
  startDate?: string;
  endDate?: string;
  usageLimit?: number;
}

export interface UpdatePricingRuleData extends Partial<CreatePricingRuleData> {
  status?: PricingRuleStatus;
}

export interface CalculatePriceParams {
  productId: string;
  quantity: number;
  customerId?: string;
  couponCode?: string;
}

// Pricing API functions
async function getPricingRules(params?: ListPricingRulesParams): Promise<PaginatedResponse<PricingRule>> {
  const response = await api.get<unknown>("/api/v1/billing/pricing/rules", {
    params: {
      page: params?.page ?? 1,
      page_size: params?.pageSize ?? 10,
      type: params?.type,
      status: params?.status,
    },
  });
  return normalizePaginatedResponse<PricingRule>(response);
}

async function getPricingRule(id: string): Promise<PricingRule> {
  return api.get<PricingRule>(`/api/v1/billing/pricing/rules/${id}`);
}

async function createPricingRule(data: CreatePricingRuleData): Promise<PricingRule> {
  return api.post<PricingRule>("/api/v1/billing/pricing/rules", data);
}

async function updatePricingRule(id: string, data: UpdatePricingRuleData): Promise<PricingRule> {
  return api.put<PricingRule>(`/api/v1/billing/pricing/rules/${id}`, data);
}

async function deletePricingRule(id: string): Promise<void> {
  return api.delete<void>(`/api/v1/billing/pricing/rules/${id}`);
}

async function activatePricingRule(id: string): Promise<PricingRule> {
  return api.post<PricingRule>(`/api/v1/billing/pricing/rules/${id}/activate`);
}

async function deactivatePricingRule(id: string): Promise<PricingRule> {
  return api.post<PricingRule>(`/api/v1/billing/pricing/rules/${id}/deactivate`);
}

async function calculatePrice(params: CalculatePriceParams): Promise<PricingCalculation> {
  return api.post<PricingCalculation>("/api/v1/billing/pricing/calculate", params);
}

async function getPricingConflicts(): Promise<PricingConflict[]> {
  return api.get<PricingConflict[]>("/api/v1/billing/pricing/conflicts");
}

async function resolvePricingConflict(conflictId: string, resolution: { priority?: number; disable?: string[] }): Promise<void> {
  return api.post<void>(`/api/v1/billing/pricing/conflicts/${conflictId}/resolve`, resolution);
}

// Pricing Hooks
export function usePricingRules(params?: ListPricingRulesParams) {
  return useQuery({
    queryKey: queryKeys.billing.pricing.rules.list(params),
    queryFn: () => getPricingRules(params),
    placeholderData: (previousData) => previousData,
  });
}

export function usePricingRule(id: string) {
  return useQuery({
    queryKey: queryKeys.billing.pricing.rules.detail(id),
    queryFn: () => getPricingRule(id),
    enabled: !!id,
  });
}

export function useCreatePricingRule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createPricingRule,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.billing.pricing.rules.all(),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.billing.pricing.conflicts(),
      });
    },
  });
}

export function useUpdatePricingRule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdatePricingRuleData }) =>
      updatePricingRule(id, data),
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.billing.pricing.rules.detail(data.id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.billing.pricing.rules.all(),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.billing.pricing.conflicts(),
      });
    },
  });
}

export function useDeletePricingRule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deletePricingRule,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.billing.pricing.rules.all(),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.billing.pricing.conflicts(),
      });
    },
  });
}

export function useActivatePricingRule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: activatePricingRule,
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.billing.pricing.rules.detail(data.id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.billing.pricing.rules.all(),
      });
    },
  });
}

export function useDeactivatePricingRule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deactivatePricingRule,
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.billing.pricing.rules.detail(data.id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.billing.pricing.rules.all(),
      });
    },
  });
}

export function useCalculatePrice() {
  return useMutation({
    mutationFn: calculatePrice,
  });
}

export function usePricingConflicts() {
  return useQuery({
    queryKey: queryKeys.billing.pricing.conflicts(),
    queryFn: getPricingConflicts,
    staleTime: 60 * 1000,
  });
}

export function useResolvePricingConflict() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ conflictId, resolution }: { conflictId: string; resolution: { priority?: number; disable?: string[] } }) =>
      resolvePricingConflict(conflictId, resolution),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.billing.pricing.conflicts(),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.billing.pricing.rules.all(),
      });
    },
  });
}

// ============================================
// Billing Settings API and Hooks
// ============================================

export interface CompanySettings {
  companyName: string;
  legalName?: string;
  taxId?: string;
  address: {
    street: string;
    city: string;
    state: string;
    postalCode: string;
    country: string;
  };
  email: string;
  phone?: string;
  website?: string;
  logo?: string;
}

export interface TaxSettings {
  taxEnabled: boolean;
  defaultTaxRate: number;
  taxInclusive: boolean;
  taxId?: string;
  taxRegion: string;
  customTaxRates: Array<{
    id: string;
    name: string;
    rate: number;
    region?: string;
    productCategories?: string[];
  }>;
}

export interface PaymentSettings {
  defaultCurrency: string;
  supportedCurrencies: string[];
  paymentMethods: Array<{
    id: string;
    type: "stripe" | "paypal" | "bank_transfer" | "manual";
    enabled: boolean;
    isDefault: boolean;
    config?: Record<string, unknown>;
  }>;
  autoRetry: {
    enabled: boolean;
    maxAttempts: number;
    intervalDays: number;
  };
  invoiceDueDays: number;
}

export interface InvoiceTemplate {
  id: string;
  name: string;
  isDefault: boolean;
  logoPosition: "left" | "center" | "right";
  primaryColor: string;
  footerText?: string;
  termsAndConditions?: string;
  showTaxBreakdown: boolean;
  showPaymentInstructions: boolean;
}

export interface NotificationSettings {
  emailNotifications: {
    invoiceCreated: boolean;
    invoiceSent: boolean;
    paymentReceived: boolean;
    paymentFailed: boolean;
    subscriptionRenewing: boolean;
    subscriptionCancelled: boolean;
  };
  reminderSchedule: {
    beforeDue: number[];
    afterDue: number[];
  };
}

export interface BillingSettings {
  company: CompanySettings;
  tax: TaxSettings;
  payment: PaymentSettings;
  templates: InvoiceTemplate[];
  notifications: NotificationSettings;
}

// Billing Settings API functions
async function getBillingSettings(): Promise<BillingSettings> {
  return api.get<BillingSettings>("/api/v1/billing/settings");
}

async function updateCompanySettings(data: Partial<CompanySettings>): Promise<CompanySettings> {
  return api.put<CompanySettings>("/api/v1/billing/settings/company", data);
}

async function updateTaxSettings(data: Partial<TaxSettings>): Promise<TaxSettings> {
  return api.put<TaxSettings>("/api/v1/billing/settings/tax", data);
}

async function updatePaymentSettings(data: Partial<PaymentSettings>): Promise<PaymentSettings> {
  return api.put<PaymentSettings>("/api/v1/billing/settings/payment", data);
}

async function updateNotificationSettings(data: Partial<NotificationSettings>): Promise<NotificationSettings> {
  return api.put<NotificationSettings>("/api/v1/billing/settings/notifications", data);
}

async function getInvoiceTemplates(): Promise<InvoiceTemplate[]> {
  return api.get<InvoiceTemplate[]>("/api/v1/billing/settings/templates");
}

async function updateInvoiceTemplate(id: string, data: Partial<InvoiceTemplate>): Promise<InvoiceTemplate> {
  return api.put<InvoiceTemplate>(`/api/v1/billing/settings/templates/${id}`, data);
}

// Billing Settings Hooks
export function useBillingSettings() {
  return useQuery({
    queryKey: queryKeys.billing.settings.all(),
    queryFn: getBillingSettings,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useUpdateCompanySettings() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: updateCompanySettings,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.billing.settings.all(),
      });
    },
  });
}

export function useUpdateTaxSettings() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: updateTaxSettings,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.billing.settings.all(),
      });
    },
  });
}

export function useUpdatePaymentSettings() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: updatePaymentSettings,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.billing.settings.all(),
      });
    },
  });
}

export function useUpdateNotificationSettings() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: updateNotificationSettings,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.billing.settings.all(),
      });
    },
  });
}

export function useInvoiceTemplates() {
  return useQuery({
    queryKey: queryKeys.billing.settings.invoiceTemplates(),
    queryFn: getInvoiceTemplates,
  });
}

export function useUpdateInvoiceTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<InvoiceTemplate> }) =>
      updateInvoiceTemplate(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.billing.settings.invoiceTemplates(),
      });
    },
  });
}

// ============================================
// Add-ons API and Hooks
// ============================================

export interface Addon {
  id: string;
  name: string;
  description: string;
  category: string;
  icon?: string;
  price: number;
  billingCycle: "monthly" | "yearly" | "one_time";
  currency: string;
  features: string[];
  limits?: Record<string, number>;
  isPopular?: boolean;
  isFeatured?: boolean;
}

export interface ActiveAddon {
  id: string;
  addonId: string;
  addon: Addon;
  status: "active" | "cancelled" | "expired";
  purchasedAt: string;
  expiresAt?: string;
  nextBillingDate?: string;
  usage?: {
    current: number;
    limit: number;
    unit: string;
  };
}

export interface ListAddonsParams extends ListQueryParams {
  category?: string;
}

// Add-ons API functions
async function getAddonsMarketplace(params?: ListAddonsParams): Promise<PaginatedResponse<Addon>> {
  const response = await api.get<unknown>("/api/v1/billing/addons/marketplace", {
    params: {
      page: params?.page ?? 1,
      page_size: params?.pageSize ?? 20,
      category: params?.category,
    },
  });
  return normalizePaginatedResponse<Addon>(response);
}

async function getAddon(id: string): Promise<Addon> {
  return api.get<Addon>(`/api/v1/billing/addons/${id}`);
}

async function getActiveAddons(): Promise<ActiveAddon[]> {
  return api.get<ActiveAddon[]>("/api/v1/billing/addons/active");
}

async function purchaseAddon(addonId: string): Promise<ActiveAddon> {
  return api.post<ActiveAddon>(`/api/v1/billing/addons/${addonId}/purchase`);
}

async function cancelAddon(activeAddonId: string): Promise<ActiveAddon> {
  return api.post<ActiveAddon>(`/api/v1/billing/addons/active/${activeAddonId}/cancel`);
}

async function getAddonUsage(activeAddonId: string): Promise<{
  current: number;
  limit: number;
  unit: string;
  history: Array<{ date: string; value: number }>;
}> {
  return api.get(`/api/v1/billing/addons/active/${activeAddonId}/usage`);
}

// Add-ons Hooks
export function useAddonsMarketplace(params?: ListAddonsParams) {
  return useQuery({
    queryKey: queryKeys.billing.addons.marketplace(params),
    queryFn: () => getAddonsMarketplace(params),
    placeholderData: (previousData) => previousData,
  });
}

export function useAddon(id: string) {
  return useQuery({
    queryKey: queryKeys.billing.addons.detail(id),
    queryFn: () => getAddon(id),
    enabled: !!id,
  });
}

export function useActiveAddons() {
  return useQuery({
    queryKey: queryKeys.billing.addons.active(),
    queryFn: getActiveAddons,
  });
}

export function usePurchaseAddon() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: purchaseAddon,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.billing.addons.active(),
      });
    },
  });
}

export function useCancelAddon() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: cancelAddon,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.billing.addons.active(),
      });
    },
  });
}

export function useAddonUsage(activeAddonId: string) {
  return useQuery({
    queryKey: queryKeys.billing.addons.usage(activeAddonId),
    queryFn: () => getAddonUsage(activeAddonId),
    enabled: !!activeAddonId,
  });
}

// ============================================
// Bank Accounts API and Hooks
// ============================================

export interface BankAccount {
  id: string;
  name: string;
  accountNumber: string;
  bankName: string;
  type: "checking" | "savings" | "cash";
  currency: string;
  balance: number;
  isDefault: boolean;
  createdAt: string;
  lastReconciled?: string;
}

export interface BankTransaction {
  id: string;
  accountId: string;
  type: "deposit" | "withdrawal" | "transfer" | "fee" | "interest";
  amount: number;
  currency: string;
  description: string;
  reference?: string;
  date: string;
  reconciled: boolean;
  invoiceId?: string;
  paymentId?: string;
}

export interface ManualPayment {
  id: string;
  invoiceId: string;
  invoiceNumber: string;
  customerName: string;
  amount: number;
  currency: string;
  method: "cash" | "check" | "bank_transfer" | "other";
  reference?: string;
  notes?: string;
  receivedAt: string;
  recordedBy: string;
  bankAccountId?: string;
}

export interface CashRegister {
  id: string;
  name: string;
  location?: string;
  openingBalance: number;
  currentBalance: number;
  currency: string;
  status: "open" | "closed";
  openedAt?: string;
  openedBy?: string;
  closedAt?: string;
  closedBy?: string;
  expectedBalance?: number;
  variance?: number;
}

export interface ListBankTransactionsParams extends ListQueryParams {
  type?: BankTransaction["type"];
  reconciled?: boolean;
  dateRange?: DateRange;
}

export interface ListManualPaymentsParams extends ListQueryParams {
  method?: ManualPayment["method"];
  dateRange?: DateRange;
}

export interface RecordManualPaymentData {
  invoiceId: string;
  amount: number;
  method: ManualPayment["method"];
  reference?: string;
  notes?: string;
  receivedAt: string;
  bankAccountId?: string;
}

// Bank Accounts API functions
async function getBankAccounts(): Promise<BankAccount[]> {
  return api.get<BankAccount[]>("/api/v1/billing/bank-accounts");
}

async function getBankAccount(id: string): Promise<BankAccount> {
  return api.get<BankAccount>(`/api/v1/billing/bank-accounts/${id}`);
}

async function createBankAccount(data: Omit<BankAccount, "id" | "balance" | "createdAt" | "lastReconciled">): Promise<BankAccount> {
  return api.post<BankAccount>("/api/v1/billing/bank-accounts", data);
}

async function updateBankAccount(id: string, data: Partial<BankAccount>): Promise<BankAccount> {
  return api.put<BankAccount>(`/api/v1/billing/bank-accounts/${id}`, data);
}

async function getBankTransactions(accountId: string, params?: ListBankTransactionsParams): Promise<PaginatedResponse<BankTransaction>> {
  const response = await api.get<unknown>(`/api/v1/billing/bank-accounts/${accountId}/transactions`, {
    params: {
      page: params?.page ?? 1,
      page_size: params?.pageSize ?? 20,
      type: params?.type,
      reconciled: params?.reconciled,
      date_from: params?.dateRange?.start,
      date_to: params?.dateRange?.end,
    },
  });
  return normalizePaginatedResponse<BankTransaction>(response);
}

async function reconcileTransactions(accountId: string, transactionIds: string[]): Promise<void> {
  return api.post(`/api/v1/billing/bank-accounts/${accountId}/reconcile`, { transaction_ids: transactionIds });
}

async function getManualPayments(params?: ListManualPaymentsParams): Promise<PaginatedResponse<ManualPayment>> {
  const response = await api.get<unknown>("/api/v1/billing/manual-payments", {
    params: {
      page: params?.page ?? 1,
      page_size: params?.pageSize ?? 20,
      method: params?.method,
      date_from: params?.dateRange?.start,
      date_to: params?.dateRange?.end,
    },
  });
  return normalizePaginatedResponse<ManualPayment>(response);
}

async function recordManualPayment(data: RecordManualPaymentData): Promise<ManualPayment> {
  return api.post<ManualPayment>("/api/v1/billing/manual-payments", data);
}

async function getCashRegisters(): Promise<CashRegister[]> {
  return api.get<CashRegister[]>("/api/v1/billing/cash-registers");
}

async function getCashRegister(id: string): Promise<CashRegister> {
  return api.get<CashRegister>(`/api/v1/billing/cash-registers/${id}`);
}

async function openCashRegister(id: string, openingBalance: number): Promise<CashRegister> {
  return api.post<CashRegister>(`/api/v1/billing/cash-registers/${id}/open`, { opening_balance: openingBalance });
}

async function closeCashRegister(id: string, expectedBalance: number): Promise<CashRegister> {
  return api.post<CashRegister>(`/api/v1/billing/cash-registers/${id}/close`, { expected_balance: expectedBalance });
}

// Bank Accounts Hooks
export function useBankAccounts() {
  return useQuery({
    queryKey: queryKeys.billing.bankAccounts.all(),
    queryFn: getBankAccounts,
  });
}

export function useBankAccount(id: string) {
  return useQuery({
    queryKey: queryKeys.billing.bankAccounts.detail(id),
    queryFn: () => getBankAccount(id),
    enabled: !!id,
  });
}

export function useCreateBankAccount() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createBankAccount,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.billing.bankAccounts.all(),
      });
    },
  });
}

export function useUpdateBankAccount() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<BankAccount> }) =>
      updateBankAccount(id, data),
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.billing.bankAccounts.detail(data.id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.billing.bankAccounts.all(),
      });
    },
  });
}

export function useBankTransactions(accountId: string, params?: ListBankTransactionsParams) {
  return useQuery({
    queryKey: queryKeys.billing.bankAccounts.transactions(accountId, params),
    queryFn: () => getBankTransactions(accountId, params),
    enabled: !!accountId,
    placeholderData: (previousData) => previousData,
  });
}

export function useReconcileTransactions() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ accountId, transactionIds }: { accountId: string; transactionIds: string[] }) =>
      reconcileTransactions(accountId, transactionIds),
    onSuccess: (_, { accountId }) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.billing.bankAccounts.transactions(accountId),
      });
    },
  });
}

export function useManualPayments(params?: ListManualPaymentsParams) {
  return useQuery({
    queryKey: queryKeys.billing.bankAccounts.manualPayments.list(params),
    queryFn: () => getManualPayments(params),
    placeholderData: (previousData) => previousData,
  });
}

export function useRecordManualPayment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: recordManualPayment,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.billing.bankAccounts.manualPayments.all(),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.billing.invoices.all(),
      });
    },
  });
}

export function useCashRegisters() {
  return useQuery({
    queryKey: queryKeys.billing.bankAccounts.cashRegisters.all(),
    queryFn: getCashRegisters,
  });
}

export function useCashRegister(id: string) {
  return useQuery({
    queryKey: queryKeys.billing.bankAccounts.cashRegisters.detail(id),
    queryFn: () => getCashRegister(id),
    enabled: !!id,
  });
}

export function useOpenCashRegister() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, openingBalance }: { id: string; openingBalance: number }) =>
      openCashRegister(id, openingBalance),
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.billing.bankAccounts.cashRegisters.detail(data.id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.billing.bankAccounts.cashRegisters.all(),
      });
    },
  });
}

export function useCloseCashRegister() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, expectedBalance }: { id: string; expectedBalance: number }) =>
      closeCashRegister(id, expectedBalance),
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.billing.bankAccounts.cashRegisters.detail(data.id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.billing.bankAccounts.cashRegisters.all(),
      });
    },
  });
}
