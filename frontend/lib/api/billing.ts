/**
 * Billing API
 *
 * Revenue, invoices, and payment data fetching
 * Connected to real backend endpoints
 */

import { api, normalizePaginatedResponse } from "./client";

export interface BillingMetrics {
  mrr: number; // Monthly Recurring Revenue (in cents)
  mrrChange: number;
  arr: number; // Annual Recurring Revenue (in cents)
  arrChange: number;
  outstanding: number; // Outstanding amount (in cents)
  overdueCount: number;
  collectionRate: number;
  collectionRateChange: number;
  activeSubscriptions: number;
  subscriptionChange: number;
  churnedThisMonth: number;
  upgradesThisMonth: number;
}

export async function getBillingMetrics(): Promise<BillingMetrics> {
  return api.get<BillingMetrics>("/api/v1/billing/metrics");
}

export interface Invoice {
  id: string;
  number: string;
  status: "draft" | "pending" | "paid" | "overdue" | "cancelled";
  amount: number; // in cents
  currency: string;
  customer: {
    id: string;
    name: string;
    email: string;
  };
  dueDate: string;
  paidAt?: string;
  createdAt: string;
  lineItems: Array<{
    description: string;
    quantity: number;
    unitPrice: number;
    amount: number;
  }>;
}

export async function getRecentInvoices(limit = 10): Promise<Invoice[]> {
  const response = await api.get<unknown>("/api/v1/billing/invoices", {
    params: {
      page: 1,
      page_size: limit,
      sort_by: "created_at",
      sort_order: "desc",
    },
  });
  const normalized = normalizePaginatedResponse<Invoice>(response);
  return normalized.items;
}

export interface GetInvoicesParams {
  page?: number;
  pageSize?: number;
  status?: Invoice["status"];
  customerId?: string;
  startDate?: string;
  endDate?: string;
}

export async function getInvoices(params: GetInvoicesParams = {}): Promise<{
  invoices: Invoice[];
  totalCount: number;
  pageCount: number;
}> {
  const { page = 1, pageSize = 20, status, customerId, startDate, endDate } = params;

  const response = await api.get<unknown>("/api/v1/billing/invoices", {
    params: {
      page,
      page_size: pageSize,
      status,
      customer_id: customerId,
      start_date: startDate,
      end_date: endDate,
    },
  });
  const normalized = normalizePaginatedResponse<Invoice>(response);

  return {
    invoices: normalized.items,
    totalCount: normalized.total,
    pageCount: normalized.totalPages,
  };
}

export async function getInvoice(id: string): Promise<Invoice> {
  return api.get<Invoice>(`/api/v1/billing/invoices/${id}`);
}

export interface CreateInvoiceData {
  customerId: string;
  lineItems: Array<{
    description: string;
    quantity: number;
    unitPrice: number;
  }>;
  dueDate: string;
  notes?: string;
}

export async function createInvoice(data: CreateInvoiceData): Promise<Invoice> {
  return api.post<Invoice>("/api/v1/billing/invoices", {
    customer_id: data.customerId,
    line_items: data.lineItems.map((item) => ({
      description: item.description,
      quantity: item.quantity,
      unit_price: item.unitPrice,
    })),
    due_date: data.dueDate,
    notes: data.notes,
  });
}

export async function sendInvoice(id: string): Promise<Invoice> {
  return api.post<Invoice>(`/api/v1/billing/invoices/${id}/send`);
}

export async function markInvoicePaid(id: string): Promise<Invoice> {
  return api.post<Invoice>(`/api/v1/billing/invoices/${id}/mark-paid`);
}

export async function voidInvoice(id: string): Promise<Invoice> {
  return api.post<Invoice>(`/api/v1/billing/invoices/${id}/void`);
}

// Subscription types
export interface Subscription {
  id: string;
  status: "active" | "trialing" | "past_due" | "canceled" | "paused";
  plan: {
    id: string;
    name: string;
    price: number;
    interval: "month" | "year";
  };
  customer: {
    id: string;
    name: string;
    email: string;
  };
  currentPeriodStart: string;
  currentPeriodEnd: string;
  cancelAtPeriodEnd: boolean;
  createdAt: string;
}

export async function getSubscriptions(params?: {
  page?: number;
  pageSize?: number;
  status?: Subscription["status"];
}): Promise<{
  subscriptions: Subscription[];
  totalCount: number;
  pageCount: number;
}> {
  const { page = 1, pageSize = 20, status } = params || {};

  const response = await api.get<unknown>("/api/v1/billing/subscriptions", {
    params: {
      page,
      page_size: pageSize,
      status,
    },
  });
  const normalized = normalizePaginatedResponse<Subscription>(response);

  return {
    subscriptions: normalized.items,
    totalCount: normalized.total,
    pageCount: normalized.totalPages,
  };
}

export async function getSubscription(id: string): Promise<Subscription> {
  return api.get<Subscription>(`/api/v1/billing/subscriptions/${id}`);
}

export async function cancelSubscription(id: string, immediately = false): Promise<Subscription> {
  return api.post<Subscription>(`/api/v1/billing/subscriptions/${id}/cancel`, {
    immediately,
  });
}

export async function pauseSubscription(id: string): Promise<Subscription> {
  return api.post<Subscription>(`/api/v1/billing/subscriptions/${id}/pause`);
}

export async function resumeSubscription(id: string): Promise<Subscription> {
  return api.post<Subscription>(`/api/v1/billing/subscriptions/${id}/resume`);
}

// Payment types
export interface Payment {
  id: string;
  amount: number;
  currency: string;
  status: "succeeded" | "pending" | "failed" | "refunded";
  method: {
    type: "card" | "bank_transfer" | "invoice";
    last4?: string;
    brand?: string;
  };
  invoiceId?: string;
  customerId: string;
  createdAt: string;
}

export async function getPayments(params?: {
  page?: number;
  pageSize?: number;
  status?: Payment["status"];
  customerId?: string;
}): Promise<{
  payments: Payment[];
  totalCount: number;
  pageCount: number;
}> {
  const { page = 1, pageSize = 20, status, customerId } = params || {};

  const response = await api.get<unknown>("/api/v1/billing/payments", {
    params: {
      page,
      page_size: pageSize,
      status,
      customer_id: customerId,
    },
  });
  const normalized = normalizePaginatedResponse<Payment>(response);

  return {
    payments: normalized.items,
    totalCount: normalized.total,
    pageCount: normalized.totalPages,
  };
}

// Payment method types
export interface PaymentMethod {
  id: string;
  type: "card" | "bank_account";
  isDefault: boolean;
  card?: {
    brand: string;
    last4: string;
    expMonth: number;
    expYear: number;
  };
  bankAccount?: {
    bankName: string;
    last4: string;
  };
  createdAt: string;
}

export async function getPaymentMethods(): Promise<PaymentMethod[]> {
  return api.get<PaymentMethod[]>("/api/v1/billing/payment-methods");
}

export async function setDefaultPaymentMethod(id: string): Promise<PaymentMethod> {
  return api.post<PaymentMethod>(`/api/v1/billing/payment-methods/${id}/default`);
}

export async function deletePaymentMethod(id: string): Promise<void> {
  return api.delete(`/api/v1/billing/payment-methods/${id}`);
}

// Credit Note types
export type CreditNoteStatus = "draft" | "issued" | "applied" | "voided";

export interface CreditNote {
  id: string;
  number: string;
  customerId: string;
  customerName: string;
  invoiceId?: string;
  invoiceNumber?: string;
  amount: number; // in cents
  currency: string;
  status: CreditNoteStatus;
  reason: string;
  lineItems: Array<{
    id: string;
    description: string;
    quantity: number;
    unitPrice: number;
    total: number;
  }>;
  appliedAmount: number;
  remainingAmount: number;
  issueDate?: string;
  voidedDate?: string;
  createdAt: string;
  updatedAt: string;
}

export interface GetCreditNotesParams {
  page?: number;
  pageSize?: number;
  status?: CreditNoteStatus;
  customerId?: string;
  startDate?: string;
  endDate?: string;
}

export async function getCreditNotes(params: GetCreditNotesParams = {}): Promise<{
  creditNotes: CreditNote[];
  totalCount: number;
  pageCount: number;
}> {
  const { page = 1, pageSize = 20, status, customerId, startDate, endDate } = params;

  const response = await api.get<unknown>("/api/v1/billing/credit-notes", {
    params: {
      page,
      page_size: pageSize,
      status,
      customer_id: customerId,
      start_date: startDate,
      end_date: endDate,
    },
  });
  const normalized = normalizePaginatedResponse<CreditNote>(response);

  return {
    creditNotes: normalized.items,
    totalCount: normalized.total,
    pageCount: normalized.totalPages,
  };
}

export async function getCreditNote(id: string): Promise<CreditNote> {
  return api.get<CreditNote>(`/api/v1/billing/credit-notes/${id}`);
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

export async function createCreditNote(data: CreateCreditNoteData): Promise<CreditNote> {
  return api.post<CreditNote>("/api/v1/billing/credit-notes", {
    customer_id: data.customerId,
    invoice_id: data.invoiceId,
    reason: data.reason,
    line_items: data.lineItems.map((item) => ({
      description: item.description,
      quantity: item.quantity,
      unit_price: item.unitPrice,
    })),
  });
}

export async function issueCreditNote(id: string): Promise<CreditNote> {
  return api.post<CreditNote>(`/api/v1/billing/credit-notes/${id}/issue`);
}

export async function voidCreditNote(id: string): Promise<CreditNote> {
  return api.post<CreditNote>(`/api/v1/billing/credit-notes/${id}/void`);
}

export async function applyCreditNote(
  id: string,
  invoiceId: string,
  amount: number
): Promise<CreditNote> {
  return api.post<CreditNote>(`/api/v1/billing/credit-notes/${id}/apply`, {
    invoice_id: invoiceId,
    amount,
  });
}

export async function getCustomerOpenInvoices(customerId: string): Promise<Invoice[]> {
  const response = await api.get<unknown>(`/api/v1/billing/customers/${customerId}/invoices`, {
    params: {
      status: "pending",
    },
  });
  const normalized = normalizePaginatedResponse<Invoice>(response);
  return normalized.items;
}
