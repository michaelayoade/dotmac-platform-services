# DotMac Platform - User Journey Documentation

This document outlines the complete user journeys for all user types in the DotMac Platform Services ecosystem.

## Table of Contents

1. [Overview](#overview)
2. [User Types](#user-types)
3. [Platform Admin Journeys](#platform-admin-journeys)
4. [Tenant User Journeys](#tenant-user-journeys)
5. [Partner Journeys](#partner-journeys)
6. [Cross-Cutting Flows](#cross-cutting-flows)

---

## Overview

DotMac Platform Services is a multi-tenant SaaS control plane with three distinct portal experiences:

| Portal | URL Path | Primary Users |
|--------|----------|---------------|
| Admin Dashboard | `/dashboard/*` | Platform Administrators |
| Tenant Portal | `/portal/*` | Tenant Account Holders |
| Partner Portal | `/partner/*` | ISP Partners & Resellers |

---

## User Types

### Platform Administrator
- Full system access
- Manages all tenants, users, billing, and deployments
- Access to analytics and monitoring
- Configures platform settings

### Tenant User
- Organization-scoped access
- Manages team members within tenant
- Views billing and usage
- Configures tenant settings

### Partner
- Referral program participant
- Tracks commissions and referrals
- Manages referred tenants
- Views financial statements

---

## Platform Admin Journeys

### 1. Admin First-Time Setup

```mermaid
flowchart TD
    A[Admin Receives Invite] --> B[Navigate to /auth/login]
    B --> C[Enter Credentials]
    C --> D{Email Verified?}
    D -->|No| E[Check Email for Verification]
    E --> F[Click Verification Link]
    F --> G[Email Verified]
    D -->|Yes| G
    G --> H{2FA Required?}
    H -->|Yes| I[Setup TOTP Authenticator]
    I --> J[Scan QR Code]
    J --> K[Enter Verification Code]
    K --> L[Save Backup Codes]
    H -->|No| M[Access Dashboard]
    L --> M
    M --> N[Complete Profile Setup]
    N --> O[Ready for Platform Management]
```

### 2. User Management Journey

```mermaid
flowchart TD
    A[Admin Dashboard] --> B[Navigate to Users Section]
    B --> C{Action Required}
    C -->|Create User| D[Click 'Add User']
    D --> E[Fill User Details]
    E --> F[Assign Role & Permissions]
    F --> G[Send Invitation Email]
    G --> H[User Created]

    C -->|Edit User| I[Select User from List]
    I --> J[Modify User Details]
    J --> K[Update Permissions]
    K --> L[Save Changes]

    C -->|Disable User| M[Select User]
    M --> N[Click Disable]
    N --> O[Confirm Action]
    O --> P[User Sessions Revoked]

    C -->|View Activity| Q[Select User]
    Q --> R[View Audit Trail]
    R --> S[Filter by Date/Action]
```

### 3. Tenant Management Journey

```mermaid
flowchart TD
    A[Admin Dashboard] --> B[Navigate to Tenants]
    B --> C{Action Required}

    C -->|Create Tenant| D[Click 'New Tenant']
    D --> E[Enter Organization Details]
    E --> F[Select Subscription Plan]
    F --> G[Configure Settings]
    G --> H[Assign Admin User]
    H --> I[Tenant Created]
    I --> J[Provisioning Initiated]

    C -->|Manage Tenant| K[Select Tenant]
    K --> L{Sub-Action}
    L -->|View Details| M[Tenant Overview]
    L -->|Edit Settings| N[Modify Configuration]
    L -->|View Usage| O[Usage Analytics]
    L -->|Manage Billing| P[Billing Section]
    L -->|Suspend| Q[Suspend Tenant]
    Q --> R[Confirm Suspension]
    R --> S[Services Paused]

    C -->|Delete Tenant| T[Select Tenant]
    T --> U[Initiate Soft Delete]
    U --> V[Retention Period Starts]
    V --> W{Restore?}
    W -->|Yes| X[Restore Tenant]
    W -->|No| Y[Permanent Deletion]
```

### 4. Billing Administration Journey

```mermaid
flowchart TD
    A[Admin Dashboard] --> B[Navigate to Billing]
    B --> C{Billing Action}

    C -->|Generate Invoice| D[Select Tenant]
    D --> E[Choose Invoice Type]
    E --> F[Set Line Items]
    F --> G[Apply Discounts/Tax]
    G --> H[Preview Invoice]
    H --> I[Generate & Send]
    I --> J[Invoice Sent to Tenant]

    C -->|Record Payment| K[Select Invoice]
    K --> L[Enter Payment Details]
    L --> M[Select Payment Method]
    M --> N[Record Transaction]
    N --> O[Invoice Marked Paid]

    C -->|Manage Dunning| P[View Overdue Invoices]
    P --> Q[Select Dunning Campaign]
    Q --> R[Configure Reminders]
    R --> S[Set Escalation Rules]
    S --> T[Activate Campaign]

    C -->|Issue Credit| U[Select Tenant/Invoice]
    U --> V[Create Credit Note]
    V --> W[Specify Amount & Reason]
    W --> X[Apply Credit]
```

### 5. Deployment Management Journey

```mermaid
flowchart TD
    A[Admin Dashboard] --> B[Navigate to Deployments]
    B --> C{Deployment Action}

    C -->|New Deployment| D[Select Product]
    D --> E[Choose Target Tenant]
    E --> F[Select Deployment Type]
    F --> G{Deployment Target}
    G -->|Kubernetes| H[Configure Helm Values]
    G -->|Docker| I[Set Compose Config]
    G -->|AWX| J[Select Playbook]
    H --> K[Set Resource Limits]
    I --> K
    J --> K
    K --> L[Initiate Provisioning]
    L --> M[Monitor Progress]
    M --> N{Status}
    N -->|Success| O[Deployment Active]
    N -->|Failed| P[View Error Logs]
    P --> Q[Retry/Rollback]

    C -->|Scale| R[Select Deployment]
    R --> S[Adjust Resources]
    S --> T[Apply Changes]
    T --> U[Scaling in Progress]

    C -->|Suspend| V[Select Deployment]
    V --> W[Confirm Suspension]
    W --> X[Resources Released]
```

### 6. Analytics & Monitoring Journey

```mermaid
flowchart TD
    A[Admin Dashboard] --> B[Navigate to Analytics]
    B --> C{Analytics View}

    C -->|Platform Overview| D[View KPIs Dashboard]
    D --> E[Active Users/Tenants]
    D --> F[Revenue Metrics]
    D --> G[System Health]

    C -->|Tenant Analytics| H[Select Tenant]
    H --> I[Usage Metrics]
    H --> J[Growth Trends]
    H --> K[Feature Adoption]

    C -->|Revenue Reports| L[Select Date Range]
    L --> M[MRR/ARR Charts]
    L --> N[Churn Analysis]
    L --> O[Export Reports]

    C -->|System Monitoring| P[Health Dashboard]
    P --> Q[Service Status]
    P --> R[Error Rates]
    P --> S[Performance Metrics]
    P --> T[Alert Configuration]
```

---

## Tenant User Journeys

### 1. Tenant Self-Signup Journey

```mermaid
flowchart TD
    A[Visitor] --> B[Navigate to /auth/signup]
    B --> C[Fill Registration Form]
    C --> D[Username/Email/Password]
    D --> E[Submit Registration]
    E --> F[System Creates User]
    F --> G[System Creates Tenant Org]
    G --> H[Verification Email Sent]
    H --> I[User Clicks Verify Link]
    I --> J[Email Confirmed]
    J --> K[Auto-Login to Portal]
    K --> L[Welcome Dashboard]
    L --> M[Guided Onboarding]
    M --> N{Select Plan}
    N -->|Free| O[Free Tier Activated]
    N -->|Paid| P[Enter Payment Info]
    P --> Q[Subscription Created]
    O --> R[Portal Ready]
    Q --> R
```

### 2. Tenant Portal Dashboard Journey

```mermaid
flowchart TD
    A[Tenant User Login] --> B[Portal Dashboard]
    B --> C{Dashboard Sections}

    C -->|Overview| D[Key Metrics Widget]
    D --> E[Active Users Count]
    D --> F[Usage Summary]
    D --> G[Billing Status]
    D --> H[Recent Activity]

    C -->|Quick Actions| I[Common Tasks]
    I --> J[Invite Team Member]
    I --> K[View Invoices]
    I --> L[Update Settings]

    C -->|Notifications| M[Alert Panel]
    M --> N[System Notices]
    M --> O[Billing Alerts]
    M --> P[Action Items]
```

### 3. Team Management Journey

```mermaid
flowchart TD
    A[Tenant Portal] --> B[Navigate to Team]
    B --> C{Team Action}

    C -->|Invite Member| D[Click 'Invite']
    D --> E[Enter Email Address]
    E --> F[Select Role]
    F --> G[Send Invitation]
    G --> H[Invitee Receives Email]
    H --> I[Invitee Clicks Link]
    I --> J{Has Account?}
    J -->|Yes| K[Login & Accept]
    J -->|No| L[Create Account]
    L --> M[Accept Invitation]
    K --> N[Member Added to Team]
    M --> N

    C -->|Manage Roles| O[Select Member]
    O --> P[Change Role]
    P --> Q[Update Permissions]
    Q --> R[Save Changes]

    C -->|Remove Member| S[Select Member]
    S --> T[Click Remove]
    T --> U[Confirm Removal]
    U --> V[Access Revoked]
```

### 4. Tenant Billing Journey

```mermaid
flowchart TD
    A[Tenant Portal] --> B[Navigate to Billing]
    B --> C{Billing Section}

    C -->|View Invoices| D[Invoice List]
    D --> E[Filter by Status/Date]
    E --> F[Select Invoice]
    F --> G[View Details]
    G --> H[Download PDF]

    C -->|Payment Methods| I[Saved Methods List]
    I --> J{Action}
    J -->|Add Card| K[Enter Card Details]
    K --> L[Stripe Validation]
    L --> M[Card Saved]
    J -->|Set Default| N[Select Card]
    N --> O[Mark as Default]
    J -->|Remove| P[Select Card]
    P --> Q[Confirm Removal]

    C -->|Subscription| R[Current Plan Details]
    R --> S{Plan Action}
    S -->|Upgrade| T[View Available Plans]
    T --> U[Select New Plan]
    U --> V[Confirm Upgrade]
    V --> W[Prorated Billing]
    S -->|Downgrade| X[Select Lower Plan]
    X --> Y[Effective Next Cycle]
    S -->|Cancel| Z[Initiate Cancellation]
    Z --> AA[Retention Offer]
    AA --> AB{Accept?}
    AB -->|Yes| AC[Plan Retained]
    AB -->|No| AD[Cancellation Scheduled]
```

Note: Payment method management is planned; current tenant portal surfaces placeholders for add/edit actions but does not persist payment methods yet.

### 5. Tenant Usage Monitoring Journey

```mermaid
flowchart TD
    A[Tenant Portal] --> B[Navigate to Usage]
    B --> C[Usage Dashboard]
    C --> D{Usage Metrics}

    D -->|API Calls| E[Request Volume Chart]
    E --> F[Daily/Weekly/Monthly View]
    F --> G[Endpoint Breakdown]

    D -->|Storage| H[Storage Usage]
    H --> I[Current vs Limit]
    I --> J[Usage Trend]

    D -->|Users| K[Active Users]
    K --> L[Seats Used vs Available]
    L --> M[User Activity Heatmap]

    D -->|Alerts| N[Usage Alerts Config]
    N --> O[Set Thresholds]
    O --> P[Enable Notifications]
    P --> Q[Email/In-App Alerts]
```

### 6. Tenant Settings Journey

```mermaid
flowchart TD
    A[Tenant Portal] --> B[Navigate to Settings]
    B --> C{Settings Category}

    C -->|Organization| D[Company Details]
    D --> E[Name/Logo/Address]
    E --> F[Save Changes]

    C -->|Security| G[Security Settings]
    G --> H[Password Policy]
    G --> I[2FA Requirements]
    G --> J[Session Timeout]
    G --> K[IP Allowlist]

    C -->|Notifications| L[Notification Prefs]
    L --> M[Email Preferences]
    L --> N[In-App Settings]
    L --> O[Alert Thresholds]

    C -->|Integrations| P[Connected Apps]
    P --> Q[View Active Integrations]
    P --> R[Add New Integration]
    R --> S[OAuth Authorization]
    S --> T[Configure Permissions]
    T --> U[Integration Active]

    C -->|API Keys| V[API Key Management]
    V --> W[Generate New Key]
    W --> X[Set Permissions]
    X --> Y[Copy Key - One Time]
    V --> Z[Revoke Existing Key]
```

---

## Partner Journeys

### 1. Partner Registration Journey

```mermaid
flowchart TD
    A[Potential Partner] --> B[Navigate to Partner Signup]
    B --> C[Fill Application Form]
    C --> D[Company Information]
    D --> E[Contact Details]
    E --> F[Business Type Selection]
    F --> G[Submit Application]
    G --> H[Application Under Review]
    H --> I{Approval Decision}
    I -->|Approved| J[Welcome Email Sent]
    J --> K[Account Activated]
    K --> L[Access Partner Portal]
    I -->|Rejected| M[Rejection Notice]
    M --> N[Feedback Provided]
    I -->|More Info| O[Request for Details]
    O --> P[Partner Provides Info]
    P --> H
```

### 2. Partner Dashboard Journey

```mermaid
flowchart TD
    A[Partner Login] --> B[Partner Dashboard]
    B --> C{Dashboard Sections}

    C -->|Performance Overview| D[KPI Cards]
    D --> E[Total Referrals]
    D --> F[Active Customers]
    D --> G[Monthly Earnings]
    D --> H[Conversion Rate]

    C -->|Recent Activity| I[Activity Feed]
    I --> J[New Signups]
    I --> K[Commission Events]
    I --> L[Customer Updates]

    C -->|Quick Stats| M[Charts Panel]
    M --> N[Referral Trends]
    M --> O[Revenue Graph]
    M --> P[Customer Growth]
```

### 3. Referral Management Journey

```mermaid
flowchart TD
    A[Partner Portal] --> B[Navigate to Referrals]
    B --> C{Referral Actions}

    C -->|Generate Link| D[Create Referral Link]
    D --> E[Select Campaign]
    E --> F[Customize Parameters]
    F --> G[Generate Unique URL]
    G --> H[Copy/Share Link]

    C -->|Track Referrals| I[Referral List]
    I --> J[Filter by Status]
    J --> K[View Referral Details]
    K --> L[Customer Info]
    K --> M[Signup Date]
    K --> N[Conversion Status]
    K --> O[Associated Revenue]

    C -->|Monitor Pipeline| P[Conversion Funnel]
    P --> Q[Clicked Links]
    P --> R[Started Signup]
    P --> S[Completed Registration]
    P --> T[Converted to Paid]
```

### 4. Commission Tracking Journey

```mermaid
flowchart TD
    A[Partner Portal] --> B[Navigate to Commissions]
    B --> C{Commission Views}

    C -->|Pending| D[Pending Commissions]
    D --> E[Customer Name]
    D --> F[Transaction Amount]
    D --> G[Commission Rate]
    D --> H[Expected Payout]

    C -->|Earned| I[Earned Commissions]
    I --> J[Filter by Period]
    J --> K[Commission Breakdown]
    K --> L[By Customer]
    K --> M[By Product]
    K --> N[By Month]

    C -->|Paid Out| O[Payout History]
    O --> P[Payment Date]
    O --> Q[Amount]
    O --> R[Payment Method]
    O --> S[Download Receipt]
```

### 5. Partner Financial Statements Journey

```mermaid
flowchart TD
    A[Partner Portal] --> B[Navigate to Statements]
    B --> C[Statement List]
    C --> D[Select Period]
    D --> E[View Statement]
    E --> F{Statement Sections}

    F -->|Summary| G[Period Overview]
    G --> H[Total Revenue Generated]
    G --> I[Commission Earned]
    G --> J[Adjustments]
    G --> K[Net Payout]

    F -->|Details| L[Line Items]
    L --> M[Per-Customer Breakdown]
    L --> N[Transaction Details]
    L --> O[Commission Calculations]

    F -->|Export| P[Download Options]
    P --> Q[PDF Statement]
    P --> R[CSV Export]
    P --> S[Send to Email]
```

### 6. Partner Tenant Management Journey

```mermaid
flowchart TD
    A[Partner Portal] --> B[Navigate to Tenants]
    B --> C[Referred Tenants List]
    C --> D[Select Tenant]
    D --> E{Tenant Views}

    E -->|Overview| F[Tenant Summary]
    F --> G[Status]
    F --> H[Plan Type]
    F --> I[Signup Date]
    F --> J[Lifetime Value]

    E -->|Activity| K[Customer Activity]
    K --> L[Login History]
    K --> M[Usage Patterns]
    K --> N[Support Tickets]

    E -->|Revenue| O[Revenue Details]
    O --> P[Monthly Spend]
    O --> Q[Payment History]
    O --> R[Commission Generated]

    E -->|Support| S[Request Support]
    S --> T[Create Ticket for Customer]
    S --> U[Escalate Issue]
```

---

## Cross-Cutting Flows

### 1. Authentication Flow

```mermaid
flowchart TD
    A[User Visits Platform] --> B{Has Account?}
    B -->|No| C[Navigate to Signup]
    C --> D[Fill Registration Form]
    D --> E[Submit Credentials]
    E --> F[Server Validates Input]
    F --> G[Create User Record]
    G --> H[Send Verification Email]
    H --> I[User Verifies Email]
    I --> J[Account Activated]

    B -->|Yes| K[Navigate to Login]
    K --> L[Enter Credentials]
    L --> M[Server Validates]
    M --> N{Valid?}
    N -->|No| O[Show Error]
    O --> K
    N -->|Yes| P{2FA Enabled?}
    P -->|Yes| Q[Enter TOTP Code]
    Q --> R{Code Valid?}
    R -->|No| S[Retry/Backup Code]
    R -->|Yes| T[Generate Tokens]
    P -->|No| T
    T --> U[Set HttpOnly Cookies]
    U --> V[Redirect to Dashboard]

    J --> K
```

### 2. Password Reset Flow

```mermaid
flowchart TD
    A[User Forgot Password] --> B[Click 'Forgot Password']
    B --> C[Enter Email Address]
    C --> D[Submit Request]
    D --> E[Server Generates Token]
    E --> F[Send Reset Email]
    F --> G[User Opens Email]
    G --> H[Click Reset Link]
    H --> I[Token Validation]
    I --> J{Valid Token?}
    J -->|No| K[Token Expired/Invalid]
    K --> L[Request New Link]
    L --> C
    J -->|Yes| M[Show Password Form]
    M --> N[Enter New Password]
    N --> O[Confirm Password]
    O --> P[Submit]
    P --> Q[Password Updated]
    Q --> R[All Sessions Invalidated]
    R --> S[Redirect to Login]
```

### 3. Session Management Flow

```mermaid
flowchart TD
    A[User Makes Request] --> B[Extract Access Token]
    B --> C{Token Present?}
    C -->|No| D[Return 401]
    C -->|Yes| E[Validate JWT]
    E --> F{Token Valid?}
    F -->|No| G{Expired?}
    G -->|Yes| H[Try Refresh Token]
    H --> I{Refresh Valid?}
    I -->|Yes| J[Issue New Access Token]
    J --> K[Continue Request]
    I -->|No| L[Return 401 - Re-login]
    G -->|No| M[Return 401 - Invalid]
    F -->|Yes| N[Extract User/Tenant Context]
    N --> O[Check Permissions]
    O --> P{Authorized?}
    P -->|Yes| K
    P -->|No| Q[Return 403]
```

### 4. Invoice Lifecycle Flow

```mermaid
flowchart TD
    A[Invoice Creation] --> B[Draft Status]
    B --> C[Add Line Items]
    C --> D[Calculate Totals]
    D --> E[Apply Tax]
    E --> F[Generate Invoice Number]
    F --> G[Finalize Invoice]
    G --> H[Pending Status]
    H --> I[Send to Customer]
    I --> J{Payment Received?}
    J -->|Yes| K[Payment Recorded]
    K --> L[Paid Status]
    J -->|No| M{Due Date Passed?}
    M -->|Yes| N[Overdue Status]
    N --> O[Dunning Campaign]
    O --> P[Send Reminders]
    P --> Q{Payment After Reminder?}
    Q -->|Yes| K
    Q -->|No| R{Max Retries?}
    R -->|No| P
    R -->|Yes| S[Escalate - Suspend Tenant]
    M -->|No| T[Wait]
    T --> J
```

### 5. Subscription Lifecycle Flow

```mermaid
flowchart TD
    A[New Subscription] --> B[Trial Period]
    B --> C{Trial Expires}
    C --> D{Converted to Paid?}
    D -->|Yes| E[Active Subscription]
    D -->|No| F[Subscription Expired]

    E --> G{Monthly Cycle}
    G --> H[Generate Invoice]
    H --> I[Process Payment]
    I --> J{Payment Success?}
    J -->|Yes| K[Continue Service]
    K --> G
    J -->|No| L[Grace Period]
    L --> M[Retry Payment]
    M --> N{Retry Success?}
    N -->|Yes| K
    N -->|No| O{Max Retries?}
    O -->|No| M
    O -->|Yes| P[Suspend Subscription]

    E --> Q{User Cancels?}
    Q -->|Yes| R[Cancellation Scheduled]
    R --> S[Service Until Period End]
    S --> T[Subscription Cancelled]

    E --> U{Upgrade/Downgrade?}
    U -->|Yes| V[Plan Change]
    V --> W[Prorated Adjustment]
    W --> E
```

### 6. Multi-Factor Authentication Setup Flow

```mermaid
flowchart TD
    A[User Settings] --> B[Navigate to Security]
    B --> C[Click Enable 2FA]
    C --> D[Server Generates Secret]
    D --> E[Display QR Code]
    E --> F[User Scans with Auth App]
    F --> G[Enter Verification Code]
    G --> H{Code Valid?}
    H -->|No| I[Show Error]
    I --> G
    H -->|Yes| J[Generate Backup Codes]
    J --> K[Display Backup Codes]
    K --> L[User Saves Codes]
    L --> M[Confirm Saved]
    M --> N[2FA Activated]
    N --> O[All Sessions Require 2FA]
```

### 7. API Key Management Flow

```mermaid
flowchart TD
    A[User/Admin Portal] --> B[Navigate to API Keys]
    B --> C{API Key Action}

    C -->|Create| D[Click Generate Key]
    D --> E[Enter Key Name]
    E --> F[Select Permissions]
    F --> G[Set Expiration]
    G --> H[Generate Key]
    H --> I[Display Key Once]
    I --> J[User Copies Key]
    J --> K[Key Active]

    C -->|Rotate| L[Select Existing Key]
    L --> M[Click Rotate]
    M --> N[New Key Generated]
    N --> O[Old Key Deprecated]
    O --> P[Grace Period]
    P --> Q[Old Key Revoked]

    C -->|Revoke| R[Select Key]
    R --> S[Click Revoke]
    S --> T[Confirm Revocation]
    T --> U[Key Immediately Invalid]
```

---

## Appendix: User Role Permissions Matrix

| Feature | Platform Admin | Tenant Admin | Tenant Member | Partner |
|---------|---------------|--------------|---------------|---------|
| Manage All Users | Yes | No | No | No |
| Manage Tenant Users | Yes | Yes | No | No |
| View All Tenants | Yes | No | No | No |
| Manage Own Tenant | Yes | Yes | Limited | No |
| Platform Billing | Yes | No | No | No |
| Tenant Billing | Yes | Yes | View Only | No |
| Deployments | Yes | No | No | No |
| Analytics (Platform) | Yes | No | No | No |
| Analytics (Tenant) | Yes | Yes | Yes | Limited |
| Partner Management | Yes | No | No | Self |
| System Settings | Yes | No | No | No |
| Tenant Settings | Yes | Yes | Limited | No |

---

## Document Metadata

| Property | Value |
|----------|-------|
| Version | 1.0.0 |
| Last Updated | 2024 |
| Status | Active |
| Owner | Platform Team |
