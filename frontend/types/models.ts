// Domain Model Types
// Core business entities used across the platform

import type { UserRole, Permission } from "./auth";

export type { UserRole, Permission } from "./auth";

/**
 * Base entity with common fields
 */
export interface BaseEntity {
  id: string;
  createdAt: string;
  updatedAt: string;
}

/**
 * Plan type - can be a string (from list endpoints) or full object (from detail endpoints)
 */
export type TenantPlanType = "Enterprise" | "Professional" | "Starter" | "Free";

/**
 * Tenant entity
 */
export interface Tenant extends BaseEntity {
  name: string;
  slug: string;
  domain?: string;
  logo?: string;
  status: TenantStatus;
  plan: TenantPlanType | SubscriptionPlan; // String from list, object from detail
  settings?: TenantSettings;
  metadata?: Record<string, unknown>;
  userCount: number;
  storageUsed: number; // bytes
  storageLimit: number; // bytes
  mrr?: number; // Monthly recurring revenue in cents
  deploymentCount?: number;
}

export type TenantStatus = "active" | "inactive" | "suspended" | "trial" | "pending";

export interface TenantSettings {
  timezone: string;
  language: string;
  dateFormat: string;
  currency: string;
  mfaRequired: boolean;
  ssoEnabled: boolean;
  ipWhitelist?: string[];
  customBranding?: {
    primaryColor: string;
    logo: string;
    favicon: string;
  };
  features?: string[];
  limits?: Record<string, number>;
}

/**
 * User entity
 */
export interface User extends BaseEntity {
  email: string;
  name: string;
  avatar?: string;
  role: UserRole;
  permissions: Permission[];
  tenantId: string;
  status: UserStatus;
  phone?: string;
  timezone?: string;
  language?: string;
  mfaEnabled: boolean;
  lastLogin?: string;
  invitedBy?: string;
  teams?: string[];
}

export type UserStatus = "active" | "inactive" | "pending" | "suspended" | "invited";

/**
 * Customer entity (CRM)
 */
export interface Customer extends BaseEntity {
  tenantId: string;
  name: string;
  email: string;
  phone?: string;
  company?: string;
  status: CustomerStatus;
  type: CustomerType;
  assignedTo?: string;
  tags: string[];
  notes?: string;
  address?: Address;
  billingAddress?: Address; // Alias for address
  revenue: number;
  lifetimeValue: number;
  firstPurchase?: string;
  lastPurchase?: string;
  purchaseCount: number;
  metadata?: Record<string, unknown>;
}

export type CustomerStatus = "active" | "inactive" | "churned" | "prospect" | "lead";
export type CustomerType = "individual" | "business" | "enterprise";

export interface Address {
  line1: string;
  line2?: string;
  city: string;
  state: string;
  postalCode: string;
  country: string;
}

/**
 * Billing entities
 */
export interface Invoice extends BaseEntity {
  tenantId: string;
  customerId?: string;
  customer?: {
    id: string;
    name: string;
    email: string;
  };
  number: string;
  status: InvoiceStatus;
  amount: number;
  tax: number;
  total: number;
  currency: string;
  dueDate: string;
  paidAt?: string;
  items: InvoiceItem[];
  paymentMethod?: PaymentMethod;
}

export type InvoiceStatus = "draft" | "pending" | "paid" | "overdue" | "cancelled" | "refunded";

export interface InvoiceItem {
  id: string;
  description: string;
  quantity: number;
  unitPrice: number;
  total: number;
}

export interface PaymentMethod extends BaseEntity {
  tenantId: string;
  type: "card" | "bank_account" | "paypal";
  isDefault: boolean;
  // Flat card properties for convenience
  brand?: string;
  last4?: string;
  expMonth?: number;
  expYear?: number;
  // Nested structures for full details
  card?: {
    brand: string;
    last4: string;
    expiryMonth: number;
    expiryYear: number;
  };
  bankAccount?: {
    bankName: string;
    last4: string;
    accountType: "checking" | "savings";
  };
}

export interface Subscription extends BaseEntity {
  tenantId: string;
  customerId: string;
  customer?: Customer;
  plan?: SubscriptionPlan;
  status: SubscriptionStatus;
  currentPeriodStart: string;
  currentPeriodEnd: string;
  cancelAtPeriodEnd: boolean;
  trialEnd?: string;
  paymentMethodId?: string;
}

export type SubscriptionStatus = "active" | "canceled" | "past_due" | "trialing" | "paused";

/**
 * Receipt entity (payment confirmation)
 */
export interface Receipt extends BaseEntity {
  tenantId: string;
  customerId: string;
  customer?: Customer;
  invoiceId?: string;
  invoice?: Invoice;
  number: string;
  amount: number;
  tax: number;
  total: number;
  currency: string;
  paymentMethod?: PaymentMethod;
  paymentDate: string;
  status: ReceiptStatus;
  description?: string;
  metadata?: Record<string, unknown>;
}

export type ReceiptStatus = "completed" | "pending" | "failed" | "refunded";

export interface SubscriptionPlan {
  id: string;
  name: string;
  description: string;
  price: number;
  interval: "month" | "year";
  features: string[];
  limits: {
    users: number;
    storage: number; // GB
    apiCalls: number;
    deployments: number;
  };
}

/**
 * Deployment entities
 */
export interface Deployment extends BaseEntity {
  tenantId: string;
  name: string;
  environment: DeploymentEnvironment;
  status: DeploymentStatus;
  version: string;
  image: string;
  region?: string;
  replicas: number;
  resources: DeploymentResources;
  endpoints: DeploymentEndpoint[];
  healthCheck?: HealthCheck;
  lastDeployedAt?: string;
  lastDeployedBy?: string;
  envVars?: Record<string, string>;
}

export type DeploymentEnvironment = "production" | "staging" | "development" | "preview";
export type DeploymentStatus = "running" | "stopped" | "deploying" | "failed" | "pending" | "scaling";

export interface DeploymentResources {
  cpu: string; // millicores
  memory: string; // MB
  storage?: string; // GB
}

export interface DeploymentEndpoint {
  url: string;
  type: "public" | "internal";
  protocol: "http" | "https" | "grpc";
}

export interface HealthCheck {
  path: string;
  interval: number; // seconds
  timeout: number; // seconds
  healthyThreshold: number;
  unhealthyThreshold: number;
}

export interface DeploymentMetrics {
  cpu: number; // percentage
  memory: number; // percentage
  storage?: number; // percentage
  requestsPerMinute?: number;
  requests: number;
  errors: number;
  errorRate?: number; // percentage
  averageLatency?: number; // ms
  latencyP50: number; // ms
  latencyP95: number; // ms
  latencyP99: number; // ms
}

/**
 * API Key entity
 */
export interface ApiKey extends BaseEntity {
  tenantId: string;
  name: string;
  prefix: string; // First few characters for identification
  permissions: Permission[];
  expiresAt?: string;
  lastUsed?: string;
  usageCount: number;
  rateLimit: number; // requests per minute
  ipWhitelist?: string[];
  status: "active" | "revoked" | "expired";
}

/**
 * Notification entity
 */
export interface Notification extends BaseEntity {
  userId: string;
  tenantId: string;
  type: NotificationType;
  title: string;
  message: string;
  read: boolean;
  actionUrl?: string;
  metadata?: Record<string, unknown>;
}

export type NotificationType =
  | "info"
  | "warning"
  | "error"
  | "success"
  | "billing"
  | "security"
  | "deployment"
  | "system";

/**
 * Audit log entry
 */
export interface AuditLog extends BaseEntity {
  tenantId: string;
  userId: string;
  userName: string;
  action: string;
  resource: string;
  resourceId: string;
  changes?: {
    before?: Record<string, unknown>;
    after?: Record<string, unknown>;
  };
  ipAddress: string;
  userAgent: string;
  status: "success" | "failure";
  errorMessage?: string;
}
