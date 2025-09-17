# @dotmac/styled-components

Beautiful, accessible styled components for the DotMac ISP Platform. Built on
top of `@dotmac/primitives` with portal-specific theming and responsive design.

## 🎨 Portal Themes

### Admin Portal

High-density, professional interface optimized for power users and data
management.

```tsx
import { AdminButton, AdminCard, AdminDataTable } from '@dotmac/styled-components/admin';
```

**Characteristics:**

- **Compact Density**: Maximizes information display
- **High Contrast**: Clear visual hierarchy for data
- **Professional**: Dark theme available for long sessions
- **Advanced Controls**: Bulk actions, keyboard shortcuts, inline editing

### Customer Portal

Friendly, accessible interface designed for end-user self-service.

```tsx
import { CustomerButton, CustomerCard, CustomerInput } from '@dotmac/styled-components/customer';
```

**Characteristics:**

- **Comfortable Spacing**: Easy on the eyes
- **Friendly Colors**: Approachable and welcoming
- **Clear Guidance**: Helpful text and validation messages
- **Mobile Optimized**: Touch-friendly controls

### Reseller Portal

Professional, brandable interface for partner and reseller management.

```tsx
import { ResellerButton, ResellerCard, ResellerInput } from '@dotmac/styled-components/reseller';
```

**Characteristics:**

- **Brand Flexibility**: Customizable primary colors
- **Professional**: Business-appropriate styling
- **Commission Focus**: Specialized components for earnings
- **White-label Ready**: Easy rebranding options

## 📦 Installation

```bash
npm install @dotmac/styled-components @dotmac/primitives
# or
yarn add @dotmac/styled-components @dotmac/primitives
# or
pnpm add @dotmac/styled-components @dotmac/primitives
```

## 🚀 Quick Start

### 1. Set up Theme Provider

```tsx
import { ThemeProvider } from '@dotmac/styled-components';
import '@dotmac/styled-components/styles.css';

function App() {
  return (
    <ThemeProvider defaultPortal='customer' defaultColorScheme='light'>
      <YourApp />
    </ThemeProvider>
  );
}
```

### 2. Use Portal-Specific Components

```tsx
// Customer Portal Example
import {
  CustomerButton,
  CustomerCard,
  CustomerCardHeader,
  CustomerCardTitle,
  CustomerCardContent,
  CustomerInput,
} from '@dotmac/styled-components/customer';

function BillingCard() {
  return (
    <CustomerCard variant='elevated'>
      <CustomerCardHeader>
        <CustomerCardTitle>Current Bill</CustomerCardTitle>
      </CustomerCardHeader>
      <CustomerCardContent>
        <div className='space-y-4'>
          <div className='text-2xl font-bold'>$89.99</div>
          <CustomerButton variant='default' size='lg' fullWidth>
            Pay Now
          </CustomerButton>
        </div>
      </CustomerCardContent>
    </CustomerCard>
  );
}
```

### 3. Admin Portal Example

```tsx
import {
  AdminButton,
  AdminCard,
  AdminDataTable,
  AdminInput,
} from '@dotmac/styled-components/admin';

function CustomerManagement() {
  return (
    <AdminCard compact>
      <AdminCardHeader
        actions={
          <AdminButton size='sm' leftIcon={<PlusIcon />}>
            Add Customer
          </AdminButton>
        }
      >
        <AdminCardTitle>Customer Database</AdminCardTitle>
      </AdminCardHeader>
      <AdminCardContent>
        <AdminDataTable
          columns={customerColumns}
          data={customers}
          enableBulkActions
          enableQuickFilter
          compact
        />
      </AdminCardContent>
    </AdminCard>
  );
}
```

## 🎯 Component Examples

### Buttons Across Portals

```tsx
// Admin Portal - Compact and functional
<AdminButton variant="default" size="sm" leftIcon={<EditIcon />}>
  Edit
</AdminButton>

// Customer Portal - Friendly and accessible
<CustomerButton variant="default" size="lg" fullWidth>
  Update My Plan
</CustomerButton>

// Reseller Portal - Professional with brand accent
<ResellerButton variant="brand" glow>
  Launch Campaign
</ResellerButton>
```

### Cards with Portal Styling

```tsx
// Admin Portal - Dense information display
<AdminCard variant="outlined" compact>
  <AdminCardHeader>
    <AdminCardTitle size="sm">Network Status</AdminCardTitle>
  </AdminCardHeader>
  <AdminCardContent>
    <MetricCard title="Uptime" value="99.9%" />
  </AdminCardContent>
</AdminCard>

// Customer Portal - Welcoming and spacious
<CustomerCard variant="elevated" decorative>
  <CustomerCardHeader icon={<WifiIcon />}>
    <CustomerCardTitle>Your Internet Plan</CustomerCardTitle>
    <CustomerCardDescription>
      High-speed fiber internet with unlimited data
    </CustomerCardDescription>
  </CustomerCardHeader>
  <CustomerCardContent>
    <div className="text-center">
      <div className="text-3xl font-bold">100 Mbps</div>
      <div className="text-muted-foreground">Download Speed</div>
    </div>
  </CustomerCardContent>
</CustomerCard>

// Reseller Portal - Professional with status
<ResellerCard variant="branded">
  <ResellerCardHeader
    status="active"
    category="Commission"
  >
    <ResellerCardTitle>Monthly Earnings</ResellerCardTitle>
    <ResellerCardDescription>
      Commission from customer subscriptions
    </ResellerCardDescription>
  </ResellerCardHeader>
  <ResellerCardContent metrics>
    <div className="text-2xl font-bold text-success">$2,847</div>
  </ResellerCardContent>
</ResellerCard>
```

### Forms with Validation

```tsx
// Customer Portal - Friendly form with helpful guidance
<div className="space-y-6">
  <CustomerInput
    label="Email Address"
    type="email"
    placeholder="Enter your email"
    helperText="We'll use this to send you important account updates"
    required
    fullWidth
  />

  <CustomerInput
    label="Phone Number"
    state="success"
    helperText="Phone number verified successfully"
    rightIcon={<CheckIcon />}
    fullWidth
  />

  <CustomerButton variant="default" size="lg" fullWidth>
    Update Contact Information
  </CustomerButton>
</div>

// Admin Portal - Compact form for quick data entry
<div className="grid grid-cols-3 gap-2">
  <AdminInput
    placeholder="Customer ID"
    size="sm"
    leftIcon={<SearchIcon />}
  />
  <AdminInput
    placeholder="Filter by status"
    variant="filled"
    size="sm"
  />
  <AdminButton size="sm" variant="outline">
    Apply Filters
  </AdminButton>
</div>
```

## 🎨 Shared Components

Some components work across all portals with adaptive theming:

```tsx
import { Badge, Avatar, QuickTooltip } from '@dotmac/styled-components/shared';

// Status badges that adapt to portal theme
<Badge variant="success">Active</Badge>
<Badge variant="warning" pulse>Pending</Badge>

// User avatars with status
<Avatar
  src="/user.jpg"
  fallback="JD"
  status="online"
  size="lg"
/>

// Helpful tooltips
<QuickTooltip content="Click to view customer details">
  <AdminButton variant="ghost" size="icon">
    <InfoIcon />
  </AdminButton>
</QuickTooltip>
```

## 🌙 Dark Mode Support

All portals support dark mode with automatic system detection:

```tsx
import { ThemeProvider, ThemeSwitcher } from '@dotmac/styled-components';

// Theme provider with system detection
<ThemeProvider defaultColorScheme="system">
  <App />
</ThemeProvider>

// Manual theme switcher
<ThemeSwitcher showColorSchemeSwitcher />

// Programmatic theme control
const { colorScheme, setColorScheme, toggleColorScheme } = useTheme();
```

## 📱 Responsive Design

Components automatically adapt to different screen sizes:

```tsx
// Mobile-first responsive grid
<Grid cols={1} className="md:grid-cols-2 lg:grid-cols-3" gap="md">
  <CustomerCard>Mobile: 1 col, Tablet: 2 cols, Desktop: 3 cols</CustomerCard>
</Grid>

// Responsive button sizing
<CustomerButton
  size="lg"           // Large on mobile for touch
  className="md:size-md"  // Medium on desktop
>
  Responsive Button
</CustomerButton>
```

## 🎛️ Customization

### Custom Portal Colors

```css
/* Override portal colors */
.reseller-portal {
  --reseller-primary: 210 100% 50%; /* Custom blue */
  --reseller-accent: 280 100% 50%; /* Custom purple */
}
```

### Portal-Specific Styling

```tsx
// Components automatically detect portal context
<Badge variant='default'>
  {/* Renders with admin styling in admin portal */}
  {/* Renders with customer styling in customer portal */}
  Adaptive Badge
</Badge>
```

### Theme Utilities

```tsx
import { cn, createPortalTheme } from '@dotmac/styled-components';

// Create custom theme utilities
const myTheme = createPortalTheme('customer');

// Use theme-aware class names
<div className={cn('base-styles', myTheme.class('custom-component'))}>Themed content</div>;
```

## 🔧 Advanced Usage

### Portal Switching

```tsx
function MultiPortalApp() {
  const [currentPortal, setCurrentPortal] = useState('customer');

  return (
    <ThemeProvider portal={currentPortal}>
      {currentPortal === 'admin' && <AdminDashboard />}
      {currentPortal === 'customer' && <CustomerPortal />}
      {currentPortal === 'reseller' && <ResellerPortal />}

      <ThemeSwitcher showPortalSwitcher />
    </ThemeProvider>
  );
}
```

### Custom Component Creation

```tsx
import { cn, customerTheme } from '@dotmac/styled-components/customer';

// Create portal-specific custom components
function CustomMetricCard({ value, label, trend }) {
  return (
    <div
      className={cn(
        'p-4 rounded-lg border',
        customerTheme.shadow.md,
        'bg-customer-card border-customer-border'
      )}
    >
      <div className='text-2xl font-bold'>{value}</div>
      <div className='text-sm text-customer-muted-foreground'>{label}</div>
      {trend && (
        <Badge variant={trend > 0 ? 'success' : 'destructive'} size='sm'>
          {trend > 0 ? '+' : ''}
          {trend}%
        </Badge>
      )}
    </div>
  );
}
```

## 🚀 Performance

### Tree Shaking

Import only what you need for optimal bundle sizes:

```tsx
// ✅ Good - only imports specific components
import { CustomerButton } from '@dotmac/styled-components/customer';

// ❌ Avoid - imports entire library
import { CustomerButton } from '@dotmac/styled-components';
```

### Component Lazy Loading

```tsx
// Lazy load portal-specific components
const AdminDashboard = lazy(() => import('./AdminDashboard'));
const CustomerPortal = lazy(() => import('./CustomerPortal'));

<Suspense fallback={<Loading />}>
  {portal === 'admin' && <AdminDashboard />}
  {portal === 'customer' && <CustomerPortal />}
</Suspense>;
```

## 📊 Component Matrix

| Component | Admin | Customer | Reseller | Shared |
| --------- | ----- | -------- | -------- | ------ |
| Button    | ✅    | ✅       | ✅       | ❌     |
| Card      | ✅    | ✅       | ✅       | ❌     |
| Input     | ✅    | ✅       | ✅       | ❌     |
| DataTable | ✅    | ❌       | ❌       | ❌     |
| Badge     | ❌    | ❌       | ❌       | ✅     |
| Avatar    | ❌    | ❌       | ❌       | ✅     |
| Tooltip   | ❌    | ❌       | ❌       | ✅     |

## 🛠️ Development

```bash
# Install dependencies
pnpm install

# Build the package
pnpm build

# Watch for changes
pnpm dev

# Type checking
pnpm type-check

# Linting
pnpm lint
```

## 📄 License

MIT © DotMac Platform

---

**Ready to build beautiful ISP interfaces? Start with the portal that matches
your users' needs! 🚀**
