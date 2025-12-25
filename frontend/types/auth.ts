// Authentication & Authorization Types

/**
 * User roles available in the system
 */
export type UserRole =
  | "super_admin"
  | "tenant_admin"
  | "manager"
  | "operator"
  | "viewer"
  | "api_user";

/**
 * Available permissions in the system
 */
export type Permission =
  // User management
  | "users.view"
  | "users.create"
  | "users.update"
  | "users.delete"
  | "users.manage_roles"
  // Tenant management
  | "tenants.view"
  | "tenants.create"
  | "tenants.update"
  | "tenants.delete"
  | "tenants.manage_settings"
  // Billing
  | "billing.view"
  | "billing.manage"
  | "billing.view_invoices"
  | "billing.manage_subscriptions"
  // Customers
  | "customers.view"
  | "customers.create"
  | "customers.update"
  | "customers.delete"
  // Deployments
  | "deployments.view"
  | "deployments.create"
  | "deployments.update"
  | "deployments.delete"
  | "deployments.manage"
  // Analytics
  | "analytics.view"
  | "analytics.export"
  // Settings
  | "settings.view"
  | "settings.manage"
  // API Keys
  | "api_keys.view"
  | "api_keys.create"
  | "api_keys.revoke";

/**
 * Extended user type with platform-specific fields
 */
export interface PlatformUser {
  id: string;
  username?: string | null;
  email?: string | null;
  fullName?: string | null;
  firstName?: string | null;
  lastName?: string | null;
  avatarUrl?: string | null;
  roles: string[];
  permissions: string[];
  isPlatformAdmin: boolean;
  tenantId?: string | null;
  partnerId?: string | null;
  managedTenantIds?: string[] | null;
  mfaEnabled?: boolean;
  mfaBackupCodesRemaining?: number;
  activeOrganization?: {
    id: string;
    name: string;
    slug?: string | null;
    role?: string | null;
    permissions?: string[];
  } | null;
}

/**
 * Login credentials
 */
export interface LoginCredentials {
  email: string;
  password: string;
  mfaCode?: string;
  rememberMe?: boolean;
}

/**
 * Login response
 */
export interface LoginResponse {
  user: PlatformUser;
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
  mfaRequired?: boolean;
}

/**
 * OAuth provider configuration
 */
export interface OAuthProvider {
  id: string;
  name: string;
  type: "google" | "microsoft" | "github" | "okta" | "custom";
  enabled: boolean;
  clientId?: string;
  tenantId?: string; // For Microsoft
}

/**
 * MFA setup response
 */
export interface MfaSetupResponse {
  secret: string;
  qrCodeUrl: string;
  backupCodes: string[];
}

/**
 * Session information
 */
export interface SessionInfo {
  id: string;
  device: string;
  browser: string;
  os: string;
  ip: string;
  location?: string;
  lastActive: string;
  createdAt: string;
  current: boolean;
}

/**
 * Password requirements
 */
export interface PasswordPolicy {
  minLength: number;
  requireUppercase: boolean;
  requireLowercase: boolean;
  requireNumbers: boolean;
  requireSpecialChars: boolean;
  maxAge?: number; // Days until password expires
  preventReuse?: number; // Number of previous passwords to check
}
