import { EntityType, FormMode, PortalVariant, EntityFormConfig, FormFieldConfig } from '../types';

/**
 * Generate entity form configuration based on entity type, mode, and portal variant
 * This centralizes all form configurations and makes them reusable across portals
 */
export function generateEntityFormConfig(
  entityType: EntityType,
  mode: FormMode,
  portalVariant: PortalVariant
): EntityFormConfig {
  const baseConfigs: Record<EntityType, Partial<EntityFormConfig>> = {
    customer: getCustomerFormConfig(mode, portalVariant),
    tenant: getTenantFormConfig(mode, portalVariant),
    user: getUserFormConfig(mode, portalVariant),
    device: getDeviceFormConfig(mode, portalVariant),
    service: getServiceFormConfig(mode, portalVariant),
    reseller: getResellerFormConfig(mode, portalVariant),
    technician: getTechnicianFormConfig(mode, portalVariant),
    'work-order': getWorkOrderFormConfig(mode, portalVariant),
    invoice: getInvoiceFormConfig(mode, portalVariant),
    ticket: getTicketFormConfig(mode, portalVariant),
  };

  const baseConfig = baseConfigs[entityType];

  if (!baseConfig) {
    throw new Error(`No form configuration found for entity type: ${entityType}`);
  }

  // Apply default values
  return {
    entity: entityType,
    mode,
    title: baseConfig.title,
    subtitle: baseConfig.subtitle,
    fields: baseConfig.fields || [],
    sections: baseConfig.sections,
    actions: baseConfig.actions,
    layout: baseConfig.layout || 'single-column',
    portalCustomizations: baseConfig.portalCustomizations || {},
    ...baseConfig,
  };
}

// Customer form configuration
function getCustomerFormConfig(
  mode: FormMode,
  portalVariant: PortalVariant
): Partial<EntityFormConfig> {
  const fields: FormFieldConfig[] = [
    {
      name: 'name',
      label: 'Customer Name',
      type: 'text',
      placeholder: 'Enter customer name',
      required: true,
      description: 'Full name of the customer',
    },
    {
      name: 'email',
      label: 'Email Address',
      type: 'email',
      placeholder: 'customer@example.com',
      required: true,
      description: 'Primary email address for communications',
    },
    {
      name: 'phone',
      label: 'Phone Number',
      type: 'phone',
      placeholder: '+1 (555) 123-4567',
      required: true,
      description: 'Primary contact phone number',
    },
    {
      name: 'address',
      label: 'Address',
      type: 'address',
      required: true,
      description: 'Service address for the customer',
    },
    {
      name: 'status',
      label: 'Status',
      type: 'select',
      options: [
        { value: 'active', label: 'Active' },
        { value: 'inactive', label: 'Inactive' },
        { value: 'suspended', label: 'Suspended' },
      ],
      required: true,
      portalVariants: ['admin', 'management-admin', 'reseller'], // Hide from customer portal
      permissions: ['customers.manage'],
    },
    {
      name: 'serviceLevel',
      label: 'Service Level',
      type: 'select',
      options: [
        { value: 'basic', label: 'Basic' },
        { value: 'premium', label: 'Premium' },
        { value: 'enterprise', label: 'Enterprise' },
      ],
      required: true,
      portalVariants: ['admin', 'management-admin', 'reseller'],
      permissions: ['customers.manage'],
    },
  ];

  return {
    title:
      mode === 'create'
        ? 'Add New Customer'
        : mode === 'edit'
          ? 'Edit Customer'
          : 'Customer Details',
    subtitle: mode === 'create' ? 'Create a new customer account' : 'Manage customer information',
    fields,
    sections: [
      {
        title: 'Basic Information',
        fields: ['name', 'email', 'phone'],
      },
      {
        title: 'Address Information',
        fields: ['address'],
      },
      {
        title: 'Account Settings',
        fields: ['status', 'serviceLevel'],
      },
    ],
    layout: 'single-column',
    portalCustomizations: {
      customer: {
        // Customer portal customizations
        fields: fields.filter((f) => !f.portalVariants || f.portalVariants.includes('customer')),
        sections: [
          {
            title: 'Personal Information',
            fields: ['name', 'email', 'phone'],
          },
          {
            title: 'Service Address',
            fields: ['address'],
          },
        ],
      },
      technician: {
        // Technician portal customizations - minimal fields for field service
        fields: [
          { name: 'name', label: 'Customer', type: 'text', disabled: true },
          { name: 'phone', label: 'Contact Number', type: 'phone', disabled: true },
          { name: 'address', label: 'Service Location', type: 'address', disabled: true },
        ],
        layout: 'single-column',
      },
    },
  };
}

// Tenant form configuration
function getTenantFormConfig(
  mode: FormMode,
  portalVariant: PortalVariant
): Partial<EntityFormConfig> {
  const fields: FormFieldConfig[] = [
    {
      name: 'name',
      label: 'Tenant Name',
      type: 'text',
      placeholder: 'Acme ISP Company',
      required: true,
    },
    {
      name: 'domain',
      label: 'Subdomain',
      type: 'text',
      placeholder: 'acme-isp',
      required: true,
      description: 'Unique subdomain for tenant access',
    },
    {
      name: 'plan',
      label: 'Subscription Plan',
      type: 'select',
      options: [
        { value: 'starter', label: 'Starter' },
        { value: 'professional', label: 'Professional' },
        { value: 'enterprise', label: 'Enterprise' },
      ],
      required: true,
    },
    {
      name: 'status',
      label: 'Status',
      type: 'select',
      options: [
        { value: 'active', label: 'Active' },
        { value: 'trial', label: 'Trial' },
        { value: 'suspended', label: 'Suspended' },
        { value: 'cancelled', label: 'Cancelled' },
      ],
      required: true,
      portalVariants: ['management-admin'],
      permissions: ['tenants.manage'],
    },
  ];

  return {
    title:
      mode === 'create' ? 'Create New Tenant' : mode === 'edit' ? 'Edit Tenant' : 'Tenant Details',
    subtitle: mode === 'create' ? 'Set up a new ISP tenant' : 'Manage tenant configuration',
    fields,
    sections: [
      {
        title: 'Basic Information',
        fields: ['name', 'domain'],
      },
      {
        title: 'Subscription',
        fields: ['plan', 'status'],
      },
    ],
  };
}

// User form configuration
function getUserFormConfig(
  mode: FormMode,
  portalVariant: PortalVariant
): Partial<EntityFormConfig> {
  const fields: FormFieldConfig[] = [
    {
      name: 'firstName',
      label: 'First Name',
      type: 'text',
      required: true,
    },
    {
      name: 'lastName',
      label: 'Last Name',
      type: 'text',
      required: true,
    },
    {
      name: 'email',
      label: 'Email Address',
      type: 'email',
      required: true,
    },
    {
      name: 'phone',
      label: 'Phone Number',
      type: 'phone',
    },
    {
      name: 'role',
      label: 'Role',
      type: 'select',
      options: [
        { value: 'admin', label: 'Administrator' },
        { value: 'manager', label: 'Manager' },
        { value: 'operator', label: 'Operator' },
        { value: 'viewer', label: 'Viewer' },
      ],
      required: true,
      permissions: ['users.manage'],
    },
  ];

  return {
    title: mode === 'create' ? 'Add New User' : mode === 'edit' ? 'Edit User' : 'User Details',
    fields,
  };
}

// Device form configuration
function getDeviceFormConfig(
  mode: FormMode,
  portalVariant: PortalVariant
): Partial<EntityFormConfig> {
  const fields: FormFieldConfig[] = [
    {
      name: 'name',
      label: 'Device Name',
      type: 'text',
      required: true,
    },
    {
      name: 'type',
      label: 'Device Type',
      type: 'select',
      options: [
        { value: 'router', label: 'Router' },
        { value: 'switch', label: 'Switch' },
        { value: 'access-point', label: 'Access Point' },
        { value: 'modem', label: 'Modem' },
        { value: 'ont', label: 'ONT' },
        { value: 'other', label: 'Other' },
      ],
      required: true,
    },
    {
      name: 'model',
      label: 'Model',
      type: 'text',
      required: true,
    },
    {
      name: 'serialNumber',
      label: 'Serial Number',
      type: 'text',
      required: true,
    },
    {
      name: 'macAddress',
      label: 'MAC Address',
      type: 'text',
      placeholder: '00:11:22:33:44:55',
      required: true,
    },
  ];

  return {
    title: mode === 'create' ? 'Add Device' : mode === 'edit' ? 'Edit Device' : 'Device Details',
    fields,
    portalCustomizations: {
      technician: {
        // Add installation-specific fields for technicians
        fields: [
          ...fields,
          {
            name: 'installationPhotos',
            label: 'Installation Photos',
            type: 'file',
            description: 'Upload photos of the installed device',
            required: mode === 'create',
          },
          {
            name: 'installationNotes',
            label: 'Installation Notes',
            type: 'textarea',
            description: 'Notes about the installation process',
            required: mode === 'create',
          },
        ],
      },
    },
  };
}

// Service form configuration
function getServiceFormConfig(
  mode: FormMode,
  portalVariant: PortalVariant
): Partial<EntityFormConfig> {
  const fields: FormFieldConfig[] = [
    {
      name: 'name',
      label: 'Service Name',
      type: 'text',
      required: true,
    },
    {
      name: 'type',
      label: 'Service Type',
      type: 'select',
      options: [
        { value: 'internet', label: 'Internet' },
        { value: 'phone', label: 'Phone' },
        { value: 'tv', label: 'TV' },
        { value: 'bundle', label: 'Bundle' },
      ],
      required: true,
    },
    {
      name: 'plan',
      label: 'Service Plan',
      type: 'text',
      required: true,
    },
  ];

  return {
    title: mode === 'create' ? 'Add Service' : mode === 'edit' ? 'Edit Service' : 'Service Details',
    fields,
  };
}

// Placeholder configurations for other entity types
function getResellerFormConfig(
  mode: FormMode,
  portalVariant: PortalVariant
): Partial<EntityFormConfig> {
  return {
    title:
      mode === 'create' ? 'Add Reseller' : mode === 'edit' ? 'Edit Reseller' : 'Reseller Details',
    fields: [],
  };
}

function getTechnicianFormConfig(
  mode: FormMode,
  portalVariant: PortalVariant
): Partial<EntityFormConfig> {
  return {
    title:
      mode === 'create'
        ? 'Add Technician'
        : mode === 'edit'
          ? 'Edit Technician'
          : 'Technician Details',
    fields: [],
  };
}

function getWorkOrderFormConfig(
  mode: FormMode,
  portalVariant: PortalVariant
): Partial<EntityFormConfig> {
  return {
    title:
      mode === 'create'
        ? 'Create Work Order'
        : mode === 'edit'
          ? 'Edit Work Order'
          : 'Work Order Details',
    fields: [],
  };
}

function getInvoiceFormConfig(
  mode: FormMode,
  portalVariant: PortalVariant
): Partial<EntityFormConfig> {
  return {
    title:
      mode === 'create' ? 'Create Invoice' : mode === 'edit' ? 'Edit Invoice' : 'Invoice Details',
    fields: [],
  };
}

function getTicketFormConfig(
  mode: FormMode,
  portalVariant: PortalVariant
): Partial<EntityFormConfig> {
  return {
    title: mode === 'create' ? 'Create Ticket' : mode === 'edit' ? 'Edit Ticket' : 'Ticket Details',
    fields: [],
  };
}
