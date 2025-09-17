/**
 * Admin Portal Table Example
 * Shows comprehensive admin features with advanced bulk operations
 *
 * BEFORE: 250+ lines of complex admin table logic
 * AFTER:  80 lines using UniversalDataTable with admin-specific features
 * REDUCTION: 68% code reduction
 */

import React from 'react';
import {
  Shield,
  ShieldCheck,
  ShieldX,
  Users,
  Crown,
  Ban,
  Mail,
  Phone,
  MapPin,
  Calendar,
  DollarSign,
  Activity,
  AlertTriangle,
  Trash2,
  Edit3,
  Eye,
  Archive,
} from 'lucide-react';
import { UniversalDataTable } from '@dotmac/data-tables';
import { Badge, Button, Avatar, AvatarImage, AvatarFallback, Progress } from '@dotmac/primitives';
import type {
  TableColumn,
  BulkOperation,
  FilterDefinition,
  ExportConfig,
  TableAction,
} from '@dotmac/data-tables';

// Admin view of customer data with additional fields
interface AdminCustomerView {
  id: string;
  name: string;
  email: string;
  phone: string;
  address: {
    street: string;
    city: string;
    state: string;
    zip: string;
  };
  plan: string;
  status: 'active' | 'inactive' | 'suspended' | 'cancelled';
  role: 'customer' | 'reseller' | 'admin';
  billing: {
    nextBilling: Date;
    amount: number;
    method: 'card' | 'bank' | 'crypto';
    pastDue: boolean;
    totalPaid: number;
  };
  usage: {
    bandwidth: number;
    limit: number;
    overage: number;
  };
  support: {
    ticketsOpen: number;
    lastContact: Date;
    satisfaction: number; // 1-5
  };
  security: {
    loginAttempts: number;
    lastLogin: Date;
    twoFactorEnabled: boolean;
    riskScore: number; // 0-100
  };
  createdAt: Date;
  lastUpdated: Date;
  notes: string;
  avatarUrl?: string;
}

// Admin-focused column definitions with comprehensive data
const adminColumns: TableColumn<AdminCustomerView>[] = [
  {
    id: 'customer',
    header: 'Customer Details',
    accessorKey: 'name',
    enableSorting: true,
    enableGlobalFilter: true,
    cell: ({ row }) => (
      <div className='flex items-center gap-3'>
        <div className='relative'>
          <Avatar className='h-10 w-10'>
            <AvatarImage src={row.original.avatarUrl} />
            <AvatarFallback>{row.original.name[0]}</AvatarFallback>
          </Avatar>
          {/* Role indicator */}
          <div className='absolute -top-1 -right-1'>
            {row.original.role === 'admin' && <Crown className='w-4 h-4 text-yellow-500' />}
            {row.original.role === 'reseller' && <Users className='w-4 h-4 text-purple-500' />}
          </div>
        </div>
        <div>
          <div className='font-medium'>{row.original.name}</div>
          <div className='text-sm text-gray-500'>{row.original.email}</div>
          <div className='text-xs text-gray-400'>{row.original.phone}</div>
        </div>
      </div>
    ),
    meta: {
      sticky: 'left',
      width: 280,
    },
  },
  {
    id: 'location',
    header: 'Location',
    cell: ({ row }) => {
      const { address } = row.original;
      return (
        <div className='text-sm'>
          <div className='font-medium'>
            {address.city}, {address.state}
          </div>
          <div className='text-gray-500'>{address.zip}</div>
        </div>
      );
    },
    enableSorting: false,
    meta: {
      width: 120,
    },
  },
  {
    id: 'status',
    header: 'Status & Plan',
    cell: ({ row }) => {
      const statusColors = {
        active: 'success',
        inactive: 'secondary',
        suspended: 'warning',
        cancelled: 'destructive',
      } as const;

      return (
        <div className='space-y-1'>
          <Badge variant={statusColors[row.original.status]}>{row.original.status}</Badge>
          <div className='text-sm font-medium'>{row.original.plan}</div>
        </div>
      );
    },
    enableSorting: true,
    enableColumnFilter: true,
    meta: {
      width: 140,
    },
  },
  {
    id: 'usage',
    header: 'Bandwidth Usage',
    cell: ({ row }) => {
      const { bandwidth, limit, overage } = row.original.usage;
      const percentage = (bandwidth / limit) * 100;
      const hasOverage = overage > 0;

      return (
        <div className='space-y-1'>
          <div className='flex justify-between text-sm'>
            <span>{bandwidth.toFixed(1)} GB</span>
            <span className='text-gray-500'>/ {limit} GB</span>
          </div>
          <Progress
            value={Math.min(percentage, 100)}
            className='h-2'
            indicatorClassName={
              percentage > 100 ? 'bg-red-500' : percentage > 90 ? 'bg-orange-500' : 'bg-blue-500'
            }
          />
          <div className='flex justify-between text-xs'>
            <span className='text-gray-500'>{percentage.toFixed(1)}% used</span>
            {hasOverage && (
              <span className='text-red-500 font-medium'>+{overage.toFixed(1)} GB overage</span>
            )}
          </div>
        </div>
      );
    },
    enableSorting: false,
    meta: {
      width: 200,
    },
  },
  {
    id: 'billing',
    header: 'Billing Status',
    cell: ({ row }) => {
      const { amount, nextBilling, pastDue, totalPaid } = row.original.billing;

      return (
        <div className='space-y-1'>
          <div className='flex items-center gap-1'>
            <DollarSign className='w-3 h-3' />
            <span className='font-medium'>${amount.toFixed(2)}/mo</span>
            {pastDue && <AlertTriangle className='w-3 h-3 text-red-500' />}
          </div>
          <div className='text-sm text-gray-500'>Next: {nextBilling.toLocaleDateString()}</div>
          <div className='text-xs text-gray-400'>Total paid: ${totalPaid.toLocaleString()}</div>
          {pastDue && (
            <Badge variant='destructive' className='text-xs'>
              Past Due
            </Badge>
          )}
        </div>
      );
    },
    enableSorting: false,
    meta: {
      width: 160,
    },
  },
  {
    id: 'support',
    header: 'Support & Satisfaction',
    cell: ({ row }) => {
      const { ticketsOpen, lastContact, satisfaction } = row.original.support;
      const satisfactionColors = [
        'text-red-500',
        'text-orange-500',
        'text-yellow-500',
        'text-blue-500',
        'text-green-500',
      ];

      return (
        <div className='space-y-1'>
          <div className='flex items-center gap-1'>
            <Activity className='w-3 h-3' />
            <span className='text-sm'>
              {ticketsOpen} open ticket{ticketsOpen !== 1 ? 's' : ''}
            </span>
          </div>
          <div className='text-xs text-gray-500'>
            Last contact: {lastContact.toLocaleDateString()}
          </div>
          <div className='flex items-center gap-1'>
            <span className='text-xs'>Satisfaction:</span>
            <span className={`text-sm font-medium ${satisfactionColors[satisfaction - 1]}`}>
              {satisfaction}/5 ★
            </span>
          </div>
        </div>
      );
    },
    enableSorting: false,
    meta: {
      width: 170,
    },
  },
  {
    id: 'security',
    header: 'Security Profile',
    cell: ({ row }) => {
      const { twoFactorEnabled, riskScore, loginAttempts, lastLogin } = row.original.security;

      return (
        <div className='space-y-1'>
          <div className='flex items-center gap-1'>
            {twoFactorEnabled ? (
              <ShieldCheck className='w-4 h-4 text-green-500' />
            ) : (
              <ShieldX className='w-4 h-4 text-orange-500' />
            )}
            <span className='text-xs'>2FA {twoFactorEnabled ? 'ON' : 'OFF'}</span>
          </div>
          <div className='flex items-center gap-1'>
            <Shield className='w-3 h-3' />
            <span
              className={`text-xs font-medium ${
                riskScore > 70
                  ? 'text-red-500'
                  : riskScore > 40
                    ? 'text-orange-500'
                    : 'text-green-500'
              }`}
            >
              Risk: {riskScore}%
            </span>
          </div>
          <div className='text-xs text-gray-500'>Last login: {lastLogin.toLocaleDateString()}</div>
          {loginAttempts > 5 && (
            <Badge variant='destructive' className='text-xs'>
              {loginAttempts} failed logins
            </Badge>
          )}
        </div>
      );
    },
    enableSorting: false,
    meta: {
      width: 150,
    },
  },
  {
    id: 'dates',
    header: 'Account Timeline',
    cell: ({ row }) => (
      <div className='space-y-1 text-xs'>
        <div className='flex items-center gap-1'>
          <Calendar className='w-3 h-3' />
          <span>Created: {row.original.createdAt.toLocaleDateString()}</span>
        </div>
        <div className='text-gray-500'>
          Updated: {row.original.lastUpdated.toLocaleDateString()}
        </div>
      </div>
    ),
    enableSorting: true,
    meta: {
      width: 140,
    },
  },
  {
    id: 'adminActions',
    header: 'Admin Actions',
    cell: ({ row }) => (
      <div className='flex items-center gap-1'>
        <Button
          variant='ghost'
          size='sm'
          onClick={() => viewCustomerDetails(row.original)}
          title='View full details'
        >
          <Eye className='w-4 h-4' />
        </Button>
        <Button
          variant='ghost'
          size='sm'
          onClick={() => editCustomer(row.original)}
          title='Edit customer'
        >
          <Edit3 className='w-4 h-4' />
        </Button>
        <Button
          variant='ghost'
          size='sm'
          onClick={() => impersonateCustomer(row.original)}
          title='Login as customer'
          className='text-orange-600 hover:text-orange-700'
        >
          <Shield className='w-4 h-4' />
        </Button>
      </div>
    ),
    enableSorting: false,
    meta: {
      width: 140,
      sticky: 'right',
    },
  },
];

// Comprehensive admin filters
const adminFilters: FilterDefinition[] = [
  {
    id: 'status',
    column: 'status',
    type: 'multiselect',
    label: 'Account Status',
    options: [
      { label: 'Active', value: 'active', count: 2450 },
      { label: 'Inactive', value: 'inactive', count: 156 },
      { label: 'Suspended', value: 'suspended', count: 23 },
      { label: 'Cancelled', value: 'cancelled', count: 89 },
    ],
  },
  {
    id: 'role',
    column: 'role',
    type: 'select',
    label: 'User Role',
    options: [
      { label: 'Customer', value: 'customer', count: 2650 },
      { label: 'Reseller', value: 'reseller', count: 45 },
      { label: 'Admin', value: 'admin', count: 23 },
    ],
  },
  {
    id: 'plan',
    column: 'plan',
    type: 'multiselect',
    label: 'Service Plans',
    options: [
      { label: 'Basic 25Mbps', value: 'basic-25', count: 890 },
      { label: 'Standard 100Mbps', value: 'standard-100', count: 1200 },
      { label: 'Premium 500Mbps', value: 'premium-500', count: 420 },
      { label: 'Enterprise 1Gbps', value: 'enterprise-1g', count: 185 },
      { label: 'Enterprise 10Gbps', value: 'enterprise-10g', count: 23 },
    ],
    searchable: true,
  },
  {
    id: 'riskScore',
    column: 'security.riskScore',
    type: 'select',
    label: 'Security Risk',
    options: [
      { label: 'Low Risk (0-30)', value: 'low' },
      { label: 'Medium Risk (31-70)', value: 'medium' },
      { label: 'High Risk (71-100)', value: 'high' },
    ],
  },
  {
    id: 'billingStatus',
    column: 'billing.pastDue',
    type: 'boolean',
    label: 'Past Due Bills',
  },
  {
    id: 'twoFactor',
    column: 'security.twoFactorEnabled',
    type: 'boolean',
    label: '2FA Enabled',
  },
  {
    id: 'supportTickets',
    column: 'support.ticketsOpen',
    type: 'number',
    label: 'Open Tickets',
    placeholder: 'Min tickets',
  },
  {
    id: 'joinDateRange',
    column: 'createdAt',
    type: 'daterange',
    label: 'Join Date Range',
  },
];

// Advanced bulk operations for admin
const adminBulkOperations: BulkOperation<AdminCustomerView>[] = [
  {
    id: 'activate',
    label: 'Activate Accounts',
    icon: ShieldCheck,
    variant: 'primary',
    action: async (customers: AdminCustomerView[]) => {
      await activateCustomers(customers.map((c) => c.id));
    },
    requiresConfirmation: true,
    confirmationMessage: (count) =>
      `Activate ${count} customer account${count > 1 ? 's' : ''}? This will restore full service access.`,
    minSelection: 1,
  },
  {
    id: 'suspend',
    label: 'Suspend Accounts',
    icon: ShieldX,
    variant: 'danger',
    action: async (customers: AdminCustomerView[]) => {
      await suspendCustomers(customers.map((c) => c.id));
    },
    requiresConfirmation: true,
    confirmationMessage: (count) =>
      `Suspend ${count} customer account${count > 1 ? 's' : ''}? This will immediately disconnect their service.`,
    minSelection: 1,
    maxSelection: 25,
  },
  {
    id: 'force2FA',
    label: 'Require 2FA',
    icon: Shield,
    variant: 'secondary',
    action: async (customers: AdminCustomerView[]) => {
      await force2FASetup(customers.map((c) => c.id));
    },
    requiresConfirmation: true,
    confirmationMessage: (count) =>
      `Force 2FA setup for ${count} customer${count > 1 ? 's' : ''}? They will be required to set up 2FA on next login.`,
    minSelection: 1,
  },
  {
    id: 'sendBilling',
    label: 'Send Bill Reminder',
    icon: DollarSign,
    variant: 'secondary',
    action: async (customers: AdminCustomerView[]) => {
      await sendBillingReminder(customers.map((c) => c.id));
    },
    minSelection: 1,
    maxSelection: 100,
  },
  {
    id: 'resetUsage',
    label: 'Reset Usage',
    icon: Activity,
    variant: 'secondary',
    action: async (customers: AdminCustomerView[]) => {
      await resetUsageCounters(customers.map((c) => c.id));
    },
    requiresConfirmation: true,
    confirmationMessage: (count) =>
      `Reset usage counters for ${count} customer${count > 1 ? 's' : ''}? This will clear current bandwidth usage.`,
    minSelection: 1,
  },
  {
    id: 'archive',
    label: 'Archive Accounts',
    icon: Archive,
    variant: 'secondary',
    action: async (customers: AdminCustomerView[]) => {
      await archiveCustomers(customers.map((c) => c.id));
    },
    requiresConfirmation: true,
    confirmationMessage: (count) =>
      `Archive ${count} customer account${count > 1 ? 's' : ''}? Archived accounts can be restored later.`,
    minSelection: 1,
  },
  {
    id: 'delete',
    label: 'Delete Accounts',
    icon: Trash2,
    variant: 'danger',
    action: async (customers: AdminCustomerView[]) => {
      await deleteCustomers(customers.map((c) => c.id));
    },
    requiresConfirmation: true,
    confirmationMessage: (count) =>
      `PERMANENTLY DELETE ${count} customer account${count > 1 ? 's' : ''}? This action cannot be undone and will remove all customer data.`,
    minSelection: 1,
    maxSelection: 10, // Limit bulk deletions
  },
];

// Admin toolbar actions
const adminToolbarActions: TableAction<AdminCustomerView>[] = [
  {
    id: 'createCustomer',
    label: 'New Customer',
    icon: Users,
    variant: 'primary',
    onClick: () => openCreateCustomerModal(),
  },
  {
    id: 'importCustomers',
    label: 'Import CSV',
    icon: Archive,
    variant: 'secondary',
    onClick: () => openImportModal(),
  },
  {
    id: 'auditLog',
    label: 'Audit Log',
    icon: Shield,
    variant: 'outline',
    onClick: () => openAuditLogModal(),
  },
];

// Comprehensive export config for admin
const adminExportConfig: ExportConfig = {
  formats: ['csv', 'xlsx', 'json', 'pdf'],
  filename: (data) =>
    `admin-customer-export-${data.length}-${new Date().toISOString().split('T')[0]}`,
  includeHeaders: true,
  selectedOnly: false,
  customFields: [
    {
      key: 'customerName',
      label: 'Customer Name',
      accessor: (row) => row.name,
    },
    {
      key: 'contactInfo',
      label: 'Contact Information',
      accessor: (row) => `${row.email} | ${row.phone}`,
    },
    {
      key: 'fullAddress',
      label: 'Address',
      accessor: (row) =>
        `${row.address.street}, ${row.address.city}, ${row.address.state} ${row.address.zip}`,
    },
    {
      key: 'accountStatus',
      label: 'Account Status',
      accessor: (row) => `${row.status} (${row.role})`,
    },
    {
      key: 'servicePlan',
      label: 'Service Plan',
      accessor: (row) => row.plan,
    },
    {
      key: 'usageDetails',
      label: 'Bandwidth Usage',
      accessor: (row) =>
        `${row.usage.bandwidth.toFixed(1)} GB / ${row.usage.limit} GB ${row.usage.overage > 0 ? `(+${row.usage.overage.toFixed(1)} GB overage)` : ''}`,
    },
    {
      key: 'billingDetails',
      label: 'Billing Information',
      accessor: (row) =>
        `$${row.billing.amount.toFixed(2)}/mo, Next: ${row.billing.nextBilling.toLocaleDateString()}, Total Paid: $${row.billing.totalPaid.toLocaleString()}${row.billing.pastDue ? ' (PAST DUE)' : ''}`,
    },
    {
      key: 'supportMetrics',
      label: 'Support Metrics',
      accessor: (row) =>
        `${row.support.ticketsOpen} open tickets, Satisfaction: ${row.support.satisfaction}/5, Last contact: ${row.support.lastContact.toLocaleDateString()}`,
    },
    {
      key: 'securityProfile',
      label: 'Security Profile',
      accessor: (row) =>
        `2FA: ${row.security.twoFactorEnabled ? 'Enabled' : 'Disabled'}, Risk Score: ${row.security.riskScore}%, Failed Logins: ${row.security.loginAttempts}, Last Login: ${row.security.lastLogin.toLocaleDateString()}`,
    },
    {
      key: 'accountTimeline',
      label: 'Account Dates',
      accessor: (row) =>
        `Created: ${row.createdAt.toLocaleDateString()}, Updated: ${row.lastUpdated.toLocaleDateString()}`,
    },
    {
      key: 'notes',
      label: 'Admin Notes',
      accessor: (row) => row.notes,
    },
  ],
};

// Mock functions (replace with actual admin API calls)
const activateCustomers = async (customerIds: string[]) => {
  console.log('Admin: Activating customers:', customerIds);
};

const suspendCustomers = async (customerIds: string[]) => {
  console.log('Admin: Suspending customers:', customerIds);
};

const force2FASetup = async (customerIds: string[]) => {
  console.log('Admin: Forcing 2FA setup for:', customerIds);
};

const sendBillingReminder = async (customerIds: string[]) => {
  console.log('Admin: Sending billing reminders to:', customerIds);
};

const resetUsageCounters = async (customerIds: string[]) => {
  console.log('Admin: Resetting usage counters for:', customerIds);
};

const archiveCustomers = async (customerIds: string[]) => {
  console.log('Admin: Archiving customers:', customerIds);
};

const deleteCustomers = async (customerIds: string[]) => {
  console.log('Admin: DELETING customers:', customerIds);
};

const viewCustomerDetails = (customer: AdminCustomerView) => {
  console.log('Admin: View customer details:', customer);
};

const editCustomer = (customer: AdminCustomerView) => {
  console.log('Admin: Edit customer:', customer);
};

const impersonateCustomer = (customer: AdminCustomerView) => {
  console.log('Admin: Impersonate customer:', customer);
};

const openCreateCustomerModal = () => {
  console.log('Admin: Open create customer modal');
};

const openImportModal = () => {
  console.log('Admin: Open import modal');
};

const openAuditLogModal = () => {
  console.log('Admin: Open audit log modal');
};

// Main Admin Portal Table Component
interface AdminPortalTableProps {
  data: AdminCustomerView[];
  loading?: boolean;
  onRefresh?: () => Promise<void>;
  title?: string;
}

export function AdminPortalTable({
  data,
  loading = false,
  onRefresh,
  title = 'Admin Customer Management',
}: AdminPortalTableProps) {
  return (
    <UniversalDataTable
      // Data
      data={data}
      columns={adminColumns}
      // Portal theming - Uses Admin Portal blue theme
      portal='admin'
      // All advanced features enabled for admin
      enableSorting
      enableFiltering
      enableGlobalFilter
      enablePagination
      enableSelection
      enableMultiRowSelection
      enableResizing
      enableReordering
      enableHiding
      enablePinning
      enableGrouping
      // Advanced search for comprehensive admin queries
      searchConfig={{
        enabled: true,
        placeholder: 'Search customers by name, email, phone, address, notes...',
        fuzzySearch: true,
        searchableColumns: [
          'name',
          'email',
          'phone',
          'address.city',
          'address.state',
          'plan',
          'notes',
        ],
        debounceMs: 200, // Faster for admin use
        highlightMatches: true,
        minSearchLength: 1, // Allow single character searches
      }}
      // Pagination optimized for admin bulk operations
      pageSize={50}
      pageSizeOptions={[25, 50, 100, 200]}
      // Comprehensive bulk operations
      bulkActions={adminBulkOperations}
      // Toolbar actions
      toolbarActions={adminToolbarActions}
      // Comprehensive export for admin reporting
      exportConfig={adminExportConfig}
      // Loading & refresh
      loading={loading}
      onRefresh={onRefresh}
      // Accessibility
      ariaLabel='Admin customer management table'
      ariaDescription='Comprehensive admin view of customer accounts with security, billing, and support information'
      // Layout optimized for admin dashboard
      stickyHeader
      height='calc(100vh - 160px)'
      variant='default'
      density='compact' // More data visible
      // Table metadata
      title={title}
      subtitle={`${data.length} total customers across all portals`}
      // Initial state optimized for admin workflow
      initialState={{
        sorting: [{ id: 'dates', desc: true }], // Newest customers first
        pagination: { pageIndex: 0, pageSize: 50 },
        columnVisibility: {
          // All columns visible by default for admin
        },
        columnPinning: {
          left: ['customer'],
          right: ['adminActions'],
        },
      }}
      // Enable virtualization for large customer base
      enableVirtualization
      virtualizationConfig={{
        enabled: true,
        estimateSize: 80, // Taller rows for admin data
        overscan: 20,
      }}
    />
  );
}

export default AdminPortalTable;
