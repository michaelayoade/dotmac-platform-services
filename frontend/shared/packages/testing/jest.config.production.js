/**
 * Production-Ready Jest Configuration
 * Optimized for <30s test execution with 90% security coverage
 * Leverages unified architecture for maximum efficiency
 */

const { testOptimizer } = require('./src/performance/test-performance-optimizer');

/** @type {import('jest').Config} */
module.exports = {
  // Use optimized configuration
  ...testOptimizer.createOptimizedJestConfig(),

  // Project identification
  displayName: 'DotMac Frontend - Production Tests',

  // Root configuration
  rootDir: '../..',
  testEnvironment: 'jsdom',

  // Performance-optimized patterns
  testMatch: [
    '<rootDir>/packages/security/src/__tests__/**/*.test.{ts,tsx}',
    '<rootDir>/packages/auth/src/__tests__/**/*.test.{ts,tsx}',
    '<rootDir>/packages/testing/src/**/*.test.{ts,tsx}',
    '<rootDir>/apps/*/src/**/__tests__/**/*.{test,spec}.{ts,tsx}',
  ],

  // Fast module resolution
  moduleNameMapper: {
    '^@dotmac/ui$': '<rootDir>/packages/ui/src',
    '^@dotmac/providers$': '<rootDir>/packages/providers/src',
    '^@dotmac/auth$': '<rootDir>/packages/auth/src',
    '^@dotmac/headless$': '<rootDir>/packages/headless/src',
    '^@dotmac/testing$': '<rootDir>/packages/testing/src',
    '^@dotmac/security$': '<rootDir>/packages/security/src',
    '^@/(.*)$': '<rootDir>/src/$1',
  },

  // Optimized setup
  setupFilesAfterEnv: ['<rootDir>/packages/testing/src/setup/production-setup.ts'],

  // Fast transforms
  transform: {
    '^.+\\.(ts|tsx)$': [
      'ts-jest',
      {
        isolatedModules: true,
        useESM: true,
        tsconfig: {
          jsx: 'react-jsx',
          esModuleInterop: true,
          allowSyntheticDefaultImports: true,
        },
      },
    ],
  },

  // Production coverage settings
  collectCoverage: true,
  coverageDirectory: '<rootDir>/coverage',
  coverageReporters: ['text-summary', 'lcov', 'html'],

  // Security-focused coverage
  collectCoverageFrom: [
    '<rootDir>/packages/security/src/**/*.{ts,tsx}',
    '<rootDir>/packages/auth/src/**/*.{ts,tsx}',
    '<rootDir>/packages/providers/src/**/*.{ts,tsx}',
    '<rootDir>/packages/ui/src/**/*.{ts,tsx}',
    '<rootDir>/apps/*/src/**/*.{ts,tsx}',
    '!**/__tests__/**',
    '!**/*.test.{ts,tsx}',
    '!**/*.spec.{ts,tsx}',
    '!**/*.d.ts',
    '!**/node_modules/**',
  ],

  // Aggressive coverage thresholds for security
  coverageThreshold: {
    global: {
      branches: 85,
      functions: 90,
      lines: 90,
      statements: 90,
    },
    // Critical security modules require 95%
    './packages/security/src/**/*.{ts,tsx}': {
      branches: 95,
      functions: 95,
      lines: 95,
      statements: 95,
    },
    './packages/auth/src/**/*.{ts,tsx}': {
      branches: 95,
      functions: 95,
      lines: 95,
      statements: 95,
    },
  },

  // Performance optimization
  maxWorkers: '50%', // Use half CPU cores for stability
  cache: true,
  cacheDirectory: '<rootDir>/.jest-cache',

  // Timeout settings
  testTimeout: 10000, // 10s max per test

  // CI/CD optimizations
  reporters: [
    'default',
    [
      'jest-junit',
      {
        outputDirectory: '<rootDir>/test-results',
        outputName: 'junit.xml',
      },
    ],
    [
      'jest-html-reporter',
      {
        pageTitle: 'DotMac Frontend Test Results',
        outputPath: '<rootDir>/test-results/test-report.html',
        includeFailureMsg: true,
        includeSuiteFailure: true,
      },
    ],
  ],

  // Memory management
  logHeapUsage: true,
  detectOpenHandles: false,
  forceExit: true,

  // Mock configurations for unified architecture
  modulePathIgnorePatterns: ['<rootDir>/node_modules/'],

  // Global test configuration
  globals: {
    'ts-jest': {
      isolatedModules: true,
    },
    // Performance monitoring
    __PERFORMANCE_TESTING__: true,
    __SECURITY_TESTING__: true,
  },

  // Test environment setup
  testEnvironmentOptions: {
    url: 'http://localhost:3000',
  },

  // Ignore patterns for speed
  testPathIgnorePatterns: ['/node_modules/', '/\.next/', '/coverage/', '/dist/', '/build/'],

  // Watch mode optimization (development)
  watchPlugins: ['jest-watch-typeahead/filename', 'jest-watch-typeahead/testname'],

  // Snapshot serializers
  snapshotSerializers: ['@emotion/jest/serializer'],
};
