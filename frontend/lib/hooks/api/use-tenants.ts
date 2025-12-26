"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, normalizePaginatedResponse } from "@/lib/api/client";
import { queryKeys } from "@/lib/api/query-keys";
import type { Tenant, TenantStatus, TenantSettings, TenantPlanType } from "@/types/models";
import type { PaginatedResponse, ListQueryParams } from "@/types/api";

// Types
export interface ListTenantsParams extends ListQueryParams {
  status?: TenantStatus;
  planType?: string;
  isTrial?: boolean;
}

export interface CreateTenantData {
  name: string;
  slug: string;
  plan?: TenantPlanType;
  planType?: string; // Deprecated - use plan
  billingCycle?: "month" | "year";
  domain?: string;
  ownerEmail?: string;
  ownerName?: string;
}

export interface UpdateTenantData {
  name?: string;
  domain?: string;
  logo?: string;
  settings?: Partial<TenantSettings>;
}

export interface TenantStats {
  userCount: number;
  storageUsed: number;
  storageLimit: number;
  apiCallsThisMonth: number;
  apiCallsLimit: number;
  deploymentsActive: number;
  deploymentsLimit: number;
  mrr?: number; // Monthly recurring revenue in cents
}

type TenantsResponse = PaginatedResponse<Tenant>;

// API functions
async function getTenants(params?: ListTenantsParams): Promise<TenantsResponse> {
  const response = await api.get<unknown>("/api/v1/tenants", {
    params: {
      page: params?.page ?? 1,
      page_size: params?.pageSize ?? 10,
      sort_by: params?.sort?.[0]?.field,
      sort_order: params?.sort?.[0]?.direction,
      search: params?.search,
      status: params?.status,
      plan_type: params?.planType,
      is_trial: params?.isTrial,
    },
  });
  return normalizePaginatedResponse<Tenant>(response);
}

async function getTenant(id: string): Promise<Tenant> {
  return api.get<Tenant>(`/api/v1/tenants/${id}`);
}

async function getCurrentTenant(): Promise<Tenant> {
  return api.get<Tenant>("/api/v1/tenants/current");
}

async function getTenantBySlug(slug: string): Promise<Tenant> {
  return api.get<Tenant>(`/api/v1/tenants/slug/${slug}`);
}

async function createTenant(data: CreateTenantData): Promise<Tenant> {
  return api.post<Tenant>("/api/v1/tenants", data);
}

async function updateTenant({
  id,
  data,
}: {
  id: string;
  data: UpdateTenantData;
}): Promise<Tenant> {
  return api.patch<Tenant>(`/api/v1/tenants/${id}`, data);
}

async function deleteTenant(id: string): Promise<void> {
  return api.delete<void>(`/api/v1/tenants/${id}`);
}

async function suspendTenant(id: string): Promise<Tenant> {
  return api.post<Tenant>(`/api/v1/tenants/${id}/suspend`);
}

async function activateTenant(id: string): Promise<Tenant> {
  return api.post<Tenant>(`/api/v1/tenants/${id}/activate`);
}

async function restoreTenant(id: string): Promise<Tenant> {
  return api.post<Tenant>(`/api/v1/tenants/${id}/restore`);
}

async function getTenantStats(id: string): Promise<TenantStats> {
  return api.get<TenantStats>(`/api/v1/tenants/${id}/stats`);
}

async function getTenantSettings(id: string): Promise<TenantSettings> {
  return api.get<TenantSettings>(`/api/v1/tenants/${id}/settings`);
}

async function updateTenantSettings({
  id,
  settings,
}: {
  id: string;
  settings: Partial<TenantSettings>;
}): Promise<TenantSettings> {
  return api.patch<TenantSettings>(`/api/v1/tenants/${id}/settings`, settings);
}

// Hooks
export function useTenants(params?: ListTenantsParams) {
  return useQuery({
    queryKey: queryKeys.tenants.list(params),
    queryFn: () => getTenants(params),
    placeholderData: (previousData) => previousData,
  });
}

export function useTenant(id: string) {
  return useQuery({
    queryKey: queryKeys.tenants.detail(id),
    queryFn: () => getTenant(id),
    enabled: !!id,
  });
}

export function useCurrentTenant() {
  return useQuery({
    queryKey: queryKeys.tenants.current(),
    queryFn: getCurrentTenant,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useTenantBySlug(slug: string) {
  return useQuery({
    queryKey: [...queryKeys.tenants.all, "slug", slug],
    queryFn: () => getTenantBySlug(slug),
    enabled: !!slug,
  });
}

export function useCreateTenant() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createTenant,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.tenants.all });
    },
  });
}

export function useUpdateTenant() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: updateTenant,
    onSuccess: (data, { id }) => {
      queryClient.setQueryData(queryKeys.tenants.detail(id), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.tenants.lists() });
    },
  });
}

export function useDeleteTenant() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteTenant,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.tenants.all });
    },
  });
}

export function useSuspendTenant() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: suspendTenant,
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.tenants.detail(data.id), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.tenants.lists() });
    },
  });
}

export function useActivateTenant() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: activateTenant,
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.tenants.detail(data.id), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.tenants.lists() });
    },
  });
}

export function useRestoreTenant() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: restoreTenant,
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.tenants.detail(data.id), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.tenants.lists() });
    },
  });
}

export function useTenantStats(id: string) {
  return useQuery({
    queryKey: queryKeys.tenants.stats(id),
    queryFn: () => getTenantStats(id),
    enabled: !!id,
  });
}

export function useTenantSettings(id: string) {
  return useQuery({
    queryKey: queryKeys.tenants.settings(id),
    queryFn: () => getTenantSettings(id),
    enabled: !!id,
  });
}

export function useUpdateTenantSettings() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: updateTenantSettings,
    onSuccess: (data, { id }) => {
      queryClient.setQueryData(queryKeys.tenants.settings(id), data);
    },
  });
}

// Domain Verification Hooks
import {
  getDomainStatus,
  initiateDomainVerification,
  checkDomainVerification,
  removeDomain,
  type VerificationMethod,
  type DomainVerification,
} from "@/lib/api/tenants";

export function useDomainStatus(tenantId: string) {
  return useQuery({
    queryKey: queryKeys.tenants.domainStatus(tenantId),
    queryFn: () => getDomainStatus(tenantId),
    enabled: !!tenantId,
  });
}

export function useInitiateDomainVerification() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      tenantId,
      domain,
      method,
    }: {
      tenantId: string;
      domain: string;
      method: VerificationMethod;
    }) => initiateDomainVerification(tenantId, domain, method),
    onSuccess: (_, { tenantId }) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.tenants.domainStatus(tenantId),
      });
    },
  });
}

export function useCheckDomainVerification() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ tenantId, domain }: { tenantId: string; domain: string }) =>
      checkDomainVerification(tenantId, domain),
    onSuccess: (_, { tenantId }) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.tenants.domainStatus(tenantId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.tenants.detail(tenantId),
      });
    },
  });
}

export function useRemoveDomain() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (tenantId: string) => removeDomain(tenantId),
    onSuccess: (_, tenantId) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.tenants.domainStatus(tenantId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.tenants.detail(tenantId),
      });
    },
  });
}

// Branding Hooks
import {
  getBranding,
  updateBranding,
  uploadBrandingLogo,
  type TenantBranding,
} from "@/lib/api/tenants";

export function useBranding(tenantId: string) {
  return useQuery({
    queryKey: queryKeys.tenants.branding(tenantId),
    queryFn: () => getBranding(tenantId),
    enabled: !!tenantId,
  });
}

export function useUpdateBranding() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      tenantId,
      data,
    }: {
      tenantId: string;
      data: Partial<TenantBranding>;
    }) => updateBranding(tenantId, data),
    onSuccess: (data, { tenantId }) => {
      queryClient.setQueryData(queryKeys.tenants.branding(tenantId), data);
    },
  });
}

export function useUploadBrandingLogo() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      tenantId,
      file,
      type,
    }: {
      tenantId: string;
      file: File;
      type: "logo" | "favicon";
    }) => uploadBrandingLogo(tenantId, file, type),
    onSuccess: (_, { tenantId }) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.tenants.branding(tenantId),
      });
    },
  });
}
