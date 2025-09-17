# @dotmac/forms

Universal Form & Data Entry Patterns for DotMac Framework - Production-ready form components that work consistently across all portals with automatic portal-specific theming and validation.

## 🎯 Features

- **Universal Entity Forms**: Single form component handles all entity types (Customer, Tenant, User, Device, Service)
- **Portal-Aware Styling**: Automatic theming based on portal variant (7 portals supported)
- **Advanced Search & Filtering**: Debounced search with sorting, filtering, and saved searches
- **Bulk Operations**: Multi-select actions with confirmation dialogs
- **Production-Ready Validation**: Zod schemas with portal-specific rules
- **Permission-Based Fields**: Show/hide fields based on user permissions
- **Mobile-First Responsive**: Optimized layouts for all screen sizes
- **Accessibility**: WCAG 2.1 AA compliant with full keyboard navigation

## 📦 Installation

```bash
# Install the package
pnpm add @dotmac/forms

# Peer dependencies (usually already installed)
pnpm add react react-dom react-hook-form @hookform/resolvers zod
```

## 🚀 Quick Start

### Basic Entity Form

```tsx
import { EntityForm } from '@dotmac/forms';

function CustomerFormPage() {
  const handleSubmit = async (data) => {
    // Handle form submission
    await updateCustomer(data);
  };

  return (
    <EntityForm
      entity='customer'
      mode='edit'
      portalVariant='admin'
      initialData={customerData}
      onSubmit={handleSubmit}
      onCancel={() => router.back()}
    />
  );
}
```

### Universal Search

```tsx
import { UniversalSearch } from '@dotmac/forms';

function CustomerListPage() {
  const filters = [
    {
      key: 'status',
      label: 'Status',
      type: 'select',
      options: [
        { value: 'active', label: 'Active' },
        { value: 'inactive', label: 'Inactive' },
        { value: 'suspended', label: 'Suspended' },
      ],
    },
    {
      key: 'serviceLevel',
      label: 'Service Level',
      type: 'multiselect',
      options: [
        { value: 'basic', label: 'Basic' },
        { value: 'premium', label: 'Premium' },
        { value: 'enterprise', label: 'Enterprise' },
      ],
    },
    {
      key: 'createdAt',
      label: 'Registration Date',
      type: 'date',
    },
  ];

  const handleSearch = (query) => {
    // Handle search with filters
    fetchCustomers(query);
  };

  return (
    <UniversalSearch
      entityType='customer'
      portalVariant='admin'
      filters={filters}
      onSearch={handleSearch}
      showSort={true}
      sortOptions={[
        { field: 'name', label: 'Customer Name' },
        { field: 'createdAt', label: 'Registration Date' },
      ]}
    />
  );
}
```

### Bulk Operations

```tsx
import { BulkOperations } from '@dotmac/forms';

function CustomerTable() {
  const [selectedCustomers, setSelectedCustomers] = useState([]);

  const bulkOperations = [
    {
      id: 'activate',
      label: 'Activate Customers',
      icon: CheckCircle,
      variant: 'success',
      requiresConfirmation: true,
      confirmationMessage: 'Are you sure you want to activate the selected customers?',
    },
    {
      id: 'suspend',
      label: 'Suspend Customers',
      icon: XCircle,
      variant: 'warning',
      requiresConfirmation: true,
    },
    {
      id: 'export',
      label: 'Export to CSV',
      icon: Download,
      variant: 'default',
      requiresConfirmation: false,
    },
  ];

  const handleBulkOperation = async (operation, items) => {
    switch (operation) {
      case 'activate':
        await activateCustomers(items.map((c) => c.id));
        break;
      case 'suspend':
        await suspendCustomers(items.map((c) => c.id));
        break;
      case 'export':
        await exportCustomersToCSV(items);
        break;
    }
  };

  return (
    <BulkOperations
      selectedItems={selectedCustomers}
      availableOperations={bulkOperations}
      onExecute={handleBulkOperation}
      portalVariant='admin'
    />
  );
}
```

## 🎨 Portal Variants

The package automatically applies portal-specific theming:

- `management-admin` - Platform administration (Indigo theme)
- `customer` - Customer self-service (Emerald theme)
- `admin` - ISP administration (Purple theme)
- `reseller` - Reseller operations (Red theme)
- `technician` - Mobile field service (Cyan theme)
- `management-reseller` - Reseller network management (Blue theme)
- `tenant-portal` - Multi-tenant self-service (Teal theme)

## 🔧 Advanced Configuration

### Custom Form Configuration

```tsx
import { EntityForm } from '@dotmac/forms';

const customConfig = {
  title: 'Customer Onboarding',
  subtitle: 'Complete customer setup process',
  layout: 'two-column',
  sections: [
    {
      title: 'Personal Information',
      description: 'Basic customer details',
      fields: ['name', 'email', 'phone'],
      collapsible: false,
    },
    {
      title: 'Service Configuration',
      description: 'Service plan and billing setup',
      fields: ['serviceLevel', 'billingInfo'],
      collapsible: true,
      defaultExpanded: true,
    },
  ],
  actions: {
    primary: {
      label: 'Complete Onboarding',
      variant: 'primary',
    },
    secondary: [
      { label: 'Save as Draft', variant: 'secondary', action: 'save-draft' },
      { label: 'Cancel', variant: 'secondary', action: 'cancel' },
    ],
  },
};

<EntityForm
  entity='customer'
  mode='create'
  portalVariant='admin'
  config={customConfig}
  onSubmit={handleSubmit}
/>;
```

### Portal-Specific Customizations

```tsx
// Form automatically adapts to portal variant
<EntityForm
  entity="customer"
  mode="edit"
  portalVariant="customer" // Customer portal hides admin fields
  initialData={customerData}
  onSubmit={handleSubmit}
/>

<EntityForm
  entity="device"
  mode="create"
  portalVariant="technician" // Technician portal adds installation fields
  onSubmit={handleInstallation}
/>
```

### Validation Context

```tsx
import { EntityForm } from '@dotmac/forms';

<EntityForm
  entity='customer'
  mode='edit'
  portalVariant='admin'
  validationContext={{
    userRole: 'manager',
    userPermissions: ['customers.edit', 'billing.view'],
    tenantId: 'tenant-123',
  }}
  onSubmit={handleSubmit}
/>;
```

## 🔍 Field Types

### Supported Field Types

| Type          | Description                  | Example             |
| ------------- | ---------------------------- | ------------------- |
| `text`        | Basic text input             | Name, description   |
| `email`       | Email validation             | Email addresses     |
| `password`    | Password with show/hide      | User passwords      |
| `number`      | Numeric input                | Prices, quantities  |
| `select`      | Single selection             | Status dropdown     |
| `multiselect` | Multiple selection           | Tags, categories    |
| `textarea`    | Multi-line text              | Notes, descriptions |
| `checkbox`    | Boolean input                | Agreements, flags   |
| `radio`       | Single choice from options   | Payment method      |
| `date`        | Date picker                  | Installation date   |
| `phone`       | Phone number with formatting | Contact numbers     |
| `address`     | Multi-field address          | Service addresses   |
| `file`        | File upload with drag/drop   | Documents, photos   |

### Custom Field Configuration

```tsx
const customFields = [
  {
    name: 'customerTier',
    label: 'Customer Tier',
    type: 'select',
    options: [
      { value: 'bronze', label: 'Bronze' },
      { value: 'silver', label: 'Silver' },
      { value: 'gold', label: 'Gold' },
      { value: 'platinum', label: 'Platinum' },
    ],
    required: true,
    description: 'Customer service tier level',
    portalVariants: ['admin', 'management-admin'], // Only show in admin portals
    permissions: ['customers.manage'], // Require permission
    dependencies: [
      // Show only if other field has specific value
      {
        field: 'serviceLevel',
        value: 'enterprise',
        action: 'show',
      },
    ],
  },
];
```

## 🔐 Security & Validation

### Built-in Validation

```tsx
// Automatic validation based on entity type and portal variant
import { validateEntity, getEntitySchema } from '@dotmac/forms';

// Validate customer data for admin portal
const result = validateEntity(formData, 'customer', 'admin', validationContext);

if (result.success) {
  // Data is valid
  console.log(result.data);
} else {
  // Handle validation errors
  console.error(result.error.errors);
}
```

### Permission-Based Field Access

```tsx
// Fields automatically show/hide based on permissions
const fieldConfig = {
  name: 'adminNotes',
  label: 'Admin Notes',
  type: 'textarea',
  permissions: ['admin.notes'], // Only users with this permission see this field
  portalVariants: ['admin', 'management-admin'], // Only show in admin portals
};
```

## 📱 Mobile Optimization

### Responsive Layouts

```tsx
// Automatic responsive behavior
<EntityForm
  entity='customer'
  mode='create'
  portalVariant='technician' // Automatically optimized for mobile
  layout='auto' // Responsive: single-column on mobile, two-column on desktop
  onSubmit={handleSubmit}
/>
```

### Touch-Friendly Components

- **44px minimum touch targets** for mobile devices
- **Swipe gestures** for advanced interactions
- **Keyboard-friendly** navigation patterns
- **Screen reader** compatible

## 🧪 Testing

### Component Testing

```tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { EntityForm } from '@dotmac/forms';

test('customer form submits valid data', async () => {
  const mockSubmit = jest.fn();

  render(
    <EntityForm entity='customer' mode='create' portalVariant='admin' onSubmit={mockSubmit} />
  );

  // Fill form fields
  fireEvent.change(screen.getByLabelText(/customer name/i), {
    target: { value: 'John Doe' },
  });

  fireEvent.change(screen.getByLabelText(/email address/i), {
    target: { value: 'john@example.com' },
  });

  // Submit form
  fireEvent.click(screen.getByRole('button', { name: /create/i }));

  await waitFor(() => {
    expect(mockSubmit).toHaveBeenCalledWith({
      name: 'John Doe',
      email: 'john@example.com',
      // ... other form data
    });
  });
});
```

## 🔧 Troubleshooting

### Common Issues

1. **Form not appearing**: Check that all required props are provided
2. **Validation errors**: Ensure data matches expected schema for entity type
3. **Portal styling not applied**: Verify `portalVariant` prop is correct
4. **Fields not showing**: Check user permissions and portal variant restrictions

### Debug Mode

```tsx
// Enable debug information in development
<EntityForm
  entity='customer'
  mode='create'
  portalVariant='admin'
  onSubmit={handleSubmit}
  // Debug info automatically appears in development mode
/>
```

## 📚 API Reference

### EntityForm Props

| Prop                | Type                     | Required | Description                                   |
| ------------------- | ------------------------ | -------- | --------------------------------------------- |
| `entity`            | `EntityType`             | ✅       | Type of entity (customer, tenant, user, etc.) |
| `mode`              | `FormMode`               | ✅       | Form mode (create, edit, view, duplicate)     |
| `portalVariant`     | `PortalVariant`          | ✅       | Portal type for theming and behavior          |
| `onSubmit`          | `Function`               | ✅       | Form submission handler                       |
| `initialData`       | `Object`                 | ❌       | Pre-populate form with data                   |
| `config`            | `EntityFormConfig`       | ❌       | Custom form configuration                     |
| `validationContext` | `ValidationContext`      | ❌       | Context for validation rules                  |
| `onCancel`          | `Function`               | ❌       | Cancel button handler                         |
| `isLoading`         | `boolean`                | ❌       | Show loading state                            |
| `errors`            | `Record<string, string>` | ❌       | External validation errors                    |

### UniversalSearch Props

| Prop            | Type             | Required | Description                            |
| --------------- | ---------------- | -------- | -------------------------------------- |
| `entityType`    | `EntityType`     | ✅       | Type of entity to search               |
| `portalVariant` | `PortalVariant`  | ✅       | Portal type for theming                |
| `filters`       | `FilterConfig[]` | ✅       | Available filter configurations        |
| `onSearch`      | `Function`       | ✅       | Search handler function                |
| `placeholder`   | `string`         | ❌       | Search input placeholder               |
| `initialQuery`  | `string`         | ❌       | Pre-populate search query              |
| `debounceMs`    | `number`         | ❌       | Search debounce delay (default: 300ms) |
| `showFilters`   | `boolean`        | ❌       | Show filter panel (default: true)      |
| `showSort`      | `boolean`        | ❌       | Show sort options (default: true)      |

## 🤝 Contributing

1. **Development Setup**:

   ```bash
   cd frontend/packages/forms
   pnpm install
   pnpm dev # Start development mode
   ```

2. **Testing**:

   ```bash
   pnpm test # Run tests
   pnpm test:coverage # Generate coverage report
   ```

3. **Build**:

   ```bash
   pnpm build # Build for production
   pnpm type-check # Validate TypeScript
   ```

## 📄 License

MIT License - see LICENSE file for details.

---

Built with ❤️ by the DotMac Framework Team
