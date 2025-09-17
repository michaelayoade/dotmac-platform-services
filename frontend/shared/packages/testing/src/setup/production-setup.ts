/**
 * Production Test Setup
 * High-performance test environment with security focus
 * Leverages unified architecture patterns
 */

import '@testing-library/jest-dom';
import { configure } from '@testing-library/react';
import {
  testOptimizer,
  performanceTestHelpers,
  type TestPerformanceMetrics,
} from '../performance/test-performance-optimizer';

// Configure Testing Library for performance
configure({
  testIdAttribute: 'data-testid',
  computedStyleSupportsPseudoElements: false, // Performance optimization
  asyncUtilTimeout: 5000, // Shorter timeout for fast tests
  defaultHidden: false, // Skip hidden element checks for speed
});

// Performance monitoring setup
let testStartTime: number;
let testSuiteName: string;

// Global test hooks for performance tracking
beforeAll(() => {
  testStartTime = performance.now();
  testSuiteName = expect.getState().testPath?.split('/').pop() || 'unknown';

  console.log(`🚀 Starting ${testSuiteName} with performance monitoring`);

  // Setup performance monitoring
  testOptimizer.checkMemoryUsage();

  // Mock console methods for cleaner output in CI
  if (process.env.CI) {
    const originalWarn = console.warn;
    console.warn = (...args) => {
      // Only show performance and security warnings
      if (args[0]?.includes('⚠️') || args[0]?.includes('🔒')) {
        originalWarn(...args);
      }
    };
  }
});

afterAll(() => {
  const testEndTime = performance.now();
  const totalTime = testEndTime - testStartTime;

  const report = testOptimizer.generateReport();
  const recommendations = testOptimizer.getOptimizationRecommendations();

  console.log(`✅ ${testSuiteName} completed in ${Math.round(totalTime)}ms`);
  console.log(`📊 Cache hit ratio: ${report.cacheHitRatio.toFixed(1)}%`);

  // Performance budget enforcement
  if (totalTime > 30000) {
    console.error(`❌ Test suite exceeded 30s budget: ${Math.round(totalTime)}ms`);

    if (process.env.CI) {
      process.exit(1);
    }
  }

  // Memory cleanup
  testOptimizer.clearCaches();

  if (global.gc) {
    global.gc();
  }
});

beforeEach(() => {
  const testName = expect.getState().currentTestName || 'unknown-test';
  testOptimizer.startTest(testName);

  // Reset DOM for clean tests
  document.body.innerHTML = '';
  document.head.innerHTML = '';

  // Reset viewport for consistent testing
  Object.defineProperty(window, 'innerWidth', { value: 1024, writable: true });
  Object.defineProperty(window, 'innerHeight', { value: 768, writable: true });
});

afterEach(() => {
  const testName = expect.getState().currentTestName || 'unknown-test';
  const duration = testOptimizer.endTest(testName);

  // Clean up any remaining timers/intervals
  jest.clearAllTimers();
  jest.clearAllMocks();

  // Memory check after slow tests
  if (duration > 2000) {
    testOptimizer.checkMemoryUsage();
  }
});

// Mock implementations for unified architecture
const mockIntersectionObserver = jest.fn();
mockIntersectionObserver.mockReturnValue({
  observe: () => null,
  unobserve: () => null,
  disconnect: () => null,
});
window.IntersectionObserver = mockIntersectionObserver;

// Mock ResizeObserver for responsive components
const mockResizeObserver = jest.fn();
mockResizeObserver.mockReturnValue({
  observe: () => null,
  unobserve: () => null,
  disconnect: () => null,
});
window.ResizeObserver = mockResizeObserver;

// Mock matchMedia for responsive testing
const mockMatchMedia = (query: string) => ({
  matches: false,
  media: query,
  onchange: null,
  addListener: jest.fn(), // deprecated
  removeListener: jest.fn(), // deprecated
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  dispatchEvent: jest.fn(),
});
window.matchMedia = mockMatchMedia;

// Mock fetch for API testing
const mockFetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    status: 200,
    statusText: 'OK',
    json: () => Promise.resolve({}),
    text: () => Promise.resolve(''),
    blob: () => Promise.resolve(new Blob()),
    arrayBuffer: () => Promise.resolve(new ArrayBuffer(0)),
    headers: new Headers(),
    redirected: false,
    type: 'default' as ResponseType,
    url: '',
    clone: jest.fn(),
    body: null,
    bodyUsed: false,
  })
);
global.fetch = mockFetch;

// Mock localStorage for persistent state testing
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
  length: 0,
  key: jest.fn(),
};
Object.defineProperty(window, 'localStorage', { value: localStorageMock });

// Mock sessionStorage
const sessionStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
  length: 0,
  key: jest.fn(),
};
Object.defineProperty(window, 'sessionStorage', { value: sessionStorageMock });

// Mock crypto for security testing
const mockCrypto = {
  randomUUID: () => '123e4567-e89b-12d3-a456-426614174000',
  getRandomValues: (array: Uint8Array) => {
    for (let i = 0; i < array.length; i++) {
      array[i] = Math.floor(Math.random() * 256);
    }
    return array;
  },
  subtle: {
    encrypt: jest.fn(),
    decrypt: jest.fn(),
    sign: jest.fn(),
    verify: jest.fn(),
    digest: jest.fn(),
    generateKey: jest.fn(),
    deriveKey: jest.fn(),
    deriveBits: jest.fn(),
    importKey: jest.fn(),
    exportKey: jest.fn(),
    wrapKey: jest.fn(),
    unwrapKey: jest.fn(),
  },
};
Object.defineProperty(window, 'crypto', { value: mockCrypto });

// Mock clipboard for copy/paste functionality
const mockClipboard = {
  writeText: jest.fn().mockResolvedValue(undefined),
  readText: jest.fn().mockResolvedValue('mocked text'),
  write: jest.fn().mockResolvedValue(undefined),
  read: jest.fn().mockResolvedValue([]),
};
Object.defineProperty(navigator, 'clipboard', { value: mockClipboard });

// Mock geolocation for location-based features
const mockGeolocation = {
  getCurrentPosition: jest.fn(),
  watchPosition: jest.fn(),
  clearWatch: jest.fn(),
};
Object.defineProperty(navigator, 'geolocation', { value: mockGeolocation });

// Mock notification API
const mockNotification = jest.fn();
mockNotification.requestPermission = jest.fn().mockResolvedValue('granted');
mockNotification.permission = 'granted';
window.Notification = mockNotification;

// Mock performance API enhancements
Object.defineProperty(window.performance, 'mark', {
  value: jest.fn(),
  writable: true,
});

Object.defineProperty(window.performance, 'measure', {
  value: jest.fn(),
  writable: true,
});

// Enhanced error handling for security tests
const originalConsoleError = console.error;
console.error = (...args) => {
  // Capture security-related errors
  const message = args[0]?.toString() || '';
  if (message.includes('security') || message.includes('auth') || message.includes('csrf')) {
    // Store security errors for analysis
    if (!(global as any).__securityErrors) {
      (global as any).__securityErrors = [];
    }
    (global as any).__securityErrors.push(args);
  }

  // Call original for actual error logging
  originalConsoleError(...args);
};

// Global test utilities available in all tests
(global as any).testUtils = {
  mockFetch,
  localStorageMock,
  sessionStorageMock,
  mockCrypto,
  mockClipboard,
  mockGeolocation,
  createMockUser: () => ({
    id: '123',
    email: 'test@example.com',
    roles: ['user'],
    permissions: ['read'],
  }),
  createMockTenant: () => ({
    id: 'tenant-123',
    name: 'Test Tenant',
    domain: 'test.example.com',
  }),
  // Performance testing utilities
  waitForPerformanceBudget: async (budget: number) => {
    const start = performance.now();
    return new Promise<void>((resolve, reject) => {
      const check = () => {
        const elapsed = performance.now() - start;
        if (elapsed > budget) {
          reject(new Error(`Performance budget exceeded: ${elapsed}ms > ${budget}ms`));
        } else {
          resolve();
        }
      };
      setTimeout(check, 0);
    });
  },
};

// Export for external use
export { testOptimizer, performanceHooks };
