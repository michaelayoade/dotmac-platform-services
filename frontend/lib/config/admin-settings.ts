/**
 * Admin Settings Configuration
 *
 * Defines category metadata including icons, labels, and descriptions
 * for the admin settings UI.
 */

import {
  Mail,
  Database,
  Server,
  Shield,
  HardDrive,
  Building2,
  Globe,
  Gauge,
  Activity,
  Layers,
  Flag,
  CreditCard,
  Key,
  type LucideIcon,
} from "lucide-react";
import type { SettingsCategory } from "@/lib/api/admin-settings";

export interface CategoryConfig {
  icon: LucideIcon;
  label: string;
  description: string;
  color: string;
}

export const categoryConfig: Record<SettingsCategory, CategoryConfig> = {
  email: {
    icon: Mail,
    label: "Email & SMTP",
    description: "Configure email delivery and SMTP settings",
    color: "text-blue-500",
  },
  database: {
    icon: Database,
    label: "Database",
    description: "Database connection and pooling configuration",
    color: "text-green-500",
  },
  redis: {
    icon: Server,
    label: "Redis Cache",
    description: "Cache and session storage settings",
    color: "text-red-500",
  },
  vault: {
    icon: Shield,
    label: "Secrets Management",
    description: "HashiCorp Vault integration settings",
    color: "text-purple-500",
  },
  storage: {
    icon: HardDrive,
    label: "Object Storage",
    description: "S3/MinIO storage configuration",
    color: "text-orange-500",
  },
  tenant: {
    icon: Building2,
    label: "Multi-Tenancy",
    description: "Tenant isolation and management settings",
    color: "text-indigo-500",
  },
  cors: {
    icon: Globe,
    label: "CORS",
    description: "Cross-origin resource sharing configuration",
    color: "text-cyan-500",
  },
  rate_limit: {
    icon: Gauge,
    label: "Rate Limiting",
    description: "API rate limit configuration",
    color: "text-yellow-500",
  },
  observability: {
    icon: Activity,
    label: "Observability",
    description: "Logging and monitoring settings",
    color: "text-pink-500",
  },
  celery: {
    icon: Layers,
    label: "Background Tasks",
    description: "Celery worker configuration",
    color: "text-teal-500",
  },
  features: {
    icon: Flag,
    label: "Feature Flags",
    description: "Platform feature toggles",
    color: "text-violet-500",
  },
  billing: {
    icon: CreditCard,
    label: "Billing",
    description: "Billing system settings",
    color: "text-emerald-500",
  },
  jwt: {
    icon: Key,
    label: "JWT & Auth",
    description: "Authentication token settings",
    color: "text-amber-500",
  },
};

/**
 * Get category configuration by category key.
 */
export function getCategoryConfig(category: SettingsCategory): CategoryConfig {
  return categoryConfig[category] ?? {
    icon: Flag,
    label: category,
    description: `Settings for ${category}`,
    color: "text-gray-500",
  };
}

/**
 * All settings categories in display order.
 */
export const categoryOrder: SettingsCategory[] = [
  "email",
  "database",
  "redis",
  "vault",
  "storage",
  "tenant",
  "cors",
  "rate_limit",
  "observability",
  "celery",
  "features",
  "billing",
  "jwt",
];

/**
 * Map field types from backend to input types.
 */
export const fieldTypeMap: Record<string, string> = {
  str: "text",
  string: "text",
  int: "number",
  integer: "number",
  float: "number",
  bool: "toggle",
  boolean: "toggle",
  email: "email",
  url: "url",
  json: "json",
  list: "json",
  dict: "json",
  secret: "password",
  password: "password",
};

/**
 * Get the input type for a field based on its backend type.
 */
export function getFieldInputType(type: string, sensitive: boolean): string {
  if (sensitive) {
    return "password";
  }
  return fieldTypeMap[type.toLowerCase()] ?? "text";
}
