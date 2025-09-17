/**
 * Jest Setup for Dashboard Package
 * Configures testing environment for React components
 */

require('@testing-library/jest-dom');

// Mock framer-motion to prevent animation issues in tests
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }) => <div {...props}>{children}</div>,
    button: ({ children, ...props }) => <button {...props}>{children}</button>,
  },
  AnimatePresence: ({ children }) => children,
}));

// Mock date-fns for consistent time-based tests
jest.mock('date-fns', () => ({
  formatDistanceToNow: () => 'a few seconds ago',
  format: () => '12:00 PM',
  subHours: (date, hours) => new Date(date.getTime() - hours * 60 * 60 * 1000),
  subDays: (date, days) => new Date(date.getTime() - days * 24 * 60 * 60 * 1000),
  subWeeks: (date, weeks) => new Date(date.getTime() - weeks * 7 * 24 * 60 * 60 * 1000),
}));

// Global test helpers
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};
