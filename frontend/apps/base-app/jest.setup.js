// Learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom'

// Mock next/router
jest.mock('next/router', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
    back: jest.fn(),
    pathname: '/',
    query: {},
    asPath: '/',
  }),
}))

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
    back: jest.fn(),
    forward: jest.fn(),
    refresh: jest.fn(),
  }),
  usePathname: () => '/',
  useSearchParams: () => new URLSearchParams(),
}))

// Mock useToast hook (migration from sonner)
jest.mock('@/components/ui/use-toast', () => ({
  useToast: () => ({
    toast: jest.fn(),
    dismiss: jest.fn(),
    toasts: [],
  }),
}))

// Set up global test environment
global.fetch = jest.fn()

// Add Request and Response polyfills for Next.js API routes
global.Request = class Request {
  constructor(input, init) {
    this.url = input;
    this.method = (init && init.method) || 'GET';
    this.headers = new Map(Object.entries((init && init.headers) || {}));
    this.cookies = {
      get: jest.fn(),
      getAll: jest.fn(() => [])
    };
  }
}

global.Response = class Response {
  constructor(body, init) {
    this.body = body;
    this.status = (init && init.status) || 200;
    this.headers = new Map(Object.entries((init && init.headers) || {}));
  }

  json() {
    return Promise.resolve(JSON.parse(this.body));
  }

  static json(data, init) {
    return new Response(JSON.stringify(data), {
      ...init,
      headers: { 'content-type': 'application/json', ...(init && init.headers) }
    });
  }
}