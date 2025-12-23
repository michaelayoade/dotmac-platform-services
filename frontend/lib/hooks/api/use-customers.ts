"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, normalizePaginatedResponse } from "@/lib/api/client";
import { queryKeys } from "@/lib/api/query-keys";
import type { Customer, CustomerStatus, CustomerType, Address } from "@/types/models";
import type { PaginatedResponse, ListQueryParams } from "@/types/api";

// Types
export interface ListCustomersParams extends ListQueryParams {
  status?: CustomerStatus;
  type?: CustomerType;
  assignedTo?: string;
  tags?: string[];
  minRevenue?: number;
  maxRevenue?: number;
}

export interface CreateCustomerData {
  name: string;
  email: string;
  phone?: string;
  company?: string;
  type: CustomerType;
  assignedTo?: string;
  tags?: string[];
  notes?: string;
  address?: Address;
}

export interface UpdateCustomerData {
  name?: string;
  email?: string;
  phone?: string;
  company?: string;
  status?: CustomerStatus;
  type?: CustomerType;
  assignedTo?: string;
  tags?: string[];
  notes?: string;
  address?: Address;
  billingAddress?: Address; // Alias for address
}

export interface CustomerMetrics {
  totalRevenue: number;
  lifetimeValue: number;
  averageOrderValue: number;
  purchaseCount: number;
  lastPurchaseDate?: string;
  daysSinceLastPurchase?: number;
  engagementScore: number;
  healthScore: "good" | "at_risk" | "churned";
}

type CustomersResponse = PaginatedResponse<Customer>;

// API functions
async function getCustomers(params?: ListCustomersParams): Promise<CustomersResponse> {
  const response = await api.get<unknown>("/api/v1/customers", {
    params: {
      page: params?.page ?? 1,
      page_size: params?.pageSize ?? 10,
      sort_by: params?.sort?.[0]?.field,
      sort_order: params?.sort?.[0]?.direction,
      search: params?.search,
      status: params?.status,
      type: params?.type,
      assigned_to: params?.assignedTo,
      tags: params?.tags?.join(","),
      min_revenue: params?.minRevenue,
      max_revenue: params?.maxRevenue,
    },
  });
  return normalizePaginatedResponse<Customer>(response);
}

async function getCustomer(id: string): Promise<Customer> {
  return api.get<Customer>(`/api/v1/customers/${id}`);
}

async function createCustomer(data: CreateCustomerData): Promise<Customer> {
  return api.post<Customer>("/api/v1/customers", data);
}

async function updateCustomer({
  id,
  data,
}: {
  id: string;
  data: UpdateCustomerData;
}): Promise<Customer> {
  return api.patch<Customer>(`/api/v1/customers/${id}`, data);
}

async function deleteCustomer(id: string): Promise<void> {
  return api.delete<void>(`/api/v1/customers/${id}`);
}

async function getCustomerMetrics(id: string): Promise<CustomerMetrics> {
  return api.get<CustomerMetrics>(`/api/v1/customers/${id}/metrics`);
}

async function addCustomerTag({
  id,
  tag,
}: {
  id: string;
  tag: string;
}): Promise<Customer> {
  return api.post<Customer>(`/api/v1/customers/${id}/tags`, { tag });
}

async function removeCustomerTag({
  id,
  tag,
}: {
  id: string;
  tag: string;
}): Promise<Customer> {
  return api.delete<Customer>(`/api/v1/customers/${id}/tags/${encodeURIComponent(tag)}`);
}

async function assignCustomer({
  id,
  userId,
}: {
  id: string;
  userId: string;
}): Promise<Customer> {
  return api.post<Customer>(`/api/v1/customers/${id}/assign`, {
    user_id: userId,
  });
}

// Hooks
export function useCustomers(params?: ListCustomersParams) {
  return useQuery({
    queryKey: queryKeys.customers.list(params),
    queryFn: () => getCustomers(params),
    placeholderData: (previousData) => previousData,
  });
}

export function useCustomer(id: string) {
  return useQuery({
    queryKey: queryKeys.customers.detail(id),
    queryFn: () => getCustomer(id),
    enabled: !!id,
  });
}

export function useCreateCustomer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createCustomer,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.customers.all });
    },
  });
}

export function useUpdateCustomer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: updateCustomer,
    onSuccess: (data, { id }) => {
      queryClient.setQueryData(queryKeys.customers.detail(id), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.customers.lists() });
    },
  });
}

export function useDeleteCustomer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteCustomer,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.customers.all });
    },
  });
}

export function useCustomerMetrics(id: string) {
  return useQuery({
    queryKey: queryKeys.customers.metrics(id),
    queryFn: () => getCustomerMetrics(id),
    enabled: !!id,
  });
}

export function useAddCustomerTag() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: addCustomerTag,
    onSuccess: (data, { id }) => {
      queryClient.setQueryData(queryKeys.customers.detail(id), data);
    },
  });
}

export function useRemoveCustomerTag() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: removeCustomerTag,
    onSuccess: (data, { id }) => {
      queryClient.setQueryData(queryKeys.customers.detail(id), data);
    },
  });
}

export function useAssignCustomer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: assignCustomer,
    onSuccess: (data, { id }) => {
      queryClient.setQueryData(queryKeys.customers.detail(id), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.customers.lists() });
    },
  });
}
