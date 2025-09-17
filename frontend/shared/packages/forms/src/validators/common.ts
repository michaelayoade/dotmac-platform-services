/**
 * Common Validation Schemas
 * Reusable validation rules across all portals
 */

import { z } from 'zod';

// Base validation rules
export const email = z.string().email('Invalid email address');

export const password = z
  .string()
  .min(8, 'Password must be at least 8 characters')
  .regex(/(?=.*[a-z])/, 'Password must contain at least one lowercase letter')
  .regex(/(?=.*[A-Z])/, 'Password must contain at least one uppercase letter')
  .regex(/(?=.*\d)/, 'Password must contain at least one number');

export const strongPassword = password
  .min(12, 'Password must be at least 12 characters')
  .regex(/(?=.*[!@#$%^&*])/, 'Password must contain at least one special character');

export const phoneNumber = z
  .string()
  .regex(/^\+?[\d\s\-\(\)]+$/, 'Invalid phone number format')
  .min(10, 'Phone number must be at least 10 digits');

export const url = z.string().url('Invalid URL format');

export const ipAddress = z
  .string()
  .regex(
    /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/,
    'Invalid IP address'
  );

export const macAddress = z
  .string()
  .regex(/^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$/, 'Invalid MAC address format');

export const zipCode = z.string().regex(/^\d{5}(-\d{4})?$/, 'Invalid ZIP code format');

export const ssn = z.string().regex(/^\d{3}-?\d{2}-?\d{4}$/, 'Invalid SSN format');

// Common form schemas
export const loginSchema = z.object({
  email,
  password: z.string().min(1, 'Password is required'),
  rememberMe: z.boolean().optional(),
});

export const registerSchema = z
  .object({
    firstName: z.string().min(1, 'First name is required'),
    lastName: z.string().min(1, 'Last name is required'),
    email,
    password,
    confirmPassword: z.string(),
    agreeToTerms: z.boolean().refine((val) => val === true, 'You must agree to terms'),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  });

export const contactSchema = z.object({
  firstName: z.string().min(1, 'First name is required'),
  lastName: z.string().min(1, 'Last name is required'),
  email,
  phone: phoneNumber,
  company: z.string().optional(),
  message: z.string().min(10, 'Message must be at least 10 characters'),
});

export const addressSchema = z.object({
  street: z.string().min(1, 'Street address is required'),
  city: z.string().min(1, 'City is required'),
  state: z.string().min(2, 'State is required').max(2, 'State must be 2 characters'),
  zipCode,
  country: z.string().default('US'),
});

export const billingSchema = z.object({
  cardNumber: z.string().min(13, 'Card number must be at least 13 digits'),
  expiryMonth: z.number().min(1).max(12),
  expiryYear: z.number().min(new Date().getFullYear()),
  cvv: z.string().min(3).max(4),
  billingAddress: addressSchema,
});

// Utility functions
export const createRequiredString = (fieldName: string) =>
  z.string().min(1, `${fieldName} is required`);

export const createMinLength = (fieldName: string, min: number) =>
  z.string().min(min, `${fieldName} must be at least ${min} characters`);

export const createMaxLength = (fieldName: string, max: number) =>
  z.string().max(max, `${fieldName} must be no more than ${max} characters`);
