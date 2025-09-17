import { z } from 'zod';
import { EntityType, PortalVariant, ValidationContext } from '../types';

// Base validation schemas
export const baseEntitySchema = z.object({
  id: z.string().uuid().optional(),
  createdAt: z.string().datetime().optional(),
  updatedAt: z.string().datetime().optional(),
  createdBy: z.string().uuid().optional(),
  updatedBy: z.string().uuid().optional(),
});

// Address schema (reusable)
export const addressSchema = z.object({
  street: z.string().min(1, 'Street address is required').max(200),
  city: z.string().min(1, 'City is required').max(100),
  state: z.string().min(2, 'State is required').max(50),
  zipCode: z.string().min(5, 'Valid ZIP code required').max(10),
  country: z.string().min(2, 'Country is required').max(50).default('US'),
});

// Phone number validation with international support
export const phoneSchema = z
  .string()
  .regex(/^\+?[1-9]\d{1,14}$/, 'Please enter a valid phone number')
  .transform((phone) => (phone.startsWith('+') ? phone : `+1${phone}`));

// Customer schema with portal-specific variations
export const baseCustomerSchema = baseEntitySchema.extend({
  name: z
    .string()
    .min(2, 'Name must be at least 2 characters')
    .max(100, 'Name must not exceed 100 characters')
    .regex(/^[a-zA-Z\s\-'\.]+$/, 'Name contains invalid characters'),

  email: z
    .string()
    .email('Please enter a valid email address')
    .max(255, 'Email must not exceed 255 characters')
    .toLowerCase(),

  phone: phoneSchema,

  address: addressSchema,

  status: z.enum(['active', 'inactive', 'suspended']).default('active'),

  serviceLevel: z.enum(['basic', 'premium', 'enterprise']).default('basic'),

  billingInfo: z
    .object({
      paymentMethod: z.enum(['credit_card', 'bank_transfer', 'check']),
      billingAddress: addressSchema.optional(),
    })
    .optional(),
});

// Tenant schema
export const tenantSchema = baseEntitySchema.extend({
  name: z
    .string()
    .min(2, 'Tenant name must be at least 2 characters')
    .max(100, 'Tenant name must not exceed 100 characters')
    .regex(/^[a-zA-Z0-9\s\-_]+$/, 'Tenant name contains invalid characters'),

  domain: z
    .string()
    .min(3, 'Domain must be at least 3 characters')
    .max(63, 'Domain must not exceed 63 characters')
    .regex(/^[a-z0-9-]+$/, 'Domain must contain only lowercase letters, numbers, and hyphens')
    .refine(
      (domain) => !domain.startsWith('-') && !domain.endsWith('-'),
      'Domain cannot start or end with a hyphen'
    ),

  plan: z.enum(['starter', 'professional', 'enterprise']).default('starter'),

  status: z.enum(['active', 'trial', 'suspended', 'cancelled']).default('trial'),

  limits: z.object({
    users: z.number().int().min(1).max(10000),
    storage: z.number().int().min(1).max(10000), // GB
    bandwidth: z.number().int().min(10).max(100000), // GB/month
    apiCalls: z.number().int().min(1000).max(10000000), // per month
  }),

  settings: z.object({
    timezone: z.string().min(1, 'Timezone is required'),
    currency: z.string().length(3, 'Currency must be 3 characters'),
    language: z.string().length(2, 'Language must be 2 characters'),
  }),
});

// User schema
export const userSchema = baseEntitySchema.extend({
  firstName: z
    .string()
    .min(1, 'First name is required')
    .max(50, 'First name must not exceed 50 characters')
    .regex(/^[a-zA-Z\s\-'\.]+$/, 'First name contains invalid characters'),

  lastName: z
    .string()
    .min(1, 'Last name is required')
    .max(50, 'Last name must not exceed 50 characters')
    .regex(/^[a-zA-Z\s\-'\.]+$/, 'Last name contains invalid characters'),

  email: z
    .string()
    .email('Please enter a valid email address')
    .max(255, 'Email must not exceed 255 characters')
    .toLowerCase(),

  phone: phoneSchema.optional(),

  role: z.string().min(1, 'Role is required'),

  permissions: z.array(z.string()).default([]),

  status: z.enum(['active', 'inactive', 'pending']).default('pending'),

  lastLogin: z.string().datetime().optional(),

  mfaEnabled: z.boolean().default(false),

  tenantId: z.string().uuid().optional(),
});

// Device schema
export const deviceSchema = baseEntitySchema.extend({
  name: z
    .string()
    .min(1, 'Device name is required')
    .max(100, 'Device name must not exceed 100 characters'),

  type: z.enum(['router', 'switch', 'access-point', 'modem', 'ont', 'other']),

  model: z.string().min(1, 'Model is required').max(100, 'Model must not exceed 100 characters'),

  manufacturer: z
    .string()
    .min(1, 'Manufacturer is required')
    .max(100, 'Manufacturer must not exceed 100 characters'),

  serialNumber: z
    .string()
    .min(1, 'Serial number is required')
    .max(100, 'Serial number must not exceed 100 characters')
    .regex(/^[a-zA-Z0-9\-_]+$/, 'Serial number contains invalid characters'),

  macAddress: z
    .string()
    .regex(/^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$/, 'Please enter a valid MAC address'),

  ipAddress: z
    .string()
    .ip({ version: 'v4', message: 'Please enter a valid IPv4 address' })
    .optional(),

  location: z.object({
    site: z.string().min(1, 'Site is required'),
    rack: z.string().optional(),
    position: z.string().optional(),
    coordinates: z
      .object({
        lat: z.number().min(-90).max(90),
        lng: z.number().min(-180).max(180),
      })
      .optional(),
  }),

  status: z.enum(['online', 'offline', 'maintenance', 'error']).default('offline'),

  customerId: z.string().uuid().optional(),
});

// Service schema
export const serviceSchema = baseEntitySchema.extend({
  name: z
    .string()
    .min(1, 'Service name is required')
    .max(100, 'Service name must not exceed 100 characters'),

  type: z.enum(['internet', 'phone', 'tv', 'bundle']),

  plan: z.string().min(1, 'Plan is required').max(100, 'Plan must not exceed 100 characters'),

  speed: z
    .object({
      download: z.number().min(1, 'Download speed must be at least 1 Mbps'),
      upload: z.number().min(1, 'Upload speed must be at least 1 Mbps'),
    })
    .optional(),

  pricing: z.object({
    monthlyRate: z.number().min(0, 'Monthly rate cannot be negative'),
    setupFee: z.number().min(0, 'Setup fee cannot be negative').default(0),
    currency: z.string().length(3, 'Currency must be 3 characters').default('USD'),
  }),

  status: z.enum(['active', 'pending', 'suspended', 'cancelled']).default('pending'),

  customerId: z.string().uuid(),

  installationDate: z.string().datetime().optional(),
});

// Schema registry for easy access
export const entitySchemas = {
  customer: baseCustomerSchema,
  tenant: tenantSchema,
  user: userSchema,
  device: deviceSchema,
  service: serviceSchema,
} as const;

// Portal-specific schema variations
export function getEntitySchema(
  entityType: EntityType,
  portalVariant: PortalVariant,
  context?: ValidationContext
) {
  const baseSchema = entitySchemas[entityType as keyof typeof entitySchemas];

  if (!baseSchema) {
    throw new Error(`No schema found for entity type: ${entityType}`);
  }

  // Apply portal-specific variations
  switch (portalVariant) {
    case 'customer':
      return applyCustomerPortalVariations(baseSchema, entityType, context);

    case 'technician':
      return applyTechnicianPortalVariations(baseSchema, entityType, context);

    case 'management-admin':
      return applyManagementAdminVariations(baseSchema, entityType, context);

    default:
      return baseSchema;
  }
}

// Portal-specific schema variations
function applyCustomerPortalVariations(
  schema: z.ZodSchema,
  entityType: EntityType,
  context?: ValidationContext
) {
  if (entityType === 'customer') {
    // Customer portal: customers can only edit their own profile
    // Remove sensitive fields like status, serviceLevel
    return baseCustomerSchema.omit({
      status: true,
      serviceLevel: true,
    });
  }
  return schema;
}

function applyTechnicianPortalVariations(
  schema: z.ZodSchema,
  entityType: EntityType,
  context?: ValidationContext
) {
  if (entityType === 'device') {
    // Technician portal: add field validation requirements
    return deviceSchema.extend({
      // Require installation photos for technicians
      installationPhotos: z
        .array(z.string().url())
        .min(1, 'At least one installation photo is required'),
      installationNotes: z.string().min(10, 'Installation notes must be at least 10 characters'),
    });
  }
  return schema;
}

function applyManagementAdminVariations(
  schema: z.ZodSchema,
  entityType: EntityType,
  context?: ValidationContext
) {
  if (entityType === 'tenant') {
    // Management admin: add advanced tenant fields
    return tenantSchema.extend({
      billingContactEmail: z.string().email('Valid billing contact email required'),
      technicalContactEmail: z.string().email('Valid technical contact email required'),
      contractStartDate: z.string().datetime(),
      contractEndDate: z.string().datetime(),
    });
  }
  return schema;
}

// Validation utilities
export function validateEntity<T>(
  data: unknown,
  entityType: EntityType,
  portalVariant: PortalVariant,
  context?: ValidationContext
): { success: true; data: T } | { success: false; error: z.ZodError } {
  try {
    const schema = getEntitySchema(entityType, portalVariant, context);
    const validatedData = schema.parse(data);
    return { success: true, data: validatedData as T };
  } catch (error) {
    if (error instanceof z.ZodError) {
      return { success: false, error };
    }
    throw error;
  }
}

// Field-level validation for real-time feedback
export function validateField(
  fieldName: string,
  value: any,
  entityType: EntityType,
  portalVariant: PortalVariant,
  context?: ValidationContext
): { isValid: boolean; error?: string } {
  try {
    const schema = getEntitySchema(entityType, portalVariant, context);

    // Extract field schema if it exists
    if (schema instanceof z.ZodObject) {
      const fieldSchema = schema.shape[fieldName];
      if (fieldSchema) {
        fieldSchema.parse(value);
      }
    }

    return { isValid: true };
  } catch (error) {
    if (error instanceof z.ZodError) {
      return {
        isValid: false,
        error: error.errors[0]?.message || 'Invalid value',
      };
    }
    return { isValid: false, error: 'Validation error' };
  }
}
