# Frontend Authentication Security Guide

## Issues Fixed

### 1. ✅ API Base URL Double `/api` Issue

**Problem:** `platformConfig.apiBaseUrl` defaulted to `http://localhost:8000/api`, while apiClient appended endpoints like `/api/v1/auth/login`, producing `http://localhost:8000/api/api/v1/...`

**Solution:** Changed `platformConfig.apiBaseUrl` to `http://localhost:8000` (host only)

```typescript
// Before (BROKEN)
apiBaseUrl: 'http://localhost:8000/api'
// Resulted in: http://localhost:8000/api/api/v1/auth/login

// After (FIXED)
apiBaseUrl: 'http://localhost:8000'
// Results in: http://localhost:8000/api/v1/auth/login
```

### 2. ✅ Config Loader TypeScript Compilation Issue

**Problem:** config-loader imported non-existent `config` export and referenced `staticConfig.api.baseURL`

**Solution:** Updated to use `platformConfig`

```typescript
// Before (BROKEN)
import { config as staticConfig } from './config';
const response = await fetch(`${staticConfig.api.baseURL}/api/v1/config/public`

// After (FIXED)
import { platformConfig } from './config';
const response = await fetch(`${platformConfig.apiBaseUrl}/api/v1/config/public`
```

### 3. ⚠️ Cookie Security Consideration

**Current State:** Client-managed cookies (not truly HttpOnly)

**Security Implications:**
- ✅ **SameSite=Strict**: Prevents CSRF attacks
- ✅ **Secure flag**: Only sent over HTTPS in production
- ❌ **HttpOnly limitation**: Cannot be set client-side, tokens readable by JavaScript

## Current Authentication Flow

```typescript
// Login sets client-side cookies
async login(username: string, password: string) {
  const response = await this.post('/api/v1/auth/login', { username, password });

  if (response.success && response.data) {
    // Client sets cookies (NOT HttpOnly)
    this.setTokenCookies(response.data.access_token, response.data.refresh_token);
  }
}

// Cookies are readable by JavaScript
private getAccessToken(): string | null {
  const match = document.cookie.match(/access_token=([^;]+)/);
  return match ? match[1] : null;
}
```

## Security Options

### Option 1: Current Approach (Client-Managed Cookies)
**Pros:**
- Simple implementation
- Works with any backend
- Easy token refresh handling

**Cons:**
- Tokens readable by JavaScript (XSS vulnerability)
- Not truly HttpOnly

### Option 2: Server-Managed HttpOnly Cookies (Recommended)
**Implementation needed:**
- Backend sets `Set-Cookie` headers with `HttpOnly` flag
- Frontend relies on automatic cookie inclusion
- More secure against XSS attacks

```typescript
// Backend would set cookies like:
Set-Cookie: access_token=xyz123; HttpOnly; Secure; SameSite=Strict; Max-Age=900
Set-Cookie: refresh_token=abc456; HttpOnly; Secure; SameSite=Strict; Max-Age=604800
```

### Option 3: Hybrid Approach
- Access token in memory (not stored in cookies)
- Refresh token as HttpOnly cookie set by server
- More complex but most secure

## Recommended Next Steps

1. **Short-term:** Current implementation is functional and reasonably secure with:
   - SameSite=Strict (CSRF protection)
   - Secure flag in production (HTTPS only)
   - Automatic token refresh

2. **Long-term:** Consider migrating to server-managed HttpOnly cookies:
   ```typescript
   // Update login method to check for server-set cookies
   if (response.success) {
     // Check if server already set HttpOnly cookies
     // If not, fall back to client-side cookies
     if (!this.checkServerSetCookies()) {
       this.setTokenCookies(response.data.access_token, response.data.refresh_token);
     }
   }
   ```

3. **Testing:** The provided test suite validates correct URL formation and login flow

## Environment Variables

```bash
# Correct base URL (host only, no /api suffix)
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# In production
NEXT_PUBLIC_API_BASE_URL=https://api.yourdomain.com
```

## Security Best Practices Applied

✅ **HTTPS in production** (Secure flag)
✅ **SameSite=Strict** (CSRF protection)
✅ **Automatic token refresh** (UX + security)
✅ **Credentials: include** (cookie handling)
✅ **401 handling with redirect** (auth flow)
⚠️ **HttpOnly tokens** (requires server-side implementation)

The current implementation provides good security for most use cases. HttpOnly cookies would be the next security improvement if XSS protection is critical.