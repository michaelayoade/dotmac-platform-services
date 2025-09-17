/**
 * ISP-Specific Validation Schemas
 * Domain-specific validation for telecommunications
 */

import { z } from 'zod';
import { email, phoneNumber, ipAddress, macAddress, createRequiredString } from './common';

// ISP Service Plans
export const servicePlanSchema = z.object({
  name: createRequiredString('Plan name'),
  description: z.string().optional(),
  downloadSpeed: z.number().min(1, 'Download speed must be at least 1 Mbps'),
  uploadSpeed: z.number().min(1, 'Upload speed must be at least 1 Mbps'),
  dataLimit: z.number().optional(), // null for unlimited
  price: z.number().min(0, 'Price cannot be negative'),
  setupFee: z.number().min(0, 'Setup fee cannot be negative'),
  contractLength: z.enum(['month-to-month', '12-months', '24-months']),
  isActive: z.boolean().default(true),
});

// Customer Management
export const customerSchema = z.object({
  firstName: createRequiredString('First name'),
  lastName: createRequiredString('Last name'),
  email,
  phone: phoneNumber,
  alternatePhone: phoneNumber.optional(),
  serviceAddress: z.object({
    street: createRequiredString('Street address'),
    unit: z.string().optional(),
    city: createRequiredString('City'),
    state: z.string().min(2).max(2),
    zipCode: z.string().regex(/^\d{5}(-\d{4})?$/, 'Invalid ZIP code'),
    coordinates: z
      .object({
        lat: z.number(),
        lng: z.number(),
      })
      .optional(),
  }),
  billingAddress: z
    .object({
      sameAsService: z.boolean(),
      street: z.string().optional(),
      city: z.string().optional(),
      state: z.string().optional(),
      zipCode: z.string().optional(),
    })
    .optional(),
  servicePlan: createRequiredString('Service plan'),
  installationDate: z.date().optional(),
  notes: z.string().optional(),
});

// Network Equipment
export const equipmentSchema = z.object({
  type: z.enum(['router', 'modem', 'access-point', 'switch', 'ont', 'cpe']),
  brand: createRequiredString('Brand'),
  model: createRequiredString('Model'),
  serialNumber: createRequiredString('Serial number'),
  macAddress: macAddress.optional(),
  firmwareVersion: z.string().optional(),
  location: createRequiredString('Location'),
  ipAddress: ipAddress.optional(),
  status: z.enum(['active', 'inactive', 'maintenance', 'retired']).default('active'),
  installDate: z.date().optional(),
  warrantyExpires: z.date().optional(),
  customerId: z.string().optional(),
});

// Network Infrastructure
export const networkNodeSchema = z.object({
  name: createRequiredString('Node name'),
  type: z.enum(['tower', 'ptp', 'ptmp', 'fiber-node', 'distribution-point']),
  location: z.object({
    address: createRequiredString('Address'),
    coordinates: z.object({
      lat: z.number(),
      lng: z.number(),
      elevation: z.number().optional(),
    }),
  }),
  ipRange: z.string().regex(/^(\d{1,3}\.){3}\d{1,3}\/\d{1,2}$/, 'Invalid CIDR notation'),
  capacity: z.number().min(1, 'Capacity must be positive'),
  currentLoad: z.number().min(0).max(100, 'Load must be between 0-100%'),
  equipment: z.array(z.string()).default([]),
  status: z.enum(['online', 'offline', 'maintenance', 'planned']).default('online'),
});

// Technician Work Orders
export const workOrderSchema = z.object({
  type: z.enum(['installation', 'maintenance', 'repair', 'upgrade', 'disconnection']),
  priority: z.enum(['low', 'medium', 'high', 'urgent']).default('medium'),
  customerId: createRequiredString('Customer ID'),
  description: createRequiredString('Description'),
  scheduledDate: z.date(),
  estimatedDuration: z.number().min(15, 'Duration must be at least 15 minutes'),
  requiredSkills: z.array(z.string()).default([]),
  equipment: z.array(z.string()).default([]),
  notes: z.string().optional(),
  completionNotes: z.string().optional(),
  status: z.enum(['scheduled', 'in-progress', 'completed', 'cancelled']).default('scheduled'),
});

// Support Tickets
export const supportTicketSchema = z.object({
  customerId: createRequiredString('Customer ID'),
  subject: createRequiredString('Subject'),
  description: createRequiredString('Description'),
  category: z.enum(['technical', 'billing', 'service', 'equipment', 'other']),
  priority: z.enum(['low', 'medium', 'high', 'urgent']).default('medium'),
  status: z.enum(['open', 'in-progress', 'resolved', 'closed']).default('open'),
  assignedTo: z.string().optional(),
  attachments: z.array(z.string()).default([]),
});

// Reseller/Partner Management
export const partnerSchema = z.object({
  companyName: createRequiredString('Company name'),
  contactPerson: createRequiredString('Contact person'),
  email,
  phone: phoneNumber,
  businessAddress: z.object({
    street: createRequiredString('Street address'),
    city: createRequiredString('City'),
    state: z.string().min(2).max(2),
    zipCode: z.string().regex(/^\d{5}(-\d{4})?$/),
  }),
  taxId: z.string().optional(),
  territory: z.array(z.string()).min(1, 'At least one territory required'),
  commissionRate: z.number().min(0).max(100, 'Commission rate must be 0-100%'),
  contractStart: z.date(),
  contractEnd: z.date().optional(),
  status: z.enum(['active', 'inactive', 'suspended']).default('active'),
  bankingInfo: z
    .object({
      accountNumber: z.string(),
      routingNumber: z.string().length(9, 'Routing number must be 9 digits'),
      accountType: z.enum(['checking', 'savings']),
    })
    .optional(),
});

// Network Performance Monitoring
export const performanceMetricSchema = z.object({
  nodeId: createRequiredString('Node ID'),
  timestamp: z.date(),
  metrics: z.object({
    latency: z.number().min(0),
    jitter: z.number().min(0),
    packetLoss: z.number().min(0).max(100),
    throughput: z.number().min(0),
    errorRate: z.number().min(0).max(100),
    uptime: z.number().min(0).max(100),
  }),
  alertThresholds: z
    .object({
      latencyMax: z.number().default(50),
      jitterMax: z.number().default(10),
      packetLossMax: z.number().default(1),
      uptimeMin: z.number().default(99),
    })
    .optional(),
});
