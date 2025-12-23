/**
 * Licensing API
 *
 * Software licensing, activations, and validation
 */

import { api, normalizePaginatedResponse } from "./client";

// ============================================================================
// License Types
// ============================================================================

export type LicenseStatus = "active" | "expired" | "suspended" | "revoked" | "trial";
export type LicenseType = "perpetual" | "subscription" | "trial" | "enterprise";

export interface License {
  id: string;
  licenseKey: string;
  productId: string;
  productName: string;
  customerId?: string;
  customerName?: string;
  type: LicenseType;
  status: LicenseStatus;
  seats: number;
  usedSeats: number;
  features: string[];
  issuedAt: string;
  expiresAt?: string;
  lastValidatedAt?: string;
  metadata?: Record<string, unknown>;
}

export interface LicenseActivation {
  id: string;
  licenseId: string;
  deviceId: string;
  deviceName?: string;
  activationKey: string;
  status: "active" | "deactivated" | "expired";
  activatedAt: string;
  lastHeartbeat?: string;
  expiresAt?: string;
  metadata?: Record<string, unknown>;
}

// ============================================================================
// License CRUD
// ============================================================================

export interface GetLicensesParams {
  page?: number;
  pageSize?: number;
  status?: LicenseStatus;
  type?: LicenseType;
  productId?: string;
  customerId?: string;
  search?: string;
}

export async function getLicenses(params: GetLicensesParams = {}): Promise<{
  licenses: License[];
  totalCount: number;
  pageCount: number;
}> {
  const { page = 1, pageSize = 20, status, type, productId, customerId, search } = params;

  const response = await api.get<unknown>("/api/licensing/licenses", {
    params: {
      page,
      page_size: pageSize,
      status,
      type,
      product_id: productId,
      customer_id: customerId,
      search,
    },
  });
  const normalized = normalizePaginatedResponse<License>(response);

  return {
    licenses: normalized.items,
    totalCount: normalized.total,
    pageCount: normalized.totalPages,
  };
}

export async function getLicense(id: string): Promise<License> {
  return api.get<License>(`/api/licensing/licenses/${id}`);
}

export async function getLicenseByKey(licenseKey: string): Promise<License> {
  return api.get<License>(`/api/licensing/licenses/by-key/${licenseKey}`);
}

export interface CreateLicenseData {
  productId: string;
  customerId?: string;
  type: LicenseType;
  seats?: number;
  features?: string[];
  expiresAt?: string;
  metadata?: Record<string, unknown>;
}

export async function createLicense(data: CreateLicenseData): Promise<License> {
  return api.post<License>("/api/licensing/licenses", {
    product_id: data.productId,
    customer_id: data.customerId,
    type: data.type,
    seats: data.seats ?? 1,
    features: data.features,
    expires_at: data.expiresAt,
    metadata: data.metadata,
  });
}

export async function updateLicense(
  id: string,
  data: Partial<{
    seats: number;
    features: string[];
    status: LicenseStatus;
    expiresAt: string;
    metadata: Record<string, unknown>;
  }>
): Promise<License> {
  return api.put<License>(`/api/licensing/licenses/${id}`, {
    seats: data.seats,
    features: data.features,
    status: data.status,
    expires_at: data.expiresAt,
    metadata: data.metadata,
  });
}

export async function deleteLicense(id: string): Promise<void> {
  return api.delete(`/api/licensing/licenses/${id}`);
}

// ============================================================================
// License Validation
// ============================================================================

export interface LicenseValidationResult {
  valid: boolean;
  licenseId?: string;
  status?: LicenseStatus;
  expiresAt?: string;
  features?: string[];
  remainingSeats?: number;
  message?: string;
  errorCode?: string;
}

export async function validateLicense(licenseKey: string): Promise<LicenseValidationResult> {
  return api.post<LicenseValidationResult>(`/api/licensing/licenses/${licenseKey}/validate`);
}

export async function validateActivation(
  activationKey: string
): Promise<LicenseValidationResult & { activationId?: string }> {
  return api.post(`/api/licensing/activations/${activationKey}/validate`);
}

// ============================================================================
// License Activations
// ============================================================================

export async function getLicenseActivations(licenseId: string): Promise<LicenseActivation[]> {
  return api.get<LicenseActivation[]>(`/api/licensing/licenses/${licenseId}/activations`);
}

export async function createActivation(data: {
  licenseKey: string;
  deviceId: string;
  deviceName?: string;
  metadata?: Record<string, unknown>;
}): Promise<LicenseActivation> {
  return api.post<LicenseActivation>("/api/licensing/activations", {
    license_key: data.licenseKey,
    device_id: data.deviceId,
    device_name: data.deviceName,
    metadata: data.metadata,
  });
}

export async function deactivateActivation(activationId: string): Promise<void> {
  return api.delete(`/api/licensing/activations/${activationId}`);
}

export async function sendHeartbeat(
  activationKey: string,
  metadata?: Record<string, unknown>
): Promise<{ acknowledged: boolean; expiresAt?: string }> {
  return api.post(`/api/licensing/activations/${activationKey}/heartbeat`, {
    metadata,
  });
}

// ============================================================================
// License Operations
// ============================================================================

export async function renewLicense(
  id: string,
  data: {
    expiresAt: string;
    seats?: number;
  }
): Promise<License> {
  return api.post<License>(`/api/licensing/licenses/${id}/renew`, {
    expires_at: data.expiresAt,
    seats: data.seats,
  });
}

export async function transferLicense(
  id: string,
  data: {
    newCustomerId: string;
    transferNote?: string;
  }
): Promise<License> {
  return api.post<License>(`/api/licensing/licenses/${id}/transfer`, {
    new_customer_id: data.newCustomerId,
    transfer_note: data.transferNote,
  });
}

export async function suspendLicense(id: string, reason?: string): Promise<License> {
  return api.post<License>(`/api/licensing/licenses/${id}/suspend`, { reason });
}

export async function reactivateLicense(id: string): Promise<License> {
  return api.post<License>(`/api/licensing/licenses/${id}/reactivate`);
}

// ============================================================================
// License Templates
// ============================================================================

export interface LicenseTemplate {
  id: string;
  name: string;
  productId: string;
  type: LicenseType;
  defaultSeats: number;
  defaultFeatures: string[];
  validityDays?: number;
  description?: string;
}

export async function getLicenseTemplates(): Promise<LicenseTemplate[]> {
  return api.get<LicenseTemplate[]>("/api/licensing/templates");
}

export async function createLicenseFromTemplate(
  templateId: string,
  data: {
    customerId?: string;
    seats?: number;
    expiresAt?: string;
  }
): Promise<License> {
  return api.post<License>(`/api/licensing/templates/${templateId}/create`, {
    customer_id: data.customerId,
    seats: data.seats,
    expires_at: data.expiresAt,
  });
}

// ============================================================================
// Emergency Codes
// ============================================================================

export async function generateEmergencyCode(licenseId: string): Promise<{
  code: string;
  expiresAt: string;
  validHours: number;
}> {
  return api.post(`/api/licensing/licenses/${licenseId}/emergency-code`);
}

export async function validateEmergencyCode(code: string): Promise<LicenseValidationResult> {
  return api.post("/api/licensing/emergency-codes/validate", { code });
}
