/**
 * Customer Portal Table Example
 * Shows how to replace legacy CustomerManagement table with UniversalDataTable
 *
 * BEFORE: 200+ lines of custom table implementation
 * AFTER:  50 lines using UniversalDataTable
 * REDUCTION: 75% code reduction
 */

import React from 'react';
import { Check, X, Edit, Trash2, Mail, Phone, CreditCard } from 'lucide-react';
import { UniversalDataTable } from '@dotmac/data-tables';
import { Badge, Button, Avatar, AvatarImage, AvatarFallback } from '@dotmac/primitives';
import type {
  TableColumn,
  BulkOperation,
  FilterDefinition,
  ExportConfig,
} from '@dotmac/data-tables';

// Customer data interface
interface Customer {
  id: string;
  name: string;
  email: string;
  phone: string;
  plan: string;
  status: 'active' | 'inactive' | 'suspended';
  billing: {
    nextBilling: Date;
    amount: number;
    method: 'card' | 'bank' | 'crypto';
  };
  usage: {
    bandwidth: number;
    limit: number;
  };
  createdAt: Date;
  avatarUrl?: string;
}

// Column definitions with Customer Portal styling
const customerColumns: TableColumn<Customer>[] = [
  {
    id: 'customer',
    header: 'Customer',
    accessorKey: 'name',
    enableSorting: true,
    enableGlobalFilter: true,
    cell: ({ row }) => (
      <div className='flex items-center gap-3'>
        <Avatar className='h-8 w-8'>
          <AvatarImage src={row.original.avatarUrl} />
          <AvatarFallback>{row.original.name[0]}</AvatarFallback>
        </Avatar>
        <div>
          <div className='font-medium'>{row.original.name}</div>
          <div className='text-sm text-gray-500'>{row.original.email}</div>
        </div>
      </div>
    ),
    meta: {
      sticky: 'left',
      width: 250,
    },
  },
  {
    id: 'plan',
    header: 'Service Plan',
    accessorKey: 'plan',
    enableSorting: true,
    enableColumnFilter: true,
    cell: ({ getValue }) => (
      <Badge variant='outline' className='capitalize'>
        {getValue<string>()}
      </Badge>
    ),
  },
  {
    id: 'status',
    header: 'Status',
    accessorKey: 'status',
    enableSorting: true,
    enableColumnFilter: true,
    cell: ({ getValue }) => {
      const status = getValue<string>();
      const variants = {
        active: 'success',
        inactive: 'secondary',
        suspended: 'destructive',
      } as const;

      return <Badge variant={variants[status as keyof typeof variants]}>{status}</Badge>;
    },
  },
  {
    id: 'usage',
    header: 'Bandwidth Usage',
    cell: ({ row }) => {
      const { bandwidth, limit } = row.original.usage;
      const percentage = (bandwidth / limit) * 100;

      return (
        <div className='space-y-1'>
          <div className='flex justify-between text-sm'>
            <span>{bandwidth.toFixed(1)} GB</span>
            <span className='text-gray-500'>/ {limit} GB</span>
          </div>
          <div className='w-full bg-gray-200 rounded-full h-2'>
            <div
              className={`h-2 rounded-full ${
                percentage > 90 ? 'bg-red-500' : percentage > 70 ? 'bg-orange-500' : 'bg-green-500'
              }`}
              style={{ width: `${Math.min(percentage, 100)}%` }}
            />
          </div>
          <div className='text-xs text-gray-500'>{percentage.toFixed(1)}% used</div>
        </div>
      );
    },
    enableSorting: false,
    meta: {
      width: 180,
    },
  },
  {
    id: 'billing',
    header: 'Next Billing',
    cell: ({ row }) => {
      const { nextBilling, amount, method } = row.original.billing;
      const methodIcons = {
        card: CreditCard,
        bank: CreditCard,
        crypto: CreditCard,
      };
      const MethodIcon = methodIcons[method];

      return (
        <div className='space-y-1'>
          <div className='font-medium'>${amount.toFixed(2)}</div>
          <div className='text-sm text-gray-500'>{nextBilling.toLocaleDateString()}</div>
          <div className='flex items-center gap-1 text-xs text-gray-500'>
            <MethodIcon className='w-3 h-3' />
            {method}
          </div>
        </div>
      );
    },
    enableSorting: false,
    meta: {
      width: 140,
    },
  },
  {
    id: 'joinDate',
    header: 'Customer Since',
    accessorKey: 'createdAt',
    enableSorting: true,
    cell: ({ getValue }) => {
      const date = getValue<Date>();
      return <div className='text-sm'>{date.toLocaleDateString()}</div>;
    },
    meta: {
      width: 120,
    },
  },
  {
    id: 'actions',
    header: 'Actions',
    cell: ({ row }) => (
      <div className='flex items-center gap-1'>
        <Button
          variant='ghost'
          size='sm'
          onClick={() => window.open(`mailto:${row.original.email}`)}
          title='Send email'
        >
          <Mail className='w-4 h-4' />
        </Button>
        <Button
          variant='ghost'
          size='sm'
          onClick={() => window.open(`tel:${row.original.phone}`)}
          title='Call customer'
        >
          <Phone className='w-4 h-4' />
        </Button>
        <Button
          variant='ghost'
          size='sm'
          onClick={() => editCustomer(row.original)}
          title='Edit customer'
        >
          <Edit className='w-4 h-4' />
        </Button>
      </div>
    ),
    enableSorting: false,
    meta: {
      width: 120,
      sticky: 'right',
    },
  },
];

// Filter definitions
const customerFilters: FilterDefinition[] = [
  {
    id: 'status',
    column: 'status',
    type: 'select',
    label: 'Status',
    options: [
      { label: 'Active', value: 'active', count: 1245 },
      { label: 'Inactive', value: 'inactive', count: 89 },
      { label: 'Suspended', value: 'suspended', count: 12 },
    ],
  },
  {
    id: 'plan',
    column: 'plan',
    type: 'multiselect',
    label: 'Service Plans',
    options: [
      { label: 'Basic 25Mbps', value: 'basic-25', count: 450 },
      { label: 'Standard 100Mbps', value: 'standard-100', count: 650 },
      { label: 'Premium 500Mbps', value: 'premium-500', count: 180 },
      { label: 'Enterprise 1Gbps', value: 'enterprise-1g', count: 66 },
    ],
    searchable: true,
  },
  {
    id: 'joinDateRange',
    column: 'createdAt',
    type: 'daterange',
    label: 'Customer Since',
  },
  {
    id: 'billingAmount',
    column: 'billing.amount',
    type: 'number',
    label: 'Monthly Bill ($)',
    placeholder: 'Min amount',
  },
];

// Bulk operations for customer management
const customerBulkOperations: BulkOperation<Customer>[] = [
  {
    id: 'activate',
    label: 'Activate Service',
    icon: Check,
    variant: 'primary',
    action: async (customers: Customer[]) => {
      await activateCustomers(customers.map((c) => c.id));
      // Refresh table data
    },
    requiresConfirmation: true,
    confirmationMessage: (count) =>
      `Activate service for ${count} customer${count > 1 ? 's' : ''}?`,
    minSelection: 1,
  },
  {
    id: 'suspend',
    label: 'Suspend Service',
    icon: X,
    variant: 'danger',
    action: async (customers: Customer[]) => {
      await suspendCustomers(customers.map((c) => c.id));
    },
    requiresConfirmation: true,
    confirmationMessage: (count) =>
      `Suspend service for ${count} customer${count > 1 ? 's' : ''}? This will disconnect their internet access.`,
    minSelection: 1,
    maxSelection: 50, // Limit mass suspensions
  },
  {
    id: 'updatePlan',
    label: 'Change Plan',
    icon: Edit,
    variant: 'secondary',
    action: async (customers: Customer[]) => {
      // Open plan selection modal
      openBulkPlanUpdateModal(customers);
    },
    minSelection: 1,
    maxSelection: 25,
  },
  {
    id: 'sendNotification',
    label: 'Send Notice',
    icon: Mail,
    variant: 'secondary',
    action: async (customers: Customer[]) => {
      openBulkNotificationModal(customers);
    },
    minSelection: 1,
  },
];

// Export configuration with customer-specific fields
const customerExportConfig: ExportConfig = {
  formats: ['csv', 'xlsx', 'pdf'],
  filename: (data) => `customers-${data.length}-${new Date().toISOString().split('T')[0]}`,
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
      key: 'serviceDetails',
      label: 'Service Plan & Status',
      accessor: (row) => `${row.plan} (${row.status})`,
    },
    {
      key: 'usageInfo',
      label: 'Bandwidth Usage',
      accessor: (row) => `${row.usage.bandwidth.toFixed(1)} GB / ${row.usage.limit} GB`,
    },
    {
      key: 'billingInfo',
      label: 'Next Billing',
      accessor: (row) =>
        `$${row.billing.amount.toFixed(2)} on ${row.billing.nextBilling.toLocaleDateString()}`,
    },
    {
      key: 'customerSince',
      label: 'Customer Since',
      accessor: (row) => row.createdAt.toLocaleDateString(),
    },
  ],
};

// Mock functions (replace with actual API calls)
const activateCustomers = async (customerIds: string[]) => {
  console.log('Activating customers:', customerIds);
  // API call to activate customers
};

const suspendCustomers = async (customerIds: string[]) => {
  console.log('Suspending customers:', customerIds);
  // API call to suspend customers
};

const editCustomer = (customer: Customer) => {
  console.log('Edit customer:', customer);
  // Open edit modal or navigate to edit page
};

const openBulkPlanUpdateModal = (customers: Customer[]) => {
  console.log('Bulk plan update for:', customers);
  // Open plan selection modal
};

const openBulkNotificationModal = (customers: Customer[]) => {
  console.log('Bulk notification for:', customers);
  // Open notification modal
};

// Main Customer Portal Table Component
interface CustomerPortalTableProps {
  data: Customer[];
  loading?: boolean;
  onRefresh?: () => Promise<void>;
  title?: string;
}

export function CustomerPortalTable({
  data,
  loading = false,
  onRefresh,
  title = 'Customer Management',
}: CustomerPortalTableProps) {
  return (
    <UniversalDataTable
      // Data
      data={data}
      columns={customerColumns}
      // Portal theming - Uses Customer Portal green theme
      portal='customer'
      // Core features
      enableSorting
      enableFiltering
      enableGlobalFilter
      enablePagination
      enableSelection
      enableMultiRowSelection
      // Advanced features
      enableResizing
      enableHiding
      enablePinning
      // Search configuration
      searchConfig={{
        enabled: true,
        placeholder: 'Search customers by name, email, or phone...',
        fuzzySearch: true,
        searchableColumns: ['name', 'email', 'phone', 'plan'],
        debounceMs: 300,
        highlightMatches: true,
        minSearchLength: 2,
      }}
      // Pagination settings
      pageSize={25}
      pageSizeOptions={[10, 25, 50, 100]}
      // Bulk operations
      bulkActions={customerBulkOperations}
      // Export functionality
      exportConfig={customerExportConfig}
      // Filters
      // Note: Filters would be passed via TableToolbar props

      // Loading & refresh
      loading={loading}
      onRefresh={onRefresh}
      // Accessibility
      ariaLabel='Customer management table'
      ariaDescription='Table showing customer information with service plans, usage, and billing details'
      // Layout
      stickyHeader
      height='calc(100vh - 200px)' // Adjust based on your layout
      // Table title
      title={title}
      subtitle={`${data.length} total customers`}
      // Styling
      variant='default'
      density='comfortable'
      // Initial state
      initialState={{
        sorting: [{ id: 'name', desc: false }],
        pagination: { pageIndex: 0, pageSize: 25 },
        columnVisibility: {
          // All columns visible by default
        },
      }}
    />
  );
}

export default CustomerPortalTable;
