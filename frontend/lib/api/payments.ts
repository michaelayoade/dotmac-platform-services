/**
 * Payments API
 *
 * Payment management data fetching and mutations
 * Connected to real backend endpoints
 */

import { api, normalizePaginatedResponse } from "./client";

// Types
export interface Payment {
  id: string;
  customerId: string;
  customerName?: string;
  invoiceId?: string;
  invoiceNumber?: string;
  amount: number;
  currency: string;
  method:
    | "cash"
    | "check"
    | "bank_transfer"
    | "wire_transfer"
    | "card"
    | "other";
  status: "pending" | "completed" | "failed" | "refunded";
  referenceNumber?: string;
  paymentDate: string;
  processedDate?: string;
  notes?: string;
  createdAt: string;
  createdBy?: string;
}

export interface ListPaymentsParams {
  page?: number;
  pageSize?: number;
  status?: Payment["status"];
  method?: Payment["method"];
  customerId?: string;
  startDate?: string;
  endDate?: string;
  search?: string;
}

export interface ListPaymentsResponse {
  payments: Payment[];
  total: number;
  page: number;
  pageSize: number;
  pageCount: number;
}

export interface RecordPaymentRequest {
  customerId: string;
  amount: number;
  currency?: string;
  method: Payment["method"];
  referenceNumber?: string;
  invoiceId?: string;
  paymentDate?: string;
  notes?: string;
}

export interface FailedPaymentsSummary {
  count: number;
  totalAmount: number;
  byReason: Array<{ reason: string; count: number; amount: number }>;
}

type BackendPayment = {
  payment_id?: string;
  id?: string;
  customer_id?: string;
  customerId?: string;
  customer_name?: string;
  customerName?: string;
  invoice_id?: string;
  invoiceId?: string;
  invoice_number?: string;
  invoiceNumber?: string;
  amount?: number;
  currency?: string;
  method?: string;
  payment_method?: string;
  status?: string;
  reference_number?: string;
  referenceNumber?: string;
  payment_date?: string;
  paymentDate?: string;
  processed_date?: string;
  processedDate?: string;
  notes?: string;
  created_at?: string;
  createdAt?: string;
  processed_at?: string;
  processedAt?: string;
  created_by?: string;
  createdBy?: string;
  payment_method_type?: string;
  amount_display?: number;
};

function mapPaymentStatus(status?: string): Payment["status"] {
  switch (status) {
    case "succeeded":
      return "completed";
    case "failed":
    case "cancelled":
      return "failed";
    case "refunded":
    case "partially_refunded":
      return "refunded";
    case "processing":
    case "pending":
    default:
      return "pending";
  }
}

function mapPaymentMethod(method?: string): Payment["method"] {
  switch (method) {
    case "cash":
    case "check":
    case "card":
    case "wire_transfer":
      return method;
    case "bank_account":
    case "bank_transfer":
      return "bank_transfer";
    default:
      return "other";
  }
}

function mapPayment(p: BackendPayment): Payment {
  const methodSource = p.payment_method_type || p.method || p.payment_method;
  const statusSource = p.status;
  const amountValue =
    p.amount ?? (p.amount_display !== undefined ? Math.round(p.amount_display * 100) : 0);

  return {
    id: p.payment_id || p.id || "",
    customerId: p.customer_id || p.customerId || "",
    customerName: p.customer_name || p.customerName,
    invoiceId: p.invoice_id || p.invoiceId,
    invoiceNumber: p.invoice_number || p.invoiceNumber,
    amount: amountValue,
    currency: p.currency || "USD",
    method: mapPaymentMethod(methodSource),
    status: mapPaymentStatus(statusSource),
    referenceNumber: p.reference_number || p.referenceNumber,
    paymentDate:
      p.payment_date ||
      p.paymentDate ||
      p.processed_at ||
      p.processedDate ||
      p.created_at ||
      p.createdAt ||
      "",
    processedDate: p.processed_at || p.processedDate,
    notes: p.notes,
    createdAt: p.created_at || p.createdAt || "",
    createdBy: p.created_by || p.createdBy,
  };
}

export async function listPayments(
  params: ListPaymentsParams = {}
): Promise<ListPaymentsResponse> {
  const { page = 1, pageSize = 20, status, method, customerId, startDate, endDate, search } = params;
  const backendStatus = status === "completed" ? "succeeded" : status;

  const response = await api.get<unknown>("/api/v1/billing/payments", {
    params: {
      page,
      page_size: pageSize,
      status: backendStatus,
      method,
      customer_id: customerId,
      start_date: startDate,
      end_date: endDate,
      search,
    },
  });

  const normalized = normalizePaginatedResponse<BackendPayment>(response);

  return {
    payments: normalized.items.map(mapPayment),
    total: normalized.total,
    page: normalized.page,
    pageSize: normalized.pageSize,
    pageCount: normalized.totalPages,
  };
}

export async function getPayment(id: string): Promise<Payment> {
  const payment = await api.get<BackendPayment>(`/api/v1/billing/payments/${id}`);
  return mapPayment(payment);
}

export async function recordOfflinePayment(data: RecordPaymentRequest): Promise<Payment> {
  const payment = await api.post<BackendPayment>("/api/v1/billing/payments/offline", {
    customer_id: data.customerId,
    amount: data.amount,
    currency: data.currency || "USD",
    payment_method: data.method,
    reference_number: data.referenceNumber,
    invoice_id: data.invoiceId,
    payment_date: data.paymentDate,
    notes: data.notes,
  });
  return mapPayment(payment);
}

export async function getFailedPaymentsSummary(): Promise<FailedPaymentsSummary> {
  const response = await api.get<{
    count?: number;
    total_amount?: number;
    totalAmount?: number;
    by_reason?: Array<{ reason: string; count: number; amount: number }>;
    byReason?: Array<{ reason: string; count: number; amount: number }>;
  }>("/api/v1/billing/payments/failed");

  return {
    count: response.count || 0,
    totalAmount: response.total_amount || response.totalAmount || 0,
    byReason: response.by_reason || response.byReason || [],
  };
}
