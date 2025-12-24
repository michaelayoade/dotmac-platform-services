/**
 * Feature Flags API
 *
 * Feature flag management and evaluation
 */

import { api } from "./client";

// ============================================================================
// Feature Flag Types
// ============================================================================

export interface FeatureFlag {
  name: string;
  enabled: boolean;
  description?: string;
  context?: Record<string, unknown>;
  variant?: string;
  rolloutPercentage?: number;
  targetingRules?: TargetingRule[];
  createdAt: string;
  updatedAt: string;
}

export interface TargetingRule {
  id: string;
  attribute: string;
  operator: "eq" | "neq" | "contains" | "in" | "not_in" | "gt" | "lt" | "gte" | "lte";
  value: unknown;
  enabled: boolean;
}

export interface FeatureFlagCheck {
  enabled: boolean;
  variant?: string;
  contextEvaluatedAt: string;
  matchedRule?: string;
}

// ============================================================================
// Feature Flag CRUD
// ============================================================================

export async function getFeatureFlags(): Promise<FeatureFlag[]> {
  return api.get<FeatureFlag[]>("/api/v1/feature-flags/flags");
}

export async function getFeatureFlag(name: string): Promise<FeatureFlag> {
  return api.get<FeatureFlag>(`/api/v1/feature-flags/flags/${encodeURIComponent(name)}`);
}

export interface CreateFeatureFlagData {
  name: string;
  enabled?: boolean;
  description?: string;
  context?: Record<string, unknown>;
  rolloutPercentage?: number;
  targetingRules?: Omit<TargetingRule, "id">[];
}

export async function createFeatureFlag(data: CreateFeatureFlagData): Promise<FeatureFlag> {
  return api.post<FeatureFlag>(`/api/v1/feature-flags/flags/${encodeURIComponent(data.name)}`, {
    enabled: data.enabled ?? false,
    description: data.description,
    context: data.context,
    rollout_percentage: data.rolloutPercentage,
    targeting_rules: data.targetingRules,
  });
}

export async function updateFeatureFlag(
  name: string,
  data: Partial<Omit<CreateFeatureFlagData, "name">>
): Promise<FeatureFlag> {
  return api.patch<FeatureFlag>(`/api/v1/feature-flags/flags/${encodeURIComponent(name)}`, {
    enabled: data.enabled,
    description: data.description,
    context: data.context,
    rollout_percentage: data.rolloutPercentage,
    targeting_rules: data.targetingRules,
  });
}

export async function deleteFeatureFlag(name: string): Promise<void> {
  return api.delete(`/api/v1/feature-flags/flags/${encodeURIComponent(name)}`);
}

// ============================================================================
// Feature Flag Evaluation
// ============================================================================

export async function checkFeatureFlag(
  name: string,
  context?: Record<string, unknown>
): Promise<FeatureFlagCheck> {
  return api.post<FeatureFlagCheck>(`/api/v1/feature-flags/flags/${encodeURIComponent(name)}/check`, {
    context,
  });
}

export async function checkFeatureFlags(
  names: string[],
  context?: Record<string, unknown>
): Promise<Record<string, FeatureFlagCheck>> {
  return api.post<Record<string, FeatureFlagCheck>>("/api/v1/feature-flags/flags/bulk", {
    names,
    context,
  });
}

// ============================================================================
// Feature Flag Status
// ============================================================================

export interface FeatureFlagStatus {
  totalFlags: number;
  enabledFlags: number;
  disabledFlags: number;
  flagsByStatus: {
    enabled: string[];
    disabled: string[];
  };
  recentChanges: Array<{
    flagName: string;
    action: "created" | "updated" | "deleted" | "enabled" | "disabled";
    timestamp: string;
    userId?: string;
  }>;
}

export async function getFeatureFlagStatus(): Promise<FeatureFlagStatus> {
  return api.get<FeatureFlagStatus>("/api/v1/feature-flags/status");
}

// ============================================================================
// Feature Flag Admin
// ============================================================================

export async function clearFeatureFlagCache(): Promise<{ cleared: boolean }> {
  return api.post<{ cleared: boolean }>("/api/v1/feature-flags/admin/clear-cache");
}

export async function syncFeatureFlagsToRedis(): Promise<{ synced: number }> {
  return api.post<{ synced: number }>("/api/v1/feature-flags/admin/sync-redis");
}

// ============================================================================
// Feature Flag Toggle Shorthand
// ============================================================================

export async function enableFeatureFlag(name: string): Promise<FeatureFlag> {
  return updateFeatureFlag(name, { enabled: true });
}

export async function disableFeatureFlag(name: string): Promise<FeatureFlag> {
  return updateFeatureFlag(name, { enabled: false });
}
