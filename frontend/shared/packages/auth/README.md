# @dotmac/auth

A production-ready, multi-variant authentication system for the DotMac Framework. Provides simple, secure, and enterprise-level authentication with consistent APIs across all portal types.

## Features

- **Multi-Variant Architecture**: Three authentication levels (simple, secure, enterprise)
- **Portal-Specific Configuration**: Tailored auth configs for each portal type
- **JWT Token Management**: Secure token storage and auto-refresh
- **Session Management**: Configurable timeouts and activity monitoring
- **Permission-Based Access Control**: Fine-grained authorization system
- **Account Security**: Login attempt tracking and account lockout
- **MFA Support**: Multi-factor authentication capabilities
- **Audit Logging**: Security event tracking (enterprise)
- **Device Fingerprinting**: Enhanced security for enterprise users
- **TypeScript**: Full type safety and excellent developer experience

## Installation

```bash
npm install @dotmac/auth
```

## Quick Start

### 1. Simple Authentication (Customer Portal)

````tsx
import { AuthProvider } from '@dotmac/auth';

function App() {
  return (
    <AuthProvider
      variant="simple"
      portal="customer"
      config={{
        sessionTimeout: 30 * 60 * 1000, // 30 minutes
        enableMFA: false,
        enablePermissions: false,
        endpoints: {
          login: '/api/customer/auth/login',
          logout: '/api/customer/auth/logout',
          refresh: '/api/customer/auth/refresh',
          profile: '/api/customer/auth/profile',
        }
      }}
    >
      <CustomerApp />
    </AuthProvider>
  );
}\n```\n\n### 2. Secure Authentication (Admin Portal)\n\n```tsx\nimport { AuthProvider } from '@dotmac/auth';\n\nfunction AdminApp() {\n  return (\n    <AuthProvider\n      variant=\"secure\"\n      portal=\"admin\"\n      config={{\n        sessionTimeout: 60 * 60 * 1000, // 1 hour\n        enableMFA: true,\n        enablePermissions: true,\n        requirePasswordComplexity: true,\n        maxLoginAttempts: 3,\n        lockoutDuration: 30 * 60 * 1000,\n        endpoints: {\n          login: '/api/admin/auth/login',\n          logout: '/api/admin/auth/logout',\n          refresh: '/api/admin/auth/refresh',\n          profile: '/api/admin/auth/profile',\n        }\n      }}\n    >\n      <AdminDashboard />\n    </AuthProvider>\n  );\n}\n```\n\n### 3. Enterprise Authentication (Management Portal)\n\n```tsx\nimport { AuthProvider } from '@dotmac/auth';\n\nfunction ManagementApp() {\n  return (\n    <AuthProvider\n      variant=\"enterprise\"\n      portal=\"management\"\n      config={{\n        sessionTimeout: 2 * 60 * 60 * 1000, // 2 hours\n        enableMFA: true,\n        enablePermissions: true,\n        enableAuditLog: true,\n        requirePasswordComplexity: true,\n        maxLoginAttempts: 3,\n        lockoutDuration: 60 * 60 * 1000,\n        endpoints: {\n          login: '/api/management/auth/login',\n          logout: '/api/management/auth/logout',\n          refresh: '/api/management/auth/refresh',\n          profile: '/api/management/auth/profile',\n        }\n      }}\n    >\n      <ManagementDashboard />\n    </AuthProvider>\n  );\n}\n```\n\n## Using Authentication\n\n### Basic Login\n\n```tsx\nimport { useAuth } from '@dotmac/auth';\n\nfunction LoginForm() {\n  const { login, isLoading, isAuthenticated, user } = useAuth();\n\n  const handleLogin = async (email: string, password: string) => {\n    try {\n      await login({\n        email,\n        password,\n        portal: 'admin',\n        rememberMe: true,\n      });\n    } catch (error) {\n      console.error('Login failed:', error);\n    }\n  };\n\n  if (isAuthenticated) {\n    return <div>Welcome, {user?.name}!</div>;\n  }\n\n  return (\n    <form onSubmit={(e) => {\n      e.preventDefault();\n      const formData = new FormData(e.target as HTMLFormElement);\n      handleLogin(\n        formData.get('email') as string,\n        formData.get('password') as string\n      );\n    }}>\n      <input name=\"email\" type=\"email\" placeholder=\"Email\" required />\n      <input name=\"password\" type=\"password\" placeholder=\"Password\" required />\n      <button type=\"submit\" disabled={isLoading}>\n        {isLoading ? 'Logging in...' : 'Login'}\n      </button>\n    </form>\n  );\n}\n```\n\n### Permission-Based Access Control\n\n```tsx\nimport { useAuth, Permission, UserRole } from '@dotmac/auth';\n\nfunction ProtectedComponent() {\n  const { hasPermission, hasRole, isSuperAdmin } = useAuth();\n\n  if (!hasPermission(Permission.USERS_READ)) {\n    return <div>Access denied. Missing required permissions.</div>;\n  }\n\n  return (\n    <div>\n      <h1>User Management</h1>\n      \n      {hasPermission(Permission.USERS_CREATE) && (\n        <button>Create User</button>\n      )}\n      \n      {hasRole([UserRole.SUPER_ADMIN, UserRole.MASTER_ADMIN]) && (\n        <button>Advanced Settings</button>\n      )}\n      \n      {isSuperAdmin() && (\n        <button>System Administration</button>\n      )}\n    </div>\n  );\n}\n```\n\n### Authenticated API Requests\n\n```tsx\nimport { useAuthenticatedApi } from '@dotmac/auth';\n\nfunction DataComponent() {\n  const api = useAuthenticatedApi();\n  const [data, setData] = React.useState([]);\n\n  React.useEffect(() => {\n    const fetchData = async () => {\n      try {\n        const result = await api.get('/api/users');\n        setData(result);\n      } catch (error) {\n        console.error('Failed to fetch data:', error);\n      }\n    };\n\n    if (api.isAuthenticated) {\n      fetchData();\n    }\n  }, [api]);\n\n  const createUser = async (userData: any) => {\n    try {\n      const newUser = await api.post('/api/users', userData);\n      setData(prev => [...prev, newUser]);\n    } catch (error) {\n      console.error('Failed to create user:', error);\n    }\n  };\n\n  return (\n    <div>\n      {/* Render data */}\n    </div>\n  );\n}\n```\n\n## API Reference\n\n### AuthProvider Props\n\n- `variant`: Authentication variant (`'simple'` | `'secure'` | `'enterprise'`)\n- `portal`: Portal type (`'admin'` | `'customer'` | `'reseller'` | `'technician'` | `'management'`)\n- `config`: Authentication configuration object\n\n### useAuth Hook\n\nReturns an object with:\n\n**State:**\n- `user`: Current user object or null\n- `isAuthenticated`: Boolean indicating authentication status\n- `isLoading`: Boolean indicating loading state\n- `isRefreshing`: Boolean indicating token refresh state\n\n**Actions:**\n- `login(credentials)`: Authenticate user\n- `logout()`: Sign out user\n- `refreshToken()`: Manually refresh authentication token\n- `updateProfile(updates)`: Update user profile\n\n**Authorization:**\n- `hasPermission(permission)`: Check if user has specific permission(s)\n- `hasRole(role)`: Check if user has specific role(s)\n- `isSuperAdmin()`: Check if user is a super admin\n\n**Session Management:**\n- `extendSession()`: Extend current session\n- `getSessionTimeRemaining()`: Get remaining session time in milliseconds\n\n**MFA (Secure/Enterprise variants):**\n- `setupMFA?()`: Setup multi-factor authentication\n- `verifyMFA?(code)`: Verify MFA code\n- `disableMFA?()`: Disable MFA for user\n\n### useAuthenticatedApi Hook\n\nReturns an object with:\n- `get(url, options?)`: GET request with authentication\n- `post(url, data?, options?)`: POST request with authentication\n- `put(url, data?, options?)`: PUT request with authentication\n- `patch(url, data?, options?)`: PATCH request with authentication\n- `delete(url, options?)`: DELETE request with authentication\n- `request(url, options)`: Generic request method\n- `isAuthenticated`: Current authentication status\n\n## Configuration\n\n### AuthConfig Interface\n\n```typescript\ninterface AuthConfig {\n  sessionTimeout: number;              // Session timeout in milliseconds\n  enableMFA: boolean;                  // Enable multi-factor authentication\n  enablePermissions: boolean;          // Enable permission-based access control\n  requirePasswordComplexity: boolean;  // Require complex passwords\n  maxLoginAttempts: number;           // Max failed login attempts before lockout\n  lockoutDuration: number;            // Account lockout duration in milliseconds\n  enableAuditLog: boolean;            // Enable security event logging\n  tokenRefreshThreshold: number;      // Token refresh threshold in milliseconds\n  endpoints: {\n    login: string;                    // Login endpoint URL\n    logout: string;                   // Logout endpoint URL\n    refresh: string;                  // Token refresh endpoint URL\n    profile: string;                  // User profile endpoint URL\n  };\n}\n```\n\n### Portal-Specific Defaults\n\nEach portal type has sensible defaults:\n\n- **Customer**: Simple auth, no MFA, 15-minute sessions\n- **Admin**: Secure auth, MFA enabled, 1-hour sessions\n- **Reseller**: Secure auth, MFA enabled, 45-minute sessions\n- **Technician**: Simple auth, no MFA, 8-hour sessions (for field work)\n- **Management**: Enterprise auth, full security features, 2-hour sessions\n\n## Authentication Variants\n\n### Simple\n- Basic token storage in localStorage\n- Simple session management\n- Minimal security features\n- Best for: Customer portals, low-security applications\n\n### Secure\n- Enhanced token management with auto-refresh\n- Session timeout and activity monitoring\n- Account lockout protection\n- MFA support\n- Best for: Admin portals, business applications\n\n### Enterprise\n- All secure features plus:\n- Device fingerprinting\n- Advanced audit logging\n- Activity monitoring\n- Enhanced security events\n- Best for: Management portals, high-security environments\n\n## Security Features\n\n- **Token Security**: Secure storage with automatic refresh\n- **Session Management**: Configurable timeouts with activity detection\n- **Account Protection**: Failed attempt tracking with lockout\n- **Permission System**: Role and permission-based access control\n- **Audit Trail**: Comprehensive security event logging (enterprise)\n- **Device Trust**: Device fingerprinting for enhanced security\n- **CSRF Protection**: Built-in CSRF token handling\n\n## TypeScript Support\n\nFull TypeScript support with comprehensive type definitions:\n\n```typescript\nimport type {\n  User,\n  UserRole,\n  Permission,\n  AuthConfig,\n  LoginCredentials,\n  AuthContextValue\n} from '@dotmac/auth';\n```\n\n## License\n\nMIT"
}
````
