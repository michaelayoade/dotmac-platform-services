import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Routes that don't require authentication
const publicRoutes = ['/login', '/register', '/forgot-password', '/reset-password', '/'];
const apiRoutes = ['/api/auth/login', '/api/auth/register', '/api/auth/refresh'];

export function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname;

  // Skip middleware for public routes and API auth endpoints
  if (publicRoutes.includes(pathname) || apiRoutes.some(route => pathname.startsWith(route))) {
    return NextResponse.next();
  }

  // Skip middleware for static files and API routes
  if (
    pathname.startsWith('/_next') ||
    pathname.startsWith('/static') ||
    pathname.includes('.') ||
    pathname.startsWith('/api/health')
  ) {
    return NextResponse.next();
  }

  // Check for auth token in cookies
  const token = request.cookies.get('access_token');
  const refreshToken = request.cookies.get('refresh_token');

  // Handle API routes
  if (pathname.startsWith('/api/')) {
    if (!token) {
      return NextResponse.json(
        { error: 'Unauthorized', message: 'No valid authentication token' },
        { status: 401 }
      );
    }

    // Add token to headers for API routes
    const requestHeaders = new Headers(request.headers);
    requestHeaders.set('Authorization', `Bearer ${token.value}`);

    return NextResponse.next({
      request: {
        headers: requestHeaders,
      },
    });
  }

  // Handle protected routes
  if (!token && !refreshToken) {
    const url = request.nextUrl.clone();
    url.pathname = '/login';
    url.searchParams.set('from', pathname);
    return NextResponse.redirect(url);
  }

  // Token exists but might be expired - let client handle refresh
  if (!token && refreshToken) {
    // Set flag for client to attempt refresh
    const response = NextResponse.next();
    response.headers.set('X-Token-Refresh-Required', 'true');
    return response;
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    '/((?!_next/static|_next/image|favicon.ico|public).*)',
  ],
};