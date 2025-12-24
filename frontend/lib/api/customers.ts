/**
 * Customers API
 *
 * Customer/CRM management data fetching and mutations
 * Connected to real backend endpoints
 */

import { api, normalizePaginatedResponse } from "./client";

export interface Customer {
  id: string;
  name: string;
  email: string;
  phone?: string;
  company?: string;
  status: "active" | "inactive" | "churned" | "lead";
  type: "individual" | "business" | "enterprise";
  tenantId: string;
  billingAddress?: {
    line1: string;
    line2?: string;
    city: string;
    state: string;
    postalCode: string;
    country: string;
  };
  tags?: string[];
  metadata?: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
}

export interface CustomerMetrics {
  totalSpend: number;
  invoiceCount: number;
  averageInvoiceValue: number;
  lastPaymentDate?: string;
  subscriptionStatus?: string;
  lifetimeValue: number;
}

export interface GetCustomersParams {
  page?: number;
  pageSize?: number;
  search?: string;
  status?: Customer["status"];
  type?: Customer["type"];
  tags?: string[];
  sortBy?: string;
  sortOrder?: "asc" | "desc";
}

export async function getCustomers(params: GetCustomersParams = {}): Promise<{
  customers: Customer[];
  totalCount: number;
  pageCount: number;
}> {
  const { page = 1, pageSize = 20, search, status, type, tags, sortBy, sortOrder } = params;

  const response = await api.get<unknown>("/api/v1/customers", {
    params: {
      page,
      page_size: pageSize,
      search,
      status,
      type,
      tags: tags?.join(","),
      sort_by: sortBy,
      sort_order: sortOrder,
    },
  });
  const normalized = normalizePaginatedResponse<Customer>(response);

  return {
    customers: normalized.items,
    totalCount: normalized.total,
    pageCount: normalized.totalPages,
  };
}

export async function getCustomer(id: string): Promise<Customer> {
  return api.get<Customer>(`/api/v1/customers/${id}`);
}

export async function getCustomerMetrics(id: string): Promise<CustomerMetrics> {
  return api.get<CustomerMetrics>(`/api/v1/customers/${id}/metrics`);
}

export interface CreateCustomerData {
  name: string;
  email: string;
  phone?: string;
  company?: string;
  type?: Customer["type"];
  billingAddress?: Customer["billingAddress"];
  tags?: string[];
  metadata?: Record<string, unknown>;
}

export async function createCustomer(data: CreateCustomerData): Promise<Customer> {
  return api.post<Customer>("/api/v1/customers", {
    name: data.name,
    email: data.email,
    phone: data.phone,
    company: data.company,
    type: data.type,
    billing_address: data.billingAddress,
    tags: data.tags,
    metadata: data.metadata,
  });
}

export interface UpdateCustomerData {
  name?: string;
  email?: string;
  phone?: string;
  company?: string;
  status?: Customer["status"];
  type?: Customer["type"];
  billingAddress?: Customer["billingAddress"];
  tags?: string[];
  metadata?: Record<string, unknown>;
}

export async function updateCustomer(id: string, data: UpdateCustomerData): Promise<Customer> {
  return api.patch<Customer>(`/api/v1/customers/${id}`, {
    name: data.name,
    email: data.email,
    phone: data.phone,
    company: data.company,
    status: data.status,
    type: data.type,
    billing_address: data.billingAddress,
    tags: data.tags,
    metadata: data.metadata,
  });
}

export async function deleteCustomer(id: string): Promise<void> {
  return api.delete(`/api/v1/customers/${id}`);
}

// Customer tags management
export async function addCustomerTag(id: string, tag: string): Promise<Customer> {
  return api.post<Customer>(`/api/v1/customers/${id}/tags`, { tag });
}

export async function removeCustomerTag(id: string, tag: string): Promise<Customer> {
  return api.delete<Customer>(`/api/v1/customers/${id}/tags/${encodeURIComponent(tag)}`);
}

// Customer notes
export interface CustomerNote {
  id: string;
  content: string;
  createdBy: {
    id: string;
    name: string;
  };
  createdAt: string;
  updatedAt: string;
}

export async function getCustomerNotes(customerId: string): Promise<CustomerNote[]> {
  return api.get<CustomerNote[]>(`/api/v1/customers/${customerId}/notes`);
}

export async function addCustomerNote(customerId: string, content: string): Promise<CustomerNote> {
  return api.post<CustomerNote>(`/api/v1/customers/${customerId}/notes`, { content });
}

export async function updateCustomerNote(
  customerId: string,
  noteId: string,
  content: string
): Promise<CustomerNote> {
  return api.patch<CustomerNote>(`/api/v1/customers/${customerId}/notes/${noteId}`, { content });
}

export async function deleteCustomerNote(customerId: string, noteId: string): Promise<void> {
  return api.delete(`/api/v1/customers/${customerId}/notes/${noteId}`);
}

// Customer activity
export interface CustomerActivity {
  id: string;
  type: "invoice" | "payment" | "subscription" | "support" | "note" | "update";
  title: string;
  description: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
}

export async function getCustomerActivity(
  customerId: string,
  limit = 20
): Promise<CustomerActivity[]> {
  return api.get<CustomerActivity[]>(`/api/v1/customers/${customerId}/activity`, {
    params: { limit },
  });
}
