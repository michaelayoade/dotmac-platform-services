# DotMac Platform Frontend Sitemap

## 📱 Application Structure

Your Next.js app has **3 main sections**: Public, Dashboard, and Partner Portal

---

## 🌐 PUBLIC PAGES

### Authentication
- `/` - Landing/Home page
- `/login` - User login
- `/register` - User registration
- `/forgot-password` - Password recovery

### Testing
- `/test-plugins` - Plugin testing interface

---

## 🏢 MAIN DASHBOARD (`/dashboard`)

### 🏠 Home
- `/dashboard` - Main dashboard home

### 💰 Billing & Revenue (`/dashboard/billing-revenue`)
- `/dashboard/billing-revenue` - Billing overview
- `/dashboard/billing-revenue/invoices` - Invoice management
- `/dashboard/billing-revenue/invoices/catalog` - Product catalog
- `/dashboard/billing-revenue/invoices/subscriptions` - Subscription invoices
- `/dashboard/billing-revenue/payments` - Payment processing
- `/dashboard/billing-revenue/plans` - Pricing plans
- `/dashboard/billing-revenue/subscriptions` - Subscription management

### 🏦 Banking
- `/dashboard/banking` - Banking operations
- `/dashboard/billing` - Legacy billing (may be deprecated)

### 🔐 Security & Access (`/dashboard/security-access`)
- `/dashboard/security-access` - Security overview
- `/dashboard/security-access/api-keys` - API key management
- `/dashboard/security-access/permissions` - Permission management
- `/dashboard/security-access/roles` - Role management
- `/dashboard/security-access/secrets` - Secrets/credentials management
- `/dashboard/security-access/users` - User management

### 👥 Admin (`/dashboard/admin`)
- `/dashboard/admin/roles` - Advanced role administration

### 🤝 Partners (`/dashboard/partners`)
- `/dashboard/partners` - Partner listing
- `/dashboard/partners/[id]` - Individual partner details (dynamic route)

### 🔧 Operations (`/dashboard/operations`)
- `/dashboard/operations` - Operations overview
- `/dashboard/operations/communications` - Communication management
- `/dashboard/operations/customers` - Customer operations
- `/dashboard/operations/files` - File management

### 🏗️ Infrastructure (`/dashboard/infrastructure`)
- `/dashboard/infrastructure` - Infrastructure overview
- `/dashboard/infrastructure/feature-flags` - Feature flag management
- `/dashboard/infrastructure/health` - System health monitoring
- `/dashboard/infrastructure/imports` - Data import tools
- `/dashboard/infrastructure/logs` - Log management
- `/dashboard/infrastructure/observability` - Observability/monitoring

### 📊 Analytics
- `/dashboard/analytics` - Analytics & reporting

### 🔗 Webhooks
- `/dashboard/webhooks` - Webhook management

### ⚙️ Settings (`/dashboard/settings`)
- `/dashboard/settings` - Settings home
- `/dashboard/settings/billing` - Billing settings
- `/dashboard/settings/integrations` - Integration settings
- `/dashboard/settings/notifications` - Notification preferences
- `/dashboard/settings/organization` - Organization settings
- `/dashboard/settings/plugins` - Plugin configuration
- `/dashboard/settings/profile` - User profile settings

---

## 🤝 PARTNER PORTAL (`/portal`)

### Authentication
- `/portal/login` - Partner login

### Portal Pages
- `/portal/dashboard` - Partner dashboard
- `/portal/customers` - Partner customers
- `/portal/commissions` - Commission tracking
- `/portal/referrals` - Referral management
- `/portal/settings` - Partner settings

---

## 📂 Route Hierarchy

```
/
├── Public Routes
│   ├── / (home)
│   ├── /login
│   ├── /register
│   ├── /forgot-password
│   └── /test-plugins
│
├── /dashboard (Protected - Main App)
│   ├── / (dashboard home)
│   │
│   ├── /billing-revenue
│   │   ├── / (overview)
│   │   ├── /invoices
│   │   │   ├── / (list)
│   │   │   ├── /catalog
│   │   │   └── /subscriptions
│   │   ├── /payments
│   │   ├── /plans
│   │   └── /subscriptions
│   │
│   ├── /banking
│   ├── /billing (legacy?)
│   │
│   ├── /security-access
│   │   ├── / (overview)
│   │   ├── /api-keys
│   │   ├── /permissions
│   │   ├── /roles
│   │   ├── /secrets
│   │   └── /users
│   │
│   ├── /admin
│   │   └── /roles
│   │
│   ├── /partners
│   │   ├── / (list)
│   │   └── /[id] (detail)
│   │
│   ├── /operations
│   │   ├── / (overview)
│   │   ├── /communications
│   │   ├── /customers
│   │   └── /files
│   │
│   ├── /infrastructure
│   │   ├── / (overview)
│   │   ├── /feature-flags
│   │   ├── /health
│   │   ├── /imports
│   │   ├── /logs
│   │   └── /observability
│   │
│   ├── /analytics
│   ├── /webhooks
│   │
│   └── /settings
│       ├── / (home)
│       ├── /billing
│       ├── /integrations
│       ├── /notifications
│       ├── /organization
│       ├── /plugins
│       └── /profile
│
└── /portal (Protected - Partner Portal)
    ├── /login
    ├── /dashboard
    ├── /customers
    ├── /commissions
    ├── /referrals
    └── /settings
```

---

## 🔑 Key Features by Section

### 💰 Billing & Revenue
Complete billing suite with invoicing, subscriptions, payment processing, and product catalog management.

### 🔐 Security & Access
Comprehensive RBAC system with API keys, roles, permissions, secrets, and user management.

### 🤝 Partner Management
Partner portal with separate authentication, commission tracking, and referral management.

### 🏗️ Infrastructure
DevOps tools including health monitoring, logs, observability, feature flags, and data imports.

### 📊 Analytics & Operations
Customer management, communications, file handling, and analytics dashboards.

---

## 📝 Notes

- **Main App**: `/dashboard/*` - Primary application for internal users
- **Partner Portal**: `/portal/*` - Separate interface for partners/affiliates
- **Authentication**: Separate login flows for main app vs partner portal
- **Dynamic Routes**: `/dashboard/partners/[id]` uses Next.js dynamic routing
- **Nested Routes**: Deep nesting in billing-revenue and infrastructure sections
- **Settings**: Centralized settings hub with 7 sub-sections

---

## 🎨 Layout Structure

### Root Layout (`/app/layout.tsx`)
- Base layout for entire app
- Likely includes global providers (Theme, Auth, etc.)

### Dashboard Layout (`/app/dashboard/layout.tsx`)
- Protected layout for main dashboard
- Probably includes sidebar navigation
- Authentication guards

### Portal Layout (`/app/portal/layout.tsx`)
- Separate layout for partner portal
- Different navigation/branding
- Partner-specific authentication

---

## 🚀 Next Steps for Analysis

Would you like me to:
1. **Analyze component structure** - Map out reusable components
2. **Document API endpoints** - List all backend calls
3. **Map user flows** - Document user journeys through the app
4. **Extract navigation structure** - Document menu/sidebar configs
5. **Analyze authentication** - Document auth flows and guards
6. **Review form structures** - Document all forms and validations

Let me know what specific aspect you'd like me to dive deeper into!
