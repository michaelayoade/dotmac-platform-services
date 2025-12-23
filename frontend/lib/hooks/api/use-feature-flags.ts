"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getFeatureFlags,
  getFeatureFlag,
  createFeatureFlag,
  updateFeatureFlag,
  deleteFeatureFlag,
  checkFeatureFlag,
  checkFeatureFlags,
  getFeatureFlagStatus,
  clearFeatureFlagCache,
  syncFeatureFlagsToRedis,
  enableFeatureFlag,
  disableFeatureFlag,
  type FeatureFlag,
  type CreateFeatureFlagData,
  type FeatureFlagCheck,
  type FeatureFlagStatus,
} from "@/lib/api/feature-flags";
import { queryKeys } from "@/lib/api/query-keys";

// ============================================================================
// Feature Flags Hooks
// ============================================================================

export function useFeatureFlags() {
  return useQuery({
    queryKey: queryKeys.featureFlags.all(),
    queryFn: getFeatureFlags,
  });
}

export function useFeatureFlag(name: string) {
  return useQuery({
    queryKey: queryKeys.featureFlags.detail(name),
    queryFn: () => getFeatureFlag(name),
    enabled: !!name,
  });
}

export function useCreateFeatureFlag() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createFeatureFlag,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.featureFlags.all(),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.featureFlags.status(),
      });
    },
  });
}

export function useUpdateFeatureFlag() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ name, data }: { name: string; data: Partial<Omit<CreateFeatureFlagData, "name">> }) =>
      updateFeatureFlag(name, data),
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.featureFlags.detail(data.name), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.featureFlags.all(),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.featureFlags.status(),
      });
    },
  });
}

export function useDeleteFeatureFlag() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteFeatureFlag,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.featureFlags.all(),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.featureFlags.status(),
      });
    },
  });
}

export function useEnableFeatureFlag() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: enableFeatureFlag,
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.featureFlags.detail(data.name), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.featureFlags.all(),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.featureFlags.status(),
      });
    },
  });
}

export function useDisableFeatureFlag() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: disableFeatureFlag,
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.featureFlags.detail(data.name), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.featureFlags.all(),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.featureFlags.status(),
      });
    },
  });
}

// ============================================================================
// Feature Flag Check Hooks
// ============================================================================

export function useCheckFeatureFlag(name: string, context?: Record<string, unknown>) {
  return useQuery({
    queryKey: queryKeys.featureFlags.check(name, context),
    queryFn: () => checkFeatureFlag(name, context),
    enabled: !!name,
    staleTime: 60 * 1000, // 1 minute
  });
}

export function useCheckFeatureFlags(names: string[], context?: Record<string, unknown>) {
  return useQuery({
    queryKey: queryKeys.featureFlags.checkBulk(names, context),
    queryFn: () => checkFeatureFlags(names, context),
    enabled: names.length > 0,
    staleTime: 60 * 1000,
  });
}

// ============================================================================
// Feature Flag Status Hook
// ============================================================================

export function useFeatureFlagStatus() {
  return useQuery({
    queryKey: queryKeys.featureFlags.status(),
    queryFn: getFeatureFlagStatus,
    staleTime: 2 * 60 * 1000,
  });
}

// ============================================================================
// Feature Flag Admin Hooks
// ============================================================================

export function useClearFeatureFlagCache() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: clearFeatureFlagCache,
    onSuccess: () => {
      // Invalidate all feature flag queries after cache clear
      queryClient.invalidateQueries({
        queryKey: queryKeys.featureFlags.all(),
      });
    },
  });
}

export function useSyncFeatureFlagsToRedis() {
  return useMutation({
    mutationFn: syncFeatureFlagsToRedis,
  });
}

// ============================================================================
// Re-export types
// ============================================================================

export type {
  FeatureFlag,
  CreateFeatureFlagData,
  FeatureFlagCheck,
  FeatureFlagStatus,
};
