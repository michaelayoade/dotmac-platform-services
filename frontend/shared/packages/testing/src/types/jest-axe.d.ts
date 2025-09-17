/**
 * Type declarations for jest-axe
 */

declare module 'jest-axe' {
  export interface AxeResults {
    violations: Array<{
      id: string;
      description: string;
      impact?: string;
      tags: string[];
      nodes: Array<{
        target: string[];
        failureSummary?: string;
        html: string;
      }>;
    }>;
  }

  export function axe(element: Element | Document): Promise<AxeResults>;

  export const toHaveNoViolations: {
    toHaveNoViolations(received: AxeResults): {
      pass: boolean;
      message(): string;
    };
  };

  export function configureAxe(options?: {
    rules?: Record<string, { enabled: boolean }>;
    tags?: string[];
  }): (element: Element | Document) => Promise<AxeResults>;
}
