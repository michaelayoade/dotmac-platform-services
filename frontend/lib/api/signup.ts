/**
 * Signup & Tenant Onboarding API
 *
 * Handles tenant registration, email verification, and onboarding flows
 */

import { api } from "./client";

// Types
export interface TenantOnboardingRequest {
  tenant: {
    name: string;
    slug: string;
    industry?: string;
    companySize?: string;
    country?: string;
    planType: "free" | "starter" | "professional" | "enterprise";
  };
  adminUser: {
    username: string;
    email: string;
    password: string;
    fullName?: string;
    roles?: string[];
    sendActivationEmail?: boolean;
  };
  options?: {
    applyDefaultSettings?: boolean;
    markOnboardingComplete?: boolean;
    activateTenant?: boolean;
  };
}

export interface PublicTenantOnboardingRequest {
  tenant: {
    name: string;
    slug: string;
    industry?: string;
    companySize?: string;
    country?: string;
    planType: "free" | "starter" | "professional" | "enterprise";
  };
  adminUser: {
    email: string;
    password: string;
    fullName?: string;
    username?: string;
  };
}

export interface PublicTenantOnboardingResponse {
  tenantId: string;
  tenantSlug: string;
  adminUserId?: string;
  verificationSent: boolean;
  message: string;
}

export interface TenantOnboardingResponse {
  tenant: {
    id: string;
    name: string;
    slug: string;
    status: string;
    planType: string;
  };
  created: boolean;
  onboardingStatus: string;
  adminUserId?: string;
  adminUserPassword?: string; // Only returned once
  invitations: Array<{
    id: string;
    email: string;
    role: string;
    status: string;
  }>;
  appliedSettings: string[];
  metadata: Record<string, unknown>;
  featureFlagsUpdated: boolean;
  warnings: string[];
  logs: string[];
}

export interface EmailVerificationRequest {
  token: string;
}

export interface EmailVerificationResponse {
  success: boolean;
  message: string;
  tenantId?: string;
  userId?: string;
}

export interface ResendVerificationRequest {
  email: string;
}

export interface ResendVerificationResponse {
  success: boolean;
  message: string;
}

/**
 * Create a new tenant with admin user (self-signup)
 */
export async function createTenantOnboarding(
  data: TenantOnboardingRequest
): Promise<TenantOnboardingResponse> {
  return api.post<TenantOnboardingResponse>("/api/v1/tenants/onboarding", data, {
    requiresAuth: true,
  });
}

/**
 * Create a new tenant via public self-signup
 */
export async function createPublicTenantOnboarding(
  data: PublicTenantOnboardingRequest
): Promise<PublicTenantOnboardingResponse> {
  return api.post<PublicTenantOnboardingResponse>("/api/v1/tenants/onboarding/public", data, {
    requiresAuth: false,
  });
}

/**
 * Verify email address with token
 */
export async function verifyEmail(
  data: EmailVerificationRequest
): Promise<EmailVerificationResponse> {
  const response = await api.post<{ message: string; email?: string; isVerified?: boolean }>(
    "/api/v1/auth/verify-email/confirm",
    data,
    { requiresAuth: false }
  );

  return {
    success: response.isVerified ?? true,
    message: response.message || "Email verified successfully",
  };
}

/**
 * Resend email verification
 */
export async function resendVerificationEmail(
  data: ResendVerificationRequest
): Promise<ResendVerificationResponse> {
  const response = await api.post<{ message: string }>(
    "/api/v1/auth/verify-email/resend",
    data,
    { requiresAuth: false }
  );

  return {
    success: true,
    message: response.message || "Verification email sent",
  };
}

/**
 * Check if email is already registered
 */
export async function checkEmailAvailability(
  email: string
): Promise<{ available: boolean; message?: string }> {
  return api.get<{ available: boolean; message?: string }>(
    "/api/v1/auth/check-email",
    {
      params: { email },
      requiresAuth: false,
    }
  );
}

/**
 * Check if slug is available for tenant
 */
export async function checkSlugAvailability(
  slug: string
): Promise<{ available: boolean; suggestions?: string[] }> {
  return api.get<{ available: boolean; suggestions?: string[] }>(
    "/api/v1/tenants/check-slug",
    {
      params: { slug },
      requiresAuth: false,
    }
  );
}
