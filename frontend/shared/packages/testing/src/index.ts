// Enhanced render utilities
export * from './utils/render';

// Custom matchers
export * from './utils/matchers';

// Re-export testing library utilities
export * from '@testing-library/react';
export { default as userEvent } from '@testing-library/user-event';
export { axe, toHaveNoViolations } from 'jest-axe';

// Test configuration and utilities
export { testConfig, testUtils, a11yUtils, securityUtils, perfUtils } from './jest/setup';
