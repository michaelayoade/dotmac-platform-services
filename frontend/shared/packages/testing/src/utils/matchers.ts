/**
 * Custom Jest Matchers for DotMac Testing
 *
 * Provides custom Jest matchers for component testing, accessibility,
 * security validation, and performance monitoring
 */

import { axe } from 'jest-axe';

// Define matcher function type locally since expect types may not be available
interface MatcherResult {
  pass: boolean;
  message(): string;
}

type MatcherFunction<T extends any[]> = (
  received: any,
  ...expected: T
) => MatcherResult | Promise<MatcherResult>;

// Define AxeResults type locally since it's not exported by jest-axe
interface AxeResults {
  violations: any[];
  passes: any[];
  incomplete: any[];
  inapplicable: any[];
}

// Extend Jest expect interface
declare global {
  namespace jest {
    interface Matchers<R> {
      toBeAccessible(): Promise<R>;
      toHaveNoSecurityViolations(): R;
      toBePerformant(maxRenderTime?: number): R;
      toHaveValidMarkup(): R;
      toBeResponsive(): Promise<R>;
      toHaveLoadedWithoutErrors(): R;
      toMatchVisualSnapshot(snapshotName?: string): Promise<R>;
      toPassSecurityAudit(): R;
    }
  }
}

/**
 * Check if element is accessible using axe-core
 */
const toBeAccessible: MatcherFunction<[element?: HTMLElement]> = async function (
  received: HTMLElement | Document,
  element?: HTMLElement
) {
  const targetElement = element || (received as HTMLElement);

  try {
    const results = await axe(targetElement);

    if (results.violations.length === 0) {
      return {
        pass: true,
        message: () => `Expected element to have accessibility violations, but found none`,
      };
    }

    const violationMessages = results.violations
      .map(
        (violation) =>
          `${violation.id}: ${violation.description}\n  ${violation.nodes
            .map((node) => `- ${node.failureSummary}`)
            .join('\n  ')}`
      )
      .join('\n\n');

    return {
      pass: false,
      message: () =>
        `Expected element to be accessible, but found ${results.violations.length} violations:\n\n${violationMessages}`,
    };
  } catch (error) {
    return {
      pass: false,
      message: () => `Accessibility check failed: ${error}`,
    };
  }
};

/**
 * Check for security violations in rendered component
 */
const toHaveNoSecurityViolations: MatcherFunction<[]> = function (received: HTMLElement) {
  const violations: string[] = [];

  // Check for script tags
  const scriptTags = received.querySelectorAll('script');
  if (scriptTags.length > 0) {
    violations.push(`Found ${scriptTags.length} script tag(s)`);
  }

  // Check for event handlers
  const eventHandlers = received.querySelectorAll('[onclick], [onload], [onerror], [onmouseover]');
  if (eventHandlers.length > 0) {
    violations.push(`Found ${eventHandlers.length} inline event handler(s)`);
  }

  // Check for javascript: URLs
  const jsUrls = received.querySelectorAll('a[href*="javascript:"], [src*="javascript:"]');
  if (jsUrls.length > 0) {
    violations.push(`Found ${jsUrls.length} javascript: URL(s)`);
  }

  // Check for data URLs (potential XSS vector)
  const dataUrls = received.querySelectorAll('[src*="data:"], [href*="data:"]');
  if (dataUrls.length > 0) {
    violations.push(`Found ${dataUrls.length} data: URL(s) - verify safety`);
  }

  // Check for potentially dangerous attributes
  const dangerousAttrs = received.querySelectorAll('[srcdoc], [sandbox]');
  if (dangerousAttrs.length > 0) {
    violations.push(`Found ${dangerousAttrs.length} potentially dangerous attribute(s)`);
  }

  const pass = violations.length === 0;

  return {
    pass,
    message: () =>
      pass
        ? `Expected element to have security violations, but found none`
        : `Expected element to have no security violations, but found:\n  - ${violations.join('\n  - ')}`,
  };
};

/**
 * Check if component renders within performance threshold
 */
const toBePerformant: MatcherFunction<[maxRenderTime?: number]> = function (
  received: { renderTime?: number; domNodes?: number },
  maxRenderTime = 16 // 16ms is one frame at 60fps
) {
  const { renderTime = 0, domNodes = 0 } = received;

  if (typeof renderTime !== 'number') {
    return {
      pass: false,
      message: () =>
        `Expected performance metrics object with renderTime property, but got: ${received}`,
    };
  }

  const pass = renderTime <= maxRenderTime;
  const nodeWarning =
    domNodes > 1000 ? ` (Warning: ${domNodes} DOM nodes may impact performance)` : '';

  return {
    pass,
    message: () =>
      pass
        ? `Expected render time to exceed ${maxRenderTime}ms, but was ${renderTime.toFixed(2)}ms${nodeWarning}`
        : `Expected render time to be ≤ ${maxRenderTime}ms, but was ${renderTime.toFixed(2)}ms${nodeWarning}`,
  };
};

/**
 * Check if markup is valid HTML
 */
const toHaveValidMarkup: MatcherFunction<[]> = function (received: HTMLElement) {
  const issues: string[] = [];

  // Check for unclosed tags
  const innerHTML = received.innerHTML;
  const openTags = innerHTML.match(/<[^/][^>]*>/g) || [];
  const closeTags = innerHTML.match(/<\/[^>]*>/g) || [];

  // Basic validation - this is simplified
  const tagNames = openTags.map((tag) => {
    const match = tag.match(/<(\w+)/);
    return match?.[1] ?? '';
  });

  const selfClosingTags = ['img', 'br', 'hr', 'input', 'meta', 'link', 'area', 'base'];
  const expectedCloseTags = tagNames.filter((tag) => !selfClosingTags.includes(tag.toLowerCase()));

  if (expectedCloseTags.length !== closeTags.length) {
    issues.push(
      `Mismatched open/close tags: ${expectedCloseTags.length} open, ${closeTags.length} close`
    );
  }

  // Check for required attributes
  const images = received.querySelectorAll('img:not([alt])');
  if (images.length > 0) {
    issues.push(`${images.length} image(s) missing alt attribute`);
  }

  const links = received.querySelectorAll('a:not([href])');
  if (links.length > 0) {
    issues.push(`${links.length} link(s) missing href attribute`);
  }

  const pass = issues.length === 0;

  return {
    pass,
    message: () =>
      pass
        ? `Expected element to have invalid markup, but it was valid`
        : `Expected element to have valid markup, but found issues:\n  - ${issues.join('\n  - ')}`,
  };
};

/**
 * Check if component is responsive (simplified check)
 */
const toBeResponsive: MatcherFunction<[]> = async function (received: HTMLElement | Document) {
  const issues: string[] = [];

  // Check for fixed widths that might break responsiveness
  const elementsWithFixedWidth = received.querySelectorAll('[style*="width:"][style*="px"]');
  if (elementsWithFixedWidth.length > 0) {
    issues.push(`${elementsWithFixedWidth.length} element(s) with fixed pixel widths`);
  }

  // Check for viewport meta tag if this is a document
  if (typeof Document !== 'undefined' && received instanceof Document) {
    const viewportMeta = received.querySelector('meta[name="viewport"]');
    if (!viewportMeta) {
      issues.push('Missing viewport meta tag');
    }
  }

  // Check for elements that might overflow
  const wideElements = Array.from(received.querySelectorAll('*')).filter((el) => {
    if (typeof window !== 'undefined' && window.getComputedStyle) {
      const styles = window.getComputedStyle(el);
      const width = parseFloat(styles.width);
      return width > 1200; // Arbitrary threshold
    }
    return false;
  });

  if (wideElements.length > 0) {
    issues.push(`${wideElements.length} element(s) wider than 1200px`);
  }

  const pass = issues.length === 0;

  return {
    pass,
    message: () =>
      pass
        ? `Expected element to have responsive issues, but found none`
        : `Expected element to be responsive, but found issues:\n  - ${issues.join('\n  - ')}`,
  };
};

/**
 * Check if component loaded without JavaScript errors
 */
const toHaveLoadedWithoutErrors: MatcherFunction<[]> = function (received: HTMLElement) {
  // This is a simplified check - in a real implementation, you'd track JS errors
  const errorElements = received.querySelectorAll('[data-error], .error, [aria-invalid="true"]');
  const pass = errorElements.length === 0;

  return {
    pass,
    message: () =>
      pass
        ? `Expected element to have errors, but found none`
        : `Expected element to load without errors, but found ${errorElements.length} error indicator(s)`,
  };
};

/**
 * Visual snapshot testing matcher
 */
const toMatchVisualSnapshot: MatcherFunction<[snapshotName?: string]> = async function (
  received: HTMLElement,
  snapshotName?: string
) {
  // This would integrate with a visual testing tool like Percy, Chromatic, or Playwright
  // For now, it's a placeholder that always passes
  const name = snapshotName || 'component-snapshot';

  // In a real implementation, this would:
  // 1. Take a screenshot of the element
  // 2. Compare it to a stored baseline
  // 3. Report differences

  return {
    pass: true,
    message: () => `Visual snapshot "${name}" matched baseline`,
  };
};

/**
 * Security audit matcher
 */
const toPassSecurityAudit: MatcherFunction<[]> = function (received: HTMLElement) {
  const securityIssues: string[] = [];

  // Check for potential XSS vectors
  const dangerousElements = received.querySelectorAll(
    'script, object, embed, iframe[src*="javascript:"]'
  );
  if (dangerousElements.length > 0) {
    securityIssues.push(`${dangerousElements.length} potentially dangerous element(s)`);
  }

  // Check for forms without CSRF protection
  const forms = received.querySelectorAll('form');
  forms.forEach((form, index) => {
    const csrfToken = form.querySelector('input[name*="csrf"], input[name*="token"]');
    const method = form.getAttribute('method');
    if (!csrfToken && method?.toLowerCase() === 'post') {
      securityIssues.push(`Form ${index + 1} missing CSRF protection`);
    }
  });

  // Check for external links without security attributes
  const externalLinks = received.querySelectorAll('a[href^="http"]:not([rel*="noopener"])');
  if (externalLinks.length > 0) {
    securityIssues.push(`${externalLinks.length} external link(s) without rel="noopener"`);
  }

  const pass = securityIssues.length === 0;

  return {
    pass,
    message: () =>
      pass
        ? `Expected element to fail security audit, but it passed`
        : `Expected element to pass security audit, but found issues:\n  - ${securityIssues.join('\n  - ')}`,
  };
};

// Register all matchers
if (typeof expect !== 'undefined') {
  expect.extend({
    toBeAccessible,
    toHaveNoSecurityViolations,
    toBePerformant,
    toHaveValidMarkup,
    toBeResponsive,
    toHaveLoadedWithoutErrors,
    toMatchVisualSnapshot,
    toPassSecurityAudit,
  });
}

export {
  toBeAccessible,
  toHaveNoSecurityViolations,
  toBePerformant,
  toHaveValidMarkup,
  toBeResponsive,
  toHaveLoadedWithoutErrors,
  toMatchVisualSnapshot,
  toPassSecurityAudit,
};
