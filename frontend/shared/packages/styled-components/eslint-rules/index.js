/**
 * Custom ESLint Rules for DotMac Styled Components
 *
 * This module exports all custom ESLint rules for the styled components package.
 */

module.exports = {
  rules: {
    'no-cross-portal-imports': require('./no-cross-portal-imports'),
  },

  configs: {
    recommended: {
      plugins: ['@dotmac/styled-components'],
      rules: {
        '@dotmac/styled-components/no-cross-portal-imports': 'error',
      },
    },

    strict: {
      plugins: ['@dotmac/styled-components'],
      rules: {
        '@dotmac/styled-components/no-cross-portal-imports': [
          'error',
          {
            allowShared: true,
            allowMixedInTests: false, // Strict mode doesn't allow mixed imports even in tests
            testFilePatterns: ['**/*.test.*', '**/*.spec.*'],
          },
        ],
      },
    },
  },
};
