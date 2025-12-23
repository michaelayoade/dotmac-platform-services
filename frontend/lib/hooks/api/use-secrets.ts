"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  listSecrets,
  getSecret,
  getSecretMetadata,
  createSecret,
  updateSecret,
  deleteSecret,
  undeleteSecret,
  destroySecret,
  getSecretsHealth,
  getSecretsMetrics,
  rotateSecret,
  getRotationPolicies,
  setRotationPolicy,
  type Secret,
  type SecretValue,
  type SecretMetadata,
  type SecretsMetrics,
  type RotationPolicy,
} from "@/lib/api/secrets";
import { queryKeys } from "@/lib/api/query-keys";

// ============================================================================
// Secrets Hooks
// ============================================================================

export function useSecrets(path?: string) {
  return useQuery({
    queryKey: queryKeys.secrets.list(path),
    queryFn: () => listSecrets(path),
  });
}

export function useSecret(path: string, version?: number) {
  return useQuery({
    queryKey: queryKeys.secrets.detail(path, version),
    queryFn: () => getSecret(path, version),
    enabled: !!path,
  });
}

export function useSecretMetadata(path: string) {
  return useQuery({
    queryKey: queryKeys.secrets.metadata(path),
    queryFn: () => getSecretMetadata(path),
    enabled: !!path,
  });
}

export function useCreateSecret() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      path,
      data,
      metadata,
    }: {
      path: string;
      data: Record<string, unknown>;
      metadata?: Record<string, unknown>;
    }) => createSecret(path, data, metadata),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.secrets.all,
      });
    },
  });
}

export function useUpdateSecret() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      path,
      data,
      metadata,
    }: {
      path: string;
      data: Record<string, unknown>;
      metadata?: Record<string, unknown>;
    }) => updateSecret(path, data, metadata),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.secrets.detail(variables.path),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.secrets.metadata(variables.path),
      });
    },
  });
}

export function useDeleteSecret() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ path, versions }: { path: string; versions?: number[] }) =>
      deleteSecret(path, versions),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.secrets.detail(variables.path),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.secrets.metadata(variables.path),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.secrets.all,
      });
    },
  });
}

export function useUndeleteSecret() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ path, versions }: { path: string; versions: number[] }) =>
      undeleteSecret(path, versions),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.secrets.detail(variables.path),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.secrets.metadata(variables.path),
      });
    },
  });
}

export function useDestroySecret() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ path, versions }: { path: string; versions: number[] }) =>
      destroySecret(path, versions),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.secrets.detail(variables.path),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.secrets.metadata(variables.path),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.secrets.all,
      });
    },
  });
}

// ============================================================================
// Secrets Health Hook
// ============================================================================

export function useSecretsHealth() {
  return useQuery({
    queryKey: queryKeys.secrets.health(),
    queryFn: getSecretsHealth,
    refetchInterval: 30 * 1000, // Poll every 30 seconds
    staleTime: 10 * 1000,
  });
}

// ============================================================================
// Secrets Metrics Hook
// ============================================================================

export function useSecretsMetrics(params?: { periodDays?: number }) {
  return useQuery({
    queryKey: queryKeys.secrets.metrics(params),
    queryFn: () => getSecretsMetrics(params),
    staleTime: 5 * 60 * 1000,
  });
}

// ============================================================================
// Secret Rotation Hooks
// ============================================================================

export function useRotateSecret() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ path, newData }: { path: string; newData: Record<string, unknown> }) =>
      rotateSecret(path, newData),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.secrets.detail(variables.path),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.secrets.metadata(variables.path),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.secrets.rotationPolicies(),
      });
    },
  });
}

export function useRotationPolicies() {
  return useQuery({
    queryKey: queryKeys.secrets.rotationPolicies(),
    queryFn: getRotationPolicies,
  });
}

export function useSetRotationPolicy() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      path,
      policy,
    }: {
      path: string;
      policy: { rotationPeriodDays: number; isEnabled: boolean };
    }) => setRotationPolicy(path, policy),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.secrets.rotationPolicies(),
      });
    },
  });
}

// ============================================================================
// Re-export types
// ============================================================================

export type {
  Secret,
  SecretValue,
  SecretMetadata,
  SecretsMetrics,
  RotationPolicy,
};
