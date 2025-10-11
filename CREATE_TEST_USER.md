# How to Login as a Tenant

## Authentication Architecture

DotMac Platform has **two separate login portals**:

### 1. 🏢 **Main Platform Login** (Tenant Users)
**URL:** http://localhost:3000/login

**Purpose:** For regular tenant users (customers, employees, admins within an organization)

**Test Credentials (Development):**
```
Email: admin@example.com
Password: admin123
```

**Features:**
- Access to tenant dashboard
- Manage tenant resources
- Standard user permissions
- Tenant-isolated data

---

### 2. 🤝 **Partner Portal Login**
**URL:** http://localhost:3000/portal/login

**Purpose:** For partners (resellers, affiliates, integration partners)

**API Endpoint:** `/api/v1/partners/auth/login`

**Features:**
- Partner-specific dashboard
- Revenue tracking
- Commission management
- Partner onboarding

---

## Quick Start: Register a Test User

Since the seed script needs updating, here's how to register a new user:

### Option 1: Use the API Directly

```bash
# Register a new tenant user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "Test123!@#",
    "full_name": "Test User"
  }'
```

### Option 2: Use the Frontend Registration Page

1. Go to http://localhost:3000/register
2. Fill in the form:
   - Username: `testuser`
   - Email: `test@example.com`
   - Password: `Test123!@#` (min 8 chars)
   - Full Name: `Test User`
3. Click "Sign up"
4. You'll be redirected to the dashboard

---

## How Login Works

### Multi-Tenant Isolation

The platform uses **automatic tenant detection** based on:

1. **User's tenant_id** - Each user belongs to a tenant
2. **JWT Claims** - Token includes tenant_id for isolation
3. **Middleware** - Automatically enforces tenant context
4. **Database Queries** - All queries filter by tenant_id

### Single Login Page for All Tenants

**Yes, there is ONE login page** for all tenant users: http://localhost:3000/login

**How it works:**
1. User enters email + password
2. Backend looks up user and their associated tenant
3. JWT token is generated with `tenant_id` claim
4. User sees only their tenant's data
5. Middleware enforces tenant isolation on every request

**Example Flow:**
```
User A (Acme Corp, tenant_id=1) logs in
  ↓
Gets JWT with tenant_id=1
  ↓
Can only see Acme Corp's data

User B (TechStart, tenant_id=2) logs in
  ↓
Gets JWT with tenant_id=2
  ↓
Can only see TechStart's data
```

---

## Security Features (All Active!)

✅ **Token Type Validation**
- Refresh tokens cannot be used as access tokens
- Access tokens expire in 15 minutes
- Refresh tokens expire in 7 days

✅ **Rate Limiting**
- Login: 5 attempts/minute
- Register: 3 attempts/minute
- Password Reset: 3 attempts/minute

✅ **Session Management**
- HttpOnly cookies (XSS protection)
- Secure flag in production (HTTPS only)
- SameSite=strict in production (CSRF protection)

✅ **Tenant Isolation**
- Every query filters by tenant_id
- JWT contains tenant_id
- Middleware enforces context

---

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Login (get tokens)
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Logout (revoke token)
- `GET /api/v1/auth/me` - Get current user info

### Partner Portal
- `POST /api/v1/partners/auth/login` - Partner login
- `POST /api/v1/partners/auth/register` - Partner registration

---

## Testing Authentication

### 1. Register via API
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "email": "alice@acme.com",
    "password": "SecurePass123!",
    "full_name": "Alice Smith"
  }'
```

### 2. Login via API
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice@acme.com",
    "password": "SecurePass123!"
  }'
```

Response:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 900
}
```

### 3. Use Token to Access Protected Endpoints
```bash
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <access_token>"
```

### 4. Or use Frontend
- Navigate to http://localhost:3000/login
- Enter your credentials
- Cookies are automatically set by the server
- No need to manage tokens manually

---

## Admin Roles Explained

DotMac Platform has **THREE types of admin users**:

### 1. 👤 **Tenant Admin** (Regular Admin)
**What it is**: Admin within a specific organization/tenant

**Database fields:**
- `tenant_id`: Set to their organization's tenant ID
- `roles`: Contains `"admin"` role (JSON array)
- `is_platform_admin`: `false`

**Permissions:**
- Full control **within their tenant only**
- Can manage users, billing, settings for their organization
- Cannot access other tenants' data
- Login via: http://localhost:3000/login (same as regular users)

**How to create:**
```bash
# Register normally, then assign admin role
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@acme.com",
    "password": "Admin123!@#",
    "full_name": "Tenant Admin"
  }'

# Then assign admin role via RBAC endpoints
# POST /api/v1/auth/rbac/users/{user_id}/roles
# Body: {"role_name": "admin"}
```

### 2. 🔧 **Superuser** (Tenant Superuser)
**What it is**: Enhanced privileges within a tenant

**Database fields:**
- `tenant_id`: Set to their organization's tenant ID
- `is_superuser`: `true`
- `is_platform_admin`: `false`

**Permissions:**
- Elevated permissions **within their tenant**
- May have additional capabilities beyond regular admin
- Still tenant-isolated (cannot access other tenants)
- Login via: http://localhost:3000/login

### 3. 🌐 **Platform Admin** (SaaS Administrator)
**What it is**: System administrator who manages the entire platform

**Database fields:**
- `tenant_id`: `null` (not bound to any tenant)
- `is_platform_admin`: `true`
- `is_superuser`: Usually `true`

**Permissions:**
- Can access **ALL tenants** (cross-tenant access)
- Can use `X-Target-Tenant-ID` header to impersonate any tenant
- Manages platform-wide settings, monitoring, infrastructure
- Login via: http://localhost:3000/login (same login page, special JWT)

**Use cases:**
- SaaS provider's support team
- Platform maintenance and monitoring
- Cross-tenant operations and analytics
- Tenant onboarding and offboarding

### Summary Table

| Admin Type | `tenant_id` | `is_platform_admin` | `is_superuser` | Access Scope | Login URL |
|------------|-------------|---------------------|----------------|--------------|-----------|
| **Tenant Admin** | Set | `false` | `false` | Single tenant only | `/login` |
| **Superuser** | Set | `false` | `true` | Single tenant (enhanced) | `/login` |
| **Platform Admin** | `null` | `true` | Usually `true` | All tenants | `/login` |

### Which One Do You Need?

- **Building a tenant application?** → Use **Tenant Admin** (admin role)
- **Testing tenant features?** → Use **Tenant Admin**
- **Managing the SaaS platform itself?** → Use **Platform Admin**
- **Need elevated tenant privileges?** → Use **Superuser**

---

## Summary

| Login Type | URL | Purpose | Users |
|------------|-----|---------|-------|
| **Main Platform** | http://localhost:3000/login | Tenant users | Customers, employees, admins |
| **Partner Portal** | http://localhost:3000/portal/login | Partners | Resellers, affiliates |
| **API Docs** | http://localhost:8000/docs | Test API | Developers |

**Quick Test:**
1. Go to http://localhost:3000/register
2. Create an account
3. Login at http://localhost:3000/login
4. Access dashboard and tenant-specific features

All authentication is secure with our implemented security fixes:
- ✅ Token type validation
- ✅ Safe JSON serialization
- ✅ Rate limiting
- ✅ Production-ready session management
