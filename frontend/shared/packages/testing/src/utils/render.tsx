/**
 * Enhanced Testing Render Utilities
 *
 * Provides enhanced rendering utilities with built-in accessibility testing,
 * security validation, and performance monitoring
 */

import React from 'react';
import { render as rtlRender } from '@testing-library/react';
import type { RenderOptions, RenderResult } from '@testing-library/react';
import { axe } from 'jest-axe';
import userEvent from '@testing-library/user-event';

// Extend Jest matchers
if (typeof expect !== 'undefined' && typeof expect.extend === 'function') {
  // Note: toHaveNoViolations should be imported from jest-axe setup
}

// Test providers and wrappers
interface TestProvidersProps {
  children?: React.ReactNode;
  theme?: 'light' | 'dark';
  portal?: 'admin' | 'customer' | 'reseller';
  mockApis?: boolean;
}

function TestProviders({
  children,
  theme = 'light',
  portal = 'admin',
  mockApis = true,
}: TestProvidersProps) {
  return (
    <div data-theme={theme} data-portal={portal} data-testid='test-wrapper'>
      {children}
    </div>
  );
}

// Enhanced render options
export interface EnhancedRenderOptions extends RenderOptions {
  // Theme and portal context
  theme?: 'light' | 'dark';
  portal?: 'admin' | 'customer' | 'reseller';

  // Testing features
  enableA11yTesting?: boolean;
  enableSecurityTesting?: boolean;
  enablePerformanceTesting?: boolean;
  mockApis?: boolean;

  // User event setup
  setupUserEvent?: boolean;
  userEventOptions?: Parameters<typeof userEvent.setup>[0];
}

// Enhanced render result
export interface EnhancedRenderResult extends RenderResult {
  user: ReturnType<typeof userEvent.setup>;
  checkAccessibility: () => Promise<void>;
  checkSecurityViolations: () => Promise<void>;
  measurePerformance: () => PerformanceMetrics;
}

export interface PerformanceMetrics {
  renderTime: number;
  domNodes: number;
  memoryUsage?: number;
}

/**
 * Enhanced render function with built-in testing utilities
 */
export function render(
  component: React.ReactElement,
  options: EnhancedRenderOptions = {}
): EnhancedRenderResult {
  const {
    theme = 'light',
    portal = 'admin',
    enableA11yTesting = true,
    enableSecurityTesting = true,
    enablePerformanceTesting = false,
    mockApis = true,
    setupUserEvent = true,
    userEventOptions,
    wrapper,
    ...renderOptions
  } = options;

  // Performance tracking
  const startTime = performance.now();

  // Create wrapper with providers
  const AllProviders = ({ children }: { children: React.ReactNode }) => {
    const content = (
      <TestProviders theme={theme} portal={portal} mockApis={mockApis}>
        {children}
      </TestProviders>
    );

    return wrapper ? React.createElement(wrapper, { children: content }) : content;
  };

  // Render component
  const result = rtlRender(component, {
    wrapper: AllProviders,
    ...renderOptions,
  });

  const renderTime = performance.now() - startTime;

  // Set up user event
  const user = setupUserEvent
    ? userEvent.setup(userEventOptions)
    : ({} as ReturnType<typeof userEvent.setup>);

  // Accessibility testing function
  const checkAccessibility = async (): Promise<void> => {
    if (!enableA11yTesting) return;

    const results = await axe(result.container);
    expect(results).toHaveNoViolations();
  };

  // Security testing function
  const checkSecurityViolations = async (): Promise<void> => {
    if (!enableSecurityTesting) return;

    const container = result.container;

    // Check for dangerous patterns
    const scriptTags = container.querySelectorAll('script');
    expect(scriptTags).toHaveLength(0);

    // Check for event handlers in HTML
    const elementsWithEventHandlers = container.querySelectorAll('[onclick], [onload], [onerror]');
    expect(elementsWithEventHandlers).toHaveLength(0);

    // Check for javascript: URLs
    const dangerousLinks = container.querySelectorAll(
      'a[href*="javascript:"], [src*="javascript:"]'
    );
    expect(dangerousLinks).toHaveLength(0);

    // Check for data URLs (potential security risk)
    const dataUrls = container.querySelectorAll('[src*="data:"], [href*="data:"]');
    if (dataUrls.length > 0) {
      console.warn('Data URLs detected - verify they are safe:', dataUrls);
    }
  };

  // Performance measurement function
  const measurePerformance = (): PerformanceMetrics => {
    if (!enablePerformanceTesting) {
      return { renderTime, domNodes: 0 };
    }

    const domNodes = result.container.querySelectorAll('*').length;
    const metrics: PerformanceMetrics = {
      renderTime,
      domNodes,
    };

    // Memory usage (if available)
    if ('memory' in performance) {
      metrics.memoryUsage = (performance as any).memory.usedJSHeapSize;
    }

    return metrics;
  };

  return {
    ...result,
    user,
    checkAccessibility,
    checkSecurityViolations,
    measurePerformance,
  };
}

/**
 * Render component for accessibility testing only
 */
export async function renderA11y(
  component: React.ReactElement,
  options: EnhancedRenderOptions = {}
): Promise<EnhancedRenderResult> {
  const result = render(component, {
    ...options,
    enableA11yTesting: true,
    enableSecurityTesting: false,
    enablePerformanceTesting: false,
  });

  await result.checkAccessibility();
  return result;
}

/**
 * Render component for security testing only
 */
export async function renderSecurity(
  component: React.ReactElement,
  options: EnhancedRenderOptions = {}
): Promise<EnhancedRenderResult> {
  const result = render(component, {
    ...options,
    enableA11yTesting: false,
    enableSecurityTesting: true,
    enablePerformanceTesting: false,
  });

  await result.checkSecurityViolations();
  return result;
}

/**
 * Render component for performance testing
 */
export function renderPerformance(
  component: React.ReactElement,
  options: EnhancedRenderOptions = {}
): EnhancedRenderResult {
  return render(component, {
    ...options,
    enableA11yTesting: false,
    enableSecurityTesting: false,
    enablePerformanceTesting: true,
  });
}

/**
 * Comprehensive render with all tests
 */
export async function renderComprehensive(
  component: React.ReactElement,
  options: EnhancedRenderOptions = {}
): Promise<{ result: EnhancedRenderResult; metrics: PerformanceMetrics }> {
  const result = render(component, {
    ...options,
    enableA11yTesting: true,
    enableSecurityTesting: true,
    enablePerformanceTesting: true,
  });

  // Run all checks
  await result.checkAccessibility();
  await result.checkSecurityViolations();
  const metrics = result.measurePerformance();

  return { result, metrics };
}

// Re-export testing library utilities
export * from '@testing-library/react';
export { userEvent };
export { axe } from 'jest-axe';

// Custom queries and utilities
export const queries = {
  getByTestId: (container: HTMLElement, testId: string) =>
    container.querySelector(`[data-testid="${testId}"]`),

  getAllByTestId: (container: HTMLElement, testId: string) =>
    Array.from(container.querySelectorAll(`[data-testid="${testId}"]`)),

  getByRole: (container: HTMLElement, role: string, options?: { name?: string }) => {
    if (options?.name) {
      return container.querySelector(
        `[role="${role}"][aria-label*="${options.name}"], [role="${role}"][aria-labelledby*="${options.name}"]`
      );
    }
    return container.querySelector(`[role="${role}"]`);
  },
};
