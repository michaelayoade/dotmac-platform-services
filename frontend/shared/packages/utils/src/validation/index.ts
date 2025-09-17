/**
 * Consolidated validation schemas and utilities using Zod
 * Combines validation logic from headless, primitives, and security packages
 */

import { z } from 'zod';

// Common validation schemas
export const commonSchemas = {
  // Basic types
  email: z.string().email('Invalid email format').min(1, 'Email is required'),
  phone: z.string().regex(/^[\+]?[\d\-\(\)\s]{10,20}$/, 'Invalid phone number format'),
  url: z.string().url('Invalid URL format'),
  uuid: z.string().uuid('Invalid UUID format'),

  // Text fields
  name: z.string().min(1, 'Name is required').max(100, 'Name too long'),
  description: z.string().max(500, 'Description too long').optional(),

  // Numeric
  positiveNumber: z.number().positive('Must be a positive number'),
  currency: z.number().min(0, 'Amount cannot be negative'),

  // Date/Time
  futureDate: z.date().refine((date) => date > new Date(), 'Date must be in the future'),
  pastDate: z.date().refine((date) => date < new Date(), 'Date must be in the past'),
};

// ISP-specific validation schemas
export const ispSchemas = {
  // Customer data
  customer: z.object({
    id: commonSchemas.uuid.optional(),
    name: commonSchemas.name,
    email: commonSchemas.email,
    phone: commonSchemas.phone,
    status: z.enum(['active', 'suspended', 'cancelled']),
    address: z.object({
      street: z.string().min(1, 'Street address is required'),
      city: z.string().min(1, 'City is required'),
      state: z.string().min(2, 'State is required').max(2, 'State must be 2 characters'),
      zip: z.string().regex(/^\d{5}(-\d{4})?$/, 'Invalid ZIP code format'),
    }),
    createdAt: z.date().optional(),
    updatedAt: z.date().optional(),
  }),

  // Service data
  service: z.object({
    id: commonSchemas.uuid.optional(),
    name: z.string().min(1, 'Service name is required'),
    type: z.enum(['internet', 'tv', 'phone', 'bundle']),
    speed: z.number().positive('Speed must be positive').optional(),
    price: commonSchemas.currency,
    description: commonSchemas.description,
  }),

  // Billing data
  invoice: z.object({
    id: commonSchemas.uuid.optional(),
    customerId: commonSchemas.uuid,
    amount: commonSchemas.currency,
    dueDate: commonSchemas.futureDate,
    status: z.enum(['draft', 'sent', 'paid', 'overdue', 'cancelled']),
    lineItems: z.array(
      z.object({
        description: z.string().min(1, 'Description is required'),
        quantity: commonSchemas.positiveNumber,
        unitPrice: commonSchemas.currency,
        total: commonSchemas.currency,
      })
    ),
  }),

  // Network/Technical data
  ipAddress: z.string().ip('Invalid IP address'),
  macAddress: z
    .string()
    .regex(/^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$/, 'Invalid MAC address format'),
  vlan: z.number().int().min(1).max(4094, 'VLAN ID must be between 1 and 4094'),
};

// Form validation utilities
export class FormValidator {
  static validateField<T>(
    schema: z.ZodSchema<T>,
    value: unknown
  ): { isValid: boolean; error?: string; data?: T } {
    try {
      const data = schema.parse(value);
      return { isValid: true, data };
    } catch (error) {
      if (error instanceof z.ZodError) {
        return { isValid: false, error: error.errors[0]?.message || 'Invalid input' };
      }
      return { isValid: false, error: 'Validation failed' };
    }
  }

  static validateForm<T>(
    schema: z.ZodSchema<T>,
    formData: unknown
  ): {
    isValid: boolean;
    errors?: Record<string, string>;
    data?: T;
  } {
    try {
      const data = schema.parse(formData);
      return { isValid: true, data };
    } catch (error) {
      if (error instanceof z.ZodError) {
        const errors: Record<string, string> = {};
        error.errors.forEach((err) => {
          const path = err.path.join('.');
          errors[path] = err.message;
        });
        return { isValid: false, errors };
      }
      return { isValid: false, errors: { _form: 'Validation failed' } };
    }
  }
}

// Convenience validation functions
export const validateEmail = (email: string) =>
  FormValidator.validateField(commonSchemas.email, email);

export const validatePhone = (phone: string) =>
  FormValidator.validateField(commonSchemas.phone, phone);

export const validateURL = (url: string) => FormValidator.validateField(commonSchemas.url, url);

export const validateCustomer = (customer: unknown) =>
  FormValidator.validateForm(ispSchemas.customer, customer);

export const validateService = (service: unknown) =>
  FormValidator.validateForm(ispSchemas.service, service);

export const validateInvoice = (invoice: unknown) =>
  FormValidator.validateForm(ispSchemas.invoice, invoice);

// Type exports for TypeScript
export type Customer = z.infer<typeof ispSchemas.customer>;
export type Service = z.infer<typeof ispSchemas.service>;
export type Invoice = z.infer<typeof ispSchemas.invoice>;
export type ValidationResult<T> = ReturnType<typeof FormValidator.validateField<T>>;
export type FormValidationResult<T> = ReturnType<typeof FormValidator.validateForm<T>>;
