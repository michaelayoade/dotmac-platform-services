"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "@/lib/api/query-keys";
import {
  getSettingsCategories,
  getSettingsCategory,
  updateSettingsCategory,
  validateSettings,
  bulkUpdateSettings,
  createSettingsBackup,
  restoreSettingsBackup,
  getSettingsAuditLogs,
  exportSettings,
  importSettings,
  resetCategoryToDefaults,
  getSettingsHealth,
  type SettingsCategory,
  type SettingsUpdateRequest,
  type SettingsExportRequest,
  type SettingsImportRequest,
  type ListAuditLogsParams,
  type CreateBackupParams,
} from "@/lib/api/admin-settings";

// ============================================================================
// Query Hooks
// ============================================================================

/**
 * Hook to fetch all available settings categories with metadata.
 */
export function useSettingsCategories() {
  return useQuery({
    queryKey: queryKeys.adminSettings.categories(),
    queryFn: getSettingsCategories,
    staleTime: 60 * 1000, // 1 minute
  });
}

/**
 * Hook to fetch settings for a specific category.
 */
export function useSettingsCategory(
  category: SettingsCategory,
  includeSensitive: boolean = false
) {
  return useQuery({
    queryKey: queryKeys.adminSettings.category(category),
    queryFn: () => getSettingsCategory(category, includeSensitive),
    enabled: !!category,
  });
}

/**
 * Hook to fetch settings audit logs.
 */
export function useSettingsAuditLogs(params?: ListAuditLogsParams) {
  return useQuery({
    queryKey: queryKeys.adminSettings.auditLogs(params),
    queryFn: () => getSettingsAuditLogs(params),
  });
}

/**
 * Hook to fetch settings management health status.
 */
export function useSettingsHealth() {
  return useQuery({
    queryKey: queryKeys.adminSettings.health(),
    queryFn: getSettingsHealth,
    staleTime: 30 * 1000, // 30 seconds
  });
}

// ============================================================================
// Mutation Hooks
// ============================================================================

/**
 * Hook to update settings for a specific category.
 */
export function useUpdateSettings() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      category,
      data,
    }: {
      category: SettingsCategory;
      data: SettingsUpdateRequest;
    }) => updateSettingsCategory(category, data),
    onSuccess: (data, { category }) => {
      // Update the specific category cache
      queryClient.setQueryData(queryKeys.adminSettings.category(category), data);
      // Invalidate categories list to refresh metadata
      queryClient.invalidateQueries({
        queryKey: queryKeys.adminSettings.categories(),
      });
      // Invalidate audit logs as a new entry was created
      queryClient.invalidateQueries({
        queryKey: queryKeys.adminSettings.auditLogs(),
      });
    },
  });
}

/**
 * Hook to validate settings without applying them.
 */
export function useValidateSettings() {
  return useMutation({
    mutationFn: ({
      category,
      updates,
    }: {
      category: SettingsCategory;
      updates: Record<string, unknown>;
    }) => validateSettings(category, updates),
  });
}

/**
 * Hook to bulk update multiple settings categories.
 */
export function useBulkUpdateSettings() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      updates,
      options,
    }: {
      updates: Record<SettingsCategory, Record<string, unknown>>;
      options?: { validateOnly?: boolean; reason?: string };
    }) => bulkUpdateSettings(updates, options),
    onSuccess: () => {
      // Invalidate all settings queries
      queryClient.invalidateQueries({
        queryKey: queryKeys.adminSettings.all,
      });
    },
  });
}

/**
 * Hook to create a settings backup.
 */
export function useCreateBackup() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (params: CreateBackupParams) => createSettingsBackup(params),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.adminSettings.backups(),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.adminSettings.health(),
      });
    },
  });
}

/**
 * Hook to restore settings from a backup.
 */
export function useRestoreBackup() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (backupId: string) => restoreSettingsBackup(backupId),
    onSuccess: () => {
      // Invalidate all settings queries as multiple categories may have changed
      queryClient.invalidateQueries({
        queryKey: queryKeys.adminSettings.all,
      });
    },
  });
}

/**
 * Hook to export settings.
 */
export function useExportSettings() {
  return useMutation({
    mutationFn: (request: SettingsExportRequest) => exportSettings(request),
  });
}

/**
 * Hook to import settings.
 */
export function useImportSettings() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: SettingsImportRequest) => importSettings(request),
    onSuccess: (data) => {
      // Only invalidate if we actually imported (not validate-only)
      if (!data.validateOnly && data.imported.length > 0) {
        queryClient.invalidateQueries({
          queryKey: queryKeys.adminSettings.all,
        });
      }
    },
  });
}

/**
 * Hook to reset a category to default values.
 */
export function useResetToDefaults() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (category: SettingsCategory) => resetCategoryToDefaults(category),
    onSuccess: (data, category) => {
      queryClient.setQueryData(queryKeys.adminSettings.category(category), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.adminSettings.categories(),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.adminSettings.auditLogs(),
      });
    },
  });
}
