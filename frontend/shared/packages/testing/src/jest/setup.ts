/**
 * Jest Setup for DotMac Testing Framework
 *
 * Configures Jest with testing utilities, matchers, and global setup
 */

// Import Jest DOM matchers
import '@testing-library/jest-dom';

// Import axe matchers
import { toHaveNoViolations } from 'jest-axe';

// Import custom matchers
import '../utils/matchers';

// Extend Jest expect with axe matchers
if (typeof expect !== 'undefined') {
  expect.extend(toHaveNoViolations);
}

// Global test configuration
const TEST_CONFIG = {
  enableA11yTesting: true,
  enableSecurityTesting: true,
  enablePerformanceTesting: false,
  mockApis: true,
  logSecurityEvents: false,
};

// Mock IntersectionObserver for components that use it
if (typeof global !== 'undefined') {
  (global as any).IntersectionObserver = class IntersectionObserver {
    constructor() {}
    disconnect() {}
    observe() {}
    unobserve() {}
  };

  // Mock ResizeObserver for components that use it
  (global as any).ResizeObserver = class ResizeObserver {
    constructor() {}
    disconnect() {}
    observe() {}
    unobserve() {}
  };

  // Mock window.performance for performance testing
  if (typeof (global as any).performance === 'undefined') {
    (global as any).performance = {
      now: jest.fn(() => Date.now()),
      mark: jest.fn(),
      measure: jest.fn(),
      clearMarks: jest.fn(),
      clearMeasures: jest.fn(),
      getEntriesByName: jest.fn(() => []),
      getEntriesByType: jest.fn(() => []),
    };
  }

  // Mock crypto for security testing
  if (typeof (global as any).crypto === 'undefined') {
    (global as any).crypto = {
      randomUUID: jest.fn(() => 'test-uuid'),
      getRandomValues: jest.fn((arr: any[]) => {
        for (let i = 0; i < arr.length; i++) {
          arr[i] = Math.floor(Math.random() * 256);
        }
        return arr;
      }),
    };
  }
}

// Mock DOM APIs if running in Node.js
if (typeof window !== 'undefined') {
  // Mock matchMedia for responsive components
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: jest.fn().mockImplementation((query) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: jest.fn(), // deprecated
      removeListener: jest.fn(), // deprecated
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      dispatchEvent: jest.fn(),
    })),
  });

  // Mock localStorage for storage testing
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
}

// Global test helpers
const testUtils = {
  // Helper to wait for async operations
  waitForAsync: async (callback: () => Promise<any>, timeout = 5000) => {
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => reject(new Error('Async operation timed out')), timeout);

      callback()
        .then((result) => {
          clearTimeout(timer);
          resolve(result);
        })
        .catch((error) => {
          clearTimeout(timer);
          reject(error);
        });
    });
  },

  // Helper to mock component props
  createMockProps: (overrides: any = {}) => ({
    'data-testid': 'test-component',
    ...overrides,
  }),

  // Helper to create mock event handlers
  createMockHandlers: () => ({
    onClick: jest.fn(),
    onChange: jest.fn(),
    onSubmit: jest.fn(),
    onFocus: jest.fn(),
    onBlur: jest.fn(),
  }),
};

// Accessibility testing helpers
const a11yUtils = {
  // Check if element has proper labeling
  hasProperLabeling: (element: Element) => {
    return (
      element.hasAttribute('aria-label') ||
      element.hasAttribute('aria-labelledby') ||
      element.querySelector('label') !== null
    );
  },

  // Check if interactive element is keyboard accessible
  isKeyboardAccessible: (element: Element) => {
    return (
      element.hasAttribute('tabindex') ||
      ['button', 'a', 'input', 'select', 'textarea'].includes(element.tagName.toLowerCase())
    );
  },
};

// Security testing helpers
const securityUtils = {
  // Check for dangerous patterns
  hasDangerousPatterns: (html: string) => {
    return /(<script|javascript:|on\w+\s*=|data:)/gi.test(html);
  },

  // Sanitize test input
  sanitizeInput: (input: string) => {
    return input
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#x27;');
  },
};

// Performance testing helpers
const perfUtils = {
  measureRenderTime: async (renderFunction: () => Promise<void>) => {
    const start = performance.now();
    await renderFunction();
    const end = performance.now();
    return end - start;
  },

  measureMemoryUsage: () => {
    if (typeof performance !== 'undefined' && 'memory' in performance) {
      return (performance as any).memory.usedJSHeapSize;
    }
    return 0;
  },
};

// Setup test environment
if (typeof beforeEach !== 'undefined') {
  beforeEach(() => {
    // Clear all mocks before each test
    jest.clearAllMocks();
    // Reset console spies
    jest.clearAllTimers();
  });
}

if (typeof afterEach !== 'undefined') {
  afterEach(() => {
    // Clean up after each test
    if (typeof document !== 'undefined') {
      document.body.innerHTML = '';
    }
  });
}

// Global error handler for unhandled promise rejections
if (typeof process !== 'undefined') {
  process.on('unhandledRejection', (reason, promise) => {
    console.error('Unhandled Rejection at:', promise, 'reason:', reason);
  });
}

// Export configuration for use in tests
export const testConfig = TEST_CONFIG;
export { testUtils, a11yUtils, securityUtils, perfUtils };
