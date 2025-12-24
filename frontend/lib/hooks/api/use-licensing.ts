"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getLicenses,
  getLicense,
  getLicenseByKey,
  createLicense,
  updateLicense,
  deleteLicense,
  validateLicense,
  validateActivation,
  getLicenseActivations,
  createActivation,
  deactivateActivation,
  sendHeartbeat,
  renewLicense,
  transferLicense,
  suspendLicense,
  reactivateLicense,
  getLicenseTemplates,
  createLicenseFromTemplate,
  generateEmergencyCode,
  validateEmergencyCode,
  type GetLicensesParams,
  type License,
  type CreateLicenseData,
  type LicenseValidationResult,
  type LicenseActivation,
  type LicenseTemplate,
} from "@/lib/api/licensing";
import { queryKeys } from "@/lib/api/query-keys";

// ============================================================================
// Licenses Hooks
// ============================================================================

export function useLicenses(params?: GetLicensesParams) {
  return useQuery({
    queryKey: queryKeys.licensing.licenses.list(params),
    queryFn: () => getLicenses(params),
    placeholderData: (previousData) => previousData,
  });
}

export function useLicense(id: string) {
  return useQuery({
    queryKey: queryKeys.licensing.licenses.detail(id),
    queryFn: () => getLicense(id),
    enabled: !!id,
  });
}

export function useLicenseByKey(licenseKey: string) {
  return useQuery({
    queryKey: queryKeys.licensing.licenses.byKey(licenseKey),
    queryFn: () => getLicenseByKey(licenseKey),
    enabled: !!licenseKey,
  });
}

export function useCreateLicense() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createLicense,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.licensing.licenses.all(),
      });
    },
  });
}

export function useUpdateLicense() {
  const queryClient = useQueryClient();
  type UpdateLicenseData = Parameters<typeof updateLicense> extends [string, infer P] ? P : never;

  return useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: string;
      data: UpdateLicenseData;
    }) => updateLicense(id, data),
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.licensing.licenses.detail(data.id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.licensing.licenses.all(),
      });
    },
  });
}

export function useDeleteLicense() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteLicense,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.licensing.licenses.all(),
      });
    },
  });
}

// ============================================================================
// License Validation Hooks
// ============================================================================

export function useValidateLicense() {
  return useMutation({
    mutationFn: validateLicense,
  });
}

export function useValidateActivation() {
  return useMutation({
    mutationFn: validateActivation,
  });
}

// ============================================================================
// License Activations Hooks
// ============================================================================

export function useLicenseActivations(licenseId: string) {
  return useQuery({
    queryKey: queryKeys.licensing.activations.list(licenseId),
    queryFn: () => getLicenseActivations(licenseId),
    enabled: !!licenseId,
  });
}

export function useCreateActivation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createActivation,
    onSuccess: (data) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.licensing.activations.list(data.licenseId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.licensing.licenses.detail(data.licenseId),
      });
    },
  });
}

export function useDeactivateActivation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deactivateActivation,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.licensing.activations.all(),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.licensing.licenses.all(),
      });
    },
  });
}

export function useSendHeartbeat() {
  return useMutation({
    mutationFn: ({
      activationKey,
      metadata,
    }: {
      activationKey: string;
      metadata?: Record<string, unknown>;
    }) => sendHeartbeat(activationKey, metadata),
  });
}

// ============================================================================
// License Operations Hooks
// ============================================================================

export function useRenewLicense() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, expiresAt, seats }: { id: string; expiresAt: string; seats?: number }) =>
      renewLicense(id, { expiresAt, seats }),
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.licensing.licenses.detail(data.id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.licensing.licenses.all(),
      });
    },
  });
}

export function useTransferLicense() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      newCustomerId,
      transferNote,
    }: {
      id: string;
      newCustomerId: string;
      transferNote?: string;
    }) => transferLicense(id, { newCustomerId, transferNote }),
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.licensing.licenses.detail(data.id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.licensing.licenses.all(),
      });
    },
  });
}

export function useSuspendLicense() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, reason }: { id: string; reason?: string }) =>
      suspendLicense(id, reason),
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.licensing.licenses.detail(data.id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.licensing.licenses.all(),
      });
    },
  });
}

export function useReactivateLicense() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: reactivateLicense,
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.licensing.licenses.detail(data.id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.licensing.licenses.all(),
      });
    },
  });
}

// ============================================================================
// License Templates Hooks
// ============================================================================

export function useLicenseTemplates() {
  return useQuery({
    queryKey: queryKeys.licensing.templates.all(),
    queryFn: getLicenseTemplates,
  });
}

export function useCreateLicenseFromTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      templateId,
      customerId,
      seats,
      expiresAt,
    }: {
      templateId: string;
      customerId?: string;
      seats?: number;
      expiresAt?: string;
    }) => createLicenseFromTemplate(templateId, { customerId, seats, expiresAt }),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.licensing.licenses.all(),
      });
    },
  });
}

// ============================================================================
// Emergency Codes Hooks
// ============================================================================

export function useGenerateEmergencyCode() {
  return useMutation({
    mutationFn: generateEmergencyCode,
  });
}

export function useValidateEmergencyCode() {
  return useMutation({
    mutationFn: validateEmergencyCode,
  });
}

// ============================================================================
// Re-export types
// ============================================================================

export type {
  GetLicensesParams,
  License,
  CreateLicenseData,
  LicenseValidationResult,
  LicenseActivation,
  LicenseTemplate,
};
