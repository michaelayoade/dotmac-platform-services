export type PortalVariant =
  | 'management-admin'
  | 'customer'
  | 'admin'
  | 'reseller'
  | 'technician'
  | 'management-reseller'
  | 'tenant-portal';

export type EntityType =
  | 'customer'
  | 'tenant'
  | 'user'
  | 'device'
  | 'service'
  | 'reseller'
  | 'technician'
  | 'work-order'
  | 'invoice'
  | 'ticket';

export type FormMode = 'create' | 'edit' | 'view' | 'duplicate';

export interface BaseEntity {
  id: string;
  createdAt?: string;
  updatedAt?: string;
  createdBy?: string;
  updatedBy?: string;
}

export interface Customer extends BaseEntity {
  name: string;
  email: string;
  phone: string;
  address: {
    street: string;
    city: string;
    state: string;
    zipCode: string;
    country: string;
  };
  status: 'active' | 'inactive' | 'suspended';
  serviceLevel: 'basic' | 'premium' | 'enterprise';
  billingInfo?: {
    paymentMethod: 'credit_card' | 'bank_transfer' | 'check';
    billingAddress?: any;
  };
}

export interface Tenant extends BaseEntity {
  name: string;
  domain: string;
  plan: 'starter' | 'professional' | 'enterprise';
  status: 'active' | 'trial' | 'suspended' | 'cancelled';
  limits: {
    users: number;
    storage: number; // GB
    bandwidth: number; // GB/month
    apiCalls: number; // per month
  };
  settings: {
    timezone: string;
    currency: string;
    language: string;
  };
}

export interface User extends BaseEntity {
  firstName: string;
  lastName: string;
  email: string;
  phone?: string;
  role: string;
  permissions: string[];
  status: 'active' | 'inactive' | 'pending';
  lastLogin?: string;
  mfaEnabled: boolean;
  tenantId?: string;
}

export interface Device extends BaseEntity {
  name: string;
  type: 'router' | 'switch' | 'access-point' | 'modem' | 'ont' | 'other';
  model: string;
  manufacturer: string;
  serialNumber: string;
  macAddress: string;
  ipAddress?: string;
  location: {
    site: string;
    rack?: string;
    position?: string;
    coordinates?: {
      lat: number;
      lng: number;
    };
  };
  status: 'online' | 'offline' | 'maintenance' | 'error';
  customerId?: string;
}

export interface Service extends BaseEntity {
  name: string;
  type: 'internet' | 'phone' | 'tv' | 'bundle';
  plan: string;
  speed?: {
    download: number; // Mbps
    upload: number; // Mbps
  };
  pricing: {
    monthlyRate: number;
    setupFee: number;
    currency: string;
  };
  status: 'active' | 'pending' | 'suspended' | 'cancelled';
  customerId: string;
  installationDate?: string;
}

export interface FilterConfig {
  key: string;
  label: string;
  type: 'text' | 'select' | 'date' | 'number' | 'boolean' | 'multiselect';
  options?: { value: string; label: string }[];
  placeholder?: string;
  defaultValue?: any;
}

export interface SearchQuery {
  query?: string;
  filters: Record<string, any>;
  sort?: {
    field: string;
    direction: 'asc' | 'desc';
  };
  pagination?: {
    page: number;
    limit: number;
  };
}

export interface BulkOperation {
  id: string;
  label: string;
  icon?: React.ComponentType<{ className?: string }>;
  description?: string;
  requiresConfirmation: boolean;
  confirmationMessage?: string;
  variant?: 'default' | 'danger' | 'warning' | 'success';
  permissions?: string[];
}

export interface FormFieldConfig {
  name: string;
  label: string;
  type:
    | 'text'
    | 'email'
    | 'password'
    | 'number'
    | 'select'
    | 'multiselect'
    | 'textarea'
    | 'checkbox'
    | 'radio'
    | 'date'
    | 'file'
    | 'phone'
    | 'address';
  placeholder?: string;
  description?: string;
  required?: boolean;
  disabled?: boolean;
  hidden?: boolean;
  validation?: any; // Zod schema
  options?: { value: string; label: string }[];
  dependencies?: {
    field: string;
    value: any;
    action: 'show' | 'hide' | 'enable' | 'disable';
  }[];
  portalVariants?: PortalVariant[]; // Only show in specific portals
  permissions?: string[]; // Only show if user has permissions
}

export interface EntityFormConfig {
  entity: EntityType;
  mode: FormMode;
  title?: string;
  subtitle?: string;
  fields: FormFieldConfig[];
  sections?: {
    title: string;
    description?: string;
    fields: string[]; // field names
    collapsible?: boolean;
    defaultExpanded?: boolean;
  }[];
  actions?: {
    primary?: {
      label: string;
      variant?: 'default' | 'primary' | 'secondary' | 'danger';
    };
    secondary?: {
      label: string;
      variant?: 'default' | 'primary' | 'secondary' | 'danger';
      action: 'cancel' | 'reset' | 'duplicate' | 'delete' | 'custom';
    }[];
  };
  layout?: 'single-column' | 'two-column' | 'auto';
  portalCustomizations?: Record<PortalVariant, Partial<EntityFormConfig>>;
}

// Portal-specific styling and behavior
export interface PortalTheme {
  variant: PortalVariant;
  colors: {
    primary: string;
    secondary: string;
    accent: string;
    success: string;
    warning: string;
    error: string;
    info: string;
  };
  spacing: {
    formGap: string;
    sectionGap: string;
    fieldGap: string;
  };
  typography: {
    formTitle: string;
    sectionTitle: string;
    fieldLabel: string;
    helpText: string;
  };
  components: {
    card: string;
    input: string;
    button: string;
    label: string;
  };
}

export interface ValidationContext {
  portalVariant: PortalVariant;
  userRole: string;
  userPermissions: string[];
  tenantId?: string;
  entityData?: any;
  mode: FormMode;
}
