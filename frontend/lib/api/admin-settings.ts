/**
 * Admin Settings API
 *
 * API functions for managing platform configuration settings.
 * All endpoints require appropriate admin permissions.
 */

import { api } from "@/lib/api/client";

// ============================================================================
// Types
// ============================================================================

export type SettingsCategory =
  | "database"
  | "jwt"
  | "redis"
  | "vault"
  | "storage"
  | "email"
  | "tenant"
  | "cors"
  | "rate_limit"
  | "observability"
  | "celery"
  | "features"
  | "billing";

export interface SettingField {
  name: string;
  value: unknown;
  type: string;
  description: string | null;
  default: unknown;
  required: boolean;
  sensitive: boolean;
  validationRules: Record<string, unknown> | null;
}

export interface SettingsResponse {
  category: SettingsCategory;
  displayName: string;
  fields: SettingField[];
  lastUpdated: string | null;
  updatedBy: string | null;
}

export interface SettingsCategoryInfo {
  category: SettingsCategory;
  displayName: string;
  description: string;
  fieldsCount: number;
  hasSensitiveFields: boolean;
  restartRequired: boolean;
  lastUpdated: string | null;
}

export interface SettingsUpdateRequest {
  updates: Record<string, unknown>;
  validateOnly?: boolean;
  restartRequired?: boolean;
  reason?: string;
}

export interface SettingsValidationResult {
  valid: boolean;
  errors: Record<string, string>;
  warnings: Record<string, string>;
  restartRequired: boolean;
}

export interface AuditLog {
  id: string;
  timestamp: string;
  userId: string;
  userEmail: string;
  category: SettingsCategory;
  action: string;
  changes: Record<string, { old: unknown; new: unknown }>;
  reason: string | null;
  ipAddress: string | null;
  userAgent: string | null;
}

export interface SettingsBackup {
  id: string;
  createdAt: string;
  createdBy: string;
  name: string;
  description: string | null;
  categories: SettingsCategory[];
  settingsData: Record<string, unknown>;
}

export interface SettingsExportRequest {
  categories?: SettingsCategory[];
  includeSensitive?: boolean;
  format?: "json" | "yaml" | "env";
}

export interface SettingsImportRequest {
  data: Record<string, unknown>;
  categories?: SettingsCategory[];
  validateOnly?: boolean;
  overwrite?: boolean;
  reason?: string;
}

export interface SettingsImportResult {
  imported: string[];
  errors: Record<string, unknown>;
  validateOnly: boolean;
}

export interface SettingsHealthStatus {
  status: "healthy" | "unhealthy";
  categoriesAvailable: number;
  auditLogsCount: number;
  backupsCount: number;
}

export interface ListAuditLogsParams {
  category?: SettingsCategory;
  userId?: string;
  limit?: number;
}

export interface CreateBackupParams {
  name: string;
  description?: string;
  categories?: SettingsCategory[];
}

// ============================================================================
// API Functions
// ============================================================================

const BASE_PATH = "/api/v1/admin/settings";

/**
 * Get all available settings categories with metadata.
 */
export async function getSettingsCategories(): Promise<SettingsCategoryInfo[]> {
  return api.get<SettingsCategoryInfo[]>(`${BASE_PATH}/categories`);
}

/**
 * Get settings for a specific category.
 */
export async function getSettingsCategory(
  category: SettingsCategory,
  includeSensitive: boolean = false
): Promise<SettingsResponse> {
  return api.get<SettingsResponse>(`${BASE_PATH}/category/${category}`, {
    params: { include_sensitive: includeSensitive },
  });
}

/**
 * Update settings for a specific category.
 */
export async function updateSettingsCategory(
  category: SettingsCategory,
  data: SettingsUpdateRequest
): Promise<SettingsResponse> {
  return api.put<SettingsResponse>(`${BASE_PATH}/category/${category}`, data);
}

/**
 * Validate settings without applying them.
 */
export async function validateSettings(
  category: SettingsCategory,
  updates: Record<string, unknown>
): Promise<SettingsValidationResult> {
  return api.post<SettingsValidationResult>(`${BASE_PATH}/validate`, {
    category,
    updates,
  });
}

/**
 * Bulk update multiple settings categories at once.
 */
export async function bulkUpdateSettings(
  updates: Record<SettingsCategory, Record<string, unknown>>,
  options?: { validateOnly?: boolean; reason?: string }
): Promise<{
  results: Record<string, string>;
  errors: Record<string, unknown>;
  summary: string;
}> {
  return api.post(`${BASE_PATH}/bulk-update`, {
    updates,
    validateOnly: options?.validateOnly ?? false,
    reason: options?.reason,
  });
}

/**
 * Create a backup of current settings.
 */
export async function createSettingsBackup(
  params: CreateBackupParams
): Promise<SettingsBackup> {
  return api.post<SettingsBackup>(`${BASE_PATH}/backup`, params);
}

/**
 * Restore settings from a backup.
 */
export async function restoreSettingsBackup(
  backupId: string
): Promise<{ message: string; categories: string[] }> {
  return api.post(`${BASE_PATH}/restore/${backupId}`);
}

/**
 * Get audit logs for settings changes.
 */
export async function getSettingsAuditLogs(
  params?: ListAuditLogsParams
): Promise<AuditLog[]> {
  return api.get<AuditLog[]>(`${BASE_PATH}/audit-logs`, {
    params: {
      category: params?.category,
      user_id: params?.userId,
      limit: params?.limit ?? 100,
    },
  });
}

/**
 * Export settings to a specific format.
 */
export async function exportSettings(
  request: SettingsExportRequest
): Promise<{ format: string; data: unknown }> {
  return api.post(`${BASE_PATH}/export`, request);
}

/**
 * Import settings from external data.
 */
export async function importSettings(
  request: SettingsImportRequest
): Promise<SettingsImportResult> {
  return api.post<SettingsImportResult>(`${BASE_PATH}/import`, request);
}

/**
 * Reset a category to default values.
 */
export async function resetCategoryToDefaults(
  category: SettingsCategory
): Promise<SettingsResponse> {
  return api.post<SettingsResponse>(`${BASE_PATH}/reset/${category}`);
}

/**
 * Get settings management health status.
 */
export async function getSettingsHealth(): Promise<SettingsHealthStatus> {
  return api.get<SettingsHealthStatus>(`${BASE_PATH}/health`);
}
